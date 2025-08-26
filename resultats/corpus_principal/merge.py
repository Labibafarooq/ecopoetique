import pandas as pd
import numpy as np

"""
Ce script fusionne les résultats pour toutes les entités et génère un unique CSV contenant tous les contextes.

"""

# Charger les fichiers CSV
df1 = pd.read_csv('ENTITES_contexte_plantes.csv', usecols=['fichier', 'token_lexique', 'truncated_sentence', 'lemme'], sep='\t')
df2 = pd.read_csv('ENTITES_contexte_animaux.csv', usecols=['fichier', 'token_lexique', 'truncated_sentence', 'lemme'], sep='\t')
df3 = pd.read_csv('ENTITES_contexte_champignons.csv', usecols=['fichier', 'token_lexique', 'contexte', 'lemme'], sep='\t')
df4 = pd.read_csv('ENTITES_contexte_loterre.csv', usecols=['fichier', 'token_lexique', 'contexte', 'lemme'], sep='\t')

df5 = pd.read_csv('ENTITES_contexte_taxons.csv', usecols=['fichier', 'token_lexique', 'contexte'], sep='\t')
df5['lemme'] = np.nan

df1 = df1.rename(columns={'truncated_sentence': 'contexte'})
df2 = df2.rename(columns={'truncated_sentence': 'contexte'})

# Ajouter une colonne pour indiquer la provenance des données
df1['source'] = 'plante'
df2['source'] = 'animal'
df3['source'] = 'champignon'
df4['source'] = 'loterre'
df5['source'] = 'taxon'

df_merged = pd.concat([df1, df2, df3, df4, df5], ignore_index=True)

df_merged.to_csv("ENTITES_total.csv", sep='\t', index=False)
