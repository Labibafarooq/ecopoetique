import sys
import pandas as pd

if len(sys.argv) < 2:
	print("Usage : python assign_category.py input.csv")
	exit(1)

filename = sys.argv[1]

df = pd.read_csv(filename, sep='\t')

# Lire les fichiers et stocker les animaux dans des set
def lire_fichier(nom_fichier):
    with open(nom_fichier, 'r') as f:
        return set(line.strip() for line in f)

amphibiens = lire_fichier('../lexiques/categories_animales/AMPHIBIENS.txt')
insectes = lire_fichier('../lexiques/categories_animales/INSECTES.txt')
mammiferes = lire_fichier('../lexiques/categories_animales/MAMMIFERES.txt')
mollusques = lire_fichier('../lexiques/categories_animales/MOLLUSQUES.txt')
poissons = lire_fichier('../lexiques/categories_animales/POISSONS.txt')
oiseaux = lire_fichier('../lexiques/categories_animales/OISEAUX.txt')
reptiles = lire_fichier('../lexiques/categories_animales//REPTILES.txt')

# Fonction pour déterminer la catégorie
def determiner_categorie(lemme):
    if lemme in amphibiens:
        return 'amphibien'
    elif lemme in insectes:
        return 'insecte'
    elif lemme in mammiferes:
        return 'mammifere'
    elif lemme in mollusques:
        return 'mollusque'
    elif lemme in poissons:
        return 'poisson'
    elif lemme in oiseaux:
        return 'oiseau'
    elif lemme in reptiles:
        return 'reptile'
    else:
        return 'autre'

# Appliquer la fonction pour créer la colonne 'categorie'
df['categorie'] = df['lemme'].apply(determiner_categorie)

# Sauvegarder
df.to_csv(filename, sep='\t', index=False)
