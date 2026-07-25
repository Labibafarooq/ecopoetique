"""
Creates gold set templates for plants and Loterre
by randomly extracting sentences from the corpus files.
Riccardo just needs to fill in the 'consensus' column.
Same structure as GOLD_litteralite_animaux.csv:
fichier | token_lexique | contexte | consensus
"""

import csv
import random

random.seed(42)  # reproducible

PLANTES_INPUT  = "../resultats/corpus_principal/ENTITES_contexte_plantes.csv"
LOTERRE_INPUT  = "../resultats/corpus_principal/ENTITES_contexte_loterre.csv"

PLANTES_OUTPUT  = "GOLD_litteralite_plantes.csv"
LOTERRE_OUTPUT  = "GOLD_litteralite_loterre.csv"

N_SAMPLES = 200  # number of sentences to extract for each

def create_template(input_file, output_file, n_samples):
    print(f"\nReading {input_file}...")

    rows = []
    with open(input_file, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        fieldnames = reader.fieldnames
        print(f"  Columns: {fieldnames}")
        for row in reader:
            rows.append(row)

    print(f"  Total rows: {len(rows)}")

    # Check which column has the sentence
    # Could be 'truncated_sentence' or 'contexte'
    sentence_col = None
    for col in ["truncated_sentence", "contexte", "phrase"]:
        if col in rows[0]:
            sentence_col = col
            break

    token_col = "token_lexique" if "token_lexique" in rows[0] else "token"
    file_col = "fichier" if "fichier" in rows[0] else "file"

    print(f"  Using sentence column: '{sentence_col}', token column: '{token_col}'")

    # Filter out very short or very long sentences
    filtered = []
    for row in rows:
        sentence = row.get(sentence_col, "").strip()
        if 20 < len(sentence) < 500:  # reasonable length
            filtered.append(row)

    print(f"  After filtering: {len(filtered)} rows")

    # Random sample
    sample = random.sample(filtered, min(n_samples, len(filtered)))
    print(f"  Sampled: {len(sample)} rows")

    # Write output in same format as animal gold set
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        # Header
        writer.writerow(["fichier", "token_lexique", "contexte", "consensus"])
        # Rows — consensus is empty for Riccardo to fill
        for row in sample:
            fichier = row.get(file_col, "").strip()
            token = row.get(token_col, "").strip()
            contexte = row.get(sentence_col, "").strip()
            # Clean up contexte — remove newlines
            contexte = contexte.replace("\n", " ").replace("\r", " ").strip()
            writer.writerow([fichier, token, contexte, ""])

    print(f"  ✅ Saved to {output_file}")

def main():
    print("Creating gold set templates for Riccardo to annotate...")
    print(f"Extracting {N_SAMPLES} random sentences from each corpus")

    create_template(PLANTES_INPUT,  PLANTES_OUTPUT,  N_SAMPLES)
    create_template(LOTERRE_INPUT,  LOTERRE_OUTPUT,  N_SAMPLES)

    print("\n✅ Done! Two files created:")
    print(f"  - {PLANTES_OUTPUT}")
    print(f"  - {LOTERRE_OUTPUT}")
    print("\nRiccardo needs to fill in the 'consensus' column with:")
    print("  référentiel — literal use")
    print("  figuré      — figurative use")
    print("  X           — unclear/ambiguous")

if __name__ == "__main__":
    main()
