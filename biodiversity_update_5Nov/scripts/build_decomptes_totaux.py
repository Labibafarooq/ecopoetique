"""
Reconstruit "decomptes_totaux" (meme structure que la version deja envoyee a
Riccardo, resultats/corpus_principal/decomptes_totaux.csv) pour les 3 corpus,
a partir des donnees d'entites AJOUR (ENTITES_TOTAL.csv / BESTSELLERS_ENTITES_
MERGED.csv, incluant le correctif formes-derivees-animaux d'octobre 2026).

Demande de Riccardo (email 2026-11-03) : "a file ... giving for each work the
number of distinct animal, plant, and Loterre lemmas, as well as the total
number of occurrences for each category" -- sa propre version deja distingue
5 categories (animal/plante/champignon/loterre/taxon), donc on reproduit
exactement cette structure plutot que de la reduire a 3.

Semantique verifiee empiriquement sur le fichier deja envoye (ligne Jenni) :
  - lemmes_X    = ABONDANCE  (nombre total d'occurrences de la categorie X)
  - diversite_X = RICHESSE   (nombre de lemmes DISTINCTS de la categorie X)
  - TOTAL_LEMME / TOTAL_DIVERSITE = sommes des lemmes_X / diversite_X
  - proportion_X_%% = lemmes_X / nb_tokens * 1000 (confirme par recalcul exact)

nb_tokens/nb_formes/nb_lemmes/guiraud_index/herdan_index/dugast_index NE sont
PAS recalcules : deja presents et verifies identiques (0 difference sur 925
romans) entre l'ancien decomptes_totaux.csv et les corpus_*.csv actuels --
ce sont des stats lexicales generales, independantes du lexique ecologique,
donc jamais perimees. Reutilises tels quels depuis corpus_{DigEco,Bestsellers,
PRIX_ECOLOGIE}.csv.

Key : identifiant stable deja attribue a chaque roman dans les anciens
fichiers decomptes_totaux (corpus_principal couvre DigEco + PRIX_ECOLOGIE en
entier ; decomptes_totaux_bestsellers couvre 88/124 Bestsellers, les 36
manquants -- meme recouvrement DigEco/Bestsellers deja documente pour
l'extraction d'entites -- recuperent leur Key depuis corpus_principal).

Usage:
    python3 build_decomptes_totaux.py
"""
import csv
import os

csv.field_size_limit(10_000_000)

CATEGORIES = ["animal", "plante", "champignon", "loterre", "taxon"]
COLUMNS = [
    "Key", "File", "Year", "Author", "Sexe auteur", "Année naissance",
    "Nationalité", "Title", "Publisher", "Distinction",
    "nb_tokens", "nb_formes", "nb_lemmes",
    "guiraud_index", "herdan_index", "dugast_index",
    "lemmes_animal", "diversite_animal",
    "lemmes_plante", "diversite_plante",
    "lemmes_champignon", "diversite_champignon",
    "lemmes_loterre", "diversite_loterre",
    "lemmes_taxon", "diversite_taxon",
    "TOTAL_LEMME", "TOTAL_DIVERSITE",
    "proportion_animal_‰", "proportion_plante_‰", "proportion_champignon_‰",
    "proportion_loterre_‰", "proportion_taxon_‰",
]


def load_keys(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        if "Key" not in (reader.fieldnames or []):
            return {}
        return {r["File"]: r["Key"] for r in reader}


def load_entity_counts(entites_csv):
    """Returns {filename: {category: (abundance, richness)}}."""
    by_file = {}
    with open(entites_csv, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            by_file.setdefault(r["fichier"], {}).setdefault(r["source"], []).append(r["lemme"])
    counts = {}
    for fn, by_cat in by_file.items():
        counts[fn] = {}
        for cat, lemmes in by_cat.items():
            counts[fn][cat] = (len(lemmes), len(set(lemmes)))
    return counts


def build_corpus(name, meta_path, entites_csv, key_sources, output_path):
    with open(meta_path, encoding="utf-8") as f:
        meta_rows = list(csv.DictReader(f, delimiter="\t"))

    entity_counts = load_entity_counts(entites_csv)

    keys = {}
    for ks in key_sources:
        for fn, k in ks.items():
            keys.setdefault(fn, k)

    out_rows = []
    n_missing_key, n_missing_entities = 0, 0
    for row in meta_rows:
        fn = row["File"]
        key = keys.get(fn, "")
        if not key:
            n_missing_key += 1

        cat_counts = entity_counts.get(fn, {})
        if not cat_counts:
            n_missing_entities += 1

        nb_tokens = float(row["nb_tokens"]) if row.get("nb_tokens") else 0.0

        out = {
            "Key": key,
            "File": fn,
            "Year": row.get("Year", ""),
            "Author": row.get("Author", ""),
            "Sexe auteur": row.get("Sexe auteur", ""),
            "Année naissance": row.get("Année naissance", ""),
            "Nationalité": row.get("Nationalité", ""),
            "Title": row.get("Title", ""),
            "Publisher": row.get("Publisher", ""),
            "Distinction": row.get("Distinction", ""),
            "nb_tokens": row.get("nb_tokens", ""),
            "nb_formes": row.get("nb_formes", ""),
            "nb_lemmes": row.get("nb_lemmes", ""),
            "guiraud_index": row.get("guiraud_index", ""),
            "herdan_index": row.get("herdan_index", ""),
            "dugast_index": row.get("dugast_index", ""),
        }

        total_lemme, total_diversite = 0, 0
        for cat in CATEGORIES:
            abundance, richness = cat_counts.get(cat, (0, 0))
            out[f"lemmes_{cat}"] = abundance
            out[f"diversite_{cat}"] = richness
            total_lemme += abundance
            total_diversite += richness
        out["TOTAL_LEMME"] = total_lemme
        out["TOTAL_DIVERSITE"] = total_diversite

        for cat in CATEGORIES:
            abundance, _ = cat_counts.get(cat, (0, 0))
            out[f"proportion_{cat}_‰"] = (abundance / nb_tokens * 1000) if nb_tokens else 0.0

        out_rows.append(out)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"{name}: {len(out_rows)} romans ecrits dans {output_path} "
          f"({n_missing_key} sans Key, {n_missing_entities} sans aucune donnee d'entite)")


if __name__ == "__main__":
    keys_principal = load_keys("resultats/corpus_principal/decomptes_totaux.csv")
    keys_bestsellers = load_keys("resultats/bestsellers/decomptes_totaux_bestsellers.csv")

    build_corpus(
        "DigEco", "corpus_DigEco.csv", "resultats/corpus_principal/ENTITES_TOTAL.csv",
        [keys_principal], "resultats/corpus_principal/decomptes_totaux_AJOUR_20261105.csv",
    )
    build_corpus(
        "PRIX_ECOLOGIE", "corpus_PRIX_ECOLOGIE.csv", "resultats/corpus_principal/ENTITES_TOTAL.csv",
        [keys_principal], "resultats/decomptes_totaux_PRIX_ECOLOGIE_20261105.csv",
    )
    build_corpus(
        "Bestsellers", "corpus_Bestsellers.csv", "resultats/bestsellers/BESTSELLERS_ENTITES_MERGED.csv",
        [keys_bestsellers, keys_principal], "resultats/bestsellers/decomptes_totaux_bestsellers_AJOUR_20261105.csv",
    )
