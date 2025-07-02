#!/bin/bash

PATH_LEXICON="../lexiques/loterre"
OUTPUT_DIR="../resultats/$(date +%F)_LOTERRE"

ls "../CORPUS_TOTAL/" > "../liste_fichiers_all.txt"

mkdir "$OUTPUT_DIR"

echo "Extraction des occurrences..."

grep -Fwo -f "$PATH_LEXICON" ../CORPUS_TOTAL/*.txt > "$OUTPUT_DIR/occurrences.txt";

cut -d':' -f2 "$OUTPUT_DIR/occurrences.txt" | sort | uniq -ci | sort -rn > "$OUTPUT_DIR/counts.txt";

cut -d':' -f1 "$OUTPUT_DIR/occurrences.txt" | sort | uniq -c | sort -rn > "$OUTPUT_DIR/nb_termes_par_texte.txt"

sed -i 's/^ *//g' "$OUTPUT_DIR/nb_termes_par_texte.txt"

sed -i 's|../CORPUS_TOTAL/||g' "$OUTPUT_DIR/occurrences.txt"
sed -i 's|../CORPUS_TOTAL/||g' "$OUTPUT_DIR/nb_termes_par_texte.txt"

cat "$OUTPUT_DIR/occurrences.txt" | sort | uniq -ci | sort -rn > "$OUTPUT_DIR/nb_occurrences_par_texte.txt"

echo "Décompte des occurrences..."

while read -r filename; do echo "$filename" >> "$OUTPUT_DIR/nb_uniq_par_texte.txt"; grep -c "$filename" "$OUTPUT_DIR/nb_occurrences_par_texte.txt" >> "$OUTPUT_DIR/nb_uniq_par_texte.txt"; done < ../liste_fichiers_all.txt

echo "Construction de la table de résultats..."
python build_table.py $OUTPUT_DIR

echo "Extraction du contexte des occurrences..."
python grep_contexte.py "$OUTPUT_DIR/corpus_analyse_$(date +%F).csv" "$OUTPUT_DIR/contexte.csv"

# Filtrage des occurrences inutiles
python filter_tokens_loterre.py "$OUTPUT_DIR/contexte.csv" "$OUTPUT_DIR/1_contexte_filtre.csv"

# Elimination des doublons (souris/chauve-souris, etc)
python remove_duplicates.py "$OUTPUT_DIR/1_contexte_filtre.csv" "$OUTPUT_DIR/2_contexte_filtre_specialise.csv"

