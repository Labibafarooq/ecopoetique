# Biodiversity update — response to Riccardo's email of 2026-11-03

This is my response, point by point, to the email Riccardo sent on
2026-11-03 (biodiversity indices follow-up, with two attachments:
`decomptes_totaux.csv` and Langer et al. 2021). I read both in full before
building any of this. Neither needed to be modified — they were reference
material (his old count file, to match its exact column structure, and the
paper, to match its sampling method), both now fully incorporated below.
For provenance, I've included exact copies of both in
`reference_originaux_riccardo/` in this same folder.

## File paths — where everything lives

| File (in this folder) | What it is | Source / where the live data actually lives in the repo |
|---|---|---|
| `decomptes_totaux_DigEco.csv` | Rebuilt décomptes totaux, DigEco | Built from `resultats/corpus_principal/ENTITES_TOTAL.csv` (entity data) + `corpus_DigEco.csv` (metadata/lexical stats). Repo copy: `resultats/corpus_principal/decomptes_totaux_AJOUR_20261105.csv` |
| `decomptes_totaux_Bestsellers.csv` | Rebuilt décomptes totaux, Bestsellers | Built from `resultats/bestsellers/BESTSELLERS_ENTITES_MERGED.csv` + `corpus_Bestsellers.csv`. Repo copy: `resultats/bestsellers/decomptes_totaux_bestsellers_AJOUR_20261105.csv` |
| `decomptes_totaux_PRIX_ECOLOGIE.csv` | Rebuilt décomptes totaux, PRIX_ECOLOGIE (didn't exist before) | Built from `resultats/corpus_principal/ENTITES_TOTAL.csv` + `corpus_PRIX_ECOLOGIE.csv`. Repo copy: `resultats/decomptes_totaux_PRIX_ECOLOGIE_20261105.csv` |
| `shannon_frame10k_DigEco.csv` | Frame-based Shannon extract, DigEco | Same 3 columns also live directly in `corpus_DigEco.csv` (repo root) as `EcoRichness_frame10k`/`EcoAbundance_frame10k`/`Shannon_frame10k`, alongside every other existing biodiversity index |
| `shannon_frame10k_Bestsellers.csv` | Frame-based Shannon extract, Bestsellers | Same columns live in `corpus_Bestsellers.csv` (repo root) |
| `shannon_frame10k_PRIX_ECOLOGIE.csv` | Frame-based Shannon extract, PRIX_ECOLOGIE | Same columns live in `corpus_PRIX_ECOLOGIE.csv` (repo root) |
| `scripts/build_decomptes_totaux.py` | The script I used to build the 3 décomptes totaux files | Original/live copy: `scripts/build_decomptes_totaux.py` |
| `scripts/shannon_frame_based.py` | The script I used to build the frame-based Shannon columns | Original/live copy: `scripts/shannon_frame_based.py` |
| `PROMPTS_DOCUMENTATION.md` | All task prompts, verbatim | Original/live copy: `PROMPTS_DOCUMENTATION_20261105.md` (repo root); each section cites its own source script path individually |
| `reference_originaux_riccardo/` | Exact copies of what Riccardo sent | Original/live copy: `biodiversity_3Nov/` (repo root) |

Underlying novel texts used for the frame-based Shannon measure: `CORPUS_TOTAL/`
(DigEco + PRIX_ECOLOGIE) and `CORPUS_Bestsellers/` (Bestsellers, falling
back to `CORPUS_TOTAL/` for the 36 novels shared with DigEco).

## 1. "Where do things stand?" — status update

Two things were running in parallel to this:

- **Narratology (GPT comparison)**: I ran qwen3:30b (local), GPT-4o-mini,
  and GPT-4o (full) all on the identical 38-novel held-out test set, same
  gold file, same prompts (see `PROMPTS_DOCUMENTATION.md`, Task 0).
  Headline result: GPT-4o (full) now beats local qwen3:30b outright on
  RÉGIME NARRATIF (73.7% vs 52.6%), ESPACE (78.9% vs 42.1%), and MODE
  NARRATIF (52.6% vs 44.7%) — the three categories that had resisted months
  of local prompt-engineering. INTRIGUE stayed flat across all three models
  (47–50%), which suggests a genuine definitional/architecture issue rather
  than a model-capability one.
- **Biodiversity**: covered in full below.

## 2. Prompts used for the different tasks

`PROMPTS_DOCUMENTATION.md` — verbatim extraction from the actual production
scripts (not paraphrased, not redescribed from memory), covering:
- Task 0 (narratologie, map-reduce)
- Task 1 — animaux/plantes, and Loterre separately (distinct prompt)
- Task 2 — the 12-question structural-metaphor decision tree
- Task 4.5 — compare-target category (CH/P/NH/O/E/A)
- Task 3 — noted as using no LLM at all (pure spaCy dependency parsing)

## 3. Updated `décomptes_totaux`, all 3 corpora

Riccardo's email: *"I would also need a file like the one I've attached ...
The version I have is not up to date with the latest changes we made to the
counts and I think there are not the three corpus."* I checked both claims
before rebuilding rather than assuming he was right:

- His copy (`biodiversity_3Nov/decomptes_totaux.csv`) is dated before the
  October entity-rebuild (animal-forms-lexicon fix: feminine/young-animal
  word forms like chienne/ourse/louveteau, ~99 new forms). Confirmed stale
  by a direct row-for-row comparison on the same 892 DigEco novels: the
  rebuilt file has +3,746 more animal occurrences than his copy, in the
  expected direction.
- PRIX_ECOLOGIE never had a `décomptes_totaux` file at all. It does now.
- Bestsellers' old file only covered 88 of its 124 novels (36 overlap with
  DigEco and were missing from the Bestsellers-specific extraction — a
  known, previously-documented gap). Now covers all 124.

Files (same column structure as his original — `Key`, full metadata,
`nb_tokens`/`nb_formes`/`nb_lemmes`/lexical-richness indices, then per
category: `lemmes_X` = total occurrences, `diversite_X` = distinct lemma
count, for X in animal/plante/champignon/loterre/taxon, plus `TOTAL_LEMME`,
`TOTAL_DIVERSITE`, and `proportion_X_‰`):

- `decomptes_totaux_DigEco.csv` (892 novels)
- `decomptes_totaux_Bestsellers.csv` (124 novels)
- `decomptes_totaux_PRIX_ECOLOGIE.csv` (47 novels)

Built with `scripts/build_decomptes_totaux.py` (copy included here). `Key`
identifiers are carried over unchanged from his original files where they
already existed (confirmed byte-identical on a spot check); lexical-richness
columns (`nb_tokens` etc.) are reused as-is from the corpus metadata rather
than recomputed, since I'd already verified they were identical to his
version (0 mismatches across all 892 DigEco novels) — only the ecological
lemma counts were ever stale, never the general lexical stats.

One known, minor gap I'm flagging rather than hiding: 1 DigEco novel
(`Tesson-Sylvain_La-panthere-des-neiges.txt`) has no text file in the corpus
at all — a pre-existing gap, not something this update caused — so it has
no counts in either file.

## 4. The "fairly urgent" matter — frame-based Shannon measure

Built exactly to the method described in his email (general logic of Langer
et al. 2021, scaled to his own spec rather than the paper's):

1. Divide each novel's text into sequential, non-overlapping 1,000-token
   frames (tokenized as `\w+` word-tokens).
2. Randomly sample 10 distinct frames (without replacement) → a 10,000-token
   sample.
3. Within that sample, pool **all** ecological occurrences (animal + plante
   + champignon + loterre + taxon together — global, not split by category;
   see note below).
4. Shannon H = −Σ pᵢ ln(pᵢ) over the relative frequencies of the lemmes in
   the sample.
5. Repeat 100 times, average H (and also richness = distinct lemma count,
   and abundance = total occurrence count, on the same samples, as he asked
   "ideally").
6. Novels with fewer than 10 total frames (i.e. under ~10,000 tokens) are
   excluded — can't sample 10 distinct frames otherwise.

**Scope note**: this first version is global/pooled only, not split by the
5 taxonomic categories — that was a deliberate scoping decision on my part
(I re-read his email twice to confirm: every description in it — the
formula, the comparison to the single existing `Shannon_rarefied_50`
column, the final ask list — treats this as one combined measure, never a
per-category one). A category-split version is a natural next step if
wanted — I'm flagging it here rather than silently adding scope he didn't
ask for.

**Locating occurrences in the token stream**: the existing entity-extraction
files only store the matched word plus its context sentence, not a text
position. I relocated each occurrence by finding its context sentence as a
substring of the novel's raw text (a per-novel monotonic search cursor
resolves duplicate sentences in file order), which also naturally handles
sentences that were truncated by the existing pipeline for length (the
truncated version is always an exact substring of the original). This
preserves 100% of the existing homograph-disambiguation and lexicon work —
nothing was re-extracted from scratch.

Files (per novel: `EcoRichness_frame10k`, `EcoAbundance_frame10k`,
`Shannon_frame10k`, alongside `File`/`Year`/`Author`/`Title`/`nb_tokens` for
context):

- `shannon_frame10k_DigEco.csv` (892 novels)
- `shannon_frame10k_Bestsellers.csv` (124 novels)
- `shannon_frame10k_PRIX_ECOLOGIE.csv` (47 novels)

The same 3 columns are also written directly into the main
`corpus_DigEco.csv` / `corpus_Bestsellers.csv` / `corpus_PRIX_ECOLOGIE.csv`
metadata files in the repo root, alongside every other existing biodiversity
index — these extract files are a convenience copy, not a separate source
of truth.

Built with `scripts/shannon_frame_based.py` (copy included here).

**Validation I did before trusting any number**: hand-computed the expected
abundance for a known novel from its existing total count and confirmed the
sampled estimate matched almost exactly (e.g. a novel with 611 total
ecological mentions across ~47,500 tokens predicted ~129 in a 10,000-token
sample; the script returned 128.9). Checked internal consistency (richness
never exceeds abundance, Shannon always within valid bounds for the
observed richness) across all three corpora. 0.9–3.7% of occurrences per
corpus couldn't be relocated in the text (minor whitespace/encoding drift
between the extraction pipeline's stored context and the raw file) and are
simply excluded rather than mis-assigned — this slightly undercounts
affected novels rather than biasing them.

## What this update does *not* include

- A category-split (5-way) version of the frame-based Shannon measure —
  scoped out deliberately, see above; straightforward to add on request
  using the same script with one change.
- Task 1's Loterre référentiel/figuré classification is still incomplete
  (~70% done, separately tracked, unrelated to any number in this folder —
  I confirmed directly that the biodiversity-counting pipeline has never
  filtered by that classification for any category, animals included, even
  though Task 1 Animaux is 100% done).
