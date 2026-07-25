"""
Assembles the FINAL, fully manually-verified 200-row gold set for Task 2
+ Task 4.5, built from:
  - The 165 rows from gold_task2_task45_v2.csv confirmed genuinely
    figurative on a full manual read of all 200 rows' real sentence
    context (16 were confirmed misclassified/homograph collisions, 19
    were genuinely ambiguous even after full-context reading - both
    sets excluded here).
  - 15 replacement animaux + 20 replacement plantes rows, drawn fresh
    from gold_replacement_candidates.csv and confirmed genuinely
    figurative the same way (manual full-context read, not a heuristic).

Every single row in the output has been read in full context and
confirmed to contain a genuine figurative use (explicit comparison,
idiom, metaphor, personification, symbolic/biblical reference, or
representation) - not assumed correct from Task 1's label alone.
"""
import csv
import os

BASE = os.path.dirname(os.path.abspath(__file__))
V2_FILE = os.path.join(BASE, "gold_task2_task45_v2.csv")
CANDIDATES_FILE = os.path.join(BASE, "gold_replacement_candidates.csv")
OUTPUT_FILE = os.path.join(BASE, "gold_task2_task45_FINAL.csv")

# ids confirmed misclassified or genuinely ambiguous on full manual review
# of gold_task2_task45_v2.csv - excluded from the final set
EXCLUDE_V2_IDS = {
    # confirmed misclassified (16)
    4, 5, 17, 26, 28, 44, 79, 85, 90, 102, 134, 143, 151, 156, 178, 190,
    # genuinely ambiguous (19)
    15, 38, 46, 47, 48, 62, 65, 69, 101, 103, 108, 112, 120, 122, 140, 141, 152, 154, 173,
}

# replacement candidate ids confirmed genuinely figurative on manual review
REPLACEMENT_ANIMAUX_IDS = [1, 2, 3, 4, 7, 8, 9, 11, 12, 14, 16, 17, 18, 19, 21]
REPLACEMENT_PLANTES_IDS = [46, 47, 48, 50, 52, 53, 54, 55, 56, 58, 60, 61, 62, 63, 64, 65, 67, 68, 69, 70]


def main():
    with open(V2_FILE, encoding="utf-8") as f:
        v2_rows = list(csv.DictReader(f, delimiter="\t"))
    kept_v2 = [r for r in v2_rows if int(r["id"]) not in EXCLUDE_V2_IDS]
    print(f"Kept from v2 (confirmed figurative): {len(kept_v2)}")

    with open(CANDIDATES_FILE, encoding="utf-8") as f:
        cand_rows = {int(r["id"]): r for r in csv.DictReader(f, delimiter="\t")}

    replacement_rows = []
    for cid in REPLACEMENT_ANIMAUX_IDS + REPLACEMENT_PLANTES_IDS:
        replacement_rows.append(cand_rows[cid])
    print(f"Replacement rows added: {len(replacement_rows)}")

    all_rows = kept_v2 + replacement_rows
    print(f"Total final rows: {len(all_rows)}")

    from collections import Counter
    src_counts = Counter(r["source"] for r in all_rows)
    print(f"Source breakdown: {dict(src_counts)}")

    fieldnames = ["id", "fichier", "token_lexique", "contexte", "lemme", "source",
                  "subcategorie_metaphore", "categorie_compare", "notes"]
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for i, row in enumerate(all_rows, 1):
            writer.writerow({
                "id": i,
                "fichier": row["fichier"],
                "token_lexique": row["token_lexique"],
                "contexte": row["contexte"],
                "lemme": row.get("lemme", ""),
                "source": row["source"],
                "subcategorie_metaphore": "",
                "categorie_compare": "",
                "notes": "",
            })

    print(f"\nOutput: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
