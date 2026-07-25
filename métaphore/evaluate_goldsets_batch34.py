"""
Test batch sizes 3 and 4 on both animaux and plantes gold sets.
Shows row-by-row output + final comparison vs v6 benchmark.

V6 benchmark (single row):
  Animaux: 91.6% overall | 97.5% réf (118/121) | 81.2% fig (56/69)
  Plantes: 96.3% overall | 98.8% réf (162/164) | 79.2% fig (19/24)

Batch=5 results:
  Animaux: 88.9% overall | 94.2% réf (114/121) | 79.7% fig (55/69)
  Plantes: 94.1% overall | 97.6% réf (160/164) | 70.8% fig (17/24)
"""

import csv, json, re, requests, time

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

CAS DIFFICILES:
• "La branche d'olivier symbolisait la paix dans les négociations." → olivier = figuré (symbole)
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
    examples = EXAMPLES[category]
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

def parse_batch(raw, n):
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
            if len(results) == n:
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
    ("Animaux", "gold_standard_1_.csv",           "\t", "animaux", 121, 69),
    ("Plantes", "GOLD_litteralite_plantes_RB.csv", ";",  "plantes", 164, 24),
]

V6 = {
    "Animaux": {"ref": (118, 121), "fig": (56, 69),  "overall": (174, 190)},
    "Plantes": {"ref": (162, 164), "fig": (19, 24),  "overall": (181, 188)},
}
BATCH5 = {
    "Animaux": {"ref": (114, 121), "fig": (55, 69),  "overall": (169, 190)},
    "Plantes": {"ref": (160, 164), "fig": (17, 24),  "overall": (177, 188)},
}

# Corpus sizes for time estimates
ANIMAUX_ROWS = 127816
PLANTES_ROWS = 69287

print(f"Batch 3 & 4 evaluation — EXACT v6 prompts")
print(f"Model: {OLLAMA_MODEL}")

# Warmup
print("\nWarming up...", flush=True)
requests.post(OLLAMA_URL, json={
    "model": OLLAMA_MODEL,
    "messages": [{"role": "user", "content": "bonjour"}],
    "stream": False, "options": {"num_predict": 5},
}, timeout=60)
print("Done.\n")

summary = {}

for batch_size in [3, 4]:
    print(f"\n{'#'*65}")
    print(f"  BATCH SIZE = {batch_size}")
    print(f"{'#'*65}")

    for name, fname, sep, category, n_ref_total, n_fig_total in GOLD_SETS:
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

        print(f"\n  {'─'*60}")
        print(f"  {name}  —  {len(gold)} rows  ({n_ref} réf + {n_fig} fig)  batch={batch_size}")
        print(f"  {'─'*60}")

        correct_total = correct_ref = correct_fig = 0
        failed = 0
        times = []

        i = 0
        while i < len(gold):
            chunk = gold[i:i + batch_size]
            items = [(j+1, r["token"], r["contexte"]) for j, r in enumerate(chunk)]

            t0 = time.time()
            raw = call_ollama(build_batch_prompt(items, category))
            preds = parse_batch(raw, len(chunk))
            times.append(time.time() - t0)

            if len(preds) < len(chunk):
                failed += 1

            for j, row in enumerate(chunk):
                pred = preds.get(j+1, "référentiel")
                ok = int(pred == row["label"])
                correct_total += ok
                if row["label"] == "référentiel": correct_ref += ok
                else: correct_fig += ok

                row_num = i + j + 1
                mark = "✓" if ok else f"✗  ← gold={row['label']} pred={pred}"
                print(f"  [{row_num:>3}/{len(gold)}] {row['token']:<22} {row['label']:<14} {mark}", flush=True)

            i += batch_size

        overall  = correct_total / len(gold) * 100
        ref_acc  = correct_ref  / n_ref * 100
        fig_acc  = correct_fig  / n_fig * 100
        avg_per_row = sum(times) / len(times) / batch_size
        corpus_rows = ANIMAUX_ROWS if name == "Animaux" else PLANTES_ROWS
        est_h = corpus_rows * avg_per_row / 3600

        summary[(batch_size, name)] = {
            "ref": (correct_ref, n_ref), "fig": (correct_fig, n_fig),
            "overall": (correct_total, len(gold)),
            "speed": avg_per_row, "est_h": est_h, "failed": failed
        }

        v6  = V6[name]
        b5  = BATCH5[name]
        print(f"\n  RESULT batch={batch_size}: overall={overall:.1f}% ({correct_total}/{len(gold)})  "
              f"réf={ref_acc:.1f}% ({correct_ref}/{n_ref})  fig={fig_acc:.1f}% ({correct_fig}/{n_fig})")
        print(f"  Speed: {avg_per_row:.1f}s/row  →  {name} corpus: {est_h:.0f}h ({est_h/24:.1f} days)")
        print(f"  Failed batches: {failed}")

# ── Final comparison table ────────────────────────────────────────────────────

print(f"\n\n{'='*65}")
print(f"  FINAL COMPARISON — ANIMAUX (121 réf + 69 fig = 190 rows)")
print(f"{'='*65}")
print(f"  {'Method':<12} {'Réf':>12} {'Fig':>12} {'Overall':>12} {'Speed':>8} {'Anim days':>10}")
print(f"  {'─'*62}")

def row_str(label, ref, fig, overall, speed=None, days=None):
    r = f"  {label:<12} {ref[0]}/{ref[1]} ({ref[0]/ref[1]*100:.1f}%){'':<2} {fig[0]}/{fig[1]} ({fig[0]/fig[1]*100:.1f}%){'':<2} {overall[0]}/{overall[1]} ({overall[0]/overall[1]*100:.1f}%)"
    if speed: r += f"  {speed:>5.1f}s/row"
    if days:  r += f"  {days:.1f}d"
    return r

print(row_str("v6 (1 row)", V6["Animaux"]["ref"], V6["Animaux"]["fig"], V6["Animaux"]["overall"]))
for bs in [3, 4]:
    if (bs, "Animaux") in summary:
        s = summary[(bs, "Animaux")]
        print(row_str(f"batch={bs}", s["ref"], s["fig"], s["overall"], s["speed"], s["est_h"]/24))
s5 = BATCH5["Animaux"]
print(f"  {'batch=5':<12} {s5['ref'][0]}/{s5['ref'][1]} (94.2%)     {s5['fig'][0]}/{s5['fig'][1]} (79.7%)     {s5['overall'][0]}/{s5['overall'][1]} (88.9%)   3.4s/row   5.8d")

print(f"\n{'='*65}")
print(f"  FINAL COMPARISON — PLANTES (164 réf + 24 fig = 188 rows)")
print(f"{'='*65}")
print(f"  {'Method':<12} {'Réf':>12} {'Fig':>12} {'Overall':>12} {'Speed':>8} {'Plant days':>10}")
print(f"  {'─'*62}")
print(row_str("v6 (1 row)", V6["Plantes"]["ref"], V6["Plantes"]["fig"], V6["Plantes"]["overall"]))
for bs in [3, 4]:
    if (bs, "Plantes") in summary:
        s = summary[(bs, "Plantes")]
        print(row_str(f"batch={bs}", s["ref"], s["fig"], s["overall"], s["speed"], s["est_h"]/24))
s5p = BATCH5["Plantes"]
print(f"  {'batch=5':<12} {s5p['ref'][0]}/{s5p['ref'][1]} (97.6%)     {s5p['fig'][0]}/{s5p['fig'][1]} (70.8%)     {s5p['overall'][0]}/{s5p['overall'][1]} (94.1%)   3.1s/row   3.2d")
