"""
run_task0_v5.py  —  Task 0, all 7 criteria

Changes vs v4_all7:
  1. 9 chunks × 50 lines = 450 lines (was 6 × 40 = 240)
     Positions: 0%, 5%, 15%, 28%, 42%, 56%, 70%, 83%, 100%
  2. Counting-based criteria — no more vague "prefer simple/complex"
     TEM: count how many sections have anachronies
     INT: ask if events causally connect
     FOC_ZERO vs VAR: VAR only if novel has named POV chapters
     MOD: inner thoughts alone ≠ INTR; action must be genuinely absent
  3. num_ctx = 24576 to fit larger text
"""

import csv, json, os, re, requests, time
from collections import defaultdict

OLLAMA_URL       = "http://localhost:11435/api/chat"
MODEL            = "qwen3:30b"
GOLD_FILE        = "GOLD_narratologie.csv"
CORPUS_DIR       = os.path.expanduser("~/ecopoetique/CORPUS_TOTAL")
OUTPUT           = "resultats_task0_v5.csv"
LOG_FILE         = "task0_v5.log"
LINES_PER_CHUNK  = 50
N_CHUNKS         = 9

VALID = {
    "NAR": ["NAR_AUTOD", "NAR_TEM", "NAR_EXT"],
    "FOC": ["FOC_INT", "FOC_EXT", "FOC_ZERO", "FOC_VAR"],
    "MOD": ["MOD_EVT", "MOD_DESC", "MOD_INTR", "MOD_MIX"],
    "REG": ["REG_AUTO", "REG_REAL", "REG_FANT", "REG_SPEC"],
    "ESP": ["ESP_UNIT", "ESP_FRAG", "ESP_ITIN", "ESP_IMAG"],
    "INT": ["INTR_LIN", "INTR_FRAG", "INTR_CYC"],
    "TEM": ["TEMP_LIN", "TEMP_DIS", "TEMP_DESORD"],
}
COL_MAP = {
    "NAR": "TYPE NARRATEUR", "FOC": "FOCALISATION",
    "MOD": "MODE NARRATIF",  "REG": "REGIME NARRATIF",
    "ESP": "ESPACE",          "INT": "INTRIGUE",
    "TEM": "TEMPORALITÉ",
}
OUTPUT_FIELDS = ["File"] + [
    f for k in VALID for f in (COL_MAP[k], "GOLD_"+k, k+"_correct")
]

# ── Prompt ────────────────────────────────────────────────────────────────────

PROMPT = """/no_think
Tu es expert en narratologie française. Voici {n_chunks} extraits du roman "{title}" ({author}), pris à des positions régulières du texte (début → fin).

LIS TOUS LES EXTRAITS AVANT DE RÉPONDRE. Pour les critères structuraux (ESPACE, INTRIGUE, TEMPORALITÉ), compare activement les extraits entre eux.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DÉFINITIONS (Grille Narratologique de Riccardo Barontini)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TYPE DE NARRATEUR
• NAR_AUTOD : le narrateur EST le protagoniste principal (dit "je" et vit l'histoire).
• NAR_TEM   : le narrateur dit "je/nous" mais est personnage secondaire ou témoin.
• NAR_EXT   : le narrateur est ABSENT de l'histoire, raconte à la 3ème personne.

FOCALISATION — compare les {n_chunks} extraits pour décider
• FOC_INT  : accès à l'intériorité d'UN SEUL personnage, narration restreinte.
             Le même personnage focal domine dans tous les extraits.
• FOC_EXT  : AUCUN accès aux pensées ou émotions. Description en surface uniquement.
• FOC_ZERO : narrateur omniscient (3ème personne) accédant librement aux consciences.
             ⚠ FOC_ZERO si le narrateur est à la 3ème personne et entre dans les pensées,
               même si un seul personnage domine dans ces extraits.
             ⚠ FOC_VAR ≠ FOC_ZERO : FOC_VAR uniquement si le roman est STRUCTURELLEMENT
               organisé en chapitres/parties avec des points de vue DÉSIGNÉS différents
               (ex: "Chapitre Marie", "Chapitre Paul"). Si le narrateur passe fluidement
               d'une conscience à l'autre → FOC_ZERO, pas FOC_VAR.
• FOC_VAR  : alternance STRUCTURÉE entre plusieurs POV internes. Les sections du roman
             sont explicitement attribuées à des personnages différents.

MODE NARRATIF DOMINANT
• MOD_EVT  : l'action, les faits, les décisions dominent — même s'il y a des pensées.
             ⚠ La simple présence de pensées ne suffit pas pour choisir MOD_INTR.
• MOD_DESC : les descriptions de décors, objets, sensations, ambiances dominent.
• MOD_INTR : les réflexions intérieures et états d'âme DOMINENT CLAIREMENT sur l'action.
             Choisir MOD_INTR uniquement si l'action est clairement secondaire.
• MOD_MIX  : aucun mode ne domine — équilibre stable entre plusieurs modes.

RÉGIME NARRATIF — vérifie dans cet ordre
1. Y a-t-il des éléments surnaturels, inexplicables ou symboliques perturbant le réel ?
   → Si oui : REG_FANT
2. Le monde est-il clairement futuriste, dystopique, modifié politiquement ?
   → Si oui : REG_SPEC
3. Le narrateur parle-t-il EXPLICITEMENT de sa propre vie d'auteur / posture autobiographique ?
   → Si oui : REG_AUTO (≠ simple narration à la 1ère personne)
4. Sinon → REG_REAL

ORGANISATION DE L'ESPACE — compare les lieux mentionnés dans tous les extraits
• ESP_UNIT : les extraits se déroulent dans le MÊME environnement général
             (même ville, même bâtiment, même région — même avec des sous-lieux différents).
• ESP_FRAG : les extraits montrent des LIEUX GÉOGRAPHIQUEMENT DISTINCTS
             (différentes villes, pays, régions sans cohérence spatiale forte).
• ESP_ITIN : les personnages sont EN DÉPLACEMENT CONTINU — le voyage/l'errance est central.
• ESP_IMAG : l'espace est partiellement ou totalement inventé, irréaliste ou symbolique.

NATURE DE L'INTRIGUE — regarde si les événements se causent les uns les autres
• INTR_LIN  : les événements des extraits s'enchaînent causalement (A cause B qui cause C).
              Les extraits montrent une progression narrative logique.
• INTR_FRAG : les extraits semblent JUXTAPOSÉS sans lien causal fort.
              On pourrait lire certains extraits dans un autre ordre sans perdre le sens.
• INTR_CYC  : des motifs, situations ou scènes se RÉPÈTENT de manière structurante
              entre les extraits (l'extrait final ressemble à l'extrait initial).

TEMPORALITÉ — COMPTE combien d'extraits contiennent des anachronies (flashbacks, retours en arrière, anticipations)
• TEMP_LIN    : anachronies dans 0 à 2 extraits sur {n_chunks}. Le flux dominant est chronologique.
• TEMP_DIS    : anachronies dans 3 à 6 extraits sur {n_chunks}. Allers-retours temporels fréquents mais structurés.
• TEMP_DESORD : anachronies dans 7 extraits ou plus sur {n_chunks}, OU chronologie impossible à reconstituer.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXTRAITS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{sections}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANALYSE en 2 étapes :

Étape 1 — Notes rapides (2-3 mots par critère) :
- Personne grammaticale + narrateur : ...
- Accès aux pensées de qui : ...
- Changement POV structurel (chapitres nommés) : oui/non
- Mode dominant (action/description/introspection/équilibre) : ...
- Monde réaliste/fantastique/futuriste/autobiographique : ...
- Lieux dans les extraits (même zone ou distincte) : ...
- Lien causal entre extraits : oui/non/partiel
- Nombre d'extraits avec anachronies : .../9

Étape 2 — Réponds avec ce JSON UNIQUEMENT :
{{
  "TYPE NARRATEUR":  "NAR_AUTOD|NAR_TEM|NAR_EXT",
  "FOCALISATION":    "FOC_INT|FOC_EXT|FOC_ZERO|FOC_VAR",
  "MODE NARRATIF":   "MOD_EVT|MOD_DESC|MOD_INTR|MOD_MIX",
  "REGIME NARRATIF": "REG_AUTO|REG_REAL|REG_FANT|REG_SPEC",
  "ESPACE":          "ESP_UNIT|ESP_FRAG|ESP_ITIN|ESP_IMAG",
  "INTRIGUE":        "INTR_LIN|INTR_FRAG|INTR_CYC",
  "TEMPORALITÉ":     "TEMP_LIN|TEMP_DIS|TEMP_DESORD"
}}"""

# ── Load gold ─────────────────────────────────────────────────────────────────

def load_gold(path):
    gold = {}
    with open(path, encoding="utf-8") as f:
        rows = list(csv.reader(f, delimiter=";"))
    for row in rows[1:]:
        if not row or not row[0].strip().endswith(".txt"):
            continue
        def c(i): return row[i].strip() if i < len(row) else ""
        fn  = c(0)
        nar = c(4); nar = "NAR_AUTOD" if nar == "NAR_AUTO" else nar
        foc = c(6); foc = "FOC_INT"   if foc == "FIC_INT"  else foc
        gold[fn] = {
            "NAR": nar,   "NAR_alt": c(5),
            "FOC": foc,   "FOC_alt": c(7),
            "MOD": c(8),  "MOD_alt": c(9),
            "REG": c(10), "REG_alt": c(11),
            "ESP": c(12), "ESP_alt": c(13),
            "INT": c(14), "INT_alt": c(15),
            "TEM": c(16), "TEM_alt": c(17),
            "author": c(2), "title": c(3),
        }
    return gold

# ── Extract N_CHUNKS sections ─────────────────────────────────────────────────

def extract_sections(filename):
    path = os.path.join(CORPUS_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    n   = len(lines)
    L   = LINES_PER_CHUNK
    # evenly spaced positions from 0% to 100%
    positions = [i / (N_CHUNKS - 1) for i in range(N_CHUNKS)]
    labels = [
        "DÉBUT (0%)", "DÉBUT (5%)", "DÉBUT-MILIEU (15%)", "QUART (28%)",
        "MILIEU-DÉBUT (42%)", "MILIEU (56%)", "MILIEU-FIN (70%)",
        "TROIS-QUARTS (83%)", "FIN (100%)",
    ]
    parts = []
    for pct, label in zip(positions, labels):
        start = min(int(n * pct), max(0, n - L))
        chunk = lines[start:start + L]
        text  = "".join(chunk).strip()
        if text:
            parts.append(f"=== {label} ===\n{text}")
    return "\n\n".join(parts)

# ── API call ──────────────────────────────────────────────────────────────────

def classify(sections_text, title, author):
    prompt = PROMPT.format(
        sections=sections_text, title=title, author=author, n_chunks=N_CHUNKS
    )
    # On retry, trim text if context is very long
    for attempt in range(3):
        p = prompt
        if attempt >= 1 and len(p) > 28000:
            trimmed = sections_text[:14000]
            p = PROMPT.format(sections=trimmed, title=title, author=author, n_chunks=N_CHUNKS)
        try:
            resp = requests.post(OLLAMA_URL, json={
                "model": MODEL,
                "messages": [{"role": "user", "content": p}],
                "stream": False,
                "options": {
                    "temperature": 0,
                    "num_predict": 3000,
                    "num_ctx": 24576,
                },
            }, timeout=360)
            raw = resp.json()["message"].get("content", "").strip()
            raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
            m = re.search(r"\{[^{}]*\}", raw, re.DOTALL)
            if not m:
                print(f"\n  [attempt {attempt}] no JSON. raw={repr(raw[:100])}", flush=True)
                continue
            obj  = json.loads(m.group(0))
            result = {}
            bad    = []
            for key, valid in VALID.items():
                val = obj.get(COL_MAP[key], "").strip().upper()
                if val in valid:
                    result[key] = val
                else:
                    bad.append(f"{key}={repr(val)}")
                    result[key] = None
            if not bad:
                return result
            print(f"\n  [attempt {attempt}] bad fields: {bad}", flush=True)
        except Exception as exc:
            print(f"\n  [attempt {attempt}] exception: {exc}", flush=True)
            if attempt < 2:
                time.sleep(3)
    return None

# ── Scoring ───────────────────────────────────────────────────────────────────

def is_ok(pred, main, alt):
    return bool(pred and (pred == main or (alt and pred == alt)))

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    gold = load_gold(GOLD_FILE)
    print(f"Gold: {len(gold)} novels | {N_CHUNKS} chunks × {LINES_PER_CHUNK} lines = {N_CHUNKS*LINES_PER_CHUNK} total lines/novel")

    done = {}
    if os.path.exists(OUTPUT):
        with open(OUTPUT, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                done[row["File"]] = row
        print(f"Resuming: {len(done)} already done")

    remaining = [fn for fn in gold if fn not in done]
    print(f"To classify: {len(remaining)} | Model: {MODEL}\n{'='*70}")

    scores = {k: {"c": 0, "t": 0} for k in VALID}
    for fn, row in done.items():
        if fn not in gold: continue
        for k in VALID:
            v = row.get(k + "_correct")
            if v in ("0", "1"):
                scores[k]["t"] += 1
                if v == "1": scores[k]["c"] += 1

    file_new = not os.path.exists(OUTPUT) or os.path.getsize(OUTPUT) == 0
    out_f  = open(OUTPUT,   "a", encoding="utf-8", newline="")
    log_f  = open(LOG_FILE, "a", encoding="utf-8")
    writer = csv.DictWriter(out_f, fieldnames=OUTPUT_FIELDS)
    if file_new:
        writer.writeheader()

    for i, fn in enumerate(remaining, 1):
        g = gold[fn]
        print(f"[{i:>2}/{len(remaining)}] {fn[:52]}", end="", flush=True)

        sections = extract_sections(fn)
        if sections is None:
            print(" ⚠ not found")
            continue

        t0     = time.time()
        result = classify(sections, g["title"], g["author"])
        elapsed = time.time() - t0

        if result is None:
            print(f" ✗ failed ({elapsed:.0f}s)")
            log_f.write(f"FAILED: {fn}\n"); log_f.flush()
            continue

        row_out = {"File": fn}
        ok_flags = {}
        for k in VALID:
            pred = result[k]
            ok   = is_ok(pred, g[k], g[k + "_alt"])
            ok_flags[k] = ok
            scores[k]["t"] += 1
            if ok: scores[k]["c"] += 1
            row_out[COL_MAP[k]]    = pred
            row_out["GOLD_" + k]   = g[k]
            row_out[k + "_correct"] = "1" if ok else "0"

        sym  = lambda ok: "✓" if ok else "✗"
        line1 = " ".join(f"{k}={result[k]}{sym(ok_flags[k])}" for k in VALID)
        line2 = " ".join(
            f"{k}={scores[k]['c']/scores[k]['t']*100:.0f}%"
            for k in VALID if scores[k]["t"]
        )
        print(f" {elapsed:.0f}s\n       {line1}\n       running: {line2}")

        log_f.write(f"{fn}: {line1}\n"); log_f.flush()
        writer.writerow(row_out); out_f.flush()

    out_f.close(); log_f.close()

    print(f"\n{'='*70}")
    print(f"MODEL: {MODEL}  |  {N_CHUNKS} chunks × {LINES_PER_CHUNK} lines")
    print(f"{'='*70}")
    labels = ["TYPE NARRATEUR","FOCALISATION","MODE NARRATIF","REGIME NARRATIF",
              "ESPACE","INTRIGUE","TEMPORALITÉ"]
    total_c = total_t = 0
    for k, label in zip(VALID, labels):
        c = scores[k]["c"]; t = scores[k]["t"]
        pct = c / t * 100 if t else 0
        bar = "█" * int(pct / 5)
        print(f"  {label:<20} {c:>2}/{t:<2}  ({pct:>5.1f}%)  {bar}")
        total_c += c; total_t += t
    print(f"\n  OVERALL  {total_c}/{total_t}  ({total_c/total_t*100:.1f}%)")
    print(f"\n  Output: {OUTPUT}")

if __name__ == "__main__":
    main()
