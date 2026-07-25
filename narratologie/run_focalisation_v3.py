"""
run_focalisation_v3.py

Key fix vs v2: instead of asking each section independently,
shows the model ALL 6 sections together and asks it to track
whether the focal character STAYS THE SAME or CHANGES.

This directly solves the FOC_ZERO vs FOC_INT blindness:
- If a 3rd-person narrator + focal character is consistent = check if narrator
  is restricted (FOC_INT) or omniscient by nature (FOC_ZERO)
- If focal character CHANGES between sections = FOC_VAR

Uses Riccardo's exact definitions from Grille_Narratologique.csv.
Model: qwen3:30b on localhost:11435
"""

import csv, json, os, re, requests, time
from collections import Counter

OLLAMA_URL = "http://localhost:11435/api/chat"
MODEL      = "qwen3:30b"
GOLD_FILE  = "GOLD_narratologie.csv"
CORPUS_DIR = os.path.expanduser("~/ecopoetique/CORPUS_TOTAL")
OUTPUT     = "resultats_focalisation_v3.csv"
LOG_FILE   = "focalisation_v3.log"

VALID_NAR = ["NAR_AUTOD", "NAR_TEM", "NAR_EXT"]
VALID_FOC = ["FOC_INT", "FOC_EXT", "FOC_ZERO", "FOC_VAR"]

# ── Prompt ────────────────────────────────────────────────────────────────────

PROMPT = """/no_think
Tu es expert en narratologie française. Voici 6 extraits du même roman, pris à des positions différentes (début, 25%, 50%, 75%, fin).

DÉFINITIONS (Grille Narratologique de Riccardo Barontini) :

TYPE DE NARRATEUR :
• NAR_AUTOD : le narrateur EST le protagoniste principal (dit "je" et vit l'histoire).
• NAR_TEM   : le narrateur dit "je" ou "nous" mais est personnage secondaire/témoin.
• NAR_EXT   : le narrateur est ABSENT de l'histoire, raconte à la 3ème personne.

FOCALISATION — lis les 6 extraits ensemble avant de décider :
• FOC_INT  : accès à l'intériorité d'UN SEUL personnage, perspective subjective.
             Le même personnage focal apparaît dans TOUS les extraits.
             La narration est ATTACHÉE à ce personnage — on ne sort jamais de sa perspective.
• FOC_EXT  : AUCUN accès aux pensées ou émotions. Narration descriptive en surface.
• FOC_ZERO : narrateur omniscient ayant accès à l'ensemble des consciences.
             Narration à la 3ème personne. Le narrateur POURRAIT entrer dans n'importe quelle tête.
             ⚠ Même si UN SEUL personnage domine dans ces extraits, c'est FOC_ZERO
               si le narrateur est clairement à la 3ème personne avec accès aux pensées.
             Distinguer de FOC_INT : FOC_ZERO = narrateur omniscient mais sélectif ;
             FOC_INT = narrateur RESTREINT à un seul personnage (style indirect libre exclusif).
• FOC_VAR  : alternance entre plusieurs points de vue internes selon les séquences.
             Le personnage focal CHANGE d'un extrait à l'autre de façon structurée.

MÉTHODE EN 3 ÉTAPES :
1. Identifie la personne grammaticale : "je/nous" → NAR_AUTOD ou NAR_TEM ; "il/elle" → NAR_EXT.
2. Y a-t-il accès aux pensées/émotions ? Si oui, de qui ?
3. Le personnage dont on voit les pensées EST-IL LE MÊME dans tous les extraits ?
   - Oui, même personnage, narration "je" → FOC_INT
   - Oui, même personnage, narration "il/elle" omnisciente → FOC_ZERO (sauf si clairement restreint)
   - Non, personnages différents selon les extraits → FOC_VAR
   - Aucune pensée visible → FOC_EXT

{sections}

Réponds avec ce JSON UNIQUEMENT :
{{
  "etape1_personne": "1ere ou 3eme",
  "etape2_pensees": "oui_un_seul / oui_plusieurs / non",
  "etape3_focal_change": "meme_partout / change_selon_section / aucune_pensee",
  "TYPE NARRATEUR": "NAR_AUTOD|NAR_TEM|NAR_EXT",
  "FOCALISATION": "FOC_INT|FOC_EXT|FOC_ZERO|FOC_VAR"
}}"""

# ── Load gold ─────────────────────────────────────────────────────────────────

def load_gold(path):
    gold = {}
    with open(path, encoding="utf-8") as f:
        rows = list(csv.reader(f, delimiter=";"))
    header = rows[0]
    for row in rows[1:]:
        if not row or not row[0].strip().endswith(".txt"):
            continue
        def col(i): return row[i].strip() if i < len(row) else ""
        fn = col(0)
        nar = col(4); nar = "NAR_AUTOD" if nar == "NAR_AUTO" else nar
        foc = col(6); foc = "FOC_INT"   if foc == "FIC_INT"  else foc
        gold[fn] = {
            "nar": nar, "nar_alt": col(5),
            "foc": foc, "foc_alt": col(7),
            "author": col(2), "title": col(3),
        }
    return gold

# ── Extract 6 sections ────────────────────────────────────────────────────────

def extract_sections(filename):
    path = os.path.join(CORPUS_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    n = len(lines)
    positions = [
        ("DÉBUT (0%)",          lines[:30]),
        ("DÉBUT (5%)",          lines[30:60]),
        ("PREMIER QUART (25%)", lines[int(n*0.25):int(n*0.25)+30]),
        ("MILIEU (50%)",        lines[int(n*0.50):int(n*0.50)+30]),
        ("TROIS QUARTS (75%)",  lines[int(n*0.75):int(n*0.75)+30]),
        ("FIN (100%)",          lines[-30:]),
    ]
    parts = []
    for label, chunk in positions:
        text = "".join(chunk).strip()
        if text:
            parts.append(f"=== {label} ===\n{text}")
    return "\n\n".join(parts)

# ── API call ──────────────────────────────────────────────────────────────────

def classify(sections_text):
    prompt = PROMPT.format(sections=sections_text)
    for attempt in range(3):
        try:
            resp = requests.post(OLLAMA_URL, json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0, "num_predict": 1000, "num_ctx": 8192},
            }, timeout=180)
            raw = resp.json()["message"].get("content", "").strip()
            raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if not m:
                continue
            obj = json.loads(m.group(0))
            nar = obj.get("TYPE NARRATEUR", "").strip().upper()
            foc = obj.get("FOCALISATION",   "").strip().upper()
            if nar in VALID_NAR and foc in VALID_FOC:
                return nar, foc, obj.get("etape3_focal_change", "")
        except Exception:
            if attempt < 2:
                time.sleep(3)
    return None, None, ""

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    gold = load_gold(GOLD_FILE)
    print(f"Gold set: {len(gold)} novels")

    # Resume
    done = {}
    if os.path.exists(OUTPUT):
        with open(OUTPUT, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                done[row["File"]] = row
        print(f"Resuming: {len(done)} already done")

    remaining = [fn for fn in gold if fn not in done]
    print(f"To classify: {len(remaining)} | Model: {MODEL}\n{'='*65}")

    nar_scores = {"c": 0, "t": 0}
    foc_scores = {"c": 0, "t": 0}
    foc_by = {}

    # Count already-done
    for fn, row in done.items():
        if fn not in gold: continue
        nar_scores["t"] += 1; foc_scores["t"] += 1
        if row.get("NAR_correct") == "1": nar_scores["c"] += 1
        if row.get("FOC_correct") == "1": foc_scores["c"] += 1

    file_exists = os.path.exists(OUTPUT)
    out_f  = open(OUTPUT,   "a", encoding="utf-8", newline="")
    log_f  = open(LOG_FILE, "a", encoding="utf-8")
    fields = ["File", "TYPE NARRATEUR", "FOCALISATION", "focal_change",
              "GOLD_NAR", "GOLD_FOC", "NAR_correct", "FOC_correct"]
    writer = csv.DictWriter(out_f, fieldnames=fields)
    if not file_exists or os.path.getsize(OUTPUT) == 0:
        writer.writeheader()

    for i, fn in enumerate(remaining, 1):
        g = gold[fn]
        print(f"[{i:>2}/{len(remaining)}] {fn[:52]}", end="", flush=True)

        sections = extract_sections(fn)
        if sections is None:
            print(" ⚠ not found")
            continue

        t0 = time.time()
        nar, foc, focal_change = classify(sections)
        elapsed = time.time() - t0

        if nar is None:
            print(f" ✗ failed ({elapsed:.0f}s)")
            log_f.write(f"FAILED: {fn}\n")
            continue

        nar_ok = (nar == g["nar"]) or (g["nar_alt"] and nar == g["nar_alt"])
        foc_ok = (foc == g["foc"]) or (g["foc_alt"] and foc == g["foc_alt"])

        nar_scores["t"] += 1; foc_scores["t"] += 1
        if nar_ok: nar_scores["c"] += 1
        if foc_ok: foc_scores["c"] += 1

        # Track FOC breakdown
        key = g["foc"]
        if key not in foc_by: foc_by[key] = [0, 0]
        foc_by[key][1] += 1
        if foc_ok: foc_by[key][0] += 1

        nar_acc = nar_scores["c"] / nar_scores["t"] * 100
        foc_acc = foc_scores["c"] / foc_scores["t"] * 100
        sym = lambda ok: "✓" if ok else "✗"

        print(
            f" {elapsed:.0f}s | NAR={nar}{sym(nar_ok)}(gold:{g['nar']}) "
            f"FOC={foc}{sym(foc_ok)}(gold:{g['foc']}) "
            f"| NAR={nar_acc:.0f}% FOC={foc_acc:.0f}%"
        )
        log_f.write(f"{fn}: NAR={nar}({'OK' if nar_ok else 'WRONG'}) FOC={foc}({'OK' if foc_ok else 'WRONG'}) focal_change={focal_change}\n")
        log_f.flush()

        writer.writerow({
            "File": fn, "TYPE NARRATEUR": nar, "FOCALISATION": foc,
            "focal_change": focal_change,
            "GOLD_NAR": g["nar"], "GOLD_FOC": g["foc"],
            "NAR_correct": "1" if nar_ok else "0",
            "FOC_correct": "1" if foc_ok else "0",
        })
        out_f.flush()

    out_f.close(); log_f.close()

    print(f"\n{'='*65}")
    nar_acc = nar_scores["c"] / nar_scores["t"] * 100 if nar_scores["t"] else 0
    foc_acc = foc_scores["c"] / foc_scores["t"] * 100 if foc_scores["t"] else 0
    print(f"  TYPE NARRATEUR  {nar_scores['c']:>2}/{nar_scores['t']:>2}  ({nar_acc:.1f}%)")
    print(f"  FOCALISATION    {foc_scores['c']:>2}/{foc_scores['t']:>2}  ({foc_acc:.1f}%)")
    print(f"\n  FOC breakdown:")
    for k, (c, t) in sorted(foc_by.items()):
        print(f"    {k}: {c}/{t} ({c/t*100:.0f}%)")
    print(f"\n  Output: {OUTPUT}")

if __name__ == "__main__":
    main()
