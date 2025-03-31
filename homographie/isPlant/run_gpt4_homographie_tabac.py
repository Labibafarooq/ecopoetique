from openai import OpenAI
import os
import pandas as pd

def analyse_token_phrase(phrase):
    try:
        # Prompt pour guider GPT-4
        prompt = (
            f"Le mot \"tabac\' peut désigner une plante originaire d'Amérique centrale, ou, par métonymie, une substance à fumer ou un établissement."
            f"Quelle est l'utilisation du mot dans la phrase suivante :\n"
            f"\"{phrase}\"\n"
            f"Veuillez répondre par un des mots-clés \"plante\", \"substance\", \"établissement\" ou \"autre\" avant de fournir une brève explication."
        )

        # Appel de l'API GPT-4
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "Vous êtes un assistant linguistique spécialisé en sémantique. Vous allez déterminer si un terme se réfère à un végétal ou non. Attention, regardez bien le contexte pour décider."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.2 # la réponse doit être quasi déterministe
        )

        # Extraction de la réponse
        content = response.choices[0].message.content

        # Par exemple, extraire "référentiel" ou "métaphorique" de la réponse
        result = {"decision": None, "explanation": content}
        if "établissement" in content[:15].lower():
            result["decision"] = "établissement"
        elif "substance" in content[:10].lower():
            result["decision"] = "substance"
        elif "plante" in content[:10].lower():
            result["decision"] = "plante"
        elif "autre" in content[:10].lower():
            result["decision"] = "autre"
        else:
            result["decision"] = "x"

        return result
    except Exception as e:
        print(f"Erreur lors de l'analyse de la phrase ({phrase}): {e}")
        return {"decision": None, "explanation": str(e)}
        

MODEL="gpt-4o-mini"
key = "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"
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", key))

df = pd.read_csv("tabac.csv", sep='\t')

results = df.apply(lambda row: analyse_token_phrase(row['truncated_sentence']), axis=1)
df['decision'] = results.apply(lambda x: x['decision'])
df['explanation'] = results.apply(lambda x: x['explanation'])

# Enregistre les résultats
df.to_csv('tabac.csv', sep='\t', index=False)
