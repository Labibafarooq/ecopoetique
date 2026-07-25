"""
Create 200-item gold set for Task 2 (subcategory) + Task 4.5 (comparé category).
- 100 random figurative ANIMAL cases  → from RESULTAT_annotation_gpt.csv (Joanna/GPT)
- 100 random figurative PLANT cases   → from plantes/annotations_gpt_partie_*.csv (Joanna/GPT)

NOTE: Source is Joanna's GPT annotations (~47% figurative accuracy for Task 1).
Use this as a provisional gold set. Replace with Task 1 verified results after ~July 7.

Output: gold_task2_task45.csv  — send to Riccardo to annotate two columns:

  subcategorie_metaphore  (Task 2 — structure syntaxique de la figure) — 16 catégories:
    COMME_SN        comparaison similative       "rusé comme un renard"
    COMME_P         comparaison phrastique        "les branches craquaient comme les os..."
    COMME_SI        comparaison hypothétique      "comme si une forêt retenait son souffle"
    COMP_DEG        comparaison quantitative      "plus lent qu'une tortue"
    DE_PARANGON     analogie nominale en de       "mémoire d'éléphant"
    DE_MATIERE      métaphore matérialisante      "volonté de granit"
    DE_UNIVERS      analogie d'univers            "océan de verdure"
    DE_QUANTIF      quantification métaphorique   "une forêt de pylônes"
    DE_PROP         analogie proportionnelle      "vautours de la finance"
    META_ATTR       métaphore attributive         "cet homme est un loup"
    META_APP        métaphore appositionnelle     "la montagne sentinelle"
    META_JUXT       binôme nominal                "arbre-parapluie"
    META_VERB       métaphore verbale             "la forêt avalait la lumière"
    MOD_ANALOG      analogie modalisée            "on aurait dit une meute"
    ANALOG_COMPLEX  analogie complexe             "à côté de cette tempête..."
    META_FILEE      métaphore filée               réseau métaphorique continu

  categorie_compare  (Task 4.5 — catégorie du comparé, ce à quoi l'animal/plante est comparé):
    CH    Corps humain / personne / attitude humaine
    P     état Psychologique / affect / émotion
    NH    être Non-Humain (autre animal ou créature)
    O     Objet / artefact
    E     Environnement / élément naturel
    A     concept Abstrait
"""

import csv
import random
import os

random.seed(42)

BASE = os.path.dirname(os.path.abspath(__file__))
CORPUS_PRINCIPAL = os.path.join(BASE, "..", "resultats", "corpus_principal")

# ── Load figurative ANIMALS ───────────────────────────────────────────────────
animal_src = os.path.join(BASE, "..", "métaphore", "RESULTAT_annotation_gpt.csv")
# Try relative path from this script's location
if not os.path.exists(animal_src):
    animal_src = os.path.join(BASE, "RESULTAT_annotation_gpt.csv")

animals_fig = []
with open(animal_src, encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for row in reader:
        if row.get("label", "").strip().lower() == "figuré":
            animals_fig.append({
                "fichier":       row["fichier"].strip(),
                "token_lexique": row["token_lexique"].strip(),
                "contexte":      row["truncated_sentence"].strip(),
                "lemme":         row.get("lemme", "").strip(),
                "source":        "animaux",
            })

print(f"Figurative animals available: {len(animals_fig)}")
sample_animals = random.sample(animals_fig, min(100, len(animals_fig)))
print(f"Sampled: {len(sample_animals)}")

# ── Load figurative PLANTS ────────────────────────────────────────────────────
plants_fig = []
for fn in ["plantes/annotations_gpt_partie_1.csv", "plantes/annotations_gpt_partie_2.csv"]:
    path = os.path.join(BASE, fn)
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            label = row.get("label", "").strip().lower()
            if label == "figuré":
                # context column differs between the two files
                ctx = row.get("truncated_sentence", row.get("contexte", "")).strip()
                plants_fig.append({
                    "fichier":       row.get("fichier", "").strip(),
                    "token_lexique": row["token_lexique"].strip(),
                    "contexte":      ctx,
                    "lemme":         row.get("lemme", "").strip(),
                    "source":        "plantes",
                })

print(f"Figurative plants available: {len(plants_fig)}")
sample_plants = random.sample(plants_fig, min(100, len(plants_fig)))
print(f"Sampled: {len(sample_plants)}")

# ── Combine and shuffle ───────────────────────────────────────────────────────
all_items = sample_animals + sample_plants
random.shuffle(all_items)

# ── Write output CSV ──────────────────────────────────────────────────────────
output_path = os.path.join(BASE, "gold_task2_task45.csv")
fieldnames = [
    "id",
    "fichier",
    "token_lexique",
    "contexte",
    "lemme",
    "source",
    "subcategorie_metaphore",   # ← Riccardo annotates: COMME_SN|COMME_P|COMME_SI|COMP_DEG|DE_PARANGON|DE_MATIERE|DE_UNIVERS|DE_QUANTIF|DE_PROP|META_ATTR|META_APP|META_JUXT|META_VERB|MOD_ANALOG|ANALOG_COMPLEX|META_FILEE
    "categorie_compare",        # ← Riccardo annotates: CH|P|NH|O|E|A
    "notes",
]

with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
    writer.writeheader()
    for i, item in enumerate(all_items, 1):
        writer.writerow({
            "id":                    i,
            "fichier":               item["fichier"],
            "token_lexique":         item["token_lexique"],
            "contexte":              item["contexte"],
            "lemme":                 item["lemme"],
            "source":                item["source"],
            "subcategorie_metaphore": "",
            "categorie_compare":      "",
            "notes":                  "",
        })

print(f"\nOutput: {output_path}")
print(f"Total items: {len(all_items)} ({len(sample_animals)} animals + {len(sample_plants)} plants)")
print(f"\nColumn guide for Riccardo:")
print(f"  subcategorie_metaphore (16 categories from schema_analogies_vivant_complet):")
print(f"    COMME_SN / COMME_P / COMME_SI / COMP_DEG / DE_PARANGON / DE_MATIERE /")
print(f"    DE_UNIVERS / DE_QUANTIF / DE_PROP / META_ATTR / META_APP / META_JUXT /")
print(f"    META_VERB / MOD_ANALOG / ANALOG_COMPLEX / META_FILEE")
print(f"  categorie_compare (6 categories):")
print(f"    CH (corps humain/personne) | P (état psychologique/affect) | NH (non-humain/autre animal) |")
print(f"    O (objet/artefact) | E (environnement/naturel) | A (concept abstrait)")
