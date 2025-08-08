import polars as pl
import matplotlib.pyplot as plt
import numpy as np

df = pl.read_csv("../resultats/decomptes_totaux.csv", separator='\t')

eco = pl.read_csv("../corpus_PRIX_ECOLOGIE.csv", separator='\t')

files_eco = eco['File'].to_list()

"""
with open("../liste_corpus_sans_eco.txt", 'r') as f:
    filtre = [x.strip('\n') for x in f.readlines()] 

df = df.filter(pl.col("File").is_in(filtre))
"""


# Moyenne et médiane globale par année
stats_all = (
    df.group_by("Year")
    .agg([
        pl.col("biodiv_score").mean().alias("mean_all"),
        pl.col("biodiv_score").median().alias("median_all")
    ])
    .sort("Year")
)


# Moyenne pour le corpus Prix de l'écologie
stats_subset = (
    df.filter(pl.col("File").is_in(files_eco))
    .group_by("Year")
    .agg([
        pl.col("biodiv_score").mean().alias("mean_subset")
    ])
    .sort("Year")
)

# Fusion des dfs
stats_combined = stats_all.join(stats_subset, on="Year", how="left")


# Affichage du graphique
years = stats_combined["Year"].to_list()
mean_all = stats_combined["mean_all"].to_list()
median_all = stats_combined["median_all"].to_list()
mean_subset = stats_combined["mean_subset"].to_list()

# Conversion en arrays NumPy pour la régression
x = np.array(years)

# Tendance pour la moyenne
coef_mean_all = np.polyfit(x, mean_all, deg=1)
trend_mean_all = np.polyval(coef_mean_all, x)

# Tendance pour la médiane
coef_median_all = np.polyfit(x, median_all, deg=1)
trend_median_all = np.polyval(coef_median_all, x)

# Tendance pour corpus éco
if all(v is not None for v in mean_subset):
    coef_subset = np.polyfit(x, mean_subset, deg=1)
    trend_subset = np.polyval(coef_subset, x)
else:
    trend_subset = [None] * len(x)


plt.figure(figsize=(10, 6))
plt.plot(years, mean_all, label="Moyenne (corpus global)", marker='o')
plt.plot(years, median_all, label="Médiane (corpus global)", marker='s')
plt.plot(years, mean_subset, label="Moyenne (corpus Prix de l'écologie)", marker='^', linestyle='--')

plt.plot(years, trend_mean_all, linestyle=':', color='blue', label="Tendance moyenne")
plt.plot(years, trend_median_all, linestyle=':', color='orange', label="Tendance médiane")
#if all(v is not None for v in trend_subset):
    #plt.plot(years, trend_subset, linestyle=':', color='green', label="Tendance moyenne (sélection)")


plt.xlabel("Année")
plt.ylabel("Indice de biodiversité")
plt.title("Évolution de la biodiversité par année")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("évolution_score_biodiversité.png")
plt.show()

