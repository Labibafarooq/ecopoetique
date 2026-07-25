import csv
import run_task0_mapreduce_v7_gpt4o_mini as m

gold = m.load_gold(m.GOLD_FILE)
gold_novels = set(gold.keys())
print(f"Confirmed 60-novel gold set: {len(gold_novels)} novels")
print()

CRIT = ["TYPE NARRATEUR", "FOCALISATION", "MODE NARRATIF", "REGIME NARRATIF", "ESPACE", "INTRIGUE", "TEMPORALITÉ"]
ALT_SUFFIX = {"TYPE NARRATEUR": "TYP", "FOCALISATION": "FOC", "MODE NARRATIF": "MOD",
              "REGIME NARRATIF": "REG", "ESPACE": "ESP", "INTRIGUE": "INT", "TEMPORALITÉ": "TEM"}
GOLD_ALT_KEY = {"TYPE NARRATEUR": "NAR_alt", "FOCALISATION": "FOC_alt", "MODE NARRATIF": "MOD_alt",
                "REGIME NARRATIF": "REG_alt", "ESPACE": "ESP_alt", "INTRIGUE": "INT_alt", "TEMPORALITÉ": "TEM_alt"}


def score_file(path):
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    rows60 = [r for r in rows if r["File"] in gold_novels]
    print(f"  -> {len(rows60)}/{len(rows)} rows are in the confirmed 60-novel set")
    scores = {}
    for crit in CRIT:
        c = t = 0
        for r in rows60:
            pred = r.get(crit, "").strip().upper()
            if not pred:
                continue
            g = gold[r["File"]]
            main = g[crit].strip().upper()
            alt = g.get(GOLD_ALT_KEY[crit], "").strip().upper()
            t += 1
            if pred == main or (alt and pred == alt):
                c += 1
        scores[crit] = (c, t)
    return scores


for name, path in [
    ("v3 mapreduce", "resultats_qwen3_30b_mapreduce.csv"),
    ("v7", "resultats_task0_mapreduce_v7.csv"),
    ("chunk_classifier_60novels", "resultats_chunk_classifier_60novels.csv"),
    ("hybrid.csv", "resultats_hybrid.csv"),
]:
    print(f"=== {name} ({path}) ===")
    s = score_file(path)
    tot_c = tot_t = 0
    for crit, (c, t) in s.items():
        pct = c / t * 100 if t else 0
        print(f"    {crit:<20} {c:>2}/{t:<2}  {pct:5.1f}%")
        tot_c += c
        tot_t += t
    print(f"    {'OVERALL':<20} {tot_c:>3}/{tot_t:<3}  {tot_c/tot_t*100:5.1f}%")
    print()
