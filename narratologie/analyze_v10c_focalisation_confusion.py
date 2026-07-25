"""
Confusion-matrix breakdown for v10c's FOCALISATION predictions (new scheme:
FOC_ELARG/FOC_MIXTE/FOC_REST/FOC_RFOC) against gold, run before the v10c
background run finishes (73/79 novels in at time of writing — accuracy is
stable enough at this sample size that the last few novels won't change the
diagnosis, per Labiba, so no need to wait).

Reads resultats_task0_v10c_reduce_think.csv directly (whatever's written so
far) — safe to re-run anytime, including mid-run.
"""
import csv
from collections import Counter, defaultdict

INPUT = "resultats_task0_v10c_reduce_think.csv"

with open(INPUT, encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

scored = [r for r in rows if r.get("GOLD_FOC", "").strip()]
print(f"Scored rows: {len(scored)}")

correct = sum(1 for r in scored if r["FOCALISATION"].strip() == r["GOLD_FOC"].strip())
print(f"Overall FOCALISATION accuracy: {correct}/{len(scored)} = {correct/len(scored)*100:.1f}%\n")

by_gold = defaultdict(list)
for r in scored:
    by_gold[r["GOLD_FOC"].strip()].append(r)

print("Per gold category:")
for cat, sub in sorted(by_gold.items(), key=lambda x: -len(x[1])):
    c = sum(1 for r in sub if r["FOCALISATION"].strip() == cat)
    print(f"  {cat}: {c}/{len(sub)} = {c/len(sub)*100:.1f}%")

print("\nConfusion (gold -> predicted) for wrong rows:")
conf = Counter()
for r in scored:
    gold = r["GOLD_FOC"].strip()
    pred = r["FOCALISATION"].strip()
    if pred != gold:
        conf[(gold, pred)] += 1
for (g, p), n in conf.most_common(20):
    print(f"  {g} -> {p}: {n}")

print("\nWrong rows detail (file, gold, predicted):")
for r in scored:
    if r["FOCALISATION"].strip() != r["GOLD_FOC"].strip():
        print(f"  {r['File']}: gold={r['GOLD_FOC']} pred={r['FOCALISATION']}")
