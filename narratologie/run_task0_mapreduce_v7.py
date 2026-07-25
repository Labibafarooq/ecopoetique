#!/usr/bin/env python3
"""
run_task0_mapreduce_v7.py  —  mapreduce v6 + evidence-based fixes for
INTRIGUE, TEMPORALITÉ, RÉGIME NARRATIF (+ a shared context-budget fix).

Root causes found by replaying actual MAP calls on known-weak novels from
mapreduce_v6 (see resultats_task0_mapreduce_v6.csv confusion patterns),
NOT by hardcoding those novels' gold labels into any prompt below:

  1. CONTEXT-BUDGET BUG (shared by v3 and v6, affects ALL criteria):
     map_prompt truncated chunk_text to chunk_text[:6000] regardless of how
     much text chunk_novel() had already selected (up to MAX_LINES=400,
     often 30-45K chars). Measured loss: 79-84% of the already-sampled text
     discarded on a representative long novel. num_predict was also fixed at
     5000 for both MAP (needs ~500 tok) and REDUCE (~250 tok) calls, wasting
     context budget that could hold passage text instead. Fix: drop the
     redundant char-level truncation (chunk_novel's line-level MAX_LINES is
     now the single source of truth for chunk size), raise MAX_LINES
     modestly (400->450, sized against measured corpus density of ~115
     chars/line to stay inside num_ctx=16384), and split num_predict into a
     small MAP budget vs REDUCE budget so the freed tokens go to input text.

  2. INTRIGUE: v6 asked each chunk "are events in this passage causally
     linked?" — nearly always true for a short passage in isolation,
     regardless of whether the WHOLE novel is fragmented. Replaced with a
     signal that's actually answerable per-chunk without seeing other
     chunks: who/what this section is centered on, and whether it reads as
     a direct continuation, a self-contained episode, or an echo of an
     earlier situation. REDUCE compares these across sections instead of
     asking the model to introspect on cross-chunk structure it can't see.

  3. TEMPORALITÉ: v6's anachrony_present (yes/no) only detects a flashback
     occurring INSIDE one excerpt, then REQUIRED it to fire in 3+ of 9
     sections — missing novels whose non-linearity comes from unsynchronized
     parallel storylines across sections rather than an in-scene flashback.
     Replaced anachrony_present with three signals: an explicit/implicit
     story-time marker per section (compared across the ordered sections at
     REDUCE), a narration-stance flag (in-scene vs. retrospective), and a
     narrower intra-section flashback flag. REDUCE reasons about the pattern
     instead of applying a fixed count threshold.

  4. RÉGIME NARRATIF: the FANT/AUTO categories were under-firing because
     (a) the schema only asked for "world_type" as a single holistic
     judgment, with no separate flag for narrative devices that constitute
     "fantastic" without impossible plot EVENTS, and (b) REG_AUTO required
     explicit authorial self-reference, a much narrower bar than the
     original grille's "narrator's real or near-real life, subjective and
     reflective posture." Added a narrator_entity flag (human vs.
     non-human/unconventional narrating consciousness) and an
     autobiographical_signal flag (none / implicit confessional tone /
     explicit author reference), both aggregated at REDUCE by
     majority-across-sections (not single-chunk trigger, to avoid
     overcorrecting into v3's opposite over-triggering bias).

  5. Dropped the "confidence" 1-5 field: empirically it returned 5/5 on
     every chunk tested (two different novels), so the "weight
     high-confidence chunks more" REDUCE instruction in v6 was a no-op.

NAR/FOC/MOD/ESP prompts are UNCHANGED from v6 (those weren't broken) so any
accuracy delta on INT/TEM/REG can be attributed to the above, not conflated
with unrelated changes.

Usage:
  python run_task0_mapreduce_v7.py --test 5
  python run_task0_mapreduce_v7.py
  python run_task0_mapreduce_v7.py --resume
"""

import os, csv, json, time, re, argparse, requests
from collections import Counter
from datetime import datetime

# ── CONFIG ───────────────────────────────────────────────────────────────────
OLLAMA_URL  = "http://localhost:11435/api/chat"
MODEL       = "qwen3:30b"
CORPUS_DIR  = os.path.expanduser("~/ecopoetique/CORPUS_TOTAL")
GOLD_FILE   = os.path.expanduser("~/ecopoetique/narratologie/GOLD_narratologie.csv")
OUTPUT_FILE = os.path.expanduser("~/ecopoetique/narratologie/resultats_task0_mapreduce_v7.csv")
N_CHUNKS    = 9
MAX_LINES   = 350          # was 400 in v6 (but v6 then silently cut chunk_text to
                            # [:6000] chars anyway, so v6's REAL per-chunk content was
                            # only ~60-100 lines). Measured against actual Ollama
                            # prompt_eval_count (not just a chars/token guess): a
                            # 450-line chunk used 15,478 of 16,384 ctx tokens, leaving
                            # no safe room for output. 350 lines leaves a real margin.
MAX_CHARS_PER_CHUNK = 38000 # hard safety cap independent of MAX_LINES: line length
                            # varies a lot between novels (measured 100-145 chars/line
                            # depending on the source file's wrapping), so a line-count
                            # cap alone doesn't reliably bound token usage. Sized so
                            # passage + CRITERIA_DEFS + schema + system stays clearly
                            # under num_ctx=16384 with real output headroom, verified
                            # against actual Ollama prompt_eval_count, not just a
                            # chars/token guess.
TIMEOUT     = 300
N_REDUCE_VOTES = 3
REDUCE_TEMPERATURE = 0.4
MAP_NUM_PREDICT    = 1500   # MAP needs ~500 tok for the JSON itself; extra margin
                            # because qwen3 sometimes emits rambling prose before the
                            # JSON despite think:false + explicit instruction not to.
REDUCE_NUM_PREDICT = 900    # REDUCE returns 7 short fields (~250 tok needed) + margin

# ── CRITERIA DEFINITIONS ────────────────────────────────────────────────────
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

# ── MAP PROMPT ────────────────────────────────────────────────────────────────
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

# ── REDUCE PROMPT ─────────────────────────────────────────────────────────────
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

# ── OLLAMA CALL ───────────────────────────────────────────────────────────────
def call_ollama(system_msg, user_msg, temperature=0.0, num_predict=800):
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": user_msg},
        ],
        "stream": False,
        "think": False,   # real API-level thinking disable (text "/no_think" tricks don't work)
        "format": "json", # constrained decoding: forces valid JSON output directly.
                           # Prompt-only anti-rambling instructions ("no preamble")
                           # were NOT reliable enough on their own — verified against
                           # a live batch where MAP/REDUCE calls kept walking through
                           # step-by-step prose reasoning and exhausting num_predict
                           # before ever emitting JSON. format=json fixes this at the
                           # decoding level instead of hoping the model complies.
        "options": {
            "temperature": temperature,
            "num_ctx": 16384,
            "num_predict": num_predict,
        }
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    content = data.get("message", {}).get("content", "")
    if not content:
        content = data.get("response", "")
    return content.strip()

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

# ── CHUNKING ──────────────────────────────────────────────────────────────────
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
    print("="*62 + "\n")

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
            raw = call_ollama(MAP_SYSTEM, map_prompt(text, idx, N_CHUNKS),
                               temperature=0.0, num_predict=MAP_NUM_PREDICT)
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
        raw = call_ollama(REDUCE_SYSTEM, reduce_prompt(good, filename),
                           temperature=REDUCE_TEMPERATURE, num_predict=REDUCE_NUM_PREDICT)
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
    ap.add_argument("--novels", type=str, default="")  # comma-separated filenames for targeted validation
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    print(f"\n{'='*62}")
    print(f"  TASK 0 MAP-REDUCE v7  (v6 rules + evidence-based INT/TEM/REG fixes)")
    print(f"  Model: {MODEL}   Chunks: {N_CHUNKS}   Max lines/chunk: {MAX_LINES}   Reduce votes: {N_REDUCE_VOTES}")
    print(f"  Started: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"{'='*62}\n")

    gold = load_gold(GOLD_FILE)
    print(f"Gold: {len(gold)} novels")

    all_txt = set(os.listdir(CORPUS_DIR))
    to_run  = [(fn, os.path.join(CORPUS_DIR, fn)) for fn in gold if fn in all_txt]
    missing = [fn for fn in gold if fn not in all_txt]
    print(f"Novels in CORPUS_TOTAL: {len(to_run)}  missing: {len(missing)}")

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
