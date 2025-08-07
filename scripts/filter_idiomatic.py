import polars as pl
import sys

if len(sys.argv) < 3:
	print("Usage : python filter_idiomatic.py input.csv output.csv")
	exit(1)

infile = sys.argv[1]
outfile = sys.argv[2]

REF_IDIOMATIC = "../métaphore/liste_expressions_figées_animaux.csv"

df = pl.read_csv(infile, separator='\t')

df_ref = pl.read_csv(REF_IDIOMATIC, separator='\t')


df_joined = df.join(df_ref, on='token_lexique', how='inner')

df_matched = df_joined.filter(
    df_joined['contexte'].str.contains(df_joined['expression'])
)

df_matched.write_csv("../métaphore/Bestsellers_contexte_expressions_idiomatiques.csv", separator='\t')

df_clean = df_matched.select(df.columns) # supprime les colonnes excédentaires

df_clean = df.join(df_clean, on=df.columns, how='anti')

df_clean.write_csv(outfile, separator='\t')
