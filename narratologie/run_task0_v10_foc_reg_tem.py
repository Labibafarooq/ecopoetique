#!/usr/bin/env python3
"""
run_task0_v10_foc_reg_tem.py — "v10": v7 map-reduce pipeline, stripped down
to ONLY three criteria, definitions corrected to match Riccardo's canonical
definitions (compared 2026-07-08 against narratologie/
"tableau_narratif_22_08 (1).csv"). NAR/MODE/ESPACE/INTRIGUE are dropped
entirely (not just left unchanged) — this version only asks for, computes,
and scores FOCALISATION, RÉGIME NARRATIF, and TEMPORALITÉ.

1. FOCALISATION — completely new reader-vs-character-knowledge scheme:
     FOC_RFOC  : récit focalisé — reader shares the character(s)' information.
     FOC_REST  : focalisation restreinte — reader knows LESS than characters.
     FOC_ELARG : focalisation élargie — reader knows MORE than characters.
     FOC_MIXTE : structured alternation between focalization regimes across
                 distinct chapters/voices/blocks.
   Replaces the old whose-consciousness scheme (FOC_INT/EXT/ZERO/VAR).

2. RÉGIME NARRATIF — REG_AUTO tightened back to the canonical definition
   ("fondé sur l'expérience de l'auteur ou un double fictionnel"), which is
   narrower than v7's "posture subjective et réflexive constante" trigger.
   Confusion-matrix analysis (2026-07-08) found REG_REAL<->REG_AUTO as the
   single biggest RÉGIME error pair (5 of 14 errors on 60 novels) — v7's
   looser trigger over-fires AUTO on merely-introspective REAL narrators.

3. TEMPORALITÉ — TEMP_DIS's "posture rétrospective" trigger REMOVED. The
   canonical definition is "analepses ou prolepses PONCTUELLES mais
   significatives" (concrete, locatable flashback/flash-forward instances)
   and never mentions narrative stance/retrospection at all. Confusion-matrix
   analysis found 15 of 19 TEMPORALITÉ errors (79%) are the single confusion
   gold=TEMP_LIN -> predicted=TEMP_DIS — almost certainly caused by v7's
   extra retrospective-stance trigger firing on ordinary retrospective
   first-person narration that is still chronologically linear.

Scored against the new gold set: narratologie/GOLD_narratologie_0807.csv
(79 novels, includes all 60 of the original confirmed gold novels + 19 new).

Usage:
  python run_task0_v10_foc_reg_tem.py --test 5
  python run_task0_v10_foc_reg_tem.py
  python run_task0_v10_foc_reg_tem.py --resume
"""

import os, csv, json, time, re, argparse, requests
from collections import Counter
from datetime import datetime

# ── CONFIG ───────────────────────────────────────────────────────────────────
OLLAMA_URL  = "http://localhost:11435/api/chat"
MODEL       = "qwen3:30b"
CORPUS_DIR  = os.path.expanduser("~/ecopoetique/CORPUS_TOTAL")
CORPUS_DIR_FALLBACK = os.path.expanduser("~/ecopoetique/CORPUS_Bestsellers")  # 3 of the 79 new-gold novels live here instead
GOLD_FILE   = os.path.expanduser("~/ecopoetique/narratologie/GOLD_narratologie_0807.csv")
OUTPUT_FILE = os.path.expanduser("~/ecopoetique/narratologie/resultats_task0_v10b_calibrated.csv")
N_CHUNKS    = 9
MAX_LINES   = 350
MAX_CHARS_PER_CHUNK = 38000
TIMEOUT     = 300
N_REDUCE_VOTES = 3
REDUCE_TEMPERATURE = 0.4
MAP_NUM_PREDICT    = 1500
REDUCE_NUM_PREDICT = 900

# ── CRITERIA DEFINITIONS ────────────────────────────────────────────────────
# ONLY FOCALISATION, RÉGIME NARRATIF, TEMPORALITÉ — per explicit instruction,
# NAR/MODE/ESPACE/INTRIGUE dropped entirely (not just left unchanged).
CRITERIA_DEFS = """
FOCALISATION — degré d'accès du LECTEUR aux informations disponibles pour les
personnages (partage, restriction, ou excès de savoir par rapport à eux) :
• FOC_RFOC  : récit focalisé — centrage narratif sur un ou plusieurs personnages,
              avec un accès privilégié à ce qu'ils perçoivent, pensent ou savent ;
              le LECTEUR PARTAGE leur champ d'information (ni plus, ni moins).
• FOC_REST  : focalisation restreinte — le LECTEUR EN SAIT MOINS que les
              personnages ; l'accès à l'information est partiel ou différé, ce
              qui crée un effet de curiosité ou de mystère.
• FOC_ELARG : focalisation élargie — le LECTEUR EN SAIT PLUS que les
              personnages ; certaines informations sont divulguées de manière à
              permettre l'anticipation d'événements que les protagonistes
              ignorent (ironie dramatique).
              Signaux fréquents à rechercher activement (ne pas attendre une
              déclaration explicite) : le texte mentionne ce qu'un personnage
              IGNORE ou ne sait PAS encore (ex. tournures comme "sans savoir
              que...", "ignorant que...", "à son insu...") ; la narration
              bascule entre plusieurs personnages de façon à ce que le lecteur
              voie l'ensemble d'une situation qu'aucun personnage ne voit en
              entier ; un événement est raconté ou annoncé au lecteur avant
              qu'un personnage n'en apprenne l'existence dans l'histoire.
              Ne PAS se limiter au seul cas où un narrateur omniscient
              l'affirme explicitement — l'ironie dramatique est souvent
              implicite.
• FOC_MIXTE : alternance STRUCTURÉE de plusieurs régimes de focalisation dans
              des séquences distinctes (chapitres, voix, blocs narratifs) —
              PAS un mélange local dans une même scène, mais un changement de
              régime clairement délimité par section/chapitre.

RÉGIME NARRATIF — vérifie dans cet ordre, en te basant sur L'ENSEMBLE des sections
1. Des éléments surnaturels ou étranges perturbent-ils le réel dans un cadre par
   ailleurs réaliste, de façon récurrente à travers plusieurs sections ? → REG_FANT
   (Un narrateur ou personnage focal non-humain/à la conscience non-conventionnelle
   — animal, objet, entité collective — est un signal SUPPLÉMENTAIRE utile pour
   REG_FANT quand il s'accompagne d'autres éléments étranges, mais n'est PAS
   suffisant à lui seul si le monde décrit reste par ailleurs parfaitement réaliste.)
2. Sinon, le monde présente-t-il DES INDICES, même partiels, d'une transformation
   futuriste, dystopique, ou politique/technologique par rapport au réel actuel
   (ex. une technologie inédite, un régime politique inventé, une chronologie
   légèrement décalée dans le futur) ? → REG_SPEC (pas besoin que TOUT le monde
   soit transformé, un cadre par ailleurs réaliste avec quelques altérations
   marquées suffit)
3. Sinon, AU MOINS UNE section fournit-elle une indication concrète (même
   implicite) d'un lien entre le récit et la vie réelle de l'auteur — référence
   explicite (à l'écriture du livre, à l'identité/au nom de l'auteur) OU
   ressemblance biographique nette (âge, parcours, entourage identifiables) —
   ET aucune autre section ne contredit clairement ce lien ? → REG_AUTO
   ⚠ Un ton confessionnel/introspectif SEUL, sans AUCUNE indication concrète nulle
     part dans le texte, NE SUFFIT PAS pour REG_AUTO. Mais une seule section
     avec une indication claire et non contredite SUFFIT — pas besoin que
     plusieurs sections le répètent.
4. Sinon → REG_REAL

TEMPORALITÉ — compare les repères temporels (time_position_marker) des sections DANS
L'ORDRE (section 1 → section {n_chunks})
• TEMP_LIN    : la narration suit PRINCIPALEMENT l'ordre réel/chronologique des
                événements. ⚠ Le simple fait que le narrateur raconte après coup
                (posture rétrospective, narration_stance=retrospective_reflection)
                NE SUFFIT PAS à sortir de TEMP_LIN — un narrateur peut raconter son
                histoire des années plus tard tout en la racontant dans l'ordre où
                elle s'est déroulée. Regarde l'ORDRE DES ÉVÉNEMENTS RACONTÉS, pas le
                moment depuis lequel le narrateur parle.
• TEMP_DIS    : présence de retours en arrière ou d'anticipations MODÉRÉES mais
                significatives. Déclencheurs suffisants : un ou plusieurs retours
                en arrière/anticipations concrets et localisables
                (flashback_or_jump_in_section=yes dans au moins une section, ou un
                repère temporel plus tardif apparaissant avant un repère plus
                précoce) ; OU plusieurs sections en narration_stance=
                retrospective_reflection DONT les repères temporels eux-mêmes ne
                progressent pas clairement de façon linéaire d'une section à
                l'autre (la posture rétrospective seule, avec des repères qui
                progressent normalement, reste TEMP_LIN — voir ci-dessus). Sans
                que la chronologie devienne totalement illisible.
• TEMP_DESORD : la chronologie est impossible à reconstituer de façon cohérente à
                partir des repères temporels donnés dans la majorité des sections
                (structure éclatée, nombreux déplacements temporels non hiérarchisés).
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
  "pov_chapter_marker": "yes OU no (cette section est-elle explicitement attribuée à un personnage précis, ex: titre de chapitre nommé, changement de voix marqué ?)",
  "reader_vs_character_knowledge": "same_as_characters (le lecteur sait ce que les personnages savent, ni plus ni moins) OU less_than_characters (des informations sont cachées/différées au lecteur, effet de mystère) OU more_than_characters (le lecteur voit/sait des choses que les personnages ignorent, ironie dramatique)",
  "world_type": "realistic OU autobiographical_explicit OU fantastic OU speculative_sf",
  "narrator_entity": "human OU non_human_or_unconventional (ex: animal, objet, entité collective)",
  "autobiographical_signal": "none OU implicit_confessional_tone OU explicit_author_reference",
  "time_position_marker": "tout repère temporel explicite/implicite dans CETTE section (âge, date, saison, avant/après un événement...), ou 'none'",
  "narration_stance": "in_scene OU retrospective_reflection",
  "flashback_or_jump_in_section": "yes OU no (un saut temporel DANS cet extrait même)"
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
- Pour FOCALISATION : regarde reader_vs_character_knowledge à travers TOUTES les
  sections. Si AU MOINS UNE section montre clairement more_than_characters (le
  lecteur sait/voit quelque chose qu'un personnage ignore à ce moment) et que
  cela n'est pas contredit ailleurs → penche vers FOC_ELARG, même si d'autres
  sections sont same_as_characters (l'ironie dramatique n'a pas besoin d'être
  présente dans une majorité de sections pour être la caractéristique dominante
  du récit). Sinon, si la MAJORITÉ des sections indiquent la même valeur →
  utilise-la (same_as_characters → FOC_RFOC, less_than_characters → FOC_REST).
  Si PLUSIEURS sections ont pov_chapter_marker=yes ET que reader_vs_character_
  knowledge change de façon structurée d'une section attribuée à l'autre (pas
  juste du bruit ponctuel) → FOC_MIXTE.
- Pour TEMPORALITÉ : compare l'ORDRE DES ÉVÉNEMENTS entre sections. Un flashback/
  saut concret et localisable (flashback_or_jump_in_section=yes) ou une
  contradiction d'ordre entre repères temporels précis suffit pour TEMP_DIS. Une
  narration rétrospective SEULE (narration_stance=retrospective_reflection) qui
  raconte les événements dans l'ordre chronologique reste TEMP_LIN — mais si
  PLUSIEURS sections sont rétrospectives ET que leurs repères temporels ne
  progressent pas clairement de façon linéaire entre elles, penche vers TEMP_DIS.
- Pour RÉGIME NARRATIF : REG_AUTO ne demande PAS que plusieurs sections répètent
  le lien à l'auteur — UNE SEULE section avec une indication concrète et non
  contredite ailleurs suffit. FANT et SPEC acceptent aussi des indices partiels,
  pas besoin que la totalité du monde soit transformée.
- Choisis EXACTEMENT un code par critère.

Réponds UNIQUEMENT avec ce JSON :
{{
  "FOCALISATION":    "FOC_RFOC ou FOC_REST ou FOC_ELARG ou FOC_MIXTE",
  "REGIME NARRATIF": "REG_AUTO ou REG_REAL ou REG_FANT ou REG_SPEC",
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
        "think": False,
        "format": "json",
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

# ── GOLD LOADING (new 0807 file — same column layout as the old gold file) ───
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
    ("FOCALISATION",    "FOC_alt"),
    ("REGIME NARRATIF", "REG_alt"),
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
    print(f"  FOCALISATION-NEW-SCHEME RESULTS  —  {MODEL}  ({N_REDUCE_VOTES}x reduce vote)")
    print("="*62)
    for crit, (c, t) in scores.items():
        if t:
            acc = c/t*100
            bar = "█" * int(acc/5)
            marker = "  <-- NEW SCHEME" if crit == "FOCALISATION" else ""
            print(f"  {crit:<22} {c:>2}/{t:<2}  ({acc:>5.1f}%)  {bar}{marker}")
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
                  f"know={str(obs.get('reader_vs_character_knowledge','?'))[:20]} "
                  f"chmark={obs.get('pov_chapter_marker','?')}")
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
        final[crit] = winners[0]
    return final

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test",   type=int, default=0)
    ap.add_argument("--novels", type=str, default="")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    print(f"\n{'='*62}")
    print(f"  TASK 0 — FOCALISATION NEW SCHEME (v7 base, FOC replaced only)")
    print(f"  Model: {MODEL}   Chunks: {N_CHUNKS}   Max lines/chunk: {MAX_LINES}   Reduce votes: {N_REDUCE_VOTES}")
    print(f"  Gold: {GOLD_FILE}")
    print(f"  Started: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"{'='*62}\n")

    gold = load_gold(GOLD_FILE)
    print(f"Gold: {len(gold)} novels")

    all_txt = set(os.listdir(CORPUS_DIR))
    fallback_txt = set(os.listdir(CORPUS_DIR_FALLBACK)) if os.path.isdir(CORPUS_DIR_FALLBACK) else set()
    to_run = []
    missing = []
    n_fallback = 0
    for fn in gold:
        if fn in all_txt:
            to_run.append((fn, os.path.join(CORPUS_DIR, fn)))
        elif fn in fallback_txt:
            to_run.append((fn, os.path.join(CORPUS_DIR_FALLBACK, fn)))
            n_fallback += 1
        else:
            missing.append(fn)
    print(f"Novels in CORPUS_TOTAL: {len(to_run)-n_fallback}  in CORPUS_Bestsellers: {n_fallback}  missing entirely: {len(missing)}")

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
                  f"FOC={pred.get('FOCALISATION','?')}{chk('FOCALISATION','FOC_alt')} "
                  f"REG={pred.get('REGIME NARRATIF','?')}{chk('REGIME NARRATIF','REG_alt')} "
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
