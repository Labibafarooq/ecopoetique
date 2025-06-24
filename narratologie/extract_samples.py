import os
from glob import glob

#fichiers = ['../CORPUS_TOTAL/Rolin-Jean_Un-chien-mort-apres-lui.txt', '../CORPUS_TOTAL/Hunzinger-Claudie_Un-chien-a-ma-table.txt', '../CORPUS_TOTAL/Autissier-Isabelle_Soudain-seuls.txt', '../CORPUS_TOTAL/Senges-Pierre_Ruines-de-Rome.txt', '../CORPUS_TOTAL/Miano-Leonora_Rouge-imperatrice.txt', '../CORPUS_TOTAL/Flahaut-Thomas_Ostwald.txt', '../CORPUS_TOTAL/Kerangal-Maylisde_Naissance-dun-pont.txt', '../CORPUS_TOTAL/Hunzinger-Claudie_Les-grands-cerfs.txt', '../CORPUS_TOTAL/Binet-Laurent_La-septieme-fonction-du-langage.txt', '../CORPUS_TOTAL/Mbougar_La-plus-secrete-memoire-des-hommes.txt', '../CORPUS_TOTAL/Bienne-Gisele_La-malchimie.txt', '../CORPUS_TOTAL/Houellebecq-Michel_La-carte-et-le-territoire.txt', '../CORPUS_TOTAL/Simonnot-Maud_LEnfant-celeste.txt', '../CORPUS_TOTAL/Nirsimloo-Anenden-Ananda_Eve-de-ses-decombres.txt', '../CORPUS_TOTAL/Rodier-Jean_En-remontant-les-ruisseaux.txt', '../CORPUS_TOTAL/Filhol-Elizabeth_Doggerland.txt', '../CORPUS_TOTAL/Bofane-In-Koli-Jean_Congo_inc._le_testament_de_Bismarck.txt', '../CORPUS_TOTAL/Reverdy-ThomasB_Climax.txt', '../CORPUS_TOTAL/Slimani-Leila_Chanson-douce.txt', '../CORPUS_TOTAL/Mouawad-Wajdi_Anima.txt']

def extraire_lignes(lignes, fichier_sortie):
    

    total = len(lignes)
    resultats = []

    # 10 premières lignes
    resultats.append('\n\n--- DEBUT ---\n\n')
    resultats.extend(lignes[:25])

    # Lignes à 35%, 50% et 75%
    for ratio in [0.35, 0.50, 0.75]:
        index = int(total * ratio)
        debut = max(0, min(index, total - 25))
        resultats.append(f'\n\n--- {int(ratio * 100)}% ---\n\n')
        resultats.extend(lignes[debut:debut + 25])

    # 10 dernières lignes
    resultats.append('\n\n--- FIN ---\n\n')
    resultats.extend(lignes[-25:])


    with open(fichier_sortie, 'w', encoding='utf-8') as f:
        f.writelines(resultats)


os.mkdir('narrato_extraits', exist_ok=True)

for filename in glob('../CORPUS_TOTAL/*.txt'):
	with open(filename, 'r', encoding='utf-8') as f:
		    lignes = f.readlines()

	output = os.path.basename(filename)
	extraire_lignes(lignes, os.path.join('narrato_extraits', 'narrato_sample_' + output))
