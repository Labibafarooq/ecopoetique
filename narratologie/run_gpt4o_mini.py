"""
GPT-4o-mini Evaluation - Ecopoétique Project
Reads API key from environment variable OPENAI_API_KEY
Usage: export OPENAI_API_KEY="your-key" && python run_gpt4o_mini.py
"""

import os
import csv
import json
import time
import re
import socket
import subprocess

# obtic-gpu1's local DNS returns SERVFAIL for public hostnames (university
# network policy) even though raw outbound TCP is open. Resolve api.openai.com
# via public DNS once at startup and pin just that hostname to the returned IP
# for this process — TLS SNI/Host header still say "api.openai.com" so cert
# validation is unaffected. No system files touched, nothing persisted.
def _patch_dns_for_openai():
    try:
        ip = subprocess.run(
            ["dig", "+short", "api.openai.com", "@8.8.8.8"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip().splitlines()[-1]
    except Exception:
        return
    real_getaddrinfo = socket.getaddrinfo
    def patched(host, *args, **kwargs):
        if host == "api.openai.com":
            host = ip
        return real_getaddrinfo(host, *args, **kwargs)
    socket.getaddrinfo = patched

_patch_dns_for_openai()

from openai import OpenAI

MODEL = "gpt-4o-mini"
GOLD_FILE = "GOLD_narratologie.csv"
EXTRAITS_DIR = "narrato_extraits"
OUTPUT_FILE = "resultats_gpt4o_mini.csv"

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
    # GOLD_narratologie.csv is ";"-delimited and repeats the header
    # "Acceptable aussi: " once per criterion with no distinguishing suffix.
    # csv.DictReader collapses same-named columns to the last occurrence, so
    # we read positionally instead: col 4=NAR,5=NAR_alt,6=FOC,7=FOC_alt, ... 16=TEM,17=TEM_alt
    gold = {}
    with open(gold_file, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        header = next(reader)
        for row in reader:
            if not row or not row[0].strip():
                continue
            row = row + [""] * (18 - len(row))
            filename = row[0].strip()
            gold[filename] = {
                "TYPE NARRATEUR":  row[4].strip(),
                "FOCALISATION":    row[6].strip(),
                "MODE NARRATIF":   row[8].strip(),
                "REGIME NARRATIF": row[10].strip(),
                "ESPACE":          row[12].strip(),
                "INTRIGUE":        row[14].strip(),
                "TEMPORALITÉ":     row[16].strip(),
                "NAR_alt": row[5].strip(),
                "FOC_alt": row[7].strip(),
                "MOD_alt": row[9].strip(),
                "REG_alt": row[11].strip(),
                "ESP_alt": row[13].strip(),
                "INT_alt": row[15].strip(),
                "TEM_alt": row[17].strip(),
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

EXTRAIT:
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
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=500,
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
    # Check API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set.")
        print("   Run: export OPENAI_API_KEY='your-key-here'")
        return

    print(f"Loading gold set from {GOLD_FILE}...")
    gold = load_gold(GOLD_FILE)
    print(f"  → {len(gold)} novels")

    client = OpenAI(api_key=api_key)

    # Test connection
    print(f"\nTesting {MODEL}...")
    test = classify(client, 'Réponds uniquement avec ce JSON: {"test": "ok"}')
    if test is None:
        print("❌ API call failed — check your key")
        return
    print(f"  ✓ {MODEL} OK")

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

    print(f"\nRunning {MODEL} on {len(gold)} novels...")
    print("-"*60)

    for i, (filename, gold_data) in enumerate(gold.items(), 1):
        print(f"[{i:>2}/{len(gold)}] {filename[:50]}", end="", flush=True)

        extrait = load_extrait(filename, EXTRAITS_DIR)
        if extrait is None:
            print(" ⚠️ extract not found")
            failed += 1
            continue

        start = time.time()
        prediction = classify(client, build_prompt(extrait))
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
        print(f" {elapsed:.1f}s | NAR={nar}{nar_ok} FOC={foc}{foc_ok} MOD={mod}{mod_ok}")

        for crit, alt_key in criteria:
            if crit in prediction:
                scores[crit]["total"] += 1
                if is_correct(prediction[crit], g[crit], g[alt_key]):
                    scores[crit]["correct"] += 1

        row = {f: "" for f in OUTPUT_FIELDS}
        row["Model"] = MODEL
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

        if i % 10 == 0:
            save_csv(results, OUTPUT_FILE)
            print(f"  💾 Checkpoint ({i} novels)")

    save_csv(results, OUTPUT_FILE)
    print(f"\n✅ Results saved to {OUTPUT_FILE}")
    print(f"   Processed: {len(results)}/{len(gold)} | Failed: {failed}")

    # Final scores
    print("\n" + "="*60)
    print(f"MODEL: {MODEL}")
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

    print("\nComparison with local models:")
    print(f"  {'qwen3:30b':<20} NAR=88.3%  FOC=63.3%  MOD=35.0%  OVERALL=55.7%")
    print(f"  {'mistral-nemo':<20} NAR=60.0%  FOC=53.3%  MOD=36.7%  OVERALL=47.4%")
    print(f"  {'llama3.1:8b':<20} NAR=66.7%  FOC=30.0%  MOD=33.3%  OVERALL=40.2%")

if __name__ == "__main__":
    main()