import re

with open('/tmp/evaluate_all_goldsets_v5_server.py', encoding='utf-8') as f:
    content = f.read()

# Replace animaux section with v3 examples
new_animaux = '''"animaux": """
EXEMPLES — termes animaux (indépendants du jeu d\'évaluation):

référentiel (animal réel):
• "Le fermier nourrissait ses poules chaque matin avant le lever du soleil."
  → poules = référentiel (vraies volailles d\'élevage)
• "Un aigle tournoyait lentement au-dessus des rochers calcaires."
  → aigle = référentiel (oiseau réel observé dans la nature)
• "La rivière grouillait de truites que les pêcheurs tentaient d\'attraper."
  → truites = référentiel (poissons réels dans une rivière)
• "Elle tira le chat par la queue pour le faire descendre de la table."
  → chat = référentiel (animal domestique présent physiquement)

figuré (métaphore, comparaison, expression):
• "Monter sur ses grands chevaux — il s\'est mis en colère pour rien."
  → chevaux = figuré (expression idiomatique, pas de vrais chevaux)
• "Elle avait un caractère de cochon — personne ne pouvait la supporter."
  → cochon = figuré (expression pour décrire le caractère d\'une personne)
• "Il travaillait comme un bœuf du matin au soir sans jamais se plaindre."
  → bœuf = figuré (comparaison pour décrire l\'effort humain)
• "Avoir d\'autres chats à fouetter — j\'ai des choses plus importantes à faire."
  → chats = figuré (expression idiomatique française)
• "Les candidats tombaient comme des mouches face aux questions du jury."
  → mouches = figuré (comparaison, pas de vraies mouches)""",'''

# Replace loterre section with v3 examples
new_loterre = '''"loterre": """
EXEMPLES — termes écologiques/géographiques Loterre (indépendants du jeu d\'évaluation):

référentiel (lieu ou concept écologique réel):
• "Les scientifiques étudient l\'écosystème du lac depuis vingt ans."
  → écosystème = référentiel (vrai concept écologique dans un contexte scientifique)
• "La déforestation détruit les forêts tropicales à un rythme alarmant."
  → forêts = référentiel (vraies forêts détruites par l\'activité humaine)
• "Le biologiste traversait la steppe mongole à dos de cheval depuis des jours."
  → steppe = référentiel (vrai biome géographique traversé physiquement)
• "L\'expédition longeait le fleuve Amazone pendant trois semaines."
  → fleuve = référentiel (vrai fleuve parcouru lors d\'une expédition)
• "La biodiversité des récifs coralliens est menacée par le réchauffement."
  → biodiversité = référentiel (vrai concept écologique dans un rapport scientifique)
• "Les plages de Normandie furent le théâtre du débarquement allié en 1944."
  → plages = référentiel (vrais lieux géographiques, contexte historique)
• "La montagne culminait à 4807 mètres — le Mont Blanc, toit de l\'Europe."
  → montagne = référentiel (vrai sommet géographique précis)

figuré (métaphore, expression idiomatique):
• "Prêcher dans le désert — personne n\'écoutait ses avertissements répétés."
  → désert = figuré (expression idiomatique, parler sans être entendu)
• "Déplacer des montagnes — elle ferait tout pour sauver son entreprise."
  → montagnes = figuré (expression idiomatique, effort surhumain)
• "Ce n\'est pas la mer à boire — il suffit de remplir deux formulaires."
  → mer = figuré (expression idiomatique, ce n\'est pas si difficile)
• "Naviguer en eaux troubles — la négociation devenait de plus en plus risquée."
  → eaux = figuré (métaphore pour une situation dangereuse et incertaine)
• "L\'autoroute était une mer de lumières rouges à perte de vue."
  → mer = figuré (métaphore visuelle pour un embouteillage)
• "Sa carrière était un désert depuis son licenciement il y a deux ans."
  → désert = figuré (métaphore pour une période creuse, sans activité)
• "Enseveli dans la forêt de ses cheveux, il ne voyait plus rien autour."
  → forêt = figuré (métaphore pour des cheveux très épais)
• "Ils vivaient dans un océan de dettes depuis la faillite de la société."
  → océan = figuré (métaphore pour une grande quantité accablante)
• "Son habitat naturel était la bibliothèque — il n\'en sortait jamais."
  → habitat naturel = figuré (ironie, pas un vrai habitat écologique)
• "Remonter à la surface — il essayait de se sortir de sa dépression."
  → surface = figuré (métaphore aquatique pour surmonter des difficultés)""",'''

content = re.sub(r'"animaux": """.*?""",', new_animaux, content, flags=re.DOTALL)
content = re.sub(r'"loterre": """.*?""",', new_loterre, content, flags=re.DOTALL)
content = content.replace('eval_animaux_v5_results.csv', 'eval_animaux_v6_results.csv')
content = content.replace('eval_plantes_v5_results.csv', 'eval_plantes_v6_results.csv')
content = content.replace('eval_loterre_v5_results.csv', 'eval_loterre_v6_results.csv')
content = content.replace('TASK 1 — LITERAL/FIGURATIVE EVALUATION  v5', 'TASK 1 — LITERAL/FIGURATIVE EVALUATION  v6')

with open('/tmp/evaluate_all_goldsets_v6.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("v6 created successfully")
