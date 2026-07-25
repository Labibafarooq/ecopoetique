"""
Per-Criterion Multi-Model Ensemble for Narratological Classification
Strategy:
  - TYPE NARRATEUR: qwen3:30b (already 91.7%)
  - FOCALISATION:   qwen2.5:72b (needs deep psychological insight)
  - MODE NARRATIF:  qwen2.5:32b majority vote x3
  - REGIME NARRATIF:qwen2.5:32b majority vote x3
  - ESPACE:         qwen2.5:72b (spatial reasoning)
  - INTRIGUE:       qwen2.5:14b majority vote x3
  - TEMPORALITÉ:    qwen2.5:14b majority vote x3

Then combine best per criterion into final hybrid.
"""

import os, csv, json, re, time
from collections import Counter
import requests

OLLAMA_URL  = "http://localhost:11434/api/chat"
GOLD_FILE   = os.path.expanduser("~/ecopoetique/narratologie/GOLD_narratologie_clean.csv")
CORPUS_DIR  = os.path.expanduser("~/ecopoetique/CORPUS_TOTAL")
OUTPUT_FILE = os.path.expanduser("~/ecopoetique/narratologie/resultats_ensemble.csv")
LOG_FILE    = os.path.expanduser("~/ecopoetique/narratologie/ensemble.log")
SAMPLE_LINES = 120
VOTE_RUNS    = 3   # majority vote runs per criterion

# ── Per-criterion model assignment ─────────────────────────────────────────────
CRITERION_MODEL = {
    "TYPE NARRATEUR":  ("qwen2.5:32b",  3),   # already best, 1 run enough
    "FOCALISATION":    ("qwen2.5:72b",  3),   # biggest model, 3 votes
    "MODE NARRATIF":   ("qwen2.5:32b",  3),   # 3 votes
    "REGIME NARRATIF": ("qwen2.5:32b",  3),   # 3 votes
    "ESPACE":          ("qwen2.5:72b",  3),   # biggest model, 3 votes
    "INTRIGUE":        ("qwen2.5:14b",  3),   # 3 votes
    "TEMPORALITÉ":     ("qwen2.5:14b",  3),   # 3 votes
}

VALID_CODES = {
    "TYPE NARRATEUR":  ["NAR_AUTOD", "NAR_TEM", "NAR_EXT", "NAR_VAR"],
    "FOCALISATION":    ["FOC_INT", "FOC_EXT", "FOC_ZERO", "FOC_VAR"],
    "MODE NARRATIF":   ["MOD_EVT", "MOD_DESC", "MOD_INTR", "MOD_MIX", "MOD_DIA"],
    "REGIME NARRATIF": ["REG_AUTO", "REG_REAL", "REG_FANT", "REG_SPEC"],
    "ESPACE":          ["ESP_UNIT", "ESP_FRAG", "ESP_ITIN", "ESP_IMAG"],
    "INTRIGUE":        ["INTR_LIN", "INTR_FRAG", "INTR_CYC"],
    "TEMPORALITÉ":     ["TEMP_LIN", "TEMP_DIS", "TEMP_DESORD"],
}
CRITERIA = list(VALID_CODES.keys())

# ── Logging ────────────────────────────────────────────────────────────────────
import sys
class Tee:
    def __init__(self, fp):
        self.console = sys.stdout
        self.file = open(fp, "w", encoding="utf-8")
    def write(self, t):
        self.console.write(t); self.file.write(t); self.file.flush()
    def flush(self):
        self.console.flush(); self.file.flush()
sys.stdout = Tee(LOG_FILE)

# ── Data loading ───────────────────────────────────────────────────────────────
def load_gold():
    gold = {}
    with open(GOLD_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            fn = row["File"].strip()
            gold[fn] = {
                c: row.get(c, "").strip() for c in CRITERIA
            }
            # Also store alt codes
            gold[fn]["_alt"] = {
                "TYPE NARRATEUR":  row.get("Acceptable aussi: ", "").strip(),
                "FOCALISATION":    row.get("Acceptable aussi: .1", "").strip(),
                "MODE NARRATIF":   row.get("Acceptable aussi: .2", "").strip(),
                "REGIME NARRATIF": row.get("Acceptable aussi: .3", "").strip(),
                "ESPACE":          row.get("Acceptable aussi: .4", "").strip(),
                "INTRIGUE":        row.get("Acceptable aussi: .5", "").strip(),
                "TEMPORALITÉ":     row.get("Acceptable aussi: .6", "").strip(),
            }
    return gold

def load_excerpt(fn, n=SAMPLE_LINES):
    path = os.path.join(CORPUS_DIR, fn)
    if not os.path.exists(path): return None
    lines = open(path, encoding="utf-8").readlines()
    total = len(lines)
    if total <= n: return "".join(lines)
    per = n // 4
    secs = []
    for r in [0, 0.30, 0.60, 1.0]:
        pos = min(int(total*r), total-per)
        secs.append("".join(lines[pos:pos+per]))
    return "\n[...]\n".join(secs)

# ── Prompts ────────────────────────────────────────────────────────────────────
def make_single_criterion_prompt(criterion, excerpt):
    codes = VALID_CODES[criterion]
    descriptions = {
        "TYPE NARRATEUR": "Qui raconte l'histoire? Le narrateur est-il personnage principal (NAR_AUTOD), témoin (NAR_TEM), externe/absent (NAR_EXT), ou variable (NAR_VAR)?",
        "FOCALISATION": "Quel est le point de vue? Accès à un personnage (FOC_INT), surface sans accès intérieur (FOC_EXT), omniscient (FOC_ZERO), ou variable (FOC_VAR)?",
        "MODE NARRATIF": "Quel est le contenu dominant? Actions/faits (MOD_EVT), descriptions/ambiances (MOD_DESC), réflexions intérieures (MOD_INTR), dialogues (MOD_DIA), ou mixte équilibré (MOD_MIX)?",
        "REGIME NARRATIF": "Quel type de monde? Autobiographique/autofictionnel (REG_AUTO), réaliste (REG_REAL), fantastique (REG_FANT), dystopique/uchronique (REG_SPEC)?",
        "ESPACE": "Comment l'espace est-il organisé? Un lieu unique (ESP_UNIT), lieux multiples fragmentés (ESP_FRAG), déplacements continus (ESP_ITIN), ou espace imaginaire (ESP_IMAG)?",
        "INTRIGUE": "Quelle est la structure de l'intrigue? Linéaire/continue (INTR_LIN), fragmentée/discontinue (INTR_FRAG), ou cyclique avec répétitions (INTR_CYC)?",
        "TEMPORALITÉ": "Comment le temps est-il géré? Linéaire/chronologique (TEMP_LIN), avec analepses/retours en arrière (TEMP_DIS), ou temporalité éclatée/complexe (TEMP_DESORD)?",
    }
    return f"""Analyse cet extrait de roman français pour déterminer UN SEUL critère narratologique.

CRITÈRE: {criterion}
QUESTION: {descriptions[criterion]}
CODES VALIDES: {' | '.join(codes)}

EXTRAIT:
{excerpt[:2500]}

Réponds UNIQUEMENT avec ce JSON (un seul code):
{{"{criterion}": "CODE"}}"""

# ── Ollama call ────────────────────────────────────────────────────────────────
def call_ollama(model, prompt, timeout=300):
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 200},
        }, timeout=timeout)
        resp.raise_for_status()
        content = resp.json()["message"]["content"]
        # Strip thinking tags
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        # Extract JSON
        m = re.search(r'\{.*?\}', content, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        print(f" [ERR: {str(e)[:50]}]", end="")
    return {}

# ── Per-criterion voting ───────────────────────────────────────────────────────
def classify_criterion(criterion, excerpt, model, n_votes):
    votes = []
    valid = VALID_CODES[criterion]
    for v in range(n_votes):
        result = call_ollama(model, make_single_criterion_prompt(criterion, excerpt))
        pred = result.get(criterion, "").strip()
        if pred in valid:
            votes.append(pred)
    if not votes:
        return None, votes
    # Majority vote
    winner = Counter(votes).most_common(1)[0][0]
    return winner, votes

# ── Main evaluation ────────────────────────────────────────────────────────────
def main():
    print("="*65)
    print("PER-CRITERION MULTI-MODEL ENSEMBLE")
    print("="*65)
    for c, (model, n) in CRITERION_MODEL.items():
        print(f"  {c:<20}: {model} x{n} votes")
    print("="*65)

    gold = load_gold()
    print(f"\nGold set: {len(gold)} novels")

    # Find novels in corpus
    corpus_files = set(os.listdir(CORPUS_DIR))
    to_run = [(fn, labels) for fn, labels in gold.items() if fn in corpus_files]
    missing = [fn for fn in gold if fn not in corpus_files]
    print(f"Found in corpus: {len(to_run)} | Missing: {len(missing)}")

    scores = {c: {"correct": 0, "total": 0} for c in CRITERIA}
    results = []

    for i, (fn, gold_labels) in enumerate(to_run, 1):
        print(f"\n[{i:>2}/{len(to_run)}] {fn}")
        excerpt = load_excerpt(fn)
        if excerpt is None:
            print("  ⚠️  Could not load excerpt")
            continue

        preds = {}
        for criterion, (model, n_votes) in CRITERION_MODEL.items():
            print(f"  {criterion:<20} [{model}]", end="", flush=True)
            pred, votes = classify_criterion(criterion, excerpt, model, n_votes)
            preds[criterion] = pred
            gold_val = gold_labels.get(criterion, "")
            alt_val  = gold_labels.get("_alt", {}).get(criterion, "")
            is_correct = pred and (pred == gold_val or (alt_val and pred == alt_val))
            mark = "✓" if is_correct else "✗"
            print(f" → {pred or '?':<12} {mark} (votes: {votes})")
            if gold_val:
                scores[criterion]["total"] += 1
                if is_correct:
                    scores[criterion]["correct"] += 1

        results.append({
            "fichier": fn,
            **{c: preds.get(c, "") for c in CRITERIA},
            **{f"GOLD_{c[:3].upper()}": gold_labels.get(c, "") for c in CRITERIA},
        })

        # Checkpoint every 10 novels
        if i % 10 == 0:
            save_results(results)
            print(f"\n  💾 Checkpoint saved ({i} done)")

    # Final save
    save_results(results)

    # Print summary
    print(f"\n{'='*65}")
    print("ENSEMBLE RESULTS — per-criterion multi-model voting")
    print(f"{'='*65}")
    oc = ot = 0
    for c in CRITERIA:
        s = scores[c]
        if s["total"] > 0:
            acc = s["correct"]/s["total"]*100
            model_used = CRITERION_MODEL[c][0]
            bar = "█" * int(acc/5)
            print(f"  {c:<20} {s['correct']:>2}/{s['total']:>2} ({acc:>5.1f}%) {bar}  [{model_used}]")
            oc += s["correct"]; ot += s["total"]
    print(f"  {'-'*60}")
    if ot:
        print(f"  OVERALL: {oc}/{ot} ({oc/ot*100:.1f}%)")
    print(f"{'='*65}")
    print(f"\n  Previous best (Hybrid 3-way, 60 novels): 69.3%")
    print(f"  Map-reduce (76 novels):                  65.4%")
    print(f"  Ensemble (this run):                     {oc/ot*100:.1f}%" if ot else "")
    print(f"\n✅ Results saved to {OUTPUT_FILE}")

def save_results(results):
    if not results: return
    fields = ["fichier"] + CRITERIA + [f"GOLD_{c[:3].upper()}" for c in CRITERIA]
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)

if __name__ == "__main__":
    main()
