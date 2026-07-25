"""
run_task0_v4_all7.py  —  Comprehensive Task 0, all 7 criteria

Fixes vs all previous scripts:
  1. ALL 7 criteria in one prompt using Riccardo's exact definitions
     from Grille_Narratologique.csv
  2. 40 lines per section (was 30) × 6 sections = 240 lines total
  3. ALL sections shown together — model compares ACROSS the novel,
     not one section at a time (this is the fix for ESP, INT, TEM)
  4. Anti-bias guidance for the 4 broken categories:
       - MOD: over-predicts MOD_MIX  → requires truly balanced mix
       - ESP: over-predicts ESP_FRAG → ESP_UNIT if same general area
       - INT: over-predicts INTR_FRAG → INTR_LIN if causally connected
       - TEM: over-predicts TEMP_DIS → TEMP_LIN if mostly chronological
  5. FOC fix from v3: tracks whether focal character changes across sections
  6. num_ctx = 16384 to handle larger sections

Model: qwen3:30b on localhost:11435
"""

import csv, json, os, re, requests, time
from collections import Counter

OLLAMA_URL = "http://localhost:11435/api/chat"
MODEL      = "qwen3:30b"
GOLD_FILE  = "GOLD_narratologie.csv"
CORPUS_DIR = os.path.expanduser("~/ecopoetique/CORPUS_TOTAL")
OUTPUT     = "resultats_task0_v4_all7.csv"
LOG_FILE   = "task0_v4_all7.log"
LINES_PER_SECTION = 40  # was 30

VALID = {
    "NAR": ["NAR_AUTOD", "NAR_TEM", "NAR_EXT"],
    "FOC": ["FOC_INT", "FOC_EXT", "FOC_ZERO", "FOC_VAR"],
    "MOD": ["MOD_EVT", "MOD_DESC", "MOD_INTR", "MOD_MIX"],
    "REG": ["REG_AUTO", "REG_REAL", "REG_FANT", "REG_SPEC"],
    "ESP": ["ESP_UNIT", "ESP_FRAG", "ESP_ITIN", "ESP_IMAG"],
    "INT": ["INTR_LIN", "INTR_FRAG", "INTR_CYC"],
    "TEM": ["TEMP_LIN", "TEMP_DIS", "TEMP_DESORD"],
}

OUTPUT_FIELDS = [
    "File",
    "TYPE NARRATEUR", "GOLD_NAR", "NAR_correct",
    "FOCALISATION",   "GOLD_FOC", "FOC_correct",
    "MODE NARRATIF",  "GOLD_MOD", "MOD_correct",
    "REGIME NARRATIF","GOLD_REG", "REG_correct",
    "ESPACE",         "GOLD_ESP", "ESP_correct",
    "INTRIGUE",       "GOLD_INT", "INT_correct",
    "TEMPORALITÉ",    "GOLD_TEM", "TEM_correct",
]

# ── Prompt ────────────────────────────────────────────────────────────────────

PROMPT = """/no_think
Tu es expert en narratologie française. Voici 6 extraits du roman "{title}" ({author}), pris à des positions différentes du texte.

LIS TOUS LES EXTRAITS AVANT DE RÉPONDRE. Compare-les entre eux pour les critères structuraux.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DÉFINITIONS EXACTES (Grille Narratologique de Riccardo Barontini)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TYPE DE NARRATEUR — qui raconte ?
• NAR_AUTOD : le narrateur EST le protagoniste principal (dit "je" et vit l'histoire).
• NAR_TEM   : le narrateur dit "je/nous" mais est personnage secondaire ou témoin.
• NAR_EXT   : le narrateur est ABSENT de l'histoire, raconte à la 3ème personne.

FOCALISATION — accès à l'intériorité (compare les 6 extraits ensemble) :
• FOC_INT  : accès à l'intériorité d'UN SEUL personnage, perspective subjective.
             Le MÊME personnage focal dans TOUS les extraits.
• FOC_EXT  : AUCUN accès aux pensées. Narration descriptive en surface.
• FOC_ZERO : narrateur omniscient (3ème personne) ayant accès à l'ensemble des consciences.
             ⚠ FOC_ZERO si le narrateur est à la 3ème personne avec accès aux pensées,
               même si un seul personnage domine dans ces extraits.
             FOC_INT vs FOC_ZERO : FOC_INT = narration RESTREINTE à un seul personnage ;
             FOC_ZERO = narrateur omniscient, sélectif mais non restreint.
• FOC_VAR  : alternance entre plusieurs points de vue internes selon les séquences.
             Le personnage focal CHANGE d'un extrait à l'autre de façon structurée.

MODE NARRATIF DOMINANT — quel est le contenu prédominant ?
• MOD_EVT  : priorité à l'action, aux faits et aux décisions.
• MOD_DESC : mise en valeur des décors, sensations, objets, ambiances.
• MOD_INTR : mise en avant de la subjectivité, des réflexions intérieures.
• MOD_MIX  : combinaison FLUIDE ET STABLE de plusieurs modes SANS PRÉDOMINANCE CLAIRE.
             ⚠ MOD_MIX uniquement si aucun mode ne dépasse ~50%. Si l'action domine
               même légèrement → MOD_EVT. Si l'introspection domine → MOD_INTR.

RÉGIME NARRATIF — quel type de monde est représenté ?
• REG_AUTO : récit fondé sur l'expérience ou la voix de l'auteur, posture autobiographique.
             ⚠ REG_AUTO ≠ narration à la 1ère personne. Il faut une posture EXPLICITEMENT
               autobiographique ou autofictionnelle (auteur = narrateur).
• REG_REAL : représentation cohérente d'un monde familier, fiction mimétique.
• REG_FANT : perturbation du réel par l'étrange, l'inexplicable, le symbolique.
• REG_SPEC : projection spéculative — monde modifié, futuriste, dystopique, uchronique.

ORGANISATION DE L'ESPACE — structure spatiale dominante (compare les 6 extraits) :
• ESP_UNIT : récit centré sur UN lieu unique ou fortement restreint (maison, île, village).
             ⚠ ESP_UNIT même si plusieurs pièces ou sous-lieux, si c'est la même zone.
             ⚠ Ne pas confondre avec ESP_FRAG : ESP_UNIT = cohérence spatiale globale.
• ESP_FRAG : succession de lieux MULTIPLES et VARIÉS, sans unité géographique forte.
             Nécessite des déplacements entre villes/pays/régions distinctes.
• ESP_ITIN : déplacement CONTINU ou PROGRESSIF à travers l'espace (voyage, errance).
• ESP_IMAG : espace partiellement ou totalement inventé, irréaliste ou symbolique.

NATURE DE L'INTRIGUE — structure des événements (compare les 6 extraits) :
• INTR_LIN  : les événements s'enchaînent dans un ordre progressif et causal.
              ⚠ INTR_LIN même s'il y a quelques digressions ou retours en arrière,
                si la progression causale GLOBALE est maintenue.
• INTR_FRAG : narration par blocs indépendants, ruptures fréquentes, pas de progression causale claire.
              Nécessite une fragmentation STRUCTURELLE, pas juste quelques ellipses.
• INTR_CYC  : répétition structurante de motifs ou situations créant un effet de boucle.

TEMPORALITÉ — degré de discordance temporelle (compare les 6 extraits) :
• TEMP_LIN     : déroulement quasi linéaire. Transitions temporelles explicites et peu fréquentes.
                 ⚠ TEMP_LIN même s'il y a QUELQUES analepses ou flashbacks ponctuels.
                 Le flux narratif DOMINANT reste chronologique.
• TEMP_DIS     : alternance modérée entre temps présents et passés. Analepses récurrentes
                 mais pas chaotiques. Ellipses et retours structurés.
• TEMP_DESORD  : temporalité ÉCLATÉE ou complexe. Nombreuses analepses, récits enchâssés,
                 confusion temporelle fréquente. L'ordre chronologique est impossible à suivre.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXTRAITS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{sections}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANALYSE — réponds avec ce JSON UNIQUEMENT :
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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
        fn = c(0)
        nar = c(4); nar = "NAR_AUTOD" if nar == "NAR_AUTO" else nar
        foc = c(6); foc = "FOC_INT"  if foc == "FIC_INT"  else foc
        gold[fn] = {
            "NAR": nar, "NAR_alt": c(5),
            "FOC": foc, "FOC_alt": c(7),
            "MOD": c(8),  "MOD_alt": c(9),
            "REG": c(10), "REG_alt": c(11),
            "ESP": c(12), "ESP_alt": c(13),
            "INT": c(14), "INT_alt": c(15),
            "TEM": c(16), "TEM_alt": c(17),
            "author": c(2), "title": c(3),
        }
    return gold

# ── Extract 6 sections of LINES_PER_SECTION lines ────────────────────────────

def extract_sections(filename):
    path = os.path.join(CORPUS_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    n = len(lines)
    L = LINES_PER_SECTION
    positions = [
        ("DÉBUT (0%)",           lines[:L]),
        ("DÉBUT (5%)",           lines[L:L*2]),
        ("PREMIER QUART (25%)",  lines[int(n*0.25):int(n*0.25)+L]),
        ("MILIEU (50%)",         lines[int(n*0.50):int(n*0.50)+L]),
        ("TROIS QUARTS (75%)",   lines[int(n*0.75):int(n*0.75)+L]),
        ("FIN (100%)",           lines[-L:]),
    ]
    parts = []
    for label, chunk in positions:
        text = "".join(chunk).strip()
        if text:
            parts.append(f"=== {label} ===\n{text}")
    return "\n\n".join(parts)

# ── API call ──────────────────────────────────────────────────────────────────

def classify(sections_text, title, author):
    # On empty-content retries, use a smaller context (fewer sections passed in)
    prompt = PROMPT.format(sections=sections_text, title=title, author=author)
    for attempt in range(3):
        # If context too long, trim to first 12000 chars of sections text
        if attempt >= 1 and len(prompt) > 24000:
            short = sections_text[:12000]
            prompt = PROMPT.format(sections=short, title=title, author=author)
        try:
            resp = requests.post(OLLAMA_URL, json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {
                    "temperature": 0,
                    "num_predict": 3000,
                    "num_ctx": 16384,
                },
            }, timeout=300)
            raw = resp.json()["message"].get("content", "").strip()
            raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
            m = re.search(r"\{.*?\}", raw, re.DOTALL)
            if not m:
                print(f"\n  [debug attempt {attempt}] no JSON found. raw={repr(raw[:120])}", flush=True)
                continue
            obj = json.loads(m.group(0))
            col_map = {
                "NAR": "TYPE NARRATEUR", "FOC": "FOCALISATION",
                "MOD": "MODE NARRATIF",  "REG": "REGIME NARRATIF",
                "ESP": "ESPACE",          "INT": "INTRIGUE",
                "TEM": "TEMPORALITÉ",
            }
            result = {}
            bad = []
            for key, valid in VALID.items():
                val = obj.get(col_map[key], "").strip().upper()
                if val in valid:
                    result[key] = val
                else:
                    bad.append(f"{key}={repr(val)}")
                    result[key] = None
            if not bad:
                return result
            print(f"\n  [debug attempt {attempt}] invalid fields: {bad}", flush=True)
        except Exception as exc:
            print(f"\n  [debug attempt {attempt}] exception: {exc}", flush=True)
            if attempt < 2:
                time.sleep(3)
    return None

# ── Scoring ───────────────────────────────────────────────────────────────────

def is_correct(pred, main, alt):
    return pred and (pred == main or (alt and pred == alt))

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    gold = load_gold(GOLD_FILE)
    print(f"Gold set: {len(gold)} novels")
    print(f"Lines per section: {LINES_PER_SECTION} × 6 = {LINES_PER_SECTION*6} total")

    # Resume
    done = {}
    if os.path.exists(OUTPUT):
        with open(OUTPUT, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                done[row["File"]] = row
        print(f"Resuming: {len(done)} already done")

    remaining = [fn for fn in gold if fn not in done]
    print(f"To classify: {len(remaining)} | Model: {MODEL}\n{'='*70}")

    # Running scores
    scores = {k: {"c": 0, "t": 0} for k in VALID}
    for fn, row in done.items():
        if fn not in gold: continue
        for k in VALID:
            col_map = {
                "NAR":"NAR_correct","FOC":"FOC_correct","MOD":"MOD_correct",
                "REG":"REG_correct","ESP":"ESP_correct","INT":"INT_correct","TEM":"TEM_correct"
            }
            if row.get(col_map[k]) in ("0","1"):
                scores[k]["t"] += 1
                if row[col_map[k]] == "1": scores[k]["c"] += 1

    file_exists = os.path.exists(OUTPUT)
    out_f  = open(OUTPUT,   "a", encoding="utf-8", newline="")
    log_f  = open(LOG_FILE, "a", encoding="utf-8")
    writer = csv.DictWriter(out_f, fieldnames=OUTPUT_FIELDS)
    if not file_exists or os.path.getsize(OUTPUT) == 0:
        writer.writeheader()

    keys_display = ["NAR","FOC","MOD","REG","ESP","INT","TEM"]

    for i, fn in enumerate(remaining, 1):
        g = gold[fn]
        print(f"[{i:>2}/{len(remaining)}] {fn[:50]}", end="", flush=True)

        sections = extract_sections(fn)
        if sections is None:
            print(" ⚠ not found")
            continue

        t0 = time.time()
        result = classify(sections, g["title"], g["author"])
        elapsed = time.time() - t0

        if result is None:
            print(f" ✗ failed ({elapsed:.0f}s)")
            log_f.write(f"FAILED: {fn}\n")
            continue

        col_map = {
            "NAR": "TYPE NARRATEUR", "FOC": "FOCALISATION",
            "MOD": "MODE NARRATIF",  "REG": "REGIME NARRATIF",
            "ESP": "ESPACE",          "INT": "INTRIGUE",
            "TEM": "TEMPORALITÉ",
        }
        row_out = {"File": fn}
        ok_flags = {}
        for k in VALID:
            pred = result[k]
            main = g[k]; alt = g[k+"_alt"]
            ok = is_correct(pred, main, alt)
            ok_flags[k] = ok
            scores[k]["t"] += 1
            if ok: scores[k]["c"] += 1
            row_out[col_map[k]]          = pred
            row_out["GOLD_"+k if k not in ("MOD","REG","ESP","INT","TEM") else
                    {"MOD":"GOLD_MOD","REG":"GOLD_REG","ESP":"GOLD_ESP",
                     "INT":"GOLD_INT","TEM":"GOLD_TEM"}[k]] = main
            row_out[k+"_correct"] = "1" if ok else "0"

        # Fix row_out gold column names
        row_out["GOLD_NAR"] = g["NAR"]; row_out["GOLD_FOC"] = g["FOC"]
        row_out["GOLD_MOD"] = g["MOD"]; row_out["GOLD_REG"] = g["REG"]
        row_out["GOLD_ESP"] = g["ESP"]; row_out["GOLD_INT"] = g["INT"]
        row_out["GOLD_TEM"] = g["TEM"]

        sym = lambda ok: "✓" if ok else "✗"
        short = " ".join(
            f"{k}={result[k]}{sym(ok_flags[k])}"
            for k in keys_display
        )
        accs = " ".join(
            f"{k}={scores[k]['c']/scores[k]['t']*100:.0f}%"
            for k in keys_display if scores[k]['t']
        )
        print(f" {elapsed:.0f}s")
        print(f"       {short}")
        print(f"       running: {accs}")

        log_f.write(f"{fn}: {short}\n")
        log_f.flush()
        writer.writerow(row_out)
        out_f.flush()

    out_f.close(); log_f.close()

    print(f"\n{'='*70}")
    print(f"MODEL: {MODEL}  |  {LINES_PER_SECTION} lines/section × 6 sections")
    print(f"{'='*70}")
    labels = ["TYPE NARRATEUR","FOCALISATION","MODE NARRATIF","REGIME NARRATIF",
              "ESPACE","INTRIGUE","TEMPORALITÉ"]
    for k, label in zip(VALID, labels):
        c = scores[k]["c"]; t = scores[k]["t"]
        pct = c/t*100 if t else 0
        bar = "█" * int(pct/5)
        print(f"  {label:<20} {c:>2}/{t:<2}  ({pct:>5.1f}%)  {bar}")
    print(f"\n  Output: {OUTPUT}")
    print(f"  Log:    {LOG_FILE}")

if __name__ == "__main__":
    main()
