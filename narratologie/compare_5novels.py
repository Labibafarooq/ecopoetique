import csv
import run_task0_mapreduce_v8 as m

gold = m.load_gold(m.GOLD_FILE)

with open("resultats_task0_mapreduce_v8.csv", encoding="utf-8") as f:
    v8_rows = list(csv.DictReader(f))
test5_novels = set(r["File"] for r in v8_rows)
print(f"The 5 test novels: {sorted(test5_novels)}")
print()

with open("resultats_task0_mapreduce_v7.csv", encoding="utf-8") as f:
    v7_rows = [r for r in csv.DictReader(f) if r["File"] in test5_novels]

print("=== v7 (old) on these exact 5 novels ===")
m.evaluate(v7_rows, gold)

print("=== v8 (new) on these exact 5 novels ===")
m.evaluate(v8_rows, gold)
