import polars as pl

"""
Ce script effectue les décomptes d'entités à partir du fichier général et croise ces informations avec les métadonnées du corpus.
"""

# Charger les fichiers avec Polars
input_csv = 'PLANTES_ANIMAUX_LOTERRE.csv'
data = pl.read_csv(input_csv, separator='\t')
print(f"{data.height} lignes lues.")

metadata = pl.read_csv("../corpus_DigEco.csv", separator='\t')

# Liste des catégories
categories = ['animal', 'plante', 'champignon', 'loterre']

# Initialiser une liste pour stocker les résultats
results = []

# Parcourir chaque fichier unique
for file in data.select('fichier').unique().to_series():
    file_data = data.filter(pl.col('fichier') == file)

    file_result = {'File': file}

    total_lemma = 0
    total_diversity = 0

    for cat in categories:
        cat_data = file_data.filter(pl.col('source') == cat)

        nb_lemma = cat_data.height
        diversity = cat_data.select('lemme').unique().height

        file_result[f'lemmes_{cat}'] = nb_lemma
        file_result[f'diversite_{cat}'] = diversity

        total_lemma += nb_lemma
        total_diversity += diversity

    file_result['TOTAL_LEMME'] = total_lemma
    file_result['TOTAL_DIVERSITE'] = total_diversity

    results.append(file_result)

# Convertir la liste de dictionnaires en DataFrame Polars
results_df = pl.DataFrame(results)

# Fusionner avec les métadonnées sur la colonne "File"
merged = metadata.join(results_df, on='File', how='inner')

# Calcul des proportions (données en pour mille) pour chaque catégorie
for cat in categories:
    merged = merged.with_columns(
        ((pl.col(f'lemmes_{cat}') / pl.col('nb_tokens')) * 1000).alias(f'proportion_{cat}_‰')
    )

# Sauvegarder le résultat final
output_csv = 'decomptes_totaux.csv'
merged.write_csv(output_csv, separator='\t')
