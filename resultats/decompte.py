import pandas as pd

"""
Ce script effectue les décomptes d'entités à partir du fichier général et croise ces informations avec les métadonnées du corpus.

"""


input_csv = 'PLANTES_ANIMAUX_LOTERRE.csv'
data = pd.read_csv(input_csv, sep='\t')

# Initialiser un dictionnaire pour stocker les résultats
results = {}

# Parcourir chaque fichier unique dans le fichier CSV
for file in data['fichier'].unique():
    file_data = data[data['fichier'] == file]

    # Initialiser les compteurs pour chaque catégorie
    nb_lemma_animal = 0
    diversity_animal = set()
    nb_lemma_plante = 0
    diversity_plante = set()
    nb_lemma_champignon = 0
    diversity_champignon = set()
    nb_lemma_loterre = 0
    diversity_loterre = set()

    # Compter les lemmes et la diversité pour chaque catégorie
    for index, row in file_data.iterrows():
        if row['source'] == 'animal':
            nb_lemma_animal += 1
            diversity_animal.add(row['lemme'])
        elif row['source'] == 'plante':
            nb_lemma_plante += 1
            diversity_plante.add(row['lemme'])
        elif row['source'] == 'champignon':
            nb_lemma_champignon += 1
            diversity_champignon.add(row['lemme'])
        elif row['source'] == 'loterre':
            nb_lemma_loterre += 1
            diversity_loterre.add(row['lemme'])

    # Calculer la diversité
    diversity_animal = len(diversity_animal)
    diversity_plante = len(diversity_plante)
    diversity_champignon = len(diversity_champignon)
    diversity_loterre = len(diversity_loterre)

    # Calculer le total des lemmes et la diversité totale
    total_lemma = nb_lemma_animal + nb_lemma_plante + nb_lemma_champignon + nb_lemma_loterre
    total_diversity = diversity_animal + diversity_plante + diversity_champignon + diversity_loterre

    # Stocker les résultats dans le dictionnaire
    results[file] = {
        'File' : file,
        'lemmes_animal': nb_lemma_animal,
        'diversite_animal': diversity_animal,
        'lemmes_plante': nb_lemma_plante,
        'diversite_plante': diversity_plante,
        'lemmes_champignon': nb_lemma_champignon,
        'diversite_champignon': diversity_champignon,
        'lemmes_loterre' : nb_lemma_loterre,
        'diversite_loterre' : diversity_loterre,
        'TOTAL_LEMME': total_lemma,
        'TOTAL_DIVERSITE': total_diversity
    }

# Convertir le dictionnaire de résultats en DataFrame
results_df = pd.DataFrame.from_dict(results, orient='index')

metadata = pd.read_csv("../corpus_DigEco.csv", sep='\t')
metadata = metadata.merge(results_df, on=["File"])


metadata['pourcentage_animal'] = ( metadata['lemmes_animal'] / metadata['nb_tokens'] ) * 1000
metadata['pourcentage_plante'] = ( metadata['lemmes_plante'] / metadata['nb_tokens'] ) * 1000
metadata['pourcentage_champignon'] = ( metadata['lemmes_champignon'] / metadata['nb_tokens'] ) * 1000
metadata['pourcentage_loterre'] = ( metadata['lemmes_loterre'] / metadata['nb_tokens'] ) * 1000

# Sauvegarder le DataFrame dans un nouveau fichier CSV
output_csv = 'decomptes_totaux.csv'

metadata.to_csv(output_csv, sep='\t', index=False)

