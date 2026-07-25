"""
Evaluate gold sets using batch=5 with the EXACT v6 prompts.
Compares against single-row v6 results:
  Animaux: 91.6% overall | 97.5% réf | 81.2% fig
  Plantes: 96.3% overall | 98.8% réf | 79.2% fig
"""

import csv, json, re, requests, time

OLLAMA_URL   = "http://localhost:11435/api/chat"
OLLAMA_MODEL = "qwen3:30b"

# ── Exact prompts from evaluate_all_goldsets_v6.py ────────────────────────────

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

def build_batch_prompt(items, category):
    examples = EXAMPLES.get(category, EXAMPLES["animaux"])
    entries = "\n".join(
        f'{i}. TERME: <terme>{token}</terme> | PHRASE: {contexte}'
        for i, token, contexte in items
    )
    return (
        "Tu es un expert en sémantique française. Pour chaque entrée numérotée, "
        "détermine si le terme est utilisé de façon LITTÉRALE (référentiel) ou FIGURÉE.\n\n"
        + CORE_DEFINITIONS + "\n"
        + examples + "\n\n"
        + "ENTRÉES À CLASSIFIER:\n"
        + entries + "\n\n"
        + "Réponds UNIQUEMENT avec ce JSON (respecte l'ordre et les numéros):\n"
        + '[{"id": 1, "label": "..."}, {"id": 2, "label": "..."}, ...]'
    )

def call_ollama(prompt):
    resp = requests.post(OLLAMA_URL, json={
        "model": OLLAMA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0, "num_predict": 5000},
    }, timeout=300)
    raw = resp.json()["message"]["content"].strip()
    return re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

def parse_batch(raw, chunk):
    results = {}
    arr_match = re.search(r'\[.*?\]', raw, re.DOTALL)
    if arr_match:
        try:
            arr = json.loads(arr_match.group(0))
            for item in arr:
                item_id = item.get("id")
                label = item.get("label", "").strip().lower()
                if item_id and label in ["référentiel", "figuré"]:
                    results[item_id] = label
            if len(results) == len(chunk):
                return results
        except: pass
    for m in re.finditer(r'\{[^}]+\}', raw):
        try:
            obj = json.loads(m.group(0))
            item_id = obj.get("id")
            label = obj.get("label", "").strip().lower()
            if item_id and label in ["référentiel", "figuré"]:
                results[item_id] = label
        except: pass
    return results

GOLD_SETS = [
    ("Animaux", "gold_standard_1_.csv",            "\t", "animaux"),
    ("Plantes", "GOLD_litteralite_plantes_RB.csv",  ";",  "plantes"),
]

V6_BENCHMARK = {
    "Animaux": (91.6, 97.5, 81.2),
    "Plantes": (96.3, 98.8, 79.2),
}

BATCH_SIZE = 5

print(f"Batch=5 evaluation with EXACT v6 prompts")
print(f"Model: {OLLAMA_MODEL}")
print("=" * 65)

# Warmup
print("Warming up...", flush=True)
requests.post(OLLAMA_URL, json={
    "model": OLLAMA_MODEL,
    "messages": [{"role": "user", "content": "bonjour"}],
    "stream": False, "options": {"num_predict": 5},
}, timeout=60)
print("Done.\n")

for name, fname, sep, category in GOLD_SETS:
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

    n_ref = sum(1 for r in gold if r["label"] == "référentiel")
    n_fig = sum(1 for r in gold if r["label"] == "figuré")

    print(f"{'─'*65}")
    print(f"  {name}  —  {len(gold)} rows  ({n_ref} référentiel + {n_fig} figuré)")
    print(f"{'─'*65}")

    correct_total = correct_ref = correct_fig = 0
    failed = 0
    times = []
    results_detail = []

    i = 0
    while i < len(gold):
        chunk = gold[i:i + BATCH_SIZE]
        items = [(j+1, r["token"], r["contexte"]) for j, r in enumerate(chunk)]

        t0 = time.time()
        raw = call_ollama(build_batch_prompt(items, category))
        preds = parse_batch(raw, chunk)
        times.append(time.time() - t0)

        if len(preds) < len(chunk):
            failed += 1

        for j, row in enumerate(chunk):
            pred = preds.get(j+1, "référentiel")
            ok = int(pred == row["label"])
            correct_total += ok
            if row["label"] == "référentiel":
                correct_ref += ok
            else:
                correct_fig += ok
            results_detail.append({
                "token": row["token"], "contexte": row["contexte"][:60],
                "gold": row["label"], "pred": pred, "correct": ok
            })
            row_num = i + j + 1
            mark = "✓" if ok else f"✗  ← gold={row['label']} pred={pred}"
            print(f"  [{row_num:>3}/{len(gold)}] {row['token']:<20} {row['label']:<14} {mark}", flush=True)

        i += BATCH_SIZE

    overall = correct_total / len(gold) * 100
    ref_acc  = correct_ref  / n_ref    * 100
    fig_acc  = correct_fig  / n_fig    * 100
    avg_per_row = sum(times) / len(times) / BATCH_SIZE

    print(f"\n  BATCH=5 RESULT:")
    print(f"    Overall : {overall:.1f}%  ({correct_total}/{len(gold)} correct)")
    print(f"    Réf     : {ref_acc:.1f}%  ({correct_ref}/{n_ref} correct)")
    print(f"    Fig     : {fig_acc:.1f}%  ({correct_fig}/{n_fig} correct)")
    print(f"    Failed batches: {failed}")
    print(f"    Speed: {avg_per_row:.1f}s/row")

    bm = V6_BENCHMARK[name]
    print(f"\n  V6 SINGLE-ROW BENCHMARK:")
    print(f"    Overall : {bm[0]:.1f}%  ({round(bm[0]/100*len(gold))}/{len(gold)} correct)")
    print(f"    Réf     : {bm[1]:.1f}%  ({round(bm[1]/100*n_ref)}/{n_ref} correct)")
    print(f"    Fig     : {bm[2]:.1f}%  ({round(bm[2]/100*n_fig)}/{n_fig} correct)")

    diff_overall = overall - bm[0]
    diff_fig     = fig_acc - bm[2]
    print(f"\n  DIFFERENCE (batch5 - v6):")
    print(f"    Overall : {diff_overall:+.1f}pp")
    print(f"    Fig     : {diff_fig:+.1f}pp")

    # Show errors
    errors = [r for r in results_detail if not r["correct"]]
    print(f"\n  ERRORS ({len(errors)} total):")
    for e in errors:
        print(f"    [{e['token']}] gold={e['gold']}  pred={e['pred']}")
        print(f"      {e['contexte']}...")
    print()

print("=" * 65)
