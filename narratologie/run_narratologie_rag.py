"""
Pipeline Narratologique — RAG approach
For each novel in the gold set:
1. Embed all sentences using multilingual sentence-transformers
2. Query with 7 narratological questions to retrieve relevant passages
3. Feed retrieved passages to qwen3:30b to classify all 7 criteria
4. Compare against gold set

Uses: paraphrase-multilingual-MiniLM-L12-v2 (French-compatible)
      FAISS for fast vector search
      qwen3:30b via Ollama for classification
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

# ── Config ────────────────────────────────────────────────────────────────────
OLLAMA_URL   = "http://127.0.0.1:11434/v1"
OLLAMA_MODEL = "qwen3:30b"
GOLD_FILE    = "GOLD_narratologie.csv"
CORPUS_DIR   = "../CORPUS_TOTAL"
OUTPUT_FILE  = "resultats_qwen3_30b_RAG.csv"

EMBED_MODEL  = "paraphrase-multilingual-MiniLM-L12-v2"
TOP_K        = 15   # retrieve top 15 sentences per query
CHUNK_SIZE   = 3    # group sentences into chunks of 3 for better context

# ── 7 Narratological queries — one per criterion ──────────────────────────────
QUERIES = {
    "TYPE NARRATEUR": [
        "je suis le personnage principal narrateur autobiographique",
        "il elle narrateur externe troisième personne",
        "je témoin secondaire observe les autres personnages",
    ],
    "FOCALISATION": [
        "pensées intérieures émotions ressenties par le personnage",
        "il pensait elle se souvenait intérieur conscience",
        "plusieurs personnages différents leurs pensées leurs points de vue",
        "actions visibles dialogues sans accès aux pensées",
    ],
    "MODE NARRATIF": [
        "action événement se passa il fit elle courut",
        "description lieu paysage décor atmosphère",
        "réflexion introspection méditation intérieure pensées",
    ],
    "REGIME NARRATIF": [
        "autofiction autobiographie réel vécu ma vie",
        "fantastique surnaturel inexplicable étrange apparition",
        "dystopie futur spéculatif uchronie monde imaginaire",
        "réaliste contemporain quotidien familier",
    ],
    "ESPACE": [
        "lieu unique maison chambre espace concentré",
        "voyage itinéraire déplacement route chemin",
        "plusieurs lieux différents villes pays espaces fragmentés",
        "espace imaginaire symbolique inventé",
    ],
    "INTRIGUE": [
        "chronologique linéaire ordre des événements",
        "rupture saut discontinu fragment ellipse",
        "retour en arrière flashback analepse souvenir passé",
        "répétition cyclique motif récurrent pattern",
    ],
    "TEMPORALITÉ": [
        "retour en arrière analepse souvenir passé enfance autrefois",
        "chronologie linéaire ordre temporel présent passé futur",
        "temporalité éclatée désordre temps non linéaire simultané",
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

# ── Load gold set ─────────────────────────────────────────────────────────────
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

# ── Load and chunk novel ──────────────────────────────────────────────────────
def load_novel_chunks(filename, corpus_dir, chunk_size=CHUNK_SIZE):
    path = os.path.join(corpus_dir, filename)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip() and len(l.strip()) > 20]

    chunks = []
    for i in range(0, len(lines), chunk_size):
        chunk = " ".join(lines[i:i+chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks

# ── Build FAISS index for a novel ────────────────────────────────────────────
def build_index(chunks, embed_model):
    embeddings = embed_model.encode(chunks, show_progress_bar=False,
                                    batch_size=64, normalize_embeddings=True)
    embeddings = np.array(embeddings, dtype=np.float32)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # Inner product = cosine similarity (normalized)
    index.add(embeddings)
    return index, embeddings

# ── Retrieve top-k passages for a query ──────────────────────────────────────
def retrieve(query, index, chunks, embed_model, top_k=TOP_K):
    q_emb = embed_model.encode([query], normalize_embeddings=True)
    q_emb = np.array(q_emb, dtype=np.float32)
    scores, indices = index.search(q_emb, top_k)
    results = []
    for idx, score in zip(indices[0], scores[0]):
        if idx < len(chunks):
            results.append((score, chunks[idx]))
    return results

# ── Build classification prompt ───────────────────────────────────────────────
def build_prompt(filename, retrieved_passages):
    """Build prompt with retrieved passages for each criterion."""
    sections = []
    for crit, passages in retrieved_passages.items():
        section = f"\n--- Passages pertinents pour {crit} ---\n"
        for i, (score, text) in enumerate(passages[:5], 1):
            section += f"{i}. {text[:200]}\n"
        sections.append(section)

    all_passages = "\n".join(sections)

    return f"""Tu es un expert en narratologie française. Analyse ces passages extraits du roman "{filename}" et classifie les 7 critères narratologiques.

RÈGLES:
- Base-toi UNIQUEMENT sur les passages fournis
- Choisis le code le plus probable même si tu n'es pas certain
- Ne réponds JAMAIS avec X — toujours choisir un code valide
- Réponds UNIQUEMENT avec le JSON demandé

CODES VALIDES:
TYPE NARRATEUR: NAR_AUTOD (je=protagoniste), NAR_TEM (je=témoin), NAR_EXT (3ème personne)
FOCALISATION: FOC_INT (pensées d'UN seul), FOC_EXT (aucune pensée), FOC_ZERO (PLUSIEURS personnages), FOC_VAR (alternance)
MODE NARRATIF: MOD_EVT (actions), MOD_DESC (descriptions), MOD_INTR (introspection), MOD_MIX (équilibré)
REGIME NARRATIF: REG_AUTO (autofiction), REG_REAL (réaliste), REG_FANT (fantastique), REG_SPEC (spéculatif)
ESPACE: ESP_UNIT (un lieu), ESP_FRAG (lieux multiples), ESP_ITIN (déplacement), ESP_IMAG (imaginaire)
INTRIGUE: INTR_LIN (linéaire), INTR_FRAG (fragmenté), INTR_CYC (cyclique)
TEMPORALITÉ: TEMP_LIN (chronologique), TEMP_DIS (analepses), TEMP_DESORD (éclaté)

{all_passages}

Réponds avec EXACTEMENT ce JSON:
{{
  "TYPE NARRATEUR": "CODE",
  "FOCALISATION": "CODE",
  "MODE NARRATIF": "CODE",
  "REGIME NARRATIF": "CODE",
  "ESPACE": "CODE",
  "INTRIGUE": "CODE",
  "TEMPORALITÉ": "CODE",
  "JUSTIFICATION": "1-2 phrases basées sur les passages"
}}"""

# ── Classify with Ollama ──────────────────────────────────────────────────────
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
            # Validate codes
            for crit, valid in VALID_CODES.items():
                if crit in result:
                    val = str(result[crit]).strip().upper()
                    if val not in valid:
                        result[crit] = valid[0]  # fallback to first valid code
                    else:
                        result[crit] = val
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

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"Loading gold set...")
    gold = load_gold(GOLD_FILE)
    print(f"  → {len(gold)} novels")

    print(f"\nLoading embedding model: {EMBED_MODEL}")
    print("  (first run downloads ~500MB — may take 1-2 minutes)")
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
    scores = {c[0]: {"correct": 0, "total": 0} for c in criteria_map}
    results = []
    failed = 0
    not_found = 0

    print(f"\nRunning RAG pipeline...")
    print(f"  Embedding model: {EMBED_MODEL}")
    print(f"  Classification model: {OLLAMA_MODEL}")
    print(f"  Top-K passages per query: {TOP_K}")
    print("-"*65)

    for i, (filename, gold_data) in enumerate(gold.items(), 1):
        print(f"[{i:>2}/{len(gold)}] {filename[:45]}", end="", flush=True)

        # Load novel
        chunks = load_novel_chunks(filename, CORPUS_DIR)
        if chunks is None:
            print(f" ⚠️ not found")
            not_found += 1
            continue

        start = time.time()

        # Build FAISS index
        index, _ = build_index(chunks, embed_model)

        # Retrieve relevant passages for each criterion
        retrieved = {}
        for crit, queries in QUERIES.items():
            all_results = []
            for q in queries:
                results_q = retrieve(q, index, chunks, embed_model, top_k=5)
                all_results.extend(results_q)
            # Sort by score, deduplicate
            seen = set()
            unique = []
            for score, text in sorted(all_results, reverse=True):
                if text not in seen:
                    seen.add(text)
                    unique.append((score, text))
            retrieved[crit] = unique[:TOP_K]

        # Classify
        prompt = build_prompt(filename, retrieved)
        prediction = classify(client, prompt)
        elapsed = time.time() - start

        if prediction is None:
            print(f" ❌ ({elapsed:.0f}s)")
            failed += 1
            continue

        g = gold_data
        nar = prediction.get("TYPE NARRATEUR", "?")
        foc = prediction.get("FOCALISATION", "?")
        mod = prediction.get("MODE NARRATIF", "?")

        nar_ok = "✓" if is_correct(nar, g["TYPE NARRATEUR"], g["NAR_alt"]) else "✗"
        foc_ok = "✓" if is_correct(foc, g["FOCALISATION"],   g["FOC_alt"]) else "✗"
        mod_ok = "✓" if is_correct(mod, g["MODE NARRATIF"],  g["MOD_alt"]) else "✗"
        print(f" {elapsed:.0f}s | NAR={nar}{nar_ok} FOC={foc}{foc_ok} MOD={mod}{mod_ok}")

        for crit, alt_key in criteria_map:
            if crit in prediction:
                scores[crit]["total"] += 1
                if is_correct(prediction[crit], g[crit], g[alt_key]):
                    scores[crit]["correct"] += 1

        row = {f: "" for f in OUTPUT_FIELDS}
        row["Model"] = OLLAMA_MODEL + "_RAG"
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

    print("\n" + "="*65)
    print(f"MODEL: {OLLAMA_MODEL} — RAG approach")
    print("="*65)
    overall_c, overall_t = 0, 0
    for crit, s in scores.items():
        if s["total"] > 0:
            acc = s["correct"] / s["total"] * 100
            bar = "█" * int(acc / 5)
            print(f"  {crit:<20} {s['correct']:>2}/{s['total']:>2}  ({acc:>5.1f}%)  {bar}")
            overall_c += s["correct"]
            overall_t += s["total"]
    print("-"*65)
    if overall_t > 0:
        print(f"  {'OVERALL':<20} {overall_c:>3}/{overall_t:>3}  ({overall_c/overall_t*100:>5.1f}%)")
    print("="*65)
    print("\nComparison with baseline:")
    print(f"  {'125-line samples':<25} NAR=88.3%  FOC=63.3%  MOD=35.0%  OVERALL=55.7%")
    print(f"  {'RAG approach':<25} NAR=?      FOC=?      MOD=?      OVERALL=?")

if __name__ == "__main__":
    main()
