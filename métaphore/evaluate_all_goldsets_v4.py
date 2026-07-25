"""
Task 1 — Literal/Figurative Evaluation — ALL GOLD SETS v4
Two-pass classification:
  Pass 1: "Is this clearly référentiel?" 
  Pass 2: If uncertain, "Is this figuré?"
This forces the model to consider figuré more carefully.
Zero overlap with gold sets in examples.
"""

import os
import csv
import json
import re
from openai import OpenAI

OLLAMA_URL   = "http://127.0.0.1:11434/v1"
OLLAMA_MODEL = "qwen3:30b"
OPENAI_MODEL = "gpt-4o-mini"

GOLD_SETS = [
    {"name": "Animaux", "file": "gold_standard_1_.csv",          "sep": "\t", "output": "eval_animaux_v4.csv",  "category": "animaux"},
    {"name": "Plantes", "file": "GOLD_litteralite_plantes_RB.csv","sep": ";",  "output": "eval_plantes_v4.csv",  "category": "plantes"},
    {"name": "Loterre", "file": "GOLD_litteralite_loterre__RB.csv","sep": ";", "output": "eval_loterre_v4.csv",  "category": "loterre"},
]

# ── Independent examples — zero overlap with gold sets ───────────────────────

REF_SIGNALS = {
    "animaux": "L'animal est physiquement présent dans la scène, observé, élevé, chassé, mangé, ou mentionné dans un contexte naturaliste ou scientifique.",
    "plantes": "La plante est physiquement présente, cultivée, cueillie, vendue, cuisinée, ou mentionnée dans un contexte botanique ou géographique réel.",
    "loterre": "Le terme désigne un lieu géographique réel, un biome, un phénomène écologique concret, ou un concept scientifique dans un contexte naturaliste ou environnemental.",
}

FIG_SIGNALS = {
    "animaux": "L'animal apparaît dans une comparaison avec 'comme', une expression idiomatique figée, une métaphore décrivant un humain ou une situation abstraite.",
    "plantes": "La plante apparaît dans une expression idiomatique (carottes cuites, beurre dans les épinards, radis), une métaphore décrivant une situation ou émotion humaine.",
    "loterre": "Le terme géographique/écologique apparaît dans une expression idiomatique (prêcher dans le désert, déplacer des montagnes), une métaphore décrivant une situation humaine, ou une comparaison abstraite.",
}

FIG_EXAMPLES = {
    "animaux": [
        ("monter sur ses grands chevaux", "chevaux", "figuré", "expression idiomatique pour la colère"),
        ("elle avait un caractère de cochon — personne ne la supportait", "cochon", "figuré", "métaphore pour le caractère"),
        ("il travaillait comme un bœuf du matin au soir", "bœuf", "figuré", "comparaison avec 'comme' pour l'effort humain"),
        ("les candidats tombaient comme des mouches face au jury", "mouches", "figuré", "comparaison, pas de vraies mouches"),
        ("avoir d'autres chats à fouetter — j'ai mieux à faire", "chats", "figuré", "expression idiomatique française"),
    ],
    "plantes": [
        ("les carottes sont cuites — il est trop tard pour changer quoi que ce soit", "carottes", "figuré", "expression figée"),
        ("mettre du beurre dans les épinards — il cherchait à améliorer ses revenus", "épinards", "figuré", "expression idiomatique financière"),
        ("ne pas avoir un radis — il était complètement fauché", "radis", "figuré", "expression idiomatique, manque d'argent"),
        ("être dans les choux — leur projet a complètement échoué", "choux", "figuré", "expression idiomatique, échec"),
        ("sa chevelure était une forêt sombre où l'on pouvait se perdre", "forêt", "figuré", "métaphore pour des cheveux abondants"),
        ("avoir la pêche — il était plein d'énergie ce matin", "pêche", "figuré", "expression familière pour la forme physique"),
    ],
    "loterre": [
        ("prêcher dans le désert — personne n'écoutait ses avertissements", "désert", "figuré", "expression idiomatique, parler sans être entendu"),
        ("déplacer des montagnes — elle ferait tout pour sauver son entreprise", "montagnes", "figuré", "expression idiomatique, effort surhumain"),
        ("ce n'est pas la mer à boire — il suffit de remplir deux formulaires", "mer", "figuré", "expression idiomatique, ce n'est pas difficile"),
        ("sa carrière était un désert depuis son licenciement", "désert", "figuré", "métaphore pour une période sans activité"),
        ("l'autoroute était une mer de lumières rouges à perte de vue", "mer", "figuré", "métaphore visuelle pour un embouteillage"),
        ("enseveli dans la forêt de ses cheveux", "forêt", "figuré", "métaphore pour des cheveux épais"),
        ("ils vivaient dans un océan de dettes depuis la faillite", "océan", "figuré", "métaphore pour une grande quantité accablante"),
        ("son habitat naturel était la bibliothèque — il n'en sortait jamais", "habitat naturel", "figuré", "ironie, pas un vrai habitat écologique"),
    ],
}

def build_pass1_prompt(token, contexte, category):
    """Pass 1: Is this clearly référentiel?"""
    ref_signal = REF_SIGNALS[category]
    return f"""Tu es un expert en sémantique française.

QUESTION: Dans cette phrase, le terme <terme>{token}</terme> est-il utilisé de façon LITTÉRALE (référentiel) ?

Référentiel signifie: {ref_signal}

PHRASE: {contexte}

Réponds UNIQUEMENT avec ce JSON:
{{"referentiel": true}} si clairement littéral
{{"referentiel": false}} si tu as le moindre doute"""

def build_pass2_prompt(token, contexte, category):
    """Pass 2: Is this figuré? (only called when Pass 1 says uncertain)"""
    fig_signal = FIG_SIGNALS[category]
    examples = FIG_EXAMPLES.get(category, [])

    ex_text = "\n".join([
        f'• "{phrase}" → {terme} = {label} ({reason})'
        for phrase, terme, label, reason in examples
    ])

    return f"""Tu es un expert en sémantique française.

Le terme <terme>{token}</terme> dans cette phrase n'est pas clairement littéral.
Détermine s'il est FIGURÉ.

Figuré signifie: {fig_signal}

EXEMPLES DE CAS FIGURÉS:
{ex_text}

PHRASE: {contexte}

Réponds UNIQUEMENT avec ce JSON:
{{"label": "figuré"}} si c'est une métaphore, comparaison ou expression idiomatique
{{"label": "référentiel"}} si finalement c'est bien littéral"""

def classify_two_pass(client, token, contexte, category, model, is_ollama=True):
    max_tok = 5000 if is_ollama else 300
    timeout = 300 if is_ollama else 30

    def call(prompt):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=max_tok,
                timeout=timeout,
            )
            raw = response.choices[0].message.content
            raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
            if '```' in raw:
                m = re.search(r'```(?:json)?\s*(.*?)\s*```', raw, re.DOTALL)
                if m: raw = m.group(1)
            m = re.search(r'\{.*?\}', raw, re.DOTALL)
            if m:
                return json.loads(m.group(0))
        except Exception:
            pass
        return None

    # Pass 1 — is it clearly référentiel?
    result1 = call(build_pass1_prompt(token, contexte, category))
    if result1 is None:
        return None, "failed"

    if result1.get("referentiel") is True:
        return "référentiel", "pass1"

    # Pass 2 — model was uncertain, ask specifically about figuré
    result2 = call(build_pass2_prompt(token, contexte, category))
    if result2 is None:
        return "référentiel", "pass1_fallback"  # fallback to référentiel

    label = result2.get("label", "").strip().lower()
    if label in ["figuré", "figure"]:
        return "figuré", "pass2"
    return "référentiel", "pass2"

def load_gold(gold_file, sep):
    gold = []
    with open(gold_file, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=sep)
        for row in reader:
            label = row["consensus"].strip()
            if label in ["référentiel", "figuré"]:
                gold.append({
                    "fichier":  row.get("fichier", "").strip(),
                    "token":    row["token_lexique"].strip(),
                    "contexte": row["contexte"].strip(),
                    "label":    label,
                })
    return gold

def evaluate_predictions(predictions, gold):
    correct = total = ref_c = ref_t = fig_c = fig_t = 0
    for g, pred in zip(gold, predictions):
        if pred is None: continue
        total += 1
        if g["label"] == "référentiel":
            ref_t += 1
            if pred == "référentiel": correct += 1; ref_c += 1
        else:
            fig_t += 1
            if pred == "figuré": correct += 1; fig_c += 1
    return {
        "accuracy":     correct / total * 100 if total else 0,
        "ref_accuracy": ref_c / ref_t * 100 if ref_t else 0,
        "fig_accuracy": fig_c / fig_t * 100 if fig_t else 0,
        "correct": correct, "total": total,
        "ref_correct": ref_c, "ref_total": ref_t,
        "fig_correct": fig_c, "fig_total": fig_t,
    }

def save_results(gold, predictions, passes, output_file):
    rows = []
    for i, item in enumerate(gold):
        pred = predictions[i] if i < len(predictions) else ""
        rows.append({
            "fichier":   item["fichier"],
            "token":     item["token"],
            "contexte":  item["contexte"][:120],
            "gold":      item["label"],
            "pred":      pred or "",
            "correct":   "1" if pred == item["label"] else "0",
            "pass_used": passes[i] if i < len(passes) else "",
        })
    if rows:
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

def run_gold_set(gs, qwen_client):
    print(f"\n{'='*60}")
    print(f"GOLD SET: {gs['name']} ({gs['file']})")
    print(f"{'='*60}")

    if not os.path.exists(gs["file"]):
        print(f"  ⚠️  File not found: {gs['file']} — skipping")
        return None

    gold = load_gold(gs["file"], gs["sep"])
    ref_count = sum(1 for g in gold if g["label"] == "référentiel")
    fig_count = sum(1 for g in gold if g["label"] == "figuré")
    print(f"  Loaded: {len(gold)} examples ({ref_count} référentiel, {fig_count} figuré)")
    print(f"  Strategy: two-pass classification")

    predictions = []
    passes_used = []
    failed = 0
    pass1_ref = 0
    pass2_count = 0

    for i, item in enumerate(gold, 1):
        print(f"  [{i:>3}/{len(gold)}] {item['token']:<20}", end="", flush=True)
        pred, which_pass = classify_two_pass(
            qwen_client, item["token"], item["contexte"],
            gs["category"], OLLAMA_MODEL, is_ollama=True
        )
        predictions.append(pred)
        passes_used.append(which_pass)

        if pred is None:
            print(" ❌"); failed += 1
        else:
            ok = "✓" if pred == item["label"] else "✗"
            pass_info = f"[P{which_pass[-1]}]" if which_pass else ""
            print(f" {pred:<12} {ok} {pass_info}")
            if "pass1" in which_pass and pred == "référentiel": pass1_ref += 1
            if which_pass == "pass2": pass2_count += 1

    scores = evaluate_predictions(predictions, gold)
    print(f"\n  Pass 1 decided référentiel: {pass1_ref}")
    print(f"  Pass 2 needed (uncertain):  {pass2_count}")
    print(f"  Failed: {failed}/{len(gold)}")
    print(f"\n  Overall: {scores['accuracy']:.1f}% | "
          f"Réf: {scores['ref_accuracy']:.1f}% | "
          f"Fig: {scores['fig_accuracy']:.1f}%")

    save_results(gold, predictions, passes_used, gs["output"])
    print(f"  💾 Saved to {gs['output']}")
    return scores

def main():
    print("Literal/Figurative Evaluation — All Gold Sets (v4 — two-pass)")
    print("Pass 1: Is it clearly référentiel?")
    print("Pass 2: If uncertain → Is it figuré?")

    qwen_client = OpenAI(base_url=OLLAMA_URL, api_key="ollama")

    all_results = {}
    for gs in GOLD_SETS:
        scores = run_gold_set(gs, qwen_client)
        all_results[gs["name"]] = scores

    print(f"\n{'='*72}")
    print("FINAL SUMMARY — v4 two-pass vs v3 single-pass")
    print(f"{'='*72}")
    print(f"  {'Gold Set':<12} {'Version':<10} {'Overall':>9} {'Réf':>8} {'Fig':>8}")
    print(f"  {'-'*52}")

    v3 = {
        "Animaux": (89.5, 95.9, 78.3),
        "Plantes": (95.7, 100.0, 66.7),
        "Loterre": (85.2, 93.2, 56.1),
    }

    for name, scores in all_results.items():
        if scores:
            print(f"  {name:<12} {'v4 (2-pass)':<10} "
                  f"{scores['accuracy']:>8.1f}% "
                  f"{scores['ref_accuracy']:>7.1f}% "
                  f"{scores['fig_accuracy']:>7.1f}%")
            ov, rv, fv = v3[name]
            print(f"  {name:<12} {'v3 (1-pass)':<10} "
                  f"{ov:>8.1f}% {rv:>7.1f}% {fv:>7.1f}%")
            print()

    print(f"{'='*72}")
    print("  Target: 90%+ overall, especially figuré")

if __name__ == "__main__":
    main()
