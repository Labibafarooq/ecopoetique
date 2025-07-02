#!/bin/bash

PATH_LEXICON="/home/johanna/Documents/DigEco/foret-numerique/thesaurus/noms_scientif_lowercase.txt"
OUTPUT_DIR="../resultats/$(date +%F)_TAXONS_lower"

#ls "../CORPUS_TOTAL/" > "../liste_fichiers.txt"

mkdir "$OUTPUT_DIR"

echo "Extraction des occurrences..."

grep -Fwo -f "$PATH_LEXICON" ../RECENT/*.txt > "$OUTPUT_DIR/occurrences.txt";

cut -d':' -f2 "$OUTPUT_DIR/occurrences.txt" | sort | uniq -ci | sort -rn > "$OUTPUT_DIR/counts.txt";

cut -d':' -f1 "$OUTPUT_DIR/occurrences.txt" | sort | uniq -c | sort -rn > "$OUTPUT_DIR/nb_termes_par_texte.txt"

sed -i 's/^ *//g' "$OUTPUT_DIR/nb_termes_par_texte.txt"

sed -i 's|../CORPUS_TOTAL/||g' "$OUTPUT_DIR/occurrences.txt"
sed -i 's|../CORPUS_TOTAL/||g' "$OUTPUT_DIR/nb_termes_par_texte.txt"

cat "$OUTPUT_DIR/occurrences.txt" | sort | uniq -ci | sort -rn > "$OUTPUT_DIR/nb_occurrences_par_texte.txt"

echo "Décompte des occurrences..."

while read -r filename; do echo "$filename" >> "$OUTPUT_DIR/nb_uniq_par_texte.txt"; grep -c "$filename" "$OUTPUT_DIR/nb_occurrences_par_texte.txt" >> "$OUTPUT_DIR/nb_uniq_par_texte.txt"; done < ../liste_recents.txt

#echo "Construction de la table de résultats..."
#python build_table.py $OUTPUT_DIR

#echo "Extraction du contexte des occurrences..."
#python grep_contexte.py "$OUTPUT_DIR/corpus_analyse_$(date +%F).csv" "$OUTPUT_DIR/contexte.csv"


