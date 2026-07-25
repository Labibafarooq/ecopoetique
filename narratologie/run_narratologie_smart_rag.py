"""
Pipeline Narratologique — Smart RAG Sampling
Instead of random 125 lines, uses RAG to find the most narratologically
relevant lines per criterion, combines into a smart ~150 line sample,
then runs the same classifier that works at 55.7%.

Key difference from pure RAG: we pre-filter to get RELEVANT lines,
then classify from those lines — not from a giant prompt.
"""

import os
import csv
import json
import re
import time
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from openai import OpenAI

OLLAMA_URL   = "http://127.0.0.1:11434/v1"
OLLAMA_MODEL = "qwen3:30b"
GOLD_FILE    = "GOLD_narratologie.csv"
CORPUS_DIR   = "../CORPUS_TOTAL"
OUTPUT_FILE  = "resultats_qwen3_30b_smart_rag.csv"
EMBED_MODEL  = "Lajavaness/sentence-camembert-large"

# Lines to retrieve per criterion query
LINES_PER_QUERY = 8
# Total lines in smart sample = LINES_PER_QUERY × number of queries

# Narratological queries — targeted at specific structural features
CRITERION_QUERIES = {
    "TYPE NARRATEUR": [
        "je suis le personnage principal de cette histoire",
        "il elle marcha dit fit troisième personne narrateur externe",
        "je témoin je regardais j'observais les autres",
    ],
    "FOCALISATION": [
        "il pensait elle se souvenait ses pensées intérieures",
        "elle ressentait il imaginait conscience intérieure",
        "plusieurs personnages pensaient chacun de leur côté",
        "seulement les actions visibles dialogues sans pensées",
    ],
    "MODE NARRATIF": [
        "il courut elle fit l'action se déroula événement",
        "le paysage la lumière la couleur décrivait décoration",
        "je réfléchissais je me demandais méditation intérieure",
    ],
    "REGIME NARRATIF": [
        "ma vie mon enfance autobiographie ma propre histoire",
        "le monde ordinaire réaliste quotidien contemporain",
        "fantastique surnaturel étrange inexplicable apparition",
        "futur dystopie monde imaginaire spéculatif",
    ],
    "ESPACE": [
        "voyage route chemin déplacement ils partirent",
        "la maison la chambre le même endroit lieu unique",
        "plusieurs villes pays lieux différents",
    ],
    "INTRIGUE": [
        "autrefois jadis dans le passé il se souvint flashback",
        "ensuite puis après chronologie ordre des événements",
        "rupture saut ellipse fragment discontinu",
    ],
    "TEMPORALITÉ": [
        "il se souvint autrefois enfance souvenir passé retour",
        "puis ensuite après le lendemain chronologie linéaire",
        "simultanément en même temps plusieurs temporalités",
    ],
}

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
    "GOLD_ESP", "GOLD_INT", "GOLD_TEM",
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

def load_novel_lines(filename, corpus_dir):
    path = os.path.join(corpus_dir, filename)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        lines = [l.strip()[:400] for l in f if l.strip() and len(l.strip()) > 15]
    return lines

def build_faiss_index(lines, embed_model):
    embeddings = embed_model.encode(lines, show_progress_bar=False, device="cpu",
                                    batch_size=128, normalize_embeddings=True)
    embeddings = np.array(embeddings, dtype=np.float32)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    return index, embeddings

def retrieve_lines(query, index, lines, embed_model, top_k=LINES_PER_QUERY):
    q_emb = embed_model.encode([query], normalize_embeddings=True)
    q_emb = np.array(q_emb, dtype=np.float32)
    scores, indices = index.search(q_emb, top_k)
    return [(lines[idx], float(scores[0][i]))
            for i, idx in enumerate(indices[0]) if idx < len(lines)]

def build_smart_sample(lines, index, embed_model):
    """
    Retrieve the most narratologically relevant lines for each criterion.
    Returns a structured text sample with sections per criterion.
    """
    seen = set()
    sections = []

    for crit, queries in CRITERION_QUERIES.items():
        crit_lines = []
        for query in queries:
            results = retrieve_lines(query, index, lines, embed_model,
                                     top_k=LINES_PER_QUERY)
            for line, score in results:
                if line not in seen:
                    seen.add(line)
                    crit_lines.append(line)
                if len(crit_lines) >= LINES_PER_QUERY:
                    break

        if crit_lines:
            sections.append(f"\n[Passages pertinents — {crit}]\n" +
                           "\n".join(crit_lines[:LINES_PER_QUERY]))

    return "\n".join(sections)

def build_prompt(smart_sample):
    return """Tu es un expert en narratologie française. Analyse ces passages extraits d'un roman et classifie les 7 critères. Ces passages ont été sélectionnés spécifiquement pour chaque critère narratologique.

RÈGLES ABSOLUES:
- Analyse UNIQUEMENT le texte fourni
- Ne réponds JAMAIS avec X — choisis toujours le code le plus probable
- Réponds UNIQUEMENT avec le JSON demandé

TYPE NARRATEUR: NAR_AUTOD (je=protagoniste), NAR_TEM (je=témoin), NAR_EXT (3ème personne)
FOCALISATION: FOC_INT (pensées d'UN seul), FOC_EXT (aucune pensée), FOC_ZERO (PLUSIEURS personnages), FOC_VAR (alternance)
⚠️ FOC_ZERO = PLUSIEURS personnages. FOC_INT = UN seul.
MODE NARRATIF: MOD_EVT (actions), MOD_DESC (descriptions), MOD_INTR (introspection), MOD_MIX (équilibré)
REGIME NARRATIF: REG_AUTO (autofiction), REG_REAL (réaliste), REG_FANT (fantastique), REG_SPEC (spéculatif)
ESPACE: ESP_UNIT (un lieu), ESP_FRAG (lieux multiples), ESP_ITIN (déplacement), ESP_IMAG (imaginaire)
INTRIGUE: INTR_LIN (linéaire), INTR_FRAG (fragmenté), INTR_CYC (cyclique)
TEMPORALITÉ: TEMP_LIN (chronologique), TEMP_DIS (analepses), TEMP_DESORD (éclaté)

""" + smart_sample + """

Réponds avec EXACTEMENT ce JSON:
{
  "TYPE NARRATEUR": "CODE",
  "FOCALISATION": "CODE",
  "MODE NARRATIF": "CODE",
  "REGIME NARRATIF": "CODE",
  "ESPACE": "CODE",
  "INTRIGUE": "CODE",
  "TEMPORALITÉ": "CODE",
  "JUSTIFICATION": "1-2 phrases basées sur les passages"
}"""

def classify(client, prompt):
    try:
        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            timeout=300,
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

    print(f"\nLoading embedding model: {EMBED_MODEL}")
    embed_model = SentenceTransformer(EMBED_MODEL)
    print(f"  ✓ Model loaded")

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
    scores  = {c[0]: {"correct": 0, "total": 0} for c in criteria_map}
    results = []
    failed  = 0

    print(f"\nRunning Smart RAG Sampling pipeline...")
    print(f"  {LINES_PER_QUERY} lines per criterion query")
    print(f"  ~{LINES_PER_QUERY * sum(len(v) for v in CRITERION_QUERIES.values())} total lines per novel")
    print("-"*65)

    for i, (filename, gold_data) in enumerate(gold.items(), 1):
        print(f"[{i:>2}/{len(gold)}] {filename[:45]}", end="", flush=True)

        lines = load_novel_lines(filename, CORPUS_DIR)
        if lines is None:
            print(f" ⚠️ not found")
            continue

        start = time.time()

        # Build FAISS index
        index, _ = build_faiss_index(lines, embed_model)

        # Build smart sample — narratologically relevant lines
        smart_sample = build_smart_sample(lines, index, embed_model)

        # Classify
        prompt = build_prompt(smart_sample)
        pred   = classify(client, prompt)
        elapsed = time.time() - start

        if pred is None:
            print(f" ❌ ({elapsed:.0f}s)")
            failed += 1
            continue

        g = gold_data
        nar = pred.get("TYPE NARRATEUR", "?")
        foc = pred.get("FOCALISATION",   "?")
        mod = pred.get("MODE NARRATIF",  "?")

        nar_ok = "✓" if is_correct(nar, g["TYPE NARRATEUR"], g["NAR_alt"]) else "✗"
        foc_ok = "✓" if is_correct(foc, g["FOCALISATION"],   g["FOC_alt"]) else "✗"
        mod_ok = "✓" if is_correct(mod, g["MODE NARRATIF"],  g["MOD_alt"]) else "✗"
        print(f" {elapsed:.0f}s | NAR={nar}{nar_ok} FOC={foc}{foc_ok} MOD={mod}{mod_ok}")

        for crit, alt_key in criteria_map:
            val = pred.get(crit, "?")
            if val != "?":
                scores[crit]["total"] += 1
                if is_correct(val, g[crit], g[alt_key]):
                    scores[crit]["correct"] += 1

        row = {f: "" for f in OUTPUT_FIELDS}
        row["Model"] = OLLAMA_MODEL + "_smart_rag"
        row["File"]  = filename
        for crit in VALID_CODES:
            row[crit] = pred.get(crit, "")
        row["JUSTIFICATION"] = pred.get("JUSTIFICATION", "")
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

    print("\n" + "="*65)
    print(f"MODEL: {OLLAMA_MODEL} — SMART RAG SAMPLING")
    print("="*65)
    overall_c = overall_t = 0
    for crit, s in scores.items():
        if s["total"] > 0:
            acc = s["correct"] / s["total"] * 100
            bar = "█" * int(acc / 5)
            print(f"  {crit:<20} {s['correct']:>2}/{s['total']:>2}  ({acc:>5.1f}%)  {bar}")
            overall_c += s["correct"]; overall_t += s["total"]
    print("-"*65)
    if overall_t:
        print(f"  {'OVERALL':<20} {overall_c:>3}/{overall_t:>3}  ({overall_c/overall_t*100:>5.1f}%)")
    print("="*65)
    print("\nFull comparison:")
    print(f"  {'125-line samples':<25} NAR=88.3%  FOC=63.3%  MOD=35.0%  OVERALL=55.7%")
    print(f"  {'RAG full novel':<25} NAR=59.3%  FOC=52.5%  MOD=35.6%  OVERALL=49.6%")
    print(f"  {'title+author':<25} NAR=58.3%  FOC=53.3%  MOD=33.3%  OVERALL=46.9%")
    print(f"  {'Smart RAG sampling':<25} NAR=?      FOC=?      MOD=?      OVERALL=?")

if __name__ == "__main__":
    main()
