import pandas as pd

"""
Ce script fusionne les résultats pour toutes les entités et génère un unique CSV contenant tous les contextes.

"""

# Charger les fichiers CSV
df1 = pd.read_csv('contexte_plantes.csv', usecols=['fichier', 'token_lexique', 'contexte', 'lemme'], sep='\t')
df2 = pd.read_csv('contexte_animaux.csv', usecols=['fichier', 'token_lexique', 'truncated_sentence', 'lemme'], sep='\t')
df3 = pd.read_csv('contexte_champignons.csv', usecols=['fichier', 'token_lexique', 'contexte', 'lemme'], sep='\t')
df4 = pd.read_csv('contexte_loterre.csv', usecols=['fichier', 'token_lexique', 'contexte', 'lemme'], sep='\t')

df2 = df2.rename(columns={'truncated_sentence': 'contexte'})

# Ajouter une colonne pour indiquer la provenance des données
df1['source'] = 'plante'
df2['source'] = 'animal'
df3['source'] = 'champignon'
df4['source'] = 'loterre'


df_merged = pd.concat([df1, df2, df3, df4], ignore_index=True)

df_merged.to_csv("PLANTES_ANIMAUX_LOTERRE.csv", sep='\t', index=False)
