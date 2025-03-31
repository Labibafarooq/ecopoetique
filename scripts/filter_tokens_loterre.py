import sys
import pandas as pd

if len(sys.argv) < 3:
	print("Usage : python filter_tokens.py input.csv output.csv")
	exit(1)

infile = sys.argv[1]
outfile = sys.argv[2]
	
df = pd.read_csv(infile, sep='\t', dtype = {'fichier': str, 'token_lexique': str, 'contexte': str})

print("Nombre initial d'occurrences : {}".format(len(df)))


# Filtre par token
filtre = df[
	((df['token_lexique'] == 'plage') & (df['contexte'].str.contains('plage arrière')))
]


print("Taille du filtre : {}".format(len(filtre)))


# Trouver les lignes dans df qui ne sont pas dans les df filtrés
df_new = df[~df.index.isin(filtre.index)]

print("Nombre d'occurrences après premier filtrage : {}".format(len(df_new)))

df_new.to_csv(outfile, sep='\t', index=False)

