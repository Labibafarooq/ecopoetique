import random
import polars as pl
from collections import Counter
from scipy.stats import entropy

df = pl.read_csv("../resultats/PLANTES_ANIMAUX_LOTERRE.csv", separator='\t')

def shannon_rarefied(population, size=50, trials=30):
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
    
digeco = pl.read_csv("../corpus_DigEco.csv", separator='\t')

df_dict = pl.DataFrame({
    'File': list(shannon_by_text.keys()),
    'Shannon_rarefied': list(shannon_by_text.values())
})

digeco = digeco.join(df_dict, on='File', how='left')

digeco.write_csv("../corpus_DigEco.csv", separator='\t')
