"""
Multi-Model Comparison Pipeline - Ecopoétique Project
Fixed: normalizes model output keys, handles typos
"""

import os
import csv
import json
import time
import re
from openai import OpenAI

OLLAMA_BASE_URL = "http://127.0.0.1:11435/v1"

MODELS = [
    "mistral-nemo:latest",
    "llama3.1:8b",
]

GOLD_FILE = "GOLD_narratologie.csv"
EXTRAITS_DIR = "narrato_extraits"

# Valid codes per criterion
VALID_CODES = {
    "TYPE NARRATEUR":  ["NAR_AUTOD", "NAR_TEM", "NAR_EXT"],
    "FOCALISATION":    ["FOC_INT", "FOC_EXT", "FOC_ZERO", "FOC_VAR"],
    "MODE NARRATIF":   ["MOD_EVT", "MOD_DESC", "MOD_INTR", "MOD_MIX"],
    "REGIME NARRATIF": ["REG_AUTO", "REG_REAL", "REG_FANT", "REG_SPEC"],
    "ESPACE":          ["ESP_UNIT", "ESP_FRAG", "ESP_ITIN", "ESP_IMAG"],
    "INTRIGUE":        ["INTR_LIN", "INTR_FRAG", "INTR_CYC"],
    "TEMPORALITÉ":     ["TEMP_LIN", "TEMP_DIS", "TEMP_DESORD"],
}

OUTPUT_FIELDS = [
    "Model", "File",
    "TYPE NARRATEUR", "FOCALISATION", "MODE NARRATIF",
    "REGIME NARRATIF", "ESPACE", "INTRIGUE", "TEMPORALITÉ",
    "JUSTIFICATION",
    "GOLD_NAR", "GOLD_FOC", "GOLD_MOD", "GOLD_REG", "GOLD_ESP", "GOLD_INT", "GOLD_TEM"
]

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
    path = os.path.join(extraits_dir, "narrato_sample_" + filename)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return f.read()

def build_prompt(extrait):
    return """Tu es un expert en narratologie française. Analyse cet extrait de roman et réponds UNIQUEMENT en JSON.

RÈGLES ABSOLUES:
- Analyse UNIQUEMENT le texte fourni. N'utilise PAS tes connaissances sur le roman ou l'auteur.
- Ne réponds JAMAIS X — choisis toujours l'option la plus probable d'après le texte.
- Réponds UNIQUEMENT avec le JSON, sans markdown ni explication.

TYPE NARRATEUR:
• NAR_AUTOD : "je" = protagoniste principal
• NAR_TEM   : "je" = témoin secondaire
• NAR_EXT   : narrateur à la 3ème personne (il/elle)

FOCALISATION:
• FOC_INT  : accès aux pensées d'UN SEUL personnage
• FOC_EXT  : aucun accès aux pensées, uniquement actions/dialogues
• FOC_ZERO : accès omniscient aux pensées de PLUSIEURS personnages
• FOC_VAR  : alternance entre plusieurs personnages selon les séquences
⚠️ FOC_ZERO = PLUSIEURS personnages. FOC_INT = UN seul.
⚠️ Ne pas choisir FOC_VAR par défaut — seulement si le texte alterne vraiment entre personnages différents.

MODE NARRATIF:
• MOD_EVT  : priorité aux ACTIONS et événements concrets
• MOD_DESC : priorité aux DESCRIPTIONS de lieux/objets/atmosphères
• MOD_INTR : priorité à l'INTROSPECTION et réflexions intérieures
• MOD_MIX  : mélange équilibré de plusieurs modes
⚠️ Romans d'aventure/voyage/guerre → souvent MOD_EVT pas MOD_INTR
⚠️ Ne pas choisir MOD_MIX par défaut — seulement si vraiment équilibré.

REGIME NARRATIF:
• REG_AUTO : autobiographique/autofiction
• REG_REAL : réaliste, monde contemporain familier
• REG_FANT : fantastique, irruption de l'inexplicable
• REG_SPEC : spéculatif/dystopique/uchronique

ESPACE:
• ESP_UNIT : un seul lieu concentré
• ESP_FRAG : lieux multiples fragmentés
• ESP_ITIN : déplacement continu et progressif
• ESP_IMAG : espace inventé/symbolique

INTRIGUE:
• INTR_LIN  : progression linéaire/chronologique
• INTR_FRAG : ruptures fréquentes, discontinu
• INTR_CYC  : répétition structurante de motifs

TEMPORALITÉ:
• TEMP_LIN    : chronologie respectée, peu d'analepses
• TEMP_DIS    : analepses présentes (retours en arrière)
• TEMP_DESORD : temporalité éclatée, non-linéaire

EXTRAIT:
""" + extrait + """

Réponds avec EXACTEMENT ce JSON (utilise les codes exacts ci-dessus):
{
  "TYPE NARRATEUR": "CODE",
  "FOCALISATION": "CODE",
  "MODE NARRATIF": "CODE",
  "REGIME NARRATIF": "CODE",
  "ESPACE": "CODE",
  "INTRIGUE": "CODE",
  "TEMPORALITÉ": "CODE",
  "JUSTIFICATION": "1-2 phrases basées sur le texte"
}"""

def normalize_prediction(prediction):
    """Fix key typos and normalize codes from model output."""
    if not prediction:
        return prediction

    # Fix common key typos
    key_fixes = {
        "REGIME NARRATIV": "REGIME NARRATIF",
        "TEMPORALITE":     "TEMPORALITÉ",
        "TEMPORALITE\u0301": "TEMPORALITÉ",
        "MODE NARRATIF DOMINANT": "MODE NARRATIF",
    }
    fixed = {}
    for k, v in prediction.items():
        clean_k = key_fixes.get(k, k)
        fixed[clean_k] = v

    # Fix common value typos
    value_fixes = {
        "NARR_EXT": "NAR_EXT",
        "NARR_AUTOD": "NAR_AUTOD",
        "NARR_TEM": "NAR_TEM",
        "FOC_VARIABLE": "FOC_VAR",
        "MOD_EVENEMENTS": "MOD_EVT",
        "MOD_INTROSPECTION": "MOD_INTR",
        "MOD_DESCRIPTION": "MOD_DESC",
        "MOD_MIXTE": "MOD_MIX",
    }
    for crit in VALID_CODES:
        if crit in fixed:
            val = str(fixed[crit]).strip().upper()
            val = value_fixes.get(val, val)
            fixed[crit] = val

    return fixed

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
        result = json.loads(raw.strip())
        return normalize_prediction(result)
    except json.JSONDecodeError:
        return None

def classify(client, prompt, model):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt + " /no_think"}],
            temperature=0,
            timeout=180,
            max_tokens=4000,
        )
        raw = response.choices[0].message.content
        return parse_response(raw)
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None

def is_correct(predicted, gold_main, gold_alt):
    if predicted == gold_main:
        return True
    if gold_alt and predicted == gold_alt:
        return True
    return False

def run_model(client, model, gold):
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
    results = []
    failed = 0

    print(f"\n{'='*60}")
    print(f"MODEL: {model}")
    print(f"{'='*60}")

    for i, (filename, gold_data) in enumerate(gold.items(), 1):
        print(f"[{i:>2}/{len(gold)}] {filename[:50]}", end="", flush=True)

        extrait = load_extrait(filename, EXTRAITS_DIR)
        if extrait is None:
            print(f" ⚠️ extract not found")
            failed += 1
            continue

        start = time.time()
        prediction = classify(client, build_prompt(extrait), model)
        elapsed = time.time() - start

        if prediction is None:
            print(f" ❌ failed ({elapsed:.0f}s)")
            failed += 1
            continue

        nar = prediction.get('TYPE NARRATEUR', '?')
        foc = prediction.get('FOCALISATION', '?')
        mod = prediction.get('MODE NARRATIF', '?')
        g = gold_data

        nar_ok = "✓" if is_correct(nar, g["TYPE NARRATEUR"], g["NAR_alt"]) else "✗"
        foc_ok = "✓" if is_correct(foc, g["FOCALISATION"],   g["FOC_alt"]) else "✗"
        mod_ok = "✓" if is_correct(mod, g["MODE NARRATIF"],  g["MOD_alt"]) else "✗"
        print(f" {elapsed:.0f}s | NAR={nar}{nar_ok} FOC={foc}{foc_ok} MOD={mod}{mod_ok}")

        for crit, alt_key in criteria:
            if crit in prediction:
                scores[crit]["total"] += 1
                if is_correct(prediction[crit], g[crit], g[alt_key]):
                    scores[crit]["correct"] += 1

        row = {f: "" for f in OUTPUT_FIELDS}
        row["Model"] = model
        row["File"] = filename
        for crit in VALID_CODES:
            row[crit] = prediction.get(crit, "")
        row["JUSTIFICATION"] = prediction.get("JUSTIFICATION", "")
        row["GOLD_NAR"] = g["TYPE NARRATEUR"]
        row["GOLD_FOC"] = g["FOCALISATION"]
        row["GOLD_MOD"] = g["MODE NARRATIF"]
        row["GOLD_REG"] = g["REGIME NARRATIF"]
        row["GOLD_ESP"] = g["ESPACE"]
        row["GOLD_INT"] = g["INTRIGUE"]
        row["GOLD_TEM"] = g["TEMPORALITÉ"]
        results.append(row)

        # Checkpoint every 10
        if i % 10 == 0:
            safe_name = model.replace(":", "_").replace("/", "_")
            save_csv(results, f"resultats_{safe_name}.csv")
            print(f"  💾 Checkpoint ({i} novels)")

    safe_name = model.replace(":", "_").replace("/", "_")
    save_csv(results, f"resultats_{safe_name}.csv")
    print(f"  💾 Saved to resultats_{safe_name}.csv")
    print(f"  Processed: {len(results)}/{len(gold)} | Failed: {failed}")

    summary = {}
    overall_c, overall_t = 0, 0
    for crit, s in scores.items():
        if s["total"] > 0:
            summary[crit] = s["correct"] / s["total"] * 100
            overall_c += s["correct"]
            overall_t += s["total"]
        else:
            summary[crit] = 0.0
    summary["OVERALL"] = (overall_c / overall_t * 100) if overall_t > 0 else 0
    summary["processed"] = len(results)
    summary["failed"] = failed
    return summary

def save_csv(rows, filename):
    if not rows:
        return
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

def print_comparison(all_scores):
    criteria = ["TYPE NARRATEUR", "FOCALISATION", "MODE NARRATIF",
                "REGIME NARRATIF", "ESPACE", "INTRIGUE", "TEMPORALITÉ", "OVERALL"]

    print("\n" + "="*90)
    print("FINAL COMPARISON — ALL MODELS")
    print("="*90)

    col_w = 16
    header = f"{'Criteria':<22}"
    for model in all_scores:
        short = model.split(":")[0][:col_w]
        header += f"  {short:>{col_w}}"
    print(header)
    print("-"*90)

    for crit in criteria:
        sep = "──" if crit == "OVERALL" else "  "
        row = f"{sep}{crit:<20}"
        for model, scores in all_scores.items():
            val = scores.get(crit, 0)
            row += f"  {val:>{col_w}.1f}%"
        print(row)

    print("="*90)
    print("\nPreviously tested (for reference):")
    print(f"  {'qwen3:30b':<22}  {'88.3%':>{col_w}}  {'63.3%':>{col_w}}  {'35.0%':>{col_w}}  ...  55.7% overall")
    print(f"  {'qwen72b-limited':<22}  {'92.5%':>{col_w}}  {'50.9%':>{col_w}}  {'32.1%':>{col_w}}  ...  50.9% overall")
    print("="*90)

def main():
    print("Loading gold set...")
    gold = load_gold(GOLD_FILE)
    print(f"  → {len(gold)} novels")

    client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
    all_scores = {}

    for model in MODELS:
        print(f"\nTesting {model}...")
        test = classify(client, 'Réponds uniquement avec ce JSON: {"test": "ok"}', model)
        if test is None:
            print(f"  ❌ {model} not responding — skipping")
            continue
        print(f"  ✓ {model} OK")

        scores = run_model(client, model, gold)
        all_scores[model] = scores

        # Print intermediate scores after each model
        print(f"\n  Scores for {model}:")
        for crit in ["TYPE NARRATEUR","FOCALISATION","MODE NARRATIF","OVERALL"]:
            print(f"    {crit:<20} {scores.get(crit, 0):.1f}%")

    if all_scores:
        print_comparison(all_scores)

if __name__ == "__main__":
    main()