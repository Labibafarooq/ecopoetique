"""
Create a NEW 200-item gold set for Task 2 (subcategorie_metaphore) + Task 4.5
(categorie_compare), replacing gold_task2_task45_RB.csv.

Why a new one: the old gold set's figuré/référentiel filter was applied
against Joanna's old GPT annotations (~47% Task 1 accuracy), not this
project's own verified Task 1 (qwen3) results - meaning some rows the old
set called "figuré" are, per our own more accurate labels, actually
référentiel (the "72 X-marked" rows flagged as a problem). This version
draws strictly from our own corrected, audited Task 1 production output:
  - resultats/task1_animaux_labels.csv (127,935 rows, task1_label column)
  - resultats/task1_plantes_labels.csv (69,468 rows, task1_label column)
filtered to task1_label == "figuré" only, per the original spec (Task 2
and Task 4.5 both only operate on figurative mentions).

100 random figurative ANIMAL rows + 100 random figurative PLANT rows,
shuffled together, written to one CSV with two blank answer columns:
  subcategorie_metaphore  <- for Riccardo/team to fill in (Task 2)
  categorie_compare       <- for Riccardo/team to fill in (Task 4.5)

Also runs a scripted sanity check (not a substitute for a human reading
every row, but catches gross errors) flagging any sampled row whose
context doesn't contain an obvious figurative marker, for manual review
before this file is finalized/sent anywhere.
"""
import csv
import random
import os

random.seed(42)

BASE = os.path.dirname(os.path.abspath(__file__))
ANIMAL_SRC = os.path.join(BASE, "..", "resultats", "task1_animaux_labels.csv")
PLANT_SRC = os.path.join(BASE, "..", "resultats", "task1_plantes_labels.csv")

FIGURATIVE_MARKERS = [
    "comme ", "comme,", "comme.", "tel ", "telle ", "tels ", "telles ",
    "pareil à", "pareille à", "on aurait dit", "semblait un", "semblait une",
    "tel un", "tel une",
]


def load_figurative(path, source_label):
    out = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row.get("task1_label", "").strip().lower() == "figuré":
                out.append({
                    "fichier": row["fichier"].strip(),
                    "token_lexique": row["token_lexique"].strip(),
                    "contexte": row["contexte"].strip(),
                    "lemme": row.get("lemme", "").strip(),
                    "source": source_label,
                })
    return out


def has_obvious_marker(contexte):
    low = contexte.lower()
    return any(m in low for m in FIGURATIVE_MARKERS)


def main():
    animals_fig = load_figurative(ANIMAL_SRC, "animaux")
    print(f"Figurative animals available (our own Task 1, audited): {len(animals_fig)}")
    sample_animals = random.sample(animals_fig, min(100, len(animals_fig)))

    plants_fig = load_figurative(PLANT_SRC, "plantes")
    print(f"Figurative plants available (our own Task 1, audited): {len(plants_fig)}")
    sample_plants = random.sample(plants_fig, min(100, len(plants_fig)))

    all_items = sample_animals + sample_plants
    random.shuffle(all_items)

    no_marker = [item for item in all_items if not has_obvious_marker(item["contexte"])]
    print(f"\nSampled {len(all_items)} total ({len(sample_animals)} animaux + {len(sample_plants)} plantes)")
    print(f"Rows with NO obvious figurative marker (comme/tel/pareil à/...) - flagged for manual review: {len(no_marker)}")

    output_path = os.path.join(BASE, "gold_task2_task45_v2.csv")
    fieldnames = [
        "id", "fichier", "token_lexique", "contexte", "lemme", "source",
        "subcategorie_metaphore", "categorie_compare", "notes",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for i, item in enumerate(all_items, 1):
            writer.writerow({
                "id": i,
                "fichier": item["fichier"],
                "token_lexique": item["token_lexique"],
                "contexte": item["contexte"],
                "lemme": item["lemme"],
                "source": item["source"],
                "subcategorie_metaphore": "",
                "categorie_compare": "",
                "notes": "NO_OBVIOUS_MARKER" if item in no_marker else "",
            })

    print(f"\nOutput: {output_path}")

    # write the no-marker rows separately too, for quick manual review
    review_path = os.path.join(BASE, "gold_task2_task45_v2_NEEDS_REVIEW.csv")
    with open(review_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["fichier", "token_lexique", "contexte", "source"], delimiter="\t")
        writer.writeheader()
        for item in no_marker:
            writer.writerow({k: item[k] for k in ["fichier", "token_lexique", "contexte", "source"]})
    print(f"Rows needing manual figurative-ness review: {review_path}")


if __name__ == "__main__":
    main()
