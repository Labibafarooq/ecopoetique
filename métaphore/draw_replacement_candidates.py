"""
Draws a fresh batch of candidate figurative rows to replace the 16
confirmed-misclassified + 19 genuinely-ambiguous rows found on full manual
review of gold_task2_task45_v2.csv (need 15 more animaux + 20 more plantes).

Excludes every row already drawn into gold_task2_task45_v2.csv (all 200,
not just the bad ones) so there's no chance of re-drawing a duplicate.
Draws a buffer (2x needed) since some fraction of any fresh random draw
will also turn out to be ambiguous/misclassified on manual review.
"""
import csv
import random
import os

random.seed(43)  # different seed from the v2 draw (42), no overlap risk anyway due to exclusion

BASE = os.path.dirname(os.path.abspath(__file__))
ANIMAL_SRC = os.path.join(BASE, "..", "resultats", "task1_animaux_labels.csv")
PLANT_SRC = os.path.join(BASE, "..", "resultats", "task1_plantes_labels.csv")
EXISTING = os.path.join(BASE, "gold_task2_task45_v2.csv")

NEEDED_ANIMAUX = 15
NEEDED_PLANTES = 20
BUFFER_MULT = 3  # draw 3x what's needed, to survive manual filtering


def load_existing_keys():
    keys = set()
    with open(EXISTING, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            keys.add((row["fichier"], row["token_lexique"], row["contexte"]))
    return keys


def load_figurative(path, source_label, exclude_keys):
    out = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row.get("task1_label", "").strip().lower() != "figuré":
                continue
            key = (row["fichier"].strip(), row["token_lexique"].strip(), row["contexte"].strip())
            if key in exclude_keys:
                continue
            out.append({
                "fichier": row["fichier"].strip(),
                "token_lexique": row["token_lexique"].strip(),
                "contexte": row["contexte"].strip(),
                "lemme": row.get("lemme", "").strip(),
                "source": source_label,
            })
    return out


def main():
    exclude_keys = load_existing_keys()
    print(f"Excluding {len(exclude_keys)} already-drawn rows")

    animals_fig = load_figurative(ANIMAL_SRC, "animaux", exclude_keys)
    plants_fig = load_figurative(PLANT_SRC, "plantes", exclude_keys)

    n_animals = min(NEEDED_ANIMAUX * BUFFER_MULT, len(animals_fig))
    n_plants = min(NEEDED_PLANTES * BUFFER_MULT, len(plants_fig))
    sample_animals = random.sample(animals_fig, n_animals)
    sample_plants = random.sample(plants_fig, n_plants)

    print(f"Drew {len(sample_animals)} candidate animaux rows (need {NEEDED_ANIMAUX} good ones)")
    print(f"Drew {len(sample_plants)} candidate plantes rows (need {NEEDED_PLANTES} good ones)")

    all_items = sample_animals + sample_plants
    output_path = os.path.join(BASE, "gold_replacement_candidates.csv")
    fieldnames = ["id", "fichier", "token_lexique", "contexte", "lemme", "source"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for i, item in enumerate(all_items, 1):
            writer.writerow({"id": i, **item})

    print(f"\nOutput: {output_path}")


if __name__ == "__main__":
    main()
