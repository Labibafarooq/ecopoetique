#!/usr/bin/env python3
"""
run_task0_mapreduce_v7_gpt4o.py

Port of run_task0_mapreduce_v7.py (the best-tuned local map-reduce narratology
pipeline — v6 rules + evidence-based INT/TEM/REG fixes + the context-budget
fix that dropped 79-84% of sampled chunk text in v3/v6) to GPT-4o instead of
qwen3:30b via Ollama. All prompts, chunking rules (MAX_LINES=350,
MAX_CHARS_PER_CHUNK=38000), the 3x reduce-vote majority scheme, and JSON
parsing are copied verbatim from v7 — only the model backend changes, so the
comparison is apples-to-apples against v7's local qwen3 result.

Differences from v7, deliberate:
  - Calls OpenAI gpt-4o instead of local Ollama qwen3:30b.
  - Ollama's "format": "json" constrained decoding -> OpenAI's equivalent
    response_format={"type": "json_object"}.
  - num_ctx/num_predict (Ollama-specific) -> max_tokens (same MAP=1500,
    REDUCE=900 budgets, generous margin kept for parity).
  - GOLD_FILE points at GOLD_narratologie_60novels_original.csv (confirmed
    identical in content to the actual committed GitLab main-branch gold
    set), not the local, differently-formatted GOLD_narratologie.csv v7
    defaulted to.
  - Bakes in a DNS workaround for api.openai.com: obtic-gpu1's local DNS
    returns SERVFAIL for public hostnames (university network policy) even
    though raw outbound TCP is open, so api.openai.com is resolved via public
    DNS once at startup and pinned for this process only.
"""

import os, csv, json, time, re, argparse, socket, subprocess
from collections import Counter
from datetime import datetime

# ── DNS workaround (see module docstring) ──────────────────────────────────
def _patch_dns_for_openai():
    try:
        ip = subprocess.run(
            ["dig", "+short", "api.openai.com", "@8.8.8.8"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip().splitlines()[-1]
    except Exception:
        return
    real_getaddrinfo = socket.getaddrinfo
    def patched(host, *args, **kwargs):
        if host == "api.openai.com":
            host = ip
        return real_getaddrinfo(host, *args, **kwargs)
    socket.getaddrinfo = patched

_patch_dns_for_openai()

from openai import OpenAI

# ── CONFIG ───────────────────────────────────────────────────────────────────
MODEL       = "gpt-4o"
CORPUS_DIR  = os.path.expanduser("~/ecopoetique/CORPUS_TOTAL")
GOLD_FILE   = os.path.expanduser("~/ecopoetique/narratologie/GOLD_narratologie_60novels_original.csv")
OUTPUT_FILE = os.path.expanduser("~/ecopoetique/narratologie/resultats_gpt4o_mapreduce_v7.csv")
N_CHUNKS    = 9
MAX_LINES   = 350
MAX_CHARS_PER_CHUNK = 38000
N_REDUCE_VOTES = 3
REDUCE_TEMPERATURE = 0.4
MAP_NUM_PREDICT    = 1500
REDUCE_NUM_PREDICT = 900

def _load_env_key():
    env = {}
    with open(os.path.expanduser("~/ecopoetique/.env")) as f:
        for line in f:
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env.get("OPENAI_API_KEY")

client = OpenAI(api_key=_load_env_key())

# ── CRITERIA DEFINITIONS (verbatim from v7) ─────────────────────────────────
CRITERIA_DEFS = """
TYPE DE NARRATEUR
• NAR_AUTOD : le narrateur EST le protagoniste principal (dit "je" et vit l'histoire).
• NAR_TEM   : le narrateur dit "je/nous" mais est personnage secondaire ou témoin.
• NAR_EXT   : le narrateur est ABSENT de l'histoire, raconte à la 3ème personne.

FOCALISATION
• FOC_INT  : accès à l'intériorité d'UN SEUL personnage, narration restreinte.
             Le même personnage focal domine dans toutes les sections.
• FOC_EXT  : AUCUN accès aux pensées ou émotions. Description en surface uniquement.
• FOC_ZERO : narrateur omniscient (3ème personne) accédant librement aux consciences.
             ⚠ FOC_ZERO si le narrateur est à la 3ème personne et entre dans les pensées,
               même si une seule section a un "pov_chapter_marker"=no et un seul
               personnage dominant dans CETTE section — regarde l'ENSEMBLE des sections.
             ⚠ FOC_VAR ≠ FOC_ZERO : FOC_VAR uniquement si plusieurs sections ont
               pov_chapter_marker=yes avec des personnages DIFFÉRENTS et DÉSIGNÉS
               (ex: "Chapitre Marie", "Chapitre Paul"). Si le narrateur passe fluidement
               d'une conscience à l'autre sans chapitres nommés → FOC_ZERO, pas FOC_VAR.
• FOC_VAR  : alternance STRUCTURÉE entre plusieurs POV internes, sections explicitement
             attribuées à des personnages différents (pov_chapter_marker=yes répété).

MODE NARRATIF DOMINANT
• MOD_EVT  : l'action, les faits, les décisions dominent — même s'il y a des pensées.
             ⚠ La simple présence de pensées ne suffit pas pour choisir MOD_INTR.
• MOD_DESC : les descriptions de décors, objets, sensations, ambiances dominent.
• MOD_INTR : les réflexions intérieures et états d'âme DOMINENT CLAIREMENT sur l'action.
             Choisir MOD_INTR uniquement si l'action est clairement secondaire dans
             la MAJORITÉ des sections, pas seulement quelques-unes.
• MOD_MIX  : aucun mode ne domine — équilibre stable entre plusieurs modes.

RÉGIME NARRATIF — vérifie dans cet ordre, en te basant sur L'ENSEMBLE des sections
1. Le narrateur ou un personnage focal est-il une entité NON-HUMAINE dotée d'une
   conscience narrative propre (animal, objet, entité collective, etc.), de façon
   récurrente à travers plusieurs sections ? OU des éléments surnaturels/inexplicables
   perturbent-ils le réel dans plusieurs sections ? → REG_FANT
2. Sinon, le monde est-il clairement futuriste, dystopique, ou transformé politiquement/
   technologiquement par rapport au réel actuel ? → REG_SPEC
3. Sinon, la MAJORITÉ des sections adoptent-elles un ton confessionnel/réflexif soutenu
   sur une vie qui semble être celle, réelle ou proche du réel, du narrateur — que ce
   soit dit explicitement (référence à l'écriture du livre, à l'identité de l'auteur)
   ou simplement par une posture subjective et réflexive constante ? → REG_AUTO
4. Sinon → REG_REAL

ORGANISATION DE L'ESPACE — compare les lieux mentionnés dans toutes les sections
• ESP_UNIT : même environnement général dans toutes les sections (même ville,
             bâtiment, région — même avec des sous-lieux différents).
• ESP_FRAG : lieux GÉOGRAPHIQUEMENT DISTINCTS entre sections (villes/pays/régions
             différents sans cohérence spatiale forte).
• ESP_ITIN : les personnages sont EN DÉPLACEMENT CONTINU — le voyage est central.
• ESP_IMAG : l'espace est partiellement ou totalement inventé, irréaliste, symbolique.

NATURE DE L'INTRIGUE — lis les key_observation de TOUTES les sections dans l'ordre
(section 1 → section {n_chunks}) et juge l'ENSEMBLE, pas une section isolément :
est-ce que l'histoire progresse comme une seule scène/action continue qui s'enchaîne
logiquement de section en section, ou est-ce que les sections ressemblent à une suite
d'épisodes/moments distincts juxtaposés — MÊME SI le même personnage revient d'une
section à l'autre (un même personnage peut être montré à travers une suite d'épisodes
séparés plutôt qu'une action continue) ?
• INTR_FRAG : plusieurs sections s'introduisent comme un nouveau moment/une nouvelle
              scène plutôt que de reprendre directement la suite de la précédente ; les
              key_observation, mis bout à bout, ne forment pas une progression continue.
• INTR_LIN  : les key_observation, mis bout à bout, forment une progression cohérente
              et continue d'un événement vers le suivant, sur le même fil narratif.
• INTR_CYC  : la situation ou les motifs de la dernière section se rapportent
              fortement à ceux de la première section (retour net au point de départ).

TEMPORALITÉ — compare les repères temporels (time_position_marker) des sections DANS
L'ORDRE (section 1 → section {n_chunks})
• TEMP_LIN    : les repères temporels progressent de façon globalement cohérente et
                avancent dans le temps ; peu ou pas de flashback_or_jump_in_section=yes
                ni de narration_stance=retrospective_reflection.
• TEMP_DIS    : au moins une contradiction notable dans la progression (un repère plus
                tardif apparaît avant un repère plus précoce, ou des lignes temporelles
                distinctes selon les sections), OU plusieurs sections signalent un
                flashback/saut ou une posture rétrospective — sans que la chronologie
                devienne totalement illisible.
• TEMP_DESORD : la chronologie est impossible à reconstituer de façon cohérente à
                partir des repères temporels donnés dans la majorité des sections.
"""

# ── MAP PROMPT (verbatim from v7) ────────────────────────────────────────────
MAP_SYSTEM = """Tu es un analyste littéraire expert en narratologie française.
Réponds UNIQUEMENT avec un objet JSON. Pas de réflexion affichée, pas d'hésitation
("d'abord je vais...", "voyons...", "analysons..."), pas de préambule, pas
d'explication. Le premier caractère de ta réponse doit être {."""

def map_prompt(chunk_text, chunk_index, total_chunks):
    pos = ("DÉBUT"    if chunk_index == 0 else
           "FIN"       if chunk_index == total_chunks - 1 else
           f"MILIEU section {chunk_index+1}/{total_chunks}")
    if len(chunk_text) > MAX_CHARS_PER_CHUNK:
        mid  = len(chunk_text) // 2
        half = MAX_CHARS_PER_CHUNK // 2
        chunk_text = chunk_text[max(0, mid-half): mid+half]
    return f"""Analyse cet extrait ({pos}) d'un roman français.

--- EXTRAIT ---
{chunk_text}
--- FIN EXTRAIT ---

DÉFINITIONS DE RÉFÉRENCE :
{CRITERIA_DEFS.format(n_chunks=total_chunks)}

Réponds directement par le JSON ci-dessous, SANS AUCUN TEXTE avant (remplace les ...
par tes observations sur CET extrait) :
{{
  "chunk": {chunk_index + 1},
  "position": "{pos}",
  "narrator_voice": "first_person OU third_person OU unclear",
  "narrator_role": "protagonist OU witness OU not_applicable",
  "inner_thoughts": "none OU one_character OU multiple_characters",
  "pov_chapter_marker": "yes OU no",
  "dominant_mode": "action_events OU description OU introspection OU mixed",
  "world_type": "realistic OU autobiographical_explicit OU fantastic OU speculative_sf",
  "narrator_entity": "human OU non_human_or_unconventional (ex: animal, objet, entité collective)",
  "autobiographical_signal": "none OU implicit_confessional_tone OU explicit_author_reference",
  "space": "single_location OU multiple_locations OU journey_travel OU imaginary",
  "focus_character_or_thread": "qui/quel fil narratif domine CETTE section (bref)",
  "time_position_marker": "tout repère temporel explicite/implicite dans CETTE section (âge, date, saison, avant/après un événement...), ou 'none'",
  "narration_stance": "in_scene OU retrospective_reflection",
  "flashback_or_jump_in_section": "yes OU no (un saut temporel DANS cet extrait même)",
  "key_observation": "deux phrases : ce qui se passe concrètement dans cette section, et comment elle COMMENCE (reprend-elle directement la suite de la scène précédente, ou s'introduit-elle comme un nouveau moment/une nouvelle scène/un nouveau décor ?)"
}}"""

# ── REDUCE PROMPT (verbatim from v7) ─────────────────────────────────────────
REDUCE_SYSTEM = """Tu es un expert en narratologie française.
Réponds UNIQUEMENT avec un objet JSON. Pas de réflexion affichée, pas d'hésitation
("attends", "en fait", "non plutôt"), pas de préambule. Va directement au résultat."""

def reduce_prompt(observations, filename):
    n = len(observations)
    return f"""Roman : {filename}

Observations de {n} sections (début → fin) :
{json.dumps(observations, ensure_ascii=False, indent=2)}

{CRITERIA_DEFS.format(n_chunks=n)}

INSTRUCTIONS :
- Base ta décision sur L'ENSEMBLE des sections, pas une seule.
- Pour ESPACE, INTRIGUE et TEMPORALITÉ : compare ACTIVEMENT les sections entre elles
  (ordre, continuité de personnage/fil narratif, cohérence des repères temporels).
- Pour RÉGIME NARRATIF : les critères FANT et AUTO se jugent sur la récurrence à travers
  PLUSIEURS sections, pas sur un seul détail isolé.
- Choisis EXACTEMENT un code par critère.

Réponds UNIQUEMENT avec ce JSON :
{{
  "TYPE NARRATEUR":  "NAR_AUTOD ou NAR_TEM ou NAR_EXT",
  "FOCALISATION":    "FOC_INT ou FOC_EXT ou FOC_ZERO ou FOC_VAR",
  "MODE NARRATIF":   "MOD_EVT ou MOD_DESC ou MOD_INTR ou MOD_MIX",
  "REGIME NARRATIF": "REG_AUTO ou REG_REAL ou REG_FANT ou REG_SPEC",
  "ESPACE":          "ESP_UNIT ou ESP_FRAG ou ESP_ITIN ou ESP_IMAG",
  "INTRIGUE":        "INTR_LIN ou INTR_FRAG ou INTR_CYC",
  "TEMPORALITÉ":     "TEMP_LIN ou TEMP_DIS ou TEMP_DESORD"
}}"""

# ── OPENAI CALL (replaces call_ollama) ───────────────────────────────────────
def call_openai(system_msg, user_msg, temperature=0.0, max_tokens=800):
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": user_msg},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},  # equivalent of Ollama's "format": "json"
    )
    return (resp.choices[0].message.content or "").strip()

def extract_json(text):
    """Robust extraction: strips think blocks/fences, finds balanced {...} objects,
    returns the last one that parses (usually the answer, not stray fragments)."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"```(?:json)?", "", text).replace("```", "")

    objects = []
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                objects.append(text[start:i+1])
                start = None

    for candidate in reversed(objects):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    raise ValueError(f"No valid JSON object found. Response was:\n{text[:400]}")

# ── CHUNKING (verbatim from v7) ───────────────────────────────────────────────
def chunk_novel(lines, n=N_CHUNKS, max_lines=MAX_LINES):
    total = len(lines)
    size  = max(total // n, 1)
    chunks = []
    for i in range(n):
        start = i * size
        end   = start + size if i < n - 1 else total
        sl = lines[start:end]
        if len(sl) > max_lines:
            mid  = len(sl) // 2
            half = max_lines // 2
            sl   = sl[max(0, mid-half): mid+half]
        chunks.append((i, "".join(sl)))
    return chunks

# ── GOLD LOADING ──────────────────────────────────────────────────────────────
def load_gold(path):
    gold = {}
    with open(path, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader)
        for row in reader:
            if not row or not row[0].strip():
                continue
            def col(i):
                return row[i].strip() if i < len(row) else ""
            fn = col(0)
            gold[fn] = {
                "TYPE NARRATEUR":  col(4),  "NAR_alt": col(5),
                "FOCALISATION":    col(6),  "FOC_alt": col(7),
                "MODE NARRATIF":   col(8),  "MOD_alt": col(9),
                "REGIME NARRATIF": col(10), "REG_alt": col(11),
                "ESPACE":          col(12), "ESP_alt": col(13),
                "INTRIGUE":        col(14), "INT_alt": col(15),
                "TEMPORALITÉ":     col(16), "TEM_alt": col(17),
            }
    return gold

def is_correct(pred, main, alt=""):
    if not pred:
        return False
    p = pred.strip().upper()
    if p == main.strip().upper():
        return True
    if alt and p == alt.strip().upper():
        return True
    return False

# ── EVALUATION ────────────────────────────────────────────────────────────────
CRITERIA = [
    ("TYPE NARRATEUR",  "NAR_alt"),
    ("FOCALISATION",    "FOC_alt"),
    ("MODE NARRATIF",   "MOD_alt"),
    ("REGIME NARRATIF", "REG_alt"),
    ("ESPACE",          "ESP_alt"),
    ("INTRIGUE",        "INT_alt"),
    ("TEMPORALITÉ",     "TEM_alt"),
]

def evaluate(results, gold):
    scores = {c: [0, 0] for c, _ in CRITERIA}
    oc = ot = 0
    for r in results:
        fn = r["File"]
        if fn not in gold:
            continue
        g = gold[fn]
        for crit, alt_key in CRITERIA:
            pred = r.get(crit, "").strip()
            if not pred:
                continue
            scores[crit][1] += 1
            ot += 1
            if is_correct(pred, g[crit], g[alt_key]):
                scores[crit][0] += 1
                oc += 1

    print("\n" + "="*62)
    print(f"  MAP-REDUCE v7 RESULTS  —  {MODEL}  ({N_REDUCE_VOTES}x reduce vote)")
    print("="*62)
    for crit, (c, t) in scores.items():
        if t:
            acc = c/t*100
            bar = "█" * int(acc/5)
            print(f"  {crit:<22} {c:>2}/{t:<2}  ({acc:>5.1f}%)  {bar}")
    print("-"*62)
    if ot:
        ov = oc/ot*100
        print(f"  {'OVERALL':<22} {oc:>3}/{ot:<3}  ({ov:>5.1f}%)")
    print("="*62)
    print(f"\n  qwen3:30b v7 (same method, local): reference point in resultats_task0_mapreduce_v7.csv")
    print(f"  gpt-4o simple baseline (1 extract/novel): 67.1%")
    print()

# ── SAVE / LOAD ───────────────────────────────────────────────────────────────
def save_results(rows, path):
    if not rows:
        return
    keys = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

def load_done(path):
    done = set()
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                done.add(row.get("File","").strip())
    return done

# ── PROCESS ONE NOVEL ─────────────────────────────────────────────────────────
def process_novel(filename, filepath):
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    chunks = chunk_novel(lines)
    print(f"    {len(lines)} lines -> {N_CHUNKS} chunks of ~{len(lines)//N_CHUNKS} lines")

    observations = []
    for idx, text in chunks:
        if not text.strip():
            continue
        try:
            raw = call_openai(MAP_SYSTEM, map_prompt(text, idx, N_CHUNKS),
                               temperature=0.0, max_tokens=MAP_NUM_PREDICT)
            obs = extract_json(raw)
            observations.append(obs)
            print(f"    chunk {idx+1}/{N_CHUNKS}: "
                  f"voice={obs.get('narrator_voice','?')[:12]} "
                  f"thread={str(obs.get('focus_character_or_thread','?'))[:20]} "
                  f"time={str(obs.get('time_position_marker','?'))[:20]}")
        except Exception as e:
            print(f"    x chunk {idx+1}/{N_CHUNKS} failed: {e}")
            observations.append({"chunk": idx+1, "error": str(e)})

    good = [o for o in observations if "error" not in o]
    if not good:
        raise ValueError(f"All {N_CHUNKS} chunks failed — no usable observations")

    print(f"    -> reduce step x{N_REDUCE_VOTES} ({len(good)}/{N_CHUNKS} good observations)")
    votes = []
    for v in range(N_REDUCE_VOTES):
        raw = call_openai(REDUCE_SYSTEM, reduce_prompt(good, filename),
                           temperature=REDUCE_TEMPERATURE, max_tokens=REDUCE_NUM_PREDICT)
        try:
            votes.append(extract_json(raw))
        except Exception as e:
            print(f"    x reduce vote {v+1}/{N_REDUCE_VOTES} failed: {e}")

    if not votes:
        raise ValueError("All reduce votes failed")

    final = {}
    for crit, _ in CRITERIA:
        vals = [v.get(crit, "").strip().upper() for v in votes if v.get(crit)]
        if not vals:
            final[crit] = ""
            continue
        counts = Counter(vals)
        top_count = max(counts.values())
        winners = [v for v in vals if counts[v] == top_count]
        final[crit] = winners[0]  # ties broken by first occurrence -> first (lowest-index) run
    return final

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test",   type=int, default=0)
    ap.add_argument("--novels", type=str, default="")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    print(f"\n{'='*62}")
    print(f"  TASK 0 MAP-REDUCE v7 — GPT-4o port")
    print(f"  Model: {MODEL}   Chunks: {N_CHUNKS}   Max lines/chunk: {MAX_LINES}   Reduce votes: {N_REDUCE_VOTES}")
    print(f"  Started: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"{'='*62}\n")

    gold = load_gold(GOLD_FILE)
    print(f"Gold: {len(gold)} novels")

    all_txt = set(os.listdir(CORPUS_DIR))
    to_run  = [(fn, os.path.join(CORPUS_DIR, fn)) for fn in gold if fn in all_txt]
    missing = [fn for fn in gold if fn not in all_txt]
    print(f"Novels in CORPUS_TOTAL: {len(to_run)}  missing: {len(missing)}")
    if missing:
        print(f"  Missing: {missing}")

    if args.novels:
        wanted = set(x.strip() for x in args.novels.split(","))
        to_run = [x for x in to_run if x[0] in wanted]
        print(f"TARGETED VALIDATION: {len(to_run)} novels")

    done = load_done(OUTPUT_FILE) if args.resume else set()
    if done:
        print(f"Resuming: {len(done)} done, {len(to_run)-len(done)} remaining")

    to_run = [x for x in to_run if x[0] not in done]
    if args.test:
        to_run = to_run[:args.test]
        print(f"TEST MODE: {args.test} novels")
    print()

    existing = []
    if args.resume and os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            existing = list(csv.DictReader(f))

    output_rows  = list(existing)
    results_eval = []

    for i, (fn, fp) in enumerate(to_run, 1):
        print(f"\n[{i}/{len(to_run)}] {fn}")
        t0 = time.time()
        g  = gold.get(fn, {})
        try:
            pred = process_novel(fn, fp)
            el   = time.time() - t0

            def chk(crit, alt):
                return "v" if is_correct(pred.get(crit,""), g.get(crit,""), g.get(alt,"")) else "x"

            print(f"  -> {el:.0f}s | "
                  f"NAR={pred.get('TYPE NARRATEUR','?')}{chk('TYPE NARRATEUR','NAR_alt')} "
                  f"FOC={pred.get('FOCALISATION','?')}{chk('FOCALISATION','FOC_alt')} "
                  f"MOD={pred.get('MODE NARRATIF','?')}{chk('MODE NARRATIF','MOD_alt')} "
                  f"REG={pred.get('REGIME NARRATIF','?')}{chk('REGIME NARRATIF','REG_alt')} "
                  f"ESP={pred.get('ESPACE','?')}{chk('ESPACE','ESP_alt')} "
                  f"INT={pred.get('INTRIGUE','?')}{chk('INTRIGUE','INT_alt')} "
                  f"TEM={pred.get('TEMPORALITÉ','?')}{chk('TEMPORALITÉ','TEM_alt')}")

            row = {"File": fn,
                   **{c: pred.get(c,"") for c, _ in CRITERIA},
                   **{f"GOLD_{c[:3]}": g.get(c,"") for c, _ in CRITERIA},
                   **{f"ALT_{c[:3]}":  g.get(a,"") for c, a in CRITERIA}}
            output_rows.append(row)
            results_eval.append(row)

        except Exception as e:
            print(f"  x FAILED: {e}")
            output_rows.append({"File": fn, "ERROR": str(e)})

        if i % 3 == 0:
            save_results(output_rows, OUTPUT_FILE)
            print(f"  [checkpoint saved, {i} done]")

    save_results(output_rows, OUTPUT_FILE)
    print(f"\nDone — {len(results_eval)} novels processed")
    print(f"Saved to: {OUTPUT_FILE}")

    if results_eval:
        evaluate(results_eval, gold)

if __name__ == "__main__":
    main()
