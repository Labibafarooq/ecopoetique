import sys, os
import spacy

"""
Ce script tokénise un texte et affiche un token par ligne avec sa catégorie grammaticale et son lemme.

"""

if len(sys.argv) < 2:
	print("Usage : python run_spacy.py filename.txt")
	exit(1)
else:
	INPUT_FILE = sys.argv[1]

nlp = spacy.load("fr_dep_news_trf")

import fr_dep_news_trf
nlp = fr_dep_news_trf.load()

outputname = os.path.splitext(INPUT_FILE)[0] + '_tokens.txt'
outf = open(outputname, 'w')

with open(INPUT_FILE, 'r') as f:
	text = f.readlines()
	for line in text:
		doc = nlp(line)
		
		for d in doc:
			outf.write('\t'.join([d.text, d.pos_, d.lemma_, '\n']))
