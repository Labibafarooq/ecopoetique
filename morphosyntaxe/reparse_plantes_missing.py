"""
Re-parse the plantes rows missing from dépendants_PLANTES.csv (entire
bestsellers subset + a gap in corpus_principal — dépendants_PLANTES.csv
predates Task 1 and was never updated for these rows).

Same head/head-of-head logic as scripts/get_token_dependencies.py +
morphosyntaxe/extract_humains.py, model fr_core_news_lg (matches what's
actually installed/used elsewhere in this project), so results are
consistent with the existing dépendants_PLANTES.csv and with the animaux
coverage-gap fix done 2026-07-08.

Input:  /tmp/.../plantes_missing_rows.tsv (fichier, token_lexique, lemme, truncated_sentence)
Output: morphosyntaxe/dépendants_PLANTES_missing_rows.csv
"""
import csv, os, sys, time
import spacy

csv.field_size_limit(10**7)

INPUT_FILE  = sys.argv[1] if len(sys.argv) > 1 else \
    "/tmp/claude-1013/-home-lfarooq/0c40159e-c731-4cf6-a5e9-6c51ee541de1/scratchpad/plantes_missing_rows.tsv"
OUTPUT_FILE = os.path.expanduser("~/ecopoetique/morphosyntaxe/dépendants_PLANTES_missing_rows.csv")

nlp = spacy.load("fr_core_news_lg")

def get_dependencies(token_text, sentence):
    doc = nlp(sentence)
    match_text = token_text
    if " " in match_text or "-" in match_text:
        match_text = nlp(match_text)[0].text

    for token in doc:
        if token.text == match_text:
            head = (token.head.text, token.dep_)
            dependents = [(child.text, child.dep_) for child in token.children]
            head_of_head = (token.head.head.text, token.head.dep_) if token.head != token else ("", "")
            return head, dependents, head_of_head
    return None, None, None

def main():
    with open(INPUT_FILE, encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    print(f"Rows to re-parse: {len(rows):,}")

    fieldnames = ["fichier", "token_lexique", "truncated_sentence", "lemme", "tête", "dépendants", "tête_de_tête"]
    out_f = open(OUTPUT_FILE, "w", newline="", encoding="utf-8")
    writer = csv.DictWriter(out_f, fieldnames=fieldnames, delimiter="\t")
    writer.writeheader()

    matched = 0
    start = time.time()
    for i, r in enumerate(rows, 1):
        head, deps, head_of_head = get_dependencies(r["token_lexique"], r["truncated_sentence"])
        if head is not None:
            matched += 1
        writer.writerow({
            "fichier": r["fichier"],
            "token_lexique": r["token_lexique"],
            "truncated_sentence": r["truncated_sentence"],
            "lemme": r["lemme"],
            "tête": str(head) if head is not None else "",
            "dépendants": str(deps) if deps is not None else "",
            "tête_de_tête": str(head_of_head) if head_of_head is not None else "",
        })
        if i % 500 == 0 or i == len(rows):
            out_f.flush()
            elapsed = time.time() - start
            eta = (elapsed / i) * (len(rows) - i)
            print(f"  [{i:,}/{len(rows):,}] matched={matched:,} ({matched/i*100:.1f}%) "
                  f"elapsed={elapsed/60:.1f}min ETA={eta/60:.1f}min", flush=True)

    out_f.close()
    print(f"\nDone. {matched:,}/{len(rows):,} matched ({matched/len(rows)*100:.1f}%)")
    print(f"Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
