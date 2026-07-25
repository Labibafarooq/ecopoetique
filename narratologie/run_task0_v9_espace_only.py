#!/usr/bin/env python3
"""
run_task0_v9_espace_only.py

Labiba doesn't want the full 7-criteria v9 run right now — only ESPACE (the
"escape" criterion), which was v9's standout at 72.7% (24/33) on the
in-progress full run before it was stopped. Reuses every function from
run_task0_mapreduce_v9.py UNCHANGED (call_ollama, chunk_novel, MAP_SYSTEM,
map_prompt, extract_json, load_gold, is_correct, CRITERIA_DEFS, config
constants) per this project's standing rule to import/reuse original
functions on a re-run rather than re-describing the prompt from scratch.

The ONLY new code here is a trimmed REDUCE step that asks for ESPACE alone
instead of all 7 criteria — cuts REDUCE output/thinking budget (one field
instead of seven) so each novel is cheaper and faster, without touching the
MAP step or the ESPACE definition text (still the exact same CRITERIA_DEFS
paragraph v9 used, just extracted rather than reworded, so any accuracy
delta vs. the full-run ESPACE number is attributable to reduced prompt
scope, not a redefinition).

Usage:
  python run_task0_v9_espace_only.py --test 5
  python run_task0_v9_espace_only.py
  python run_task0_v9_espace_only.py --resume
"""

import os, csv, json, time, argparse
from collections import Counter
from datetime import datetime

from run_task0_mapreduce_v9 import (
    MODEL, CORPUS_DIR, GOLD_FILE, N_CHUNKS, MAX_LINES, TIMEOUT,
    N_REDUCE_VOTES, REDUCE_TEMPERATURE, MAP_NUM_PREDICT,
    CRITERIA_DEFS, MAP_SYSTEM, map_prompt, call_ollama, extract_json,
    chunk_novel, load_gold, is_correct,
)

OUTPUT_FILE = os.path.expanduser("~/ecopoetique/narratologie/resultats_task0_v9_espace_only.csv")

# ESPACE's REDUCE reasoning is lighter than the full 7-criteria synthesis
# (one cross-section location comparison, not seven), so a smaller budget
# than v9's 3000 is enough — kept generous margin rather than guessing tight.
REDUCE_NUM_PREDICT = 1200

# ── REDUCE PROMPT — ESPACE only ─────────────────────────────────────────────
REDUCE_SYSTEM = """Tu es un expert en narratologie française.
Réponds UNIQUEMENT avec un objet JSON. Pas de réflexion affichée, pas d'hésitation
("attends", "en fait", "non plutôt"), pas de préambule. Va directement au résultat."""

# Same ESPACE definition text as v9's CRITERIA_DEFS, extracted (not reworded).
ESPACE_DEF = """ORGANISATION DE L'ESPACE — compare les lieux mentionnés dans toutes les sections
• ESP_UNIT : même environnement général dans toutes les sections (même ville,
             bâtiment, région — même avec des sous-lieux différents).
• ESP_FRAG : lieux GÉOGRAPHIQUEMENT DISTINCTS entre sections (villes/pays/régions
             différents sans cohérence spatiale forte).
• ESP_ITIN : les personnages sont EN DÉPLACEMENT CONTINU — le voyage est central.
• ESP_IMAG : l'espace est partiellement ou totalement inventé, irréaliste, symbolique."""

def reduce_prompt(observations, filename):
    n = len(observations)
    return f"""Roman : {filename}

Observations de {n} sections (début → fin) :
{json.dumps(observations, ensure_ascii=False, indent=2)}

{ESPACE_DEF}

INSTRUCTIONS :
- Base ta décision sur L'ENSEMBLE des sections, pas une seule.
- Compare ACTIVEMENT les lieux entre les sections (ordre, cohérence géographique).
- Choisis EXACTEMENT un code.

Réponds UNIQUEMENT avec ce JSON :
{{
  "ESPACE": "ESP_UNIT ou ESP_FRAG ou ESP_ITIN ou ESP_IMAG"
}}"""

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
                done.add(row.get("File", "").strip())
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
            print(f"    chunk {idx+1}/{N_CHUNKS}: space={obs.get('space','?')}")
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
                           temperature=REDUCE_TEMPERATURE, num_predict=REDUCE_NUM_PREDICT,
                           think=True)
        try:
            votes.append(extract_json(raw))
        except Exception as e:
            print(f"    x reduce vote {v+1}/{N_REDUCE_VOTES} failed: {e}")

    if not votes:
        raise ValueError("All reduce votes failed")

    vals = [v.get("ESPACE", "").strip().upper() for v in votes if v.get("ESPACE")]
    if not vals:
        return {"ESPACE": ""}
    counts = Counter(vals)
    top_count = max(counts.values())
    winners = [v for v in vals if counts[v] == top_count]
    return {"ESPACE": winners[0]}

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test",   type=int, default=0)
    ap.add_argument("--novels", type=str, default="")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    print(f"\n{'='*62}")
    print(f"  TASK 0 — v9 ESPACE ONLY")
    print(f"  Model: {MODEL}   Chunks: {N_CHUNKS}   Reduce votes: {N_REDUCE_VOTES}")
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

    output_rows = list(existing)

    for i, (fn, fp) in enumerate(to_run, 1):
        print(f"\n[{i}/{len(to_run)}] {fn}")
        t0 = time.time()
        g = gold.get(fn, {})
        try:
            pred = process_novel(fn, fp)
            el = time.time() - t0

            ok = is_correct(pred.get("ESPACE", ""), g.get("ESPACE", ""), g.get("ESP_alt", ""))
            print(f"  -> {el:.0f}s | ESP={pred.get('ESPACE','?')}{'v' if ok else 'x'}")

            row = {"File": fn, "ESPACE": pred.get("ESPACE", ""),
                   "GOLD_ESP": g.get("ESPACE", ""), "ALT_ESP": g.get("ESP_alt", "")}
            output_rows.append(row)
            save_results(output_rows, OUTPUT_FILE)
        except Exception as e:
            print(f"  x FAILED: {e}")

    scored = [r for r in output_rows if r.get("GOLD_ESP", "").strip()]
    c = sum(1 for r in scored
            if is_correct(r["ESPACE"], r["GOLD_ESP"], r.get("ALT_ESP", "")))
    if scored:
        print(f"\n{'='*62}")
        print(f"  ESPACE: {c}/{len(scored)} = {c/len(scored)*100:.1f}%")
        print(f"{'='*62}\n")
    print(f"Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
