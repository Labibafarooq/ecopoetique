"""
Test qwen3:30b at different num_predict values to find the best
speed/accuracy tradeoff before running on the full corpus.

Tests: 500, 1000, 2000 tokens (vs current 5000)
Uses a 30-row sample from each gold set to keep test short (~10 min total).
"""

import csv, json, re, requests, time, random

random.seed(99)

OLLAMA_URL   = "http://localhost:11435/api/chat"
OLLAMA_MODEL = "qwen3:30b"

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
EXEMPLES — termes végétaux/plantes:

référentiel (plante réelle):
• "Le jardinier arrosait ses tomates chaque soir en été."
  → tomates = référentiel (vraies plantes dans un jardin)
• "La forêt de chênes centenaires longeait toute la route départementale."
  → chênes = référentiel (vrais arbres dans un paysage)
• "Elle cueillit des champignons dans le sous-bois humide de novembre."
  → champignons = référentiel (vrais champignons cueillis)
• "L'olivier millénaire se dressait au centre de la place du village."
  → olivier = référentiel (vrai arbre présent physiquement)

figuré (métaphore, expression idiomatique):
• "Les carottes sont cuites — il est trop tard pour changer quoi que ce soit."
  → carottes = figuré (expression figée)
• "Mettre du beurre dans les épinards — il cherchait à améliorer ses revenus."
  → épinards = figuré (expression idiomatique)
• "Elle était fleur bleue — elle croyait encore aux contes de fées à trente ans."
  → fleur = figuré (expression pour désigner quelqu'un de romantique naïf)
• "Sa chevelure était une forêt sombre où l'on pouvait se perdre facilement."
  → forêt = figuré (métaphore pour des cheveux très épais)

CAS DIFFICILES:
• "La branche d'olivier symbolisait la paix dans les négociations." → olivier = figuré (symbole)
• "L'agriculteur taille ses oliviers chaque printemps." → oliviers = référentiel (vrais arbres)""",
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

def classify(token, contexte, category, num_predict):
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": build_prompt(token, contexte, category)}],
            "stream": False,
            "options": {"temperature": 0, "num_predict": num_predict},
        }, timeout=300)
        raw = resp.json()["message"]["content"].strip()
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        m = re.search(r'\{[^}]+\}', raw)
        if m:
            label = json.loads(m.group(0)).get("label", "").strip().lower()
            if label in ["référentiel", "figuré"]:
                return label
        for label in ["référentiel", "figuré"]:
            if label in raw.lower():
                return label
        return None
    except Exception as e:
        print(f"  ERROR: {e}")
        return None

GOLD_SETS = [
    ("Animaux", "gold_standard_1_.csv",           "\t", "animaux"),
    ("Plantes", "GOLD_litteralite_plantes_RB.csv", ";",  "plantes"),
]

NUM_PREDICT_VALUES = [500, 1000, 2000, 5000]
SAMPLE_SIZE = 30  # rows per gold set per num_predict — ~10 min total

print("Speed vs Accuracy test — qwen3:30b")
print("=" * 65)
print(f"Sample size: {SAMPLE_SIZE} rows per gold set")
print()

results = {}

for name, fname, sep, cat in GOLD_SETS:
    gold = []
    with open(fname, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter=sep):
            label = row["consensus"].strip()
            if label in ["référentiel", "figuré"]:
                gold.append({
                    "token":    row["token_lexique"].strip(),
                    "contexte": row["contexte"].strip(),
                    "label":    label,
                })

    # Stratified sample: keep ref/fig balance
    refs = [r for r in gold if r["label"] == "référentiel"]
    figs = [r for r in gold if r["label"] == "figuré"]
    n_fig = min(len(figs), SAMPLE_SIZE // 2)
    n_ref = SAMPLE_SIZE - n_fig
    sample = random.sample(refs, min(n_ref, len(refs))) + random.sample(figs, n_fig)
    random.shuffle(sample)

    print(f"\n{'─'*65}")
    print(f"  {name}  (sample: {len(sample)} rows, {n_fig} figuré + {n_ref} référentiel)")
    print(f"{'─'*65}")
    print(f"  {'num_predict':>12}  {'speed':>7}  {'overall':>8}  {'réf':>7}  {'fig':>7}  {'hrs(128K)':>10}")

    for np in NUM_PREDICT_VALUES:
        times = []
        correct = correct_ref = correct_fig = 0
        total_ref = total_fig = 0

        for item in sample:
            t0 = time.time()
            pred = classify(item["token"], item["contexte"], cat, np) or "référentiel"
            elapsed = time.time() - t0
            times.append(elapsed)

            ok = int(pred == item["label"])
            correct += ok
            if item["label"] == "référentiel":
                total_ref += 1; correct_ref += ok
            else:
                total_fig += 1; correct_fig += ok

        avg_t   = sum(times) / len(times)
        overall = correct / len(sample) * 100
        ref_acc = correct_ref / max(total_ref, 1) * 100
        fig_acc = correct_fig / max(total_fig, 1) * 100
        hrs_128k = 127816 * avg_t / 3600

        results.setdefault(name, {})[np] = {
            "avg_t": avg_t, "overall": overall, "ref": ref_acc, "fig": fig_acc
        }

        print(f"  {np:>12}  {avg_t:>6.1f}s  {overall:>7.1f}%  {ref_acc:>6.1f}%  {fig_acc:>6.1f}%  {hrs_128k:>9.0f}h")

print(f"\n{'='*65}")
print("RECOMMENDATION:")
best_np = None
for np in NUM_PREDICT_VALUES:
    anim = results.get("Animaux", {}).get(np, {})
    plant = results.get("Plantes", {}).get(np, {})
    avg_overall = (anim.get("overall", 0) + plant.get("overall", 0)) / 2
    avg_fig     = (anim.get("fig", 0) + plant.get("fig", 0)) / 2
    avg_t       = (anim.get("avg_t", 0) + plant.get("avg_t", 0)) / 2
    total_hrs   = (127816 + 69287) * avg_t / 3600
    print(f"  num_predict={np:>4}: avg_overall={avg_overall:.1f}% fig={avg_fig:.1f}% speed={avg_t:.1f}s/row total={total_hrs:.0f}h")
