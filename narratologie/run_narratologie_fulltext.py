"""
Pipeline Narratologique - FULL TEXT version
Uses complete novels from CORPUS_TOTAL instead of 125-line samples
Compares results against GOLD_narratologie.csv
"""

import os
import csv
import json
import time
import re
from openai import OpenAI

OLLAMA_BASE_URL = "http://127.0.0.1:11434/v1"
MODEL = "qwen3:30b"
GOLD_FILE = "GOLD_narratologie.csv"
CORPUS_DIR = "../CORPUS_TOTAL"
OUTPUT_FILE = "resultats_qwen3_30b_fulltext.csv"

# Max lines to send — full novel can be huge, so we cap at 600 lines
# (vs 125 before) — evenly distributed across the novel
MAX_LINES = 300
SECTIONS = 8  # number of sections to sample from

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
    "GOLD_NAR", "GOLD_FOC", "GOLD_MOD", "GOLD_REG",
    "GOLD_ESP", "GOLD_INT", "GOLD_TEM"
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

def load_full_novel(filename, corpus_dir, max_lines=MAX_LINES, sections=SECTIONS):
    """
    Load a novel and extract evenly distributed sections.
    Much more representative than beginning/35%/50%/75%/end.
    """
    path = os.path.join(corpus_dir, filename)
    if not os.path.exists(path):
        return None

    with open(path, encoding="utf-8") as f:
        all_lines = f.readlines()

    total = len(all_lines)
    lines_per_section = max_lines // sections

    result = []
    for i in range(sections):
        ratio = i / (sections - 1) if sections > 1 else 0
        index = int(total * ratio)
        start = max(0, min(index, total - lines_per_section))
        label = f"--- {int(ratio*100)}% ---"
        result.append(f"\n\n{label}\n\n")
        result.extend(all_lines[start:start + lines_per_section])

    return "".join(result)

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
⚠️ Ne pas choisir FOC_VAR par défaut.

MODE NARRATIF:
• MOD_EVT  : priorité aux ACTIONS et événements concrets
• MOD_DESC : priorité aux DESCRIPTIONS de lieux/objets/atmosphères
• MOD_INTR : priorité à l'INTROSPECTION et réflexions intérieures
• MOD_MIX  : mélange équilibré de plusieurs modes
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

EXTRAIT (8 sections distribuées sur l'ensemble du roman):
""" + extrait + """

Réponds avec EXACTEMENT ce JSON:
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
    if not prediction:
        return prediction
    key_fixes = {
        "REGIME NARRATIV": "REGIME NARRATIF",
        "TEMPORALITE": "TEMPORALITÉ",
        "MODE NARRATIF DOMINANT": "MODE NARRATIF",
    }
    fixed = {}
    for k, v in prediction.items():
        fixed[key_fixes.get(k, k)] = v
    value_fixes = {
        "NARR_EXT": "NAR_EXT", "NARR_AUTOD": "NAR_AUTOD",
        "FOC_VARIABLE": "FOC_VAR", "MOD_EVENEMENTS": "MOD_EVT",
        "MOD_INTROSPECTION": "MOD_INTR", "MOD_MIXTE": "MOD_MIX",
    }
    for crit in VALID_CODES:
        if crit in fixed:
            val = str(fixed[crit]).strip().upper()
            fixed[crit] = value_fixes.get(val, val)
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
        return normalize_prediction(json.loads(raw.strip()))
    except json.JSONDecodeError:
        return None

def classify(client, prompt):
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt + " /no_think"}],
            temperature=0,
            timeout=600,
            max_tokens=4000,
        )
        return parse_response(response.choices[0].message.content)
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None

def is_correct(predicted, gold_main, gold_alt):
    if predicted == gold_main:
        return True
    if gold_alt and predicted == gold_alt:
        return True
    return False

def save_csv(rows, filename):
    if not rows:
        return
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

def main():
    print(f"Loading gold set from {GOLD_FILE}...")
    gold = load_gold(GOLD_FILE)
    print(f"  → {len(gold)} novels")
    print(f"  → Using FULL TEXT from {CORPUS_DIR}")
    print(f"  → {MAX_LINES} lines per novel ({SECTIONS} sections)")

    client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")

    print("\nTesting Ollama connection...")
    test = classify(client, 'Réponds uniquement avec ce JSON: {"test": "ok"}')
    if test is None:
        print("❌ Ollama not responding")
        return
    print(f"  ✓ OK")

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
    not_found = 0

    print(f"\nRunning {MODEL} with full text...")
    print("-"*60)

    for i, (filename, gold_data) in enumerate(gold.items(), 1):
        print(f"[{i:>2}/{len(gold)}] {filename[:50]}", end="", flush=True)

        text = load_full_novel(filename, CORPUS_DIR)
        if text is None:
            print(f" ⚠️ not found in CORPUS_TOTAL")
            not_found += 1
            continue

        start = time.time()
        prediction = classify(client, build_prompt(text))
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
        row["Model"] = MODEL + "_fulltext"
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

        if i % 5 == 0:
            save_csv(results, OUTPUT_FILE)
            print(f"  💾 Checkpoint ({i} novels)")

    save_csv(results, OUTPUT_FILE)
    print(f"\n✅ Saved to {OUTPUT_FILE}")
    print(f"   Processed: {len(results)} | Failed: {failed} | Not found: {not_found}")

    # Final scores
    print("\n" + "="*60)
    print(f"MODEL: {MODEL} — FULL TEXT ({MAX_LINES} lines, {SECTIONS} sections)")
    print("="*60)
    overall_c, overall_t = 0, 0
    for crit, s in scores.items():
        if s["total"] > 0:
            acc = s["correct"] / s["total"] * 100
            bar = "█" * int(acc / 5)
            print(f"  {crit:<20} {s['correct']:>2}/{s['total']:>2}  ({acc:>5.1f}%)  {bar}")
            overall_c += s["correct"]
            overall_t += s["total"]
    print("-"*60)
    if overall_t > 0:
        print(f"  {'OVERALL':<20} {overall_c:>3}/{overall_t:>3}  ({overall_c/overall_t*100:>5.1f}%)")
    print("="*60)
    print("\nComparison with 125-line samples baseline:")
    print(f"  {'qwen3:30b 125 lines':<25} NAR=88.3%  FOC=63.3%  MOD=35.0%  OVERALL=55.7%")
    print(f"  {'qwen3:30b FULL TEXT':<25} NAR=?      FOC=?      MOD=?      OVERALL=?")

if __name__ == "__main__":
    main()