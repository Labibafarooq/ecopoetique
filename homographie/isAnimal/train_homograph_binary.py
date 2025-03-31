import pandas as pd
import torch
import torch.nn as nn
from transformers import CamembertTokenizer, CamembertModel, FlaubertTokenizer, FlaubertModel, Trainer, TrainingArguments
from sklearn.model_selection import train_test_split
from datasets import Dataset
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt
import os

# ARCHITECTURE
class FlaubertPhraseWordClassifier(nn.Module):
    def __init__(self, num_labels):
        super(FlaubertPhraseWordClassifier, self).__init__()
        self.flaubert = FlaubertModel.from_pretrained('flaubert/flaubert_base_uncased')
        self.classifier = nn.Linear(self.flaubert.config.hidden_size * 2, num_labels)
        self.loss_fct = nn.CrossEntropyLoss()

    def forward(self, input_ids_phrase, attention_mask_phrase, input_ids_word, attention_mask_word, labels=None):
        # Passer la phrase à FlauBERT
        outputs_phrase = self.flaubert(input_ids=input_ids_phrase, attention_mask=attention_mask_phrase)
        # Extraire le vecteur du premier token (comme [CLS]) pour la phrase
        phrase_embedding = outputs_phrase.last_hidden_state[:, 0, :]  # [batch_size, hidden_size]

        # Passer le mot à travers FlauBERT
        outputs_word = self.flaubert(input_ids=input_ids_word, attention_mask=attention_mask_word)
        # Extraire le vecteur du premier token (comme [CLS]) pour le mot
        word_embedding = outputs_word.last_hidden_state[:, 0, :]  # [batch_size, hidden_size]

        # Concaténer les deux embeddings (phrase et mot)
        combined_embedding = torch.cat((phrase_embedding, word_embedding), dim=1)  # [batch_size, hidden_size * 2]

        # Passer à travers le classifieur
        logits = self.classifier(combined_embedding)

        # Si les labels sont fournis, calculer la perte
        if labels is not None:
            labels = labels.long()
            loss = self.loss_fct(logits, labels)
            return loss, logits
        else:
            return logits
            
# HYPERPARAMETRES
training_args = TrainingArguments(
    output_dir='./models',
    evaluation_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=20,
    weight_decay=0.01,
)


# EVALUATION
def compute_metrics(p):
    # Convertir les prédictions en tensor PyTorch
    preds = torch.tensor(p.predictions) if not isinstance(p.predictions, torch.Tensor) else p.predictions
    labels = torch.tensor(p.label_ids) if not isinstance(p.label_ids, torch.Tensor) else p.label_ids

    preds = torch.argmax(preds, axis=1)

    accuracy = (preds == labels).float().mean().item()

    return {"accuracy": accuracy}


"""
 MAIN

"""

# Charger les données depuis un fichier CSV
df = pd.read_csv('homographie_train.csv', sep='\t')
df = df.sample(frac=1).reset_index(drop=True)

# Fonction de tokenisation de la phrase et du mot
def tokenize_function(tokenizer, examples):
    # Tokeniser la phrase complète
    phrase_encoding = tokenizer(examples['truncated_sentence'], padding='max_length', truncation=True, max_length=128)

    # Tokeniser le mot séparément
    word_encoding = tokenizer(examples['token_lexique'], padding='max_length', truncation=True, max_length=10)

    return {
        'input_ids_phrase': phrase_encoding['input_ids'],
        'attention_mask_phrase': phrase_encoding['attention_mask'],
        'input_ids_word': word_encoding['input_ids'],
        'attention_mask_word': word_encoding['attention_mask'],
        'label': examples['label']
    }

# Diviser les données en train et test
train_df, test_df = train_test_split(df, test_size=0.2)
train_df = train_df.reset_index()
test_df = test_df.reset_index()

with open("rapport.md", 'a') as fo:
	fo.write("\nDonnées d'entraînement : {}\n".format(len(train_df)))
	fo.write(str(train_df['label'].value_counts()))

	fo.write("Données de test : {}\n".format(len(test_df)))
	fo.write(str(test_df['label'].value_counts()))

# Convertir les dataframes en Dataset de Hugging Face
train_dataset = Dataset.from_pandas(train_df)
test_dataset = Dataset.from_pandas(test_df)

# Charger le tokenizer FlauBERT
flaubert_tokenizer = FlaubertTokenizer.from_pretrained('flaubert/flaubert_base_uncased', use_auth_token=True)

# Tokeniser les jeux de données
train_dataset_flaubert = train_dataset.map(lambda x: tokenize_function(flaubert_tokenizer, x), batched=True)
test_dataset_flaubert = test_dataset.map(lambda x: tokenize_function(flaubert_tokenizer, x), batched=True)

# Spécifier les colonnes à conserver
train_dataset_flaubert.set_format(type='torch', columns=['input_ids_phrase', 'attention_mask_phrase', 'input_ids_word', 'attention_mask_word', 'label'])
test_dataset_flaubert.set_format(type='torch', columns=['input_ids_phrase', 'attention_mask_phrase', 'input_ids_word', 'attention_mask_word', 'label'])

# Initialiser le modèle
flaubert_model = FlaubertPhraseWordClassifier(num_labels=2)

# Initialiser le Trainer pour FlauBERT
trainer_flaubert = Trainer(
    model=flaubert_model,
    args=training_args,
    train_dataset=train_dataset_flaubert,
    eval_dataset=test_dataset_flaubert,
    compute_metrics=compute_metrics,
)

# Entraîner le modèle
trainer_flaubert.train()

# Évaluer le modèle
eval_results_flaubert = trainer_flaubert.evaluate()
print("Résultats FlauBERT :", eval_results_flaubert)

# Prédictions sur le jeu de test
predictions_flaubert = trainer_flaubert.predict(test_dataset_flaubert)

# Convertir les prédictions en labels (argmax)
preds = torch.argmax(torch.tensor(predictions_flaubert.predictions), axis=1)
true_labels = torch.tensor(predictions_flaubert.label_ids)

# Calculer la matrice de confusion
cm = confusion_matrix(true_labels, preds)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=[0,1])
disp.plot(cmap=plt.cm.Blues)
plt.title("Matrice de confusion - FlauBERT")
plt.savefig('confusion_flaubert.png')


# Sauvegarder le modèle FlauBERT et le classifieur séparément
output_dir = "./flaubert_model_binary"
os.makedirs(output_dir, exist_ok=True)

# Sauvegarder le modèle sous-jacent FlauBERT
flaubert_model.flaubert.save_pretrained(output_dir)

# Sauvegarder les poids du classifieur (couche linéaire)
torch.save(flaubert_model.classifier.state_dict(), os.path.join(output_dir, 'classifier_weights.bin'))

# Sauvegarder le tokenizer
flaubert_tokenizer.save_pretrained(output_dir)

print(f"FlauBERT modèle sauvegardé dans {output_dir}")
