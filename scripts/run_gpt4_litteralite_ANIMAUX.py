from openai import OpenAI
import os
import re
import polars as pl
from glob import glob
load_dotenv()

MODEL="gpt-4o-mini"
API_KEY = os.getenv('OPEN_AI_KEY')

client = OpenAI(api_key=API_KEY)


# Préprompt
preprompt = (
	f"Vous êtes spécialiste en sémantique. Vous allez déterminer si des termes désignant des animaux ont un usage littéral ou figuré. Vous attribuerez donc au choix une première étiquette 'littéral' ou 'figuré'. Si le terme ne désigne en fait pas un animal, indiquer 'X'. Si le contexte donné est insuffisant pour trancher ou ambigu, indiquer '?'. Une fois cet usage déterminé, vous allez spécifier une sous-catégorie selon les critères suivants :\n"
	f"1) Pour les usages LITTÉRAUX :\n"
	f"* Si l'animal cité est inanimé et fait référence à de la nourriture ou à une matière première utilisée par l'homme, la sous-catégorie est MATIÈRE."
	f"* Dans les autres cas, indiquer AUTRE.\n"
	f"2) Pour les usages FIGURÉS :\n"
	f"* Si l'animal est l'objet d'une comparaison, indiquer COMPARAISON.\n"
	f"* Si l'animal sert à établir une métaphore, indiquer MÉTAPHORE.\n"
	f"* Si l'animal cité fait partie d'une locution adverbiale (par exemple « entre chien et loup ») ou d'une expression idiomatique ne faisant pas directement référence à l'animal (par exemple « tu es une bécasse », ou « ma puce »), indiquer IDIOMATIQUE.\n"
	f"* Si l'animal cité est une représentation abstraite comme une statue, une image, une peluche, ou encore une couleur, indiquer ABSTRACT.\n"
	f"* Dans les autres cas, indiquer AUTRE.\n"
	f"Pour la réponse, vous suivrez strictement la structure contenue dans la balise <reponse> de l'exemple ci-dessous."
	f"<exemple>\n"
	f"<phrase id=\"1\">Sur la rive droite, un grand <animal>cerf</animal> dévalait le chemin de halage.</phrase>\n"
	f"<phrase id=\"2\">Il livre les barquettes de filets de <animal>colin</animal></phrase>\n"
	f"<phrase id=\"3\">J’étais devenu un caméléon, d’ici et d’ailleurs.</phrase>\n"
	f"<reponse>"
	f"<usage id=\"1\">littéral</usage><categorie>AUTRE</categorie><explication>Il est question ici d'un animal animé, l'usage est bien référentiel.</explication>"
	f"<usage id=\"2\">littéral</usage><categorie>MATIÈRE</categorie><explication>L'animal est ici mentionné pour son rôle de nourriture.</explication>
	f"<usage id=\"3\">figuré</usage><categorie>MÉTAPHORE</categorie><explication>La caméléon désigne ici par métaphore une personne capable de s'adapter à son environnement comme le fait l'animal changeant de couleur. Il ne s'agit pas littéralement d'un animal.</explication>"
	f"</reponse>"
	f"</exemple>"
	)
	
def parse_response(response):
	# Extraire tous les blocs <reponse>
	blocs = re.findall(r"<reponse>(.*?)</reponse>", response, re.DOTALL)

	# Extraire les infos de chaque blocs
	data = []
	for bloc in blocs:
		match = re.search(r'<usage id="(\d+)">(.*?)</usage>.*?<categorie>(.*?)</categorie><explication>(.*?)</explication>', bloc, re.DOTALL)
		if match:
			id_, label, categorie, explication = match.groups()
			data.append({
				"id": int(id_),
				"label": label.strip(),
				"categorie_metaphore":categorie.strip(),
				"explication": explication.strip()
			})
		else:
			data.append({
				"id": None,
				"label": '',
				"categorie_metaphore": '',
				"explication": response
			})


	return pl.DataFrame(data)
	

for filename in glob("./batches_animaux/*.csv"):
	# Lecture du fichier
	df = pl.read_csv(filename, separator='\t')
	chunk_size = 7

	# Découper le df en batches de taille chunk_size
	batches = [df[i:i + chunk_size] for i in range(0, len(df), chunk_size)]

	list_dfs = []

	for df_batch in batches:
		# Récupération des phrases balisées (=> prompt user)
		phrases = list(df_batch['phrase_balisee'])

		# Initialisation de la conversation
		messages = [{"role": "system", "content": preprompt}]

		prompt_client = ""
		
		for i, phrase in enumerate(phrases):
			phrase = phrase.replace("<phrase>", "<phrase id=" + str(i) + ">")
			prompt_client += phrase + '\n'

		messages.append({"role": "user", "content": prompt_client})

		 # Appel du modèle
		response = client.chat.completions.create(
			model=MODEL,
			messages=messages,
			temperature=0.1,
			max_tokens=4000
		)

		msg_content = response.choices[0].message.content

		df_new = parse_response(msg_content)

		# Si tout va bien df_new a le même nombre de lignes que df_batch
		if len(df_batch) != len(df_new):
			print(df_batch)
			print(df_new)
			name = df_batch.row(0)[0]
			name = name.replace(".txt", "")
			name += "_response.txt"
			with open(name, 'w') as f:
				f.write(msg_content)
			print("Les Dataframes n'ont pas le même nombre de lignes.")

		list_dfs.append(pl.concat([df_batch, df_new], how="horizontal"))

	df_all = pl.concat(list_dfs, how="vertical")
	df_all = df_all.drop("id")

	df_all.write_csv(filename, separator='\t')

