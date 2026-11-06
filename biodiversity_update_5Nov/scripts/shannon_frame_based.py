"""
Mesure Shannon standardisee par la quantite de texte (frames de 1000 tokens),
suivant la logique de Langer et al. (2021), demandee par Riccardo (email du
2026-11-03) comme alternative a Shannon_rarefied_{20,50} (qui standardise par
NOMBRE D'OCCURRENCES ecologiques plutot que par quantite de texte).

Methode (telle que specifiee par Riccardo, globale/pooled, PAS de decoupage
par categorie taxonomique pour cette premiere version) :
  1. decouper le texte en frames sequentielles de 1000 tokens
  2. tirer aleatoirement 10 frames distinctes (sans remise) -> echantillon de
     10 000 tokens
  3. dans cet echantillon, garder toutes les occurrences ecologiques
     (animal + plante + champignon + loterre + taxon, regroupees)
  4. Shannon H = -sum(p_i * ln(p_i)) sur les frequences relatives des lemmes
  5. repeter 100 fois, moyenner H (+ richesse + abondance)

Localisation des occurrences dans le flux de tokens : ENTITES_TOTAL.csv /
BESTSELLERS_ENTITES_MERGED.csv ne stockent que le mot trouve + sa phrase de
contexte (pas de position). On relocalise chaque occurrence en cherchant sa
phrase de contexte comme sous-chaine du texte brut du roman (un curseur
monotone par roman resout les phrases dupliquees, en supposant que les lignes
du CSV d'entites suivent l'ordre de lecture du texte). Les phrases tronquees
par truncate_sentence.py (>50 mots) restent des sous-chaines exactes de la
phrase originale, donc cette recherche par sous-chaine fonctionne aussi dans
ce cas.

Tokenisation : regex \\w+ (mots uniquement, ponctuation ignoree) -- un choix
simple et explicite pour cette nouvelle mesure, applique de maniere uniforme ;
ne cherche pas a reproduire exactement l'ancien nb_tokens (dont le tokeniseur
d'origine n'est pas retrouve dans ce depot).

Usage:
    python3 shannon_frame_based.py <ENTITES.csv> <TEXT_DIRS (comma-sep)> <FICHIER_METADONNEES.csv>
"""
import sys
import csv
import random
import re
from collections import Counter
from math import log
from pathlib import Path

csv.field_size_limit(10_000_000)

FRAME_SIZE = 1000
N_FRAMES_SAMPLE = 10
TRIALS = 100
TOKEN_RE = re.compile(r"\w+", re.UNICODE)

ENTITES_CSV, TEXT_DIRS, FICHIER_METADONNEES = sys.argv[1], sys.argv[2], sys.argv[3]
TEXT_DIRS = [Path(d) for d in TEXT_DIRS.split(",")]


def find_text_file(filename):
    for d in TEXT_DIRS:
        p = d / filename
        if p.exists():
            return p
    return None


def tokenize_with_offsets(text):
    """Returns (list_of_tokens, list_of_char_start_offsets) for \\w+ tokens."""
    tokens, offsets = [], []
    for m in TOKEN_RE.finditer(text):
        tokens.append(m.group())
        offsets.append(m.start())
    return tokens, offsets


def char_offset_to_token_index(offsets, char_pos):
    """Index of the first token starting at or after char_pos (binary search)."""
    lo, hi = 0, len(offsets)
    while lo < hi:
        mid = (lo + hi) // 2
        if offsets[mid] < char_pos:
            lo = mid + 1
        else:
            hi = mid
    return lo


def shannon(lemmes):
    if not lemmes:
        return 0.0
    counts = Counter(lemmes)
    n = len(lemmes)
    H = 0.0
    for c in counts.values():
        p = c / n
        H -= p * log(p)
    return H


# ── load entity rows, grouped by novel ──────────────────────────────────────
by_file = {}
with open(ENTITES_CSV, encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        by_file.setdefault(r["fichier"], []).append(r)

print(f"Entites chargees: {sum(len(v) for v in by_file.values())} lignes, {len(by_file)} fichiers")

# ── load novel list from metadata file ──────────────────────────────────────
with open(FICHIER_METADONNEES, encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter="\t")
    fieldnames = list(reader.fieldnames)
    meta_rows = list(reader)

results = {}  # filename -> (richness_mean, abundance_mean, shannon_mean) or None

n_ok, n_excluded_short, n_excluded_notext, n_unmatched_total, n_rows_total = 0, 0, 0, 0, 0

for row in meta_rows:
    fn = row["File"]
    text_path = find_text_file(fn)
    if text_path is None:
        results[fn] = None
        n_excluded_notext += 1
        continue

    text = text_path.read_text(encoding="utf-8", errors="replace")
    tokens, offsets = tokenize_with_offsets(text)
    total_tokens = len(tokens)
    n_frames = total_tokens // FRAME_SIZE

    if n_frames < N_FRAMES_SAMPLE:
        results[fn] = None
        n_excluded_short += 1
        continue

    # locate each entity occurrence's frame index, with a monotonic search
    # cursor to resolve duplicate context sentences in file-order
    entity_frames = []  # list of (frame_index, lemme)
    cursor = 0
    for r in by_file.get(fn, []):
        n_rows_total += 1
        ctx = r["contexte"]
        pos = text.find(ctx, cursor)
        if pos == -1:
            pos = text.find(ctx)  # retry from start (out-of-order row)
        if pos == -1:
            n_unmatched_total += 1
            continue
        cursor = pos + 1
        tok_idx = char_offset_to_token_index(offsets, pos)
        if tok_idx >= total_tokens:
            continue
        frame_idx = tok_idx // FRAME_SIZE
        if frame_idx >= n_frames:
            continue  # falls in a trailing partial frame, excluded by design
        entity_frames.append((frame_idx, r["lemme"]))

    # group entity lemmes by frame for fast Monte Carlo sampling
    frame_to_lemmes = {}
    for frame_idx, lemme in entity_frames:
        frame_to_lemmes.setdefault(frame_idx, []).append(lemme)

    richness_vals, abundance_vals, shannon_vals = [], [], []
    for _ in range(TRIALS):
        sampled_frames = random.sample(range(n_frames), N_FRAMES_SAMPLE)
        pooled = []
        for fi in sampled_frames:
            pooled.extend(frame_to_lemmes.get(fi, []))
        richness_vals.append(len(set(pooled)))
        abundance_vals.append(len(pooled))
        shannon_vals.append(shannon(pooled))

    results[fn] = (
        sum(richness_vals) / TRIALS,
        sum(abundance_vals) / TRIALS,
        sum(shannon_vals) / TRIALS,
    )
    n_ok += 1

print(f"Fichiers traites: {n_ok} ok, {n_excluded_short} exclus (<{N_FRAMES_SAMPLE} frames), "
      f"{n_excluded_notext} sans texte trouve")
print(f"Occurrences ecologiques: {n_rows_total} vues, {n_unmatched_total} non localisees "
      f"({100*n_unmatched_total/max(n_rows_total,1):.2f}%)")

# ── write results into metadata file ────────────────────────────────────────
new_cols = ["EcoRichness_frame10k", "EcoAbundance_frame10k", "Shannon_frame10k"]
for col in new_cols:
    if col not in fieldnames:
        fieldnames.append(col)

for row in meta_rows:
    res = results.get(row["File"])
    if res is None:
        row["EcoRichness_frame10k"] = ""
        row["EcoAbundance_frame10k"] = ""
        row["Shannon_frame10k"] = ""
    else:
        row["EcoRichness_frame10k"], row["EcoAbundance_frame10k"], row["Shannon_frame10k"] = res

with open(FICHIER_METADONNEES, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
    writer.writeheader()
    writer.writerows(meta_rows)

print(f"Colonnes ecrites dans {FICHIER_METADONNEES}: {new_cols}")
