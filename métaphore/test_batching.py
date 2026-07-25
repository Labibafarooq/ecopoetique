"""
Test batching: send N sentences per API call instead of 1.
Compares speed and accuracy of batch sizes 1, 3, 5, 10 vs individual calls.
Uses 30 rows from the animaux gold set (same as test_speed_vs_accuracy.py).
"""

import csv, json, re, requests, time, random

random.seed(99)

OLLAMA_URL   = "http://localhost:11435/api/chat"
OLLAMA_MODEL = "qwen3:30b"

EXAMPLES_ANIMAUX = """
EXEMPLES — termes animaux (indépendants du jeu d'évaluation):

référentiel (animal réel):
• "Le fermier nourrissait ses poules chaque matin avant le lever du soleil."
  → poules = référentiel (vraies volailles d'élevage)
• "Un aigle tournoyait lentement au-dessus des rochers calcaires."
  → aigle = référentiel (oiseau réel observé dans la nature)
• "Elle tira le chat par la queue pour le faire descendre de la table."
  → chat = référentiel (animal domestique présent physiquement)

figuré (métaphore, comparaison, expression):
• "Monter sur ses grands chevaux — il s'est mis en colère pour rien."
  → chevaux = figuré (expression idiomatique, pas de vrais chevaux)
• "Elle avait un caractère de cochon — personne ne pouvait la supporter."
  → cochon = figuré (expression pour décrire le caractère d'une personne)
• "Il travaillait comme un bœuf du matin au soir sans jamais se plaindre."
  → bœuf = figuré (comparaison pour décrire l'effort humain)
• "Les candidats tombaient comme des mouches face aux questions du jury."
  → mouches = figuré (comparaison, pas de vraies mouches)"""

CORE_DEFINITIONS = """
DÉFINITIONS:
- référentiel: le terme désigne un animal RÉEL — physiquement présent dans la scène
- figuré: métaphore, comparaison avec "comme", expression idiomatique, personnification

⚠️ RÈGLES:
1. Expression idiomatique connue → toujours figuré
2. Comparaison avec "comme" pour décrire un humain → figuré
3. Animal réellement présent dans la scène → référentiel
4. Contexte naturaliste ou scientifique → référentiel
"""

def build_single_prompt(token, contexte):
    return (
        "Tu es un expert en sémantique française. Détermine si le terme est LITTÉRAL (référentiel) ou FIGURÉ.\n\n"
        + CORE_DEFINITIONS + "\n"
        + EXAMPLES_ANIMAUX + "\n\n"
        + f"TERME: <terme>{token}</terme>\n"
        + f"PHRASE: {contexte}\n\n"
        + 'Réponds UNIQUEMENT: {"label": "référentiel"} ou {"label": "figuré"}'
    )

def build_batch_prompt(items):
    """items = list of (id, token, contexte)"""
    entries = "\n".join(
        f'{i}. TERME: <terme>{token}</terme> | PHRASE: {contexte}'
        for i, token, contexte in items
    )
    return (
        "Tu es un expert en sémantique française. Pour chaque entrée numérotée, "
        "détermine si le terme est LITTÉRAL (référentiel) ou FIGURÉ.\n\n"
        + CORE_DEFINITIONS + "\n"
        + EXAMPLES_ANIMAUX + "\n\n"
        + "ENTRÉES À CLASSIFIER:\n"
        + entries + "\n\n"
        + "Réponds UNIQUEMENT avec ce JSON (une entrée par ligne, dans l'ordre):\n"
        + '[{"id": 1, "label": "référentiel"}, {"id": 2, "label": "figuré"}, ...]'
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

def parse_single(raw):
    m = re.search(r'\{[^}]+\}', raw)
    if m:
        try:
            label = json.loads(m.group(0)).get("label", "").strip().lower()
            if label in ["référentiel", "figuré"]: return label
        except: pass
    for label in ["référentiel", "figuré"]:
        if label in raw.lower(): return label
    return None

def parse_batch(raw, expected_ids):
    """Extract labels from JSON array response."""
    results = {}
    # Try parsing the full JSON array first
    arr_match = re.search(r'\[.*?\]', raw, re.DOTALL)
    if arr_match:
        try:
            arr = json.loads(arr_match.group(0))
            for item in arr:
                item_id = item.get("id")
                label = item.get("label", "").strip().lower()
                if item_id and label in ["référentiel", "figuré"]:
                    results[item_id] = label
            if len(results) == len(expected_ids):
                return results
        except: pass
    # Fallback: find individual JSON objects with id+label
    for m in re.finditer(r'\{[^}]+\}', raw):
        try:
            obj = json.loads(m.group(0))
            item_id = obj.get("id")
            label = obj.get("label", "").strip().lower()
            if item_id and label in ["référentiel", "figuré"]:
                results[item_id] = label
        except: pass
    return results

# ── Load gold set ─────────────────────────────────────────────────────────────

gold = []
with open("gold_standard_1_.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        label = row["consensus"].strip()
        if label in ["référentiel", "figuré"]:
            gold.append({
                "token":    row["token_lexique"].strip(),
                "contexte": row["contexte"].strip(),
                "label":    label,
            })

# Stratified sample of 30
refs = [r for r in gold if r["label"] == "référentiel"]
figs = [r for r in gold if r["label"] == "figuré"]
sample = random.sample(refs, 15) + random.sample(figs, 15)
random.shuffle(sample)

print(f"Batching test — {len(sample)} rows from animaux gold set")
print(f"Model: {OLLAMA_MODEL}")
print("=" * 65)

# ── Warmup ────────────────────────────────────────────────────────────────────
print("Warming up model...", flush=True)
requests.post(OLLAMA_URL, json={
    "model": OLLAMA_MODEL,
    "messages": [{"role": "user", "content": "bonjour"}],
    "stream": False,
    "options": {"num_predict": 5},
}, timeout=60)
print("Done.\n")

# ── Test each batch size ──────────────────────────────────────────────────────

TOTAL_ANIMAUX_ROWS = 127816  # after dedup corpus_principal + bestsellers

for batch_size in [1, 3, 5, 10]:
    times = []
    all_correct = []
    failed_batches = 0

    i = 0
    while i < len(sample):
        chunk = sample[i:i+batch_size]
        i += batch_size

        t0 = time.time()

        if batch_size == 1:
            raw = call_ollama(build_single_prompt(chunk[0]["token"], chunk[0]["contexte"]))
            pred = parse_single(raw) or "référentiel"
            preds = {1: pred}
        else:
            items = [(j+1, r["token"], r["contexte"]) for j, r in enumerate(chunk)]
            raw = call_ollama(build_batch_prompt(items))
            preds = parse_batch(raw, list(range(1, len(chunk)+1)))
            if len(preds) < len(chunk):
                failed_batches += 1

        elapsed = time.time() - t0
        times.append(elapsed)

        for j, row in enumerate(chunk):
            pred_label = preds.get(j+1, "référentiel")
            all_correct.append(int(pred_label == row["label"]))

    n = len(sample)
    avg_total  = sum(times) / len(times)          # seconds per batch
    avg_per_row = avg_total / batch_size           # seconds per row
    overall    = sum(all_correct) / n * 100

    # by class
    ref_correct = sum(c for c, r in zip(all_correct, sample) if r["label"] == "référentiel")
    fig_correct = sum(c for c, r in zip(all_correct, sample) if r["label"] == "figuré")
    ref_acc = ref_correct / 15 * 100
    fig_acc = fig_correct / 15 * 100

    est_hours  = TOTAL_ANIMAUX_ROWS * avg_per_row / 3600
    speedup    = (TOTAL_ANIMAUX_ROWS * (sum(times[:1]) / 1) / 3600) / est_hours if batch_size > 1 else 1.0

    print(f"Batch size = {batch_size}")
    print(f"  Time per batch : {avg_total:.1f}s")
    print(f"  Time per row   : {avg_per_row:.1f}s")
    print(f"  Overall acc    : {overall:.1f}%  (réf={ref_acc:.1f}%  fig={fig_acc:.1f}%)")
    print(f"  Failed batches : {failed_batches}/{len(times)}")
    print(f"  Animaux est.   : {est_hours:.0f}h ({est_hours/24:.1f} days)")
    if batch_size > 1:
        print(f"  Speedup vs 1   : {(TOTAL_ANIMAUX_ROWS * avg_per_row):.0f}h → {est_hours:.0f}h")
    print()

print("=" * 65)
print("NOTE: accuracy based on 30-row sample — small sample has high variance.")
print("      A drop of 1-2 wrong answers = ~7% swing. Run full gold set to confirm.")
