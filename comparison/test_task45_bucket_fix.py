"""Quick targeted test of the Bucket 1 (voice/chant) and Bucket 2 (idiom/
rhetorical cible) prompt fix on the specific rows that were misclassified
because of them, before relaunching the full gold run."""
import csv, os, sys
sys.path.insert(0, os.path.expanduser("~/ecopoetique/comparison"))
from run_task45_compare_category import make_prompt, call_ollama

GOLD_FILE = os.path.expanduser("~/ecopoetique/comparison/gold_task2_task45_RB.csv")
TEST_IDS = {"45", "121", "23", "75", "81", "135", "169"}

with open(GOLD_FILE, encoding="utf-8") as f:
    rows = list(csv.DictReader(f, delimiter=";"))

for r in rows:
    if r.get("id", "").strip() not in TEST_IDS:
        continue
    token = r["token_lexique"].strip()
    ctx = r["contexte"].strip()
    subcat = r.get("subcategorie_metaphore", "").strip()
    gold = r["categorie_compare"].strip().upper()

    code, raison = call_ollama(make_prompt(token, ctx, subcat))
    ok = "OK " if code == gold else "FAIL"
    print(f"[{ok}] id={r['id']} token={token} gold={gold} pred={code}")
    print(f"       {raison}\n")
