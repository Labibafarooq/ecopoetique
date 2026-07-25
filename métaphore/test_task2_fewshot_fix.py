"""Targeted smoke test of the few-shot/ordering fix (META_ATTR<->LOC_IDIOM,
DE_PARANGON vs DE_PROP/META_APP/COMME_SN) on the exact rows that were
misclassified because of these confusions, before relaunching the full
114-row gold run."""
import csv, os, sys
sys.path.insert(0, os.path.expanduser("~/ecopoetique/métaphore"))
from run_task2_subcategories import rule_based_classify, call_ollama, make_prompt

GOLD_FILE = os.path.expanduser("~/ecopoetique/comparison/gold_task2_task45_RB.csv")
TEST_IDS = {"32", "57", "62", "83", "90", "102", "123", "128", "149", "200"}

with open(GOLD_FILE, encoding="utf-8") as f:
    rows = list(csv.DictReader(f, delimiter=";"))

for r in rows:
    if r.get("id", "").strip() not in TEST_IDS:
        continue
    token = r["token_lexique"].strip()
    ctx = r["contexte"].strip()
    cat = r.get("categorie", "").strip()
    gold = r["subcategorie_metaphore"].strip().upper()

    code = rule_based_classify(token, ctx)
    method = "rule"
    if code is None:
        code, _ = call_ollama(make_prompt(token, ctx, cat))
        method = "llm"

    ok = "OK " if code == gold else "FAIL"
    print(f"[{ok}] id={r['id']} token={token} gold={gold} pred={code} ({method})")
