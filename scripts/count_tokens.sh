#!/bin/bash

for f in ../TOKENS_Bestsellers/*_tokens.txt;
do
	filename="${f##*/}";
	toks=$(sed '/\tSPACE\t/d' "$f" | sed '/^[[:space:]]*$/d' | grep -v 'PUNCT' | wc -l);
	lems=$(sed '/\tSPACE\t/d' "$f" | sed '/^[[:space:]]*$/d' | grep -v 'PUNCT' | cut -f3 | sort | uniq | wc -l);
	all="$filename,$toks,$lems";
	echo "File,nb_tokens,nb_lemmes" >> ../resultats/decomptes_tokens.csv
	echo "$all" >> ../resultats/decomptes_tokens.csv;
done
