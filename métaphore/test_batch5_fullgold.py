"""
Test batch=5 vs batch=1 on the FULL animaux gold set (~190 rows).
This gives a reliable accuracy comparison before running on the full corpus.
"""

import csv, json, re, requests, time, random

random.seed(42)

OLLAMA_URL   = "http://localhost:11435/api/chat"
OLLAMA_MODEL = "qwen3:30b"

EXAMPLES_ANIMAUX = """
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
  → mouches = figuré (comparaison, pas de vraies mouches)"""

CORE_DEFINITIONS = """
DÉFINITIONS:
- référentiel: le terme désigne un être vivant RÉEL — physiquement présent ou mentionné dans un contexte concret (naturaliste, scientifique, culinaire)
- figuré: le terme est utilisé comme métaphore, comparaison (avec "comme"), expression idiomatique figée, personnification, ou symbole abstrait

⚠️ RÈGLES CLÉS:
1. Expression idiomatique connue → toujours figuré
2. Terme dans une comparaison avec "comme" pour décrire un humain → figuré
3. Terme décrivant un animal réellement présent dans la scène → référentiel
4. Contexte scientifique, naturaliste, culinaire → référentiel
5. Terme dans une métaphore décrivant émotion ou situation humaine → figuré
"""

def build_single_prompt(token, contexte):
    return (
        "Tu es un expert en sémantique française. Détermine si le terme est utilisé "
        "de façon LITTÉRALE (référentiel) ou FIGURÉE dans cette phrase.\n\n"
        + CORE_DEFINITIONS + "\n"
        + EXAMPLES_ANIMAUX + "\n\n"
        + f"TERME À ANALYSER: <terme>{token}</terme>\n"
        + f"PHRASE: {contexte}\n\n"
        + 'Réponds UNIQUEMENT avec ce JSON:\n{"label": "référentiel"} ou {"label": "figuré"}'
    )

def build_batch_prompt(items):
    entries = "\n".join(
        f'{i}. TERME: <terme>{token}</terme> | PHRASE: {contexte}'
        for i, token, contexte in items
    )
    return (
        "Tu es un expert en sémantique française. Pour chaque entrée numérotée, "
        "détermine si le terme est utilisé de façon LITTÉRALE (référentiel) ou FIGURÉE.\n\n"
        + CORE_DEFINITIONS + "\n"
        + EXAMPLES_ANIMAUX + "\n\n"
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

def parse_single(raw):
    m = re.search(r'\{[^}]+\}', raw)
    if m:
        try:
            label = json.loads(m.group(0)).get("label", "").strip().lower()
            if label in ["référentiel", "figuré"]: return label
        except: pass
    for label in ["référentiel", "figuré"]:
        if label in raw.lower(): return label
    return "référentiel"

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

# ── Load FULL gold set ────────────────────────────────────────────────────────

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

n_ref = sum(1 for r in gold if r["label"] == "référentiel")
n_fig = sum(1 for r in gold if r["label"] == "figuré")
print(f"Full gold set: {len(gold)} rows  ({n_ref} référentiel + {n_fig} figuré)")
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

TOTAL_ROWS = 127816  # animaux after dedup

for batch_size in [1, 5]:
    print(f"{'─'*65}")
    print(f"  Batch size = {batch_size}  ({'single row per call' if batch_size==1 else '5 rows per call'})")
    print(f"{'─'*65}")

    times = []
    correct_total = correct_ref = correct_fig = 0
    failed = 0
    start_all = time.time()

    i = 0
    row_idx = 0
    while row_idx < len(gold):
        chunk = gold[row_idx:row_idx + batch_size]
        row_idx += batch_size
        i += 1

        t0 = time.time()
        if batch_size == 1:
            raw = call_ollama(build_single_prompt(chunk[0]["token"], chunk[0]["contexte"]))
            preds = {1: parse_single(raw)}
        else:
            items = [(j+1, r["token"], r["contexte"]) for j, r in enumerate(chunk)]
            raw = call_ollama(build_batch_prompt(items))
            preds = parse_batch(raw, len(chunk))
            if len(preds) < len(chunk):
                failed += 1
        times.append(time.time() - t0)

        for j, row in enumerate(chunk):
            pred = preds.get(j+1, "référentiel")
            ok = int(pred == row["label"])
            correct_total += ok
            if row["label"] == "référentiel": correct_ref += ok
            else: correct_fig += ok

        # Progress every 10 batches
        rows_done = min(row_idx, len(gold))
        if i % 10 == 0 or row_idx >= len(gold):
            avg_t = sum(times) / len(times)
            overall = correct_total / rows_done * 100
            ref_a = correct_ref / min(n_ref, rows_done) * 100 if correct_ref > 0 else 0
            fig_a = correct_fig / min(n_fig, rows_done) * 100 if correct_fig > 0 else 0
            remaining = (len(gold) - rows_done) * (avg_t / batch_size)
            print(f"  [{rows_done:>3}/{len(gold)}] overall={overall:.1f}%  réf={ref_a:.1f}%  fig={fig_a:.1f}%  "
                  f"speed={avg_t/batch_size:.1f}s/row  ETA={remaining/60:.0f}min", flush=True)

    avg_t = sum(times) / len(times)
    avg_per_row = avg_t / batch_size
    overall  = correct_total / len(gold) * 100
    ref_acc  = correct_ref / n_ref * 100
    fig_acc  = correct_fig / n_fig * 100
    est_h    = TOTAL_ROWS * avg_per_row / 3600

    print(f"\n  FINAL: overall={overall:.1f}%  réf={ref_acc:.1f}%  fig={fig_acc:.1f}%")
    print(f"  Speed: {avg_per_row:.1f}s/row  |  Failed batches: {failed}")
    print(f"  Animaux full corpus estimate: {est_h:.0f}h ({est_h/24:.1f} days)")
    print(f"  Total wall time for this test: {(time.time()-start_all)/60:.0f} min\n")

print("=" * 65)
print("v6 benchmark for reference: overall=91.6%  réf=97.5%  fig=81.2%")
