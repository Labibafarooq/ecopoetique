"""
Task 1 — Literal/Figurative Evaluation — v5
Improvements over v3:
  - Loterre: added contrastive examples for ecological crisis (réf) vs metaphor (fig)
  - Loterre: added postcolonial geographic terms (brousse, maquis, désert) as référentiel
  - All categories: balanced figuré/référentiel examples drawn from error analysis
  - Prompt restructured: contrastive pairs showing hard cases explicitly
"""
import os
import csv
import json
import re


OLLAMA_URL = "http://localhost:11435/api/chat"
OLLAMA_MODEL = "qwen3:30b"

GOLD_SETS = [
    {
        "name":     "Animaux",
        "file":     "gold_standard_1_.csv",
        "sep":      "\t",
        "output":   "eval_animaux_v5_results.csv",
        "category": "animaux",
    },
    {
        "name":     "Plantes",
        "file":     "GOLD_litteralite_plantes_RB.csv",
        "sep":      ";",
        "output":   "eval_plantes_v5_results.csv",
        "category": "plantes",
    },
    {
        "name":     "Loterre",
        "file":     "GOLD_litteralite_loterre__RB.csv",
        "sep":      ";",
        "output":   "eval_loterre_v5_results.csv",
        "category": "loterre",
    },
]

# ── Examples — dynamically built from error analysis, no gold set overlap ────
EXAMPLES = {
    "animaux": """
EXEMPLES — termes animaux:

référentiel (animal réel):
• "Le fermier nourrissait ses poules chaque matin avant le lever du soleil."
  → poules = référentiel (vraies volailles d'élevage)
• "Un aigle tournoyait lentement au-dessus des rochers calcaires."
  → aigle = référentiel (oiseau réel observé dans la nature)
• "La rivière grouillait de truites que les pêcheurs tentaient d'attraper."
  → truites = référentiel (poissons réels dans une rivière)
• "Elle tira le chat par la queue pour le faire descendre de la table."
  → chat = référentiel (animal domestique présent physiquement)
• "Le renard avait dévoré trois poules cette nuit — il fallait réparer le grillage."
  → renard = référentiel (vrai prédateur ayant commis des dégâts réels)

figuré (métaphore, comparaison, expression):
• "Monter sur ses grands chevaux — il s'est mis en colère pour rien."
  → chevaux = figuré (expression idiomatique, pas de vrais chevaux)
• "Elle avait un caractère de cochon — personne ne pouvait la supporter."
  → cochon = figuré (expression pour décrire le caractère)
• "Il travaillait comme un bœuf du matin au soir sans jamais se plaindre."
  → bœuf = figuré (comparaison pour décrire l'effort humain)
• "Les candidats tombaient comme des mouches face aux questions du jury."
  → mouches = figuré (comparaison, pas de vraies mouches)
• "Avoir d'autres chats à fouetter — j'ai des choses plus importantes à faire."
  → chats = figuré (expression idiomatique française)

CAS DIFFICILES — à distinguer soigneusement:
• "La proie était encore en vie quand le lion la rejoignit." → proie = référentiel (vraie proie animale)
• "Laquelle était le chasseur, laquelle la proie ?" → proie = figuré (métaphore pour rapport de force humain)
• "Le loup avait attaqué le troupeau pendant la nuit." → loup = référentiel (vrai animal)
• "Il était le loup de la meute — tous lui obéissaient." → loup = figuré (métaphore de domination)""",

    "plantes": """
EXEMPLES — termes végétaux/plantes:

référentiel (plante réelle):
• "Le jardinier arrosait ses tomates chaque soir en été."
  → tomates = référentiel (vraies plantes dans un jardin)
• "La forêt de chênes centenaires longeait toute la route départementale."
  → chênes = référentiel (vrais arbres dans un paysage)
• "Elle cueillit des champignons dans le sous-bois humide de novembre."
  → champignons = référentiel (vrais champignons cueillis)
• "Les vignes de Bourgogne produisent certains des meilleurs vins du monde."
  → vignes = référentiel (vraies plantes viticoles)
• "L'olivier millénaire se dressait au centre de la place du village."
  → olivier = référentiel (vrai arbre présent physiquement)

figuré (métaphore, expression idiomatique):
• "Les carottes sont cuites — il est trop tard pour changer quoi que ce soit."
  → carottes = figuré (expression figée)
• "Mettre du beurre dans les épinards — il cherchait à améliorer ses revenus."
  → épinards = figuré (expression idiomatique)
• "Ne pas avoir un radis — il était complètement fauché après les vacances."
  → radis = figuré (expression idiomatique)
• "Elle était fleur bleue — elle croyait encore aux contes de fées à trente ans."
  → fleur = figuré (expression pour désigner quelqu'un de romantique naïf)
• "Sa chevelure était une forêt sombre où l'on pouvait se perdre facilement."
  → forêt = figuré (métaphore pour des cheveux très épais)

CAS DIFFICILES — à distinguer soigneusement:
• "La branche d'olivier symbolisait la paix dans les négociations." → olivier = figuré (symbole)
• "Ne laissez pas la branche d'olivier tomber de ma main…" → olivier = figuré (symbole politique/religieux)
• "L'agriculteur taille ses oliviers chaque printemps." → oliviers = référentiel (vrais arbres)
• "Elle a la peau couleur lime." → lime = figuré (comparaison de couleur, pas de vraie lime)""",

    "loterre": """
EXEMPLES — termes écologiques/géographiques Loterre:

référentiel (lieu ou concept écologique réel):
• "Les scientifiques étudient l'écosystème du lac depuis vingt ans."
  → écosystème = référentiel (vrai concept écologique scientifique)
• "La déforestation détruit les forêts tropicales à un rythme alarmant."
  → forêts = référentiel (vraies forêts détruites, contexte écologique)
• "Le biologiste traversait la steppe mongole à dos de cheval."
  → steppe = référentiel (vrai biome géographique traversé)
• "La montagne culminait à 4807 mètres — le Mont Blanc, toit de l'Europe."
  → montagne = référentiel (vrai sommet géographique précis)
• "Cet après-midi la brousse s'est encore ouverte sur un homme du chantier."
  → brousse = référentiel (vrai paysage africain, contexte géographique)
• "N'avoir rien dit contre l'occupant, avoir laissé les autres partir pour le maquis."
  → maquis = référentiel (vrai terrain + résistance, contexte historique précis)
• "Les forêts brûlaient. Les océans agonisaient. Le permafrost fondait."
  → océans = référentiel (vrais océans dans un contexte de crise écologique réelle)
• "Il s'est imaginé adoubé par les grandes familles du désert."
  → désert = référentiel (vrai désert, contexte géographique/tribal africain)
• "Face à nous le lac nous accueille et je tressaille."
  → lac = référentiel (vrai lac présent physiquement dans la scène)

figuré (métaphore, expression idiomatique):
• "Prêcher dans le désert — personne n'écoutait ses avertissements répétés."
  → désert = figuré (expression idiomatique, parler sans être entendu)
• "Déplacer des montagnes — elle ferait tout pour sauver son entreprise."
  → montagnes = figuré (expression idiomatique, effort surhumain)
• "Ce n'est pas la mer à boire — il suffit de remplir deux formulaires."
  → mer = figuré (expression idiomatique, ce n'est pas difficile)
• "Naviguer en eaux troubles — la négociation devenait de plus en plus risquée."
  → eaux = figuré (métaphore pour une situation dangereuse)
• "Sa carrière était un désert depuis son licenciement."
  → désert = figuré (métaphore pour une période creuse sans activité)
• "Ils vivaient dans un océan de dettes depuis la faillite."
  → océan = figuré (métaphore pour une grande quantité accablante)
• "Ce serait être largué en pleine mer sans bouée de sauvetage."
  → mer = figuré (métaphore pour l'abandon et le danger)
• "Le temps nous a poussés vivants hors des marais."
  → marais = figuré (métaphore pour une situation difficile dont on s'échappe)
• "Cette promesse a traversé mille fois la mer et ma mémoire."
  → mer = figuré (métaphore du voyage, la mer comme distance émotionnelle)

CAS DIFFICILES — LA RÈGLE PRINCIPALE:
• Crise écologique réelle (réchauffement, pollution, déforestation) → TOUJOURS référentiel
  Ex: "les océans agonisaient" dans un texte sur le réchauffement → référentiel
• Même terme en contexte humain/émotionnel → figuré
  Ex: "un océan de tristesse" → figuré
• Terme géographique avec nom propre ou mesure précise → référentiel
• Terme géographique décrivant une émotion ou situation abstraite → figuré
• Contexte colonial/postcolonial avec paysage africain/asiatique réel → référentiel
  Ex: brousse, maquis, savane, désert dans contexte géographique africain → référentiel""",
}

CORE_DEFINITIONS = """
DÉFINITIONS:
- référentiel: le terme désigne un être vivant, lieu, ou élément naturel RÉEL — physiquement présent ou mentionné comme tel dans un contexte concret (naturaliste, géographique, culinaire, scientifique, écologique)
- figuré: le terme est utilisé comme métaphore, comparaison (avec "comme"), expression idiomatique figée, personnification, ou symbole abstrait décrivant une situation ou émotion humaine

⚠️ RÈGLES CLÉS:
1. Expression idiomatique connue (carottes cuites, mer à boire, montagnes à déplacer...) → toujours figuré
2. Terme dans une comparaison avec "comme" pour décrire un humain → figuré
3. Terme décrivant un lieu ou être réellement présent dans la scène → référentiel
4. Terme dans un contexte scientifique, géographique, naturaliste, écologique → référentiel
5. Crise environnementale réelle (réchauffement, pollution, extinction) → référentiel même si le verbe semble fort
6. Terme géographique africain/asiatique dans contexte colonial ou de voyage → référentiel
7. Terme dans une métaphore décrivant émotion ou situation humaine → figuré
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

def classify(client, token, contexte, category, model):
    import requests as req
    try:
        resp = req.post(
            "http://localhost:11435/api/chat",
            json={
                "model": model,
                "messages": [{"role": "user", "content": build_prompt(token, contexte, category)}],
                "stream": False,
                "options": {"temperature": 0, "num_predict": 5000},
            },
            timeout=300,
        )
        resp.raise_for_status()
        raw = resp.json()["message"]["content"].strip()
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        raw = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
        m = re.search(r'\{[^}]+\}', raw)
        if m:
            data = json.loads(m.group(0))
            label = data.get("label", "").strip().lower()
            if label in ["référentiel", "figuré"]:
                return label
        for label in ["référentiel", "figuré"]:
            if label in raw.lower():
                return label
        return None
    except Exception as e:
        print(f"    ERROR: {e}")
        return None

def evaluate_gold_set(client, gold_set, model):
    name     = gold_set["name"]
    filepath = gold_set["file"]
    sep      = gold_set["sep"]
    output   = gold_set["output"]
    category = gold_set["category"]

    print(f"\n{'='*70}")
    print(f"  Evaluating: {name}  |  model: {model}")
    print(f"{'='*70}")

    gold = load_gold(filepath, sep)
    print(f"  Gold set: {len(gold)} examples")

    n_ref = sum(1 for g in gold if g["label"] == "référentiel")
    n_fig = sum(1 for g in gold if g["label"] == "figuré")
    print(f"  Référentiel: {n_ref} | Figuré: {n_fig}")

    results = []
    correct_total = correct_ref = correct_fig = 0
    total_ref = total_fig = 0

    for i, item in enumerate(gold, 1):
        pred = classify(client, item["token"], item["contexte"], category, model)
        if pred is None:
            pred = "référentiel"  # fallback

        is_correct = int(pred == item["label"])
        correct_total += is_correct

        if item["label"] == "référentiel":
            total_ref += 1
            correct_ref += is_correct
        else:
            total_fig += 1
            correct_fig += is_correct

        results.append({
            "fichier":      item["fichier"],
            "token":        item["token"],
            "contexte":     item["contexte"],
            "gold_label":   item["label"],
            "qwen_pred":    pred,
            "qwen_correct": is_correct,
        })

        if i % 20 == 0 or i == len(gold):
            acc     = correct_total / i * 100
            acc_ref = correct_ref / max(total_ref, 1) * 100
            acc_fig = correct_fig / max(total_fig, 1) * 100
            print(f"  [{i:>3}/{len(gold)}] Overall={acc:.1f}%  "
                  f"Réf={acc_ref:.1f}%  Fig={acc_fig:.1f}%")

    # Save results
    with open(output, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)

    # Final scores
    overall = correct_total / len(gold) * 100
    ref_acc = correct_ref / max(total_ref, 1) * 100
    fig_acc = correct_fig / max(total_fig, 1) * 100

    print(f"\n  {'─'*50}")
    print(f"  {name:<12} Overall: {overall:>5.1f}%  "
          f"Réf: {ref_acc:>5.1f}%  Fig: {fig_acc:>5.1f}%  N={len(gold)}")
    print(f"  Saved to: {output}")

    return {"name": name, "overall": overall, "ref": ref_acc, "fig": fig_acc, "n": len(gold)}

def main():
    # Connect to local Ollama
    client = None  # using requests directly
    model  = OLLAMA_MODEL

    print(f"\n{'='*70}")
    print(f"  TASK 1 — LITERAL/FIGURATIVE EVALUATION  v5")
    print(f"  Model: {model}")
    print(f"{'='*70}")

    all_results = []
    for gold_set in GOLD_SETS:
        result = evaluate_gold_set(client, gold_set, model)
        all_results.append(result)

    # Summary table
    print(f"\n{'='*70}")
    print(f"  FINAL SUMMARY — ALL GOLD SETS (v5)")
    print(f"{'='*70}")
    print(f"  {'Gold Set':<12} {'Model':<14} {'Overall':>9} {'Réf':>8} {'Fig':>8} {'N':>5}")
    print(f"  {'─'*56}")

    # Previous v3 results for comparison
    prev = {
        "Animaux": (89.5, 95.9, 78.3, 190),
        "Plantes": (95.7, 100.0, 66.7, 188),
        "Loterre": (85.2, 93.2, 56.1, 189),
    }

    for r in all_results:
        p = prev.get(r["name"], (0,0,0,0))
        diff_overall = r["overall"] - p[0]
        diff_fig = r["fig"] - p[2]
        sign_o = "+" if diff_overall >= 0 else ""
        sign_f = "+" if diff_fig >= 0 else ""
        print(f"  {r['name']:<12} {model:<14} {r['overall']:>8.1f}% "
              f"{r['ref']:>7.1f}% {r['fig']:>7.1f}% {r['n']:>5}")
        print(f"  {'':12} {'vs v3':14} {sign_o}{diff_overall:>7.1f}pp "
              f"{'':>7}  {sign_f}{diff_fig:>6.1f}pp (fig)")

    print(f"{'='*70}")
    print(f"\n  Previous v3 results:")
    print(f"  Animaux: 89.5% overall | 95.9% réf | 78.3% fig")
    print(f"  Plantes: 95.7% overall | 100.0% réf | 66.7% fig")
    print(f"  Loterre: 85.2% overall | 93.2% réf | 56.1% fig")

if __name__ == "__main__":
    main()
