"""
Pipeline Narratologique — Title + Author approach
Gives qwen3:30b just the title and author name, lets it use its
training knowledge about the novel to classify all 7 criteria.
Same approach as Riccardo's "RAG" notebook but with qwen3:30b instead of GPT-4o.
"""

import os
import csv
import json
import re
import time
from openai import OpenAI

OLLAMA_URL   = "http://127.0.0.1:11434/v1"
OLLAMA_MODEL = "qwen3:30b"
GOLD_FILE    = "GOLD_narratologie.csv"
OUTPUT_FILE  = "resultats_qwen3_30b_title_author.csv"

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
    "JUSTIFICATION", "KNOWN",
    "GOLD_NAR", "GOLD_FOC", "GOLD_MOD", "GOLD_REG",
    "GOLD_ESP", "GOLD_INT", "GOLD_TEM",
]

def load_gold(gold_file):
    gold = {}
    with open(gold_file, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            filename = row["File"].strip()
            gold[filename] = {
                "author": row.get("Author", "").strip(),
                "title":  row.get("Title", "").strip(),
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

def build_prompt(author, title):
    return f"""Tu es un expert en narratologie française contemporaine.

Classifie ce roman selon les 7 critères narratologiques ci-dessous.
Utilise tes connaissances sur ce roman. Si tu ne le connais pas, dis-le dans JUSTIFICATION et choisis quand même le code le plus probable.

ROMAN: "{title}" par {author}

CODES VALIDES:
TYPE NARRATEUR: 
  NAR_AUTOD = "je" est le protagoniste principal (autofiction/autobiographie)
  NAR_TEM = "je" est un témoin/personnage secondaire
  NAR_EXT = narration à la 3ème personne (il/elle)

FOCALISATION:
  FOC_INT = accès aux pensées d'UN SEUL personnage
  FOC_EXT = aucune pensée, seulement actions et dialogues
  FOC_ZERO = omniscient, accès aux pensées de PLUSIEURS personnages
  FOC_VAR = alternance entre différents personnages selon les séquences

MODE NARRATIF:
  MOD_EVT = priorité aux actions et événements
  MOD_DESC = priorité aux descriptions
  MOD_INTR = priorité à l'introspection et réflexions
  MOD_MIX = mélange équilibré

REGIME NARRATIF:
  REG_AUTO = autobiographique/autofiction
  REG_REAL = réaliste, monde contemporain
  REG_FANT = fantastique
  REG_SPEC = spéculatif/dystopique/uchronique

ESPACE:
  ESP_UNIT = un seul lieu concentré
  ESP_FRAG = lieux multiples fragmentés
  ESP_ITIN = déplacement continu (voyage, itinéraire)
  ESP_IMAG = espace inventé/symbolique

INTRIGUE:
  INTR_LIN = progression linéaire/chronologique
  INTR_FRAG = ruptures fréquentes, discontinu
  INTR_CYC = répétition structurante de motifs

TEMPORALITÉ:
  TEMP_LIN = chronologie respectée
  TEMP_DIS = analepses présentes (retours en arrière)
  TEMP_DESORD = temporalité éclatée, non-linéaire

Réponds avec EXACTEMENT ce JSON:
{{
  "TYPE NARRATEUR": "CODE",
  "FOCALISATION": "CODE",
  "MODE NARRATIF": "CODE",
  "REGIME NARRATIF": "CODE",
  "ESPACE": "CODE",
  "INTRIGUE": "CODE",
  "TEMPORALITÉ": "CODE",
  "KNOWN": true/false,
  "JUSTIFICATION": "1-2 phrases sur ce que tu sais du roman"
}}"""

def classify(client, author, title):
    try:
        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": build_prompt(author, title)}],
            temperature=0,
            timeout=120,
            max_tokens=5000,
        )
        raw = response.choices[0].message.content
        raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
        if '```' in raw:
            m = re.search(r'```(?:json)?\s*(.*?)\s*```', raw, re.DOTALL)
            if m: raw = m.group(1)
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            result = json.loads(m.group(0))
            for crit, valid in VALID_CODES.items():
                if crit in result:
                    val = str(result[crit]).strip().upper()
                    result[crit] = val if val in valid else valid[0]
            return result
        return None
    except Exception as e:
        print(f" [ERR: {e}]", end="")
        return None

def is_correct(predicted, gold_main, gold_alt):
    if predicted == gold_main: return True
    if gold_alt and predicted == gold_alt: return True
    return False

def save_csv(rows, filename):
    if not rows: return
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

def main():
    print("Loading gold set...")
    gold = load_gold(GOLD_FILE)
    print(f"  → {len(gold)} novels")

    # Check columns
    sample = next(iter(gold.values()))
    print(f"  → Author example: '{sample['author']}'")
    print(f"  → Title example:  '{sample['title']}'")

    client = OpenAI(base_url=OLLAMA_URL, api_key="ollama")

    criteria_map = [
        ("TYPE NARRATEUR",  "NAR_alt"),
        ("FOCALISATION",    "FOC_alt"),
        ("MODE NARRATIF",   "MOD_alt"),
        ("REGIME NARRATIF", "REG_alt"),
        ("ESPACE",          "ESP_alt"),
        ("INTRIGUE",        "INT_alt"),
        ("TEMPORALITÉ",     "TEM_alt"),
    ]
    scores      = {c[0]: {"correct": 0, "total": 0} for c in criteria_map}
    known_scores= {c[0]: {"correct": 0, "total": 0} for c in criteria_map}
    results     = []
    failed      = 0
    known_count = 0

    print(f"\nRunning {OLLAMA_MODEL} — title+author only")
    print("-"*65)

    for i, (filename, gold_data) in enumerate(gold.items(), 1):
        author = gold_data["author"]
        title  = gold_data["title"]
        print(f"[{i:>2}/{len(gold)}] {author[:20]:<20} — {title[:25]}", end="", flush=True)

        start = time.time()
        pred  = classify(client, author, title)
        elapsed = time.time() - start

        if pred is None:
            print(f" ❌ ({elapsed:.0f}s)")
            failed += 1
            continue

        g = gold_data
        nar = pred.get("TYPE NARRATEUR", "?")
        foc = pred.get("FOCALISATION",   "?")
        mod = pred.get("MODE NARRATIF",  "?")
        known = pred.get("KNOWN", False)
        if known: known_count += 1

        nar_ok = "✓" if is_correct(nar, g["TYPE NARRATEUR"], g["NAR_alt"]) else "✗"
        foc_ok = "✓" if is_correct(foc, g["FOCALISATION"],   g["FOC_alt"]) else "✗"
        mod_ok = "✓" if is_correct(mod, g["MODE NARRATIF"],  g["MOD_alt"]) else "✗"
        k_sym  = "K" if known else "?"
        print(f" [{k_sym}] {elapsed:.0f}s | NAR={nar}{nar_ok} FOC={foc}{foc_ok} MOD={mod}{mod_ok}")

        for crit, alt_key in criteria_map:
            val = pred.get(crit, "?")
            if val != "?":
                scores[crit]["total"] += 1
                correct = is_correct(val, g[crit], g[alt_key])
                if correct: scores[crit]["correct"] += 1
                if known:
                    known_scores[crit]["total"] += 1
                    if correct: known_scores[crit]["correct"] += 1

        row = {f: "" for f in OUTPUT_FIELDS}
        row["Model"] = OLLAMA_MODEL + "_title_author"
        row["File"]  = filename
        for crit in VALID_CODES:
            row[crit] = pred.get(crit, "")
        row["JUSTIFICATION"] = pred.get("JUSTIFICATION", "")
        row["KNOWN"]         = str(known)
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
    print(f"\n✅ Saved to {OUTPUT_FILE}")
    print(f"   Processed: {len(results)} | Failed: {failed} | Known by model: {known_count}/{len(results)}")

    print("\n" + "="*65)
    print(f"MODEL: {OLLAMA_MODEL} — TITLE+AUTHOR approach")
    print("="*65)
    overall_c = overall_t = 0
    known_c   = known_t   = 0
    for crit, s in scores.items():
        if s["total"] > 0:
            acc  = s["correct"] / s["total"] * 100
            ks   = known_scores[crit]
            kacc = ks["correct"] / ks["total"] * 100 if ks["total"] else 0
            bar  = "█" * int(acc / 5)
            print(f"  {crit:<20} {s['correct']:>2}/{s['total']:>2} ({acc:>5.1f}%)  known:{kacc:>5.1f}%  {bar}")
            overall_c += s["correct"]; overall_t += s["total"]
            known_c   += ks["correct"]; known_t  += ks["total"]

    print("-"*65)
    if overall_t:
        print(f"  {'OVERALL':<20} {overall_c:>3}/{overall_t:>3} ({overall_c/overall_t*100:>5.1f}%)  known:{known_c/known_t*100:>5.1f}%" if known_t else "")
    print("="*65)
    print("\nComparison:")
    print(f"  {'125-line samples':<25} NAR=88.3%  FOC=63.3%  MOD=35.0%  OVERALL=55.7%")
    print(f"  {'RAG full novel':<25} NAR=59.3%  FOC=52.5%  MOD=35.6%  OVERALL=49.6%")
    print(f"  {'title+author':<25} NAR=?      FOC=?      MOD=?      OVERALL=?")

if __name__ == "__main__":
    main()
