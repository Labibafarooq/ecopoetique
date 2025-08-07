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
	((df['token_lexique'] == 'oie') & (df['contexte'].str.contains("pattes-d’oie|jeu de l’oie"))) |
	((df['token_lexique'] == 'bœuf') & (df['contexte'].str.contains("œil-de-bœuf"))) |
	((df['token_lexique'] == 'élan') & (df['contexte'].str.contains("dans son élan"))) |
	((df['token_lexique'] == 'élan') & (df['contexte'].str.contains("dans un élan"))) |
	((df['token_lexique'] == 'élan') & (df['contexte'].str.contains("prendre de l’élan"))) |
	((df['token_lexique'] == 'pie') & (df['contexte'].str.contains("apple-pie"))) |
	((df['token_lexique'] == 'pies') & (df['contexte'].str.contains("queue-de-pies|apple-pies"))) |
	((df['token_lexique'] == 'carpe') & (df['contexte'].str.contains("carpe diem"))) |
	((df['token_lexique'] == 'grue') & (df['contexte'].str.contains("pied de grue"))) |
	((df['token_lexique'] == 'bouc') & (df['contexte'].str.contains("bouc émissaire"))) |
	((df['token_lexique'] == 'bouc') & (df['contexte'].str.contains("dos-d'âne"))) |
	((df['token_lexique'] == 'poule') & (df['contexte'].str.contains("nids-de-poule|chair de poule|cul-de-poule|nid-de-poule"))) |
	((df['token_lexique'] == 'vairons') & (df['contexte'].str.contains("yeux vairons"))) |
	((df['token_lexique'] == 'raie') & (df['contexte'].str.contains("raie des fesses|raie sur le côté|raie de côté|raie de la tête|raie au milieu|séparés par une raie|raie du cul|raie bien dessinée")))|
	((df['token_lexique'] == 'loup') & (df['contexte'].str.contains("loup-garou"))) |
	((df['token_lexique'] == 'puces') & (df['contexte'].str.contains("marché aux puces"))) |
	((df['token_lexique'] == 'vive') & (df['contexte'].str.contains("qui-vive"))) |
	#((df['token_lexique'] == 'biche') & (df['contexte'].str.contains("ventre-de-biche"))) |
	((df['token_lexique'] == 'papillon') & (df['contexte'].str.contains("nœud papillon"))) |
	((df['token_lexique'] == 'papillons') & (df['contexte'].str.contains("nœuds papillons"))) |
	((df['token_lexique'] == 'poule') & (df['contexte'].str.contains("poule mouillée"))) |
	((df['token_lexique'] == 'souris') & (df['contexte'].str.contains("clic de souris"))) |
	((df['token_lexique'] == 'fourmis') & (df['contexte'].str.contains("fourmis dans les jambes"))) |
	((df['token_lexique'] == 'rats') & (df['contexte'].str.contains("mort-aux-rats"))) |
	((df['token_lexique'] == 'coq')  & (df['contexte'].str.contains("coq-à-l’âne"))) |
	((df['token_lexique'] == 'âne')  & (df['contexte'].str.contains("coq-à-l’âne"))) |
	((df['token_lexique'] == 'biche') & (df['contexte'].str.contains("pied-de-biche|pieds-de-biche"))) |
	(df['token_lexique'] == 'serpette') | (df['token_lexique'] == 'savate') |
	(df['token_lexique'] == 'castillane') |
	(df['token_lexique'] == 'cordon blanc')
]


filtre_2 = df[
	((df['fichier'] == 'Deville-Patrick_Peste_choléra.txt') & (df['token_lexique'] == 'lama')) |
	((df['fichier'] == 'Grayson-Catherine-Lune_Le-testament-de-nos-corps.txt') & (df['token_lexique'] == 'lama')) |
	((df['fichier'] == 'Kaddour-Hedi_Waltenberg.txt') & (df['token_lexique'] == 'taupe')) |
	((df['fichier'] == 'Donner-Christophe_Un-roi-sans-lendemain.txt') & (df['token_lexique'] == 'dauphin')) |
	((df['fichier'] == 'Lobe-Max_Confidences.txt') & (df['token_lexique'] == 'barbue')) |
	((df['fichier'] == 'April-Jean-Philippe_Les-ensauvagés.txt') & (df['token_lexique'] == 'capucin')) |
	((df['fichier'] == 'Apperry-Yann_Farrago.txt') & (df['token_lexique'] == 'pie')) |
	((df['fichier'] == 'Alaoui-Meryem_La-verite-sort-de-la-bouche-du-cheval.txt') & (df['token_lexique'] == 'cheval') & (df['contexte'].str.contains("Bouche de cheval")))
]

filtre = pd.concat([filtre_1, filtre_2])

print(filtre)
#filtre.to_csv("temp.csv", sep='\t', index=False)
print("Taille du filtre : {}".format(len(filtre)))


# Trouver les lignes dans df qui ne sont pas dans les df filtrés
df_new = df[~df.index.isin(filtre.index)]

print("Nombre d'occurrences après premier filtrage : {}".format(len(df_new)))

df_new.to_csv(outfile, sep='\t', index=False)

