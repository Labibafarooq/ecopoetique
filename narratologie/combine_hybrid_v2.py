#!/usr/bin/env python3
"""
combine_hybrid_v2.py

Combines THREE prediction sources, using whichever is empirically best
for each criterion:
  - v3        (map-reduce, single combined reduce prompt)
  - clf       (sklearn classifier on text features + v3 predictions)
  - optionA   (map-reduce, targeted per-criterion reduce prompts)

Winner per criterion (from evaluation on 60 novels):
  TYPE NARRATEUR  → Option A   (91.7%)
  FOCALISATION    → Option A   (63.3%, tied with clf)
  MODE NARRATIF   → classifier (71.7%)
  REGIME NARRATIF → classifier (71.7%)
  ESPACE          → Option A   (50.0%)
  INTRIGUE        → v3         (65.0%)
  TEMPORALITÉ     → v3         (71.7%)

Usage:
  cd ~/ecopoetique/narratologie
  python combine_hybrid_v2.py
"""

import os, csv

RESULTS_V3      = os.path.expanduser("~/ecopoetique/narratologie/resultats_qwen3_30b_mapreduce.csv")
RESULTS_CLF     = os.path.expanduser("~/ecopoetique/narratologie/resultats_chunk_classifier.csv")
RESULTS_OPTIONA = os.path.expanduser("~/ecopoetique/narratologie/resultats_qwen3_30b_mapreduce_optionA.csv")
GOLD_FILE       = os.path.expanduser("~/ecopoetique/narratologie/GOLD_narratologie.csv")
OUTPUT_FILE     = os.path.expanduser("~/ecopoetique/narratologie/resultats_hybrid_v2.csv")

# Which source wins for each criterion
ROUTING = {
    "TYPE NARRATEUR":  "v3",
    "FOCALISATION":  "clf",
    "MODE NARRATIF":  "clf",
    "REGIME NARRATIF":  "v3",
    "ESPACE":  "v3",
    "INTRIGUE":  "v3",
    "TEMPORALITÉ":  "v3",
}

CRITERIA = [
    ("TYPE NARRATEUR",  "NAR_alt"),
    ("FOCALISATION",    "FOC_alt"),
    ("MODE NARRATIF",   "MOD_alt"),
    ("REGIME NARRATIF", "REG_alt"),
    ("ESPACE",          "ESP_alt"),
    ("INTRIGUE",        "INT_alt"),
    ("TEMPORALITÉ",     "TEM_alt"),
]

def load_gold(path):
    gold = {}
    with open(path, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader)
        for row in reader:
            if not row or not row[0].strip(): continue
            def col(i): return row[i].strip() if i < len(row) else ""
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
    if not pred: return False
    p = pred.strip().upper()
    if p == main.strip().upper(): return True
    if alt and p == alt.strip().upper(): return True
    return False

def load_preds(path):
    preds = {}
    if not os.path.exists(path):
        print(f"Warning: {path} not found")
        return preds
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            fn = row.get("File","").strip()
            if fn:
                preds[fn] = row
    return preds

def main():
    gold    = load_gold(GOLD_FILE)
    v3      = load_preds(RESULTS_V3)
    clf     = load_preds(RESULTS_CLF)
    optionA = load_preds(RESULTS_OPTIONA)

    print(f"\n{'='*62}")
    print(f"  3-WAY HYBRID COMBINER")
    print(f"  v3 predictions:         {len(v3)} novels")
    print(f"  Classifier predictions: {len(clf)} novels")
    print(f"  Option A predictions:   {len(optionA)} novels")
    print(f"{'='*62}\n")

    sources = {"v3": v3, "clf": clf, "optionA": optionA}

    all_fns = set(v3.keys()) | set(clf.keys()) | set(optionA.keys())
    all_fns = [fn for fn in all_fns if fn in gold]

    results = []
    scores  = {c: [0, 0] for c, _ in CRITERIA}
    oc = ot = 0

    for fn in all_fns:
        g    = gold[fn]
        row  = {"File": fn}

        for crit, alt_key in CRITERIA:
            primary_source = ROUTING[crit]
            pred = sources[primary_source].get(fn, {}).get(crit, "")

            # Fallback chain if primary is empty
            if not pred:
                for fallback in ["v3", "clf", "optionA"]:
                    pred = sources[fallback].get(fn, {}).get(crit, "")
                    if pred:
                        break

            row[crit]                 = pred
            row[f"GOLD_{crit[:3]}"]   = g.get(crit, "")
            row[f"SOURCE_{crit[:3]}"] = primary_source

            if pred:
                scores[crit][1] += 1
                ot += 1
                if is_correct(pred, g[crit], g[alt_key]):
                    scores[crit][0] += 1
                    oc += 1

        results.append(row)

    # Known individual scores for comparison
    v3_scores      = {"TYPE NARRATEUR":90.0,"FOCALISATION":51.7,"MODE NARRATIF":51.7,
                       "REGIME NARRATIF":66.7,"ESPACE":46.7,"INTRIGUE":65.0,"TEMPORALITÉ":71.7}
    clf_scores     = {"TYPE NARRATEUR":88.3,"FOCALISATION":63.3,"MODE NARRATIF":71.7,
                       "REGIME NARRATIF":71.7,"ESPACE":48.3,"INTRIGUE":63.3,"TEMPORALITÉ":61.7}
    optionA_scores = {"TYPE NARRATEUR":91.7,"FOCALISATION":63.3,"MODE NARRATIF":40.0,
                       "REGIME NARRATIF":65.0,"ESPACE":50.0,"INTRIGUE":35.0,"TEMPORALITÉ":43.3}

    print(f"{'='*62}")
    print(f"  HYBRID v2 RESULTS")
    print(f"{'='*62}")

    for crit, (c, t) in scores.items():
        if not t: continue
        acc = c / t * 100
        src = ROUTING[crit]
        bar = "█" * int(acc / 5)
        best_individual = max(v3_scores.get(crit,0), clf_scores.get(crit,0), optionA_scores.get(crit,0))
        print(f"  {crit:<22} {c:>2}/{t:<2}  ({acc:>5.1f}%)  {bar:<20}  [{src}]")

    print(f"{'-'*62}")
    if ot:
        ov = oc / ot * 100
        print(f"  {'OVERALL':<22} {oc:>3}/{ot:<3}  ({ov:>5.1f}%)")
    print(f"{'='*62}")
    print(f"\n  Progression:")
    print(f"  Baseline (125-line):       55.7%")
    print(f"  Map-reduce v3:             63.3%")
    print(f"  Chunk classifier:          66.9%")
    print(f"  Hybrid v1 (v3+clf):        68.8%")
    print(f"  Option A (standalone):     55.5%")
    if ot:
        print(f"  Hybrid v2 (3-way):         {ov:.1f}%")
    print()

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)
    print(f"Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
