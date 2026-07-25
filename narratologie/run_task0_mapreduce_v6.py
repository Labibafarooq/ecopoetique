#!/usr/bin/env python3
"""
run_task0_mapreduce_v6.py  —  mapreduce architecture + v6 rules

Why this script exists: v5/v6 (run_task0_v6.py) put all chunks + reasoning +
synthesis into ONE call, and that architecture only ever won NAR/FOC — ESP,
INTRIGUE, TEMPORALITÉ stayed flat versus the older mapreduce_v3 pipeline
(resultats_qwen3_30b_mapreduce.csv), which separates "observe each chunk"
(MAP, one small call per chunk) from "synthesize across all chunks" (REDUCE,
one call given compact structured tags, not raw text). That separation is
almost certainly why mapreduce_v3 wins the structural/whole-book categories.

Changes vs v3 (run_narratologie_mapreduce.py):
  1. MAP and REDUCE definitions upgraded to v6's refined French rules —
     especially the FOC_ZERO vs FOC_INT/VAR disambiguation that took FOC_ZERO
     from 6% -> 56% correct in v6, the MOD_INTR strictness rule, and the
     counting-based TEMPORALITÉ thresholds. v3's MAP stage previously had no
     access to these rules at all (each chunk was tagged using vague English
     categories), so chunk-level tags themselves should improve, not just the
     final synthesis.
  2. Added a "pov_chapter_marker" tag per chunk — directly operationalizes
     v6's discovery that FOC_VAR requires STRUCTURALLY named POV chapters,
     not just alternating consciousness.
  3. Added a confidence score (1-5) per chunk observation, anchored with
     concrete examples (per LLM×MapReduce's in-context calibration approach),
     and the REDUCE prompt is instructed to weight low-confidence chunks less
     when chunks disagree.
  4. Self-consistency: REDUCE runs 3x at temperature 0.4 (MAP stays temp=0,
     since per-chunk observation is closer to factual extraction than
     judgment call — only REDUCE concentrates the ambiguous synthesis step).
     Final label per criterion = majority vote across the 3 reduce runs;
     ties broken by the first (lowest-index) run.
  5. think:false applied properly at the API level (root-caused in v6: the
     "/no_think" text trick doesn't disable qwen3's native thinking via
     Ollama's chat API — confirmed via direct API test, done_reason="length"
     with the whole token budget burned on an unfinished <think> block).
  6. Kept v3's robust balanced-brace JSON extractor (handles multiple objects
     and thinking-text noise better than v6's single-level regex).
  7. N_CHUNKS kept at 9 (v3's proven value) deliberately NOT changed alongside
     everything else, so any accuracy delta can be attributed to the rule/
     confidence/voting changes rather than conflated with a chunk-count change.

Usage:
  python run_task0_mapreduce_v6.py --test 5
  python run_task0_mapreduce_v6.py
  python run_task0_mapreduce_v6.py --resume
"""

import os, csv, json, time, re, argparse, requests
from collections import Counter
from datetime import datetime

# ── CONFIG ───────────────────────────────────────────────────────────────────
OLLAMA_URL  = "http://localhost:11435/api/chat"
MODEL       = "qwen3:30b"
CORPUS_DIR  = os.path.expanduser("~/ecopoetique/CORPUS_TOTAL")
GOLD_FILE   = os.path.expanduser("~/ecopoetique/narratologie/GOLD_narratologie.csv")
OUTPUT_FILE = os.path.expanduser("~/ecopoetique/narratologie/resultats_task0_mapreduce_v6.csv")
N_CHUNKS    = 9
MAX_LINES   = 400
TIMEOUT     = 300
N_REDUCE_VOTES = 3
REDUCE_TEMPERATURE = 0.4

# ── CRITERIA DEFINITIONS (v6's refined French rules) ───────────────────────────
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

RÉGIME NARRATIF — vérifie dans cet ordre
1. Éléments surnaturels, inexplicables ou symboliques perturbant le réel ? → REG_FANT
2. Monde clairement futuriste, dystopique, politiquement modifié ? → REG_SPEC
3. Le narrateur parle-t-il EXPLICITEMENT de sa propre vie d'auteur / posture
   autobiographique (≠ simple narration à la 1ère personne) ? → REG_AUTO
4. Sinon → REG_REAL

ORGANISATION DE L'ESPACE — compare les lieux mentionnés dans toutes les sections
• ESP_UNIT : même environnement général dans toutes les sections (même ville,
             bâtiment, région — même avec des sous-lieux différents).
• ESP_FRAG : lieux GÉOGRAPHIQUEMENT DISTINCTS entre sections (villes/pays/régions
             différents sans cohérence spatiale forte).
• ESP_ITIN : les personnages sont EN DÉPLACEMENT CONTINU — le voyage est central.
• ESP_IMAG : l'espace est partiellement ou totalement inventé, irréaliste, symbolique.

NATURE DE L'INTRIGUE — les événements des sections se causent-ils les uns les autres ?
• INTR_LIN  : les sections s'enchaînent causalement (A cause B qui cause C),
              progression narrative logique du début à la fin.
• INTR_FRAG : les sections semblent JUXTAPOSÉES sans lien causal fort entre elles.
• INTR_CYC  : des motifs/situations/scènes se RÉPÈTENT de manière structurante —
              la section finale ressemble à la section initiale.

TEMPORALITÉ — COMPTE combien de sections sur {n_chunks} ont anachrony_present=yes
• TEMP_LIN    : anachronies dans 0 à 2 sections sur {n_chunks}. Flux chronologique dominant.
• TEMP_DIS    : anachronies dans 3 à 6 sections sur {n_chunks}. Fréquentes mais structurées.
• TEMP_DESORD : anachronies dans 7 sections ou plus sur {n_chunks}, OU chronologie
                impossible à reconstituer.
"""

# ── MAP PROMPT ────────────────────────────────────────────────────────────────
MAP_SYSTEM = """Tu es un analyste littéraire expert en narratologie française.
Réponds UNIQUEMENT avec un objet JSON. Pas d'explication, pas de préambule."""

def map_prompt(chunk_text, chunk_index, total_chunks):
    pos = ("DÉBUT"    if chunk_index == 0 else
           "FIN"       if chunk_index == total_chunks - 1 else
           f"MILIEU section {chunk_index+1}/{total_chunks}")
    return f"""Analyse cet extrait ({pos}) d'un roman français.

--- EXTRAIT ---
{chunk_text[:6000]}
--- FIN EXTRAIT ---

DÉFINITIONS DE RÉFÉRENCE :
{CRITERIA_DEFS.format(n_chunks=total_chunks)}

Réponds UNIQUEMENT avec ce JSON (remplace les ... par tes observations sur CET extrait) :
{{
  "chunk": {chunk_index + 1},
  "position": "{pos}",
  "narrator_voice": "first_person OU third_person OU unclear",
  "narrator_role": "protagonist OU witness OU not_applicable",
  "inner_thoughts": "none OU one_character OU multiple_characters",
  "pov_chapter_marker": "yes OU no",
  "dominant_mode": "action_events OU description OU introspection OU mixed",
  "world_type": "realistic OU autobiographical_explicit OU fantastic OU speculative_sf",
  "space": "single_location OU multiple_locations OU journey_travel OU imaginary",
  "plot_causality": "events_causally_linked OU juxtaposed_no_strong_link OU repeats_earlier_motif",
  "anachrony_present": "yes OU no",
  "confidence": "1 à 5 (1=très incertain, 5=évident sans ambiguïté)",
  "key_observation": "une phrase"
}}"""

# ── REDUCE PROMPT ─────────────────────────────────────────────────────────────
REDUCE_SYSTEM = """Tu es un expert en narratologie française.
Réponds UNIQUEMENT avec un objet JSON. Pas de réflexion affichée, pas d'hésitation
("attends", "en fait", "non plutôt"), pas de préambule. Va directement au résultat."""

def reduce_prompt(observations, filename):
    n = len(observations)
    return f"""Roman : {filename}

Observations de {n} sections (début → fin), chacune avec un score de confiance (1-5) :
{json.dumps(observations, ensure_ascii=False, indent=2)}

{CRITERIA_DEFS.format(n_chunks=n)}

INSTRUCTIONS :
- Base ta décision sur L'ENSEMBLE des sections, pas une seule.
- Pour ESPACE, INTRIGUE et TEMPORALITÉ : compare ACTIVEMENT les sections entre elles.
- Si les sections sont en désaccord, pèse davantage celles avec confidence=4 ou 5,
  et moins celles avec confidence=1 ou 2 (signal faible/ambigu).
- Pour TEMPORALITÉ : compte le nombre de sections avec anachrony_present=yes parmi
  les {n} sections et applique le seuil exact (voir définitions ci-dessus).
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
def call_ollama(system_msg, user_msg, temperature=0.0):
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": user_msg},
        ],
        "stream": False,
        "think": False,   # real API-level thinking disable (text "/no_think" tricks don't work)
        "options": {
            "temperature": temperature,
            "num_ctx": 16384,
            "num_predict": 5000,
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
    print(f"  MAP-REDUCE v6 RESULTS  —  {MODEL}  ({N_REDUCE_VOTES}x reduce vote)")
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
            raw = call_ollama(MAP_SYSTEM, map_prompt(text, idx, N_CHUNKS), temperature=0.0)
            obs = extract_json(raw)
            observations.append(obs)
            print(f"    chunk {idx+1}/{N_CHUNKS}: "
                  f"voice={obs.get('narrator_voice','?')[:12]} "
                  f"mode={obs.get('dominant_mode','?')[:12]} "
                  f"conf={obs.get('confidence','?')}")
        except Exception as e:
            print(f"    x chunk {idx+1}/{N_CHUNKS} failed: {e}")
            observations.append({"chunk": idx+1, "error": str(e)})

    good = [o for o in observations if "error" not in o]
    if not good:
        raise ValueError(f"All {N_CHUNKS} chunks failed — no usable observations")

    print(f"    -> reduce step x{N_REDUCE_VOTES} ({len(good)}/{N_CHUNKS} good observations)")
    votes = []
    for v in range(N_REDUCE_VOTES):
        raw = call_ollama(REDUCE_SYSTEM, reduce_prompt(good, filename), temperature=REDUCE_TEMPERATURE)
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
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    print(f"\n{'='*62}")
    print(f"  TASK 0 MAP-REDUCE v6  (v3 architecture + v6 rules)")
    print(f"  Model: {MODEL}   Chunks: {N_CHUNKS}   Reduce votes: {N_REDUCE_VOTES}")
    print(f"  Started: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"{'='*62}\n")

    gold = load_gold(GOLD_FILE)
    print(f"Gold: {len(gold)} novels")

    all_txt = set(os.listdir(CORPUS_DIR))
    to_run  = [(fn, os.path.join(CORPUS_DIR, fn)) for fn in gold if fn in all_txt]
    missing = [fn for fn in gold if fn not in all_txt]
    print(f"Novels in CORPUS_TOTAL: {len(to_run)}  missing: {len(missing)}")

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
