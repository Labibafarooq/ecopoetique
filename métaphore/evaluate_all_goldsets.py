"""
Task 1 — Literal/Figurative Evaluation — ALL GOLD SETS v3
Category-specific few-shot examples — NONE from the gold sets.
All examples are independently sourced from French literature and idioms.
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
    {
        "name":     "Animaux",
        "file":     "gold_standard_1_.csv",
        "sep":      "\t",
        "output":   "eval_animaux_results.csv",
        "category": "animaux",
    },
    {
        "name":     "Plantes",
        "file":     "GOLD_litteralite_plantes_RB.csv",
        "sep":      ";",
        "output":   "eval_plantes_results.csv",
        "category": "plantes",
    },
    {
        "name":     "Loterre",
        "file":     "GOLD_litteralite_loterre__RB.csv",
        "sep":      ";",
        "output":   "eval_loterre_results.csv",
        "category": "loterre",
    },
]

# ── Few-shot examples — ZERO overlap with any gold set ───────────────────────
# Sources: classic French literature, common French idioms, ecological writing
# NOT drawn from any of the three gold set files.

EXAMPLES = {

    "animaux": """
EXEMPLES — termes animaux (indépendants du jeu d'évaluation):

référentiel (animal réel):
• "Le fermier nourrissait ses poules chaque matin avant le lever du soleil."
  → poules = référentiel (vraies volailles d'élevage)
• "Un aigle tournoyait lentement au-dessus des rochers calcaires."
  → aigle = référentiel (oiseau réel observé dans la nature)
• "La rivière grouillait de truites que les pêcheurs tentaient d'attraper."
  → truites = référentiel (poissons réels dans une rivière)
• "Elle tira le chat par la queue pour le faire descendre de la table."
  → chat = référentiel (animal domestique présent physiquement)

figuré (métaphore, comparaison, expression):
• "Il pleut des cordes — dehors c'est impossible de sortir sans parapluie."
  → (expression météo, pas d'animaux)
• "Monter sur ses grands chevaux — il s'est mis en colère pour rien."
  → chevaux = figuré (expression idiomatique, pas de vrais chevaux)
• "Elle avait un caractère de cochon — personne ne pouvait la supporter."
  → cochon = figuré (expression pour décrire le caractère d'une personne)
• "Il travaillait comme un bœuf du matin au soir sans jamais se plaindre."
  → bœuf = figuré (comparaison pour décrire l'effort humain)
• "Avoir d'autres chats à fouetter — j'ai des choses plus importantes à faire."
  → chats = figuré (expression idiomatique française)
• "Les candidats tombaient comme des mouches face aux questions du jury."
  → mouches = figuré (comparaison, pas de vraies mouches)""",

    "plantes": """
EXEMPLES — termes végétaux/plantes (indépendants du jeu d'évaluation):

référentiel (plante réelle):
• "Le jardinier arrosait ses tomates chaque soir en été."
  → tomates = référentiel (vraies plantes dans un jardin)
• "La forêt de chênes centenaires longeait toute la route départementale."
  → chênes = référentiel (vrais arbres dans un paysage)
• "Elle cueillit des champignons dans le sous-bois humide de novembre."
  → champignons = référentiel (vrais champignons cueillis)
• "Le marché proposait du basilic frais, du persil et de la coriandre."
  → basilic = référentiel (vraie herbe aromatique vendue au marché)
• "Les vignes de Bourgogne produisent certains des meilleurs vins du monde."
  → vignes = référentiel (vraies plantes viticoles dans une région)

figuré (métaphore, comparaison, expression):
• "Les carottes sont cuites — il est trop tard pour changer quoi que ce soit."
  → carottes = figuré (expression figée, situation sans retour)
• "Mettre du beurre dans les épinards — il cherchait à améliorer ses revenus."
  → épinards = figuré (expression idiomatique pour améliorer sa situation financière)
• "Ne pas avoir un radis — il était complètement fauché après les vacances."
  → radis = figuré (expression idiomatique, manque total d'argent)
• "Être dans les choux — leur projet a complètement échoué dès le début."
  → choux = figuré (expression idiomatique française, échec total)
• "Faire le poirier — les enfants s'amusaient à se tenir sur les mains."
  → poirier = figuré (expression, position acrobatique humaine)
• "Elle était fleur bleue — elle croyait encore aux contes de fées à trente ans."
  → fleur = figuré (expression pour désigner quelqu'un de romantique naïf)
• "Sa chevelure était une forêt sombre où l'on pouvait se perdre facilement."
  → forêt = figuré (métaphore pour des cheveux très épais et abondants)
• "Avoir la pêche — il était de bonne humeur et plein d'énergie ce matin."
  → pêche = figuré (expression familière pour désigner la forme physique)""",

    "loterre": """
EXEMPLES — termes écologiques/géographiques Loterre (indépendants du jeu d'évaluation):

référentiel (lieu ou concept écologique réel):
• "Les scientifiques étudient l'écosystème du lac depuis vingt ans."
  → écosystème = référentiel (vrai concept écologique dans un contexte scientifique)
• "La déforestation détruit les forêts tropicales à un rythme alarmant."
  → forêts = référentiel (vraies forêts détruites par l'activité humaine)
• "Le biologiste traversait la steppe mongole à dos de cheval depuis des jours."
  → steppe = référentiel (vrai biome géographique traversé physiquement)
• "L'expédition longeait le fleuve Amazone pendant trois semaines."
  → fleuve = référentiel (vrai fleuve parcouru lors d'une expédition)
• "La biodiversité des récifs coralliens est menacée par le réchauffement."
  → biodiversité = référentiel (vrai concept écologique dans un rapport scientifique)
• "Les plages de Normandie furent le théâtre du débarquement allié en 1944."
  → plages = référentiel (vrais lieux géographiques, contexte historique)
• "La montagne culminait à 4807 mètres — le Mont Blanc, toit de l'Europe."
  → montagne = référentiel (vrai sommet géographique précis)

figuré (métaphore, expression idiomatique):
• "Prêcher dans le désert — personne n'écoutait ses avertissements répétés."
  → désert = figuré (expression idiomatique, parler sans être entendu)
• "Déplacer des montagnes — elle ferait tout pour sauver son entreprise."
  → montagnes = figuré (expression idiomatique, effort surhumain)
• "Ce n'est pas la mer à boire — il suffit de remplir deux formulaires."
  → mer = figuré (expression idiomatique, ce n'est pas si difficile)
• "Naviguer en eaux troubles — la négociation devenait de plus en plus risquée."
  → eaux = figuré (métaphore pour une situation dangereuse et incertaine)
• "L'autoroute était une mer de lumières rouges à perte de vue."
  → mer = figuré (métaphore visuelle pour un embouteillage)
• "Sa carrière était un désert depuis son licenciement il y a deux ans."
  → désert = figuré (métaphore pour une période creuse, sans activité)
• "Enseveli dans la forêt de ses cheveux, il ne voyait plus rien autour."
  → forêt = figuré (métaphore pour des cheveux très épais)
• "Ils vivaient dans un océan de dettes depuis la faillite de la société."
  → océan = figuré (métaphore pour une grande quantité accablante)
• "Son habitat naturel était la bibliothèque — il n'en sortait jamais."
  → habitat naturel = figuré (ironie, pas un vrai habitat écologique)
• "Remonter à la surface — il essayait de se sortir de sa dépression."
  → surface = figuré (métaphore aquatique pour surmonter des difficultés)""",
}

CORE_DEFINITIONS = """
DÉFINITIONS:
- référentiel: le terme désigne un être vivant, lieu, ou élément naturel RÉEL — physiquement présent ou mentionné comme tel dans un contexte concret (naturaliste, géographique, culinaire, scientifique)
- figuré: le terme est utilisé comme métaphore, comparaison (avec "comme"), expression idiomatique figée, personnification, ou symbole abstrait décrivant une situation ou émotion humaine

⚠️ RÈGLES CLÉS:
- Expression idiomatique connue (carottes cuites, mer à boire, montagnes à déplacer...) → toujours figuré
- Terme dans une comparaison avec "comme" pour décrire un humain → figuré
- Terme décrivant un lieu ou être réellement présent dans la scène → référentiel
- Terme dans un contexte scientifique, géographique, naturaliste → référentiel
- Terme comme nourriture ou matière concrète réelle → référentiel
- Terme dans une métaphore décrivant émotion ou situation humaine → figuré
"""

def build_prompt(token, contexte, category):
    examples = EXAMPLES.get(category, EXAMPLES["animaux"])
    return f"""Tu es un expert en sémantique française. Détermine si le terme est utilisé de façon LITTÉRALE (référentiel) ou FIGURÉE dans cette phrase.

{CORE_DEFINITIONS}

{examples}

TERME À ANALYSER: <terme>{token}</terme>
PHRASE: {contexte}

Réponds UNIQUEMENT avec ce JSON:
{{"label": "référentiel"}} ou {{"label": "figuré"}}"""

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

def classify(client, token, contexte, category, model, is_ollama=True):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": build_prompt(token, contexte, category)}],
            temperature=0,
            max_tokens=5000 if is_ollama else 300,
            timeout=300 if is_ollama else 30,
        )
        raw = response.choices[0].message.content
        raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
        if '```' in raw:
            m = re.search(r'```(?:json)?\s*(.*?)\s*```', raw, re.DOTALL)
            if m: raw = m.group(1)
        m = re.search(r'\{.*?\}', raw, re.DOTALL)
        if m:
            result = json.loads(m.group(0))
            label = result.get("label", "").strip().lower()
            if label in ["référentiel", "littéral", "literal"]:
                return "référentiel"
            elif label in ["figuré", "figure"]:
                return "figuré"
        return None
    except Exception:
        return None

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

def save_results(gold, qwen_preds, gpt_preds, output_file):
    rows = []
    for i, item in enumerate(gold):
        rows.append({
            "fichier":      item["fichier"],
            "token":        item["token"],
            "contexte":     item["contexte"][:120],
            "gold_label":   item["label"],
            "qwen_pred":    qwen_preds[i] if i < len(qwen_preds) else "",
            "qwen_correct": "1" if i < len(qwen_preds) and qwen_preds[i] == item["label"] else "0",
            "gpt_pred":     gpt_preds[i] if i < len(gpt_preds) else "",
            "gpt_correct":  "1" if i < len(gpt_preds) and gpt_preds[i] == item["label"] else "0",
        })
    if rows:
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

def run_gold_set(gs, qwen_client, gpt_client, api_key):
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

    qwen_preds = []
    failed = 0
    print(f"\n  Running {OLLAMA_MODEL}...")
    for i, item in enumerate(gold, 1):
        print(f"  [{i:>3}/{len(gold)}] {item['token']:<20}", end="", flush=True)
        pred = classify(qwen_client, item["token"], item["contexte"],
                        gs["category"], OLLAMA_MODEL, is_ollama=True)
        qwen_preds.append(pred)
        if pred is None:
            print(" ❌"); failed += 1
        else:
            ok = "✓" if pred == item["label"] else "✗"
            print(f" {pred:<12} {ok}")

    qwen_scores = evaluate_predictions(qwen_preds, gold)
    print(f"\n  qwen3:30b — Overall: {qwen_scores['accuracy']:.1f}% | "
          f"Réf: {qwen_scores['ref_accuracy']:.1f}% | "
          f"Fig: {qwen_scores['fig_accuracy']:.1f}% | "
          f"Failed: {failed}/{len(gold)}")

    gpt_preds = []
    gpt_scores = None
    if api_key and gpt_client:
        print(f"\n  Running {OPENAI_MODEL}...")
        gpt_failed = 0
        for i, item in enumerate(gold, 1):
            print(f"  [{i:>3}/{len(gold)}] {item['token']:<20}", end="", flush=True)
            pred = classify(gpt_client, item["token"], item["contexte"],
                            gs["category"], OPENAI_MODEL, is_ollama=False)
            gpt_preds.append(pred)
            if pred is None:
                print(" ❌"); gpt_failed += 1
            else:
                ok = "✓" if pred == item["label"] else "✗"
                print(f" {pred:<12} {ok}")
        gpt_scores = evaluate_predictions(gpt_preds, gold)
        print(f"\n  gpt-4o-mini — Overall: {gpt_scores['accuracy']:.1f}%")

    save_results(gold, qwen_preds, gpt_preds, gs["output"])
    print(f"  💾 Saved to {gs['output']}")
    return {"qwen": qwen_scores, "gpt": gpt_scores}

def print_summary(all_results):
    print(f"\n{'='*72}")
    print("FINAL SUMMARY — ALL GOLD SETS (v3 — no gold set leakage)")
    print(f"{'='*72}")
    print(f"  {'Gold Set':<12} {'Model':<14} {'Overall':>9} {'Réf':>8} {'Fig':>8} {'N':>5}")
    print(f"  {'-'*58}")
    for name, scores in all_results.items():
        if scores is None: continue
        for model_name, s in [("qwen3:30b", scores["qwen"]),
                               ("gpt-4o-mini", scores["gpt"])]:
            if s is None: continue
            print(f"  {name:<12} {model_name:<14} "
                  f"{s['accuracy']:>8.1f}% "
                  f"{s['ref_accuracy']:>7.1f}% "
                  f"{s['fig_accuracy']:>7.1f}% "
                  f"{s['total']:>5}")
    print(f"{'='*72}")
    print("\n  Baseline (v1 — generic animal examples only):")
    print(f"  {'Animaux':<12} {'qwen3:30b':<14} {'92.1%':>9} {'93.4%':>8} {'89.9%':>8} {'190':>5}")
    print(f"  {'Plantes':<12} {'qwen3:30b':<14} {'94.7%':>9} {'99.4%':>8} {'62.5%':>8} {'188':>5}")
    print(f"  {'Loterre':<12} {'qwen3:30b':<14} {'83.1%':>9} {'91.9%':>8} {'51.2%':>8} {'189':>5}")
    print(f"\n  Target: 90%+ overall — especially figuré for Plantes and Loterre")

def main():
    print("Literal/Figurative Evaluation — All Gold Sets (v3)")
    print("Category-specific examples — zero overlap with gold sets")

    qwen_client = OpenAI(base_url=OLLAMA_URL, api_key="ollama")
    api_key = os.environ.get("OPENAI_API_KEY")
    gpt_client = OpenAI(api_key=api_key) if api_key else None
    if not api_key:
        print("\n  ℹ️  No OPENAI_API_KEY — only running qwen3:30b")

    all_results = {}
    for gs in GOLD_SETS:
        scores = run_gold_set(gs, qwen_client, gpt_client, api_key)
        all_results[gs["name"]] = scores
    print_summary(all_results)

if __name__ == "__main__":
    main()
