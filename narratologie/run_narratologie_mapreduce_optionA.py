#!/usr/bin/env python3
"""
run_narratologie_mapreduce_optionA.py  —  v4 (Option A)

Key improvement over v3:
  Instead of one combined reduce prompt deciding all 7 criteria,
  each criterion gets its OWN targeted reduce prompt that directly
  addresses the specific confusion patterns found in error analysis:

  FOCALISATION:   over-predicts FOC_VAR (saw FOC_ZERO→FOC_VAR 8x, FOC_INT→FOC_VAR 8x)
  ESPACE:         over-predicts ESP_FRAG (saw ESP_UNIT→ESP_FRAG 12x)
  MODE NARRATIF:  over-predicts MOD_MIX (26/29 errors were wrongly MOD_MIX)
  REGIME NARRATIF: confuses REG_REAL→REG_AUTO (7x, first-person ≠ autofiction)
  INTRIGUE:       symmetric LIN↔FRAG confusion (10x + 8x)
  TEMPORALITÉ:    over-predicts TEMP_DIS (sees any flashback → calls it DIS)

Map step is identical to v3. Only the reduce step changes.

Usage:
  cd ~/ecopoetique/narratologie
  python run_narratologie_mapreduce_optionA.py --test 5
  python run_narratologie_mapreduce_optionA.py
  python run_narratologie_mapreduce_optionA.py --resume
"""

import os, csv, json, time, re, argparse, requests
from datetime import datetime

# ── CONFIG ───────────────────────────────────────────────────────────────────
OLLAMA_URL  = "http://localhost:11435/api/chat"
MODEL       = "qwen3:30b"
CORPUS_DIR  = os.path.expanduser("~/ecopoetique/CORPUS_TOTAL")
GOLD_FILE   = os.path.expanduser("~/ecopoetique/narratologie/GOLD_narratologie.csv")
OUTPUT_FILE = os.path.expanduser("~/ecopoetique/narratologie/resultats_qwen3_30b_mapreduce_optionA.csv")
N_CHUNKS    = 9
MAX_LINES   = 400
TIMEOUT     = 300

# ── MAP PROMPT (unchanged from v3) ───────────────────────────────────────────
MAP_SYSTEM = """You are a French literary analyst. You MUST respond with ONLY a JSON object.
No thinking. No explanation. No preamble. Just the JSON."""

def map_prompt(chunk_text, chunk_index, total_chunks):
    pos = ("BEGINNING" if chunk_index == 0 else
           "END"       if chunk_index == total_chunks - 1 else
           f"MIDDLE section {chunk_index+1} of {total_chunks}")
    return f"""Analyse this passage from the {pos} of a French novel.

--- PASSAGE ---
{chunk_text[:3000]}
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

# ── TARGETED REDUCE PROMPTS (one per criterion) ───────────────────────────────

REDUCE_SYSTEM = """You are an expert in French narratology (Genette framework).
You MUST respond with ONLY a JSON object containing exactly one key.
No thinking. No explanation. No preamble. Just the JSON."""

def reduce_focalisation(obs):
    """
    Error pattern: model over-predicts FOC_VAR.
    Fix: explicitly distinguish FOC_ZERO (omniscient=knows ALL characters' thoughts)
    from FOC_VAR (perspective SWITCHES between named characters chapter by chapter).
    FOC_INT means ONE character's interiority dominates throughout.
    """
    return f"""Based on these observations from 9 sections of a novel:
{json.dumps(obs, ensure_ascii=False, indent=2)}

Classify FOCALISATION using these PRECISE rules:

FOC_INT  = ONE character's inner thoughts/feelings dominate throughout the WHOLE novel.
           Even if other characters appear, we primarily see the world through one mind.
           Most "inner_thoughts: yes_one_character" observations → likely FOC_INT.

FOC_ZERO = OMNISCIENT narrator who freely enters ANY character's mind at will.
           The narrator knows what multiple characters think WITHOUT switching perspective.
           Key signal: "inner_thoughts: yes_multiple" across many sections.

FOC_VAR  = The PRIMARY perspective character CHANGES between named characters.
           Different sections are clearly written FROM different characters' viewpoints.
           NOT just "multiple characters appear" — the FOCALIZATION POINT changes.
           Requires clear evidence of perspective shifts, not just multiple characters.

FOC_EXT  = Narrator sees characters purely from OUTSIDE — no inner thoughts revealed.
           "inner_thoughts: no" in most sections.

CRITICAL DISTINCTIONS:
- Multiple characters present ≠ FOC_VAR. FOC_VAR requires the LENS to shift.
- If unsure between FOC_ZERO and FOC_VAR: ask "does one narrator freely enter all minds (ZERO) 
  or does the chapter/section perspective belong to a specific character (VAR)?"
- First-person narrative almost always = FOC_INT (one protagonist's view).

Return ONLY: {{"FOCALISATION": "<FOC_INT|FOC_ZERO|FOC_VAR|FOC_EXT>"}}"""

def reduce_espace(obs):
    """
    Error pattern: model over-predicts ESP_FRAG (12x ESP_UNIT→ESP_FRAG).
    Fix: ESP_UNIT allows multiple places as long as ONE main location dominates.
    Model was calling anything with multiple locations ESP_FRAG.
    """
    # Count location signals
    single = sum(1 for o in obs if o.get("space") == "single_location")
    multiple = sum(1 for o in obs if o.get("space") == "multiple_locations")
    journey = sum(1 for o in obs if o.get("space") == "journey_travel")
    imaginary = sum(1 for o in obs if o.get("space") == "imaginary")
    
    return f"""Based on these observations from 9 sections of a novel:
{json.dumps(obs, ensure_ascii=False, indent=2)}

Section space counts: single_location={single}, multiple_locations={multiple}, 
journey_travel={journey}, imaginary={imaginary}

Classify ESPACE using these PRECISE rules:

ESP_UNIT  = Action centered on ONE main location (house, city, workplace).
            Secondary locations may be mentioned but the story RETURNS to one home base.
            Signal: majority of sections are "single_location" OR action keeps returning 
            to the same place. Do NOT confuse "mentions other places" with "fragmented."

ESP_FRAG  = Story scattered across MANY DISCONNECTED locations with no single anchor.
            Characters are in genuinely different, unconnected places.
            Signal: majority of sections are "multiple_locations" with no dominant base.

ESP_ITIN  = Characters TRAVEL THROUGH places in a journey/road-trip structure.
            Locations change PROGRESSIVELY — the movement itself is the structure.
            Signal: majority of sections are "journey_travel" OR clear travel progression.

ESP_IMAG  = Story set in a wholly invented world (not realistic geography).
            Signal: majority of sections are "imaginary."

CRITICAL: ESP_UNIT does NOT mean only one room. A novel set "in Paris" with scenes 
in different cafés, apartments, streets is still ESP_UNIT if Paris is the anchor.
Only choose ESP_FRAG if locations are genuinely disconnected with no dominant base.

Return ONLY: {{"ESPACE": "<ESP_UNIT|ESP_FRAG|ESP_ITIN|ESP_IMAG>"}}"""

def reduce_mode(obs):
    """
    Error pattern: 26/29 errors were things wrongly called MOD_MIX.
    Fix: force the model to identify the DOMINANT mode. MOD_MIX only if truly balanced.
    """
    action = sum(1 for o in obs if o.get("dominant_mode") == "action_events")
    desc   = sum(1 for o in obs if o.get("dominant_mode") == "description")
    intr   = sum(1 for o in obs if o.get("dominant_mode") == "introspection")
    mixed  = sum(1 for o in obs if o.get("dominant_mode") == "mixed")
    
    return f"""Based on these observations from 9 sections of a novel:
{json.dumps(obs, ensure_ascii=False, indent=2)}

Section mode counts: action_events={action}, description={desc}, 
introspection={intr}, mixed={mixed}

Classify MODE NARRATIF using these PRECISE rules:

MOD_EVT  = EVENTS AND ACTION clearly dominate. Plot moves forward through things happening.
           Characters do things, events occur, story progresses through action.
           Choose this if action_events sections outnumber others, OR if "mixed" sections
           are mostly action-driven.

MOD_DESC = DESCRIPTION clearly dominates. Places, objects, appearances are described at length.
           The text spends more time depicting the world than moving plot or inner life.

MOD_INTR = INNER LIFE clearly dominates. Thoughts, feelings, memories, reflection.
           The narrative stays inside a character's consciousness more than outside.

MOD_MIX  = GENUINELY BALANCED between two or more modes with NO clear dominant.
           ONLY choose this if you cannot identify a dominant mode.
           Do NOT choose MOD_MIX just because multiple modes appear — every novel has some mix.
           Ask: "If I had to pick ONE mode that describes most of this novel, what is it?"
           Only if that question is truly unanswerable → MOD_MIX.

RULE: If action_events > introspection + description → MOD_EVT
      If introspection > action_events + description → MOD_INTR  
      If description > action_events + introspection → MOD_DESC
      Otherwise → MOD_MIX

Return ONLY: {{"MODE NARRATIF": "<MOD_EVT|MOD_DESC|MOD_INTR|MOD_MIX>"}}"""

def reduce_regime(obs):
    """
    Error pattern: 7x REG_REAL→REG_AUTO (model sees 1st person → assumes autofiction).
    Fix: REG_AUTO requires explicit real-world author identity, not just 1st person.
    """
    auto_signals = sum(1 for o in obs if o.get("world_type") == "autobiographical")
    real_signals = sum(1 for o in obs if o.get("world_type") == "realistic")
    fant_signals = sum(1 for o in obs if o.get("world_type") == "fantastic")
    spec_signals = sum(1 for o in obs if o.get("world_type") == "speculative_sf")
    first_person = sum(1 for o in obs if o.get("narrator_voice") == "first_person")
    
    return f"""Based on these observations from 9 sections of a novel:
{json.dumps(obs, ensure_ascii=False, indent=2)}

Section world_type counts: autobiographical={auto_signals}, realistic={real_signals},
fantastic={fant_signals}, speculative_sf={spec_signals}
First-person sections: {first_person}/9

Classify REGIME NARRATIF using these PRECISE rules:

REG_REAL = World follows REAL-WORLD rules. Could be set in contemporary or historical reality.
           Characters are fictional even if setting is real. Most common regime.
           First-person narration alone does NOT make it REG_AUTO.

REG_AUTO = AUTOFICTION or AUTOBIOGRAPHY. The narrator IS explicitly the real author,
           or a thinly veiled version of themselves with their real name/biography.
           Requires EXPLICIT signals: author's real name used, real biographical events 
           described as personal experience, explicit "I, the author" framing.
           CRITICAL: First-person narration ≠ REG_AUTO. A first-person fictional narrator
           is still REG_REAL. Only choose REG_AUTO for genuine autofiction.

REG_FANT = FANTASTIC elements intrude into an otherwise normal world.
           Impossible events occur but the world is otherwise realistic.
           Characters or narrator react with surprise to impossible events.

REG_SPEC = SPECULATIVE/SF. The entire world operates under different rules.
           Future setting, alternate reality, post-apocalyptic, sci-fi worldbuilding.
           The impossible is normal within this world's logic.

DISTINCTION: REG_FANT = impossible events surprise characters (horror, magic realism)
             REG_SPEC = impossible is the baseline reality (sci-fi, dystopia)

Return ONLY: {{"REGIME NARRATIF": "<REG_REAL|REG_AUTO|REG_FANT|REG_SPEC>"}}"""

def reduce_intrigue(obs):
    """
    Error pattern: symmetric LIN↔FRAG confusion (10x + 8x).
    Fix: explicit structural rules — INTR_LIN allows subplots, INTR_FRAG requires
    genuinely parallel/broken storylines that don't resolve into one.
    """
    threads = [o.get("plot_threads", "") for o in obs]
    one_count = threads.count("one")
    multi_count = threads.count("multiple")
    
    return f"""Based on these observations from 9 sections of a novel:
{json.dumps(obs, ensure_ascii=False, indent=2)}

Plot thread counts across sections: one={one_count}, multiple={multi_count}

Classify INTRIGUE using these PRECISE rules:

INTR_LIN  = ONE main storyline followed from beginning to end.
            Subplots and secondary characters are allowed — they serve the main plot.
            The novel has a clear single narrative spine.
            Signal: most sections report "plot_threads: one" OR multiple threads 
            that clearly converge into one story.

INTR_FRAG = MULTIPLE genuinely parallel storylines, OR one storyline deliberately
            broken/fragmented into pieces that don't follow conventional order.
            Multiple POV characters with their own separate arcs.
            OR: a single story told in deliberately disconnected fragments.
            Signal: consistently "plot_threads: multiple" with separate character arcs,
            OR structure is explicitly broken/collage-like.

INTR_CYC  = Story ends where it began — circular/cyclical structure.
            The ending returns to the opening situation or moment.
            Rare — only choose if there is explicit evidence of circular return.

CRITICAL DISTINCTION:
- A novel with ONE protagonist who meets many people = INTR_LIN (not fragmented)
- A novel with THREE protagonists each with their own storyline = INTR_FRAG
- When in doubt between LIN and FRAG: if there is ONE clear protagonist 
  whose journey we follow → INTR_LIN

Return ONLY: {{"INTRIGUE": "<INTR_LIN|INTR_FRAG|INTR_CYC>"}}"""

def reduce_temporalite(obs):
    """
    Error pattern: 13x TEMP_LIN→TEMP_DIS (model sees any flashback → calls it DIS).
    Fix: TEMP_LIN allows minor flashbacks. TEMP_DIS requires flashbacks to be
    STRUCTURALLY significant, not just occasional memories.
    """
    chron = sum(1 for o in obs if o.get("time_order") == "chronological")
    flash = sum(1 for o in obs if o.get("time_order") == "has_flashbacks_or_jumps")
    scramb = sum(1 for o in obs if o.get("time_order") == "radically_scrambled")
    all_markers = []
    for o in obs:
        all_markers.extend(o.get("time_markers", []))
    
    return f"""Based on these observations from 9 sections of a novel:
{json.dumps(obs, ensure_ascii=False, indent=2)}

Time order counts: chronological={chron}, has_flashbacks_or_jumps={flash}, 
radically_scrambled={scramb}
Time markers found: {all_markers[:15]}

Classify TEMPORALITÉ using these PRECISE rules:

TEMP_LIN    = Events told in CHRONOLOGICAL ORDER overall.
              Minor flashbacks (memories, brief recalls) are ALLOWED — every novel has some.
              Choose TEMP_LIN if the DOMINANT narrative flow is forward in time.
              Signal: majority of sections are "chronological."
              CRITICAL: A novel is TEMP_LIN even if characters remember the past,
              as long as the story moves forward overall.

TEMP_DIS    = SIGNIFICANT time jumps or flashbacks are STRUCTURALLY IMPORTANT.
              The narrative regularly moves between different time periods.
              Flashbacks are not just memories — they are substantial narrative sequences.
              The non-chronological structure is a deliberate narrative choice.
              Signal: many sections show "has_flashbacks_or_jumps" AND the jumps 
              cover substantial time periods (years, decades), not just brief memories.

TEMP_DESORD = Time is RADICALLY SCRAMBLED throughout.
              The chronological order is systematically disrupted.
              The reader must actively reconstruct the timeline.
              Signal: "radically_scrambled" appears, OR the sequence of events is 
              genuinely impossible to follow chronologically.

THRESHOLD RULE:
- If {chron} or more sections are chronological out of 9 → strongly consider TEMP_LIN
- Only choose TEMP_DIS if flashbacks are major structural elements, not just memories
- Only choose TEMP_DESORD if scrambling is extreme and consistent

Return ONLY: {{"TEMPORALITÉ": "<TEMP_LIN|TEMP_DIS|TEMP_DESORD>"}}"""

def reduce_nar(obs):
    """TYPE NARRATEUR already at 90% — keep simple combined prompt."""
    first_p = sum(1 for o in obs if o.get("narrator_voice") == "first_person")
    third_p = sum(1 for o in obs if o.get("narrator_voice") == "third_person")
    protag  = sum(1 for o in obs if o.get("narrator_role") == "protagonist")
    witness = sum(1 for o in obs if o.get("narrator_role") == "witness")
    
    return f"""Based on these observations from 9 sections of a novel:
First-person sections: {first_p}/9, Third-person sections: {third_p}/9
Narrator as protagonist: {protag}/9, Narrator as witness: {witness}/9

Full observations:
{json.dumps(obs, ensure_ascii=False, indent=2)}

Classify TYPE NARRATEUR:
  NAR_AUTOD = First-person narrator IS the main protagonist
  NAR_TEM   = First-person narrator is a WITNESS (not main character)  
  NAR_EXT   = Third-person narrator outside the story

If majority first_person AND protagonist → NAR_AUTOD
If majority first_person AND witness → NAR_TEM
If majority third_person → NAR_EXT

Return ONLY: {{"TYPE NARRATEUR": "<NAR_AUTOD|NAR_TEM|NAR_EXT>"}}"""

# ── OLLAMA CALL ───────────────────────────────────────────────────────────────
def call_ollama(system_msg, user_msg):
    user_msg = user_msg.encode("utf-8", errors="replace").decode("utf-8")
    user_msg = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", user_msg)
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": user_msg},
        ],
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_ctx": 16384,
            "num_predict": 4096,
        }
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    content = data.get("message", {}).get("content", "") or data.get("response", "")
    return content.strip()

def extract_json(text):
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
    objects = []
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0: start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                objects.append(text[start:i+1])
                start = None
    for candidate in reversed(objects):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise ValueError(f"No valid JSON found. Response: {repr(text[:300])}")

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
        next(reader)
        for row in reader:
            if not row or not row[0].strip():
                continue
            def col(i): return row[i].strip() if i < len(row) else ""
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
    if not pred: return False
    p = pred.strip().upper()
    if p == main.strip().upper(): return True
    if alt and p == alt.strip().upper(): return True
    return False

CRITERIA = [
    ("TYPE NARRATEUR",  "NAR_alt"),
    ("FOCALISATION",    "FOC_alt"),
    ("MODE NARRATIF",   "MOD_alt"),
    ("REGIME NARRATIF", "REG_alt"),
    ("ESPACE",          "ESP_alt"),
    ("INTRIGUE",        "INT_alt"),
    ("TEMPORALITÉ",     "TEM_alt"),
]

# ── EVALUATION ────────────────────────────────────────────────────────────────
def evaluate(results, gold):
    scores = {c: [0, 0] for c, _ in CRITERIA}
    oc = ot = 0
    for r in results:
        fn = r["File"]
        if fn not in gold: continue
        g = gold[fn]
        for crit, alt_key in CRITERIA:
            pred = r.get(crit, "").strip()
            if not pred: continue
            scores[crit][1] += 1
            ot += 1
            if is_correct(pred, g[crit], g[alt_key]):
                scores[crit][0] += 1
                oc += 1

    print("\n" + "="*62)
    print(f"  OPTION A RESULTS  —  {MODEL}")
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
    print(f"\n  Baseline (125-line):   55.7%")
    print(f"  Map-reduce v3:         63.3%")
    if ot:
        delta_base = ov - 55.7
        delta_v3   = ov - 63.3
        print(f"  Option A (this run):   {ov:.1f}%  "
              f"({'+'if delta_base>=0 else ''}{delta_base:.1f}pp vs baseline, "
              f"{'+'if delta_v3>=0 else ''}{delta_v3:.1f}pp vs v3)")
    print()

# ── SAVE / LOAD ───────────────────────────────────────────────────────────────
def save_results(rows, path):
    if not rows: return
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

    # ── MAP STEP ──
    observations = []
    for idx, text in chunks:
        if not text.strip(): continue
        try:
            raw = call_ollama(MAP_SYSTEM, map_prompt(text, idx, N_CHUNKS))
            obs = extract_json(raw)
            observations.append(obs)
            print(f"    ✓ chunk {idx+1}/{N_CHUNKS}: "
                  f"voice={obs.get('narrator_voice','?')[:12]} "
                  f"mode={obs.get('dominant_mode','?')[:12]} "
                  f"time={obs.get('time_order','?')[:18]}")
        except Exception as e:
            print(f"    ✗ chunk {idx+1}/{N_CHUNKS} failed: {e}")
            observations.append({"chunk": idx+1, "error": str(e)})

    good = [o for o in observations if "error" not in o]
    if not good:
        raise ValueError(f"All {N_CHUNKS} chunks failed")

    print(f"    → reduce step ({len(good)}/{N_CHUNKS} good) — 7 targeted calls")

    # ── REDUCE STEP — one call per criterion ──
    result = {}
    reduce_calls = [
        ("TYPE NARRATEUR",  reduce_nar),
        ("FOCALISATION",    reduce_focalisation),
        ("MODE NARRATIF",   reduce_mode),
        ("REGIME NARRATIF", reduce_regime),
        ("ESPACE",          reduce_espace),
        ("INTRIGUE",        reduce_intrigue),
        ("TEMPORALITÉ",     reduce_temporalite),
    ]

    for crit, prompt_fn in reduce_calls:
        try:
            raw = call_ollama(REDUCE_SYSTEM, prompt_fn(good))
            parsed = extract_json(raw)
            # Extract the value for this criterion
            val = parsed.get(crit, "")
            if not val:
                # Try any value if key mismatch
                val = next(iter(parsed.values()), "")
            result[crit] = val
        except Exception as e:
            print(f"    ✗ reduce {crit} failed: {e}")
            result[crit] = ""

    return result

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test",   type=int, default=0)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    print(f"\n{'='*62}")
    print(f"  NARRATOLOGIE MAP-REDUCE  Option A  (targeted reduce)")
    print(f"  Model: {MODEL}   Port: 11435   Chunks: {N_CHUNKS}")
    print(f"  Started: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"{'='*62}\n")

    try:
        r = requests.get("http://localhost:11435/api/tags", timeout=5)
        models = [m["name"] for m in r.json().get("models", [])]
        print(f"Ollama reachable. Models: {models}\n")
    except Exception as e:
        print(f"⚠ Cannot reach Ollama: {e}")
        return

    gold = load_gold(GOLD_FILE)
    print(f"Gold: {len(gold)} novels")
    sample = list(gold.values())[0]
    print(f"TEMPORALITÉ sample: '{sample['TEMPORALITÉ']}' "
          f"{'✓' if sample['TEMPORALITÉ'] else '✗'}")
    n_alt = sum(1 for g in gold.values()
                if any(g[k] for k in ["NAR_alt","FOC_alt","MOD_alt",
                                       "REG_alt","ESP_alt","INT_alt","TEM_alt"]))
    print(f"With 'Acceptable aussi': {n_alt}\n")

    all_txt = set(os.listdir(CORPUS_DIR))
    to_run  = [(fn, os.path.join(CORPUS_DIR, fn)) for fn in gold if fn in all_txt]
    print(f"Novels in CORPUS_TOTAL: {len(to_run)}")

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
