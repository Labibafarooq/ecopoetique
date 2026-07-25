"""
Estimates the false-positive rate among the 533 unique names that
extract_humains_multilingual.py's multilingual-only pass (XLM-R) added
on top of the French spaCy model, in the 72-novel partial run
(dépendants_HUMAINS_multilingual.csv, confirmed to cover exactly 72
novels, 18,083 rows: 16,676 fr_model + 1,407 multilingual_model).

METHOD (2nd, corrected version):
A first attempt used an automated POS-tag heuristic (lowercase the name
in its real sentence, re-run through fr_core_news_lg, check the tag).
That heuristic was found unreliable on manual review: it wrongly flagged
genuine foreign/rare names (Abdelkader, Anissa, Azzouze, Ourida, Wafaa,
Soraya...) as "common nouns," because spaCy's French model doesn't
recognize unfamiliar names and mis-tags them once decapitalized -
exactly the names this multilingual pass exists to catch. Trusting it
would have overstated the false-positive rate.

This version instead uses ONLY:
1. Curated, evidence-based lists built by manually reading every one of
   the ~179 heuristic-flagged candidates' real sentence context (not
   guessed, not pattern-matched) - true common nouns/titles/religious
   references, kept ONLY when the sentence context leaves no reasonable
   doubt (e.g. "Dieu" verified via full-sentence reading across all 6+
   sampled occurrences to be used only as "God", never as a name).
2. Curated fictional/mythological and brand/org/artwork lists, verified
   against the actual data (all entries confirmed present).
3. Regex-detected tokenization artifacts (hyphenation split across a
   line break, not rejoined).
4. A separate "ambiguous / functions as a nickname" bucket for cases
   like "M. Miroir" or "Tordu" that are common words being used AS a
   literary character's nickname within the novel - these are a
   genuinely different case from an outright false positive (the
   character really is being referred to by that word throughout the
   text) and are reported separately rather than folded into either
   bucket, so the headline number isn't inflated or deflated by a
   judgment call that could go either way.
5. Everything else = plausible real name (the default, not a guess -
   confirmed by reading a sample of this bucket too, see script output).

Runs entirely on CPU. No GPU, no Ollama/LLM call - pure Python + regex
+ a fixed lookup against manually-curated lists.
"""
import csv
import re
from collections import Counter

INPUT = "dépendants_HUMAINS_multilingual.csv"

FICTIONAL_MYTHOLOGICAL = {
    "barbie", "don quichotte", "minotaure", "petit prince", "prince",
    "schtroumpf grognon", "tintin", "yoda",
    # added on full manual read of the "plausible_real_name" bucket:
    "betty boop", "bovary", "homais", "caliban", "dracula", "d’artagnan",
    "d'artagnan", "golem", "gargantua", "jiminy cricket", "jane eyre",
    "karamazov", "lady chatterley", "léviathan", "lolita",
    "michel strogoff", "mister freeze", "moloch", "nosferatu", "obélix",
    "petit nicolas", "philip marlowe", "phèdre", "pieds nickelés",
    "quasimodo", "robinson crusoé", "salammbô", "satanas", "schéhérazade",
    "spirou", "teddy bear", "zorro", "zorro-don diego", "jéhovah",
    "highlander",
}
BRAND_ORG_ARTWORK = {
    "chanel", "libé", "libe", "tsahal", "pietà", "pieta",
    # added on full manual read:
    "buitoni", "prefab sprout", "metallica", "smiths", "vogue", "rexona",
    "versace", "mein kampf", "goldwyn mayer", "n.w.a", "armani", "prozac",
    "nirvana", "queen",
}
PLACE_NAME = {
    "angleterre", "sotchi", "vichy",
}

# Built by manually reading the real sentence context for every one of
# these (not pattern-matched) - unambiguous common nouns, titles, or
# religious/biblical references, never used as a person's proper name
# in the sampled sentence(s).
TRUE_COMMON_NOUN_TITLE = {
    "dieu": "God (religious common noun) - verified across 6+ sampled sentences, all non-name usage",
    "mademoiselle": "title (\"Mademoiselle Elsa\" - title prefixing a real name, not itself a name)",
    "maman": "\"Mom\" - generic term of address",
    "monseigneur": "title (\"Monseigneur Feltin\" - title prefixing a real name)",
    "seigneur": "\"Lord\" - religious/honorific common noun",
    "ancêtre": "\"the Ancestor\" - common noun with definite article (l'Ancêtre)",
    "maître": "\"the Master/teacher\" - title with definite article (Le Maître)",
    "martyr": "common noun, not used as a proper name in context",
    "messie": "\"Messiah\" - religious common noun",
    "messager": "\"the Messenger\" - common noun with definite article",
    "héros": "\"Hero\" - common noun",
    "vierge": "\"the Virgin\" (Mary) - religious common noun",
    "genèse": "\"Genesis\" - biblical book title, not a person",
    "coran": "\"Quran\" - religious text title, not a person",
    "temps": "\"Time\" - abstract common noun",
    "autre": "\"other\" - pronoun/adjective, not a name",
    # added on full manual read:
    "bureau": "\"office/desk\" - common noun",
    "fainéant": "\"lazy/do-nothing\" - adjective used as a nickname-like description",
    "grande": "\"big/great\" - adjective, no capitalized-name context found",
    "haut": "\"high/tall\" - adjective",
    "intendant": "\"steward/manager\" - occupation title, common noun",
    "paléontologue": "\"paleontologist\" - occupation noun, common noun",
    "proviseur": "\"headmaster\" - occupation/title, common noun",
    "tante": "\"aunt\" - kinship common noun",
    "camelot": "\"camelot du roi\" - historical French term for a street vendor/pamphleteer, not a person's name",
    "sioux": "\"ruses de Sioux\" - fixed French idiom meaning \"cunning tricks,\" not a reference to a specific person",
}

# Genuinely ambiguous: the word IS a common noun, but the sentence shows
# it being used AS a character's nickname/appellation within the novel
# (a real literary device, not an extraction error) - reported
# separately, not counted as a false positive nor as a clean real name.
NICKNAME_AMBIGUOUS = {
    "cicatrice": "\"Scar\" - reads as a nickname for a character in context",
    "tordu": "\"Twisted\" - reads as a nickname (\"-Tordu, qui avait de temps à autre des crises...\")",
    "soigne": "ambiguous short fragment, insufficient context to be certain",
    "mauvais": "\"the Bad man\" - reads as a nickname/appellation (\"l'homme Mauvais\")",
    "miroir": "\"M. Miroir\" - explicitly used as a character's nickname in a list of nicknames",
    "poison": "capitalized with explicit \"P majuscule\" - authorial signal it's being used as a name/epithet",
    "divine": "\"la Divine\" - reads as a nickname",
    "faucheuse": "\"the Reaper\" - personification, borderline nickname-as-character",
    "rouge": "\"Red\" - could be a nickname or literal color reference, insufficient context",
    "pilote": "\"Pilote\" - reads as a callsign/nickname in context",
    "chérie": "\"darling\" - term of endearment, could be used as a pet name for a specific character",
    "silence": "capitalized, put \"on a list\" per the sentence - ambiguous, insufficient context",
    "empereur": "\"l'Empereur\" - likely a title referring to a real historical figure (e.g. Napoleon), not itself a name",
    "saint": "could prefix a real name (Saint-X) or be a standalone religious title - insufficient context",
    "sainte": "same as 'saint' - ambiguous title vs. name-prefix",
    "nobel": "likely \"prix Nobel\" (the award, common noun) rather than a person reference - insufficient context to be fully certain",
}

HYPHEN_ARTIFACT_RE = re.compile(r"-\s+\S|\S\s+-\S")


def load_multilingual_only_rows():
    with open(INPUT, encoding="utf-8") as f:
        r = csv.reader(f, delimiter="\t")
        header = next(r)
        rows = list(r)
    tok_idx = header.index("token_lexique")
    src_idx = header.index("source")
    sent_idx = header.index("truncated_sentence")
    file_idx = header.index("fichier")
    novels = set()
    out = []
    for row in rows:
        if len(row) > src_idx and row[src_idx] == "multilingual_model":
            out.append((row[tok_idx], row[sent_idx]))
        if len(row) > file_idx:
            novels.add(row[file_idx])
    return out, novels


def classify(name):
    lname = name.strip().lower()

    if HYPHEN_ARTIFACT_RE.search(name):
        return "tokenization_artifact"

    if lname in FICTIONAL_MYTHOLOGICAL:
        return "fictional_mythological"

    if lname in BRAND_ORG_ARTWORK:
        return "brand_org_artwork"

    if lname in PLACE_NAME:
        return "place_name"

    if lname in TRUE_COMMON_NOUN_TITLE:
        return "common_noun_title_confirmed"

    if lname in NICKNAME_AMBIGUOUS:
        return "ambiguous_nickname_as_name"

    if len(name.strip(".")) <= 2:
        return "fragment_too_short_to_judge"

    return "plausible_real_name"


def main():
    rows, novels = load_multilingual_only_rows()
    total_occurrences = len(rows)
    print(f"Novels covered by this partial run: {len(novels)}")
    print(f"Total multilingual-only occurrences: {total_occurrences}")

    occ_counter = Counter()
    for name, _ in rows:
        occ_counter[name] += 1
    unique_names = sorted(occ_counter.keys())
    print(f"Unique names: {len(unique_names)}")
    print()

    results = {name: classify(name) for name in unique_names}

    cat_unique_counts = Counter(results.values())
    cat_occ_counts = Counter()
    for name, cat in results.items():
        cat_occ_counts[cat] += occ_counter[name]

    print("=== By UNIQUE NAME ===")
    for cat, cnt in cat_unique_counts.most_common():
        pct = 100 * cnt / len(unique_names)
        print(f"  {cat:32s} {cnt:4d}  ({pct:5.1f}%)")

    print()
    print(f"=== By TOTAL OCCURRENCES ===")
    for cat, cnt in cat_occ_counts.most_common():
        pct = 100 * cnt / total_occurrences
        print(f"  {cat:32s} {cnt:4d}  ({pct:5.1f}%)")

    with open("multilingual_name_classification_v2.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "category", "occurrences"])
        for name in unique_names:
            w.writerow([name, results[name], occ_counter[name]])
    print()
    print("Full classification written to multilingual_name_classification_v2.csv")


if __name__ == "__main__":
    main()
