"""
Small-batch validation of the v6 prompt fixes (LOC_IDIOM self-check,
MOD_ANALOG broadened triggers, DE_PARANGON copula exclusion,
META_ATTR/META_VERB contrastive examples) before running the full 114-row
gold set. Targets 15 previously-wrong rows (concentrated in the categories
touched by the fix) + 5 previously-correct rows as a regression check.
Reuses the real production functions, does not modify them.
"""
import os, csv, sys, time
sys.path.insert(0, os.path.expanduser("~/ecopoetique/métaphore"))
from run_task2_subcategories import rule_based_classify, call_ollama, make_prompt, VALID_CODES

GOLD_FILE = os.path.expanduser("~/ecopoetique/comparison/gold_task2_task45_RB.csv")

TARGET_IDS = {
    # previously wrong, concentrated in META_ATTR/DE_PARANGON/LOC_IDIOM/META_VERB
    "8","23","28","32","36","48","57","65","68","70",
    "71","76","77","83","91",
    # previously correct, regression check
    "5","6","9","11","12",
}

def is_x(v):
    return v.strip().lower() == "x"

def main():
    with open(GOLD_FILE, encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter=";"))

    usable = [r for r in rows if r["id"] in TARGET_IDS]
    print(f"Testing {len(usable)} rows")

    correct = 0
    rule_count = llm_count = 0
    results = []
    start = time.time()

    for i, r in enumerate(usable, 1):
        token = r["token_lexique"].strip()
        ctx = r["contexte"].strip()
        cat = r.get("categorie", "").strip()
        gold = r["subcategorie_metaphore"].strip().upper()

        code = rule_based_classify(token, ctx)
        method = "rule"
        if code is None:
            code, _ = call_ollama(make_prompt(token, ctx, cat))
            method = "llm"

        is_correct = (code == gold)
        if is_correct:
            correct += 1
        if method == "rule":
            rule_count += 1
        else:
            llm_count += 1

        results.append({"id": r["id"], "fichier": r["fichier"], "token_lexique": token,
                         "gold_subcategory": gold, "predicted": code, "method": method,
                         "correct": is_correct})
        el = (time.time() - start) / 60
        print(f"  [{i}/{len(usable)}] id={r['id']} gold={gold} pred={code} "
              f"{'OK' if is_correct else 'WRONG'} correct={correct} elapsed={el:.1f}min")

    print(f"\nFinal: {correct}/{len(usable)} = {correct/len(usable)*100:.1f}%  "
          f"(rule={rule_count} llm={llm_count})")

    out = os.path.expanduser("~/ecopoetique/métaphore/resultats_task2_smallbatch_v6.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id","fichier","token_lexique","gold_subcategory","predicted","method","correct"])
        w.writeheader()
        w.writerows(results)
    print(f"Saved to: {out}")

if __name__ == "__main__":
    main()
