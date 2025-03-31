import sys
import pandas as pd

if len(sys.argv) < 3:
	print("Usage : python filter_tokens.py input.csv output.csv")
	exit(1)

infile = sys.argv[1]
outfile = sys.argv[2]
	
df = pd.read_csv(infile, sep='\t', dtype = {'fichier': str, 'token_lexique': str, 'contexte': str})

print("Nombre initial d'occurrences : {}".format(len(df)))

#filtre_1 = df[(df['token'] == 'lama') & (df['contexte'].str.contains('dalaï-lama'))]

# Filtre par token
filtre_1 = df[
	((df['token_lexique'] == 'lama') & (df['contexte'].str.contains('dalaï-lama'))) |
	((df['token_lexique'] == 'cheval') & (df['contexte'].str.contains('queue-de-cheval|queue de cheval|cheval d’arçon|à cheval sur'))) |
	((df['token_lexique'] == 'kangourou') & (df['contexte'].str.contains('slip kangourou'))) |
	((df['token_lexique'] == 'colin') & (df['contexte'].str.contains('colin-maillard'))) |
	((df['token_lexique'] == 'lapin') & (df['contexte'].str.contains('coup du lapin'))) |
	((df['token_lexique'] == 'cerfs') & (df['contexte'].str.contains('cerfs-volants'))) |
	((df['token_lexique'] == 'cerf') & (df['contexte'].str.contains('cerf-volants'))) |
	((df['token_lexique'] == 'oie') & (df['contexte'].str.contains("pattes-d’oie"))) |
	((df['token_lexique'] == 'bœuf') & (df['contexte'].str.contains("œil-de-bœuf"))) |
	((df['token_lexique'] == 'élan') & (df['contexte'].str.contains("dans son élan"))) |
	((df['token_lexique'] == 'élan') & (df['contexte'].str.contains("dans un élan"))) |
	((df['token_lexique'] == 'élan') & (df['contexte'].str.contains("prendre de l’élan")))
]


filtre_2 = df[
	((df['fichier'] == 'Deville-Patrick_Peste_choléra.txt') & (df['token_lexique'] == 'lama')) |
	((df['fichier'] == 'Grayson-Catherine-Lune_Le-testament-de-nos-corps.txt') & (df['token_lexique'] == 'lama')) |
	((df['fichier'] == 'Kaddour-Hedi_Waltenberg.txt') & (df['token_lexique'] == 'taupe')) |
	((df['fichier'] == 'Donner-Christophe_Un-roi-sans-lendemain.txt') & (df['token_lexique'] == 'dauphin')) |
	((df['fichier'] == 'Lobe-Max_Confidences.txt') & (df['token_lexique'] == 'barbue')) |
	((df['fichier'] == 'April-Jean-Philippe_Les-ensauvagés.txt') & (df['token_lexique'] == 'capucin'))
]

filtre = pd.concat([filtre_1, filtre_2])

print(filtre)
#filtre.to_csv("temp.csv", sep='\t', index=False)
print("Taille du filtre : {}".format(len(filtre)))


# Trouver les lignes dans df qui ne sont pas dans les df filtrés
df_new = df[~df.index.isin(filtre.index)]

print("Nombre d'occurrences après premier filtrage : {}".format(len(df_new)))

df_new.to_csv(outfile, sep='\t', index=False)

