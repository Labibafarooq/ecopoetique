"""
Builds the Task 2 input file from OUR OWN Task 1 (qwen3) référentiel/figuré
results — NOT from Joanna's old ChatGPT-based métaphores_identifiées_gpt.csv.

Per Riccardo (2026-06-25 meeting): "I am not sure if I should use this animal
cases of Joanna because it was run on ChatGPT results... No, you should use
yours." The old file (23,327 rows, all pre-labeled figuré) only overlaps
about half with our own Task 1 animaux figuré set (38,260 rows) — wrong input,
found 2026-07-09.

Merges task1_animaux_labels.csv (complete, 2026-07-05) + task1_plantes_labels.csv
(still running as of this writing — this script picks up whatever is done so
far each time it's re-run; re-run again once Task 1 plantes finishes for the
final full-corpus file before scaling Task 2).

Output: figuratifs_task1_own.csv (matches the column shape run_task2_subcategories.py
expects: fichier, token_lexique, contexte, categorie, lemme, decision)
"""
import csv
import os

ANIMAUX_FILE = os.path.expanduser("~/ecopoetique/resultats/task1_animaux_labels.csv")
PLANTES_FILE = os.path.expanduser("~/ecopoetique/resultats/task1_plantes_labels.csv")
OUTPUT_FILE  = os.path.expanduser("~/ecopoetique/métaphore/figuratifs_task1_own.csv")

FIELDS = ["fichier", "token_lexique", "contexte", "categorie", "lemme", "decision"]

def load_figuratifs(path):
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    return [r for r in rows if r.get("task1_label", "").strip() == "figuré"]

def main():
    animaux_fig = load_figuratifs(ANIMAUX_FILE)
    plantes_fig = load_figuratifs(PLANTES_FILE)
    print(f"animaux figuré rows : {len(animaux_fig):,} (Task 1 animaux complete)")
    print(f"plantes figuré rows : {len(plantes_fig):,} (Task 1 plantes still running — partial)")

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for r in animaux_fig + plantes_fig:
            writer.writerow({
                "fichier": r["fichier"], "token_lexique": r["token_lexique"],
                "contexte": r["contexte"], "categorie": r["categorie"],
                "lemme": r["lemme"], "decision": "figuré",
            })

    print(f"\nTotal written: {len(animaux_fig) + len(plantes_fig):,}")
    print(f"Saved to: {OUTPUT_FILE}")
    print("\nNOTE: plantes portion is PARTIAL. Re-run this script once Task 1")
    print("plantes finishes to get the complete full-corpus file before scaling Task 2.")

if __name__ == "__main__":
    main()
