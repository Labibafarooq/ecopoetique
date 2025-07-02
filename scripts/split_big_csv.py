import polars as pl

def split_tsv_with_polars(input_file, output_prefix, lines_per_file):
    # Lire le fichier TSV avec Polars
    df = pl.read_csv(input_file, separator="\t")

    # Calculer le nombre total de lignes et le nombre de fichiers nécessaires
    total_rows = df.height
    num_files = (total_rows // lines_per_file) + 1

    # Partitionner et sauvegarder les fichiers
    for i in range(num_files):
        start_idx = i * lines_per_file
        end_idx = start_idx + lines_per_file
        output_file = f"{output_prefix}_{i + 1}.tsv"

        # Extraire la portion du DataFrame
        df_slice = df.slice(start_idx, lines_per_file)

        # Sauvegarder la portion dans un fichier TSV
        df_slice.write_csv(output_file, separator="\t")

# Exemple d'utilisation
split_tsv_with_polars('NEW_contexte_animaux.csv', 'animaux', 2000)
