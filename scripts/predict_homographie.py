import sys
import torch
import torch.nn as nn
from transformers import FlaubertTokenizer, FlaubertModel
import os
import pandas as pd
from tqdm import tqdm

# Fichier à analyser
if len(sys.argv) < 3:
	print("Usage : python predict_homographie.py contexte.csv homographie_annotee.csv")
	exit(1)
infile = sys.argv[1]
outfile = sys.argv[2]

# Charger le modèle
class FlaubertPhraseWordClassifier(nn.Module):
    def __init__(self, num_labels):
        super(FlaubertPhraseWordClassifier, self).__init__()
        self.flaubert = FlaubertModel.from_pretrained(model_dir)
        self.classifier = nn.Linear(self.flaubert.config.hidden_size * 2, num_labels)

    def forward(self, input_ids_phrase, attention_mask_phrase, input_ids_word, attention_mask_word):
        outputs_phrase = self.flaubert(input_ids=input_ids_phrase, attention_mask=attention_mask_phrase)
        phrase_embedding = outputs_phrase.last_hidden_state[:, 0, :]

        outputs_word = self.flaubert(input_ids=input_ids_word, attention_mask=attention_mask_word)
        word_embedding = outputs_word.last_hidden_state[:, 0, :]

        combined_embedding = torch.cat((phrase_embedding, word_embedding), dim=1)

        logits = self.classifier(combined_embedding)

        return logits

def tokenize_pair(tokenizer, phrase, word):
    # Tokeniser la phrase
    phrase_inputs = tokenizer(phrase, return_tensors='pt', padding=True, truncation=True)
    
    # Tokeniser le mot
    word_inputs = tokenizer(word, return_tensors='pt', padding=True, truncation=True)
    
    return phrase_inputs, word_inputs

# Fonction pour prédire la classe d'une paire mot-phrase
def predict_pair(model, tokenizer, phrase, word):
    phrase_inputs, word_inputs = tokenize_pair(tokenizer, phrase, word)
    
    # Passer les données dans le modèle
    with torch.no_grad():
        logits = model(
            input_ids_phrase=phrase_inputs['input_ids'],
            attention_mask_phrase=phrase_inputs['attention_mask'],
            input_ids_word=word_inputs['input_ids'],
            attention_mask_word=word_inputs['attention_mask']
        )
    
    # Obtenir la classe prédite (argmax sur les logits)
    predicted_class = torch.argmax(logits, dim=1).item()
    
    return predicted_class
    
    
df = pd.read_csv(infile, sep='\t')

ambiguite_mammifere = ['paresseux', 'zèbres', 'makis', 'lama', 'lapins', 'chiens', 'capucin', 'vaches', 'girafe', 'fouine', 'lamas', 'dingo', 'cheval', 'chien', 'taupe', 'cobayes', 'souris', 'chèvres', 'capucins', 'girafes', 'cobaye', 'zèbre', 'élan', 'élans', 'maki', 'dauphin', 'dingos', 'lapin', 'dauphins', 'vache', 'chèvre']

ambiguite_oiseau = ['marabouts', 'chouette', 'caille', 'pic', 'pics', 'manchot', 'manchots', 'harpie', 'cailles', 'pie', 'pies', 'aigrette', 'martinet', 'pigeons', 'coucous', 'grue', 'coucou', 'chouettes', 'aigrettes', 'poules', 'pigeon', 'martinets', 'harpies', 'échasses', 'grues', 'poule']

ambiguite_poisson = ['sars', 'sar', 'sole', 'maquereaux', 'tanche', 'raies', 'bar', 'raie', 'perche', 'perches', 'bogues', 'maquereau', 'soles', 'bars']

ambiguite_insecte = ['bourdon', 'pou', 'papillons', 'papillon', 'puce', 'puces', 'poux']


# Appliquer les modèles

res = []
print("{} éléments à traiter".format(len(df['token_lexique'])))

for token, sent in tqdm(zip(df['token_lexique'], df['truncated_sentence']), desc="Processing tokens"):
    if token in ambiguite_mammifere:
        model_dir = "../models/flaubert_model_MAMMIFERES"
    elif token in ambiguite_oiseau:
        model_dir = "../models/flaubert_model_OISEAUX"
    elif token in ambiguite_poisson:
        model_dir = "../models/flaubert_model_POISSONS"
    elif token in ambiguite_insecte:
        model_dir = "../models/flaubert_model_INSECTES"
    else:
        res.append('x')
        continue
    
    tokenizer = FlaubertTokenizer.from_pretrained(model_dir)
    model = FlaubertPhraseWordClassifier(num_labels=2)
    model.classifier.load_state_dict(torch.load(os.path.join(model_dir, 'classifier_weights.bin'), map_location=torch.device('cpu')))
    model.eval()
    res.append(predict_pair(model, tokenizer, sent, token))

df['prediction_model'] = res

df.to_csv(outfile, sep='\t', index=False)

