import sys, os
from ast import literal_eval
from subprocess import Popen, PIPE
import pandas as pd

PATH_CORPUS = "../CORPUS_TOTAL" # Remplacer ici par le chemin absolu

if len(sys.argv) < 3:
	print("Usage : python grep_contexte.py decompte.csv OUTPUT_NAME.csv")
	exit(1)
else:
	INPUT_CSV = sys.argv[1]
	OUTPUT_CSV = sys.argv[2]

df = pd.read_csv(INPUT_CSV, delimiter='\t')
df = df.fillna(0)

col_filename = []
col_token = []
col_texte = []

for fichier, terms in zip(df['File'], df['terms_fq']):
	if terms != '0':
		to_grep = [ x[0] for x in list(literal_eval(terms)) ]
		nom_fichier = os.path.join(PATH_CORPUS, fichier)
		
		for tok in to_grep:
			p1 = Popen(["grep", "-w", tok, nom_fichier], stdout=PIPE)
			res = p1.communicate()[0]
			sentences = [ s.strip(' ') for s in res.decode("utf-8").split('\n') if s != '' ]
			
			for sent in sentences:
				# grep more contexte if it is short
				if len(sent.split(' ')) < 6:
					#print(sent)
					p2 = Popen(["grep", "-Fw", "-B", "1", "-A", "1", sent, nom_fichier], stdout=PIPE)
					local_res = p2.communicate()[0]
					sent = local_res.decode("utf-8")
				col_filename.append(fichier)
				col_token.append(tok)
				col_texte.append(sent)
	#else:
		#col_filename.append(fichier)
		#col_token.append(0)
		#col_texte.append('')

df_res = pd.DataFrame()
df_res['fichier'] = col_filename
df_res['token_lexique'] = col_token
df_res['contexte'] = col_texte

df_res.to_csv(OUTPUT_CSV, sep='\t', index=False)

