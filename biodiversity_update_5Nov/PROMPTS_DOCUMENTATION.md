# Prompts utilisés par tâche — compilation pour Riccardo (2026-11-05)

Extraction verbatim des scripts de production actuels. Chaque section est
copiée telle quelle depuis le fichier source indiqué (aucune paraphrase).

---

## Task 0 — Narratologie (map-reduce, qwen3:30b)

Source : `narratologie/run_task0_mapreduce_v7_newgold.py`

```python
CRITERIA_DEFS = """
TYPE DE NARRATEUR
• NAR_AUTOD : le narrateur EST le protagoniste principal (dit "je" et vit l'histoire).
• NAR_TEM   : le narrateur dit "je/nous" mais est personnage secondaire ou témoin.
• NAR_EXT   : le narrateur est ABSENT de l'histoire, raconte à la 3ème personne.
• NAR_VAR   : le TYPE de narrateur lui-même change de façon structurée au cours
              du roman (ex: alterne entre un narrateur-personnage "je" dans
              certains chapitres/sections et un narrateur externe à la 3ème
              personne dans d'autres) — ne pas confondre avec un simple
              changement de PERSONNAGE focalisé (qui reste du ressort de
              FOCALISATION) : ici c'est la NATURE même du narrateur
              (autodiégétique / témoin / externe) qui varie selon les parties.
              ⚠ RARE : choisis NAR_VAR UNIQUEMENT si narrator_voice passe
              RÉELLEMENT de first_person à third_person (ou l'inverse) entre
              au moins 2 sections distinctes. Un simple changement de
              personnage focalisé (même type de voix partout) n'est PAS
              NAR_VAR -- c'est FOCALISATION. Si tu hésites, NE choisis PAS
              NAR_VAR ; choisis le type dominant parmi les 3 autres.

MODE NARRATIF DOMINANT
• MOD_EVT  : l'action, les faits, les décisions dominent — même s'il y a des pensées.
             ⚠ La simple présence de pensées ne suffit pas pour choisir MOD_INTR.
• MOD_DESC : les descriptions de décors, objets, sensations, ambiances dominent.
• MOD_INTR : les réflexions intérieures et états d'âme DOMINENT CLAIREMENT sur l'action.
             Choisir MOD_INTR uniquement si l'action est clairement secondaire dans
             la MAJORITÉ des sections, pas seulement quelques-unes.
• MOD_DIA  : les échanges verbaux (dialogues) ou la polyphonie de voix multiples
             structurent et dominent le récit de manière prédominante.
• MOD_MIX  : aucun mode ne domine — équilibre stable entre plusieurs modes.
             ⚠ Si les 9 sections montrent des dominant_mode DIFFÉRENTS d'une
             section à l'autre (certaines action_events, d'autres introspection
             ou description) SANS qu'un seul mode ne l'emporte sur l'ENSEMBLE
             du roman, choisis MOD_MIX -- ne force PAS MOD_INTR juste parce
             que quelques sections individuelles penchent vers l'introspection.

RÉGIME NARRATIF — vérifie dans cet ordre, en te basant sur L'ENSEMBLE des sections
1. Le narrateur ou un personnage focal est-il une entité NON-HUMAINE dotée d'une
   conscience narrative propre (animal, objet, entité collective, etc.), de façon
   récurrente à travers plusieurs sections ? OU des éléments surnaturels/inexplicables
   perturbent-ils le réel dans plusieurs sections ? → REG_FANT
2. Sinon, le monde est-il clairement futuriste, dystopique, ou transformé politiquement/
   technologiquement par rapport au réel actuel ? → REG_SPEC
3. Sinon, la MAJORITÉ des sections adoptent-elles un ton confessionnel/réflexif soutenu
   sur une vie qui semble être celle, réelle ou proche du réel, du narrateur — que ce
   soit dit explicitement (référence à l'écriture du livre, à l'identité de l'auteur)
   ou simplement par une posture subjective et réflexive constante ? → REG_AUTO
4. Sinon → REG_REAL

ORGANISATION DE L'ESPACE — compare les lieux mentionnés dans toutes les sections
• ESP_UNIT : même environnement général dans toutes les sections (même ville,
             bâtiment, région — même avec des sous-lieux différents).
• ESP_FRAG : lieux GÉOGRAPHIQUEMENT DISTINCTS entre sections (villes/pays/régions
             différents sans cohérence spatiale forte).
• ESP_ITIN : les personnages sont EN DÉPLACEMENT CONTINU — le voyage est central.
• ESP_IMAG : l'espace est partiellement ou totalement inventé, irréaliste, symbolique.

NATURE DE L'INTRIGUE — lis les key_observation de TOUTES les sections dans l'ordre
(section 1 → section {n_chunks}) et juge l'ENSEMBLE, pas une section isolément :
est-ce que l'histoire progresse comme une seule scène/action continue qui s'enchaîne
logiquement de section en section, ou est-ce que les sections ressemblent à une suite
d'épisodes/moments distincts juxtaposés — MÊME SI le même personnage revient d'une
section à l'autre (un même personnage peut être montré à travers une suite d'épisodes
séparés plutôt qu'une action continue) ?
• INTR_FRAG : plusieurs sections s'introduisent comme un nouveau moment/une nouvelle
              scène plutôt que de reprendre directement la suite de la précédente ; les
              key_observation, mis bout à bout, ne forment pas une progression continue.
• INTR_LIN  : les key_observation, mis bout à bout, forment une progression cohérente
              et continue d'un événement vers le suivant, sur le même fil narratif.
• INTR_CYC  : la situation ou les motifs de la dernière section se rapportent
              fortement à ceux de la première section (retour net au point de départ).

TEMPORALITÉ — compare les repères temporels (time_position_marker) des sections DANS
L'ORDRE (section 1 → section {n_chunks})
• TEMP_LIN    : les repères temporels progressent de façon globalement cohérente et
                avancent dans le temps ; peu ou pas de flashback_or_jump_in_section=yes
                ni de narration_stance=retrospective_reflection.
• TEMP_DIS    : au moins une contradiction notable dans la progression (un repère plus
                tardif apparaît avant un repère plus précoce, ou des lignes temporelles
                distinctes selon les sections), OU plusieurs sections signalent un
                flashback/saut ou une posture rétrospective — sans que la chronologie
                devienne totalement illisible.
• TEMP_DESORD : la chronologie est impossible à reconstituer de façon cohérente à
                partir des repères temporels donnés dans la majorité des sections.
"""

# ── MAP PROMPT ────────────────────────────────────────────────────────────────
MAP_SYSTEM = """Tu es un analyste littéraire expert en narratologie française.
Réponds UNIQUEMENT avec un objet JSON. Pas de réflexion affichée, pas d'hésitation
("d'abord je vais...", "voyons...", "analysons..."), pas de préambule, pas
d'explication. Le premier caractère de ta réponse doit être {."""

def map_prompt(chunk_text, chunk_index, total_chunks):
    pos = ("DÉBUT"    if chunk_index == 0 else
           "FIN"       if chunk_index == total_chunks - 1 else
           f"MILIEU section {chunk_index+1}/{total_chunks}")
    if len(chunk_text) > MAX_CHARS_PER_CHUNK:
        mid  = len(chunk_text) // 2
        half = MAX_CHARS_PER_CHUNK // 2
        chunk_text = chunk_text[max(0, mid-half): mid+half]
    return f"""Analyse cet extrait ({pos}) d'un roman français.

--- EXTRAIT ---
{chunk_text}
--- FIN EXTRAIT ---

DÉFINITIONS DE RÉFÉRENCE :
{CRITERIA_DEFS.format(n_chunks=total_chunks)}

Réponds directement par le JSON ci-dessous, SANS AUCUN TEXTE avant (remplace les ...
par tes observations sur CET extrait) :
{{
  "chunk": {chunk_index + 1},
  "position": "{pos}",
  "narrator_voice": "first_person OU third_person OU unclear",
  "narrator_role": "protagonist OU witness OU not_applicable",
  "inner_thoughts": "none OU one_character OU multiple_characters",
  "pov_chapter_marker": "yes OU no",
  "dominant_mode": "action_events OU description OU introspection OU mixed",
  "world_type": "realistic OU autobiographical_explicit OU fantastic OU speculative_sf",
  "narrator_entity": "human OU non_human_or_unconventional (ex: animal, objet, entité collective)",
  "autobiographical_signal": "none OU implicit_confessional_tone OU explicit_author_reference",
  "space": "single_location OU multiple_locations OU journey_travel OU imaginary",
  "focus_character_or_thread": "qui/quel fil narratif domine CETTE section (bref)",
  "time_position_marker": "tout repère temporel explicite/implicite dans CETTE section (âge, date, saison, avant/après un événement...), ou 'none'",
  "narration_stance": "in_scene OU retrospective_reflection",
  "flashback_or_jump_in_section": "yes OU no (un saut temporel DANS cet extrait même)",
  "key_observation": "deux phrases : ce qui se passe concrètement dans cette section, et comment elle COMMENCE (reprend-elle directement la suite de la scène précédente, ou s'introduit-elle comme un nouveau moment/une nouvelle scène/un nouveau décor ?)"
}}"""

# ── REDUCE PROMPT ─────────────────────────────────────────────────────────────
REDUCE_SYSTEM = """Tu es un expert en narratologie française.
Réponds UNIQUEMENT avec un objet JSON. Pas de réflexion affichée, pas d'hésitation
("attends", "en fait", "non plutôt"), pas de préambule. Va directement au résultat."""

def reduce_prompt(observations, filename):
    n = len(observations)
    return f"""Roman : {filename}

Observations de {n} sections (début → fin) :
{json.dumps(observations, ensure_ascii=False, indent=2)}

{CRITERIA_DEFS.format(n_chunks=n)}

INSTRUCTIONS :
- Base ta décision sur L'ENSEMBLE des sections, pas une seule.
- Pour ESPACE, INTRIGUE et TEMPORALITÉ : compare ACTIVEMENT les sections entre elles
  (ordre, continuité de personnage/fil narratif, cohérence des repères temporels).
- Pour RÉGIME NARRATIF : les critères FANT et AUTO se jugent sur la récurrence à travers
  PLUSIEURS sections, pas sur un seul détail isolé.
- Choisis EXACTEMENT un code par critère.

Réponds UNIQUEMENT avec ce JSON :
{{
  "TYPE NARRATEUR":  "NAR_AUTOD ou NAR_TEM ou NAR_EXT ou NAR_VAR",
  "MODE NARRATIF":   "MOD_EVT ou MOD_DESC ou MOD_INTR ou MOD_DIA ou MOD_MIX",
  "REGIME NARRATIF": "REG_AUTO ou REG_REAL ou REG_FANT ou REG_SPEC",
  "ESPACE":          "ESP_UNIT ou ESP_FRAG ou ESP_ITIN ou ESP_IMAG",
  "INTRIGUE":        "INTR_LIN ou INTR_FRAG ou INTR_CYC",
  "TEMPORALITÉ":     "TEMP_LIN ou TEMP_DIS ou TEMP_DESORD"
}}"""

# ── FOCALISATION — isolated MAP/REDUCE pass (2026-11-01, see note above
# CRITERIA_DEFS) ────────────────────────────────────────────────────────────
FOC_DEFS = """
FOCALISATION — degré d'accès du LECTEUR aux informations disponibles pour les
personnages (partage, restriction, ou excès de savoir par rapport à eux) :
• FOC_RFOC  : récit focalisé — centrage narratif sur un ou plusieurs personnages,
              avec un accès privilégié à ce qu'ils perçoivent, pensent ou savent ;
              le LECTEUR PARTAGE leur champ d'information (ni plus, ni moins).
• FOC_REST  : focalisation restreinte — le LECTEUR EN SAIT MOINS que les
              personnages ; l'accès à l'information est partiel ou différé, ce
              qui crée un effet de curiosité ou de mystère.
• FOC_ELARG : focalisation élargie — le LECTEUR EN SAIT PLUS que les
              personnages ; certaines informations sont divulguées de manière à
              permettre l'anticipation d'événements que les protagonistes
              ignorent (ironie dramatique).
              ⚠ Exige plusieurs instances CONCRÈTES et INDÉPENDANTES de ce
              signal à travers le roman (pas une seule occurrence isolée dans
              une seule section) — une section isolée qui semble montrer ce
              signal peut être une fausse alerte due au manque de contexte de
              cette section seule ; ce n'est un vrai FOC_ELARG que si le
              phénomène se répète à travers le récit.
• FOC_MIXTE : alternance STRUCTURÉE de plusieurs régimes de focalisation dans
              des séquences distinctes (chapitres, voix, blocs narratifs) —
              PAS un mélange local dans une même scène, mais un changement de
              régime clairement délimité par section/chapitre.
"""

MAP_FOC_SYSTEM = MAP_SYSTEM
REDUCE_FOC_SYSTEM = REDUCE_SYSTEM
MAP_FOC_NUM_PREDICT = 400   # 3 short fields only
REDUCE_FOC_NUM_PREDICT = 200  # 1 short field only


def map_prompt_foc(chunk_text, chunk_index, total_chunks):
    pos = ("DÉBUT"    if chunk_index == 0 else
           "FIN"       if chunk_index == total_chunks - 1 else
           f"MILIEU section {chunk_index+1}/{total_chunks}")
    if len(chunk_text) > MAX_CHARS_PER_CHUNK:
        mid  = len(chunk_text) // 2
        half = MAX_CHARS_PER_CHUNK // 2
        chunk_text = chunk_text[max(0, mid-half): mid+half]
    return f"""Analyse cet extrait ({pos}) d'un roman français.

--- EXTRAIT ---
{chunk_text}
--- FIN EXTRAIT ---

DÉFINITIONS DE RÉFÉRENCE :
{FOC_DEFS}

Réponds directement par le JSON ci-dessous, SANS AUCUN TEXTE avant :
{{
  "chunk": {chunk_index + 1},
  "position": "{pos}",
  "pov_chapter_marker": "yes OU no",
  "dramatic_irony_evidence": "cite ou décris BRIÈVEMENT un moment CONCRET de CETTE section où le lecteur apprend/voit quelque chose qu'un personnage ignore encore à ce moment précis (ex: 'le lecteur sait que X trompe Y, que Y ignore') — sinon écris exactement 'none'. N'invente rien : ne réponds que s'il y a un exemple précis et localisable dans cet extrait.",
  "info_withheld_evidence": "cite ou décris BRIÈVEMENT une information CONCRÈTE que CETTE section cache ou diffère volontairement au lecteur (effet de mystère/suspense) — sinon écris exactement 'none'. N'invente rien : ne réponds que s'il y a un exemple précis et localisable dans cet extrait."
}}"""


def reduce_prompt_foc(observations, filename):
    n = len(observations)
    return f"""Roman : {filename}

Observations de {n} sections (début → fin) :
{json.dumps(observations, ensure_ascii=False, indent=2)}

{FOC_DEFS}

INSTRUCTIONS :
- Regarde dramatic_irony_evidence et info_withheld_evidence à travers TOUTES les sections.
  ⚠ Une seule section avec un exemple de dramatic_irony_evidence n'est PAS
  suffisante pour FOC_ELARG — une section isolée peut sembler montrer ce signal
  simplement par manque de contexte (elle ne voit pas le reste du roman). Exige
  AU MOINS DEUX sections avec des exemples concrets et distincts de
  dramatic_irony_evidence (pas juste "none" partout ailleurs) pour choisir
  FOC_ELARG. Même logique pour FOC_REST avec info_withheld_evidence (au moins
  deux sections avec des exemples concrets).
  Si ni l'un ni l'autre seuil n'est atteint (la plupart des sections répondent
  "none" aux deux champs) → FOC_RFOC par défaut (le lecteur partage simplement
  le champ d'information des personnages, cas le plus courant).
  Si PLUSIEURS sections ont pov_chapter_marker=yes ET que le motif
  d'évidence (irony/withheld/aucun des deux) change de façon structurée d'une
  section attribuée à l'autre (pas juste du bruit ponctuel) → FOC_MIXTE.

Réponds UNIQUEMENT avec ce JSON :
{{
  "FOCALISATION": "FOC_RFOC ou FOC_REST ou FOC_ELARG ou FOC_MIXTE"
}}"""

```

---

## Task 1 — Référentiel vs figuré (qwen3:30b)

Source : `métaphore/run_task1_corpus.py`

```python
EXAMPLES = {
    "animaux": """
EXEMPLES — termes animaux (indépendants du jeu d'évaluation):

référentiel (animal réel):
• "Le fermier nourrissait ses poules chaque matin avant le lever du soleil."
  → poules = référentiel (vraies volailles d'élevage)
• "Un aigle tournoyait lentement au-dessus des rochers calcaires."
  → aigle = référentiel (oiseau réel observé dans la nature)
• "La rivière grouillait de truites que les pêcheurs tentaient d'attraper."
  → truites = référentiel (poissons réels dans une rivière)
• "Elle tira le chat par la queue pour le faire descendre de la table."
  → chat = référentiel (animal domestique présent physiquement)

figuré (métaphore, comparaison, expression):
• "Monter sur ses grands chevaux — il s'est mis en colère pour rien."
  → chevaux = figuré (expression idiomatique, pas de vrais chevaux)
• "Elle avait un caractère de cochon — personne ne pouvait la supporter."
  → cochon = figuré (expression pour décrire le caractère d'une personne)
• "Il travaillait comme un bœuf du matin au soir sans jamais se plaindre."
  → bœuf = figuré (comparaison pour décrire l'effort humain)
• "Avoir d'autres chats à fouetter — j'ai des choses plus importantes à faire."
  → chats = figuré (expression idiomatique française)
• "Les candidats tombaient comme des mouches face aux questions du jury."
  → mouches = figuré (comparaison, pas de vraies mouches)""",

    "plantes": """
EXEMPLES — termes végétaux/plantes:

référentiel (plante réelle):
• "Le jardinier arrosait ses tomates chaque soir en été."
  → tomates = référentiel (vraies plantes dans un jardin)
• "La forêt de chênes centenaires longeait toute la route départementale."
  → chênes = référentiel (vrais arbres dans un paysage)
• "Elle cueillit des champignons dans le sous-bois humide de novembre."
  → champignons = référentiel (vrais champignons cueillis)
• "Les vignes de Bourgogne produisent certains des meilleurs vins du monde."
  → vignes = référentiel (vraies plantes viticoles)
• "L'olivier millénaire se dressait au centre de la place du village."
  → olivier = référentiel (vrai arbre présent physiquement)

figuré (métaphore, expression idiomatique):
• "Les carottes sont cuites — il est trop tard pour changer quoi que ce soit."
  → carottes = figuré (expression figée)
• "Mettre du beurre dans les épinards — il cherchait à améliorer ses revenus."
  → épinards = figuré (expression idiomatique)
• "Ne pas avoir un radis — il était complètement fauché après les vacances."
  → radis = figuré (expression idiomatique)
• "Elle était fleur bleue — elle croyait encore aux contes de fées à trente ans."
  → fleur = figuré (expression pour désigner quelqu'un de romantique naïf)
• "Sa chevelure était une forêt sombre où l'on pouvait se perdre facilement."
  → forêt = figuré (métaphore pour des cheveux très épais)

CAS DIFFICILES:
• "La branche d'olivier symbolisait la paix dans les négociations." → olivier = figuré (symbole)
• "Ne laissez pas la branche d'olivier tomber de ma main…" → olivier = figuré (symbole politique/religieux)
• "L'agriculteur taille ses oliviers chaque printemps." → oliviers = référentiel (vrais arbres)
• "Elle a la peau couleur lime." → lime = figuré (comparaison de couleur, pas de vraie lime)""",
}

CORE_DEFINITIONS = """
DÉFINITIONS:
- référentiel: le terme désigne un être vivant, lieu, ou élément naturel RÉEL — physiquement présent ou mentionné comme tel dans un contexte concret (naturaliste, géographique, culinaire, scientifique, écologique)
- figuré: le terme est utilisé comme métaphore, comparaison (avec "comme"), expression idiomatique figée, personnification, ou symbole abstrait décrivant une situation ou émotion humaine

⚠️ RÈGLES CLÉS:
1. Expression idiomatique connue (carottes cuites, mer à boire, montagnes à déplacer...) → toujours figuré
2. Terme dans une comparaison avec "comme" pour décrire un humain → figuré
3. Terme décrivant un lieu ou être réellement présent dans la scène → référentiel
4. Terme dans un contexte scientifique, géographique, naturaliste, écologique → référentiel
5. Crise environnementale réelle (réchauffement, pollution, extinction) → référentiel même si le verbe semble fort
6. Terme géographique africain/asiatique dans contexte colonial ou de voyage → référentiel
7. Terme dans une métaphore décrivant émotion ou situation humaine → figuré
"""

def build_batch_prompt(items, category):
    entries = "\n".join(
        f'{i}. TERME: <terme>{token}</terme> | PHRASE: {contexte}'
        for i, token, contexte in items
    )
    return (
        "Tu es un expert en sémantique française. Pour chaque entrée numérotée, "
        "détermine si le terme est utilisé de façon LITTÉRALE (référentiel) ou FIGURÉE.\n\n"
        + CORE_DEFINITIONS + "\n"
        + EXAMPLES[category] + "\n\n"
        + "ENTRÉES À CLASSIFIER:\n"
        + entries + "\n\n"
        + "Réponds UNIQUEMENT avec ce JSON (respecte l'ordre et les numéros):\n"
        + '[{"id": 1, "label": "..."}, {"id": 2, "label": "..."}, ...]'
    )
```


### Task 1 — Loterre (catégorie séparée, prompt dédié)

Source : `métaphore/evaluate_loterre_v8.py` — prompt réutilisé tel quel
par le runner de production `métaphore/run_loterre_corpus.py` (85.2%
précision sur le jeu d'or, finalisé 2026-06-24). Catégorie distincte des
animaux/plantes ci-dessus — termes géographiques/écologiques Loterre
(écosystème, steppe, forêt, etc.).

```python
EXAMPLES_LOTERRE = """
EXEMPLES — termes écologiques/géographiques Loterre (indépendants du jeu d'évaluation):

référentiel (lieu ou concept écologique réel):
• "Les scientifiques étudient l'écosystème du lac depuis vingt ans."
  → écosystème = référentiel (vrai concept écologique scientifique)
• "La déforestation détruit les forêts tropicales à un rythme alarmant."
  → forêts = référentiel (vraies forêts, contexte écologique)
• "Le biologiste traversait la steppe mongole à dos de cheval depuis des jours."
  → steppe = référentiel (vrai biome géographique traversé)
• "La montagne culminait à 4807 mètres — le Mont Blanc, toit de l'Europe."
  → montagne = référentiel (vrai sommet géographique précis)
• "Il s'assit au bord du fleuve et regarda l'eau couler en silence pendant une heure."
  → fleuve = référentiel (vrai cours d'eau, présent physiquement dans la scène)
• "Les forêts brûlaient. Les océans agonisaient. Le permafrost fondait."
  → océans = référentiel (vrais océans dans un contexte de crise écologique réelle)
• "Le four de la boulangerie brûlait depuis cinq heures du matin."
  → four = référentiel (vrai appareil de cuisson, contexte concret de boulangerie)
• "Il alluma les brûleurs de la cuisinière et la flamme s'éleva."
  → flamme = référentiel (vraie flamme physique dans une cuisine)

figuré (métaphore, expression idiomatique):
• "Prêcher dans le désert — personne n'écoutait ses avertissements répétés."
  → désert = figuré (expression idiomatique, parler sans être entendu)
• "Déplacer des montagnes — elle ferait tout pour sauver son entreprise."
  → montagnes = figuré (expression idiomatique, effort surhumain)
• "Ce n'est pas la mer à boire — il suffit de remplir deux formulaires."
  → mer = figuré (expression idiomatique, ce n'est pas difficile)
• "Sa carrière était un désert depuis son licenciement."
  → désert = figuré (métaphore pour une période sans activité)
• "Ils vivaient dans un océan de dettes depuis la faillite."
  → océan = figuré (métaphore pour une grande quantité accablante)
• "Il avait enfin réussi à sortir du bourbier de ses dettes accumulées pendant des années."
  → bourbier = figuré (métaphore pour une situation embourbée, difficile à quitter)
• "Le temps l'avait lentement extrait des sables mouvants de sa dépression."
  → sables mouvants = figuré (métaphore pour une situation qui engloutit progressivement)
• "Cette lettre avait traversé des décennies et des océans avant de lui parvenir."
  → océans = figuré (métaphore pour une grande distance temporelle et géographique-émotionnelle)
• "Être jeté dans l'arène sans préparation — c'est ce qu'il avait ressenti à son premier jour."
  → arène = figuré (métaphore pour une situation de compétition/confrontation)
• "La chaleur de leur accueil était un véritable incendie de bienveillance."
  → incendie = figuré (métaphore hyperbolique pour une intensité émotionnelle)
• "L'effervescence de la salle de rédaction brûlait comme un feu de camp permanent."
  → feu = figuré (comparaison pour une énergie collective intense, pas un vrai feu)
• "Je prépare en moi la renaissance du printemps, ce renouveau que j'attends depuis des mois."
  → renaissance du printemps = figuré (métaphore pour un renouveau intérieur/psychologique)
• "Son sourire était une éclaircie après des mois de tempête intérieure."
  → tempête = figuré (métaphore pour une période de trouble émotionnel)
• "Après des années passées dans les marécages de l'indécision, il avait enfin choisi."
  → marécages = figuré (métaphore pour une situation d'enlisement et d'hésitation)

CAS DIFFICILES — règles décisives:
• "Le temps + terme géographique" (le temps nous a poussés hors des marais) → TOUJOURS figuré (le temps ne pousse pas dans de vrais marais)
• "Terme + de + abstraction" (incendie de bienveillance, océan de dettes, forêt de questions) → figuré (DE_QUANTIF ou métaphore)
• "Traverser/franchir + terme + et + abstraction" (traversé la mer et ma mémoire) → figuré (énumération poétique)
• "Renaissance/renouveau du paysage/printemps" dans contexte intérieur → figuré
• Vrai appareil de cuisson qui produit de la chaleur réelle → référentiel (pas figuré)
• Vrai lieu géographique avec coordonnées ou description physique → référentiel
• Terme géographique suivi immédiatement d'une notion abstraite humaine → figuré
"""

CORE_DEFINITIONS = """
DÉFINITIONS:
- référentiel: le terme désigne un lieu géographique ou phénomène écologique RÉEL — physiquement présent ou mentionné dans un contexte concret (naturaliste, géographique, scientifique, écologique)
- figuré: le terme est utilisé comme métaphore, comparaison (avec "comme"), expression idiomatique, ou symbole abstrait décrivant une situation ou émotion humaine

⚠️ RÈGLES CLÉS:
1. Expression idiomatique connue → toujours figuré
2. "Le temps + terme géographique" comme sujet → toujours figuré
3. Terme géographique + abstraction humaine dans même énumération → figuré
4. "Incendie/feu/flamme" décrivant une émotion ou intensité → figuré
5. "Renaissance/renouveau" du paysage dans contexte humain → figuré
6. Terme géographique dans un contexte écologique/scientifique/physique → référentiel
7. Vrai appareil ou source de chaleur physique → référentiel
"""

def build_prompt(token, contexte):
    return f"""Tu es un expert en sémantique française. Détermine si le terme est utilisé de façon LITTÉRALE (référentiel) ou FIGURÉE dans cette phrase.

{CORE_DEFINITIONS}

{EXAMPLES_LOTERRE}

TERME À ANALYSER: <terme>{token}</terme>
PHRASE: {contexte}

Réponds UNIQUEMENT avec ce JSON:
{{"label": "référentiel"}} ou {{"label": "figuré"}}"""

```


---

## Task 2 — Sous-catégories de métaphore (12 questions, arbre de décision)

Source : `métaphore/run_task2_subcategories.py`

```python
def make_prompt(token, context, category):
    return f"""Tu es expert en stylistique française et en figures de style.

Le mot «{token}» (catégorie: {category}) est utilisé de façon FIGURATIVE dans ce contexte:
«{context}»

Détermine la catégorie structurelle de cette figure en suivant CET ORDRE de
questions (comme un arbre de décision — réponds à la première question qui
s'applique, ne compare pas toutes les catégories en même temps).
⚠ DISCIPLINE D'ORDRE OBLIGATOIRE : teste les questions UNE PAR UNE, dans
l'ordre numéroté. Dès qu'une question s'applique clairement, réponds avec
son code et ARRÊTE-TOI — ne continue pas à évaluer les questions suivantes
"au cas où" une autre catégorie semblerait mieux correspondre.

1. Y a-t-il une expression figée/lexicalisée où «{token}» a perdu son sens
   littéral d'animal/plante ? Quelques exemples illustrant des FORMES variées
   que peut prendre une expression figée (le point commun n'est pas la forme
   syntaxique mais le fait que le sens global est FIXÉ par l'usage, indépendant
   du sens propre de chaque mot) :
   - avec "comme" : "rusé comme un renard", "muet comme une carpe"
   - avec "de" : "larmes de crocodile", "rat de bibliothèque", "travail de fourmi"
   - nom composé : "bouc émissaire", "chant du cygne"
   - locution verbale : "avoir la chair de poule", "poser un lapin",
     "avoir une araignée au plafond", "avoir des fourmis dans les jambes/les
     muscles" (sensation de picotement/fourmillement, pas de vraies fourmis)
   ⚠ EXCLUS de LOC_IDIOM — vérifie ces cas AVANT de conclure LOC_IDIOM,
   même si l'expression "a l'air" figée. Si l'un s'applique, va directement
   à la question indiquée plutôt que de répondre ici :
   - L'expression sert à COULEUR (ex: "poivre et sel" pour des cheveux) →
     ne réponds PAS ici, va à la question 2 (COUL).
   - Après "comme", le nom garde un sens LITTÉRAL actif dans la scène, OU
     "comme" introduit une proposition entière décrivant un ÉVÉNEMENT/
     PROCESSUS (même via une proposition relative ou un participe, pas
     seulement un verbe conjugué autonome) — ex: "se faire tirer comme des
     lièvres" (de vrais lièvres sont chassés), "comme on compte des
     moutons" (bien que "compter les moutons" soit aussi une expression
     connue, ICI c'est une comparaison vivante avec son propre verbe
     conjugué, pas une locution figée hors-contexte), "comme des baleines
     qu'on a abattues et dépecées" (proposition relative décrivant un
     événement) → ce n'est PAS une locution figée mais une comparaison
     vivante, ne réponds PAS ici, va à la question 4 (COMP_Q) ou 5
     (COMP_SIM/COMP_P). RÈGLE GÉNÉRALE : si "comme X" peut être développé en
     une proposition avec un événement/processus concret (même implicite ou
     elliptique), préfère la question 5 (COMP_P) à LOC_IDIOM, même si "comme
     X" ressemble aussi à une expression connue par ailleurs.
     ⚠ AUTO-VÉRIFICATION OBLIGATOIRE avant de répondre LOC_IDIOM : retire
     mentalement "comme" + le mot-clé de la phrase. Reste-t-il un événement
     ou une action CONCRÈTE et LITTÉRALE décrite dans le passage (des morts,
     une chasse, un mouvement réel, une action accomplie SUR le mot-clé) ?
     Si oui, ce n'est PAS LOC_IDIOM, quel que soit l'air "figé" de la
     tournure — c'est une comparaison vivante (question 4 ou 5). Ne réponds
     LOC_IDIOM que si retirer la comparaison ne changerait RIEN au sens
     factuel de la phrase.
   - Le contexte décrit une représentation/symbole (photo, motif, dessin,
     objet décoratif) plutôt qu'un usage figuré de langage (ex: "fleurs de
     lis" sur un drapeau, "à l'eau de rose" en référence à des photos
     sentimentales) → ne réponds PAS ici, va à la question 3 (IMAG).
   - La tournure est une RESSEMBLANCE-SEULEMENT du type "n'avoir de X que
     l'aspect/le nom/l'air" (ex: "qui n'a de concombre que l'aspect") →
     même si ça "a l'air" d'une expression figée, ne réponds PAS ici, va à
     la question 6 (MOD_ANALOG) — cette tournure est structurellement une
     analogie modalisée (ressemblance de surface, pas un sens lexicalisé
     figé), pas une locution.
   - L'expression COMBINE ou MODIFIE une locution connue de façon créative
     plutôt que de la citer dans sa forme EXACTE et figée (ex: "le cimetière
     des moutons noirs" fusionne deux expressions connues — "cimetière des
     éléphants" et "mouton noir" — en quelque chose de nouveau ; "la pomme
     du péché" est une référence symbolique mais n'est PAS la forme figée
     exacte, qui serait "le fruit défendu" ; "mon buisson ardent" est un
     usage créatif, pas idiomatique dans ce contexte), OU l'expression n'a
     PAS de sens figé conventionnel attesté et semble inventée pour
     l'occasion → ne réponds PAS LOC_IDIOM, va à la question 9 (META_NOM).
     RÈGLE GÉNÉRALE (confirmée par le chercheur superviseur) : préfère
     META_NOM à LOC_IDIOM dès que l'expression n'est pas EXACTEMENT sa forme
     canonique figée — une reprise, une recombinaison, une modification ou
     un usage créatif en fait une métaphore vivante, pas un idiome figé.
   Si aucun de ces cas ne s'applique → LOC_IDIOM.
2. «{token}» désigne-t-il une COULEUR (ex: "vert pomme", "bleu ciel") plutôt
   qu'un être vivant ? → COUL
   ⚠ EXCLUS de COUL si ce n'est pas «{token}» lui-même qui nomme une couleur,
   mais un ADJECTIF DE COULEUR séparé appliqué au sujet dans une comparaison
   de degré (ex: "aussi blond que les blés" — c'est "blond" qui est un terme
   de couleur, pas «blés», et la structure "aussi...que" est une comparaison
   de degré) → ne réponds PAS ici, va à la question 4 (COMP_Q).
3. Le contexte décrit-il une REPRÉSENTATION du vivant — pas seulement une
   image/dessin/sculpture explicite, mais aussi une simple RESSEMBLANCE DE
   FORME/silhouette avec le vivant, un DÉGUISEMENT ("déguisé/habillé/costumé
   en" + «{token}» — ex: "des chiens que l'on déguise en éléphants nains" =
   les chiens ont la FORME/l'apparence d'éléphants, pas de vrais éléphants),
   un MOTIF DÉCORATIF sur un objet/vêtement ("parsemé de", "orné de",
   "décoré de", "à motifs de" + «{token}»), OU une ÉVOCATION d'une figure/
   d'un titre/d'un symbole CULTUREL, LITTÉRAIRE, MYTHOLOGIQUE ou de CONTE
   déjà connu et associé au vivant, plutôt qu'une comparaison vivante
   inventée dans ce passage (ex: "le Roi des Aulnes" — référence au titre/
   personnage légendaire, pas une nouvelle métaphore ; "la princesse au
   petit pois" — référence au conte ; un vitrail ou vers biblique citant
   "la vigne") (ex: "un tableau représentant un lion" ; "une tache en forme
   de haricot" ; "des motifs à fleurs de lis") — plutôt que le vivant
   lui-même agissant ou étant décrit dans une scène vivante ? → IMAG.
   ⚠ Vérifie ce cas AVANT la question 7 (META_APP) et la question 8
   (structure "N de N2") — une simple juxtaposition de noms ("citrouille
   gomme à effacer", "Fenrir, loup géant") a la FORME d'une apposition
   (question 7) mais si le sens est une RESSEMBLANCE DE FORME ou une
   RÉFÉRENCE CONNUE plutôt qu'une caractérisation vivante, c'est IMAG, pas
   META_APP. De même, "parsemée de tournesols" a la forme d'un "N de N2"
   mais désigne un motif décoratif, donc IMAG, pas META_QUAL (question 8).
   ⚠ EXCLUS de IMAG — même si «{token}» évoque une référence culturelle/
   biblique/littéraire connue — si la phrase a par ailleurs une COPULE
   D'IDENTITÉ explicite ("est/sont/était/c'est"...) ou un VERBE/ADJECTIF
   dont le sens est incompatible avec «{token}» : dans ce cas la référence
   culturelle est secondaire, et la question 9 (META_NOM, si copule) ou 10
   (META_PRED, si verbe/adjectif incompatible) doit primer. Ex: "l'ivraie sera jetée
     au feu" (référence biblique MAIS «sera jetée» est un verbe appliqué
     métaphoriquement à l'ivraie pour désigner les pécheurs) → META_PRED,
     pas IMAG simplement parce que la scène a une origine biblique. La
   référence culturelle ne déclenche IMAG que si AUCUNE autre structure
   (copule, verbe incompatible) n'explique mieux la figure.
   ⚠⚠ MAIS cette exclusion NE S'APPLIQUE PAS si la copule se contente
   d'IDENTIFIER la figure culturelle/mythologique elle-même à son propre
   sujet grammatical — sans introduire de référent réel DIFFÉRENT auquel
   on la compare. Teste : le sujet de la copule EST-IL déjà la figure
   culturelle elle-même (autre pronom/nom qui la désigne, pas une personne
   ou un objet distinct du passage) ? Si oui → reste IMAG malgré la copule.
   Si le sujet est un référent réel autre que la figure elle-même → META_NOM.
   Ex: "Fenrir, loup géant... c'est le loup qui tuera Odin" (le sujet de
   "c'est" est Fenrir lui-même, la copule ne fait que redire son identité
   mythologique déjà établie) → IMAG. Mais "Riccardo, c'est le loup qui
   tuera Odin" (le sujet "Riccardo" est une personne réelle DIFFÉRENTE du
   loup mythologique, comparée à lui) → META_NOM.
4. Y a-t-il une comparaison de degré ("plus/moins/aussi/autant... que") ? → COMP_Q
5. Y a-t-il "comme" (y compris "comme si") ? Regarde ce qui suit "comme" et
   ce que «{token}» (ou le groupe nominal qui le contient) FAIT ou SUBIT :
   - Une résemblance STATIQUE/qualitative simple, SANS processus ni action —
     «{token}» est juste décrit comme ressemblant à quelque chose, sans
     qu'aucun événement ne lui arrive (ex: "rusé comme un renard", "comme
     les tentacules d'une pieuvre") → COMP_SIM
   - Une comparaison où le vivant comparé SUBIT ou ACCOMPLIT une ACTION, un
     PROCESSUS ou un ÉVÉNEMENT — que ce soit via un verbe conjugué autonome,
     une proposition relative, OU un participe/gérondif décrivant ce
     processus (ex: "comme les os craquent" ; "comme si une forêt retenait
     son souffle" ; "comme des roses... finissant par composer un bouquet"
     — les roses SUBISSENT un devenir/une transformation ; "comme une
     araignée fouettée" — l'araignée SUBIT l'action d'être fouettée, même
     si "fouettée" est un participe et non un verbe pleinement conjugué ;
     "comme des baleines qu'on a abattues et dépecées") → COMP_P
   ⚠ Le test n'est PAS "y a-t-il un verbe conjugué séparé" mais "le vivant
   comparé subit-il/accomplit-il quelque chose (même exprimé par un
   participe ou une proposition relative), ou est-il juste décrit de façon
   statique" ? Processus/action → COMP_P. Simple trait statique → COMP_SIM.
   ⚠ ATTENTION : un simple ADJECTIF ("un olivier fourbu") ou une phrase
   prépositionnelle IDENTIFIANTE ("le chien DE LA BRIGADE CANINE") qui
   modifie le nom comparé SANS décrire d'action/processus NE DÉCLENCHE PAS
   COMP_P — reste COMP_SIM. Seul un participe/proposition relative décrivant
   un évènement SUBI (comme "fouettée", "qu'on a abattues") déclenche COMP_P ;
   un adjectif ou "de X" qui ne fait que PRÉCISER/IDENTIFIER le nom (quel
   olivier, quel chien) ne compte pas comme un processus.
6. Y a-t-il "sembler", "on dirait", "avoir l'air de", "faire l'effet de", ou
   une tournure équivalente de perception/auto-perception analogique
   ("se voir", "se sentir devenir", "s'imaginer en"), OU une tournure de
   RESSEMBLANCE-SEULEMENT du type "n'avoir de X que l'aspect/le nom/l'air"
   (ex: "qui n'a de concombre que l'aspect" = ne ressemble au concombre que
   par l'apparence, sans en être vraiment un), OU "ressemblance/ressembler
   à/avec" + «{token}» (ex: "la ressemblance du Lockheed Vega avec un
   aigle"), OU "des airs de" + «{token}» (variante plurielle d'"avoir l'air
   de" — ex: "des airs implorants de chat") ? → MOD_ANALOG
7. «{token}» est-il placé JUSTE À CÔTÉ d'un nom (sujet ou complément) SANS
   copule ("est/était"), SANS "de" — une simple apposition, épithète directe,
   OU mot composé/juxtaposition directe avec ou sans trait d'union (ex: "la
   montagne sentinelle", "poulpe enfiévré tournoyant dans ma bouche",
   "arbre-parapluie", "forêt cathédrale") ? → META_APP. Ce cas couvre aussi
   ce qu'on appelait autrefois META_JUXT (catégorie éliminée le 2026-07-10
   sur confirmation de Riccardo — tout binôme nominal/juxtaposition va
   désormais dans META_APP). Ce cas doit être écarté AVANT de considérer
   "N1 de N2" ci-dessous — ne choisis META_DET/META_QUAL/META_NOM que si une
   vraie copule ou un vrai "de" relie les deux noms.
   ⚠ EXCLUS de META_APP si le sens est une RESSEMBLANCE DE FORME ou une
   RÉFÉRENCE CULTURELLE/LITTÉRAIRE CONNUE plutôt qu'une caractérisation
   vivante (voir question 3, IMAG) — re-vérifie la question 3 avant de
   répondre ici si ce doute existe.
8. Y a-t-il une structure "N1 de N2" (sans "comme") ? La question n'est PAS
   le domaine sémantique du trait illustré (qualité vs matière vs catégorie
   sociale...) mais une question PUREMENT POSITIONNELLE : «{token}» occupe-t-
   il la place de N1 (avant "de") ou de N2 (après "de") ?
   - «{token}» = N1, le terme vivant METAPHORISE N2 (ex: "une forêt de
     pylônes" — forêt=N1 métaphorise les pylônes ; "pomme de discorde" —
     pomme=N1 métaphorise la discorde ; "un essaim de pensées" — essaim=N1
     métaphorise les pensées) → META_DET
   - «{token}» = N2, le terme vivant est utilisé pour QUALIFIER N1 (ex:
     "une mémoire d'éléphant" — éléphant=N2 qualifie la mémoire ; "une mer
     de soie" — soie n'est pas vivant mais même logique inversée ; "ventre
     de pastèque" — pastèque=N2 qualifie le ventre) → META_QUAL
   ⚠ C'est un test de POSITION, pas de sens : regarde seulement si «{token}»
   est avant ou après "de" dans cette structure précise, rien d'autre.
   ⚠ EXCLUS de META_DET/META_QUAL si la structure "N1 de N2" ENTIÈRE (le
   groupe nominal complet, pas juste le lien interne) est elle-même placée
   en APPOSITION à un AUTRE nom plus large (ex: "sa tête, boule de piquants
   noirs" — ce n'est pas "piquants noirs" qui qualifie "boule" en isolation,
   c'est le groupe ENTIER "boule de piquants noirs" qui est apposé à "tête"
   pour la décrire) → ne réponds pas ici, retourne à la question 7
   ⚠ EXCLUS également si la structure "N1 de N2" ENTIÈRE est l'ATTRIBUT d'une
   COPULE qui porte sur un AUTRE référent plus large dans la même phrase (ex:
   "ses yeux... avec deux grains DE CASSIS" où "deux grains de cassis"
   identifie "ses yeux" ; "je serai... la feuille DU BANANIER" où "je" est
   identifié à "la feuille du bananier" via "serai") — ici c'est la COPULE
   (être/serai/sera/étaient...) qui gouverne l'identification à l'échelle de
   la phrase, PAS le lien interne "de" entre «{token}» et l'autre nom ; la
   structure "de" ne fait que préciser LEQUEL objet est identifié, elle n'est
   pas elle-même la figure. → ne réponds pas ici, va à la question 9 (META_NOM)
   (META_APP) et traite tout le groupe "N de N2" comme l'élément apposé.
   Test : y a-t-il un AUTRE nom, séparé par une virgule ou juste avant, que
   le groupe "N de N2" entier vient décrire/renommer ? Si oui → META_APP au
   niveau du groupe entier, pas META_QUAL au niveau du "de" interne.
   ⚠ EXCLUS de META_DET/META_QUAL si le "N de N2" est en fait la partie
   prédicative d'une copule d'IDENTITÉ ("il est LE X de N2", "elle est
   celle de N2" — la phrase affirme une identité, pas juste une relation
   N1-de-N2) → ne réponds pas ici, va plutôt à la question 9 (META_NOM).
   Ex: "il est le cerf de ma vie" (affirmation d'identité "il EST le
   cerf") → META_NOM, pas META_DET/META_QUAL.
   ⚠ EXCLUS de META_DET/META_QUAL si N1 est un nom-écran de RESSEMBLANCE
   ("forme", "aspect", "sorte", "genre", "espèce", "air", "façon" — ex: "en
   forme de palmiers", "une sorte de dragon") : ce n'est pas N1 qui est
   qualifié par N2, c'est une comparaison de ressemblance équivalente à
   "comme N2" → traite comme COMP_SIM (question 5), pas META_QUAL.
9. Y a-t-il une copule "est/était/sont/sommes/c'est/ce sont/serai.../fut/
   fussent/soit" (toute forme ou temps de "être", y compris l'INFINITIF
   "être" après un verbe modal/de préférence : "mieux vaut être X",
   "veut/voudrait être X", "doit être X"), OU "devenir/redevenir", OU un
   surnommage/désignation identifiante (ex: "on le surnomme le rat", "on
   l'appelle la vipère", "on le traite de macaque" — «{token}» devient
   littéralement le nom/surnom donné à quelqu'un), OU une EXCLAMATION
   insultante/caractérisante du type "quel/quelle N1 de N2 !" visant une
   personne/un animal précis déjà présent dans la scène (ex: "quel têtard
   de quelle mare !" — insulte qui NOMME la personne par ce terme, comme
   "quel idiot !") ? → META_NOM
   Exemples : "cet homme est un loup" ; "nous sommes de grosses côtes de
   bœuf" ; "c'est le cygne et le chat qui se nettoient" ; "Constance
   redevint un agneau" ; "mieux vaut être une mouette qu'une huître".
   ⚠ COMPTE AUSSI COMME COPULE D'IDENTITÉ (→ META_NOM), même sans "être"
   explicite adjacent à «{token}» :
   - un DÉTERMINANT DÉMONSTRATIF ("ce/cette/cet") introduisant «{token}»
     pour identifier directement un référent réel précis (ex: "j'étais ce
     chamois effaré" ; "cette antilope qui cherche une source" ; "ce
     haricot rouge doré" désignant une partie du corps) — le démonstratif
     fonctionne ici comme une identification, au même titre que "est".
   - une forme SUBJONCTIVE/CONCESSIVE de "être" ("fussent-ils des chiens",
     "fût-elle un ange") qui affirme quand même une identité de façon
     concessive ("même si/en admettant qu'ils étaient X") — à ne pas
     confondre avec le cas hypothétique "si X était Y" exclu ci-dessous,
     qui lui pose une hypothèse non affirmée.
   ⚠ EXCLUS de META_NOM si la copule est au conditionnel/hypothétique
   ("si X était Y, ..." — une hypothèse, pas une affirmation d'identité) :
   va plutôt à la question 5 (COMP_P, "comme si" couvre aussi ce cas).
   ⚠ EXCLUS de META_NOM — ne réponds PAS ici, même avec une copule
   explicite, dans ces 2 cas (le prédicat/l'attribut a sa PROPRE structure
   figurative plus spécifique, qui doit primer sur la copule générique) :
   - Le nom attribut est lui-même une EXPRESSION FIGÉE/IDIOME connu, ou a
     sa propre structure "N1 de N2" déjà couverte par la question 8 (ex:
     "je suis un cœur d'artichaut" — idiome fixe ; "la langue chinoise
     était un sésame" — référence à "Sésame, ouvre-toi") → va plutôt à la
     question 1 (LOC_IDIOM) ou reste sur la réponse de la question 8.
   - «{token}» est un TERME D'AFFECTION/D'ADRESSE figé ("mon loup", "ma
     poule", "mon chou", "mon lapin" utilisés pour s'adresser affectueusement
     à une personne précise, PAS pour la caractériser ou l'insulter) → ces
     termes sont du vocabulaire affectif FIGÉ → va plutôt à la question 1
     (LOC_IDIOM). Contraste : "on le traite de rat" (insulte qui
     CARACTÉRISE la personne) → reste META_NOM. "mon loup" (appellation
     affectueuse neutre) → LOC_IDIOM.
   ⚠ DISTINCTION AVEC META_PRED (question 10, juste après) : si «{token}»
   est lui-même le SUJET ou l'ATTRIBUT d'une copule d'identité (le mot-clé
   EST ce qu'on affirme) → META_NOM (ex: "cet homme est un loup",
   "j'ai engendré un chicon" — chicon est l'identité/le produit affirmé,
   pas une action). Si «{token}» est plutôt le sujet d'un VERBE D'ACTION ou
   le support d'un ADJECTIF normalement incompatible avec lui, même si une
   copule existe ailleurs dans la phrase → META_PRED (ex: "le chêne a
   répliqué" — chêne accomplit l'action humaine de répliquer, ce n'est pas
   une identité affirmée).
10. Y a-t-il un VERBE dont le sens littéral est incompatible avec son sujet,
    OU un ADJECTIF normalement réservé à un autre domaine appliqué à
    «{token}» (ex: "la forêt avalait la lumière", "le glacier agonisait",
    "le chêne a répliqué", "une douceur végétale" — «{token}» accomplit une
    ACTION ou reçoit une QUALIFICATION qui lui est normalement étrangère,
    plutôt que de simplement RECEVOIR une identité/un nom via une copule) ?
    → META_PRED

Réponds UNIQUEMENT avec ce JSON (indique aussi le numéro de question qui a
déclenché ta réponse, pour vérification) :
{{"code": "CODE", "question_number": N, "raison": "explication courte en français"}}"""

# ── OLLAMA CALL ───────────────────────────────────────────────────────────────
```

---

## Task 4.5 — Catégorie du comparé (CH/P/NH/O/E/A)

Source : `comparison/run_task45_compare_category_v2_physical_psych.py`

```python
CATEGORIES = {
    "CH": ("Corps humain et processus biologiques",
           "références métaphoriques au corps humain, fonctions physiologiques, processus biologiques humains"),
    "P":  ("États psychologiques et fonctions cognitives",
           "émotions, sensations, fonctions cognitives comme la mémoire et l'imagination"),
    "NH": ("Créatures non humaines vivantes et processus biologiques",
           "animaux, plantes, processus biologiques chez les êtres vivants non humains"),
    "O":  ("Objets et structures artificiels",
           "objets fabriqués par l'homme, artefacts technologiques"),
    "E":  ("Éléments naturels inanimés et processus naturels",
           "paysages naturels, formations géologiques, phénomènes météorologiques, aspects non vivants du monde naturel"),
    "A":  ("Concepts abstraits",
           "idées abstraites : politique, religion, art, institutions sociales comme le mariage"),
}
VALID_CODES = list(CATEGORIES.keys())

# ── LLM PROMPT — Conceptual Metaphor Theory (CMT) step-by-step chain ────────
# Redesigned 2026-07-08 per literature on CMT-based prompting for metaphor
# interpretation (arxiv 2502.01901: sequential source->target->differ questions
# reached F1 up to 82.59, vs. asking for the answer directly) and tenor-
# vehicle-ground extraction (arxiv 2010.05633: validate via the shared
# "ground" property before committing to a classification). Our first prompt
# fix (tenor/vehicle warning) helped (Task 4.5 gold accuracy 30%->63.5%) but
# residual CH<->NH confusion remained — this forces the model through each
# step explicitly instead of just warning it not to make the mistake.
#
# Corrected 2026-07-10 per Riccardo's email: the categories classify what
# KIND OF ENTITY the cible (target/comparé) literally IS, never the semantic
# domain of the trait/quality the comparison illustrates. An earlier version
# of this prompt told the model "personality trait -> P, not CH" and "voice/
# artistic quality -> A, not CH" — both wrong, since a personality trait
# attributed to a human referent is still CH (the referent is a person), a
# voice attributed to a human referent is still CH, etc. Riccardo's own
# example: "Je bats lâchement en retraite... comme un rat" -> cible = "il"
# (a person) -> CH, even though the illustrated trait (lâcheté) is
# psychological. Contrast: "Mes émotions se cachaient comme des rats" ->
# cible = "mes émotions" -> P. "L'île ressemblait à un rat" -> cible =
# "l'île" -> E. Same vehicle, different category, purely by what the cible
# itself is.
def make_prompt(token, context, subcategory):
    cats_desc = "\n".join(f"  {code}: {info[0]} — {info[1]}" for code, info in CATEGORIES.items())
    return f"""Tu es expert en stylistique française et en figures de style, formé à
la théorie de la métaphore conceptuelle (véhicule / cible / fondement commun).

Le mot «{token}» est utilisé de façon FIGURATIVE dans ce contexte :
«{context}»

Cette figure appartient à la catégorie structurelle: {subcategory}

Réponds aux questions suivantes DANS L'ORDRE, en JSON, une par une :

1. vehicule : que désigne «{token}» littéralement, en dehors de ce contexte
   (ex: "rat" = un petit rongeur) ? Réponse brève.
2. cible : dans CETTE phrase précise, quel est le RÉFÉRENT RÉEL — la vraie
   personne, chose, créature ou idée — auquel «{token}» est comparé ? C'est
   en général le sujet réel de la comparaison (ex: "il", "elle", "mes
   émotions", "l'île", "le mariage"). Réponse brève, un groupe nominal.
3. fondement_commun : quelle qualité ou propriété partagée justifie cette
   comparaison entre le véhicule et la cible (ex: pingrerie, ruse, fragilité) ?
   Réponse brève. Cette qualité NE SERT PAS à choisir la catégorie (étape 5) —
   elle est juste là pour vérifier que la comparaison est cohérente.
4. verification : le véhicule (réponse 1) et la cible (réponse 2) sont-ils
   des choses DIFFÉRENTES ? (yes/no — si non, ce n'est probablement pas une
   vraie figure, mais classe quand même du mieux possible)
5. code : classe la CIBLE (réponse 2) selon LE TYPE D'ENTITÉ QU'ELLE EST
   LITTÉRALEMENT — jamais selon le domaine de la qualité/du trait illustré
   (réponse 3). Choisis parmi :

{cats_desc}

EXEMPLES DE RÉFÉRENCE (inventés, un par catégorie — même s'ils ne parlent pas
de «{token}», la LOGIQUE de classement est ce qui compte) :
- CH : «Pierre courait comme un lièvre, le souffle court» — cible = «Pierre»
  (une personne, même si le trait "vitesse/souffle" a une composante
  physique OU comportementale) → CH.
- P : «Sa jalousie rôdait comme un loup affamé» — cible = «sa jalousie» (une
  émotion elle-même, sujette grammaticale de l'action) → P.
- NH : «Le chat de la voisine grimpait comme un écureuil» — cible = «le
  chat» (un animal non-humain, pas une personne) → NH.
- O : «La vieille voiture toussait comme un vieillard essoufflé» — cible =
  «la voiture» (un objet fabriqué) → O.
- E : «La falaise se dressait comme une sentinelle» — cible = «la falaise»
  (un élément naturel non-vivant) → E.
- A : «Le mariage, cette cage dorée, l'étouffait» — cible = «le mariage»
  (une institution/pratique sociale, pas une personne précise) → A.

⚠ RÈGLE CENTRALE (précisée par Riccardo Barontini, 2026-07-10, en réponse à
des cas où la règle simple "cible=personne → CH" s'est révélée insuffisante) :
la catégorie dépend de ce que la cible EST — mais quand la cible est une
PERSONNE, il faut aller un cran plus loin et déterminer QUELLE DIMENSION de
cette personne est réellement comparée :
- si la comparaison porte sur le CORPS de la personne, un mouvement/une
  action PHYSIQUE qu'elle accomplit, ou un processus physiologique → CH.
- si la comparaison porte sur son CARACTÈRE, son COMPORTEMENT, une
  disposition psychologique ou morale (courage, lâcheté, cupidité, bêtise,
  intelligence, etc.) → P, MÊME SI la cible elle-même est une personne.
Ce n'est PAS la même chose que classer par le domaine du fondement_commun en
général (E/O/A restent déterminés par la nature de la cible, sans cette
subtilité) — cette distinction physique/psychologique ne s'applique QUE
lorsque la cible est une personne.

Procédure : identifie d'abord QUI ou QUOI est réellement comparé au véhicule
(la cible, réponse 2). ⚠ Ne t'arrête pas à la première expression qui
ressemble à la cible en surface — si besoin, élargis mentalement la phrase
au-delà de la proposition immédiate pour trouver le VRAI référent (ex: une
expression comme "en mon penser" peut sembler désigner "ma pensée" alors que
le vrai sujet comparé, une fois la phrase entière prise en compte, est le
corps physique de la personne en train de rester allongée, immobile). Puis
classe cette entité :
- si c'est une personne → détermine la dimension physique vs psychologique
  ci-dessus (CH ou P).
- si c'est un état psychologique, une émotion, une sensation, une faculté
  cognitive (mémoire, imagination...) EN TANT QUE TEL, sujet grammatical
  autonome de sa propre action (ex: "mes émotions se cachaient" — les
  émotions agissent elles-mêmes) → P.
- si c'est un animal, une plante, ou un processus biologique non-humain → NH
- si c'est un objet fabriqué, une structure artificielle → O
- si c'est un élément naturel non-vivant (paysage, mer, ciel, météo,
  formation géologique...) → E
- si c'est une idée, une institution, une pratique sociale/culturelle
  (politique, religion, art, mariage, justice...) → A

Exemples (d'après Riccardo Barontini, 2026-07-10 et 2026-07-10 suite) :
- «Je bats lâchement en retraite... comme un rat» : cible = « il » (une
  personne). Riccardo juge que "battre en retraite" relève du MOUVEMENT
  PHYSIQUE du corps → CH (même si on pourrait aussi le lire autrement).
- «Pierre Castaneda s'y comporte comme un vrai chacal» (fondement=rapacité) :
  cible = Pierre Castaneda (une personne), MAIS le référent n'est pas son
  corps, c'est son COMPORTEMENT (rapacité = un trait moral/comportemental)
  → P, PAS CH. Même type de cible (personne nommée) que l'exemple du rat,
  catégorie différente à cause de la dimension visée.
- «...apparenté en mon penser au lycopode, à la fougère» (contexte élargi :
  le narrateur reste allongé, immobile, "en parfait état de légumerie") :
  la cible n'est PAS "mon penser" pris isolément — en élargissant la phrase,
  ce qui est réellement comparé au végétal est le CORPS du narrateur, immobile
  et végétatif → CH, PAS P, malgré la présence du mot "penser" en surface.
- «Mes émotions se cachaient comme des rats» : cible = « mes émotions »
  (un état psychologique agissant comme sujet autonome, pas une personne) → P.
- «L'île ressemblait à un rat» : cible = « l'île » (un élément naturel) → E.

⚠ Attention à la voix/au chant : la cible n'est PAS automatiquement la
personne qui parle/chante. Regarde ce que la phrase compare RÉELLEMENT :
- «une voix d'aéroport... annonça» : c'est LA VOIX elle-même qui agit/est
  décrite comme sujet, pas la personne → cible = « la voix » → A (qualité
  artistique/esthétique du son), PAS CH.
- «il chantait comme un rossignol» : ici c'est LA PERSONNE qui est le sujet
  de l'action de chanter, le véhicule décrit COMMENT ELLE chante → cible =
  « il » (la personne) → CH.
Distingue : si le nom (voix/chant/voice) est lui-même le sujet grammatical
de la phrase ou l'objet direct de la comparaison → cible = ce nom → A. Si
c'est la PERSONNE qui est le sujet et que voix/chant n'est qu'un détail
descriptif → cible = la personne → CH.

⚠ Expressions figées, comparaisons rhétoriques, et descriptions poétiques
détournées — ne prends PAS le nom le plus proche du véhicule au pied de la
lettre si la phrase ne parle pas vraiment de cette chose littérale :
- Locution figée sans référent littéral (ex: "ménager la chèvre et le
  chou" = essayer de contenter tout le monde) : il n'y a PAS de chèvre ou
  de chou réels dans la scène. La cible est le COMPORTEMENT/CONCEPT abstrait
  nommé par l'expression (ici : l'indécision, le compromis) → A.
- Énumération rhétorique de paires incompatibles (ex: "différents comme
  mouton et carpe, tambour et flûte") : la cible n'est ni le mouton ni la
  carpe — c'est la NOTION ABSTRAITE d'incompatibilité/différence que
  l'énumération illustre → A.
- Description poétique/violente détournée (ex: "un livre se fraye un
  chemin de loup dans votre gorge") : ne classe pas "chemin" comme un lieu
  physique (E) si la phrase décrit en réalité une sensation, une expérience
  de lecture, ou un effet ressenti — cherche ce que la phrase décrit
  VRAIMENT en train de se passer, pas le sens littéral du nom isolé.
- Si le véhicule est utilisé pour décrire l'apparence fantastique/grotesque
  d'un PERSONNAGE humain (ex: "un être composite avec une truffe de
  chien..." décrivant quelqu'un) → cible = ce personnage → CH, même si la
  description elle-même ressemble à une créature non-humaine.
Dans tous ces cas : identifie d'abord de QUOI la phrase parle VRAIMENT
(quel comportement, quelle notion, quel personnage) avant de choisir la
catégorie — ne t'arrête pas au nom syntaxiquement le plus proche du
véhicule si ce n'est pas le vrai sujet de la comparaison.

Réponds UNIQUEMENT avec ce JSON :
{{"vehicule": "...", "cible": "...", "fondement_commun": "...", "verification": "yes/no", "code": "CODE"}}"""

# ── OLLAMA CALL (mirrors Task 1's proven config: thinking ON, no format constraint,
#    large num_predict — NOT Task 2's original broken num_predict=200) ──────────
```

---

## Task 3 — Agentivité (dépendances spaCy, PAS de LLM)

Task 3 n'utilise aucun prompt LLM — classification humains/animaux/plantes
actif/passif/objet/complément via l'analyse de dépendances syntaxiques
spaCy (`morphosyntaxe/analyse_agentivite.py`), zéro appel qwen3/GPT.
