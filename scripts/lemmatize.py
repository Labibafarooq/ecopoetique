import sys
import pandas as pd
from french_lefff_lemmatizer.french_lefff_lemmatizer import FrenchLefffLemmatizer

if len(sys.argv) < 2:
	print("Usage : python lemmatize.py input.csv")
	exit(1)

infile = sys.argv[1]

dict_tok = {}

def lemmatize(token):
	if not token in dict_tok:
		dict_tok[token] = lemmatizer.lemmatize(token, 'n')
	return dict_tok[token]

lemmatizer = FrenchLefffLemmatizer()

df = pd.read_csv(infile, sep='\t')

df['lemme'] = df['token_lexique'].apply(lemmatize)

df.to_csv(infile, sep='\t', index=False)
