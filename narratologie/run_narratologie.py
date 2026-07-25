"""
Pipeline Narratologique v2 - Ecopoétique Project
Improved prompt for FOCALISATION and MODE NARRATIF
"""

import os
import csv
import json
import time
import re
from openai import OpenAI

OLLAMA_BASE_URL = "http://127.0.0.1:11435/v1"
MODEL = "qwen72b-limited:latest"
GOLD_FILE = "GOLD_narratologie_clean.csv"
EXTRAITS_DIR = "narrato_extraits"
OUTPUT_FILE = "resultats_qwen3_30b_v2.csv"

def load_gold(gold_file):
    gold = {}
    with open(gold_file, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            filename = row["File"].strip()
            gold[filename] = {
                "TYPE NARRATEUR":  row["TYPE NARRATEUR"].strip(),
                "FOCALISATION":    row["FOCALISATION"].strip(),
                "MODE NARRATIF":   row["MODE NARRATIF"].strip(),
                "REGIME NARRATIF": row["REGIME NARRATIF"].strip(),
                "ESPACE":          row["ESPACE"].strip(),
                "INTRIGUE":        row["INTRIGUE"].strip(),
                "TEMPORALITÉ":     row["TEMPORALITÉ"].strip(),
                "NAR_alt": row.get("Acceptable aussi: ",   "").strip(),
                "FOC_alt": row.get("Acceptable aussi: .1", "").strip(),
                "MOD_alt": row.get("Acceptable aussi: .2", "").strip(),
                "REG_alt": row.get("Acceptable aussi: .3", "").strip(),
                "ESP_alt": row.get("Acceptable aussi: .4", "").strip(),
                "INT_alt": row.get("Acceptable aussi: .5", "").strip(),
                "TEM_alt": row.get("Acceptable aussi: .6", "").strip(),
            }
    return gold

def load_extrait(filename, extraits_dir):
    sample_name = "narrato_sample_" + filename
    path = os.path.join(extraits_dir, sample_name)
    if not os.path.exists(path):
        print(f"  ⚠️  Extract not found: {sample_name}")
        return None
    with open(path, encoding="utf-8") as f:
        return f.read()

def build_prompt(extrait):
    prompt = """Tu es un expert en narratologie française. Analyse cet extrait de roman et réponds UNIQUEMENT en JSON.

RÈGLES ABSOLUES:
- Analyse UNIQUEMENT le texte fourni. N'utilise PAS tes connaissances sur le roman ou l'auteur.
- Ne réponds JAMAIS X — choisis toujours l'option la plus probable d'après le texte.
- Réponds UNIQUEMENT avec le JSON, sans markdown ni explication avant ou après.

━━━ CODES ET DÉFINITIONS ━━━

TYPE NARRATEUR — Qui raconte ?
• NAR_AUTOD : narrateur = protagoniste principal, utilise "je" comme personnage central
• NAR_TEM   : narrateur = témoin secondaire, utilise "je" mais n'est pas le héros principal
• NAR_EXT   : narrateur absent de l'histoire, raconte à la 3ème personne (il/elle/ils)

FOCALISATION — Accès à l'intériorité de qui ?
• FOC_INT  : accès aux pensées/émotions d'UN SEUL personnage (même si narrateur externe)
• FOC_EXT  : AUCUN accès aux pensées — uniquement actions visibles et dialogues
• FOC_ZERO : accès omniscient aux pensées de PLUSIEURS personnages différents
• FOC_VAR  : alternance entre plusieurs personnages différents selon les séquences

⚠️ ATTENTION FOCALISATION — erreurs fréquentes:
- Un narrateur à la 3ème personne peut avoir FOC_INT (il suit UN personnage de l'intérieur)
- FOC_ZERO ≠ FOC_INT : FOC_ZERO = plusieurs personnages, FOC_INT = un seul
- Si le texte suit UN personnage principal et ses pensées → FOC_INT (pas FOC_ZERO)
- FOC_ZERO = le narrateur sait ce que pensent Jean ET Marie ET Pierre

MODE NARRATIF — Qu'est-ce qui domine le texte ?
• MOD_EVT  : priorité aux ACTIONS, faits concrets, événements qui font avancer l'histoire
• MOD_DESC : priorité aux DESCRIPTIONS de lieux, objets, atmosphères, sensations
• MOD_INTR : priorité aux RÉFLEXIONS intérieures, émotions, états d'âme subjectifs
• MOD_MIX  : mélange ÉQUILIBRÉ de plusieurs modes sans prédominance claire

⚠️ ATTENTION MODE NARRATIF — erreurs fréquentes:
- Romans d'aventure, thriller, voyage, guerre → souvent MOD_EVT
- Ne pas confondre description physique (MOD_DESC) avec introspection (MOD_INTR)
- Si le "je" raconte des événements passés chronologiquement → MOD_EVT pas MOD_INTR
- MOD_MIX seulement si vraiment équilibré — sinon choisir le mode dominant

REGIME NARRATIF — Quel type de monde ?
• REG_AUTO : autobiographique/autofiction — voix de l'auteur, expérience personnelle réelle
• REG_REAL : réaliste — monde contemporain familier, logique quotidienne
• REG_FANT : fantastique — irruption de l'inexplicable dans le réel
• REG_SPEC : spéculatif/dystopique/uchronique — monde modifié, futuriste, fictionnalisé

ESPACE — Comment l'espace est-il organisé ?
• ESP_UNIT : UN lieu unique ou très concentré (une maison, un village, une île)
• ESP_FRAG : lieux MULTIPLES sans continuité géographique forte
• ESP_ITIN : déplacement CONTINU et progressif à travers l'espace
• ESP_IMAG : espace inventé, symbolique, irréaliste

INTRIGUE — Comment les événements s'enchaînent-ils ?
• INTR_LIN  : progression continue et globalement chronologique
• INTR_FRAG : ruptures fréquentes, blocs juxtaposés, discontinuité
• INTR_CYC  : répétition structurante de motifs ou situations

TEMPORALITÉ — Comment le temps est-il géré ?
• TEMP_LIN    : chronologie respectée, peu d'analepses
• TEMP_DIS    : analepses présentes (retours en arrière structurants)
• TEMP_DESORD : temporalité éclatée, non-linéaire, confuse

━━━ EXTRAIT À ANALYSER ━━━

""" + extrait + """

━━━ RÉPONSE ATTENDUE ━━━
Réponds avec EXACTEMENT ce JSON (remplace CODE par le code approprié):
{
  "TYPE NARRATEUR": "CODE",
  "FOCALISATION": "CODE",
  "MODE NARRATIF": "CODE",
  "REGIME NARRATIF": "CODE",
  "ESPACE": "CODE",
  "INTRIGUE": "CODE",
  "TEMPORALITÉ": "CODE",
  "JUSTIFICATION": "1-2 phrases citant des indices précis du texte"
}"""
    return prompt

def parse_response(raw):
    if not raw or not raw.strip():
        return None
    raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
    if not raw:
        return None
    if '```' in raw:
        match = re.search(r'```(?:json)?\s*(.*?)\s*```', raw, re.DOTALL)
        if match:
            raw = match.group(1)
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        raw = match.group(0)
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        return None

def classify(client, prompt, model):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt + " /no_think"}],
            temperature=0,
            timeout=120,
            max_tokens=4000,
        )
        raw = response.choices[0].message.content
        result = parse_response(raw)
        if result is None:
            print(f"  Raw (first 300 chars): {repr(raw[:300])}")
        return result
    except Exception as e:
        print(f"  ❌ API error: {e}")
        return None

def is_correct(predicted, gold_main, gold_alt):
    if predicted == gold_main:
        return True
    if gold_alt and predicted == gold_alt:
        return True
    return False

def evaluate(results, gold):
    criteria = [
        ("TYPE NARRATEUR",  "NAR_alt"),
        ("FOCALISATION",    "FOC_alt"),
        ("MODE NARRATIF",   "MOD_alt"),
        ("REGIME NARRATIF", "REG_alt"),
        ("ESPACE",          "ESP_alt"),
        ("INTRIGUE",        "INT_alt"),
        ("TEMPORALITÉ",     "TEM_alt"),
    ]
    scores = {c[0]: {"correct": 0, "total": 0} for c in criteria}
    overall_correct = 0
    overall_total = 0

    for filename, predicted in results.items():
        if filename not in gold:
            continue
        g = gold[filename]
        for crit, alt_key in criteria:
            if crit not in predicted:
                continue
            scores[crit]["total"] += 1
            overall_total += 1
            if is_correct(predicted[crit], g[crit], g[alt_key]):
                scores[crit]["correct"] += 1
                overall_correct += 1

    print("\n" + "="*60)
    print(f"MODEL: {MODEL}  |  VERSION: v2 (improved prompt)")
    print("="*60)
    for crit, s in scores.items():
        if s["total"] > 0:
            acc = s["correct"] / s["total"] * 100
            bar = "█" * int(acc / 5)
            print(f"  {crit:<20} {s['correct']:>2}/{s['total']:>2}  ({acc:>5.1f}%)  {bar}")
    print("-"*60)
    if overall_total > 0:
        overall_acc = overall_correct / overall_total * 100
        print(f"  {'OVERALL':<20} {overall_correct:>3}/{overall_total:>3}  ({overall_acc:>5.1f}%)")
    print("="*60)
    print("\nComparison with v1 baseline:")
    print("  TYPE NARRATEUR  v1: 88.3%")
    print("  FOCALISATION    v1: 63.3%")
    print("  MODE NARRATIF   v1: 35.0%")
    print("  OVERALL         v1: 55.7%")
    return scores

def save_results(rows, output_file):
    if not rows:
        return
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

def main():
    print(f"Loading gold set from {GOLD_FILE}...")
    gold = load_gold(GOLD_FILE)
    print(f"  → {len(gold)} novels in gold set")

    client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")

    print("\nTesting Ollama connection...")
    test = classify(client, 'Réponds uniquement avec ce JSON exact: {"test": "ok"}', MODEL)
    if test is None:
        print("❌ Ollama connection failed.")
        return
    print(f"  ✓ Connection OK: {test}")

    results = {}
    output_rows = []

    print(f"\nRunning classification v2 with {MODEL}...")
    print("-"*60)

    for i, (filename, gold_data) in enumerate(gold.items(), 1):
        print(f"[{i:>2}/{len(gold)}] {filename}")

        extrait = load_extrait(filename, EXTRAITS_DIR)
        if extrait is None:
            continue

        prompt = build_prompt(extrait)
        start = time.time()
        prediction = classify(client, prompt, MODEL)
        elapsed = time.time() - start

        if prediction is None:
            print(f"  ❌ Classification failed")
            continue

        results[filename] = prediction
        nar = prediction.get('TYPE NARRATEUR', '?')
        foc = prediction.get('FOCALISATION', '?')
        mod = prediction.get('MODE NARRATIF', '?')
        reg = prediction.get('REGIME NARRATIF', '?')

        # Show if correct
        g = gold_data
        nar_ok = "✓" if is_correct(nar, g["TYPE NARRATEUR"], g["NAR_alt"]) else "✗"
        foc_ok = "✓" if is_correct(foc, g["FOCALISATION"],   g["FOC_alt"]) else "✗"
        mod_ok = "✓" if is_correct(mod, g["MODE NARRATIF"],  g["MOD_alt"]) else "✗"

        print(f"  {elapsed:.1f}s | NAR={nar}{nar_ok} FOC={foc}{foc_ok} MOD={mod}{mod_ok} REG={reg}")

        row = {"File": filename}
        row.update(prediction)
        row["GOLD_NAR"] = g["TYPE NARRATEUR"]
        row["GOLD_FOC"] = g["FOCALISATION"]
        row["GOLD_MOD"] = g["MODE NARRATIF"]
        row["GOLD_REG"] = g["REGIME NARRATIF"]
        row["GOLD_ESP"] = g["ESPACE"]
        row["GOLD_INT"] = g["INTRIGUE"]
        row["GOLD_TEM"] = g["TEMPORALITÉ"]
        output_rows.append(row)

        if i % 5 == 0:
            save_results(output_rows, OUTPUT_FILE)
            print(f"  💾 Checkpoint saved ({i} novels)")

    save_results(output_rows, OUTPUT_FILE)
    print(f"\n✅ Results saved to {OUTPUT_FILE}")
    print(f"   Processed: {len(results)}/{len(gold)} novels")

    if results:
        evaluate(results, gold)

if __name__ == "__main__":
    main()