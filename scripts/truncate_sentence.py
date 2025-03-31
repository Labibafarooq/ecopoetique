import sys
import pandas as pd
import re

def truncate_sentence(row, max_length=50):
    word = row['token_lexique']
    contexte = row['contexte']
    
    words = re.findall(r"\w+|[.,!?;]", contexte)  # Séparer ponctuation
    token_words = word.split()
    
    if len(words) > max_length:
        # Trouver l'index du premier mot du token dans la phrase
        for i in range(len(words)):
            if words[i:i+len(token_words)] == token_words:
                start_idx = max(0, i - max_words // 2)
                end_idx = min(len(words), i + len(token_words) + max_words // 2)
                return " ".join(words[start_idx:end_idx])
    return contexte


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage : python truncate_sentence.py input.csv output.csv")
        exit(1)
    
    infile = sys.argv[1]
    outfile = sys.argv[2]
    
    df = pd.read_csv(infile, sep='\t')
    
    df['truncated_sentence'] = df.apply(truncate_sentence, axis=1)
    df.to_csv(outfile, sep='\t', index=False)
