from openai import OpenAI
import re
import polars as pl
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

load_dotenv()

MODEL="gpt-4o-mini"
API_KEY = os.getenv('OPEN_AI_KEY')

client = OpenAI(api_key=)

df = pl.read_csv("ENTITES_contexte_plantes.csv", separator='\t')


df = df.with_columns(
    pl.struct(["truncated_sentence", "token_lexique"]).map_elements(
        lambda cols: cols["truncated_sentence"].replace(
            cols["token_lexique"],
            f"<plante>{cols['token_lexique']}</plante>"
        ),
        return_dtype=pl.Utf8
    ).alias("phrase_balisee")
)

# Création des batches (par roman)
#grouped = df.group_by("fichier")

df = df.sort("fichier")


preprompt = (
	f"Vous êtes spécialiste en sémantique. Vous allez déterminer si des termes désignant des plantes ou parties de plantes (fruit, fleur, etc.) ont un usage littéral ou figuré. Vous attribuerez donc au choix une première étiquette 'littéral' ou 'figuré'. Si le terme ne désigne en fait pas un élément du règne Plantae, indiquer 'X'. Si le contexte donné est insuffisant pour trancher ou ambigu, indiquer '?'. Une fois cet usage déterminé, vous allez spécifier une sous-catégorie selon les critères suivants :\n"
		f"1) Pour les usages LITTÉRAUX :\n"
	f"* Si la plante citée est une plante cultivée, un produit maraîcher ou un produit naturel destiné à la consommation humaine ou animale, la sous-catégorie est DENRÉE."
	f"* Si la plante citée est utilisée dans le contexte comme épice, condiment ou aromatique, la sous-catégorie est CONDIMENT."
	f"* Si la plante citée fait référence à une matière première utilisée par l'homme, la sous-catégorie est MATIÈRE."
	f"* Dans les autres cas, indiquer AUTRE.\n"
	f"2) Pour les usages FIGURÉS :\n"
	f"* Si la plante est l'objet d'une comparaison, indiquer COMPARAISON."
	f"* Si la plante sert à établir une métaphore, indiquer MÉTAPHORE."
	f"* Si la plante fait partie d'une expression figée ou d'une locution adverbiale ne faisant pas directement référence au végétal, indiquer IDIOMATIQUE."
	f"* Si la plante est une représentation abstraite comme une image, un objet ou encore une couleur, indiquer ABSTRACT.\n"
	f"* Dans les autres cas, indiquer AUTRE.\n"
	f"Pour la réponse, vous suivrez strictement la structure contenue dans la balise <reponse> de l'exemple ci-dessous."
	f"<exemple>\n"
	f"<phrase id=\"1\">Un halo mouillé dans la nuit des champs de <plante>betterave</plante>.</phrase>\n"
	f"<phrase id=\"2\">Elle appelle ma mère son petit <plante>pruneau</plante>.</phrase>\n"
	f"<phrase id=\"3\">Serveuses en déshabillé, talons hauts, petit tablier blanc et <plante>camélia</plante> en tissu dans les cheveux.</phrase>\n"
	f"<phrase id=\"4\">Une étoffe de <plante>lin</plante> blanc recouvrait une partie de son torse.</phrase>"
	f"<reponse>"
	f"<usage id=\"1\">littéral</usage><categorie>DENRÉE</categorie><explication>La betterave est ici évoquée dans le contexte de sa culture (champs de betterave), probablement pour un usage alimentaire.</explication>"
	f"<usage id=\"2\">figuré</usage><categorie>IDIOMATIQUE</categorie><explication>Le terme pruneau est ici employé comme terme d'affection, et ne fait donc pas directement référence au fruit.</explication>"
	f"<usage id=\"3\">figuré</usage><categorie>ABSTRACT</categorie><explication>Le camélia en tissu est un accessoire vestimentaire, il s'agit donc d'une représentation abstraite de la plante.</explication>"
	f"<usage id=\"3\">littéral</usage><categorie>MATIÈRE</categorie><explication>Le lin désigne ici le matériau ayant servi à fabriquer l'étoffe dont il est question. Il s'agit bien d'un usage littéral car c'est bien la plante de lin qui est employée pour fabriquer l'étoffe.</explication>"
	f"</reponse>"
	f"</exemple>"
	)

def parse_response(xml_string: str) -> pl.DataFrame:
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError as e:
        raise ValueError(f"Chaîne XML invalide : {e}")

    rows = []
    children = list(root)

    # on avance de 3 en 3 mais en vérifiant qu’on a bien un triplet
    for i in range(0, len(children), 3):
        if i + 2 >= len(children):
            # on saute le bloc incomplet
            continue

        usage, categorie, explication = children[i:i+3]

        rows.append({
            "id": usage.attrib.get("id", ""),
            "label": (usage.text or "").strip(),
            "categorie_metaphore": (categorie.text or "").strip(),
            "explication": (explication.text or "").strip()
        })

    return pl.DataFrame(rows)



chunk_size = 7

# Découper le df en batches de taille chunk_size
batches = [df[i:i + chunk_size] for i in range(0, len(df), chunk_size)]

batch_id = 1
batch_count = 1
list_dfs = []

for sub_batch in batches:

	phrases = list(sub_batch['phrase_balisee'])
		
	prompt_client = ""
		
	for phrase in phrases:
		phrase = "<phrase id=" + str(batch_id) + ">" + phrase + "</phrase>"
		prompt_client += phrase + '\n'
		batch_id += 1

	messages = [{"role": "system", "content": preprompt}]
	
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

	
	df_batch = pl.concat([sub_batch, df_new], how="horizontal")

	list_dfs.append(df_batch)
	
	print(batch_id)
	

	if batch_count % 10 == 0:
		df_all = pl.concat(list_dfs, how="vertical")
		#df_all = df_all.drop("id")

		df_all.write_csv(f"analyse_gpt_metaphor_{batch_id}.csv", separator='\t')
		
		list_dfs = []

	batch_count += 1
