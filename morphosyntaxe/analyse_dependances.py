import sys
import polars as pl
from ast import literal_eval
import matplotlib.pyplot as plt
import seaborn as sns


if len(sys.argv) < 2:
	print("Usage : python analyse_dependances.py filename.csv")
	exit(1)
else:
	INPUT_FILE = sys.argv[1]

df = pl.read_csv(INPUT_FILE, separator='\t')


"""
# Pour filter les romans écologiques
corpus_eco = pl.read_csv("../corpus_PRIX_ECOLOGIE.csv", separator='\t')

# FILTRAGE DES ROMANS ECO
df = df.filter(~df['fichier'].is_in(corpus_eco['File']))
"""

# Agentivité : nsubj, ROOT, obl:agent
# Récepteur passif : nsubj:pass
# Complément du nom : nmod
# Élément de conjonction : conj
# Objet : obj
# Non-étiquetés

# Evaluation littérale des colonnes pour récupérer tuple
df = df.with_columns([
    pl.col("tête").map_elements(literal_eval).alias("tête"),
    pl.col("tête_de_tête").map_elements(literal_eval).alias("tête_de_tête")
])

def classify_relation(tete, tete_de_tete):
    rel = tete[1] if tete and len(tete) > 1 else None

    if rel == "conj":
        rel = tete_de_tete[1] if tete_de_tete and len(tete_de_tete) > 1 else None

    if rel in ["nsubj", "ROOT", "obl:agent"]:
        return "Agent"
    elif rel == "nsubj:pass":
        return "Récepteur passif"
    elif rel == "nmod":
        return "Complément du nom"
    elif rel == "obj":
        return "Objet"
    elif rel in [None, ""]:
        return "Autre"
    else:
        return "Autre"
    
# Appliquer la classification
df = df.with_columns([
    pl.struct(["tête", "tête_de_tête"]).map_elements(
        lambda row: classify_relation(row["tête"], row["tête_de_tête"])
    ).alias("catégorie")
])

# Compter les fréquences
counts = df.group_by("catégorie").len().sort("len", descending=True)

# Conversion pour matplotlib
labels = counts["catégorie"].to_list()
sizes = counts["len"].to_list()


# Afficher seulement les pourcentages > 1%
def my_autopct(pct):
    return ('%1.1f%%' % pct) if pct >= 1 else ''
    
color_map = {
    "Complément du nom": "peachpuff",
    "Agent": "dodgerblue",
    "Autre": "palevioletred",
    "Objet": "lightgreen",
    "Récepteur passif": "gold",
    #"Non-étiquetés": "white"  # Optionnel
}

colors = [color_map.get(label, "lightgrey") for label in labels]

# Tracer le diagramme circulaire
#cmap = sns.color_palette("husl", len(labels))
plt.figure(figsize=(8, 6))
plt.pie(sizes, labels=labels, autopct=my_autopct, startangle=115, colors=colors)
plt.title("Répartition des relations syntaxiques", pad=20)
plt.axis('equal')
plt.show()
