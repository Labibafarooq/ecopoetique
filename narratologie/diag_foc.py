import csv
import run_task0_mapreduce_v8 as m

gold = m.load_gold(m.GOLD_FILE)
with open("resultats_task0_mapreduce_v8.csv", encoding="utf-8") as f:
    v8 = list(csv.DictReader(f))
with open("resultats_task0_mapreduce_v7.csv", encoding="utf-8") as f:
    v7 = {r["File"]: r for r in csv.DictReader(f)}

for r in v8:
    fn = r["File"]
    g = gold.get(fn, {})
    v7r = v7.get(fn, {})
    print(fn)
    print(f"   gold FOC = {g.get('FOCALISATION')}  alt = {g.get('FOC_alt')}")
    print(f"   v8   FOC = {r.get('FOCALISATION')}")
    print(f"   v7(old) FOC = {v7r.get('FOCALISATION', '(not in v7 results)')}")
