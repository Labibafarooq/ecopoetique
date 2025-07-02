import sys
import pandas as pd

# Format du fichier en entrée : dataframe contenant la colonne truncated_sentence

if len(sys.argv) < 2:
    print("Usage : python balise_phrases.py filename.csv")
    exit(1)
else:
    INPUT_FILE = sys.argv[1]

def baliser_phrase(row):
    phrase = row["truncated_sentence"]
    animal = row["token_lexique"]
    
    if animal:
        # Baliser l'animal dans la phrase
        phrase_balisee = phrase.replace(animal, f"<animal>{animal}</animal>")

        phrase_balisee = f"<phrase>{phrase_balisee}</phrase>"

        return phrase_balisee
    else:
        return ''


df = pd.read_csv(INPUT_FILE, sep='\t')
df["phrase_balisee"] = df.apply(baliser_phrase, axis=1)
df.to_csv(INPUT_FILE, sep='\t', index=False)
