import sys
import spacy
import pandas as pd

"""
Ce script détermine la tête et les dépendants de l'entité token_lexique dans son contexte.
"""

nlp = spacy.load("fr_dep_news_trf")

if len(sys.argv) < 2:
	print("Usage : python get_token_dependencies.py filename.csv")
	exit(1)
else:
	INPUT_FILE = sys.argv[1]

df = pd.read_csv(INPUT_FILE, sep='\t')

def get_dependencies(row):
    doc = nlp(row['truncated_sentence'])
    token_text = row['token_lexique']
    # Cas où l'entité est composée de plusieurs tokens
    if ' ' in token_text or '-' in token_text:
        tokens_entite = nlp(token_text)
        token_text = tokens_entite[0].text

    for token in doc:
        if token.text == token_text:
            head = (token.head.text, token.dep_)
            dependents = [(child.text, child.dep_) for child in token.children]
            return head, dependents

    return None, None

# Appliquer la fonction à chaque ligne du DataFrame
df['tête'], df['dépendants'] = zip(*df.apply(get_dependencies, axis=1))


df.to_csv("../morphosyntaxe/a_reannoter.csv", sep='\t')
