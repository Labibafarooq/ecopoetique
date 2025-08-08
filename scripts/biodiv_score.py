import polars as pl

df = pl.read_csv("../resultats/decomptes_totaux.csv", separator='\t')

biodiv_by_text = {}

df = df.with_columns((pl.col("Shannon_rarefied") * (pl.col("TOTAL_LEMME") / pl.col("nb_tokens"))).alias('biodiv_score'))

df.write_csv("../resultats/decomptes_totaux.csv", separator='\t')


