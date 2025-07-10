import sys
import pandas as pd
import spacy
import csv

if len(sys.argv) < 3:
    print("Usage : python filter_tokens_ambigus_loterre.py input.csv output.csv")
    exit(1)

infile = sys.argv[1]
outfile = sys.argv[2]
    
# Charger le fichier CSV
df = pd.read_csv(infile, sep='\t', dtype={'fichier': str, 'token_lexique': str, 'contexte': str})

print("Nombre initial d'occurrences : {}".format(len(df)))

nlp = spacy.load("fr_dep_news_trf")

# 1. Filtre pour les expressions figées ( un sens qui n'est pas lié à la biodiversité)
filtre_expressions = df[
    
    ((df['token_lexique'] == 'espèce') & (df['contexte'].str.contains(r"\bespèce d['’] *\w+", case=False))) |
    
    
    ((df['token_lexique'] == 'nature') & (df['contexte'].str.contains('par nature|de nature|nature humaine|nature profonde|nature des êtres', case=False))) |
    
    
    ((df['token_lexique'] == 'milieu') & (df['contexte'].str.contains('au milieu de|milieu social'))) |
    
   
    ((df['token_lexique'] == 'espaces') & (df['contexte'].str.contains('espaces vides', case=False))) |
    
    
    ((df['token_lexique'] == 'bord') & (df['contexte'].str.contains('bord de table|bord de trottoir', case=False))) |
    
    
    ((df['token_lexique'] == 'fond') & (df['contexte'].str.contains('fond de tiroir', case=False))) |


    ((df['token_lexique'] == 'proie') & (df['contexte'].str.contains('en proie à', case=False))) |


    ((df['token_lexique'] == 'atmosphère') & (df['contexte'].str.contains(r"atmosphère\s+(?:étrange|romantique|pesante|angoissante|lourde|de la pièce|de la ville)", case=False))) |
    
    ((df['token_lexique'] == 'champ') & (df['contexte'].str.contains('champ lexical|champ de bataille', case=False))) |
    
    # Herbe - filtrer les usages liés à la drogue
    ((df['token_lexique'] == 'herbe') & (df['contexte'].str.contains('fumer de l\'herbe', case=False))) |
    
    ((df['token_lexique'] == 'zone') & (df['contexte'].str.contains('zone militaire', case=False))) |
    
    # Sol - filtrer les usages musicaux
    ((df['token_lexique'] == 'sol') & (df['contexte'].str.contains('note de sol|sol majeur', case=False))) |
    
    ((df['token_lexique'] == 'sols') & (df['contexte'].str.contains('sols carrelés', case=False))) |

    ((df['token_lexique'] == 'plage') & df['contexte'].str.contains(r"\bplages? (?:horaires?|arrières?|de temps )", case=False)) |
    
    ((df['token_lexique'] == 'cycle') & (df['contexte'].str.contains('cycle scolaire', case=False))) |
     
    ((df['token_lexique'] == 'fleuve') & df['contexte'].str.contains(r"\bromans?-?fleuves?\b", case=False)) |
    
    ((df['token_lexique'] == 'pêche') & (df['contexte'].str.contains('a la pêche|ont la pêche|peau de pêche|couleur pêche|couleur de pêche|noyau de pêche|teinte pêche|jus de pêche|sirop de pêche|pêche Melba'))) |
    
    ((df['token_lexique'] == 'baie') & df['contexte'].str.contains("baie vitrée")) |
    ((df['token_lexique'] == 'atmosphère') & df['contexte'].str.contains("détendre l’atmosphère|détend l’atmosphère|atmosphère (malsaine|joyeuse|tendue|confinée|festive)"))
]

print("Filtre expressions figées : {} occurrences".format(len(filtre_expressions)))
 
# 2. Filtre pour l'ambiguïté grammaticale 
ambiguites_grammaticales = {
    "plante": {"pos_invalide": ["VERB"], "lemmes_invalides": ["planter"], "description": "Verbe 'planter'"},
    "désert": {"pos_invalide": ["ADJ"], "lemmes_invalides": ["désert"], "description": "Adjectif 'lieu désert'"},
    "sauvage": {"pos_invalide": ["ADJ"], "lemmes_invalides": ["sauvage"], "description": "Adjectif comportemental"},
    "marin": {"pos_invalide": ["NOUN"], "lemmes_invalides": ["marin"], "description": "Nom de métier"},
    "carnassier":{"pos_invalide":["ADJ"], "lemmes_invalides":["carnassier"], "description" : "Adjectif 'animal carnassier'"} 
}

filtre_grammatical_indices = []
tokens_grammaticaux = ambiguites_grammaticales.keys()

# Sélectionner les lignes qui contiennent potentiellement ces tokens

df_gram = pd.DataFrame()
for token in tokens_grammaticaux:
    df_gram = pd.concat([df_gram, df[df['contexte'].str.contains(r'\b' + token + r'\w*\b', case=False, regex=True)]])

df_gram = df_gram.drop_duplicates()
print("Analyse grammaticale de {} occurrences avec spaCy...".format(len(df_gram)))

for idx, row in df_gram.iterrows():
    contexte = row['contexte']
    
    # Analyser la phrase avec spaCy
    doc = nlp(contexte)
    
    # Parcourir tous les mots de la phrase
    for word in doc:
        # Vérifier si le lemme correspond à l'un des lemmes à filtrer
        for token, regles in ambiguites_grammaticales.items():
            if word.lemma_.lower() in regles["lemmes_invalides"] and word.pos_ in regles["pos_invalide"]:
                filtre_grammatical_indices.append(idx)
                break

filtre_grammatical = df.loc[filtre_grammatical_indices]
print("Filtre grammatical : {} occurrences".format(len(filtre_grammatical)))

# Combiner les filtres existants
filtre_combine = pd.concat([filtre_expressions, filtre_grammatical])
filtre = filtre_combine
print("Taille totale du filtre actuel : {}".format(len(filtre)))

# Trouver les lignes dans df qui ne sont pas dans le filtre
df_new = df[~df.index.isin(filtre.index)].drop_duplicates()

print("Nombre d'occurrences après filtrage : {}".format(len(df_new)))


# Enregistrer le résultat filtré
df_new.to_csv(outfile, sep='\t', index=False)
