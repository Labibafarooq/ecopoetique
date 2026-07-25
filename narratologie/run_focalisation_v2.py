"""
FOCALISATION v2 — Three techniques combined:
1. Self-consistency: 5 samples at temperature 0.3, majority vote
2. No thinking mode: model=qwen3:30b/no_think
3. Genette definitions verbatim + quotation-mark rule from Hicke et al.
4. Extra training examples from critere_narration_focalisation.csv (NOT gold set)

60 novels only, compared against gold set.
"""
import os, csv, json, re, requests, time
from collections import Counter

OLLAMA_URL   = "http://localhost:11435/api/chat"
MODEL        = "qwen3:30b"  # we'll set think=false in options
GOLD         = "/home/lfarooq/ecopoetique/narratologie/GOLD_narratologie.csv"
OLD60        = "/home/lfarooq/ecopoetique/narratologie/resultats_hybrid.csv"
CORPUS       = os.path.expanduser("~/ecopoetique/CORPUS_TOTAL")
CRITERE_FILE = os.path.expanduser("~/ecopoetique/narratologie/critere_narration_focalisation.csv")
OUTPUT       = "/home/lfarooq/ecopoetique/narratologie/resultats_focalisation_v2.csv"

N_SAMPLES    = 5      # self-consistency samples
TEMPERATURE  = 0.3   # non-zero for diversity
N_CHUNKS     = 9
MAX_LINES    = 150

# Map critere labels to our codes
CRITERE_MAP = {
    "Interne": "FOC_INT",
    "Zéro": "FOC_ZERO",
    "Externe": "FOC_EXT",
    "Variable": "FOC_VAR",
}

PROMPT = """Tu es expert en narratologie française. Analyse la focalisation de ce roman selon Genette.

DÉFINITIONS PRÉCISES (Genette, Figures III):
- FOC_INT (focalisation interne): Le récit est filtré par la conscience d'UN SEUL personnage. On n'accède qu'à ce qu'il perçoit, pense et ressent. Les autres personnages sont vus de l'extérieur, à travers ses yeux. Signal: discours indirect libre, "elle pensait que...", "il sentait...", mais toujours le même "il/elle".
- FOC_ZERO (focalisation zéro = omnisciente): Le narrateur SAIT TOUT et entre librement dans les pensées de N'IMPORTE QUEL personnage. "Pierre pensait X... Marie pensait Y... L'autre savait que Z..." Plusieurs consciences accessibles sans restriction.
- FOC_EXT (focalisation externe): Narration purement behaviouriste. AUCUN accès aux pensées ou émotions. Le narrateur voit les personnages de l'extérieur comme une caméra. Les dialogues entre guillemets sont un signal fort de FOC_EXT.
- FOC_VAR (focalisation variable): La focalisation CHANGE de personnage d'un chapitre ou d'une section à l'autre. Chapitre 1 = Pierre, Chapitre 2 = Marie, etc.

RÈGLES CLÉS (Hicke et al. 2024):
1. Les discours directs entre guillemets comptent comme signal de FOC_EXT
2. FOC_INT ≠ FOC_ZERO: si UN seul personnage domine = INT; si narrateur entre librement dans TOUTES les têtes = ZERO
3. FOC_VAR nécessite un CHANGEMENT EXPLICITE de focalisateur entre sections, pas juste plusieurs personnages présents

{few_shot}

EXTRAITS DU ROMAN (début, milieu, fin):
{excerpts}

Réponds avec UN SEUL code parmi: FOC_INT, FOC_ZERO, FOC_EXT, FOC_VAR
Format: {{"FOCALISATION": "FOC_XXX"}}"""

# Build few-shot examples from critere file (NOT from gold set)
def build_few_shot(gold_fns, critere_file, corpus_dir, n_per_class=2):
    """Load examples from critere file, excluding gold set novels."""
    critere = {}
    with open(critere_file, encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            fn = row.get('File','').strip()
            foc = row.get('Focalisation','').strip()
            if fn and foc in CRITERE_MAP and fn not in gold_fns:
                code = CRITERE_MAP[foc]
                if code not in critere:
                    critere[code] = []
                critere[code].append(fn)

    few_shot_parts = []
    corpus_files = set(os.listdir(corpus_dir))
    
    for code, fns in critere.items():
        count = 0
        for fn in fns:
            if count >= n_per_class: break
            if fn not in corpus_files: continue
            path = os.path.join(corpus_dir, fn)
            lines = open(path, encoding='utf-8').readlines()
            if len(lines) < 50: continue
            # Get opening 30 lines
            excerpt = "".join(lines[:30])[:800]
            few_shot_parts.append(
                f"EXEMPLE ({code}):\n{excerpt}\n→ {code}"
            )
            count += 1

    return "\n\n".join(few_shot_parts) if few_shot_parts else ""

def chunk_novel(fn, n=N_CHUNKS):
    path = os.path.join(CORPUS, fn)
    if not os.path.exists(path): return None
    lines = open(path, encoding='utf-8').readlines()
    total = len(lines)
    size = max(total // n, 1)
    excerpts = []
    for i in range(n):
        start = i * size
        end = start + size if i < n-1 else total
        sl = lines[start:end]
        if len(sl) > MAX_LINES:
            mid = len(sl)//2; half = MAX_LINES//2
            sl = sl[max(0,mid-half):mid+half]
        excerpts.append("".join(sl)[:600])
    # Use beginning, middle, end for the prompt
    return f"[DÉBUT]\n{excerpts[0]}\n\n[MILIEU]\n{excerpts[4]}\n\n[FIN]\n{excerpts[-1]}"

def call_ollama(prompt, temperature=0.0):
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 100,  # small — no thinking, just answer
                "num_ctx": 8192,
            },
            "think": False,  # disable thinking mode explicitly
        }, timeout=120)
        resp.raise_for_status()
        content = resp.json()["message"]["content"].strip()
        # Strip any thinking that slipped through
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        m = re.search(r'"FOCALISATION":\s*"(FOC_\w+)"', content)
        if m and m.group(1) in ["FOC_INT","FOC_ZERO","FOC_EXT","FOC_VAR"]:
            return m.group(1)
        for code in ["FOC_INT","FOC_ZERO","FOC_EXT","FOC_VAR"]:
            if code in content:
                return code
        return None
    except Exception as e:
        return None

def is_correct(pred, main, alt=""):
    if not pred: return False
    p = pred.strip().upper()
    if p == main.strip().upper(): return True
    if alt and p == alt.strip().upper(): return True
    return False

def main():
    # Load 60-novel set
    old60 = set()
    with open(OLD60, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            fn = row.get('File', row.get('fichier','')).strip()
            if fn: old60.add(fn)

    # Load gold
    gold = {}
    with open(GOLD, encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        next(reader)
        for row in reader:
            if not row or not row[0].strip().endswith('.txt'): continue
            fn = row[0].strip()
            if fn not in old60 or fn in gold: continue
            def col(i): return row[i].strip() if i < len(row) else ""
            gold[fn] = {"FOCALISATION": col(6), "FOC_alt": col(7)}

    print(f"Gold set: {len(gold)} novels")

    # Build few-shot from critere file
    print("Building few-shot examples from critere file...")
    few_shot = build_few_shot(set(gold.keys()), CRITERE_FILE, CORPUS, n_per_class=2)
    n_examples = few_shot.count("EXEMPLE")
    print(f"Few-shot examples loaded: {n_examples}")

    corpus_files = set(os.listdir(CORPUS))
    novels = [(fn, g) for fn, g in gold.items() if fn in corpus_files]
    print(f"\nRunning self-consistency (n={N_SAMPLES}) on {len(novels)} novels")
    print(f"Techniques: no-think + Genette definitions + few-shot + majority vote\n")

    results = []
    correct = total = 0

    for i, (fn, g) in enumerate(novels, 1):
        excerpts = chunk_novel(fn)
        if not excerpts:
            print(f"  [{i:>2}/60] SKIP {fn}")
            continue

        prompt = PROMPT.format(few_shot=few_shot, excerpts=excerpts)

        # Self-consistency: sample N_SAMPLES times
        votes = []
        for s in range(N_SAMPLES):
            temp = 0.0 if s == 0 else TEMPERATURE
            pred = call_ollama(prompt, temperature=temp)
            if pred: votes.append(pred)

        # Majority vote
        if votes:
            final = Counter(votes).most_common(1)[0][0]
        else:
            final = "FOC_INT"

        ok = is_correct(final, g["FOCALISATION"], g["FOC_alt"])
        correct += ok; total += 1
        mark = "✓" if ok else "✗"
        vote_str = ", ".join(votes) if votes else "none"
        print(f"  [{i:>2}/60] {fn[:40]:<40} → {final} {mark} (gold:{g['FOCALISATION']}) votes:[{vote_str}]")

        results.append({
            "File": fn, "FOCALISATION": final,
            "GOLD_FOC": g["FOCALISATION"], "ALT_FOC": g["FOC_alt"],
            "correct": int(ok), "votes": vote_str,
        })

    print(f"\n{'='*65}")
    print(f"  FOCALISATION v2 — no-think + Genette + few-shot + self-consistency")
    print(f"  {correct}/{total} ({correct/total*100:.1f}%)")
    print(f"  vs local hybrid v4: 65.0%")
    print(f"  vs gpt4o_mini: 75.0%")
    print(f"{'='*65}")

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader(); w.writerows(results)
    print(f"  Saved to: {OUTPUT}")

if __name__ == "__main__":
    main()
