"""
Task 1 — Literal/Figurative Evaluation v2
Improved prompt with few-shot examples targeting figuré cases
"""

import os
import csv
import json
import time
import re
from openai import OpenAI

GOLD_FILE = "gold_standard_1_.csv"
OLLAMA_URL = "http://127.0.0.1:11434/v1"
OLLAMA_MODEL = "qwen3:30b"
OPENAI_MODEL = "gpt-4o-mini"
OUTPUT_FILE = "evaluation_litteralite_v2_resultats.csv"

def load_gold(gold_file):
    gold = []
    with open(gold_file, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            label = row["consensus"].strip()
            if label in ["référentiel", "figuré"]:
                gold.append({
                    "fichier": row["fichier"].strip(),
                    "token": row["token_lexique"].strip(),
                    "contexte": row["contexte"].strip(),
                    "label": label
                })
    return gold

def build_prompt(token, contexte):
    return f"""Tu es un expert en sémantique française. Détermine si le terme animal est utilisé de façon LITTÉRALE (référentiel) ou FIGURÉE dans cette phrase.

DÉFINITIONS:
- référentiel: l'animal est un être vivant réel, physiquement présent ou mentionné comme tel
- figuré: métaphore, comparaison, expression idiomatique, personnification, ou représentation abstraite

EXEMPLES:
Phrase: "Deux chiens couraient dans le parc."
Token: chiens → {{"label": "référentiel"}} (animaux réels qui courent)

Phrase: "La fièvre des marais faisait tomber les hommes comme des mouches."
Token: mouches → {{"label": "figuré"}} (comparaison, pas de vraies mouches)

Phrase: "Il soufflait comme un bœuf châtré."
Token: bœuf → {{"label": "figuré"}} (comparaison pour décrire un humain)

Phrase: "Sur la rive droite, un grand cerf dévalait le chemin de halage."
Token: cerf → {{"label": "référentiel"}} (animal réel dans la nature)

Phrase: "Je me voyais tantôt en agneau bêlant."
Token: agneau → {{"label": "figuré"}} (métaphore, personne se compare à un agneau)

Phrase: "Il avait dîné d'un gigot d'agneau avec des haricots."
Token: agneau → {{"label": "référentiel"}} (nourriture réelle, animal consommé)

Phrase: "Elle appelle ma mère son petit pruneau."
Token: pruneau → {{"label": "figuré"}} (terme d'affection, pas le fruit)

Phrase: "Les milans, les buses, les crécerelles brassaient le ciel."
Token: milans → {{"label": "référentiel"}} (oiseaux réels dans le ciel)

PHRASE À ANALYSER:
Terme: <animal>{token}</animal>
Phrase: {contexte}

⚠️ ATTENTION aux cas difficiles:
- Un animal dans une métaphore ou comparaison → figuré
- Un animal dans une expression figée (ex: "loup y es-tu", "pattes de lion" sur un meuble) → figuré
- Un animal réellement présent dans la scène → référentiel
- Un animal mentionné comme nourriture → référentiel
- Un animal dans un contexte zoologique/naturaliste → référentiel

Réponds UNIQUEMENT avec ce JSON:
{{"label": "référentiel"}} ou {{"label": "figuré"}}"""

def classify(client, token, contexte, model, is_ollama=True):
    try:
        kwargs = {
            "model": model,
            "messages": [{"role": "user", "content": build_prompt(token, contexte)}],
            "temperature": 0,
            "max_tokens": 5000 if is_ollama else 200,
            "timeout": 300 if is_ollama else 30,
        }
        response = client.chat.completions.create(**kwargs)
        raw = response.choices[0].message.content
        raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
        if '```' in raw:
            match = re.search(r'```(?:json)?\s*(.*?)\s*```', raw, re.DOTALL)
            if match:
                raw = match.group(1)
        match = re.search(r'\{.*?\}', raw, re.DOTALL)
        if match:
            result = json.loads(match.group(0))
            label = result.get("label", "").strip().lower()
            if label in ["référentiel", "littéral", "literal"]:
                return "référentiel"
            elif label in ["figuré", "figure"]:
                return "figuré"
        return None
    except Exception as e:
        print(f" [ERR: {e}]", end="")
        return None

def evaluate_model(predictions, gold):
    correct = 0; total = 0
    ref_correct = 0; ref_total = 0
    fig_correct = 0; fig_total = 0
    for g, pred in zip(gold, predictions):
        if pred is None:
            continue
        total += 1
        if g["label"] == "référentiel":
            ref_total += 1
            if pred == "référentiel":
                correct += 1; ref_correct += 1
        else:
            fig_total += 1
            if pred == "figuré":
                correct += 1; fig_correct += 1
    return {
        "accuracy": correct/total*100 if total else 0,
        "ref_accuracy": ref_correct/ref_total*100 if ref_total else 0,
        "fig_accuracy": fig_correct/fig_total*100 if fig_total else 0,
        "correct": correct, "total": total,
        "ref_correct": ref_correct, "ref_total": ref_total,
        "fig_correct": fig_correct, "fig_total": fig_total,
    }

def main():
    print(f"Loading gold set...")
    gold = load_gold(GOLD_FILE)
    print(f"  → {len(gold)} examples | {sum(1 for g in gold if g['label']=='référentiel')} référentiel, {sum(1 for g in gold if g['label']=='figuré')} figuré")

    qwen_client = OpenAI(base_url=OLLAMA_URL, api_key="ollama")
    qwen_predictions = []

    print(f"\n{'='*55}")
    print(f"METHOD 1: {OLLAMA_MODEL} — improved few-shot prompt")
    print(f"{'='*55}")

    for i, item in enumerate(gold, 1):
        print(f"[{i:>3}/{len(gold)}] {item['token']:<15}", end="", flush=True)
        pred = classify(qwen_client, item["token"], item["contexte"], OLLAMA_MODEL, is_ollama=True)
        qwen_predictions.append(pred)
        if pred is None:
            print(f" ❌")
        else:
            ok = "✓" if pred == item["label"] else "✗"
            print(f" {pred:<12} {ok}")

    qwen_scores = evaluate_model(qwen_predictions, gold)
    failed = sum(1 for p in qwen_predictions if p is None)
    print(f"\n  Failed: {failed}/{len(gold)}")

    # GPT-4o-mini
    api_key = os.environ.get("OPENAI_API_KEY")
    gpt_scores = None
    gpt_predictions = []

    if api_key:
        gpt_client = OpenAI(api_key=api_key)
        print(f"\n{'='*55}")
        print(f"METHOD 2: {OPENAI_MODEL} — same few-shot prompt")
        print(f"{'='*55}")
        for i, item in enumerate(gold, 1):
            print(f"[{i:>3}/{len(gold)}] {item['token']:<15}", end="", flush=True)
            pred = classify(gpt_client, item["token"], item["contexte"], OPENAI_MODEL, is_ollama=False)
            gpt_predictions.append(pred)
            if pred is None:
                print(f" ❌")
            else:
                ok = "✓" if pred == item["label"] else "✗"
                print(f" {pred:<12} {ok}")
        gpt_scores = evaluate_model(gpt_predictions, gold)
    else:
        print(f"\n  ⚠️ No OPENAI_API_KEY — skipping GPT-4o-mini")

    # Final scores
    print(f"\n{'='*65}")
    print(f"FINAL COMPARISON — LITERAL/FIGURATIVE (v2 few-shot prompt)")
    print(f"{'='*65}")
    print(f"  {'Metric':<25} {'qwen3:30b v2':>14} {'gpt-4o-mini v2':>14}")
    print(f"  {'-'*55}")
    for label, key in [("Overall accuracy","accuracy"),("Référentiel accuracy","ref_accuracy"),("Figuré accuracy","fig_accuracy")]:
        qval = f"{qwen_scores[key]:.1f}%"
        gval = f"{gpt_scores[key]:.1f}%" if gpt_scores else "N/A"
        print(f"  {label:<25} {qval:>14} {gval:>14}")
    print(f"{'='*65}")
    print(f"\n  Baseline v1 (no examples): Overall=85.8% Ref=94.2% Fig=71.0%")
    print(f"  Target: 90% overall")

    # Save
    rows = []
    for i, item in enumerate(gold):
        rows.append({
            "fichier": item["fichier"],
            "token": item["token"],
            "contexte": item["contexte"][:100],
            "gold_label": item["label"],
            "qwen_pred": qwen_predictions[i] if i < len(qwen_predictions) else "",
            "qwen_correct": "1" if i < len(qwen_predictions) and qwen_predictions[i] == item["label"] else "0",
            "gpt_pred": gpt_predictions[i] if i < len(gpt_predictions) else "",
            "gpt_correct": "1" if i < len(gpt_predictions) and gpt_predictions[i] == item["label"] else "0",
        })
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n✅ Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
