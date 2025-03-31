# Écopoétique


## Corpus

Le répertoire **CORPUS_TOTAL** contient l'ensemble du corpus au format txt. Ces fichiers sont issus de la conversion de fichiers epub ou pdf ou de la numérisation à partir d'une version papier du livre. La plupart des fichiers ont été post-traités pour faire figurer une phrase par ligne. Les éléments annexes au texte (sommaire, 4ème de couverture, etc) ont dans la mesure du possible été supprimés. Quelques rares textes contiennent de nombreux problèmes d'OCR (mauvaise accentuation, bout de phrases mélangés).

Le répertoire **TOKENS** contient l'analyse des tokens du chaque texte par Spacy. Ces fichiers sont constitués de trois colonnes indiquant le token, sa catégorie grammaticale et son lemme.

Le fichier **corpus_DigEco.csv** contient les métadonnées du corpus. Les décomptes de tokens, formes fléchies et lemmes sont basées sur les analyses Spacy. Note : le séparateur de colonne est la tabulation.


## Lexiques

3 type de lexiques ont permis l'extraction des entités liées à la biodiversité dans le corpus :
- un lexique constitué à partir d'un dump de **[Wikispecies](https://species.wikimedia.org/wiki/Accueil)** pour les êtres vivants
- le référentiel **[TaxRef](https://inpn.mnhn.fr/programme/documentation/referentiels-especes-taxref)**, qui liste l'intégralité des espèces vivantes présentes sur le territoire français (métropole et Outre-Mer)
- le thésaurus **[Loterre](https://loterre.istex.fr/fr/)**, qui contient une liste de termes liés au changement climatique et à l'anthropocène

Le lexique Wikispecies et les noms vernaculaires issus de Taxref ont été fusionnés pour créer des listes le plus exhaustives possibles pour les règnes du vivant Animalia (animaux), Fungi (champignons) et Plantae (plantes).


## Scripts

Les extractions des entités du corpus à partir des listes sont faites avec la commande bash `grep`, de façon à extraire également le contexte phrastique de chaque occurrence.

Deux pipelines ont été mises en place pour effectuer l'ensemble des opérations d'extraction, de filtrage et de traitement des données en une seule commande : `pipeline_animaux.sh` et `pipeline_plantes.sh`.

Ces scripts font appel aux scripts Python suivants :
- `grep_contexte.py` permet d'extraire le contexte phrastique des occurrences identifiées dans chaque fichier et de les écrire dans un fichier CSV avec l'entité correspondante.
- `remove_duplicates.py` supprime les doublons qui se crée lorsqu'une entité apparaît seule ou avec un qualificatif dans le lexique (exemple : "dorade" et dorade rose")
- `truncate_sentence.py` contient une fonction utilitaire pour réduire le contexte phrastique autour de l'occurrence de l'entité à un nombre de mots passé en paramètre
- `filter_*.py` contient des règles manuellement définies pour supprimer des occurrences non pertinentes (par exemple *if* en anglais alors qu'on cherche la plante « if »)
- `assign_category.py` permet d'assigner leur catégorie (mammifère, oiseau, etc.) aux entités animales
- `lemmatize.py` permet de retrouver le lemme des entités extraites. Ce script fait appel au lemmatiseur du français [LEFFF](https://github.com/ClaudeCoulombe/FrenchLefffLemmatizer) à installer avant utilisation de la pipeline



## Résultat des extractions

Le répertoire resultats contient l'état actuel de l'extraction/filtrage des différentes entités. Les fichiers `hapax_*.csv` correspondent à des entités très ambiguës que nous avons extraites manuellement avant de les éliminer des listes taxref/wiki. Elles ont été rajoutées manuellement à l'état courant des résultats.




