import sys
import pandas as pd

"""
Ce script élimine les doublons dans la liste des occurrences extraites du corpus global pour ne garder que les occurrences les plus spécifiques. Par exemple, si on a "dorade" et "dorade rose" dans le corpus, la même occurrence apparaîtra 2 fois, mais on ne gardera que "dorade rose". 

"""

param=sys.argv
if len(param) < 3:
	print("File name missing. Usage : python remove_duplicates.py  contexte.csv output.csv\n")
	exit(1)
	
df = pd.read_csv(param[1], sep='\t')

print("Taille du fichier avant filtrage : {}".format(len(df)))

# Grouper par contexte pour ne comparer que les tokens apparaissant dans le même contexte
grouped = df.groupby('contexte')

# Liste pour stocker les lignes filtrées
filtered_rows = []

# Parcourir chaque groupe (contexte similaire)
for contexte, group in grouped:
    # Trier les tokens par longueur (du plus long au plus court) dans chaque groupe
    group = group.sort_values(by='token_lexique', key=lambda x: x.str.len(), ascending=False)
    
    # Liste des tokens conservés pour chaque groupe
    tokens_conserves = []
    
    for i, row in group.iterrows():
        token = row['token_lexique']
        
        # Vérifier si le token est un sous-token d'un token déjà conservé dans le même contexte
        if not any(token in t for t in tokens_conserves):
            tokens_conserves.append(token)
            filtered_rows.append(row)

# Convertir le résultat en DataFrame
df_filtered = pd.DataFrame(filtered_rows).reset_index(drop=True)

print("Taille du fichier après filtrage : {}".format(len(df_filtered)))

df_filtered.to_csv(param[2], sep='\t', index=False)

