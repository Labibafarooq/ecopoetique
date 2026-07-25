#!/usr/bin/env python3
"""
Analyze where map-reduce went wrong, criterion by criterion.
Run this locally to understand error patterns before building Option A.
"""
import csv

RESULTS = "/home/lfarooq/ecopoetique/narratologie/resultats_qwen3_30b_mapreduce.csv"
GOLD    = "/home/lfarooq/ecopoetique/narratologie/GOLD_narratologie.csv"

# Load gold by fixed column index
gold = {}
with open(GOLD, encoding="utf-8") as f:
    reader = csv.reader(f, delimiter="\t")
    next(reader)
    for row in reader:
        if not row or not row[0].strip():
            continue
        def col(i): return row[i].strip() if i < len(row) else ""
        gold[col(0)] = {
            "TYPE NARRATEUR":  col(4),  "NAR_alt": col(5),
            "FOCALISATION":    col(6),  "FOC_alt": col(7),
            "MODE NARRATIF":   col(8),  "MOD_alt": col(9),
            "REGIME NARRATIF": col(10), "REG_alt": col(11),
            "ESPACE":          col(12), "ESP_alt": col(13),
            "INTRIGUE":        col(14), "INT_alt": col(15),
            "TEMPORALITÉ":     col(16), "TEM_alt": col(17),
        }

def is_correct(pred, main, alt=""):
    if not pred: return False
    p = pred.strip().upper()
    if p == main.strip().upper(): return True
    if alt and p == alt.strip().upper(): return True
    return False

CRITERIA = [
    ("FOCALISATION",    "FOC_alt"),
    ("ESPACE",          "ESP_alt"),
    ("MODE NARRATIF",   "MOD_alt"),
    ("REGIME NARRATIF", "REG_alt"),
    ("INTRIGUE",        "INT_alt"),
    ("TEMPORALITÉ",     "TEM_alt"),
]

# Load results
results = []
with open(RESULTS, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row.get("File") and not row.get("ERROR"):
            results.append(row)

print(f"Loaded {len(results)} results\n")

# Per-criterion confusion matrix
for crit, alt_key in CRITERIA:
    errors = []
    confusion = {}  # gold -> predicted
    correct = total = 0
    for r in results:
        fn = r["File"]
        if fn not in gold: continue
        g = gold[fn]
        pred = r.get(crit, "").strip()
        if not pred: continue
        total += 1
        gold_label = g[crit]
        if is_correct(pred, gold_label, g[alt_key]):
            correct += 1
        else:
            errors.append((fn, gold_label, pred))
            key = f"{gold_label} → {pred}"
            confusion[key] = confusion.get(key, 0) + 1

    print(f"{'='*55}")
    print(f"{crit}: {correct}/{total} ({correct/total*100:.1f}%)")
    print(f"{'='*55}")
    
    # Most common confusions
    sorted_conf = sorted(confusion.items(), key=lambda x: -x[1])
    print("Most common errors (gold → predicted):")
    for k, v in sorted_conf[:8]:
        print(f"  {v:>2}x  {k}")
    print()
