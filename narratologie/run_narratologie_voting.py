"""
Pipeline Narratologique - VOTING version
Sends 8 small sections separately, takes majority vote per criterion.
Much more accurate than one big prompt.
"""

import os
import csv
import json
import time
import re
from collections import Counter
from openai import OpenAI

OLLAMA_BASE_URL = "http://127.0.0.1:11435/v1"
MODEL = "qwen3:30b"
GOLD_FILE = "GOLD_narratologie.csv"
CORPUS_DIR = "../CORPUS_TOTAL"
OUTPUT_FILE = "resultats_qwen3_30b_voting.csv"

LINES_PER_SECTION = 35   # same size model handled well before
SECTIONS = 8             # 8 votes per novel

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
    "VOTES", "JUSTIFICATION",
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

def extract_sections(filename, corpus_dir, sections=SECTIONS, lines_per_section=LINES_PER_SECTION):
    """Extract evenly distributed sections from full novel."""
    path = os.path.join(corpus_dir, filename)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        all_lines = f.readlines()
    total = len(all_lines)
    result = []
    for i in range(sections):
        ratio = i / (sections - 1) if sections > 1 else 0
        index = int(total * ratio)
        start = max(0, min(index, total - lines_per_section))
        section_text = "".join(all_lines[start:start + lines_per_section])
        result.append((int(ratio * 100), section_text))
    return result

def build_prompt(section_text, position_pct):
    return f"""Tu es un expert en narratologie française. Analyse cet extrait (position {position_pct}% du roman) et réponds UNIQUEMENT en JSON.

RÈGLES: Analyse UNIQUEMENT ce texte. Réponds avec les codes exacts ci-dessous, sans markdown.

TYPE NARRATEUR: NAR_AUTOD ("je"=protagoniste), NAR_TEM ("je"=témoin), NAR_EXT (3ème personne)
FOCALISATION: FOC_INT (pensées d'UN seul), FOC_EXT (aucune pensée), FOC_ZERO (pensées de PLUSIEURS), FOC_VAR (alternance)
MODE NARRATIF: MOD_EVT (actions), MOD_DESC (descriptions), MOD_INTR (introspection), MOD_MIX (équilibré)
REGIME NARRATIF: REG_AUTO (autofiction), REG_REAL (réaliste), REG_FANT (fantastique), REG_SPEC (spéculatif)
ESPACE: ESP_UNIT (un lieu), ESP_FRAG (lieux multiples), ESP_ITIN (déplacement), ESP_IMAG (imaginaire)
INTRIGUE: INTR_LIN (linéaire), INTR_FRAG (fragmenté), INTR_CYC (cyclique)
TEMPORALITÉ: TEMP_LIN (chronologique), TEMP_DIS (analepses), TEMP_DESORD (éclaté)

EXTRAIT:
{section_text}

JSON:
{{
  "TYPE NARRATEUR": "CODE",
  "FOCALISATION": "CODE",
  "MODE NARRATIF": "CODE",
  "REGIME NARRATIF": "CODE",
  "ESPACE": "CODE",
  "INTRIGUE": "CODE",
  "TEMPORALITÉ": "CODE"
}}"""

def normalize_prediction(prediction):
    if not prediction:
        return prediction
    key_fixes = {
        "REGIME NARRATIV": "REGIME NARRATIF",
        "TEMPORALITE": "TEMPORALITÉ",
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
            # Validate — if not a valid code, set to None
            if fixed[crit] not in VALID_CODES[crit]:
                fixed[crit] = None
    return fixed

def parse_response(raw):
    if not raw or not raw.strip():
        return None
    raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
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

def classify_section(client, prompt):
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt + " /no_think"}],
            temperature=0,
            timeout=120,
            max_tokens=500,
        )
        return parse_response(response.choices[0].message.content)
    except Exception as e:
        return None

def majority_vote(all_predictions):
    """Take majority vote across all section predictions."""
    result = {}
    vote_summary = {}
    for crit in VALID_CODES:
        votes = [p[crit] for p in all_predictions if p and p.get(crit) in VALID_CODES[crit]]
        if votes:
            counter = Counter(votes)
            winner = counter.most_common(1)[0][0]
            result[crit] = winner
            vote_summary[crit] = dict(counter)
        else:
            result[crit] = "?"
            vote_summary[crit] = {}
    return result, vote_summary

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
    print(f"  → VOTING: {SECTIONS} sections × {LINES_PER_SECTION} lines each")
    print(f"  → Full novel coverage via majority vote")

    client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")

    print("\nTesting Ollama connection...")
    test = classify_section(client, 'Réponds uniquement avec ce JSON: {"test": "ok"}')
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

    print(f"\nRunning {MODEL} with voting...")
    print("-"*60)

    for i, (filename, gold_data) in enumerate(gold.items(), 1):
        print(f"[{i:>2}/{len(gold)}] {filename[:45]}", end="", flush=True)

        sections = extract_sections(filename, CORPUS_DIR)
        if sections is None:
            print(f" ⚠️ not found")
            failed += 1
            continue

        start = time.time()
        all_predictions = []
        for pos_pct, section_text in sections:
            pred = classify_section(client, build_prompt(section_text, pos_pct))
            if pred:
                all_predictions.append(pred)

        elapsed = time.time() - start

        if not all_predictions:
            print(f" ❌ all sections failed ({elapsed:.0f}s)")
            failed += 1
            continue

        final, vote_summary = majority_vote(all_predictions)
        g = gold_data

        nar = final.get('TYPE NARRATEUR', '?')
        foc = final.get('FOCALISATION', '?')
        mod = final.get('MODE NARRATIF', '?')

        nar_ok = "✓" if is_correct(nar, g["TYPE NARRATEUR"], g["NAR_alt"]) else "✗"
        foc_ok = "✓" if is_correct(foc, g["FOCALISATION"],   g["FOC_alt"]) else "✗"
        mod_ok = "✓" if is_correct(mod, g["MODE NARRATIF"],  g["MOD_alt"]) else "✗"
        n_votes = len(all_predictions)
        print(f" {elapsed:.0f}s ({n_votes}votes) | NAR={nar}{nar_ok} FOC={foc}{foc_ok} MOD={mod}{mod_ok}")

        for crit, alt_key in criteria:
            val = final.get(crit, '?')
            if val != '?':
                scores[crit]["total"] += 1
                if is_correct(val, g[crit], g[alt_key]):
                    scores[crit]["correct"] += 1

        row = {f: "" for f in OUTPUT_FIELDS}
        row["Model"] = MODEL + "_voting"
        row["File"] = filename
        for crit in VALID_CODES:
            row[crit] = final.get(crit, "")
        row["VOTES"] = json.dumps(vote_summary, ensure_ascii=False)
        row["JUSTIFICATION"] = f"{n_votes}/{SECTIONS} sections succeeded"
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
    print(f"   Processed: {len(results)} | Failed: {failed}")

    print("\n" + "="*60)
    print(f"MODEL: {MODEL} — VOTING ({SECTIONS} sections)")
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
    print("\nComparison:")
    print(f"  {'125-line samples':<25} NAR=88.3%  FOC=63.3%  MOD=35.0%  OVERALL=55.7%")
    print(f"  {'voting (8 sections)':<25} NAR=?      FOC=?      MOD=?      OVERALL=?")

if __name__ == "__main__":
    main()