import sys
import pandas as pd
import spacy
from truncate_sentence import truncate_sentence


nlp = spacy.load("fr_dep_news_trf")


if len(sys.argv) < 3:
	print("Usage : python pos_tag_homographe.py input.csv output.csv liste_homographe.txt")
	exit(1)

infile = sys.argv[1]
outfile = sys.argv[2]
liste_homographes = sys.argv[3]


df = pd.read_csv(infile, sep='\t', usecols=['fichier','token_lexique', 'contexte'], dtype = {'fichier': str, 'token_lexique': str, 'contexte': str})

# Termes à désambiguïser
with open(liste_homographes, 'r') as f:
	termes = [x.strip('\n') for x in f]

df_filtre = df[df['token_lexique'].isin(termes)]

print("Taille initiale du fichier : {}".format(len(df)))
print("Nombre de termes ambigus : {}".format(len(df_filtre)))

# Utiliser un contexte plus court par souci d'économie
df_filtre['chunk_for_POS'] = df_filtre.apply(truncate_sentence, axis=1)

# Appliquer spacy et stocker dans POS
df_filtre['POS'] = df_filtre['chunk_for_POS'].apply(lambda x: [(token.text, token.pos_) for token in nlp(x)])

# Créer une nouvelle colonne 'TOKEN_POS' qui contient la POS du token
df_filtre['TOKEN_POS'] = df_filtre.apply(lambda row: [pos for text, pos in row['POS'] if text == row['token_lexique']], axis=1)

# Enregistrer la trace des annotations
df_filtre.to_csv("annotations_POS_homographes.csv", sep='\t', index=False)

# Garder seulement la première annotation lorsque le token apparaît plusieurs fois
df_filtre['TOKEN_POS'] = df_filtre['TOKEN_POS'].apply(lambda x: x[0] if x else None)

# Fusionner la df et son filtre
merged_df = pd.merge(df, df_filtre[['fichier', 'token_lexique', 'contexte', 'TOKEN_POS']], on=['fichier', 'token_lexique', 'contexte'], how='left')

# Filtrer les lignes où le POS tag du token n'est pas un nom
merged_df = merged_df[(merged_df['TOKEN_POS'] == 'NOUN') | (merged_df['TOKEN_POS'].isnull())]

# Supprimer la colonne TOKEN_POS
merged_df = merged_df.drop(columns=['TOKEN_POS'])

print("Taille du fichier après élimination par POS : {}".format(len(merged_df)))

merged_df.to_csv(outfile, sep='\t', index=False)
