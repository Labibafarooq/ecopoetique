"""
Task 1 — Literal/Figurative Evaluation
Compares GPT-4o-mini (Johanna's system) vs qwen3:30b (our system)
against the human gold set (gold_standard_1_.csv)
"""

import os
import csv
import json
import time
import re
from openai import OpenAI

# ─── CONFIG ───────────────────────────────────────────────────────────────────

GOLD_FILE = "gold_standard_1_.csv"

# Johanna's output file — already classified
JOHANNA_FILE = "../métaphore/RESULTAT_annotation_gpt.csv"

# Ollama config for qwen3:30b
OLLAMA_URL = "http://127.0.0.1:11434/v1"
OLLAMA_MODEL = "qwen3:30b"

# OpenAI config
OPENAI_MODEL = "gpt-4o-mini"

# ─── LOAD GOLD SET ────────────────────────────────────────────────────────────

def load_gold(gold_file):
    gold = []
    with open(gold_file, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            label = row["consensus"].strip()
            if label in ["référentiel", "figuré"]:  # skip X
                gold.append({
                    "fichier": row["fichier"].strip(),
                    "token": row["token_lexique"].strip(),
                    "contexte": row["contexte"].strip(),
                    "label": label
                })
    return gold

# ─── LOAD JOHANNA RESULTS ─────────────────────────────────────────────────────

def load_johanna(johanna_file):
    """Load Johanna's GPT-4o-mini classifications"""
    results = {}
    if not os.path.exists(johanna_file):
        print(f"  ⚠️ Johanna file not found: {johanna_file}")
        return results

    with open(johanna_file, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            key = (row.get("fichier","").strip(),
                   row.get("token_lexique","").strip(),
                   row.get("truncated_sentence","").strip()[:50])
            label = row.get("label","").strip().lower()
            # normalize
            if label in ["littéral", "literal", "référentiel"]:
                label = "référentiel"
            elif label in ["figuré", "figure"]:
                label = "figuré"
            results[key] = label
    return results

# ─── QWEN PROMPT ──────────────────────────────────────────────────────────────

def build_prompt(token, contexte):
    return f"""Tu es un expert en sémantique française. Détermine si le terme animal est utilisé de façon LITTÉRALE ou FIGURÉE dans cette phrase.

Terme: <animal>{token}</animal>

Phrase: {contexte}

DÉFINITIONS:
- référentiel (littéral): l'animal est réel, présent physiquement ou mentionné comme être vivant réel
- figuré: métaphore, comparaison, expression idiomatique, ou représentation abstraite

Réponds UNIQUEMENT avec ce JSON:
{{"label": "référentiel"}} ou {{"label": "figuré"}}"""

def classify_qwen(client, token, contexte):
    try:
        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": build_prompt(token, contexte) }],
            temperature=0,
            timeout=300,
            max_tokens=5000,
        )
        raw = response.choices[0].message.content
        raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
        if '```' in raw:
            match = re.search(r'```(?:json)?\s*(.*?)\s*```', raw, re.DOTALL)
            if match:
                raw = match.group(1)
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            result = json.loads(match.group(0))
            label = result.get("label", "").strip().lower()
            if label in ["référentiel", "littéral", "literal"]:
                return "référentiel"
            elif label in ["figuré", "figure"]:
                return "figuré"
        return None
    except Exception as e:
        return None

def classify_gpt(client, token, contexte):
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": build_prompt(token, contexte)}],
            temperature=0,
            max_tokens=5000,
        )
        raw = response.choices[0].message.content
        if '```' in raw:
            match = re.search(r'```(?:json)?\s*(.*?)\s*```', raw, re.DOTALL)
            if match:
                raw = match.group(1)
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            result = json.loads(match.group(0))
            label = result.get("label", "").strip().lower()
            if label in ["référentiel", "littéral", "literal"]:
                return "référentiel"
            elif label in ["figuré", "figure"]:
                return "figuré"
        return None
    except Exception as e:
        return None

# ─── EVALUATE ─────────────────────────────────────────────────────────────────

def evaluate_model(predictions, gold):
    correct = 0
    total = 0
    ref_correct = 0; ref_total = 0
    fig_correct = 0; fig_total = 0

    for g, pred in zip(gold, predictions):
        if pred is None:
            continue
        total += 1
        if g["label"] == "référentiel":
            ref_total += 1
            if pred == "référentiel":
                correct += 1
                ref_correct += 1
        else:
            fig_total += 1
            if pred == "figuré":
                correct += 1
                fig_correct += 1

    acc = correct/total*100 if total else 0
    ref_acc = ref_correct/ref_total*100 if ref_total else 0
    fig_acc = fig_correct/fig_total*100 if fig_total else 0
    return {
        "accuracy": acc,
        "ref_accuracy": ref_acc,
        "fig_accuracy": fig_acc,
        "correct": correct,
        "total": total,
        "ref_correct": ref_correct,
        "ref_total": ref_total,
        "fig_correct": fig_correct,
        "fig_total": fig_total,
    }

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print(f"Loading gold set from {GOLD_FILE}...")
    gold = load_gold(GOLD_FILE)
    print(f"  → {len(gold)} labeled examples (excluding X)")

    ref_count = sum(1 for g in gold if g["label"] == "référentiel")
    fig_count = sum(1 for g in gold if g["label"] == "figuré")
    print(f"  → {ref_count} référentiel, {fig_count} figuré")

    # ── Method 1: qwen3:30b via Ollama ──
    print(f"\n{'='*55}")
    print(f"METHOD 1: {OLLAMA_MODEL} (free, local)")
    print(f"{'='*55}")

    qwen_client = OpenAI(base_url=OLLAMA_URL, api_key="ollama")
    qwen_predictions = []
    qwen_failed = 0

    for i, item in enumerate(gold, 1):
        print(f"[{i:>3}/{len(gold)}] {item['token']:<15}", end="", flush=True)
        pred = classify_qwen(qwen_client, item["token"], item["contexte"])
        qwen_predictions.append(pred)
        if pred is None:
            print(f" ❌")
            qwen_failed += 1
        else:
            ok = "✓" if pred == item["label"] else "✗"
            print(f" {pred:<12} {ok}")

    qwen_scores = evaluate_model(qwen_predictions, gold)
    print(f"\n  Failed: {qwen_failed}/{len(gold)}")

    # ── Method 2: GPT-4o-mini (new run) ──
    print(f"\n{'='*55}")
    print(f"METHOD 2: {OPENAI_MODEL} (paid API)")
    print(f"{'='*55}")

    api_key = os.environ.get("OPENAI_API_KEY")
    gpt_scores = None
    gpt_predictions = []

    if api_key:
        gpt_client = OpenAI(api_key=api_key)
        gpt_failed = 0

        for i, item in enumerate(gold, 1):
            print(f"[{i:>3}/{len(gold)}] {item['token']:<15}", end="", flush=True)
            pred = classify_gpt(gpt_client, item["token"], item["contexte"])
            gpt_predictions.append(pred)
            if pred is None:
                print(f" ❌")
                gpt_failed += 1
            else:
                ok = "✓" if pred == item["label"] else "✗"
                print(f" {pred:<12} {ok}")

        gpt_scores = evaluate_model(gpt_predictions, gold)
        print(f"\n  Failed: {gpt_failed}/{len(gold)}")
    else:
        print("  ⚠️ No OPENAI_API_KEY — skipping GPT-4o-mini")

    # ── Final comparison ──
    print(f"\n{'='*65}")
    print(f"FINAL COMPARISON — LITERAL/FIGURATIVE CLASSIFICATION")
    print(f"{'='*65}")
    print(f"  {'Metric':<25} {'qwen3:30b':>12} {'gpt-4o-mini':>12}")
    print(f"  {'-'*50}")

    metrics = [
        ("Overall accuracy", "accuracy"),
        ("Référentiel accuracy", "ref_accuracy"),
        ("Figuré accuracy", "fig_accuracy"),
    ]

    for label, key in metrics:
        qval = f"{qwen_scores[key]:.1f}%"
        gval = f"{gpt_scores[key]:.1f}%" if gpt_scores else "N/A"
        print(f"  {label:<25} {qval:>12} {gval:>12}")

    print(f"{'='*65}")
    print(f"\n  Target: 90% overall accuracy")
    print(f"  Johanna baseline: ~79-85% (from paper)")

    # Save results
    output_rows = []
    for i, item in enumerate(gold):
        row = {
            "fichier": item["fichier"],
            "token": item["token"],
            "contexte": item["contexte"][:100],
            "gold_label": item["label"],
            "qwen_pred": qwen_predictions[i] if i < len(qwen_predictions) else "",
            "qwen_correct": "1" if i < len(qwen_predictions) and qwen_predictions[i] == item["label"] else "0",
            "gpt_pred": gpt_predictions[i] if i < len(gpt_predictions) else "",
            "gpt_correct": "1" if i < len(gpt_predictions) and gpt_predictions[i] == item["label"] else "0",
        }
        output_rows.append(row)

    with open("evaluation_litteralite_resultats.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=output_rows[0].keys())
        writer.writeheader()
        writer.writerows(output_rows)
    print(f"\n✅ Detailed results saved to evaluation_litteralite_resultats.csv")

if __name__ == "__main__":
    main()
