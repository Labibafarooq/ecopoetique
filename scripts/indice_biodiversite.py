import polars as pl
import sys

"""
Ce script calcule l'indice de biodiversité et l'écrit dans le fichier global de métadonnées.
"""

if len(sys.argv) < 2:
	FICHIER_METADONNEES = "../corpus_DigEco.csv"
	FICHIER_DECOMPTE = "../resultats/corpus_principal/decomptes_totaux.csv"

else:
	FICHIER_METADONNEES = sys.argv[1]
	FICHIER_DECOMPTE = sys.argv[2]


#FICHIER_METADONNEES = "../corpus_Bestsellers.csv"
#FICHIER_DECOMPTE = "../resultats/bestsellers/decomptes_totaux_bestsellers.csv"


digeco = pl.read_csv(FICHIER_METADONNEES, separator='\t')

decomptes = pl.read_csv(FICHIER_DECOMPTE, separator='\t', columns=['File', 'TOTAL_LEMME'])

df = digeco.join(decomptes, on="File", how="left")

df = df.with_columns(
    (pl.col("Shannon_rarefied") * (pl.col("TOTAL_LEMME") / pl.col("nb_tokens"))).alias("biodiv_index")
)

df = df.drop('TOTAL_LEMME')

df.write_csv(FICHIER_METADONNEES, separator='\t')
