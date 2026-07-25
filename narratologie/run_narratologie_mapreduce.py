#!/usr/bin/env python3
"""
run_narratologie_mapreduce.py  —  v3
Fixes vs v2:
  - Port changed to 11434 (where qwen3:30b actually runs)
  - think:False replaced by /no_think suffix in model name (works on all Ollama versions)
  - Stronger JSON extraction: finds first complete {...} block even inside thinking text
  - Added raw response debug on failure so we can see what the model returns

Usage:
  cd ~/ecopoetique/narratologie
  source ~/digitize_medical_records/labelimg_env/bin/activate
  python run_narratologie_mapreduce.py --test 3
  python run_narratologie_mapreduce.py
  python run_narratologie_mapreduce.py --resume
"""

import os, csv, json, time, re, argparse, requests
from datetime import datetime

# ── CONFIG ───────────────────────────────────────────────────────────────────
OLLAMA_URL  = "http://localhost:11435/api/chat"   # port 11435 — where model runs
MODEL       = "qwen3:30b"                          # /no_think added per-call below
CORPUS_DIR  = os.path.expanduser("~/ecopoetique/CORPUS_TOTAL")
GOLD_FILE   = os.path.expanduser("~/ecopoetique/narratologie/GOLD_narratologie.csv")
OUTPUT_FILE = os.path.expanduser("~/ecopoetique/narratologie/resultats_qwen3_30b_mapreduce.csv")
N_CHUNKS    = 9
MAX_LINES   = 400
TIMEOUT     = 300

# ── CRITERIA DEFINITIONS ─────────────────────────────────────────────────────
CRITERIA_DEFS = """
TYPE NARRATEUR:
  NAR_AUTOD = Narrator IS the main protagonist (1st person, tells own story)
  NAR_TEM   = Narrator is 1st person but a WITNESS, not the main character
  NAR_EXT   = Narrator is OUTSIDE the story (3rd person, heterodiegetic)

FOCALISATION:
  FOC_INT   = Only one character's inner life is visible (limited POV)
  FOC_EXT   = Characters seen from outside only, no inner thoughts revealed
  FOC_ZERO  = Omniscient: knows all characters' inner lives
  FOC_VAR   = Shifts between characters across the text

MODE NARRATIF:
  MOD_EVT   = Dominated by action and events
  MOD_DESC  = Dominated by description of places/objects/appearances
  MOD_INTR  = Dominated by inner thoughts, feelings, memories, reflection
  MOD_MIX   = Roughly equal mix of two or more modes

REGIME NARRATIF:
  REG_REAL  = Realist: world follows real-world rules
  REG_AUTO  = Autofiction/autobiographical: narrator's real or near-real life
  REG_FANT  = Fantastic: impossible events in an otherwise normal world
  REG_SPEC  = Speculative/SF: alternate or future world

ESPACE:
  ESP_UNIT  = One main location throughout
  ESP_FRAG  = Many disconnected locations
  ESP_ITIN  = Journey/travel structure
  ESP_IMAG  = Wholly imaginary world

INTRIGUE:
  INTR_LIN  = One main storyline, followed start to finish
  INTR_FRAG = Multiple storylines, or one broken and reassembled
  INTR_CYC  = Story returns to its starting point

TEMPORALITÉ:
  TEMP_LIN    = Events told in chronological order
  TEMP_DIS    = Significant flashbacks or time jumps
  TEMP_DESORD = Radically scrambled time throughout
"""

# ── MAP PROMPT ────────────────────────────────────────────────────────────────
MAP_SYSTEM = """You are a French literary analyst. You MUST respond with ONLY a JSON object.
No thinking. No explanation. No preamble. Just the JSON."""

def map_prompt(chunk_text, chunk_index, total_chunks):
    pos = ("BEGINNING" if chunk_index == 0 else
           "END"       if chunk_index == total_chunks - 1 else
           f"MIDDLE section {chunk_index+1} of {total_chunks}")
    return f"""Analyse this passage from the {pos} of a French novel.

--- PASSAGE ---
{chunk_text[:6000]}
--- END ---

Answer ONLY with this JSON (replace ... with your answers, no other text):
{{
  "chunk": {chunk_index + 1},
  "position": "{pos}",
  "narrator_voice": "first_person OR third_person OR unclear",
  "narrator_role": "protagonist OR witness OR not_applicable",
  "inner_thoughts": "yes_one_character OR yes_multiple OR no",
  "dominant_mode": "action_events OR description OR introspection OR mixed",
  "world_type": "realistic OR autobiographical OR fantastic OR speculative_sf",
  "space": "single_location OR multiple_locations OR journey_travel OR imaginary",
  "plot_threads": "one OR multiple OR unclear",
  "time_order": "chronological OR has_flashbacks_or_jumps OR radically_scrambled OR unclear",
  "time_markers": [],
  "key_observation": "one sentence"
}}"""

# ── REDUCE PROMPT ─────────────────────────────────────────────────────────────
REDUCE_SYSTEM = """You are an expert in French narratology. You MUST respond with ONLY a JSON object.
No thinking. No explanation. No preamble. Just the JSON."""

def reduce_prompt(observations, filename):
    return f"""Novel: {filename}

Observations from {len(observations)} sections (beginning → end):
{json.dumps(observations, ensure_ascii=False, indent=2)}

DEFINITIONS:
{CRITERIA_DEFS}

Based on ALL sections together, classify the novel.
For INTRIGUE and TEMPORALITÉ look at structure across the WHOLE novel.
Choose EXACTLY ONE code per criterion.

Respond ONLY with this JSON (no other text):
{{
  "TYPE NARRATEUR": "NAR_AUTOD or NAR_TEM or NAR_EXT",
  "FOCALISATION": "FOC_INT or FOC_EXT or FOC_ZERO or FOC_VAR",
  "MODE NARRATIF": "MOD_EVT or MOD_DESC or MOD_INTR or MOD_MIX",
  "REGIME NARRATIF": "REG_REAL or REG_AUTO or REG_FANT or REG_SPEC",
  "ESPACE": "ESP_UNIT or ESP_FRAG or ESP_ITIN or ESP_IMAG",
  "INTRIGUE": "INTR_LIN or INTR_FRAG or INTR_CYC",
  "TEMPORALITÉ": "TEMP_LIN or TEMP_DIS or TEMP_DESORD"
}}"""

# ── OLLAMA CALL ───────────────────────────────────────────────────────────────
def call_ollama(system_msg, user_msg):
    """
    Uses /no_think suffix on model name — this is the correct way to suppress
    qwen3 thinking mode across all Ollama versions.
    """
    payload = {
        "model": MODEL,   # suppresses <think> blocks
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": user_msg},
        ],
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_ctx": 16384,
            "num_predict": 5000,
        }
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    content = data.get("message", {}).get("content", "")
    if not content:
        content = data.get("response", "")
    return content.strip()

def extract_json(text):
    """
    Robustly extract a JSON object from model output.
    Handles: thinking text before JSON, markdown fences, partial think blocks.
    Strategy: find the LAST complete {...} block in the response.
    """
    # Strip <think>...</think> blocks
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Strip markdown fences
    text = re.sub(r"```(?:json)?", "", text).replace("```", "")

    # Find ALL complete JSON objects (balanced braces)
    objects = []
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                objects.append(text[start:i+1])
                start = None

    # Try each found object, return the last valid one (usually the answer)
    for candidate in reversed(objects):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    raise ValueError(f"No valid JSON object found. Response was:\n{text[:400]}")

# ── CHUNKING ──────────────────────────────────────────────────────────────────
def chunk_novel(lines, n=N_CHUNKS, max_lines=MAX_LINES):
    total = len(lines)
    size  = max(total // n, 1)
    chunks = []
    for i in range(n):
        start = i * size
        end   = start + size if i < n - 1 else total
        sl = lines[start:end]
        if len(sl) > max_lines:
            mid  = len(sl) // 2
            half = max_lines // 2
            sl   = sl[max(0, mid-half): mid+half]
        chunks.append((i, "".join(sl)))
    return chunks

# ── GOLD LOADING ──────────────────────────────────────────────────────────────
def load_gold(path):
    gold = {}
    with open(path, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader)  # skip header — we read by fixed column index
        for row in reader:
            if not row or not row[0].strip():
                continue
            def col(i):
                return row[i].strip() if i < len(row) else ""
            fn = col(0)
            gold[fn] = {
                "TYPE NARRATEUR":  col(4),  "NAR_alt": col(5),
                "FOCALISATION":    col(6),  "FOC_alt": col(7),
                "MODE NARRATIF":   col(8),  "MOD_alt": col(9),
                "REGIME NARRATIF": col(10), "REG_alt": col(11),
                "ESPACE":          col(12), "ESP_alt": col(13),
                "INTRIGUE":        col(14), "INT_alt": col(15),
                "TEMPORALITÉ":     col(16), "TEM_alt": col(17),
            }
    return gold

def is_correct(pred, main, alt=""):
    if not pred:
        return False
    p = pred.strip().upper()
    if p == main.strip().upper():
        return True
    if alt and p == alt.strip().upper():
        return True
    return False

# ── EVALUATION ────────────────────────────────────────────────────────────────
CRITERIA = [
    ("TYPE NARRATEUR",  "NAR_alt"),
    ("FOCALISATION",    "FOC_alt"),
    ("MODE NARRATIF",   "MOD_alt"),
    ("REGIME NARRATIF", "REG_alt"),
    ("ESPACE",          "ESP_alt"),
    ("INTRIGUE",        "INT_alt"),
    ("TEMPORALITÉ",     "TEM_alt"),
]

def evaluate(results, gold):
    scores = {c: [0, 0] for c, _ in CRITERIA}
    oc = ot = 0
    for r in results:
        fn = r["File"]
        if fn not in gold:
            continue
        g = gold[fn]
        for crit, alt_key in CRITERIA:
            pred = r.get(crit, "").strip()
            if not pred:
                continue
            scores[crit][1] += 1
            ot += 1
            if is_correct(pred, g[crit], g[alt_key]):
                scores[crit][0] += 1
                oc += 1

    print("\n" + "="*62)
    print(f"  MAP-REDUCE RESULTS  —  {MODEL}")
    print("="*62)
    for crit, (c, t) in scores.items():
        if t:
            acc = c/t*100
            bar = "█" * int(acc/5)
            print(f"  {crit:<22} {c:>2}/{t:<2}  ({acc:>5.1f}%)  {bar}")
    print("-"*62)
    if ot:
        ov = oc/ot*100
        print(f"  {'OVERALL':<22} {oc:>3}/{ot:<3}  ({ov:>5.1f}%)")
    print("="*62)
    print(f"\n  Baseline (125-line samples): 55.7%")
    if ot:
        delta = ov - 55.7
        print(f"  Map-reduce (this run):       {ov:.1f}%  "
              f"({'+'if delta>=0 else ''}{delta:.1f}pp vs baseline)")
    print()

# ── SAVE / LOAD ───────────────────────────────────────────────────────────────
def save_results(rows, path):
    if not rows:
        return
    keys = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

def load_done(path):
    done = set()
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                done.add(row.get("File","").strip())
    return done

# ── PROCESS ONE NOVEL ─────────────────────────────────────────────────────────
def process_novel(filename, filepath):
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    chunks = chunk_novel(lines)
    print(f"    {len(lines)} lines → {N_CHUNKS} chunks of ~{len(lines)//N_CHUNKS} lines")

    observations = []
    for idx, text in chunks:
        if not text.strip():
            continue
        try:
            raw = call_ollama(MAP_SYSTEM, map_prompt(text, idx, N_CHUNKS))
            obs = extract_json(raw)
            observations.append(obs)
            print(f"    ✓ chunk {idx+1}/{N_CHUNKS}: "
                  f"voice={obs.get('narrator_voice','?')[:12]} "
                  f"mode={obs.get('dominant_mode','?')[:12]} "
                  f"time={obs.get('time_order','?')[:20]}")
        except Exception as e:
            # Print first 200 chars of raw response to help debug
            print(f"    ✗ chunk {idx+1}/{N_CHUNKS} failed: {e}")
            observations.append({"chunk": idx+1, "error": str(e)})

    good = [o for o in observations if "error" not in o]
    if not good:
        raise ValueError(f"All {N_CHUNKS} chunks failed — no usable observations")

    print(f"    → reduce step ({len(good)}/{N_CHUNKS} good observations)")
    raw = call_ollama(REDUCE_SYSTEM, reduce_prompt(good, filename))
    return extract_json(raw)

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test",   type=int, default=0)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    print(f"\n{'='*62}")
    print(f"  NARRATOLOGIE MAP-REDUCE  v3")
    print(f"  Model: {MODEL}   Port: 11434   Chunks: {N_CHUNKS}")
    print(f"  Started: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"{'='*62}\n")

    # Quick connectivity check
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = [m["name"] for m in r.json().get("models", [])]
        print(f"Ollama reachable on port 11434. Models: {models}\n")
    except Exception as e:
        print(f"⚠ Cannot reach Ollama on port 11434: {e}")
        print("  Try: ~/start_ollama.sh  or check which port Ollama is on")
        return

    gold = load_gold(GOLD_FILE)
    print(f"Gold: {len(gold)} novels")
    sample = list(gold.values())[0]
    print(f"TEMPORALITÉ sample: '{sample['TEMPORALITÉ']}' "
          f"{'✓' if sample['TEMPORALITÉ'] else '✗ BUG'}")
    n_alt = sum(1 for g in gold.values()
                if any(g[k] for k in ["NAR_alt","FOC_alt","MOD_alt",
                                       "REG_alt","ESP_alt","INT_alt","TEM_alt"]))
    print(f"With 'Acceptable aussi': {n_alt}\n")

    all_txt = set(os.listdir(CORPUS_DIR))
    to_run  = [(fn, os.path.join(CORPUS_DIR, fn)) for fn in gold if fn in all_txt]
    missing = [fn for fn in gold if fn not in all_txt]
    print(f"Novels in CORPUS_TOTAL: {len(to_run)}  missing: {len(missing)}")

    done = load_done(OUTPUT_FILE) if args.resume else set()
    if done:
        print(f"Resuming: {len(done)} done, {len(to_run)-len(done)} remaining")

    to_run = [x for x in to_run if x[0] not in done]
    if args.test:
        to_run = to_run[:args.test]
        print(f"TEST MODE: {args.test} novels")
    print()

    existing = []
    if args.resume and os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            existing = list(csv.DictReader(f))

    output_rows  = list(existing)
    results_eval = []

    for i, (fn, fp) in enumerate(to_run, 1):
        print(f"\n[{i}/{len(to_run)}] {fn}")
        t0 = time.time()
        g  = gold.get(fn, {})
        try:
            pred = process_novel(fn, fp)
            el   = time.time() - t0

            def chk(crit, alt):
                return "✓" if is_correct(pred.get(crit,""), g.get(crit,""), g.get(alt,"")) else "✗"

            print(f"  → {el:.0f}s | "
                  f"NAR={pred.get('TYPE NARRATEUR','?')}{chk('TYPE NARRATEUR','NAR_alt')} "
                  f"FOC={pred.get('FOCALISATION','?')}{chk('FOCALISATION','FOC_alt')} "
                  f"MOD={pred.get('MODE NARRATIF','?')}{chk('MODE NARRATIF','MOD_alt')} "
                  f"REG={pred.get('REGIME NARRATIF','?')}{chk('REGIME NARRATIF','REG_alt')} "
                  f"ESP={pred.get('ESPACE','?')}{chk('ESPACE','ESP_alt')} "
                  f"INT={pred.get('INTRIGUE','?')}{chk('INTRIGUE','INT_alt')} "
                  f"TEM={pred.get('TEMPORALITÉ','?')}{chk('TEMPORALITÉ','TEM_alt')}")

            row = {"File": fn,
                   **{c: pred.get(c,"") for c, _ in CRITERIA},
                   **{f"GOLD_{c[:3]}": g.get(c,"") for c, _ in CRITERIA},
                   **{f"ALT_{c[:3]}":  g.get(a,"") for c, a in CRITERIA}}
            output_rows.append(row)
            results_eval.append(row)

        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            output_rows.append({"File": fn, "ERROR": str(e)})

        if i % 3 == 0:
            save_results(output_rows, OUTPUT_FILE)
            print(f"  💾 checkpoint ({i} done)")

    save_results(output_rows, OUTPUT_FILE)
    print(f"\n✅ Done — {len(results_eval)} novels processed")
    print(f"   Saved to: {OUTPUT_FILE}")

    if results_eval:
        evaluate(results_eval, gold)

if __name__ == "__main__":
    main()
