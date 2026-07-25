import csv, os, re, requests

OLLAMA_URL = "http://localhost:11435/api/chat"
MODEL      = "qwen72b-limited"
GOLD       = "/home/lfarooq/ecopoetique/narratologie/GOLD_narratologie.csv"
OLD60      = "/home/lfarooq/ecopoetique/narratologie/resultats_hybrid.csv"
CORPUS     = os.path.expanduser("~/ecopoetique/CORPUS_TOTAL")
OUTPUT_T   = "/home/lfarooq/ecopoetique/narratologie/resultats_qwen72b_foc_think.csv"
OUTPUT_N   = "/home/lfarooq/ecopoetique/narratologie/resultats_qwen72b_foc_nothink.csv"

old60 = set()
with open(OLD60, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        fn = row.get("File", row.get("fichier","")).strip()
        if fn: old60.add(fn)

gold = {}
with open(GOLD, encoding="utf-8") as f:
    reader = csv.reader(f, delimiter=";")
    next(reader)
    for row in reader:
        if not row or not row[0].strip().endswith(".txt"): continue
        fn = row[0].strip()
        if fn not in old60 or fn in gold: continue
        def col(i): return row[i].strip() if i < len(row) else ""
        gold[fn] = {"FOCALISATION": col(6), "FOC_alt": col(7)}

def is_correct(pred, main, alt=""):
    if not pred: return False
    p = pred.strip().upper()
    if p == main.strip().upper(): return True
    if alt and p == alt.strip().upper(): return True
    return False

def chunk_novel(fn, n=9, max_lines=150):
    path = os.path.join(CORPUS, fn)
    if not os.path.exists(path): return []
    lines = open(path, encoding="utf-8").readlines()
    total = len(lines)
    size = max(total // n, 1)
    chunks = []
    for i in range(n):
        start = i * size
        end = start + size if i < n-1 else total
        sl = lines[start:end]
        if len(sl) > max_lines:
            mid = len(sl)//2; half = max_lines//2
            sl = sl[max(0,mid-half):mid+half]
        pos = "DEBUT" if i==0 else "FIN" if i==n-1 else f"MILIEU-{i}"
        chunks.append((pos, "".join(sl)[:1500]))
    return chunks

PROMPT = """Tu es expert en narratologie francaise (Genette).
FOCALISATION:
- FOC_INT: UN SEUL personnage focal. Discours indirect libre dominant.
- FOC_ZERO: Omniscient, entre dans TOUTES les consciences librement.
- FOC_EXT: Zero acces aux pensees. Style camera.
- FOC_VAR: Changement de focalisateur entre chapitres/sections.
Extraits du roman:
{excerpts}
Reponds UNIQUEMENT avec ce JSON: """ + '{"FOCALISATION": "FOC_INT|FOC_ZERO|FOC_EXT|FOC_VAR"}'

VALID = ["FOC_INT","FOC_ZERO","FOC_EXT","FOC_VAR"]

def classify(fn, think=True):
    chunks = chunk_novel(fn)
    if not chunks: return None
    excerpts = "\n\n".join(f"[{pos}]\n{text}" for pos, text in chunks)
    suffix = "" if think else " /no_think"
    num_pred = 5000 if think else 100
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "messages": [{"role": "user", "content": PROMPT.format(excerpts=excerpts) + suffix}],
            "stream": False,
            "options": {"temperature": 0, "num_predict": num_pred, "num_ctx": 8192},
        }, timeout=300)
        resp.raise_for_status()
        content = resp.json()["message"]["content"].strip()
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        pat = re.compile(r'"FOCALISATION":\s*"(FOC_\w+)"')
        m = pat.search(content)
        if m and m.group(1) in VALID:
            return m.group(1)
        for code in VALID:
            if code in content:
                return code
        return None
    except Exception as e:
        print(f"    Error: {e}"); return None

def run(think, output):
    label = "WITH thinking" if think else "WITHOUT thinking"
    print(f"\n{'='*60}")
    print(f"  qwen72b-limited — FOCALISATION — {label}")
    print(f"{'='*60}\n")
    corpus_files = set(os.listdir(CORPUS))
    novels = [(fn, g) for fn, g in gold.items() if fn in corpus_files]
    results = []
    correct = total = 0
    for i, (fn, g) in enumerate(novels, 1):
        pred = classify(fn, think=think)
        if pred is None: pred = "FOC_INT"
        ok = is_correct(pred, g["FOCALISATION"], g["FOC_alt"])
        correct += ok; total += 1
        mark = "OK" if ok else "XX"
        print(f"  [{i:>2}/60] {fn[:42]:<42} -> {pred} {mark} (gold:{g['FOCALISATION']})")
        results.append({"File": fn, "FOCALISATION": pred,
                        "GOLD_FOC": g["FOCALISATION"], "ALT_FOC": g["FOC_alt"],
                        "correct": int(ok)})
    print(f"\n  RESULT: {correct}/{total} ({correct/total*100:.1f}%)")
    with open(output, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader(); w.writerows(results)
    print(f"  Saved: {output}")
    return correct/total*100

print("Gold set:", len(gold), "novels")

# Run WITH thinking first
acc_think = run(think=True, output=OUTPUT_T)

# Run WITHOUT thinking second
acc_nothink = run(think=False, output=OUTPUT_N)

print(f"\n{'='*60}")
print(f"  FINAL COMPARISON")
print(f"  With thinking:    {acc_think:.1f}%")
print(f"  Without thinking: {acc_nothink:.1f}%")
print(f"  Previous best:    65.0% (local hybrid)")
print(f"{'='*60}")
