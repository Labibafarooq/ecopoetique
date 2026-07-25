"""
Compare qwen2.5:7b against qwen3:30b on the same 20-row targeted batch used
for the v6 prompt-fix test, to get a real accuracy/speed comparison instead
of relying on an old informal judgment. Reuses the real production
rule_based_classify/make_prompt (same v6 prompt), only swaps the model name
and drops thinking-mode (qwen2.5 doesn't have it).
"""
import os, csv, sys, time, json, requests
sys.path.insert(0, os.path.expanduser("~/ecopoetique/métaphore"))
from run_task2_subcategories import rule_based_classify, make_prompt, VALID_CODES

OLLAMA_URL = "http://localhost:11435/api/chat"
MODEL = "qwen2.5:7b"
GOLD_FILE = os.path.expanduser("~/ecopoetique/comparison/gold_task2_task45_RB.csv")

TARGET_IDS = {
    "8","23","28","32","36","48","57","65","68","70",
    "71","76","77","83","91",
    "5","6","9","11","12",
}

def call_qwen25(prompt):
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"num_predict": 2000, "temperature": 0.2},
        }, timeout=300)
        content = resp.json()["message"]["content"]
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1:
            return "UNKNOWN", content[:200]
        data = json.loads(content[start:end+1])
        code = data.get("code", "UNKNOWN").strip().upper()
        if code not in VALID_CODES:
            return "UNKNOWN", content[:200]
        return code, data.get("raison", "")
    except Exception as e:
        return "ERROR", str(e)

def main():
    with open(GOLD_FILE, encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    usable = [r for r in rows if r["id"] in TARGET_IDS]
    print(f"Testing {len(usable)} rows with {MODEL}")

    correct = 0
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
            code, _ = call_qwen25(make_prompt(token, ctx, cat))
            method = "llm"

        is_correct = (code == gold)
        if is_correct:
            correct += 1
        results.append({"id": r["id"], "gold": gold, "predicted": code, "correct": is_correct})
        el = (time.time() - start) / 60
        print(f"  [{i}/{len(usable)}] id={r['id']} gold={gold} pred={code} "
              f"{'OK' if is_correct else 'WRONG'} correct={correct} elapsed={el:.1f}min")

    total_min = (time.time() - start) / 60
    print(f"\nFinal ({MODEL}): {correct}/{len(usable)} = {correct/len(usable)*100:.1f}%  "
          f"total_time={total_min:.1f}min ({total_min/len(usable)*60:.1f}s/row)")

    out = os.path.expanduser("~/ecopoetique/métaphore/resultats_task2_qwen25_7b_smallbatch.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id","gold","predicted","correct"])
        w.writeheader()
        w.writerows(results)
    print(f"Saved to: {out}")

if __name__ == "__main__":
    main()
