"""
Validate run_task2_subcategories.py's classification logic (rule-based +
fixed LLM fallback) against the 114 usable gold-annotated rows in
comparison/gold_task2_task45_RB.csv (excludes X-marked/wrongly-classified rows).
Does not touch the full 23,327-row corpus file — gold-only validation.
"""
import os, csv, sys, time
sys.path.insert(0, os.path.expanduser("~/ecopoetique/métaphore"))
from run_task2_subcategories import rule_based_classify, call_ollama, make_prompt, VALID_CODES

GOLD_FILE = os.path.expanduser("~/ecopoetique/comparison/gold_task2_task45_RB.csv")
OUTPUT_FILE = os.path.expanduser("~/ecopoetique/métaphore/resultats_task2_gold_validation.csv")

def is_x(v):
    return v.strip().lower() == "x"

def main():
    with open(GOLD_FILE, encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter=";"))

    # META_JUXT eliminated 2026-07-10 per Riccardo — fold any gold rows still
    # labeled META_JUXT into META_APP before filtering/scoring.
    for r in rows:
        if r["subcategorie_metaphore"].strip().upper() == "META_JUXT":
            r["subcategorie_metaphore"] = "META_APP"

    usable = [r for r in rows if r["subcategorie_metaphore"].strip() in VALID_CODES
              and not is_x(r["subcategorie_metaphore"])]
    print(f"Usable gold rows: {len(usable)}")

    done_ids = set()
    correct_done = 0
    write_header = True
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            existing = list(csv.DictReader(f))
        done_ids = {r["id"] for r in existing}
        correct_done = sum(1 for r in existing if r.get("correct", "").strip() == "True")
        write_header = len(existing) == 0
        if done_ids:
            print(f"Resuming: {len(done_ids)} already done ({correct_done} correct)")

    usable = [r for r in usable if r.get("id", "") not in done_ids]
    print(f"Remaining: {len(usable)}")

    fields = ["id", "fichier", "token_lexique", "gold_subcategory", "predicted", "method", "correct"]
    out_f = open(OUTPUT_FILE, "a", newline="", encoding="utf-8")
    writer = csv.DictWriter(out_f, fieldnames=fields)
    if write_header:
        writer.writeheader()

    correct = correct_done
    rule_count = llm_count = 0
    total_base = len(done_ids)
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

        ok = (code == gold)
        correct += ok
        if method == "rule": rule_count += 1
        else: llm_count += 1

        writer.writerow({
            "id": r.get("id", ""), "fichier": r.get("fichier", ""),
            "token_lexique": token, "gold_subcategory": gold,
            "predicted": code, "method": method, "correct": ok,
        })
        out_f.flush()

        if i % 10 == 0 or i == len(usable):
            elapsed = time.time() - start
            seen = total_base + i
            print(f"  [{i}/{len(usable)} this run, {seen} total] correct={correct} ({correct/seen*100:.1f}%) "
                  f"rule={rule_count} llm={llm_count} elapsed={elapsed/60:.1f}min")

    out_f.close()
    total = total_base + len(usable)
    print(f"\nFinal: {correct}/{total} = {correct/total*100:.1f}%")
    print(f"Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
