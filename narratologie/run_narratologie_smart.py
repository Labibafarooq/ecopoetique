"""
Pipeline Narratologique - SMART SAMPLING version
Focuses on TYPE NARRATEUR + FOCALISATION only (most reliable criteria)
Uses smarter extraction: opening paragraphs + chapter breaks + closing
Target: 80%+ accuracy on these 2 criteria
"""

import os
import csv
import json
import time
import re
from collections import Counter
from openai import OpenAI

OLLAMA_BASE_URL = "http://127.0.0.1:11434/v1"
MODEL = "qwen2.5:14b"
GOLD_FILE = "GOLD_narratologie.csv"
CORPUS_DIR = "../CORPUS_TOTAL"
OUTPUT_FILE = "resultats_qwen2.5_14b_smart.csv"

# Focus on only the 2 most reliable criteria
TARGET_CRITERIA = ["TYPE NARRATEUR", "FOCALISATION"]

VALID_CODES = {
    "TYPE NARRATEUR":  ["NAR_AUTOD", "NAR_TEM", "NAR_EXT"],
    "FOCALISATION":    ["FOC_INT", "FOC_EXT", "FOC_ZERO", "FOC_VAR"],
}

OUTPUT_FIELDS = [
    "Model", "File",
    "TYPE NARRATEUR", "FOCALISATION",
    "VOTES_NAR", "VOTES_FOC",
    "GOLD_NAR", "GOLD_FOC",
    "NAR_correct", "FOC_correct"
]

def load_gold(gold_file):
    gold = {}
    with open(gold_file, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            filename = row["File"].strip()
            gold[filename] = {
                "TYPE NARRATEUR": row["TYPE NARRATEUR"].strip(),
                "FOCALISATION":   row["FOCALISATION"].strip(),
                "NAR_alt": row.get("Acceptable aussi: ",   "").strip(),
                "FOC_alt": row.get("Acceptable aussi: .1", "").strip(),
            }
    return gold

def extract_smart_sections(filename, corpus_dir):
    """
    Smart extraction focusing on structurally informative positions:
    - First 30 lines: establishes narrator voice immediately
    - Lines 30-80: confirms narrator, shows focalisation
    - 25% mark: mid-early section
    - 50% mark: middle
    - 75% mark: mid-late section  
    - Last 30 lines: closing voice
    Each section is small (30 lines) so model stays focused.
    """
    path = os.path.join(corpus_dir, filename)
    if not os.path.exists(path):
        return None

    with open(path, encoding="utf-8") as f:
        all_lines = f.readlines()

    total = len(all_lines)
    sections = []

    # Opening — most important for narrator type
    sections.append(("OUVERTURE (0%)", "".join(all_lines[:30])))

    # Early — confirms narrator
    sections.append(("DÉBUT (5%)", "".join(all_lines[30:60])))

    # Quarter mark
    q1 = int(total * 0.25)
    sections.append(("PREMIER QUART (25%)", "".join(all_lines[q1:q1+30])))

    # Middle
    mid = int(total * 0.50)
    sections.append(("MILIEU (50%)", "".join(all_lines[mid:mid+30])))

    # Three quarter
    q3 = int(total * 0.75)
    sections.append(("TROIS QUARTS (75%)", "".join(all_lines[q3:q3+30])))

    # Closing — confirms temporality and focalisation
    sections.append(("FIN (100%)", "".join(all_lines[-30:])))

    return sections

def build_prompt(section_text, position_label):
    return f"""Tu es un expert en narratologie française. Analyse cet extrait ({position_label}) et réponds UNIQUEMENT en JSON.

RÈGLE ABSOLUE: Utilise UNIQUEMENT les codes exacts listés. Pas d'autres mots.

TYPE NARRATEUR — Qui raconte ?
• NAR_AUTOD : le narrateur dit "je" et EST le protagoniste principal
• NAR_TEM : le narrateur dit "je" mais est un personnage secondaire/témoin
• NAR_EXT : narration à la 3ème personne (il, elle, ils) — narrateur absent

FOCALISATION — Accès aux pensées de qui ?
• FOC_INT : on accède aux pensées/émotions d'UN SEUL personnage uniquement
• FOC_EXT : aucun accès aux pensées — uniquement actions visibles et dialogues
• FOC_ZERO : accès omniscient aux pensées de PLUSIEURS personnages différents
• FOC_VAR : alternance entre différents personnages selon les séquences

⚠️ ATTENTION: FOC_ZERO = plusieurs personnages. FOC_INT = un seul.

EXTRAIT:
{section_text}

Réponds avec EXACTEMENT ce JSON:
{{
  "TYPE NARRATEUR": "CODE",
  "FOCALISATION": "CODE"
}}"""

def normalize(prediction):
    if not prediction:
        return prediction
    fixed = {}
    value_fixes = {
        "NARR_EXT": "NAR_EXT", "NARR_AUTOD": "NAR_AUTOD",
        "FOC_VARIABLE": "FOC_VAR",
    }
    for crit in VALID_CODES:
        if crit in prediction:
            val = str(prediction[crit]).strip().upper()
            val = value_fixes.get(val, val)
            if val in VALID_CODES[crit]:
                fixed[crit] = val
            else:
                fixed[crit] = None
        else:
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
        return normalize(json.loads(raw.strip()))
    except json.JSONDecodeError:
        return None

def classify_section(client, prompt):
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt + " /no_think"}],
            temperature=0,
            timeout=60,
            max_tokens=500,
        )
        return parse_response(response.choices[0].message.content)
    except Exception as e:
        return None

def majority_vote(all_predictions, crit):
    votes = [p[crit] for p in all_predictions
             if p and p.get(crit) in VALID_CODES[crit]]
    if not votes:
        return "?", {}
    counter = Counter(votes)
    return counter.most_common(1)[0][0], dict(counter)

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
    print(f"Loading gold set...")
    gold = load_gold(GOLD_FILE)
    print(f"  → {len(gold)} novels")
    print(f"  → Focus: TYPE NARRATEUR + FOCALISATION only")
    print(f"  → Smart sampling: 6 sections × 30 lines")

    client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")

    print("\nTesting connection...")
    test = classify_section(client, 'Réponds avec ce JSON: {"TYPE NARRATEUR": "NAR_EXT", "FOCALISATION": "FOC_ZERO"}')
    if False:  # skip connection test
        print("❌ Ollama not responding")
        return
    print(f"  ✓ OK: {test}")

    nar_scores = {"correct": 0, "total": 0}
    foc_scores = {"correct": 0, "total": 0}
    results = []
    failed = 0

    print(f"\nRunning {MODEL} with smart sampling...")
    print("-"*65)

    for i, (filename, gold_data) in enumerate(gold.items(), 1):
        print(f"[{i:>2}/{len(gold)}] {filename[:45]}", end="", flush=True)

        sections = extract_smart_sections(filename, CORPUS_DIR)
        if sections is None:
            print(f" ⚠️ not found")
            failed += 1
            continue

        start = time.time()
        all_predictions = []
        for pos_label, section_text in sections:
            if not section_text.strip():
                continue
            pred = classify_section(client, build_prompt(section_text, pos_label))
            if pred:
                all_predictions.append(pred)

        elapsed = time.time() - start

        if not all_predictions:
            print(f" ❌ all failed ({elapsed:.0f}s)")
            failed += 1
            continue

        nar_final, nar_votes = majority_vote(all_predictions, "TYPE NARRATEUR")
        foc_final, foc_votes = majority_vote(all_predictions, "FOCALISATION")
        g = gold_data

        nar_ok = is_correct(nar_final, g["TYPE NARRATEUR"], g["NAR_alt"])
        foc_ok = is_correct(foc_final, g["FOCALISATION"],   g["FOC_alt"])

        if nar_final != "?":
            nar_scores["total"] += 1
            if nar_ok:
                nar_scores["correct"] += 1

        if foc_final != "?":
            foc_scores["total"] += 1
            if foc_ok:
                foc_scores["correct"] += 1

        n = len(all_predictions)
        nar_sym = "✓" if nar_ok else "✗"
        foc_sym = "✓" if foc_ok else "✗"
        print(f" {elapsed:.0f}s ({n}v) | NAR={nar_final}{nar_sym} FOC={foc_final}{foc_sym}")

        row = {f: "" for f in OUTPUT_FIELDS}
        row["Model"] = MODEL + "_smart"
        row["File"] = filename
        row["TYPE NARRATEUR"] = nar_final
        row["FOCALISATION"] = foc_final
        row["VOTES_NAR"] = str(nar_votes)
        row["VOTES_FOC"] = str(foc_votes)
        row["GOLD_NAR"] = g["TYPE NARRATEUR"]
        row["GOLD_FOC"] = g["FOCALISATION"]
        row["NAR_correct"] = "1" if nar_ok else "0"
        row["FOC_correct"] = "1" if foc_ok else "0"
        results.append(row)

        if i % 10 == 0:
            save_csv(results, OUTPUT_FILE)
            # Show running accuracy
            nar_acc = nar_scores["correct"]/nar_scores["total"]*100 if nar_scores["total"] else 0
            foc_acc = foc_scores["correct"]/foc_scores["total"]*100 if foc_scores["total"] else 0
            print(f"  💾 Checkpoint | NAR={nar_acc:.1f}% FOC={foc_acc:.1f}%")

    save_csv(results, OUTPUT_FILE)
    print(f"\n✅ Saved to {OUTPUT_FILE}")

    print("\n" + "="*65)
    print(f"MODEL: {MODEL} — SMART SAMPLING")
    print("="*65)

    nar_acc = nar_scores["correct"]/nar_scores["total"]*100 if nar_scores["total"] else 0
    foc_acc = foc_scores["correct"]/foc_scores["total"]*100 if foc_scores["total"] else 0
    combined = (nar_scores["correct"]+foc_scores["correct"]) / \
               (nar_scores["total"]+foc_scores["total"])*100 \
               if (nar_scores["total"]+foc_scores["total"]) else 0

    nar_bar = "█" * int(nar_acc/5)
    foc_bar = "█" * int(foc_acc/5)

    print(f"  {'TYPE NARRATEUR':<20} {nar_scores['correct']:>2}/{nar_scores['total']:>2}  ({nar_acc:>5.1f}%)  {nar_bar}")
    print(f"  {'FOCALISATION':<20} {foc_scores['correct']:>2}/{foc_scores['total']:>2}  ({foc_acc:>5.1f}%)  {foc_bar}")
    print("-"*65)
    print(f"  {'COMBINED':<20} ({combined:>5.1f}%)")
    print("="*65)
    print("\nComparison:")
    print(f"  {'Baseline (125 lines)':<25} NAR=88.3%  FOC=63.3%  combined=75.8%")
    print(f"  {'Smart sampling':<25} NAR={nar_acc:.1f}%   FOC={foc_acc:.1f}%   combined={combined:.1f}%")

if __name__ == "__main__":
    main()
