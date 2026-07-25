"""
Test Gemma3:27b and Mistral-Small3.1 on weak narratological criteria only.
Focus: FOCALISATION, MODE NARRATIF, ESPACE, INTRIGUE
Strategy: map-reduce with embedded Genette definitions, no CoT, JSON output
"""

import os, csv, json, re, time, requests
from pathlib import Path
from collections import Counter

OLLAMA_URL  = "http://localhost:11435/api/chat"
GOLD_FILE   = os.path.expanduser("~/ecopoetique/narratologie/GOLD_narratologie_clean.csv")
CORPUS_DIR  = os.path.expanduser("~/ecopoetique/CORPUS_TOTAL")
LOG_FILE    = os.path.expanduser("~/ecopoetique/narratologie/weak_criteria_test.log")

MODELS = ["gemma3:27b", "mistral-small3.1"]

# Only the 4 weak criteria
WEAK_CRITERIA = {
    "FOCALISATION":    ["FOC_INT", "FOC_EXT", "FOC_ZERO", "FOC_VAR"],
    "MODE NARRATIF":   ["MOD_EVT", "MOD_DESC", "MOD_INTR", "MOD_MIX", "MOD_DIA"],
    "ESPACE":          ["ESP_UNIT", "ESP_FRAG", "ESP_ITIN", "ESP_IMAG"],
    "INTRIGUE":        ["INTR_LIN", "INTR_FRAG", "INTR_CYC"],
}

# Genette definitions embedded verbatim (from Hicke et al. approach)
DEFINITIONS = {
    "FOCALISATION": """FOCALISATION (point de vue narratif selon Genette):
- FOC_INT (interne): Le récit est limité à ce que perçoit, pense et ressent UN personnage. Accès à la vie intérieure. Utilisation de discours indirect libre, stream of consciousness, introspection.
- FOC_EXT (externe): Le narrateur rapporte uniquement les actions et paroles observables de l'extérieur, SANS accès aux pensées des personnages. Style caméra/behavioriste.
- FOC_ZERO (zéro/omnisciente): Le narrateur en sait PLUS que n'importe quel personnage. Accès illimité aux pensées de tous. Narrateur omniscient classique.
- FOC_VAR (variable): La focalisation CHANGE de personnage au cours du roman (interne à plusieurs personnages alternativement).""",

    "MODE NARRATIF": """MODE NARRATIF (contenu dominant du récit):
- MOD_EVT (événementiel): Dominé par les actions, événements, péripéties, faits qui font avancer l'intrigue.
- MOD_DESC (descriptif): Dominé par les descriptions de lieux, personnages, atmosphères, sans avancement de l'action.
- MOD_INTR (introspectif): Dominé par les réflexions intérieures, monologues, pensées, émotions des personnages.
- MOD_DIA (dialogues): Dominé par les échanges directs entre personnages (dialogues, conversations).
- MOD_MIX (mixte): Mélange équilibré de plusieurs modes sans dominante claire.""",

    "ESPACE": """ESPACE (organisation spatiale du roman):
- ESP_UNIT (unitaire): L'action se déroule principalement dans UN seul lieu ou espace géographique délimité.
- ESP_FRAG (fragmenté): L'action se déroule dans PLUSIEURS lieux distincts et discontinus, sans logique de déplacement.
- ESP_ITIN (itinérant): Le roman est structuré autour de DÉPLACEMENTS continus, voyages, itinéraires géographiques.
- ESP_IMAG (imaginaire): L'espace est fictif, fantastique, onirique ou utopique/dystopique.""",

    "INTRIGUE": """INTRIGUE (structure de la trame narrative):
- INTR_LIN (linéaire): L'intrigue suit une progression chronologique et causale continue vers une résolution.
- INTR_FRAG (fragmentée): L'intrigue est discontinue, morcelée, sans fil narratif unique ou résolution claire.
- INTR_CYC (cyclique): L'intrigue revient à son point de départ, présente des répétitions ou une structure circulaire.""",
}

CHUNK_SIZE = 100  # lines per chunk
N_CHUNKS   = 6    # sample chunks from across novel

import sys
class Tee:
    def __init__(self, fp):
        self.c = sys.stdout
        self.f = open(fp, "w", encoding="utf-8")
    def write(self, t): self.c.write(t); self.f.write(t); self.f.flush()
    def flush(self): self.c.flush(); self.f.flush()
sys.stdout = Tee(LOG_FILE)

def load_gold():
    gold = {}
    with open(GOLD_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            fn = row["File"].strip()
            gold[fn] = {c: row.get(c, "").strip() for c in WEAK_CRITERIA}
    return gold

def load_chunks(fn):
    path = os.path.join(CORPUS_DIR, fn)
    if not os.path.exists(path): return None
    lines = open(path, encoding="utf-8").readlines()
    total = len(lines)
    if total < 200: return None
    chunks = []
    for i in range(N_CHUNKS):
        pos = int(total * i / N_CHUNKS)
        chunk = "".join(lines[pos:pos+CHUNK_SIZE])
        chunks.append(chunk)
    return chunks

def call_ollama(model, prompt, timeout=180):
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0, "num_predict": 100},
        }, timeout=timeout)
        resp.raise_for_status()
        content = resp.json()["message"]["content"]
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        return content
    except Exception as e:
        return f"ERR:{str(e)[:50]}"

def classify_chunk(model, criterion, chunk, valid_codes):
    defn = DEFINITIONS[criterion]
    codes_str = " | ".join(valid_codes)
    prompt = f"""{defn}

Analyse cet extrait de roman français et détermine le code pour: {criterion}
Codes valides: {codes_str}

EXTRAIT:
{chunk[:1500]}

Réponds UNIQUEMENT avec le code JSON: {{"{criterion}": "CODE"}}
Ne fournis aucune explication."""

    result = call_ollama(model, prompt)
    m = re.search(r'"([A-Z_]+)"', result)
    if m and m.group(1) in valid_codes:
        return m.group(1)
    # Try to find any valid code in response
    for code in valid_codes:
        if code in result:
            return code
    return None

def reduce_votes(model, criterion, valid_codes, chunk_votes, novel_title):
    defn = DEFINITIONS[criterion]
    codes_str = " | ".join(valid_codes)
    vote_summary = ", ".join([f"chunk {i+1}={v}" for i,v in enumerate(chunk_votes) if v])
    prompt = f"""{defn}

Pour le roman "{novel_title}", voici les votes par section:
{vote_summary}

En tenant compte de l'ensemble du roman (pas juste une section), quel est le code final pour {criterion}?
Codes valides: {codes_str}

Réponds UNIQUEMENT avec le code JSON: {{"{criterion}": "CODE"}}"""

    result = call_ollama(model, prompt)
    m = re.search(r'"([A-Z_]+)"', result)
    if m and m.group(1) in valid_codes:
        return m.group(1)
    # Majority vote fallback
    valid_votes = [v for v in chunk_votes if v]
    if valid_votes:
        return Counter(valid_votes).most_common(1)[0][0]
    return None

def evaluate_model(model, gold):
    print(f"\n{'='*60}")
    print(f"  MODEL: {model}")
    print(f"{'='*60}")

    scores = {c: {"correct": 0, "total": 0} for c in WEAK_CRITERIA}
    results = []
    corpus_files = set(os.listdir(CORPUS_DIR))
    novels = [(fn, labels) for fn, labels in gold.items() if fn in corpus_files]

    for i, (fn, gold_labels) in enumerate(novels, 1):
        print(f"\n[{i:>2}/{len(novels)}] {fn[:55]}")
        chunks = load_chunks(fn)
        if not chunks:
            print("  ⚠️  Skipped")
            continue

        preds = {}
        for criterion, valid_codes in WEAK_CRITERIA.items():
            # Map phase: classify each chunk
            chunk_votes = []
            for j, chunk in enumerate(chunks):
                vote = classify_chunk(model, criterion, chunk, valid_codes)
                chunk_votes.append(vote)

            # Reduce phase: final decision
            pred = reduce_votes(model, criterion, valid_codes, chunk_votes, fn.replace(".txt",""))
            preds[criterion] = pred

            gold_val = gold_labels.get(criterion, "")
            is_correct = pred and pred == gold_val
            mark = "✓" if is_correct else "✗"
            print(f"  {criterion:<20} → {pred or '?':<12} {mark}  (gold:{gold_val})")

            if gold_val:
                scores[criterion]["total"] += 1
                if is_correct:
                    scores[criterion]["correct"] += 1

        results.append({"fn": fn, **{f"pred_{c}": preds.get(c,"") for c in WEAK_CRITERIA},
                        **{f"gold_{c}": gold_labels.get(c,"") for c in WEAK_CRITERIA}})

    # Summary
    print(f"\n{'='*60}")
    print(f"  RESULTS — {model}")
    print(f"{'='*60}")
    oc = ot = 0
    summary = {}
    for c in WEAK_CRITERIA:
        s = scores[c]
        if s["total"]:
            acc = s["correct"]/s["total"]*100
            bar = "█" * int(acc/5)
            print(f"  {c:<20} {s['correct']:>2}/{s['total']:>2} ({acc:>5.1f}%) {bar}")
            oc += s["correct"]; ot += s["total"]
            summary[c] = acc
        else:
            summary[c] = 0.0

    print(f"  {'─'*55}")
    if ot: print(f"  WEAK CRITERIA AVG: {oc/ot*100:.1f}%")

    # Compare to current best
    current_best = {"FOCALISATION": 63.3, "MODE NARRATIF": 71.7, "ESPACE": 50.0, "INTRIGUE": 65.0}
    print(f"\n  Comparison vs Hybrid v2:")
    for c in WEAK_CRITERIA:
        diff = summary[c] - current_best[c]
        arrow = "↑" if diff > 0 else "↓"
        print(f"  {c:<20} {summary[c]:.1f}%  ({arrow}{abs(diff):.1f}pp vs {current_best[c]:.1f}%)")

    return summary, results

def main():
    print("="*60)
    print("WEAK CRITERIA TEST — Gemma3:27b vs Mistral-Small3.1")
    print("Criteria: FOCALISATION, MODE NARRATIF, ESPACE, INTRIGUE")
    print("="*60)

    gold = load_gold()
    print(f"Gold set: {len(gold)} novels")

    all_results = {}
    for model in MODELS:
        summary, results = evaluate_model(model, gold)
        all_results[model] = summary

        # Save per-model results
        out_file = os.path.expanduser(
            f"~/ecopoetique/narratologie/resultats_{model.replace(':','_').replace('.','_')}_weak.csv")
        with open(out_file, "w", newline="", encoding="utf-8") as f:
            fields = ["fn"] + [f"pred_{c}" for c in WEAK_CRITERIA] + [f"gold_{c}" for c in WEAK_CRITERIA]
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader(); w.writerows(results)
        print(f"  ✅ Saved to {out_file}")

    # Final comparison
    print(f"\n{'='*60}")
    print("FINAL COMPARISON")
    print(f"{'='*60}")
    print(f"  {'Criterion':<20} {'Hybrid v2':>10} {'Gemma3:27b':>12} {'Mistral-S':>10}")
    print(f"  {'─'*54}")
    current = {"FOCALISATION": 63.3, "MODE NARRATIF": 71.7, "ESPACE": 50.0, "INTRIGUE": 65.0}
    for c in WEAK_CRITERIA:
        g = all_results.get("gemma3:27b", {}).get(c, 0)
        m = all_results.get("mistral-small3.1", {}).get(c, 0)
        best = max(g, m, current[c])
        print(f"  {c:<20} {current[c]:>9.1f}% {g:>11.1f}% {m:>9.1f}%  {'← NEW BEST' if best > current[c] else ''}")

if __name__ == "__main__":
    main()
