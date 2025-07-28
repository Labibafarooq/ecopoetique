import sys
import pandas as pd

if len(sys.argv) < 3:
	print("Usage : python filter_tokens.py input.csv output.csv")
	exit(1)

infile = sys.argv[1]
outfile = sys.argv[2]
	
df = pd.read_csv(infile, sep='\t', dtype = {'fichier': str, 'token_lexique': str, 'contexte': str})
df = df.rename(columns={'truncated_sentence':'contexte'})

print("Nombre initial d'occurrences : {}".format(len(df)))


# Filtre par token
filtre = df[
    ((df['fichier'] == 'Apperry-Yann_Farrago.txt') & (df['token_lexique'].isin(['aches', 'if']))) |
    ((df['fichier'] == 'Zouari-Fawzia_Le-corps-de-ma-mere.txt') & (df['token_lexique'] == 'mélia')) |
    ((df['fichier'] == 'Fontaine-Naomi_Kuessipan.txt') & (df['token_lexique'] == 'ache')) |
    ((df['fichier'].isin([
        "Angot-Christine_Le-Voyage-dans-l'Est.txt", "Assayas-Michka_Exhibition.txt",
        "Aubry-Suzanne_Ma-vie-entre-tes-mains.txt", "Audeguy-Stephane_Nous-autres.txt",
        "Binet-Laurent_La-septieme-fonction-du-langage.txt",
        "Chambaz-Bernard_Dernieres-nouvelles-du-Martin-Pêcheur.txt",
        "Clermont-Stefanie_le-jeu-de-la-musique.txt", "Corvisier-Stephane__Reine-de-nuit.txt",
        "Cusset-Catherine_L-autre-qu-on-adorait.txt", "Dantzig-Charles_Un-film-damour.txt",
        "Deville-Patrick_Equatoria.txt", "Deville-Patrick_Kampuchea.txt",
        "Dreyfus-Arthur_Journal-sexuel-dun-garçon-daujourdhui.txt",
        "Dupont-Eric_La-fiancee-americaine.txt", "Edde-Dominique_Kamal-Jann.txt",
        "Enard-Mathias_Boussole.txt", "Fleischer-Alain_L-amant-en-culottes-courtes.txt",
        "Jobidon-Gilles_Le-tranquille-affligé.txt", "Fontaine-Naomi_Kuessipan.txt",
        "Laurens-Camille_Celle-que-vous-croyez.txt", "Leger-Nathalie_Supplement-a-la-vie-de-Barbara-Loden.txt",
        "LeTellier-Herve_Lanomalie.txt", "LeTellier-Herve_Lanomalie.txt",
        "Liberati-Simon_Jayne-Mansfield-1967.txt", "Martin-Chauffier-Gilles_Lere-des-suspects.txt",
        "Mbougar-Sarr-Mohamed_Silence-du-choeur.txt", "Message-Vincent_Cora-dans-la-spirale.txt",
        "Mouawad-Wajdi_Anima.txt", "Paventi-Eza_Les-Souliers-de-Mandela.txt",
        "Peeters-Edouard_Nephros.txt", "Reinhardt-Eric_Cendrillon.txt",
        "Robles-Jean_Là-où-les-tigres-sont-chez-eux.txt"
    ])) & (df['token_lexique'] == 'if')) |
    ((df['token_lexique'] == 'foin') & df['contexte'].str.contains('tout un foin')) |
    (df['token_lexique'] == 'papier à musique') |
    ((df['token_lexique'] == 'sanguine') & (df['contexte'].str.contains('pression sanguine'))) |
    ((df['token_lexique'] == 'sanguine') & (df['contexte'].str.contains('transfusion sanguine'))) |
    ((df['token_lexique'] == 'sanguine') & (df['contexte'].str.contains('circulation sanguine'))) |
    ((df['token_lexique'] == 'lotus') & (df['contexte'].str.contains('en lotus'))) |
    ((df['token_lexique'] == 'lotus') & (df['contexte'].str.contains('posture du lotus'))) |
    ((df['token_lexique'] == 'lotus') & (df['contexte'].str.contains('position du lotus'))) |
    ((df['token_lexique'] == 'garou') & (df['contexte'].str.contains('loup-garou'))) |
    ((df['token_lexique'] == 'moutarde') & 
     (df['contexte'].str.contains('gaz moutarde') | df['contexte'].str.contains('verre à moutarde'))) |
    ((df['token_lexique'] == 'tabacs') & (df['contexte'].str.contains('bars-tabacs'))) |
    ((df['token_lexique'] == 'tabac') & (df['contexte'].str.contains('bar-tabac|faire un tabac|passer à tabac'))) |
    ((df['token_lexique'] == 'bouvier') & (df['contexte'].str.contains('bouvier bernois'))) |
    ((df['token_lexique'] == 'pomme') & (df['contexte'].str.contains('pomme d’Adam|pomme de douche'))) |
    ((df['token_lexique'] == 'radis') & (df['contexte'].str.contains('pas un radis'))) |
    ((df['token_lexique'] == 'coucou') & (df['contexte'].str.contains('faire coucou|fait coucou|coucou de la main|pendule à coucou'))) |
    (df['token_lexique'] == 'joli cœur') | (df['token_lexique'] == 'jaune d’œuf') | (df['token_lexique'] == 'phénix') | (df['token_lexique'] == 'goutte de lait') |
    ((df['token_lexique'] == 'douce-amère') & (df['contexte'].str.contains('expression douce-amère'))) |
    ((df['token_lexique'] == 'carotte') & (df['contexte'].str.contains('poil de carotte'))) |
    ((df['token_lexique'] == 'asperge') & (df['contexte'].str.contains('asperge le visage|asperge d’eau|asperge d’essence|s’asperge|m’asperge')))
]



print("Taille du filtre : {}".format(len(filtre)))


# Trouver les lignes dans df qui ne sont pas dans les df filtrés
df_new = df[~df.index.isin(filtre.index)]

print("Nombre d'occurrences après premier filtrage : {}".format(len(df_new)))

df_new.to_csv(outfile, sep='\t', index=False)

