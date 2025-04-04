import os, sys
import pandas as pd
import datetime

if len(sys.argv) < 2:
	print("Usage : python build_table.py dossier_pipeline")
	exit(1)
else:
	dir_pipeline = sys.argv[1]

now = datetime.date.today()

INPUT_CSV = "../corpus_DigEco.csv"
OUTPUT_CSV = os.path.join(dir_pipeline, "corpus_analyse_" + str(now) + '.csv')

# Fichier contenant le nombre de tokens trouvés appartenant au thésaurus par fichier
TOKENS_THESAURUS = os.path.join(dir_pipeline, "nb_termes_par_texte.txt")

# Fichier contenant le nombre de mots uniques appartenant au thésaurus
UNIQUES_THESAURUS = os.path.join(dir_pipeline, "nb_uniq_par_texte.txt")


with open(TOKENS_THESAURUS, 'r') as f:
	nb_tok_thesaurus = {}
	for line in f:
		items = line.split(' ')
		filename = items[1].strip()
		nb_tok_thesaurus[filename] = items[0].strip()
	print(nb_tok_thesaurus)

with open(UNIQUES_THESAURUS, 'r') as f:
	nb_uniq_thesaurus = {}
	for line in f:
		nb_uniq_thesaurus[line.strip()] = next(f).strip()
	

with open(os.path.join(dir_pipeline, 'nb_occurrences_par_texte.txt'), 'r') as f:
	doc_to_terms = {}
	for line in f:
		if line[0] == ' ':
			occ = line.lstrip(' ').split(' ')
			nb_occ = occ[0]
			items = ' '.join(x for x in occ[1:])
			doc_occ = items.split(':')
			doc = doc_occ[0]
			term = doc_occ[1].strip()
			if doc_to_terms.get(doc) is not None:
				doc_to_terms[doc].append((term, nb_occ))
			else:
				doc_to_terms[doc] = [(term, nb_occ)]

"""
with open(os.path.join(dir_pipeline, "vol_tokens_par_oeuvre.txt"), 'r') as f:
	tokens_par_oeuvre = {}
	for line in f:
		tokens_par_oeuvre[line.strip()] = next(f).strip()
		
with open(os.path.join(dir_pipeline, "vol_mots_uniques_par_oeuvre.txt"), 'r') as f:
	mots_uniques_par_oeuvre = {}
	for line in f:
		mots_uniques_par_oeuvre[line.strip()] = next(f).strip()
"""
# Lecture des métadonnées
df = pd.read_csv(INPUT_CSV, delimiter='\t')

col_nb_tokens_thesaurus = []
col_nb_uniq_thesaurus = []
col_terms_fq = []
#col_total_tokens = []
#col_total_formes_flechies = []

for doc in df['File']:
	if doc in nb_tok_thesaurus:
		col_nb_tokens_thesaurus.append(nb_tok_thesaurus[doc])
		col_nb_uniq_thesaurus.append(nb_uniq_thesaurus[doc])
		col_terms_fq.append(doc_to_terms[doc])
		#col_total_tokens.append(tokens_par_oeuvre[doc])
		#col_total_formes_flechies.append(mots_uniques_par_oeuvre[doc])
	else:
		print("Aucune occurrence trouvée dans {}".format(doc))
		col_nb_tokens_thesaurus.append(0)
		col_nb_uniq_thesaurus.append(0)
		col_terms_fq.append(0)


df['tok_thesaurus'] = col_nb_tokens_thesaurus
df['uniq_thesaurus'] = col_nb_uniq_thesaurus
df['terms_fq'] = col_terms_fq

#df['tokens_total'] = col_total_tokens
#df['formes_flechies_total'] = col_total_formes_flechies

df.to_csv(OUTPUT_CSV, sep='\t', index=False)
