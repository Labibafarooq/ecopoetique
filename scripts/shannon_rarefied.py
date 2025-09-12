import sys
import random
import polars as pl
from collections import Counter
from scipy.stats import entropy

"""
Ce script calcule le score de biodiversité et l'écrit dans le fichier global de métadonnées.
"""

if len(sys.argv) < 2:
	ENTITES_TOTAL = "../resultats/corpus_principal/ENTITES_TOTAL.csv"
	#ENTITES_TOTAL = "../resultats/bestsellers/BESTSELLERS_ENTITES.csv"
	FICHIER_METADONNEES = "../corpus_DigEco.csv"
	#FICHIER_METADONNEES = "../corpus_Bestsellers.csv"

else:
	ENTITES_TOTAL = sys.argv[1]
	FICHIER_METADONNEES = sys.argv[2]


df = pl.read_csv(ENTITES_TOTAL, separator='\t')

# FILTRAGE POUR CALCUL PLANTES+CHAMPIGNONS
#df = df.filter(pl.col('source').is_in(['plante', 'champignon']))

# FILTRAGE POUR CALCUL LOTERRE+TAXONS
#df = df.filter(pl.col('source').is_in(['loterre', 'taxon']))

def shannon_rarefied(population, size=10, trials=30):
    if len(population) < size:
        return None  # Pas assez d'entités pour rarefaction
    shannon_values = []
    for _ in range(trials):
        sample = random.sample(population, size)
        sample_counts = Counter(sample)
        proportions = [v / size for v in sample_counts.values()]
        H = entropy(proportions)
        shannon_values.append(H)
    return sum(shannon_values) / len(shannon_values)

shannon_by_text = {}

files = df['fichier'].unique().to_list()

for filename in files:
    data = df.filter(pl.col('fichier') == filename)
    shannon_by_text[filename] = shannon_rarefied(data['lemme'].to_list())
    
digeco = pl.read_csv(FICHIER_METADONNEES, separator='\t')

df_dict = pl.DataFrame({
    'File': list(shannon_by_text.keys()),
    'Shannon_rarefied': list(shannon_by_text.values())
})

digeco = digeco.join(df_dict, on='File', how='left')

digeco.write_csv(FICHIER_METADONNEES, separator='\t')
