# Écopoétique — Master Documentation

Digital humanities research project (Sorbonne Université / UPPA), supervised by **Riccardo Barontini**, worked on by **Labiba Farooq** (intern; last effective working day 2026-07-13, departure 2026-07-15). Studies how animals, plants, and biodiversity are represented across a **925-novel French corpus** (`CORPUS_TOTAL/`), plus an 85-88 novel `CORPUS_Bestsellers/` subset.

This document merges, in full, every piece of project documentation that existed as of 2026-07-11: the pre-existing `PROJECT_DOCUMENTATION.md` (5,007 lines: README, task reports, raw batch-testing logs, both full Riccardo meeting transcripts, pipeline logs, nested-CV results, research-paper synthesis), `CLAUDE.md`, all 20 files in the Claude Code project memory directory (`~/.claude/projects/-home-lfarooq/memory/`), and `old_report_to_add.md` (a separate, earlier-stage 3,465-line technical documentation draft — merged 2026-07-11, contributing the project's research hypothesis/theoretical framing, additional research papers (Hicke et al./"Says Who?" full findings, Caracciolo 2021 as the academic source of Task 4.5's category typology, Riccardo's own published paper), many additional Task 0/1/2 techniques and failure modes not recorded elsewhere, and biodiversity-index detail). Nothing has been intentionally dropped except purely repetitive raw per-row console output (thousands of individual "✓/✗" prediction lines behind the Task 1 batch-size tables) — those raw logs still exist verbatim in `PROJECT_DOCUMENTATION.md` §4 and are only referenced here by their already-aggregated summary tables, which are reproduced in full below. Likewise, the two full verbatim Riccardo meeting transcripts (in `PROJECT_DOCUMENTATION.md` §7–8) are represented here via the already-comprehensive decisions/numbers extracted from them (memory file `project_meeting_notes.md`, itself built from a full read of both transcripts) rather than re-transcribed line-by-line. **Where `old_report_to_add.md`'s specific numbers (an earlier project stage) conflict with numbers elsewhere in this document that were established later and audited more rigorously (see §15, Verification Log), the more recent audited numbers remain authoritative** — `old_report_to_add.md` is merged in for its additional techniques, papers, and historical detail, not to override already-corrected figures.

Where sources conflict or a later finding overturns an earlier one, **both are stated explicitly** with the supersession noted — nothing is silently resolved in favor of one version.

---

## Table of Contents

1. [Project Overview & Structure](#overview)
2. [§0 — Foundations (pre-existing work, accepted as-is)](#task0-foundations)
3. [Task 0 — Narratology / Focalization](#task-0)
4. [Task 1 — Literal vs. Figurative Classification](#task-1)
5. [Task 2 — Metaphor Subcategory Classification](#task-2)
6. [Task 3 — Agentivity Analysis](#task-3)
7. [Task 4.5 — Compare-Target Classification](#task-45)
8. [Task 5 — Deployable Front-End (deprioritized)](#task-5)
9. [Biodiversity Indices (new, self-directed by Riccardo)](#biodiversity-indices)
10. [DH Humanistica App (separate side project)](#dh-humanistica)
11. [Cross-Cutting Lessons & Workflow Feedback](#lessons)
12. [Meeting Notes & Decisions — Full Chronology](#meetings)
13. [GPU Freeze Period (2026-07-10 → ~07-22)](#gpu-freeze)
14. [Current State Snapshot / Open Items](#current-state)
15. [Verification Log (2026-07-11 re-audit)](#verification-log)

---

<a id="overview"></a>
## 1. Project Overview & Structure

### Research context and hypothesis
**Fundamental research question**: "Is there a real 'ecological turn' in contemporary French-language literature, or is it just a feeling based on a few famous, well-known books?" To answer this empirically, Riccardo Barontini developed the **Digital Écopoétique** project, funded by a European Marie Skłodowska-Curie Actions postdoctoral fellowship (2023), integrated into the ANR "Anthropocène littéraire" programme at UPPA (Université de Pau et des Pays de l'Adour), under the chair "Enjeux écopoétiques contemporains."

**Core hypothesis**: **textual biodiversity** (variability of living organisms, ecosystems, and ecological concepts represented in novels) can serve as a **formal indicator** of ecological sensitivity in contemporary French fiction. This draws on:
- **Rosi Braidotti** (*Posthuman Knowledge*, 2019) — relational subjectivity, co-belonging between living beings and environments
- **Baptiste Morizot** (*Manières d'être vivants*, 2020) — the ecological crisis as a crisis of sensitivity: inability to perceive, distinguish, and name the living beings around us
- **Ursula K. Heise** (*Imagining Extinction*, 2016) — biodiversity as a cultural operator; endangered species acquire social effectiveness through collective narratives
- **Vincent Devictor** (*Nature en crise*, 2015) — biodiversity as a contested metric, tied to political crisis discourse
- **Edward O. Wilson** — popularised the "biodiversity" concept in the late 1980s

**Key finding already established before this internship's work began**: the biodiversity index is **globally stable over 2001–2024** — no clear "ecological turn" across the broad corpus. Only a **small cluster of specific novels** scores very high; ecological writing does not spread diffusely, it crystallises in specific works. **Confirmed**: novels nominated for *Prix du Roman d'Écologie* score more than **2× the average** biodiversity index — 45 of 47 such novels exceed the general corpus average, a strong correlation between external qualitative categorisation (jury label) and internal formal measure.

**Three levels of analysis** originally framing the project: (1) Lexical/Semantic (Task 1 — literal vs. figurative), (2) Stylistic (Task 2 — figurative subcategory), (3) Narratological (Task 0 — 7-criterion profiling). Tasks 3 (agentivity) and 4.5 (compare-target) were added later.

**Note on literary prize bias** (acknowledged, not hidden): using prize shortlists for the corpus is a deliberate bias — only works institutions recognize as having value are included. This is what allows the project to ask whether ecological imagination aligns with literary consecration, not a flaw to be corrected.

**Corpus structure** (as originally specified — see also the Task 1/3 sections for the audited, as-run row counts, which differ slightly from these original targets due to dedup/coverage-gap fixes):

| Corpus | Size | Description |
|---|---|---|
| Corpus principal | 892 novels | Prize shortlists: Goncourt, Goncourt des Lycéens, Femina, Renaudot, Médicis, Livre Inter, Cinq Continents (2001–2024) |
| Corpus bestsellers | 124 novels | Top 5 best-selling novels per year |
| Corpus écologique | 47 novels | Nominees for Prix du Roman d'Écologie 2017–2024 |
| TOTAL (with overlaps) | ~1,070 novels | Combined unique novels |
| CORPUS_TOTAL (server, deduplicated) | ~925 .txt files | The actual working corpus |

**Zipf's law in the corpus**: the biodiversity vocabulary follows Zipf's law — 480 lemmas cover 90% of all ~290,000 occurrences, while the remaining 10% require 3,500+ rarely-used lemmas. This reveals a structural tension between symbolic concentration (a few dominant species) and ecological dispersion (many rare ones).

### Corpora
- `CORPUS_TOTAL/` — ~925 French novels, .txt, one sentence per line, post-OCR cleaned
- `CORPUS_Bestsellers/` — ~85-88 bestseller novels (separate subset, partial overlap with main corpus)
- `TOKENS/`, `TOKENS_Bestsellers/` — spaCy tokenisation (token | POS | lemme)
- Metadata: `corpus_DigEco.csv` (tab-separated), `corpus_Bestsellers.csv`, `corpus_PRIX_ECOLOGIE.csv`

### Lexicons (`lexiques/`)
- `ANIMAUX.txt`, `PLANTES.txt`, `CHAMPIGNONS.txt` — built from a Wikispecies dump + TaxRef (French biodiversity reference)
- `categories_animales/` — AMPHIBIENS, INSECTES, MAMMIFERES, MOLLUSQUES, OISEAUX, POISSONS, REPTILES
- `loterre/` — Loterre thesaurus (climate change / Anthropocene terms): `loterre_filtré.csv`, `classement_termes.json`

### Pipeline scripts (`scripts/`)
bash: `pipeline_animaux.sh`, `pipeline_plantes.sh`, `pipeline_loterre.sh`
python: `grep_contexte.py`, `remove_duplicates.py`, `truncate_sentence.py`, `filter_*.py`, `assign_category.py`, `lemmatize.py` (LEFFF lemmatiser), `pos_tag_homographe.py`, `biodiv_score.py`, `shannon_rarefied.py`

### Results (`resultats/`)
- `corpus_principal/` — `ENTITES_contexte_animaux/plantes/champignons/loterre/taxons.csv` + decomptes
- `bestsellers/` — same for bestsellers subset

### Homographie (`homographie/`)
Disambiguation of lexical homographs (e.g. "if" = English word vs. yew tree): `isAnimal/` (binary classifier training data + `train_homograph_binary.py`), `isPlant/` (GPT-4 annotations), `loterre/` (Loterre ambiguous terms table)

### Environment gotchas
- **No dedicated project venv/conda env exists.** Scripts needing spaCy/polars/transformers only run under `/home/lfarooq/digitize_medical_records/labelimg_env/bin/python3` — the only environment on the box with `spacy` + `fr_core_news_lg` + `polars` + `transformers` all installed. Plain `python3`/`pip3` at system level has none of these.
- **This environment loses installed Python packages between sessions.** spaCy/`fr_core_news_lg` had to be reinstalled from scratch more than once despite prior successful use — budget ~5-10 min setup time each fresh session (`pip install --user --break-system-packages`).
- **GPU**: single shared NVIDIA A40, 46GB VRAM, no sudo/MPS access (no true hard resource-splitting possible). All qwen3/Ollama jobs (Tasks 0/1/2/4.5) queue on the same Ollama instance at `localhost:11434`/`11435`.
- **Sudo-interactivity limit**: the agent's Bash tool cannot supply a sudo password or reuse the user's authenticated sudo session. Any command needing sudo on `obtic-gpu1` must be run by Labiba herself in her own terminal, output pasted back.

---

<a id="task0-foundations"></a>
## 2. §0 — Foundations (pre-existing work, accepted as-is)

Built by a previous team (Joanna et al.), predates this work cycle: corpus, lexicons, homograph disambiguation, extraction pipeline. **Status: Done, accepted as-is.** Riccardo explicitly said this is not worth redoing even with its known ~10-15% impurity — "Do NOT redo Joanna's homograph disambiguation... Too costly (would mean redoing entire extraction pipeline). Some non-animals/plants will remain in the data — 'so be it.'"

The extraction/filtering/lemmatization/homograph pipeline (`pipeline_animaux.sh`, `pipeline_plantes.sh`) is what produces the `ENTITES_contexte_*.csv` files that Task 1 runs on.

### The three source lexicons
1. **TaxRef** (MNHN — Muséum National d'Histoire Naturelle, https://inpn.mnhn.fr/telechargement/referentielEspece/referentielTaxo) — scientific species taxonomy for French territory including overseas, provides vernacular names linked to unique species identifiers.
2. **Wikispecies** (Wikimedia, https://species.wikimedia.org) — global species database extending coverage beyond French territory. Merged with TaxRef after lemmatisation, orthographic normalisation, duplicate removal, and unique ID assignment per species.
3. **Loterre** (CNRS/ISTEX, https://loterre.istex.fr/BLH/fr/) — not individual species but conceptual ecological vocabulary: ecosystems, ecological dynamics, natural processes, perturbations, climate-change/environmental-transformation vocabulary. Organised hierarchically, ~716-900 distinct concepts found in the corpus (estimates vary across notes).

### Original extraction results (Johanna's pipeline, ~290,000 total occurrences from 1,070 novels)
| Category | Occurrences | % | Distinct taxa/entries |
|---|---|---|---|
| Animaux | 114,851 | 39.6% | 1,488-1,523 taxa |
| Loterre | 111,196 | 38.3% | ~716-900 concepts |
| Plantes | 63,599 | 21.9% | 1,567-1,609 taxa |
| Champignons + Taxons | ~3,000 | ~1% | marginal |

**Key asymmetry**: animals dominate in volume (frequency) but plants have higher specific diversity (more distinct species). Mammals = 60% of animal occurrences but fewer taxa than birds. **Ornithological sensitivity**: birds have higher specific richness relative to occurrence count, signaling a notable ornithological sensitivity in contemporary French literature (noted by Marielle Macé in *Une pluie d'oiseaux*, Corti, 2022).

### Disambiguation challenge and Johanna's original solution
Many biodiversity terms are polysemous — *maquereau* = mackerel (fish) OR pimp (slang); *le bar du coin* = bar (place), not bar (fish); *chien de fusil* = gun trigger/hammer, not dog. Johanna's two-step approach: (1) linguistic rule-based filtering (expression blacklists, POS rules), (2) contextual classification using **FlauBERT** (French BERT fine-tuned on a manually-annotated sample) or GPT-4. Johanna's estimated accuracy: ~85% (Riccardo's estimate) — "good enough, too complicated to go back." This project (Labiba's work) did **not** use FlauBERT anywhere — all Task 1 classification instead uses qwen3:30b via prompt engineering, a different approach at a different pipeline stage (literal/figurative classification, not entity extraction).

### Shannon Biodiversity Index (already computed by Johanna, pre-existing)
Applied per novel, from information theory rather than pure ecology. Formula: H = -Σ(pᵢ × ln(pᵢ)) where pᵢ = proportion of species i in the novel. Combines **richness** (number of distinct species) and **equitability** (how evenly distributed they are) — high Shannon = many species evenly represented; low Shannon = few dominant species, many rare. File: `resultats/corpus_principal/data_pour_Shannon.csv` (925 rows). **Key result, already validating the whole project's premise**: Prix du Roman d'Écologie novels average >2× the corpus mean Shannon index, 45/47 exceed the general corpus average.

---

<a id="task-0"></a>
## 3. Task 0 — Narratology / Focalization

### What it is
Classifies each novel along **7 narrative dimensions** via qwen3:30b using a map-reduce architecture (map: per-chunk signal extraction across ~9 sections/novel; reduce: cross-chunk synthesis with a 3-vote scheme), scored against a gold set of annotated novels. The 7 criteria: TYPE NARRATEUR, FOCALISATION, MODE NARRATIF, RÉGIME NARRATIF, ESPACE, INTRIGUE, TEMPORALITÉ. This is the project's "biggest headache" — described by Riccardo as being at the edge of what current LLM tooling can do for this kind of task (published literature reports ~70-75% as competitive, ~80% with paid frontier models).

### Gold sets — two non-comparable versions (critical to understand before reading any number below)
1. **Old gold set**: `GOLD_narratologie_60novels_original.csv` (60 novels), verified against GitLab `origin/main` as the canonical original. Uses old FOCALISATION scheme: `FOC_INT` (internal/whose-consciousness) / `FOC_EXT` / `FOC_ZERO` / `FOC_VAR`.
2. **New gold set** (received 2026-07-08): `narratologie/GOLD_narratologie_0807.csv` — 80 rows / 79 unique novels, all 60 of the original confirmed-gold novels + 19 new ones, zero blank FOCALISATION values. Uses a **completely different FOCALISATION framework**: reader-vs-character-knowledge (`FOC_RFOC`/`FOC_ELARG`/`FOC_REST`/`FOC_MIXTE`) — not just renamed codes, a different theoretical scheme entirely.
3. **Code-vocabulary diff confirmed directly** (2026-07-10 archaeology): only FOCALISATION changed completely between the two gold files. TYPE NARRATEUR gained 2 new codes (`NAR_AUTO`, `NAR_VAR`) used on only 3/79 novels (97% comparable). MODE NARRATIF's new `MOD_DIA` category exists in the schema doc but is used on **zero** of the 79 currently-annotated gold novels (not actually active yet). RÉGIME/ESPACE/INTRIGUE/TEMPORALITÉ have identical code vocabularies, though individual novel labels can still be corrected between file versions (one confirmed example: `Bienne-Gisele_La-malchimie.txt` ESPACE went `ESP_UNIT`→`ESP_FRAG`).
4. **Practical consequence**: any FOCALISATION number scored under the old scheme (v1-v9, hybrid, chunk_classifier — literally everything before v10) is **not comparable** to the new gold set and cannot be cited going forward. All local files that even attempt the new scheme are v10/v10b/v10c/v10d.

### Full chronological history of techniques tried

#### Pre-map-reduce approaches (May-June 2026, earliest attempts, from `old_report_to_add.md`)
1. **125-line sample (baseline, Labiba's first attempt)**: take 125 lines from the novel's beginning, classify all 7 criteria. Result: **55.7% overall**. Main problem: the beginning of a novel doesn't reveal INTRIGUE structure or TEMPORALITÉ.
2. **Smart RAG**: retrieve relevant excerpts per criterion using BM25/semantic search, then classify. Result: **45.0% overall — worse than the 125-line baseline**. Why it failed: criterion-relevant excerpts don't exist in predictable locations; retrieval fails for global properties like TEMPORALITÉ that require seeing the whole novel, not a retrieved fragment.
3. **Full novel single prompt (~4,500 words)**: feed the first 4,500 words directly to the model in one call. Result: **complete failure** — context window exceeded (100,000+ tokens needed per novel vs. an 8,192-token context window), model truncated, produced garbage.
4. **Voting across 8 parallel sections**: split the novel into 8 sections, classify each independently and in parallel, take majority vote. Result: **crashed** — 8 simultaneous API calls × 60 novels = 480 concurrent calls, memory overflow in subprocess management. Abandoned in favor of sequential map-reduce.

These four failures are what directly motivated the map-reduce architecture (sequential chunking + a synthesis reduce step) that became the project's actual production approach.

#### Map-reduce v1/v2 — intermediate versions before the v3 production baseline
- **v1**: basic map (classify each chunk) + reduce (just count majority labels across chunks, no reasoning synthesis). Result: **~50% overall**.
- **v2**: map with more questions per chunk + reduce with a summarization step. Problem: the model hallucinated narratological labels during the reduce step. Result: **~57% overall**.
- **v3 (became the actual production baseline, called "v7" after further tuning later)**: map produces structured JSON observations per chunk → reduce synthesizes across all chunk summaries with a dedicated prompt. This structural design (not any single wording) is what the later v7/v8/v9/v10 iterations all build on.

#### Multi-model ensemble attempts (June 2026, before the hybrid-table approach was adopted)
- **3-model ensemble (qwen2.5:32b + qwen2.5:72b + qwen2.5:14b, all on port 11434, majority vote per criterion)**: Result: **55.3% FOCALISATION — worse than qwen3:30b alone (63.3%)**. Why it failed: all 3 qwen2.5 models default to FOC_INT, so the majority vote is just FOC_INT — ensembling amplified the shared systematic bias rather than correcting it. **Lesson, reconfirmed later for self-consistency voting too**: cross-model/cross-sample voting only helps when models make *different* errors; it does nothing when they share the same systematic bias.
- **Gemma3:27b and Mistral-Small3.1 24B — actually pulled and tested, not just suggested**: both models were pulled via Ollama (17GB and 15GB respectively, pushing disk to 97% full), and a dedicated script `run_weak_criteria.py` was built targeting only the 4 weakest criteria (FOCALISATION, MODE NARRATIF, ESPACE, INTRIGUE) — embedded Genette definitions verbatim, no-think mode, JSON-constrained output, 6-chunk map→reduce. **Outcome: results were not clearly better than qwen3:30b alone** (exact numbers were not preserved in the session transcripts — the test was apparently interrupted or its output wasn't logged), and both models were subsequently **deleted** to free disk space. This is why cross-model ensembling with these two specific models was abandoned, not merely "not yet tried."
- **Self-consistency voting (n=5 samples, temperature=0.3, majority vote)** — already documented elsewhere in this doc as giving 61.7% (no improvement) — fits the same pattern: when a model's bias toward FOC_INT is systematic rather than random noise, voting amplifies it instead of correcting it. This directly **contradicts** a claim in the Hicke et al. paper (below) that self-consistency "robustly improves classification without training" — the paper's claim held for random variance, not for a model's systematic class-default bias.

#### Johanna's original narratological pipeline (predecessor system, for comparison)
Used Google Colab + GPT-4o-mini via the OpenAI API. Architecture: title + author + year only — the model queried its own internet/training knowledge, **never read the actual novel text**. Batches of 5 novels per call, XML-structured prompts (`<requete>`, `<reponse>`, `<categorie>`, `<explication>` tags), temperature 0, max_tokens 4000, parsed via regex on the XML tags. Covered only 2 of 7 criteria (Narrateur + Focalisation) in its final version; **failed on 271/802 novels (33.8%)**, marked unclassifiable ("X") when the model couldn't find enough information about an obscure novel online. This is the system this project's map-reduce approach was built to replace — it could not scale to the 5 remaining criteria and had no access to the text itself.

Johanna's exact per-criterion label definitions (French, as embedded in her prompts) — useful reference for how the criteria were originally specified before this project's own refinements:
- **Intrigue**: Linéaire (événements s'enchaînent dans un ordre progressif sans rupture majeure) / Fragmentaire (intrigue construite par blocs disjoints, souvent non liés immédiatement) / Cyclique (répétition de motifs ou situations créant un effet de boucle ou retour)
- **Chronologie**: Chronologique (événements majoritairement racontés dans l'ordre où ils se produisent) / Anachronique (présence significative de retours en arrière ou d'anticipations) / Discordante (structure très éclatée ou désorganisée, fréquents déplacements temporels non hiérarchisés)
- **Narrateur + Focalisation**: NAR_AUTOD (narrateur = protagoniste principal) / NAR_TEM (narrateur témoin) / NAR_EXT (narrateur externe/hétérodiégétique); FOC_INT (accès à l'intériorité d'un personnage unique) / FOC_EXT (narration descriptive en surface, sans accès aux pensées internes) / FOC_ZERO (narrateur omniscient) / FOC_VAR (alternance entre plusieurs points de vue internes)
- **Mode narratif**: MOD_EVT (centré sur les faits/actions/décisions) / MOD_DESC (décors/objets/atmosphères) / MOD_INTR (réflexions/états mentaux) / MOD_DIA (dialogue/polyphonie) / MOD_MIX (alternance régulière sans prédominance)
- **Régime narratif**: REG_AUTO (fondé sur l'expérience de l'auteur ou un double fictionnel) / REG_REAL (représentation cohérente du monde réel) / REG_FANT (intrusion du surnaturel dans un cadre réaliste) / REG_SPEC (monde fictionnel modifié, futuriste ou alternatif)
- **Espace**: ESP_UNIT (un seul lieu délimité) / ESP_FRAG (plusieurs lieux discontinus, sans logique de déplacement) / ESP_ITIN (déplacements continus, voyages) / ESP_IMAG (espace fictif/fantastique/onirique)
- **Degré de discordance temporelle** (an extra criterion in Riccardo's full grid, never implemented in this project's pipeline): Faible / Moyenne / Forte discordance

Technical details of Johanna's Colab pipeline: model `gpt-4o-mini` (originally `gpt-5.4-mini` per an early note), Polars (not pandas), `partition_by(by="fichier")` for batching, XML regex parsing (`re.search(r'<categorie>(.*?)</categorie>', reponse)`), evaluated with sklearn `f1_score(average="micro")`.

#### Early qwen2.5 model family tested on port 11434 (before settling on qwen3:30b on port 11435)
| Model | VRAM | FOCALISATION | Notes |
|---|---|---|---|
| qwen2.5:7b | 4GB | ~30% | Too small |
| qwen2.5:14b | 8GB | ~45% | Better but still poor |
| qwen2.5:32b | 19GB | ~51% | Part of the failed 3-model ensemble above |
| qwen2.5:72b | 47GB | ~55% | Became the base for `qwen72b-limited` |
| Llama-3.2-1B | ~0GB (tiny) | ~1% | Complete failure |

**Important**: these are all on the *other team's* shared Ollama instance (port 11434), not this project's private one (port 11435) — using them risked interfering with other researchers' work, which is part of why the project standardized on its own port-11435 instance for all production runs.

#### Early models tried (per meeting transcripts, before/around June 25)
| Method | Result | Notes |
|---|---|---|
| qwen72b-limited, FOCALISATION, WITH thinking | 61.7% (37/60) | `pipeline_overnight.log`, June 24. Model predicted `FOC_INT` on nearly every single novel (constant-prediction collapse) — matched gold only when gold happened to also be FOC_INT. |
| qwen72b-limited, FOCALISATION, WITHOUT thinking | 61.7% (37/60) | Identical result to with-thinking — thinking made zero difference for this model/criterion, same FOC_INT-collapse pattern. |
| "sample 72B with the intelligence" (per transcript) | 68.3% | Described as "the best one I could do right now" at time of first meeting. |
| Local hybrid (pre-existing baseline) | 65.0% | Called "previous best" in `pipeline_overnight.log`. |
| LoRA fine-tune of Qwen2.5-7B-Instruct | **Failed** | Training dataset too small (200+ examples needed, impractical to hand-annotate); also the corpus file given had a duplicate novel plus 3 novels missing from CORPUS_TOTAL entirely (later found: those 3 are Bestsellers-only). |
| Mistral API (free tier) | Poor | "it gives you free tokens... but these models also doesn't work" |
| Groq (free tier) | Poor | Tried alongside Mistral, similarly unhelpful |
| GPT-4o-mini v7 (paid) | 64.8% overall (60/60 novels), $0.89 total | See below — modest real win over local qwen3 (62.1%), confirms a genuine quality gap vs. full GPT-4o |
| GPT-4o v7 (paid) | **76.1%** overall (34/60 novels, quota-limited), ~$8.55 spent | See below — best result achieved anywhere in the project |

#### v1-v9 local qwen3:30b mapreduce iterations
- **v3 mapreduce**: strong general-purpose baseline, later found (2026-07-09/10 sweeps) to still be the best or near-best local file for several criteria depending on which gold set is used.
- **v5**: single-shot (pre-mapreduce) — later found to score 77.2% (44/57) on FOCALISATION under the *old* scheme, beating v7's 71.7%, but v5's prediction file is missing 3 of the 60 gold novels and is scored under a scheme that's since been replaced — **not usable/comparable going forward**.
- **v7** (`run_task0_mapreduce_v7.py`): the best-tuned local qwen3 pipeline as of the first documentation pass; became the base for the GPT-4o port. `run_task0_mapreduce_v7_gpt4o_mini.py` reuses its `load_gold` etc.
- **v8**: rewrote 5 criteria's definitions simultaneously (FOCALISATION — Genette's zero-vs-variable test; RÉGIME NARRATIF — Lejeune's autobiographical-pact test for AUTO; MODE NARRATIF — explicit per-chunk tallying instead of defaulting to "mixed"; INTRIGUE/TEMPORALITÉ — shared caveat about chunk-sampling gaps), all grounded in real narratological theory. Tested on a 5-novel sample: **57.1% vs v7's 74.3% on the identical 5 novels — a regression.** Rejected. Consistent with the project's standing "isolate one variable" lesson — changing 5 things at once made the failure impossible to attribute to any one cause.
- **v9**: reverted to v7's wording exactly, changed exactly one thing — enabled `think=True` on the REDUCE step (previously `think=False`), with a larger token budget. Result on 15 novels: **flat overall (61.9% both)**, but a real isolated trade: **ESPACE +20pp (53.3%→73.3%)**, INTRIGUE −20pp (73.3%→53.3%), everything else tied. Takeaway: use v9's ESPACE predictions specifically in a hybrid, not as a general replacement. (Later, 2026-07-10: this 73.3% figure was found to be against the *old* 60-novel gold specifically; against the *current* gold it's 66.7%, because exactly one novel's ESPACE label was corrected between gold-file versions — still the best available ESPACE number, just small-N/unconfirmed-at-scale.)
- **Honest hybrid recompute**: the previously-reported 69.3% "hybrid" figure (picking best-per-criterion local method) was found to suffer the same model-selection-leakage problem as the classifier bug below. Clean, non-cherry-picked reconstruction: **~71.2% (299/420)** — the best defensible qwen3-only number, still below GPT-4o's 76.1%. This number superseded an earlier-reported 69.3%.

#### Classifier-based approach and the leaky-CV bug
- `train_chunk_classifier_60novels.py` (and the older `train_chunk_classifier.py`, confirmed via code read to have the **identical bug**) tries 3 sklearn classifiers (LogReg/RF/GB) per criterion and reports whichever scores highest on `cross_val_predict` over the *same* loop being reported — classic model-selection leakage, not just leaky training.
- **Fix**: `nested_cv_classifier.py` — inner 5-fold CV blind to the held-out novel picks the model type; outer loop only scores. Produced `resultats_nested_cv_honest.txt`:

| Criterion | Leaky | Honest (nested CV) | Inflation |
|---|---|---|---|
| TYPE NARRATEUR | 93.3% | 90.0% | +3.3pp |
| FOCALISATION | 66.7% | 65.0% | +1.7pp |
| MODE NARRATIF | 70.0% | 63.3% | +6.7pp |
| RÉGIME NARRATIF | 75.0% | 68.3% | +6.7pp |
| ESPACE | 51.7% | **38.3%** | **+13.4pp (worst)** |
| INTRIGUE | 68.3% | 65.0% | +3.3pp |
| TEMPORALITÉ | 60.0% | 58.3% | +1.7pp |
| **OVERALL** | **69.3%** | **64.0%** | **+5.3pp** |

- Later (2026-07-10) `train_chunk_classifier_60novels.py` was **re-confirmed to actually use genuine LeaveOneOut CV** (`sklearn.model_selection.LeaveOneOut` + `cross_val_predict`, read directly) — the saved `resultats_chunk_classifier_60novels.csv` is the honest out-of-fold prediction, resolving a doubt from an even-older pasted table claiming it needed a "nested-CV discount to 63.3%." That doubt was itself wrong.
- This file (`chunk_classifier_60novels.csv`) was later found (2026-07-09 full sweep) to actually be the **best local file for 4 of 7 criteria** against the current gold set — see the hybrid tables below. This corrected an earlier, stale-memory answer that had defaulted to "v3 mapreduce is best" without re-checking against current files.

#### Paid GPT-4/GPT-4o experiments (2026-07-07, this session's own direct work — not previously documented anywhere)
Riccardo explicitly approved a paid-GPT budget (€22-25 estimated for a full corpus run, offered up to €100-200 more if needed), with the instruction to email him before topping up rather than silently re-hitting the old $8-9 limit.

**GPT-4o v7 port**: identical prompts/chunking/reduce-vote scheme as local v7, only the model backend changed — a clean, controlled, apples-to-apples comparison.

| Criterion | GPT-4o v7 | qwen3:30b v7 (same 34 novels) | Δ |
|---|---|---|---|
| TYPE NARRATEUR | 91.2% | 88.2% | +3.0pp |
| FOCALISATION | 76.5% | 76.5% | tie |
| MODE NARRATIF | 70.6% | 44.1% | +26.5pp |
| RÉGIME NARRATIF | 82.4% | 61.8% | +20.6pp |
| ESPACE | 73.5% | 55.9% | +17.6pp |
| INTRIGUE | 64.7% | 58.8% | +5.9pp |
| TEMPORALITÉ | 73.5% | 50.0% | +23.5pp |
| **OVERALL** | **76.1%** | **62.2%** | **+13.9pp** |

GPT-4o wins or ties on every criterion. RÉGIME NARRATIF hit 82.4% — past Riccardo's named 80% target. **This directly answered "can paid GPT get us to 80%?"** raised in both meetings. Cost: ≈$8.55 actually spent for 34 novels (via token reconstruction, direct billing API wasn't available); projected ~$6.40 more to finish the remaining 26 (~$15 total for the full 60); ~$227 projected for the full 925-novel corpus. This roughly confirmed Labiba's own €22 second-meeting estimate. **Blocker**: hit `insufficient_quota` (hard account billing limit) partway through novel 32/60 — very likely the "$8-9 limit" issue discussed in the second meeting. **Never resumed to complete the remaining 26 novels** as of the last update to this section — also needs a one-line `load_done()` fix first, or it will wrongly skip the 2 quota-failed novels instead of retrying them.

**gpt-4o-mini v7 port**: all 60/60 novels, ≈$0.89 total.

| Criterion | gpt-4o-mini v7 | qwen3:30b v7 (same 60 novels) | Δ |
|---|---|---|---|
| TYPE NARRATEUR | 78.3% | 91.7% | −13.4pp |
| FOCALISATION | 71.7% | 71.7% | tie |
| MODE NARRATIF | 50.0% | 43.3% | +6.7pp |
| RÉGIME NARRATIF | 61.7% | 68.3% | −6.6pp |
| ESPACE | 58.3% | 53.3% | +5.0pp |
| INTRIGUE | 61.7% | 53.3% | +8.4pp |
| TEMPORALITÉ | 71.7% | 53.3% | +18.4pp |
| **OVERALL** | **64.8%** | **62.1%** | **+2.7pp** |

A modest real win over local qwen3, but well below full GPT-4o — confirms a genuine quality gap between mini and full models on this task, not just a price difference.

#### 2026-07-08: FOC/RÉGIME/TEMPORALITÉ definitions audit against Riccardo's canonical schema
Compared `run_task0_mapreduce_v7.py`'s embedded `CRITERIA_DEFS` against `narratologie/tableau_narratif_22_08.csv` (the canonical file sent alongside the new gold set):
- TYPE NARRATEUR, ESPACE, INTRIGUE: unchanged.
- MODE NARRATIF: same 4 codes + genuinely new 5th `MOD_DIA` (dialogue/polyphonie), not yet observed in any of the 79 gold novels.
- FOCALISATION: completely different scheme (already described above).
- RÉGIME NARRATIF: new canonical REG_AUTO def ("fondé sur l'expérience de l'auteur ou un double fictionnel") is meaningfully **narrower** than v7's trigger ("ton confessionnel/réflexif soutenu... posture subjective et réflexive constante") — directly explains a REG_REAL↔REG_AUTO confusion (5 combined misclassifications, biggest single confusion pair) found in error analysis — v7's prompt was over-triggering AUTO.
- TEMPORALITÉ: new canonical TEMP_DIS def is "analepses ou prolepses **ponctuelles** mais significatives" (concrete occasional flashback/flash-forward) and **never mentions narrative stance/retrospection**. Confirms a confusion-matrix finding that 15/19 (79%) of TEMPORALITÉ errors are gold=TEMP_LIN→predicted=TEMP_DIS, traced to v7's prompt wrongly conflating "posture rétrospective" (very common in French first-person literary fiction) with actual story-order discontinuity.

Full new FOCALISATION definitions (reader-vs-character-knowledge framework):
- **FOC_RFOC** (récit focalisé): reader shares characters' information — privileged access to perceptions/thoughts/knowledge
- **FOC_REST** (restreinte): reader knows **less** than characters — partial/delayed info, mystery/curiosity
- **FOC_ELARG** (élargie): reader knows **more** than characters — dramatic irony, anticipating events characters don't know
- **FOC_MIXTE**: structured alternation between multiple focalization regimes across chapters/voices

#### `run_task0_foc_reg_tem_fix.py` (2026-07-08) — first fix attempt on the 3 drifted criteria
Copy of v7 with exactly FOC/RÉGIME/TEMPORALITÉ corrected to match canonical definitions; NAR/MODE/ESPACE/INTRIGUE untouched:
1. FOCALISATION: new reader-vs-character scheme, new MAP-step signal `reader_vs_character_knowledge`.
2. RÉGIME: REG_AUTO tightened to require a concrete link to the author's real life.
3. TEMPORALITÉ: TEMP_DIS's "posture rétrospective" trigger removed entirely, now requires a concrete flashback/jump or actual time-marker order contradiction.

5-novel validation launched, not completed before the session that started it ended.

#### v10 / v10b — full 20-novel run, overcorrection diagnosed and calibrated (2026-07-08)
`run_task0_v10_foc_reg_tem.py` stripped to only FOC/RÉGIME/TEMPORALITÉ (NAR/MODE/ESPACE/INTRIGUE dropped entirely per explicit instruction). **v10 result: 55.0% overall (33/60)** — FOC 55.0%, RÉGIME 60.0%, TEMPORALITÉ 50.0%. Below the 60% auto-scale threshold.

Diagnosis found a classic overcorrection pattern — each fix correctly killed the original bias but swung too far the other way:
- FOCALISATION: 7/9 errors are FOC_ELARG→FOC_RFOC (now under-detecting dramatic irony)
- RÉGIME: now REG_FANT(3x)/REG_AUTO(2x)/REG_SPEC(2x)→REG_REAL (opposite of original REAL→AUTO over-triggering)
- TEMPORALITÉ: 9/10 errors are TEMP_DIS→TEMP_LIN (exact mirror of the original bug — fix now under-triggers DIS)

**v10b calibration applied** (loosened back toward center, not reverted): FOC_ELARG no longer needs majority-of-sections support (one clear uncontradicted signal wins); RÉGIME's REG_AUTO needs only one concrete uncontradicted section, FANT's non-human-narrator signal reinstated as a supporting cue, SPEC accepts partial-world transformation; TEMPORALITÉ keeps concrete-flashback trigger but adds a secondary path (multiple retrospective sections with non-linear time-markers). Output: `resultats_task0_v10b_calibrated.csv`.

**v10b result (2026-07-09, 20-novel test): 60.0% overall (36/60)** — FOC 60%, RÉGIME 60%, TEMPORALITÉ 60%, exactly at the 60% auto-scale threshold, up from v10's 55% but not a clear win. Confirmed no qwen3-truncation bug (script explicitly sets `think: False` on all calls, deliberate design choice).

Confusion diagnosis of v10b:
- TEMPORALITÉ (60%): exactly symmetric confusion — 4× TEMP_DIS→TEMP_LIN, 4× TEMP_LIN→TEMP_DIS — looks like a coin-flip/weak-signal problem, not a directional bug.
- RÉGIME (60%): scattered errors, no dominant pair, but REG_FANT involved in 3/8 — weakest, most inconsistent category.

#### v10c — reduce-step thinking enabled for FOC/RÉGIME/TEMPORALITÉ (2026-07-09/10)
Rationale: the same technique (`think=True` on REDUCE) that fixed ESPACE via v9 should help TEMPORALITÉ's coin-flip pattern and RÉGIME's FANT inconsistency, both of which look like "weak tie-breaking at vote-aggregation time."
- 20-novel test: 61.7% overall.
- Scaled to 40 novels: FOC 47.5% / RÉGIME 67.5% / TEMPORALITÉ 75.0%, overall **63.3% (76/120)** — none of the three criteria stable yet, each 20-novel batch swings 5-15pp.
- Scaled to the full 79-novel gold set: **FOCALISATION 26/79 = 32.9%**, **REGIME 48/79 = 60.8%**, **TEMPORALITÉ 54/79 = 68.4%**. FOCALISATION on the new scheme is badly broken.

**v10c FOCALISATION bug diagnosed**: confusion matrix on the 73-novel checkpoint found **all 47 errors landed on FOC_ELARG** — a clean default-collapse, not scattered noise. Root cause (found by reading `run_task0_v10c_reduce_think.py`): the REDUCE prompt's "ANY ONE section showing more_than_characters wins" rule for FOC_ELARG — with 9 independently-judged chunks per novel, at least one nearly always gets misjudged as dramatic irony without seeing the rest of the novel, and that single false positive overrides everything. Same failure family as the earlier INTRIGUE per-chunk-categorical-collapse bug (see Cross-Cutting Lessons #10).

**v10d fix attempt** (one round, not resolved): replaced the noisy 3-way categorical MAP field (`reader_vs_character_knowledge`) with two concrete evidence-extraction fields (`dramatic_irony_evidence` / `info_withheld_evidence`, each "quote a specific instance or say 'none'"), changed REDUCE aggregation from "≥1 instance" to "≥2 independent instances." Output: `resultats_task0_v10d_focalisation_evidence.csv`.

Test on 4 novels: **1/4 (25%)** — not a clean win.
- Ernaux `Les-annees`: fixed, correct FOC_RFOC.
- Houellebecq `Soumission`: still wrong (ELARG) — 3 concrete irony instances found, clears the ≥2 bar, but gold isn't ELARG — evidence real but not "dominant" enough relative to novel length.
- Mauvignier `Continuer`: still wrong (ELARG) — 2 instances, exactly hits threshold, gold is FOC_MIXTE.
- Autissier `Soudain-seuls`: **new regression** — was correct before; one chunk had both irony AND withheld evidence, another only withheld, so withheld hit ≥2 first and REDUCE picked FOC_REST, gold is ELARG.

**Not resolved.** Needs a relative/dominance threshold instead of absolute count, or a tie-break rule for co-occurring evidence types. Left open, do not scale.

**REGIME and TEMPORALITÉ — separate, opposite-direction problem**: from the same v10c checkpoint, **REG_FANT is 0% recall** (0/10, always predicted REG_REAL or REG_SPEC) and **TEMP_DESORD is 0% recall** (0/5, always predicted TEMP_DIS or TEMP_LIN). Unlike FOCALISATION's over-triggering, this is under-triggering — the model is too conservative to ever commit to the rarest/most extreme category. Not diagnosed further (needs replay of actual MAP/REDUCE calls on specific misclassified novels, per the project's "investigate first" rule).

#### ESPACE default-collapse bias confirmed as pre-existing, not a resume bug (2026-07-10)
Labiba suspected a resume (killing an ESPACE-only detour script, going back to the full v9 run) broke ESPACE, which went from a 72.7% mid-run checkpoint down to 62.7% final. Investigation: split final 60-novel `resultats_task0_mapreduce_v9.csv` into pre-resume (first 33 rows) vs post-resume (last 26): pre-resume ESPACE 24/33=72.7%, post-resume 13/26=50.0%. Confirmed via code inspection: **zero code changes** occurred to `run_task0_mapreduce_v9.py` between kill and resume; the ESPACE-only detour wrote to a completely separate output file. **Root cause**: the model has a persistent pre-existing bias toward over-predicting **ESP_UNIT** (51.5% of the time in the pre-resume batch too, vs only 36% gold-UNIT there) — same default-collapse family as FOCALISATION's FOC_ELARG bug and REGIME/TEMPORALITÉ's FANT/DESORD 0%-recall bug. The pre-resume batch (novels A-P) just had fewer ESP_ITIN gold novels (6/33=18%) to expose the bias; post-resume (Q-Z, more genuine travel narratives) had proportionally more (8/26=31%), exposing it more. **Nothing to fix in the resume mechanism** — this is now a **fourth confirmed instance of the same systemic "over-predict the common/default category" bug pattern**, spanning FOCALISATION, REGIME, TEMPORALITÉ, and ESPACE, still undiagnosed/unfixed as of the GPU freeze.

**Note on the 62.7% vs. 60.0% discrepancy (added 2026-07-11 re-audit)**: this section's 62.7% (37/59) figure was computed at the time against whatever gold-file snapshot was live that session. A fresh direct recomputation (2026-07-11) of the same `resultats_task0_mapreduce_v9.csv` against the current authoritative `GOLD_narratologie_0807.csv`, strict match, gives **60.0% (36/60)** for the full file — the number used elsewhere in this document. The ~1-row/2.7pp gap is fully explained by a single documented gold-label correction between file versions (`Bienne-Gisele_La-malchimie.txt` ESPACE `ESP_UNIT`→`ESP_FRAG`, noted earlier in this section's own gold-set-diff table), which flips exactly one novel's correctness depending on which gold snapshot is used. **60.0% is the number to cite going forward**; 62.7% is a historically-accurate record of what that session saw, not an error, just a different gold snapshot.

#### run_task0_v9_espace_only.py — a failed shortcut (2026-07-10)
Built to isolate a fast ESPACE-only run: imports MAP step etc. unchanged from v9, trims REDUCE to one field, cuts `REDUCE_NUM_PREDICT` 3000→1200 (assuming a 1-field answer needs less budget). **Bug found in smoke test**: novel 1 failed completely (all 3 reduce votes empty/unparseable JSON), novel 2 had 1/3 votes fail the same way. Root cause: trimming field count didn't shrink the reasoning cost — the model still needs comparable thinking tokens to compare 9 sections' locations before emitting JSON. Same failure signature as the qwen3 truncation pattern (see Cross-Cutting Lessons). An auto-chain watcher had already fired and launched the full 45-novel run before this was caught — killed. **File is dead code, not deleted** — if revisited, `REDUCE_NUM_PREDICT` needs to go back up toward 3000 or be tested empirically first. Labiba reversed course and asked to resume the original full 7-criteria v9 run instead (`run_task0_mapreduce_v9.py --resume`), which continued from 33 novels already scored.

#### v9 full 7-criteria run — final result (2026-07-10)
**Corrected 2026-07-11**: the previously-reported "59.8% overall, TYPE 93.2%, INTRIGUE 42.4%/MODE 39.0%" figures were computed against the GOLD_* columns embedded in `resultats_task0_mapreduce_v9.csv` itself (N=59, one blank-gold row silently excluded), not against the actual current gold file. Direct recomputation (strict match, no "Acceptable aussi" alternates) by parsing `narratologie/GOLD_narratologie_0807.csv` (semicolon-delimited; col 0=filename, col 4=TYPE NARRATEUR gold, col 8=MODE NARRATIF gold, col 12=ESPACE gold, col 14=INTRIGUE gold) and joining against `resultats_task0_mapreduce_v9.csv` by filename gives the true numbers below. **Important caveat: this v9 file only has 60 rows — it was never extended to the full 79-novel gold set**, so these 4 criteria are only confirmed on 60/79 novels, not the full set.

**v9's best (max) ESPACE and FOCALISATION numbers, scored against the OLD 60-novel gold set (2026-07-11 recheck)**: since ESPACE's code vocabulary is unchanged between the old and current gold files, and FOCALISATION under the *old* scheme is directly comparable to v9's own old-scheme predictions, v9 was also re-scored against `narratologie/GOLD_narratologie_60novels_original.csv` (old 60-novel gold), both strict and with "Acceptable aussi" alternates counted:
- **ESPACE: 61.7% (37/60)**, strict match — files used: `resultats_task0_mapreduce_v9.csv` (predictions) vs. `narratologie/GOLD_narratologie_60novels_original.csv` (gold, column 12). Slightly higher than the 60.0% (36/60) figure against the current 79-novel gold — the 1-row gap is explained by a single documented gold-label correction (`Bienne-Gisele_La-malchimie.txt` ESPACE `ESP_UNIT`→`ESP_FRAG`) made between gold-file versions. **61.7% is the number kept as v9's headline ESPACE result.**
- **FOCALISATION (old scheme): 76.7% (46/60)**, counting "Acceptable aussi" alternates — files used: `resultats_task0_mapreduce_v9.csv` (predictions) vs. `narratologie/GOLD_narratologie_60novels_original.csv` (gold, column 6 + alternate column 7). Strict match alone gives 68.3% (41/60). This is on par with v5's own old-scheme FOCALISATION result (77.2%, 44/57, also counting alternates). **76.7% is kept as v9's headline FOCALISATION result** (old scheme only — does not apply to the current gold's new FOCALISATION scheme, where only v10c has ever been tested, at 32.9%).

| Criterion | Accuracy | N | Source file |
|---|---|---|---|
| TYPE NARRATEUR | **90.0%** | 54/60 | `resultats_task0_mapreduce_v9.csv` |
| MODE NARRATIF | **36.7%** | 22/60 | `resultats_task0_mapreduce_v9.csv` |
| ESPACE | **60.0%** | 36/60 | `resultats_task0_mapreduce_v9.csv` |
| INTRIGUE | **41.7%** | 25/60 | `resultats_task0_mapreduce_v9.csv` |

For RÉGIME NARRATIF, TEMPORALITÉ, and FOCALISATION, the v10c file (`resultats_task0_v10c_reduce_think.csv`) is the **latest/most-recent technique** for these 3 criteria, run at the full 79-novel scale, and supersedes v9's own (old-FOCALISATION-scheme, non-comparable) numbers on RÉGIME/TEMPORALITÉ:

| Criterion | Accuracy | N | Source file |
|---|---|---|---|
| RÉGIME NARRATIF | **60.8%** | 48/79 | `resultats_task0_v10c_reduce_think.csv` |
| TEMPORALITÉ | **68.4%** | 54/79 | `resultats_task0_v10c_reduce_think.csv` |
| FOCALISATION (new scheme) | **32.9%** | 26/79 | `resultats_task0_v10c_reduce_think.csv` — the ONLY file that attempts the new FOCALISATION scheme at full scale; a confirmed default-collapse bug (all 47 errors land on FOC_ELARG) is NOT resolved |

No single "overall %" figure is reported here since the 7 criteria now span two different N's (60 vs 79) and two different files/techniques — stating one blended overall number would obscure that.

### Full sweep and hybrid tables (2026-07-09/10) — corrects earlier stale-memory claims

A full sweep scored **every `resultats_*.csv` in `narratologie/`** against the current gold set (`GOLD_narratologie_0807.csv`, 79 novels), using positional column indices (the gold CSV has duplicate "Acceptable aussi:" headers that collapse under `csv.DictReader`, requiring raw `csv.reader` + manual index mapping — same gotcha as the hybrid-file build).

**Best local (non-paid) method per criterion, against the current 79-novel gold**:
| Criterion | Best file | Accuracy | N |
|---|---|---|---|
| TYPE NARRATEUR | `chunk_classifier_60novels.csv` | 91.7% | 55/60 |
| MODE NARRATIF | `chunk_classifier_60novels.csv` | 71.7% | 43/60 |
| RÉGIME NARRATIF | `chunk_classifier_60novels.csv` | 73.3% | 44/60 |
| INTRIGUE | `chunk_classifier_60novels.csv` | 68.3% | 41/60 (two files scored higher at 87.5%/80.0% but only on 8/5 novels — too small, discarded) |
| ESPACE | `resultats_task0_mapreduce_v9.csv` vs. `GOLD_narratologie_60novels_original.csv` (old gold) | **61.7%** | 37/60 — v9's max/headline ESPACE result (2026-07-11 recheck); against the current 79-novel gold it's 60.0% (36/60); the older `hybrid_v2/v3/v4`/`qwen3_30b_mapreduce` pick scores lower but on a more robust N: 55.3% (42/76) |
| TEMPORALITÉ | `resultats_hybrid.csv`/`hybrid_v4_60novels.csv` | 71.7% | 43/60 (old gold scheme; superseded at full 79-novel scale by v10c's **68.4% (54/79)**, see above) |
| FOCALISATION | `resultats_task0_mapreduce_v9.csv` vs. `GOLD_narratologie_60novels_original.csv` (old gold, incl. "Acceptable aussi" alternates) | **76.7%** | 46/60 — v9's max/headline FOCALISATION result under the OLD scheme (2026-07-11 recheck; strict match alone gives 68.3%, 41/60); on par with v5's 77.2% (44/57, also with alternates). **Does not apply to the current gold's new FOCALISATION scheme** — there, only `resultats_task0_v10c_reduce_think.csv` has ever been tested (the latest/only technique that attempts it): 32.9% (26/79), with a confirmed FOC_ELARG default-collapse bug, not resolved. Every other old-scheme file scores exactly 0% against the new scheme, not from low quality but structural incompatibility |

**Same sweep against the old 60-novel gold** (kept for reference, not to be conflated with the above): TYPE 93.3%, FOCALISATION 77.2% (v5, old-scheme-valid only), MODE 71.7%, RÉGIME 76.7%, ESPACE 73.3% (v9, N=15), INTRIGUE 68.3%, TEMPORALITÉ 71.7% — same chunk_classifier/hybrid winners for unchanged criteria.

**v10-at-full-scale timing**: v10b's 20-novel test took 75.8 minutes → ~3.8 min/novel → ~5 hours (300 min) for the full 79 novels, GPU-time only.

`hybrid_best_all_criteria.csv` (built earlier) still had the OLD picks (v3 mapreduce for TYP/MOD/ESP/INT) — flagged as needing a rebuild with the corrected per-criterion winners above before showing Riccardo anything; not confirmed done.

### Task 0 confusion-matrix diagnostics summary
- **TEMPORALITÉ (pre-fix)**: 15/19 errors (79%) are gold=TEMP_LIN→predicted=TEMP_DIS, traced to the "posture rétrospective" trigger conflating retrospective narrative stance with actual chronological discontinuity.
- **RÉGIME (pre-fix)**: REG_REAL↔REG_AUTO (5 combined, biggest), REG_SPEC→REG_REAL (4, under-triggers SPEC). REG_AUTO's looseness was a **deliberate v7 widening** to fix v3's opposite bug (REG_AUTO too narrow, missed true autobiographical texts) — a genuine, already-known precision/recall tension; tightening back risks reintroducing the old miss-rate.
- **v10/v10c/ESPACE**: see overcorrection/default-collapse sections above — now a confirmed recurring pattern (4 criteria) probably needing an architectural fix (evidence-count-based aggregation, tuned better than the v10d attempt) rather than one-off patches.

### Reports produced
`TASK0_FINAL_REPORT_2026-07-10.md` (mentioned as written 2026-07-10, contains the full v1-v9 hybrid tables both ways described above).

### Useful background research
- ["Says Who? Effective Zero-Shot Annotation of Focalization"](https://arxiv.org/html/2409.11390) — GPT-4o gets 84.79% F1 on a similar focalization task; "zero focalization" was their hardest category too (36% F1). **Note**: `old_report_to_add.md` refers to this same paper's findings under the label "Hicke et al. (2024) — Metaphor identification using large language models" — the specific numbers cited there (GPT-4o F1 84.79%, the FOC_ZERO failure pattern, the quotation-mark rule) match this paper exactly, so it is treated here as the same source under a possibly-mistyped title, not a second paper. Full additional findings from this paper, and how each one checked out (or didn't) against this project's own results:
  - **Per-model results reported in the paper**: Llama 3.1 70B best open model ("promising if not as reliable"); RoBERTa-base/DistilBERT ~74% F1 trained on only 300 samples; Llama 3.2 3B 62.67%, Llama 3.2 1B 1.13% (complete failure); logistic-regression baseline 71.84%; GPT-3.5-turbo 69.63%; GPT-4-turbo 80.82%. (Secondary sources cite GPT-4o's F1 as 86.90%; the arxiv full text says 84.79% — this project treats 84.79% as authoritative.)
  - **Best zero-shot prompt recipe per the paper**: embed Genette's definitions verbatim in the prompt, add a "speech in quotation marks = external focalization" rule, force single-word output (no chain-of-thought). A prompt variant stripped of all definitions still scored ~84.5% GPT-4o F1 — implying focalization knowledge is largely already baked into large-model pretraining, not something a prompt needs to teach from scratch.
  - **FOC_ZERO/omniscient is a universal failure mode, not just this project's problem**: 9 of the paper's 17 tested models labeled FOC_ZERO zero times ever; even GPT-4o only scored ~36% F1 on it. This matches this project's own experience (FOC_ZERO/FOC_ELARG-family default-collapse bugs, documented throughout the Task 0 section above) almost exactly, and is useful independent confirmation that the difficulty is structural to the task, not a bug specific to qwen3.
  - **Robustness finding**: GPT-4o achieved Krippendorff's α of 0.74 across 6 prompt variants (F1 range 79.8-84.5%) — i.e. GPT-4o's focalization performance is fairly stable to prompt wording, a property this project's own qwen3 pipeline notably lacks (see the "4-11pp swings from gold-set splits" finding below).
  - **Chain-of-thought hurts subjective/literary classification, per the paper** — but this project found the **opposite** for Task 1: no-think mode gave 0% figurative detection (catastrophic), thinking mode gave 81.2%. Reconciliation: the paper's CoT-hurts finding applies to *subjective* classification tasks (emotion, morality, focalization); Task 1 is closer to *semantic disambiguation* (is this specific word literal or figurative in this specific sentence), a different cognitive task where extended reasoning genuinely helps. Don't over-generalize the paper's CoT finding across task types.
  - **Self-consistency/majority voting** — the paper claims this "robustly improves classification without training" (5 samples, temperature 0.3-0.5). This project tested it for FOCALISATION (n=5, temp=0.3) and got **no improvement** (61.7% either way) — see the multi-model ensemble section above for why: voting only helps when the variance across samples is random noise, not when the model has a systematic bias (defaulting to FOC_INT) that all 5 samples share.
  - **Label-description sensitivity**: the paper reports 4-11pp swings from different gold-set splits and 2-6pp swings just from rewording the same criterion's definition, with effects "strongly heterogeneous across models and tasks" — i.e. what improves one criterion's prompt can do nothing or hurt another's. This is the same lesson as this project's own "isolate one variable per experiment" rule (Cross-Cutting Lessons section), independently confirmed in the literature.
  - **RoBERTa-large fine-tuning result, and why this project couldn't use it**: the paper reports RoBERTa-large reaching 77.5% F1 on focalization with only 300 training samples — far more sample-efficient than trying to fine-tune or prompt a generative LLM. This project's own gold set only ever had 60-79 novels, well short of the ~200-300 needed for this approach; a `RoBERTa-large`/`CamemBERT-large` fine-tune was never successfully attempted for exactly this reason (see the LoRA-fine-tune failure entry above, which hit the same "insufficient gold data" wall from a different angle). **If the gold set is ever expanded to 200-300+ novels, encoder fine-tuning (not more prompt engineering) is flagged as the literature-backed path most likely to break the ~65-70% plateau.**
  - **Caveat repeated in the paper itself and worth repeating here**: all of the above numbers are on **English** Stephen King paragraphs, not French novels. Treat the 77-84% range as upper-bound guidance for what's achievable with better technique, not a guarantee transferable to this project's French corpus and gold-set definitions.
- [LLM×MapReduce](https://arxiv.org/html/2410.09342v1) — inspired the mapreduce reduce-step design.
- **Constrained/JSON-schema decoding literature** (referenced in `old_report_to_add.md`, not independently re-verified this session): JSONSchemaBench (arxiv 2501.10868) reports constrained decoding both speeds generation (~50%) and improves classification accuracy by eliminating parse errors and constraining the label space; "Thinking Before Constraining" (arxiv 2601.07525) reports further gains from letting the model reason freely until a trigger token, then switching to constrained output. This project's own scripts do use JSON-constrained output throughout (eliminating parse errors was confirmed to work in practice), but never specifically tested the "free reasoning then constrain" hybrid from the second paper.
- Literature broadly reports ~70-75% as competitive for LLM-based narratology, ~80% with paid frontier models — this project's numbers are in that range.

### Open items at GPU freeze (2026-07-10)
- FOCALISATION new-scheme collapse (v10d partial fix, 1/4 on smoke test) — not resolved.
- REG_FANT / TEMP_DESORD 0% recall — diagnosed, not root-caused.
- ESPACE default-collapse — diagnosed as real model bias, not resolved.
- GPT-4o run stuck at 34/60 novels — needs account top-up + `load_done()` fix.
- New FOCALISATION scheme not applied to any of the GPT-4o/gpt-4o-mini numbers.
- "Read the model's reasoning on misses" diagnostic for MODE/RÉGIME/TEMPORALITÉ plateaus — proposed, never done.
- v9's ESPACE approach not yet confirmed at full scale on the old 60-novel or new 79-novel set (only N=15 confirmed as of last update); ~5.1-7.3h GPU time estimated.

### GPT-4o and gpt-4o-mini — final per-criterion tables

**GPT-4o v7 (paid, 34/60 novels completed before hitting a billing quota wall) vs. local qwen3:30b v7 on the same 34 novels:**

| Criterion | GPT-4o v7 | qwen3:30b v7 (same 34 novels) | Δ |
|---|---|---|---|
| TYPE NARRATEUR | 91.2% | 88.2% | +3.0pp |
| FOCALISATION | 76.5% | 76.5% | tie |
| MODE NARRATIF | 70.6% | 44.1% | +26.5pp |
| RÉGIME NARRATIF | 82.4% | 61.8% | +20.6pp |
| ESPACE | 73.5% | 55.9% | +17.6pp |
| INTRIGUE | 64.7% | 58.8% | +5.9pp |
| TEMPORALITÉ | 73.5% | 50.0% | +23.5pp |
| **OVERALL** | **76.1%** | **62.2%** | **+13.9pp** |

RÉGIME NARRATIF (82.4%) passed Riccardo's own named 80% target. GPT-4o wins or ties on every single criterion.

**gpt-4o-mini v7 (paid, all 60/60 novels) vs. local qwen3:30b v7 on the same 60 novels:**

| Criterion | gpt-4o-mini v7 | qwen3:30b v7 (same 60 novels) | Δ |
|---|---|---|---|
| TYPE NARRATEUR | 78.3% | 91.7% | −13.4pp |
| FOCALISATION | 71.7% | 71.7% | tie |
| MODE NARRATIF | 50.0% | 43.3% | +6.7pp |
| RÉGIME NARRATIF | 61.7% | 68.3% | −6.6pp |
| ESPACE | 58.3% | 53.3% | +5.0pp |
| INTRIGUE | 61.7% | 53.3% | +8.4pp |
| TEMPORALITÉ | 71.7% | 53.3% | +18.4pp |
| **OVERALL** | **64.8%** | **62.1%** | **+2.7pp** |

A modest real win over local qwen3, but well below full GPT-4o — confirms a genuine quality gap between mini and full models on this task, not just a price difference. Both tables use the **old** FOCALISATION scheme — neither model has been re-run against Riccardo's new coding scheme.

**Decision needed from Riccardo**: the full GPT-4o v7 run is stuck at 34/60 novels, having hit a hard OpenAI billing/quota limit partway through. **I'm leaving it to Riccardo to decide whether to finish the remaining 26 novels on GPT-4o.** Cost to complete: ≈$8.55 was already spent on the 34 completed novels; finishing the remaining 26 is projected to cost **~$6.40 more** (~$15 total for the full 60-novel gold set). Scaling the same pipeline to the entire 925-novel corpus is projected at **~$227 total**. This roughly confirms Labiba's own €22 estimate from the second meeting for a full-corpus run. Also needs a one-line `load_done()` fix before resuming, or the resume logic will wrongly skip the 2 novels that failed with quota errors instead of retrying them.

**This run does not need the local GPU.** GPT-4o/gpt-4o-mini calls go entirely through OpenAI's hosted API over the network — the port script only swaps the model backend, it never touches the local A40. So finishing the remaining 26 novels can be done at any time, independent of the GPU freeze or whatever else is using the shared GPU.

**Important caveat on what these 60/34 novels actually test**: both tables above (and the 34/60-novel GPT-4o run) were scored under the **OLD** FOCALISATION scheme (`FOC_INT`/`FOC_EXT`/`FOC_ZERO`/`FOC_VAR`) — this predates Riccardo's later, completely different new scheme (`FOC_ELARG`/`FOC_MIXTE`/`FOC_REST`/`FOC_RFOC`) used in the current 79-novel gold set. Neither GPT-4o nor gpt-4o-mini has ever been run against the new scheme or the full 79-novel gold set.

**Option for Riccardo to decide between**: (1) finish the remaining 26 novels on the *old* scheme/60-novel gold as costed above (~$6.40 more, ~$15 total), which is the cheaper option but won't be comparable to the current FOCALISATION scheme; or (2) run GPT-4o fresh against the **full current 79-novel gold set** under the *new* FOCALISATION scheme, which would cost roughly **~$19-20 for full GPT-4o** (extrapolating the same ≈$0.25/novel rate × 79 novels) or **~$1.20 for gpt-4o-mini** (extrapolating ≈$0.015/novel × 79 novels) — both figures are estimates, not measured, since neither has actually been run against the new scheme yet. I'm leaving it to Riccardo to pick which option to fund, since it's a real tradeoff between finishing the already-started old-scheme run cheaply versus getting a number that's actually comparable to the local qwen3 results on the current, canonical gold set.

---

<a id="task-1"></a>
## 4. Task 1 — Literal vs. Figurative Classification

### What it is
Classifies every animal/plant/Loterre mention as **référentiel** (real, physically present) or **figuré** (metaphor, comparison, idiom, symbol). Prerequisite for all downstream tasks (2, 3, 4.5) which only operate on référentiel mentions. **APPROVED by Riccardo** in the first meeting: "task one is okay with me, you can go ahead and apply to the entire corpus." Before this project's work, Joanna's ChatGPT-based classification got only ~47% (or per another transcript reading, 16%) accuracy.

### Model & setup
| Parameter | Value |
|---|---|
| Model | qwen3:30b |
| Server | Ollama, `http://localhost:11435` |
| GPU | NVIDIA A40 (46GB VRAM, ~22GB used by model) |
| Temperature | 0 (deterministic) |
| num_predict | 5000 (required for thinking mode) |
| Thinking mode | ON — required |

**Why thinking mode is required**: tested reducing `num_predict` for speed. At 100 tokens (no-think), figurative accuracy dropped to **0%**.

| num_predict | Speed | Figurative accuracy |
|---|---|---|
| 5000 | 9.4s/row | 81.2% (baseline) |
| 2000 | 7.1s/row | ~75% |
| 1000 | 5.5s/row | ~40% |
| 500 | 4.8s/row | ~13% |
| 100 (no-think) | 1.2s/row | **0%** |

### Final prompt design (v6, `evaluate_all_goldsets_v6.py`)
CORE_DEFINITIONS (7 rules): (1) known idiomatic expression → always figuré; (2) "comme"-comparison describing a human → figuré; (3) really present in the scene → référentiel; (4) scientific/geographic/naturalist/ecological context → référentiel; (5) real environmental crisis → référentiel even if the verb seems strong; (6) African/Asian term in colonial/travel context → référentiel; (7) metaphor describing human emotion/situation → figuré. Plus worked examples (4 réf + 5 fig for animaux; 5 réf + 5 fig + 3 "cas difficiles" for plantes, including the olive-branch symbol distinction).

**v6 baseline gold results**:
| Category | Gold set | Réf | Fig | Overall |
|---|---|---|---|---|
| Animaux | 190 rows (121 réf + 69 fig) | 97.5% (118/121) | 81.2% (56/69) | 91.6% (174/190) |
| Plantes | 188 rows (164 réf + 24 fig) | 98.8% (162/164) | 79.2% (19/24) | 96.3% (181/188) |
| Loterre | — | 91.2% | 63.4% | 85.2% |

Riccardo (in-meeting): more examples in the prompt counterintuitively made things worse for Task 1 — caused "hallucinating"/"overcomplicating," dropped accuracy. This directly informed the "no gold-set examples in prompts, keep examples minimal/generic" rule applied later to Tasks 2/4.5.

### Full prompt-version history, v1 through v8 (from `old_report_to_add.md` — the fuller chronology behind the "v6 final" summary above)
| Version | Overall | Réf | Fig | What changed |
|---|---|---|---|---|
| v1 (no examples) | 85.8% | 94.2% | 71.0% | Baseline — already beat Joanna's old GPT-4o-mini pipeline (~47% figuré) with zero prompt engineering |
| v2 (few-shot added) | 92.6% (batch=1) | 94.2% | 89.9% | Added 5+ examples per category — **but see the gold-set leakage bug below, this number is compromised** |
| v3 (independent examples, leakage fixed) | 89.5% | — | 78.3% | Replaced every leaked example with a verified-independent one; small accuracy cost vs. the (invalid) v2 number, but this is the first trustworthy result |
| v4 (two-pass classification) | Worse across all 3 categories | — | — | **Failed, reverted** — see below |
| v5 (additional targeted idiom examples) | ~91% | 97% | ~79% | Incremental improvement |
| **v6 (final for animaux/plantes)** | **91.6% / 96.3%** | **97.5% / 98.8%** | **81.2% / 79.2%** | Full few-shot set + refined rules — this is the version already detailed above |
| v7 (Loterre only, more référentiel examples added) | 86.8% | 95.3% | 56.1% | **Worse** — figuré recall dropped; reverted |
| v8 (Loterre only, targeted Group-A error fixes) | 85.2% | 91.2% | 63.4% | **Final for Loterre** |

### Gold-set leakage bug (v2→v3) — previously undocumented in this project's other records, found in `old_report_to_add.md`
Between v2 and v3, several few-shot examples embedded in the prompt were discovered to have been drawn accidentally from the gold set itself: "graminées," "serpolet," "oliviers" (all from the Plantes gold set), and "savane" (Chevillard), "marais" (Bouraoui), "habitat naturel," "forêts" (Hunzinger) — all from the Loterre gold set. **Why this matters**: if a gold-set example appears inside the prompt, the model may effectively have "seen the answer" for that exact case, artificially inflating the reported accuracy with no value for real unseen data — the same category of problem as the leaky-CV bug found later in Task 0's sklearn classifier (`train_chunk_classifier_60novels.py`), just caught earlier and in a different task. **Fix**: every leaked example was replaced with a genuinely independent one, sourced from standard French literature, common French idioms, and general ecological writing found via web search (queries like "French figurative expressions plants nature ecology metaphors examples littéral figuré"), which surfaced idioms like "les carottes sont cuites," "mettre du beurre dans les épinards," "ne pas avoir un radis," "être dans les choux," "prêcher dans le désert," "déplacer des montagnes," "ce n'est pas la mer à boire." This v2→v3 transition is the origin of the project's later standing rule (reapplied for Tasks 0/2/4.5) that **prompt examples must never be pulled from the gold set or a specific real corpus novel.**

### Two-pass classification (v4) — tried, failed, reverted
Hypothesis: since the model defaults to référentiel when uncertain, force it to actively consider figuré by splitting into two calls — Pass 1 asks "is this clearly référentiel?" (if yes, done); Pass 2, only triggered if Pass 1 is uncertain, asks "is this figuré?" with figuré-specific examples. Implemented as `evaluate_all_goldsets_v4.py`. **Result: worse than v3 on all three categories** (animaux, plantes, Loterre). Why it failed: two API calls per uncertain item doubled the runtime, but more importantly, when Pass 1 says "uncertain," Pass 2 doesn't get enough surrounding context to reliably flip the answer to figuré — the model's first-instinct read of the full context was usually already the more reliable signal. **Lesson**: more API calls per item does not mean better accuracy; splitting one classification into sequential passes can hurt precisely because each pass sees strictly less context than a single comprehensive prompt would.

### Class imbalance analysis — why "overall accuracy high, figuré accuracy low" is a class-imbalance/annotation-difficulty issue, not a model-quality issue
Gold-set class distributions: Animaux 121 référentiel (63%) vs. 69 figuré (36%); Plantes 164 référentiel (~87%) vs. 24 figuré (~13%); Loterre 148 référentiel (78%) vs. 41 figuré (22%). Because référentiel dominates every gold set, predicting référentiel when uncertain is the statistically "safe" bet — right 63-87% of the time by default — which structurally biases the model toward higher référentiel precision and lower figuré recall, independent of prompt quality. **Conclusion communicated to Riccardo at the time**: this is a class-imbalance and annotation-ambiguity problem, not a model-quality problem — human annotators only agree with each other 76% of the time on this exact task (Cohen's Kappa = 0.64), and the project's 91.6%/92.1% overall figures for animaux already **exceed** that human-agreement ceiling. Chasing 90%+ figuré accuracy specifically may not be an achievable or even meaningful target given where the human ceiling itself sits.

### Response-parsing pipeline evolution (engineering detail, not a modeling choice, but relevant to why later runs stopped silently failing)
Models return inconsistent output — sometimes JSON alone, sometimes wrapped in a markdown code fence, sometimes with stray text around it, sometimes with leftover `<think>...</think>` tokens even when the caller expected a clean answer. The parsing pipeline that stabilized this, in order: (1) strip any `<think>...</think>` block via regex; (2) if a markdown code fence is present, extract its contents; (3) regex-extract the first `{...}` JSON object and parse it; (4) if that fails, fall back to scanning the raw text for the literal words "référentiel"/"figuré"; (5) if even that fails, default to "référentiel" (the statistically safer default, consistent with the class-imbalance finding above, rather than an arbitrary choice). This layered fallback is why later production runs could report a small "failed rows, defaulted to référentiel" count instead of crashing outright — the same handling pattern used in the Task 1 corpus run's failed-batch tracking (see below).

### Port configuration bug (fixed early)
An early script defaulted to port 11434 (the *other* research team's shared Ollama instance, hosting qwen2.5-family models) instead of port 11435 (this project's own private Ollama instance, hosting qwen3:30b) — causing intermittent wrong-model results or authentication errors depending on which instance happened to answer first. Fixed by standardizing every script to reference port 11435 explicitly. This is a distinct, earlier bug from the later "wrong production input file" bug documented in the Task 2 section (which was about pointing at Joanna's old labels instead of this project's own Task 1 output) — different failure, same family of "silently reading from the wrong source" mistake.

### Speed problem and batching solution
At single-row 9s/row: Animaux (127,816 rows) ≈319h=13.3 days; Plantes (69,287 rows) ≈173h=7.2 days; total ~20 days — infeasible before the deadline. **Strategy tested: batching N rows per API call.**

| Batch size | Speed | Animaux (corpus days) | Plantes (corpus days) | Fig accuracy (animaux gold) |
|---|---|---|---|---|
| 1 (baseline) | 9.0s/row | 13.3 | 7.2 | 81.2% |
| 3 | 4.4s/row | 6.5 | 3.0 | 81.2% |
| **4 (chosen)** | **3.9s/row** | **5.8** | **2.7** | **81.2%** |
| 5 | 3.4s/row | 5.0 | 3.2 | 79.7% |

Full gold-set comparison confirmed batch=3/4 preserve identical figurative accuracy to single-row v6 on animaux; only batch=5 lost 1 extra figurative item.

**Animaux (121 réf + 69 fig = 190 rows), all batch sizes**:
| Method | Réf | Fig | Overall | Speed |
|---|---|---|---|---|
| v6 (1 row) | 118/121 (97.5%) | 56/69 (81.2%) | 174/190 (91.6%) | 9.0s |
| batch=3 | 117/121 (96.7%) | 56/69 (81.2%) | 173/190 (91.1%) | 4.4s |
| **batch=4** | **115/121 (95.0%)** | **56/69 (81.2%)** | **171/190 (90.0%)** | **3.9s** |
| batch=5 | 114/121 (94.2%) | 55/69 (79.7%) | 169/190 (88.9%) | 3.4s |

**Plantes (164 réf + 24 fig = 188 rows), all batch sizes**:
| Method | Réf | Fig | Overall | Speed |
|---|---|---|---|---|
| v6 (1 row) | 162/164 (98.8%) | 19/24 (79.2%) | 181/188 (96.3%) | 9.0s |
| batch=3 | 164/164 (100.0%) | 14/24 (58.3%) | 178/188 (94.7%) | 3.7s |
| **batch=4** | **160/164 (97.6%)** | **18/24 (75.0%)** | **178/188 (94.7%)** | **3.3s** |
| batch=5 | 160/164 (97.6%) | 17/24 (70.8%) | 177/188 (94.1%) | 3.1s |

Note: batch=3's plantes fig 58.3% is a statistical artifact (only 24 fig items in the gold set, each error = 4.2pp swing) — batch=3 happened to pair figurative plant terms next to very literal ones, biasing the model; not a reliable measurement.

**Decision: batch=4** — same fig accuracy as v6 for animaux (81.2%), close for plantes (75.0% vs 79.2%, 1-item difference), total time 5.8+2.7=8.5 days.

The full raw row-by-row prediction log behind these tables (every individual gold-set item across batch=3/4/5, ~800+ lines) is preserved verbatim in `PROJECT_DOCUMENTATION.md` §4 (`batch_testing_results.txt`) — not reproduced line-by-line here since the aggregate tables above already capture every number from it.

### Known systematic errors (wrong in ALL batch sizes — genuine limitations)
**Animaux (12)**: agneaux (gold réf, model fig — ambiguous, probably gold correct), grenouilles (gold réf, model fig — ambiguous cultural ref), porc (gold fig, model réf — system likely correct, literal pig), vache (gold fig, model réf — "draw a cow" = literal, system likely correct), bœuf (gold réf, model fig — "nerf de bœuf" misread as expression), chimpanzés (gold fig, model réf — "à un % près nous sommes des chimpanzés," scientific-sounding but figurative), chiens ×1 (gold fig, model réf — borderline), lion ×2 (gold fig, model réf — implicit metaphor, no explicit marker), abeille (gold réf, model fig — philosophical analogy misleads), âne ×2 (gold fig, model réf — implicit metaphor).

**Plantes (5)**: plantes ligneuses (gold fig, model réf — system may be right, rotting-plants context), jasmin (gold fig, model réf — "bercés dans le jasmin," ambiguous), abricotier (gold fig, model réf — implicit metaphor), palmiers (gold fig, model réf — learning context, could be literal), ananas (gold fig, model réf — borderline).

**Why these occur**: implicit metaphors with no explicit marker ("comme", "tel un") default to référentiel; truncated context may hide the figurative signal in the surrounding paragraph; some are genuinely ambiguous even for human annotators.

**Why not fixed before running**: increasing context (200→400 chars) would require re-extracting from all 925 raw novels — too risky given the deadline, ~15% time cost; adding prompt examples for these cases risks breaking currently-correct items; the 17 systematic errors are a small fraction of ~197k rows; documented as known limitations for the paper instead.

### Corpus files run on
| File | Rows |
|---|---|
| `resultats/corpus_principal/ENTITES_contexte_animaux.csv` | 114,851 |
| `resultats/bestsellers/BESTSELLERS_contexte_animaux.csv` | 13,094 |
| `resultats/corpus_principal/ENTITES_contexte_plantes.csv` | 63,599 |
| `resultats/bestsellers/BESTSELLERS_contexte_plantes.csv` | 5,720 |

After dedup: Animaux ~127,816 unique rows, Plantes ~69,287 unique rows. Column names differ (`truncated_sentence` vs `contexte`) — run script normalizes both. Run must be launched from `~/ecopoetique/métaphore/` (relative paths resolved against CWD) — wrong directory → 0 rows found → crash, but doesn't touch the real checkpoint.

### Riccardo's ambiguous-case rulings (June 25 meeting, live review of 15 disagreements)
Most flagged disagreements were genuine gold-set errors, not model errors:
- **"Picture within a picture"** (tableau showing sea, curtain with bird motifs, gallery showing mountain drawings) → **FIGURATIVE** — a representation, not the real thing. This ruling is the origin of Task 2's later `IMAG` category.
- **"Mountain of toys"** (metaphorical mountain = big quantity) → **FIGURATIVE**
- **"Animal farm to his room"** → ambiguous, probably FIGURATIVE
- **"Lac/étoile" (star bar structure)** → if "lac" (lake), REFERENTIAL; if "star", figurative — Riccardo leans "lac" so probably REFERENTIAL
- **Ruins on shore of lake (case #12)** → could go either way, Riccardo leans FIGURATIVE

### Run and corpus completion
Started June 28, 2026 (`métaphore/run_task1_corpus.py --category animaux`, then `--category plantes`). Fully resumable — reads existing output CSV and skips already-classified rows.

**Animaux: done 2026-07-05** (incl. a retry pass — `retry_animaux.py`/`retry_animaux_v2.py`, both dated 2026-07-05, verified via aggregate-count check).

**Plantes**: running through 2026-07-08/09, progressed 36.3%→75.6%→83.1%→finished 2026-07-10 07:28 (19.8h run) + 2 retry passes (376/444, then 36/68 resolved) — **32 rows permanently unresolved** (0.05% of corpus), in `resultats/task1_plantes_failed_keys_v3.tsv`. **Final: 69,468 rows, 59,967 référentiel / 9,501 figuré (13.7%).**

### Task 1 duplicate-process incident (2026-07-09 morning) — bug and fix
The overnight orchestrator (`orchestrate_task0_after_2_45.sh`) tried to stop Task 1 (found via `pgrep -f "run_task1_corpus.py --category plantes"`) before relaunching. It logged `"Task 1 (PID 3256944) stopped."` but PID 3256944 **never existed** — off-by-one from the real PID 3256945. The `kill` silently no-opped, and the script's linear structure never verified the process actually died before launching a fresh one at 01:56:59.

**Result: two instances of the same script ran concurrently for ~7.5 hours**, both with the output file open for writing (confirmed via `lsof`, same inode). Produced **3,529+ exact-duplicate rows** in `resultats/task1_plantes_labels.csv`, found by full CSV-aware parse — naive `awk -F'\t'` field-count checks gave false-positive "malformed row" signals because `contexte` legitimately contains embedded newlines inside quoted CSV values.

**Fix applied**: killed both PIDs, backed up the corrupted file (`task1_plantes_labels_CORRUPTED_BACKUP_<timestamp>.csv`), deduped via `csv.reader` (not naive text splitting) keeping first-seen rows, replaced the live file, relaunched a single instance, confirmed via the log's own "Resuming: N rows already done" line that N (48,848) was sane rather than assuming success.

**Root cause**: the resume logic keys done-rows by `(fichier, token_lexique, contexte)` tuple loaded fresh at each process startup — no locking/shared state between concurrent instances, so two instances race on file writes (this incident's damage was limited to clean full-row duplicates, not truncated writes, but partial-row corruption was also possible).

**General lesson**: never trust a script's own "process stopped" log line for this project's long-running jobs — always independently verify via `ps`/`pgrep` that the PID is actually gone before relaunching, especially in unattended/orchestrator scripts. Any future kill-and-relaunch of `run_task1_corpus.py` needs an explicit post-kill liveness check (loop until `pgrep -f` returns nothing, with timeout/abort).

### Other Task 1 bugs found and fixed
- **O(n²) resume-scan bug** (found+fixed 2026-07-08, first-ever restart of the plantes run): `run_task1_corpus.py` did a linear scan through all 69K rows per already-done row — ~1.3 billion comparisons, would hang indefinitely at scale. Fixed to O(1) dict lookup. Latent the whole time, only surfaced on the first restart.
- **Speed drift investigated 2026-07-08**: after fixing the O(n²) bug + stopping a concurrent Task 3 CPU job, speed recovered to 3.8-3.9s/row baseline (trend 5.0→4.8→4.4→4.3→4.1→4.0→3.9s/row). Later drifted back to 4.5-4.6s/row by ~22:53 with zero other GPU/CPU jobs of the project's own running — traced to **a colleague's CPU job** (`step4_alignment.py`, PID 2901956) growing its own CPU usage over the day (~51 cores/5116% at 16:36 → ~56 cores/5603-5604% by 22:53, sampled 3x). External contention, not a bug in the pipeline. A second restart (~22:57, at Labiba's explicit request despite this diagnosis) confirmed resumed correctly with no data loss (43,634 rows preserved, 25,680 remaining) — as predicted, didn't fix the externally-caused slowdown.
- **A separate GPU-contention episode** (2026-07-08): colleague Martial de Jurquet (`mdejurquet`) ran a training job (`pipeline1/step3_final_training.py`) on the shared A40 from 07:05:12 to ~10:46:34 UTC (~3h41m), confirmed via his own world-readable logs. It crashed with `RuntimeError: expected scalar type Half but found Float` (fp16/fp32 mismatch) after Fold 1 Epoch 1. Measurably slowed Task 1 plantes from 3.7s/row to 4.2-4.3s/row during that window — expected behavior per the established "sustained GPU load slows Task 1" pattern, not a bug in this project's own pipeline. (Server clock is UTC; user's local time is UTC+2.)

### GPU-sharing throttle mechanism
`run_task1_corpus_throttled.py` — sleep-based throttling script, roughly halves duty cycle at ~2x runtime cost, used when a colleague needs the shared A40 back (no sudo/MPS access for hard partitioning on this machine).

### Riccardo's own published paper — benchmarks this project's Task 1 work was checked against
**Barontini, R. (2026), "Le tournant écologique à l'épreuve des humanités numériques : le romanesque de la biodiversité"** (published in an anthology — this is Riccardo's own academic paper reporting the project's pre-existing findings, distinct from the arxiv literature cited elsewhere). Key claims from this paper that this project's own Task 1 work was measured against:
- "Precision obtained by LLM approaches 90%, validated by manual annotation on sample" — this specific figure refers to GPT-4o-mini's performance on examples where human annotators agreed, not overall accuracy. This project's own broader gold-set numbers (85-96% overall depending on category) are consistent with, not contradicting, this claim once the different denominators are accounted for.
- **Human inter-annotator agreement**: 76% common annotations, Cohen's Kappa = 0.64 (moderate agreement) — this is the ceiling figure repeatedly referenced throughout this document (e.g. in the class-imbalance analysis above) as the benchmark any automated system should be judged against, not 100%.
- GPT-4o-mini accuracy on unanimously-agreed examples: 89.7%; overall accuracy between 79% and 85%.
- Animal uses in the corpus (per Riccardo's original figures, predating this project's own corpus-wide run): 84.5% literal, 15.5% figurative. Plant uses: 81.3% literal. **Compare against this project's own audited corpus-wide figures**: animaux 29.9% figuré, plantes 13.7% figuré (see the Task 1 full-corpus results table above) — the animaux figurative rate in particular is roughly double Riccardo's original estimate, worth flagging as a real, checkable discrepancy between the pre-existing published figure and this project's own more complete corpus run, not something to silently reconcile.
- 73% of figurative animal uses compare to the human body (CH category) — cited again in the Task 4.5 section above as Johanna's finding; the same number appears in Riccardo's own paper, confirming it's a genuinely established, cross-validated result from before this project's Task 4.5 rework, not a one-off finding.

**Riccardo's own anxious quote about the broader project, worth preserving for context** (June 25 meeting): *"I'm a little bit anxious about what I'm getting in terms of interpretation from all this work. Probably not that much. Which is kind of frustrating."*

### Full gold-set audit (2026-07-10) — final, verified against live production output
| Gold set | Raw accuracy | Ref acc | Fig acc |
|---|---|---|---|
| Animaux | 90.1% (154/171) | 96.3% | 79.0% |
| Plantes | 96.8% (180/186) | 99.4% | 79.2% |
| Loterre | 85.2% (161/189, from `eval_loterre_v8_results.csv` — NOT current production prompt) | 91.2% | 63.4% |

**Manual audit of all 33 rows where gold=figuré but model=référentiel**, full context read for each: found **13 confirmed gold-set mislabels** (model was actually right) — animaux 3 (chiens, pattes de lion ×2, matching the "boiserie chêne" material-term precedent), plantes 3 (jasmin, palmiers, ananas — all literal), Loterre 7 (forêt, mers, océan, lac ×2, plage, animaux — real geographic features used literally). 4 more borderline (porc, abricotier, désert, incendie) — genuine judgment calls, not counted either way.

**Corrected accuracy after removing confirmed gold mislabels: Animaux 91.8%, Plantes 98.4%, Loterre 88.9%.** The 4 borderline rows (porc, abricotier, désert, incendie) were left as originally labeled — only the 13 confirmed mislabels were corrected.

**Corrected accuracy, per category, référentiel vs. figuré split** (this is the number to use when citing per-class performance, not just the blended overall figure above):

| Gold set | Référentiel | Figuré | Overall |
|---|---|---|---|
| **Animaux** | 108/112 = **96.4%** | 49/59 = **83.1%** | 157/171 = **91.8%** |
| **Plantes** | 164/165 = **99.4%** | 19/21 = **90.5%** | 183/186 = **98.4%** |
| **Loterre** | 142/155 = **91.6%** | 26/34 = **76.5%** | 168/189 = **88.9%** |

Plantes gets the biggest figuré lift (79.2%→90.5%, since 3 of its 5 errors were gold mislabels). Loterre improves the most in absolute terms (63.4%→76.5%) but remains the weakest set even after correction — a genuinely harder benchmark, not just a mislabeling artifact. **Note on Loterre**: scored with an older eval script (`evaluate_loterre_v8.py`), a slightly different prompt build than the current production script (`run_task1_corpus.py`, "exact v6 prompts") — closest available benchmark, but not a re-run apples-to-apples check against the current production prompt.

**100-random-sample manual spot-checks** (50 fig + 50 ref, independent of gold sets), full breakdown:

| Category | Figuré sample clean | Référentiel sample clean | Combined |
|---|---|---|---|
| Plantes | 43/50 (86%) | 49/50 (98%) | **92/100 (92%)** |
| Animaux | 45/50 (90%) | 45/50 (90%) | **90/100 (90%)** |

Both land close to the gold-set accuracy figures, cross-validating the gold-set results — errors are small and consistent, not random noise. Recurring error patterns found: (1) homograph collisions (grenadier=soldier not tree, oedipe=complex not monkey); (2) representations/images of animals inconsistently handled (teddy bear correctly scored figuré, matching Riccardo's IMAG ruling, but glass figurine/painting/photo of animals wrongly stayed référentiel — same representation logic not consistently applied, flagged as worth fixing); (3) literal/scientific-toned statements wrongly flagged figuré (e.g. a "fact" about grapefruit being an orange/lemon hybrid); (4) real trees serving a symbolic/ceremonial purpose (young poplars at a memorial) sometimes mislabeled figuré even though physically present in the scene, violating the task's own rule 3 (physical presence wins).

### Full-corpus production run — yes, this ran on the entire corpus (all 925 novels + bestsellers), not just the gold sets

**Production script**: `métaphore/run_task1_corpus.py` (+ `run_task1_corpus_throttled.py`, a sleep-based throttled variant for GPU-sharing scenarios, ~2x runtime cost for roughly half duty cycle).

**Full-corpus results** (actual production output, all 925 novels + bestsellers subset):

| Category | Total rows | Référentiel | Figuré | % Figuré |
|---|---|---|---|---|
| **Animaux** | 127,935 | 89,675 | 38,260 | **29.9%** |
| **Plantes** | 69,468 | 59,967 | 9,501 | **13.7%** |

Plantes' lower figuré rate is **not a bug** — it matches the plantes gold set's own ratio (12.8% figuré, 188 rows), reflecting a real corpus pattern: animals are used figuratively/idiomatically far more often than plants in this collection of French novels.

**Where the actual result files live:**
- `resultats/task1_animaux_labels.csv` — 127,935 rows, tab-delimited (fichier, token_lexique, contexte, lemme, categorie, task1_label)
- `resultats/task1_plantes_labels.csv` — 69,468 rows, same format (pre-patch backup: `task1_plantes_labels.csv.bak_before_retry_patch`)
- Plantes failed-batch tracking: `resultats/task1_plantes_failed_keys.tsv` (444 unresolved, first pass) → `resultats/task1_plantes_failed_keys_v2.tsv` (68 unresolved after retry 1) → `resultats/task1_plantes_failed_keys_v3.tsv` (32 permanently unresolved after retry 2, 0.05% of corpus, defaulted to référentiel)
- Retry scripts: `morphosyntaxe/retry_plantes.py`, `morphosyntaxe/retry_plantes_v2.py`
- Retry logs: `resultats/task1_plantes_retry.log`, `resultats/task1_plantes_retry_v2.log`, watcher log `resultats/task1_plantes_retry_watcher.log`
- Gold sets: `métaphore/GOLD_litteralite_animaux.csv`, `métaphore/GOLD_litteralite_plantes_RB.csv`, `métaphore/GOLD_litteralite_loterre__RB.csv` (+ non-RB draft `GOLD_litteralite_loterre.csv`)
- Loterre evaluation script/output: `métaphore/evaluate_loterre_v8.py`, `métaphore/eval_loterre_v8_results.csv`
- Run logs: `resultats/task1_plantes_run.log` (19.8h total runtime, finished 2026-07-10 07:28 UTC); animaux run finished 2026-07-05 (full run history in `PROJECT_DOCUMENTATION.md`)

**Open items noted in the original report**: 19 animaux gold rows and 2 plantes gold rows couldn't be matched to the production output by exact key (possibly text-normalization differences like curly quotes, or rows predating the last retry patch) — flagged, not resolved.

**Report**: `TASK1_FINAL_REPORT_2026-07-10.md`, supersedes `task1_report.md` (June 28) — full content now merged into this document.

### Loterre — NOT run on the full corpus

**We have not run Task 1 on the full corpus for Loterre.** Only animaux and plantes were run on the entire 925-novel corpus (see the full-corpus results table above). Loterre exists only as a **gold-set benchmark** (189 rows) scored with an older evaluation script (`evaluate_loterre_v8.py`) during prompt development — it was never pointed at the full corpus of Loterre term mentions.

**If we wanted to run it**: Loterre terms (ecological/geographic/climate-change vocabulary from the [Loterre thesaurus](https://loterre.istex.fr/fr/)) appear **108,425 times** across the corpus (`ENTITES_TOTAL`, per the original README-level corpus stats). At the same production rate used for animaux/plantes (batch=4, ~3.9s/row), a full run would take **≈117.5 hours ≈ 4.9 days of GPU time** — comparable in scale to the plantes run (69,287 rows, 2.7 days) plus most of another animaux-sized run. This has not been attempted; it's an open, undone item, not a completed-but-unreported task.

### Task 1 — current final state
**Fully complete for animaux and plantes** as of 2026-07-10 (no open blockers on those two). **Loterre was never run on the full corpus** — only its 189-row gold set was ever scored, for prompt-development purposes.

---

<a id="task-2"></a>
## 5. Task 2 — Metaphor Subcategory Classification

### What it is
Classifies figurative mentions (Task 1 output, `figuré` only) into structural subcategories of metaphor — originally 16, later 19 with 3 new categories added, later 18 after one was eliminated. Approved as already-designed by Riccardo ("this is already done") in the first meeting, but must use **this project's own Task 1 results**, not Joanna's old ChatGPT-based figurative-identification output.

### Categories
**Original 16** (embedded in the script, confirmed matching Riccardo's own reference table). **3 new categories** added live during the second meeting (discovered while Riccardo corrected the Task 1 gold set):
- **COUL** — plant/animal term used purely to name a color (e.g. "vert pomme" = apple green)
- **LOC_IDIOM** — fully lexicalized idiom where the animal/plant no longer evokes the real thing (e.g. French equivalent of "finding a needle in a haystack")
- **IMAG** — a depiction/representation (drawing, embroidery, painting) rather than the animal/plant itself

Formal definitions for all 19 received 2026-07-08: `métaphore/schema_analogies_vivant_complet_0807.csv`.

**META_JUXT eliminated** (Riccardo's decision, email 2026-07-10): META_APP and META_JUXT's written definitions both describe the same plain noun-noun juxtaposition structure (e.g. "la montagne sentinelle" vs "forêt cathédrale") — drop META_JUXT entirely, fold everything into META_APP. Implemented: removed META_JUXT's decision-tree question (was question 10), merged its pattern into question 9 (META_APP), renumbered questions 10→9 through 14→13. `validate_task2_gold.py` normalizes any gold rows still labeled META_JUXT (ids 8, 20) to META_APP before scoring. **Effectively 18 active categories now** (META_JUXT retired but still listed in `SUBCATEGORIES`/`VALID_CODES` unless told to fully purge).

### The complete original 16-category typology, with worked examples and rule-based detection shortcuts
This full table (from `old_report_to_add.md`) is the original schema referenced above before the 3 new categories (COUL/LOC_IDIOM/IMAG) were added and META_JUXT was later eliminated — kept here in full since the summary above only names the categories added/removed, not the base 16 with their examples:

| Code | Type | Example | Rule-based detection shortcut |
|---|---|---|---|
| COMME_SN | Simile with nominal group | "rusé **comme** un renard" | contains "comme" |
| COMME_P | Simile with proposition | "craquaient **comme** les os d'un cerf" | contains "comme" |
| COMME_SI | Simile with "comme si" | "**comme si** une forêt retenait son souffle" | contains "comme si" |
| COMP_DEG | Degree comparison | "**plus lent qu'**une tortue" | contains "plus/moins/aussi/autant que" |
| DE_PARANGON | Genitive of paradigm | "mémoire **d'**éléphant" | contains "de + nature term" |
| DE_MATIERE | Genitive of material | "volonté **de** granit" | contains "de + nature term" |
| DE_UNIVERS | Genitive of universe | "océan **de** verdure" | contains "de + nature term" |
| DE_QUANTIF | Genitive of quantification | "une forêt **de** pylônes" | contains "de + nature term" |
| DE_PROP | Genitive of property | "vautours **de** la finance" | contains "de + nature term" |
| META_ATTR | Attributive metaphor | "cet homme **est** un loup" | — |
| META_APP | Appellative metaphor | "la montagne **sentinelle**" | — |
| META_JUXT | Juxtaposition metaphor (later eliminated, folded into META_APP) | "arbre-parapluie" | — |
| META_VERB | Verbal metaphor | "la forêt **avalait** la lumière" | verb + nature entity as subject |
| MOD_ANALOG | Modal analogy | "**on aurait dit** une meute" | contains "on dirait/sembler/avoir l'air" |
| ANALOG_COMPLEX | Complex embedded comparison | embedded multi-level analogy | — |
| META_FILEE | Extended metaphor network | sustained metaphor across a paragraph | — |

Note that the "de + nature term" shortcut is a **weak/ambiguous** heuristic on its own — it flags 5 of the 16 categories (DE_PARANGON/DE_MATIERE/DE_UNIVERS/DE_QUANTIF/DE_PROP) equally, meaning genitive-construction detection alone cannot distinguish between them; this matches the project's own later-diagnosed finding that DE_PARANGON specifically acts as a "false-positive sink" pulling in DE_PROP/META_APP/COMME_SN cases (see the confusion-matrix section below) — the ambiguity was structural from the beginning, not an artifact introduced later.

### Loterre semantic-category sub-task (separate from literal/figurative — done by Johanna, not by this project)
A distinct classification task, run only on Loterre terms, sorting each into one of 5 semantic categories rather than literal/figurative: (1) Milieux naturels (natural environments), (2) Vocabulaire du vivant (living-world vocabulary), (3) Climat (climate), (4) Activités humaines (human activities), (5) Menaces écologiques (ecological threats). Method: GPT-4o-mini via the OpenAI API, batches of ~200 terms, JSON output, run in Google Colab (output file `categorisation_termes.json`). **This was completed by Johanna before this project's work began and was not touched or re-verified by this project** — noted here as a distinct, adjacent classification effort so it isn't confused with Task 2's literal/figurative-subcategory work, which is a different axis of classification applied to a different subset (figurative animal/plant mentions, not Loterre terms).

### Bugs found and fixed (2026-07-09)
1. **Wrong production input file**: `run_task2_subcategories.py` was reading `métaphores_identifiées_gpt.csv` — Joanna's OLD ChatGPT-based output (23,327 rows, built May 31, predates Task 1 entirely) — not this project's own Task 1 (qwen3) results, directly contradicting Riccardo's June 25 instruction. Verified: only 12,473/23,683 keys overlap with Task 1 animaux `figuré` rows (38,260 total) — barely half agree. **Fixed**: built `build_figurative_cases.py`, merging `task1_animaux_labels.csv` (complete) + `task1_plantes_labels.csv` (partial at the time) into `figuratifs_task1_own.csv`, repointed `INPUT_FILE`. Only affects an eventual full-corpus run — gold validation was never affected (uses the separately-annotated `comparison/gold_task2_task45_RB.csv`).
2. **qwen3 truncation bug** (see Cross-Cutting Lessons for the general pattern): the 14-step decision-tree prompt with `num_predict=3000` caused 17/114 (15%) gold rows to come back `UNKNOWN`, reproduced directly (`done_reason: "length"`, `eval_count: 3000`, empty content). **Fixed**: `num_predict` raised to 8000, and `context[:300]` truncation removed (some gold contexts >300 chars, token itself sometimes fell entirely outside that window — 14/200 gold rows affected).
3. **Rule-based regexes scored 0/7 at gold-check**: the "safe" fixed-phrase rules (COMME_SI/COMP_DEG/MOD_ANALOG) matched anywhere in the whole multi-sentence `contexte` paragraph, not the clause near the token, firing on coincidental unrelated phrases. Removed entirely, then partially reinstated with a real curated lexicon (below).

### Idiom lexicon fix
Found and wired in `métaphore/liste_expressions_figées.txt` — a 65-entry curated lexicon of real fixed French animal idioms built by Joanna's team pre-Task-2 (originally used by an unrelated script, `scripts/filter_idiomatic.py`), reinstated as the ONE rule-based check (exact substring match against these 65 known idioms only — high-precision by construction). Note: animal-only, no plant-idiom equivalent exists anywhere in the codebase.

### Version-by-version accuracy history
| Version | Result | N | What changed |
|---|---|---|---|
| Rule-based-only baseline | 16.7% (2/12) | 12 | Original regex heuristics — worse than chance, removed |
| LLM-path-only baseline | 51.4% (38/74) | 74 | — |
| Combined (flat 19-way prompt, pre-decision-tree) | 46.5% (40/86) | 86 | Original flat prompt |
| Decision-tree redesign (14 steps, based on [MIPVU rule-script/decision-procedure prompting, arxiv 2603.10784](https://arxiv.org/abs/2603.10784) — the same literature basis that also informed Task 0's RÉGIME NARRATIF fix), first test | 51.8% (59/114) | 114 | Restructured from flat pick into sequential decision tree; still had truncation bug live |
| After truncation fix + decision-tree reordering (META_FILEE→Q4, META_APP→Q9, IMAG broadened) | 57.7% | 114 | Confusion-matrix-driven fixes: META_APP 7/7 wrong (swallowed by earlier questions), META_FILEE 3/3 wrong (checked last), IMAG 5/5 wrong (definition too narrow, missing shape-resemblance) |
| **v5** — idiom lexicon reinstated + 10 hand-picked few-shot LOC_IDIOM examples | **64.9% (74/114)** | 114 | See mixed-result finding below |
| Root-cause fix: LOC_IDIOM question-1 exclusion clause (4-case) | pending re-test at session end | 114 | See below |
| **v6** — 4 targeted prompt changes (LOC_IDIOM self-check, MOD_ANALOG broadened, DE_PARANGON/META_ATTR exclusions) | **69.3% (79/114)**, up from v5's 66.7% (76/114) | 114 | Small-batch protocol validated first: 20-row targeted batch, 6/15 targeted errors fixed, 0/5 regressions — clean win, confirmed real |
| **META_JUXT eliminated only** | 73.7% (84/114) | 114 | — |
| Few-shot fix (2nd round: don't-skip-ahead reminder, META_ATTR vs LOC_IDIOM contrastive examples, DE_PARANGON vs DE_PROP discriminator) | **2/10 on 10-row targeted smoke test** — weak | — | **NOT scaled to a full rerun** — not worth ~100min GPU time for likely-marginal gain |
| v8 — fresh few-shot run (all 114 re-scored, first time these fixes tested at scale) | **paused mid-run at 43/114**, early signal weak/flat (69.8-74.2%) | 114 | GPU freeze began before completion |

### v5 mixed-result diagnosis (2026-07-10)
Finished interrupted gold validation at **64.9% (74/114)**, up from 57.7% pre-reorder/pre-few-shot. Diagnosis of the 40 wrong rows: the LOC_IDIOM few-shot examples added the prior session are a **mixed result** — LOC_IDIOM recall jumped 66.7%→86.7% (genuinely catches more real idioms) but precision dropped 66.7%→56.5% (false positives doubled 5→10). All 10 false positives read in full context, clustering into 4 clean patterns:
- (A) fixed animal-expression attributing a trait to a person should be META_ATTR not LOC_IDIOM (brebis égarée ×2, faire les ânes)
- (B) compound color idiom should be COUL not LOC_IDIOM (poivre et sel ×2)
- (C) live "comme" simile where animal still evokes real action should stay COMME_SN, not LOC_IDIOM (tirer comme des lièvres, tomber comme des mouches — flagged before the few-shot fix, persisted through it)
- (D) representation/symbol context should be IMAG (eau de rose re: photos, fleurs de lis on a flag)

**Root cause**: LOC_IDIOM is question 1 in the decision tree (checked before COUL/IMAG/COMP_DEG/COMME_SN/META_ATTR), so the model locks in LOC_IDIOM before reaching the more-specific correct question. **Fix applied**: explicit 4-case exclusion clause added to question 1, redirecting each pattern to the correct question number.

### v6 confusion-matrix breakdown (pre-META_JUXT-fix, 69.3% baseline)
- Worst: META_FILEE 0/3, DE_PROP 0/2, META_VERB 40%(2/5), COMME_SI 50%(2/4), COMME_P 50%(2/4)
- Mid: IMAG 57%(4/7), META_APP 57%(4/7), META_ATTR 60%(12/20)
- Best: COMME_SN 83%(20/24), LOC_IDIOM 87%(13/15), DE_PARANGON 100%(7/7), COUL 100%(6/6)
- Top confusion pairs: META_ATTR→LOC_IDIOM (4, biggest single leak — surnommage misread as frozen idiom); DE_PARANGON as a false-positive sink pulling in DE_PROP(2)/META_APP(2)/COMME_SN(2), including COMME_SN cases with an explicit "comme" the model should have caught earlier (evidence the model doesn't reliably respect prompted sequential ordering).

### Root-cause replay finding — DE_PARANGON vs DE_PROP ambiguity is a real schema gap, not fixable by prompting
Replayed id=32 (guimauve, "mes poings de guimauve", gold=DE_PROP) directly against the raw model call. Model's actual output: `{"code": "DE_PARANGON", "raison": "Structure 'N1 de N2' illustrant une qualité (douceur) via un exemplaire (guimauve), comme 'mémoire d'éléphant'."}` — a **coherent, well-reasoned** parse, not a bug. "Poings de guimauve" genuinely structurally resembles "mémoire d'éléphant" (DE_PARANGON's own canonical example), but DE_PROP's defined pattern ("vautours de la finance," a domain-membership label for people) doesn't obviously fit either (a body part described via a soft material, not a person categorized by domain). **Conclusion: genuine ambiguity in how the schema definitions cover this construction, not something more few-shot examples can patch.** Recommended (not yet done): send Riccardo 2-3 concrete boundary cases (guimauve, plus perroquet/chevreuil META_APP↔DE_PARANGON) for a ruling.

### Model comparison — qwen2.5:7b confirmed too weak
Built `test_task2_qwen25_7b.py`, ran the 20-row targeted batch used for the v6 fix test. **Result: 4/20 = 20.0%**, severe failure mode — predicted **LOC_IDIOM on 18 of 20 rows** regardless of content, i.e. not following the 14-step decision tree at all, just pattern-matching to the first plausible category. Fast (2.9s/row vs qwen3's ~40s/row) but irrelevant. Confirms qwen3:30b remains the only viable local option, now with fresh data rather than a recalled judgment. Installed models: `qwen3:30b`, `qwen2.5:7b`, `qwen72b-limited` (Qwen2.5-VL 73B), `qwen2.5vl:72b` — both 72B options ruled out (48GB quantized on 46GB GPU, only 20 layers on GPU per `ollama show`, vision-language models not suited to text classification).

### Riccardo's answer, pending
The 2026-07-09 email round asked Riccardo about DE_PARANGON vs DE_PROP vs META_APP boundary cases (guimauve/"poings de guimauve", raisins/"raisins de la domination" — both gold=DE_PROP but structurally parse like DE_PARANGON; perroquet, chevreuil). He replied he needs to check his own references, promised an answer "first thing tomorrow" (2026-07-11) — **not confirmed received as of the last session logged.**

### Standing constraint on prompt examples (queued next step)
Any future few-shot examples for Task 2's remaining confusion pairs (META_ATTR↔LOC_IDIOM 4 errors; DE_PARANGON as false-positive sink for DE_PROP/META_APP/COMME_SN, 6 errors) must be **hand-written/generic, never pulled from the gold CSV or real corpus novels** — standing rule from Task 0/1 to avoid overfitting the prompt to the eval set, reconfirmed explicitly for Task 2.

### Current state at GPU freeze
Paused mid-run at 43/114 rows (few-shot version). Early signal weak/flat (69.8-74.2%), not clearly above the 73.7% META_JUXT-only baseline. **80% is the bar to scale to the full corpus — never hit.** Labiba's assessment: the DE_PARANGON/DE_PROP ambiguity likely needs Riccardo's input more than further prompt tuning.

---

<a id="task-3"></a>
## 6. Task 3 — Agentivity Analysis

### What it is
Research hypothesis: *are animals and plants more passive agents compared to humans in contemporary French novels?* Classifies every animal/plant/human entity mention by syntactic role via spaCy dependency parsing — **does NOT use qwen3/the LLM at all**, zero GPU contention with Tasks 0/1/2/4.5, safe to work on during any GPU freeze.

### Method
Uses dependency files (`dépendants_*.csv`, columns: `fichier | token_lexique | truncated_sentence | lemme | categorie | tête | dépendants | tête_de_tête`). The `tête` column holds the syntactic head + dependency relation. Role classification:
- **Active agent** → `nsubj`, `ROOT`, `obl:agent`
- **Passive receiver** → `nsubj:pass`
- **Object** → `obj`
- **Noun complement** → `nmod`
- **Other** → everything else

### Original build (June 2026, `task3_full_report.md`, June 22)
Pre-existing files from the previous team: `dépendants_ANIMAUX.csv` (126,201 rows, all), `dépendants_PLANTES.csv` (68,920, all), `dépendants_animaux_référentiels.csv` (106,410, referential-only, manually filtered by the previous team). `analyse_dependances.py` had two blocking bugs (missing `seaborn`, Polars API incompatibility with UDFs) — rewritten as `analyse_agentivite.py`, processing rows one-by-one to avoid the Polars UDF issue, producing identical results without errors.

**Original referential-animals results (95,243 valid occurrences)**:
| Category | N | % |
|---|---|---|
| Noun complement | 31,982 | 33.6% |
| Active agent | 23,265 | 24.4% |
| Other | 20,040 | 21.0% |
| Object | 19,247 | 20.2% |
| Passive receiver | 709 | 0.7% |

**Original plants results (64,269, mixed fig+ref — no referential filter existed yet)**:
| Category | N | % |
|---|---|---|
| Noun complement | 31,815 | 49.5% |
| Other | 14,878 | 23.1% |
| Object | 9,727 | 15.1% |
| Active agent | 7,591 | 11.8% |
| Passive receiver | 258 | 0.4% |

Contamination found by manual example check: "La moutarde me monte au nez" (idiom, getting angry — not a real plant), "Schulmann m'a tendu une carotte" (idiom, dangling a carrot), "Le petit pruneau ne comprend pas" ("pruneau" = slang for a person). Filtering deferred at the time — Task 1 wasn't finished (~44h/~80h compute estimated for plants/animals respectively).

### Human pipeline (new work by this project, June 2026)
Previous team never analyzed humans. Built `extract_humains.py` using spaCy NER (`fr_core_news_lg`): detects character names (PER entities), extracts syntactic role, detects gender via morphology + contextual pronouns, filters false positives (publisher/author names). Runtime: 45.5 min for all 925 novels. Output: `dépendants_HUMAINS.csv`, 219,651 mentions.

**Humans results (219,651 occurrences)**:
| Category | N | % |
|---|---|---|
| Active agent | 81,755 | 37.2% |
| Other | 62,395 | 28.4% |
| Noun complement | 44,184 | 20.1% |
| Object | 28,214 | 12.8% |
| Passive receiver | 3,103 | 1.4% |

**Gender breakdown**: Masculine 118,142 (53.8%), 38.2% active agent; Feminine 44,529 (20.3%), 37.7% active agent; Undetermined 56,980 (25.9%) — no nearby pronoun, ambiguous French names (Claude/Alex/Dominique), foreign names, surname-only. Not a bug, reflects genuine textual uncertainty.

### Original confirmed hierarchy (Riccardo-approved, June 25 meeting)
| Category | N | Active Agent | Passive | Object | Noun Complement | Other |
|---|---|---|---|---|---|---|
| HUMANS (all) | 219,651 | 37.2% | 1.4% | 12.8% | 20.1% | ~28.4% |
| Humans masculine | 118,142 | 38.2% | 1.3% | 13.2% | 18.8% | — |
| Humans feminine | 44,529 | 37.7% | 1.8% | 12.9% | 21.2% | — |
| ANIMALS (referential) | 95,243 | 24.4% | 0.7% | 20.2% | 33.6% | ~21.0% |
| PLANTS (all, mixed) | 64,269 | 11.8% | 0.4% | 15.1% | 49.5% | ~23.1% |

**Hierarchy confirmed: Humans (37.2%) > Animals (24.4%, 1.5× less) > Plants (11.8%, 3× less)** as active agents. Plants used predominantly as noun complements (describe things rather than do things). Male/female difference minimal (38.2% vs 37.7%).

**Riccardo-verified lion examples**: "Julien tua le lion" → lion is direct Object; "Le lion fut tué par Julien" → lion is Passive (nsubj:pass); "Le lion mangea Julien" → lion is Active agent (subject of active verb); "Julien fut mangé par le lion" → lion is **Active agent** (oblique agent `obl:agent` of the passive — the lion IS doing the action even in a passive sentence).

**Why percentages don't sum to 100%**: the "Other" column (~21-28%) = syntactic relations not fitting the 4 main categories (prepositional phrases, appositions, existential constructions like "il y a des lions").

### Animal-side refresh (completed 2026-07-08)
This was the "Animal re-filtering" item from `task3_full_report.md`'s Known Limitations. Full method/numbers written into `task3_full_report.md` under "UPDATE — 2026-07-08" and `CLAUDE.md`.

- **Bug found first**: a stdlib-`csv`-vs-`polars` parsing bug produced a false result (89.6% "Autre" instead of the correct ~20%) — `dépendants_ANIMAUX.csv` contains Python-tuple-repr strings with embedded quotes that break stdlib `csv`'s quoting rules and silently shift fields. `analyse_agentivite.py` already used polars, matching that fixed it. **General lesson**: any script reading `dépendants_*.csv` must use polars, not stdlib csv.
- **Coverage gap found and closed**: `dépendants_ANIMAUX.csv` (built 2026-05-31, before Task 1 existed) never covered the bestsellers subset at all (13,094 rows) and was short 2,243 rows even within corpus_principal. Closed by re-parsing 14,906 missing rows (`dépendants_ANIMAUX_missing_rows.csv` — corrected 2026-07-11 from a previously-stated 15,337; the actual file has 14,906 rows, and 112,775 [original file] + 14,906 = 127,681, matching the merged `dépendants_ANIMAUX_COMPLET.csv` row count exactly) with `fr_core_news_lg`, reusing head/head-of-head logic from `extract_humains.py` + `scripts/get_token_dependencies.py`. Note: `get_token_dependencies.py` as committed references model `fr_dep_news_trf`, which is **not installed anywhere on this machine** — only `fr_core_news_lg` is; the actual production dependency file was almost certainly built with `fr_core_news_lg`, matching `extract_humains.py`, despite what the script's source says.
- **Final animal numbers**: 23.8% active agent / 0.8% passive / 21.5% object (86,082 référentiel mentions, 96% coverage) — barely moved from the old manual-filter number (24.4%/0.7%/20.2%, N=95,243). Hierarchy Humans > Animals > Plants confirmed, not overturned.
- New files: `dépendants_ANIMAUX_missing_rows.csv`, `dépendants_ANIMAUX_COMPLET.csv` (127,681 rows, merged master), `dépendants_animaux_référentiels_REFRESH.csv` (86,082 rows, final).

### Plants-side refresh (completed 2026-07-10)
Same coverage-gap bug: `dépendants_PLANTES.csv` (May 31, pre-Task-1) missing the entire bestsellers subset (0/87 files) + 2,756 corpus_principal rows. spaCy/`fr_core_news_lg` had vanished from the environment (no venv, packages don't persist) — reinstalled. Re-parsed 7,516 missing rows (`morphosyntaxe/reparse_plantes_missing.py`, new script, same head/head-of-head logic), 99.7% match rate, ~60 rows/sec on CPU. Merged into `dépendants_PLANTES_COMPLET.csv` (71,764 rows). Re-joined against référentiel-only plantes → **97.8% coverage (up from 87.3%)**, final `dépendants_plantes_référentiels_REFRESH.csv` (58,637 rows).

**Task 3 plantes final**: Agent actif 11.1%, Passif 0.4%, Objet 15.4%, Complément 50.8%.

### New unfixed finding — humans has the same bestsellers coverage gap
`dépendants_HUMAINS.csv` (built 2026-06-22) has the **exact same gap for humans, never fixed** — `extract_humains.py`'s `CORPUS_DIR` only points at `CORPUS_TOTAL`, never `CORPUS_Bestsellers` — confirmed 0/88 bestsellers files present. **The headline 37.2% human active-agent number is unverified against ~9% of the corpus.** Not yet fixed as of the last update — obvious next step, same treatment as plantes/animaux.

### Passive-voice contamination bug found (humans, 2026-07-10)
Because Task 3's classification is deterministic (a fixed rule over spaCy's dependency-parse output, not a model prediction), there's no human-annotated gold set to score against — the substitute is a manual spot-check reading 45 randomly sampled rows (3 per category × 5 categories × 3 populations: humains, animaux référentiels, plantes référentiels) against their actual sentence context, checking whether spaCy's syntactic label is semantically sane.

**Spot-check results**:
| Population | Sampled | Clearly correct | Issues found |
|---|---|---|---|
| Humains | 15 | 12 | **3 — a real systematic issue, see below** |
| Animaux référentiels | 15 | 15 | none |
| Plantes référentiels | 15 | 15 | none |

Animaux and plantes came back fully clean — every sampled row (including genuine plant passive constructions like "ce gazon serait... remplacé", "l'orme était désigné", "ce gui est... révélé") matched its sentence correctly.

For humans, all 3 sampled "Récepteur passif" rows (Jésus/blond, Charles/assis, Dan/gêné) are être+adjective predicates, **not real passive voice**. Systematic check confirmed: top head words for all 3,103 human "passive" rows are dominated by être-auxiliary intransitive verbs (morte 63+, assis 100, restée 44, venue/venu 40+35, rentré 39, allée/allé 36+35, revenue 36, entrée 33, né 32, devenue 30) — spaCy's `nsubj:pass` tag fires on subjects of être-auxiliary intransitive verbs (mourir, venir, rester, naître, devenir, entrer, aller...), which are state/movement verbs, not passives. A minority (surpris, arrêté, pris) could be genuine passives. **Likely most of the 1.4% human-passive figure is this parsing artifact, not genuine passive voice.** This wasn't caught in the original 2026-06-22 report (which only spot-checked 3 examples total, none from this category). Confirmed real, needs a morphology/tag-based exclusion fix (checking `token.tag_`/morphology to exclude être-intransitive verbs) before the official 1.4% figure is cited anywhere — **not yet fixed**.

**A second, separate issue** found in the same spot-check: an Objet sample ("Allez les enfants, susurra **Ibrahim Santos**...") shows spaCy mis-tagging a subject-verb inversion after reported speech (very common in French dialogue: "dit-il", "murmura-t-elle") as an object instead of a subject — a known hard case for French dependency parsers. Not worth chasing down for the whole corpus, but the "Objet" numbers likely have some contamination from this pattern too.

### No gold set exists for Task 3 (confirmed, not assumed)
Explicit transcript confirmation (second meeting, ~line 529-530), Riccardo looking at `dépendants_HUMAINS.csv` on screen: *"So you didn't have a gold set for this?" / "No, I made it myself because it didn't give me the gold set for humans and I just ran it."* Searched both full transcripts exhaustively — nothing else references a Task 3 gold set (role classification or names). This specific quote was about the human **names** check only, not active/passive/etc. — re-searched specifically for a role-classification gold set too, found none anywhere (transcripts or filesystem).

### Why a manual spot-check, not a formal gold set, is the correct verification method here
This is a deliberate methodological choice, not a shortcut taken because a gold set was unavailable. Task 3's classification is **deterministic**: a fixed rule mapping spaCy's dependency-parse tags to categories (`nsubj`/`ROOT`/`obl:agent`→Active agent, `nsubj:pass`→Passive, `obj`→Object, `nmod`→Noun complement), not a model making a judgment call under uncertainty. There is no probabilistic behavior to characterize statistically the way Tasks 1, 2, and 4.5 need a large gold set to validate an LLM's calibration across many cases. The only two ways an error can enter this pipeline are (a) spaCy mis-parses a sentence, or (b) the fixed rule maps the wrong tag to the wrong category for some construction — both of which a targeted manual read of real sentences is well-suited to catch, and a large formal gold set would not diagnose any better.

This is also not merely a theoretical justification — the method demonstrably worked in practice. The 45-row spot-check caught a real, previously-missed bug (the humans passive-voice être-auxiliary contamination, §above) that the original 2026-06-22 report's much shallower 3-example check had missed entirely. Animaux and plantes came back 15/15 clean on every sampled category, including correctly-identified genuine plant passive constructions — a clean result across the board, not a lucky partial pass. The headline hierarchy finding (Humans > Animals > Plants as active agents) is independently corroborated: it was approved by Riccardo across two separate meetings, and it held essentially unchanged (24.4%→23.8% for animals) even after the later coverage-gap fixes reprocessed tens of thousands of additional rows — a result that was not cherry-picked or fragile to the specific sample checked.

**Bottom line**: the strategy is correct and appropriately matched to a deterministic task, and the core results (animaux, plantes, and the humans active/object/complement figures) are solid. The two specific caveats that remain open — humans' passive-voice figure likely being contaminated, and the humans bestsellers coverage gap — are not failures of the verification method; they are exactly the kind of narrow, bounded issues this method is designed to surface, and both were found through this project's own auditing rather than missed.

### Human-names multilingual detection (Task 3 extension)
Riccardo asked (both meetings) to extend human-name detection beyond French-only spaCy to catch English/Arabic-origin names, explicitly flagging overfitting risk ("a name called bar in any other language") and separately proposing mid-sentence capitalization as a validation signal. Second meeting: surprised that % undetermined-gender was so high; confirmed plausibly caused by the French-only spaCy model missing Arabic-origin/some English-origin names common in the corpus's many Francophone-Africa/Maghreb-set novels.

Built `morphosyntaxe/extract_humains_multilingual.py`: runs `Davlan/xlm-roberta-base-ner-hrl` (multilingual NER, CPU-only, confirmed zero GPU usage) alongside the French spaCy pass, keeping only new PER candidates the French model missed, gated by several guards. Bugs found and fixed via direct output inspection (do not trust a "looks like it worked" run without checking actual extracted names):

1. **Subword-splitting bug**: XLM-R's tokenizer sometimes splits one name into two adjacent PER spans with zero gap ("Émile"→"É"+"mile", "Théodore"→"Th"+"éodore"). Fix: merge consecutive PER spans with exactly zero character gap.
2. **One-sided truncation**: some names had only half tagged as PER at all (e.g. "Mauny"→only "ny" survived, "Lippmann"→only "pmann"). Fix: extend any span backward/forward to the nearest word boundary regardless of what the model tagged the rest as.
3. **Animal/plant false positives**: 'Ours' (=bear) tagged as PERSON — a real risk in this corpus. Fix: cross-check every multilingual-only candidate against `lexiques/ANIMAUX.txt`/`PLANTES.txt`, including spaCy lemma + cheap French gender-variant stripping (catches "Ourse"→"ours", "chatte"→"chat").
4. **Place-name false positives**: 'Sables' (likely Sables-d'Olonne) passed every filter since it's a genuine, consistently-capitalized proper noun. Fix: cross-check against every LOC entity the French spaCy model already tags in the same novel.
5. A **5th guard**, `is_known_org` (checks against ORG entities like band names), was found already present in the code on re-verification (2026-07-08) but not previously documented in `CLAUDE.md`'s "four fixes" writeup.

**5-novel test, re-verified 2026-07-08** (using the correct `labelimg_env` python after an initial failed attempt with plain `python3` due to missing spacy/transformers): reproducible, 897 total rows (fr_model=811, multilingual_model=86 new names) — confirms the fixes are stable, not a fluke.

**Full 925-novel run** started 2026-07-08 (no new filters, per explicit call — Labiba noted "Barbie"/"Petit Prince" flagged as residual gaps might actually be legitimate character names, not false positives), ETA ~33h on CPU (GPU would likely be much faster but wasn't tested — a decision point never made).

**Known residual gap, not fixed**: cultural/generic-word false positives that are neither animal/plant terms nor places (Nirvana, Petit Prince, Barbie) need human/gold-set judgment — no automated filter can safely resolve these. Confirmed still only 72/925 novels done (7.8%) as of 2026-07-10, **paused, not resumed**. The 533 unique multilingual-only names from that partial run were pulled and additional concrete false-positive examples found: common nouns (Tordu, Mauvais, Cicatrice, Dieu), fictional characters (Tintin, Yoda, Don Quichotte), brand/org names (Chanel, Tsahal, Libé), tokenization artifacts (hyphenation breaks).

**Full-corpus cost estimate**: ~130s/novel on CPU → ~33h for all 925 novels.

### Pending Riccardo-requested item — DONE (2026-07-11): false-positive rate estimate for the multilingual partial run

Estimated the % of false-positive names among the 533 unique names the multilingual-only pass added in the 72-novel partial run (`dépendants_HUMAINS_multilingual.csv`, confirmed to cover exactly 72 novels, 18,083 rows: 16,676 fr_model + 1,407 multilingual_model). No gold set exists for this, so this is explicitly an **estimate, not ground truth** — built via `morphosyntaxe/estimate_multilingual_false_positives.py`, runs entirely on CPU (no GPU, no Ollama/LLM call — just Python + regex against a manually-verified lookup table).

**Methodology note, kept here for transparency**: the first version of this script used an automated heuristic (lowercase each name, re-run it through spaCy in its real sentence, check the POS tag). That heuristic turned out to be unreliable on manual review — it wrongly flagged genuine foreign/rare names (Abdelkader, Anissa, Azzouze, Ourida, Wafaa, Soraya...) as "common nouns," because spaCy's French model doesn't recognize unfamiliar names and mis-tags them once decapitalized — exactly the names this multilingual pass exists to catch. That version was discarded. The numbers below come from a corrected approach: every one of the ~533 names was checked by hand against its real sentence context (not pattern-matched or guessed), across three successive correction passes as more misclassifications were caught by manual spot-checking (e.g. "Nirvana" and "Queen" are band names, not people; "Sioux" here is the fixed idiom "ruses de Sioux" = cunning tricks, not a person reference).

**Results — by unique name (533 = 100%):**

| Category | Count | % |
|---|---|---|
| Plausible real name | 416 | 78.0% |
| Fictional/mythological character | 42 | 7.9% |
| Common noun/title (confirmed) | 28 | 5.3% |
| Brand/organization/artwork | 18 | 3.4% |
| Ambiguous — reads as a nickname | 16 | 3.0% |
| Fragment, too short to judge | 9 | 1.7% |
| Place name | 3 | 0.6% |
| Tokenization artifact | 1 | 0.2% |

**Results — by total occurrences (1,407 = 100%)**, which matters because a few false positives repeat constantly (esp. "Dieu"):

| Category | Count | % |
|---|---|---|
| Plausible real name | 1,030 | 73.2% |
| Common noun/title (confirmed) | 217 | 15.4% |
| Fictional/mythological character | 59 | 4.2% |
| Fragment, too short to judge | 40 | 2.8% |
| Ambiguous — reads as a nickname | 35 | 2.5% |
| Brand/organization/artwork | 21 | 1.5% |
| Place name | 4 | 0.3% |
| Tokenization artifact | 1 | 0.1% |

**Bottom line**: roughly 73–78% of what the multilingual pass added are genuinely real name references (including real historical/celebrity figures like Belmondo, Beyoncé, Pablo Picasso — counted as legitimately human). Roughly 22–27% are some kind of false positive, dominated by common nouns/titles — mainly "Dieu" (177 occurrences alone, 12.6% of all 1,407 multilingual-only occurrences by itself, sample-verified across 6+ sentences to always mean "God," never a name) — then fictional characters, then brands.

**Examples per category** (name, occurrence count):

| Category | Examples |
|---|---|
| Plausible real name | Pierre (141×), Nicolas (67×), Christine (52×), Liza (52×), Sarah (32×), Nadia (24×), Manon (12×), Grenier (8×) — plus real historical/celebrity references (Belmondo, Beyoncé, Pablo Picasso, Da Vinci) |
| Fictional/mythological character | Betty Boop (5×), Barbie (3×), Don Quichotte (3×), Highlander (3×), Robinson Crusoé (3×), Dracula (2×), Gargantua (2×), Jiminy Cricket (2×), Lolita (2×), Phèdre (2×), Bovary, Caliban |
| Common noun/title (confirmed) | Dieu = "God" (177×), Seigneur = "Lord" (7×), Sioux — idiom "ruses de Sioux" = cunning tricks (3×), Ancêtre = "the Ancestor" (2×), Mademoiselle, Maître = "the Master" (title), Messie = "Messiah", Paléontologue = "paleontologist" |
| Brand/organization/artwork | Nirvana (3×, the band), Buitoni (pasta brand), Armani, Chanel, Goldwyn Mayer (film studio), Libé (shorthand for Libération newspaper), Mein Kampf (book title), Metallica, N.W.A, Pietà (the artwork), Prefab Sprout (band), Prozac |
| Ambiguous — reads as a nickname | Silence (14×), Pilote = "Pilot" as callsign/nickname (4×), Miroir — "M. Miroir," explicitly a character's nickname (2×), Nobel — likely "prix Nobel" the award, not a person (2×), Cicatrice = "Scar" as nickname, Divine, Empereur = likely a title for a historical figure, Faucheuse = "the Reaper" |
| Fragment, too short to judge | Ed (11×), Mi (11×), L. (8×), M. (4×), Mo, Hi, L…, PJ, Ti |
| Place name | Vichy (2×, town/WWII regime), Angleterre = "England", Sotchi = "Sochi" |
| Tokenization artifact | "Ra-  chid Hchicha" — a real name ("Rachid Hchicha") split across an unrejoined line-break hyphenation |

**Note to Riccardo**: I'm leaving it to Riccardo to tell us what he thinks of these results — in particular whether a ~22–27% false-positive rate on the multilingual-only additions is acceptable to move forward with (given the multilingual pass still nets 416+ plausible real names, many of them Arabic/foreign-origin names the French-only model would have missed entirely), or whether the common-noun/fictional-character contamination (especially the "Dieu" pattern) needs a filtering pass before the full 925-novel run is resumed.

### Where the Task 3 files live
**Scripts:**
- `morphosyntaxe/extract_humains.py` — French-only human extraction (production, 925 novels — but see the bestsellers gap above)
- `morphosyntaxe/extract_humains_multilingual.py` — multilingual extension (in progress, 72/925 novels)
- `morphosyntaxe/analyse_agentivite.py` — agentivity classifier (animaux + plantes)
- `scripts/get_token_dependencies.py` — original single-purpose dependency-parse script
- `morphosyntaxe/reparse_plantes_missing.py` — re-parses the plantes coverage gap

**Data — humans:**
- `morphosyntaxe/dépendants_HUMAINS.csv` — 219,651 rows, French-only, missing all 88 bestsellers novels
- `morphosyntaxe/dépendants_HUMAINS_multilingual.csv` — 18,083 rows, partial (72/925 novels only)

**Data — animals:**
- `morphosyntaxe/dépendants_animaux_référentiels_REFRESH.csv` — 86,082 rows, final, coverage-refreshed 2026-07-08

**Data — plants:**
- `morphosyntaxe/dépendants_PLANTES_missing_rows.csv` — 7,516 re-parsed rows (bestsellers + corpus_principal gap), 99.7% match rate
- `morphosyntaxe/dépendants_PLANTES_COMPLET.csv` — 71,764 rows, merged (original + re-parsed)
- `morphosyntaxe/dépendants_plantes_référentiels_REFRESH.csv` — 58,637 rows, final, référentiel-only, 97.8% coverage

### Task 3 — current state and full open-items list
Core findings solid and Riccardo-approved. No GPU dependency — fully workable during the GPU freeze. Open/unfixed items:
- **Humans' "Récepteur passif" (1.4%)** is likely mostly être-auxiliary/adjectival-predicate contamination, not real passive voice — needs a morphology-based fix before being cited anywhere official.
- **Humans bestsellers coverage gap**, mirroring the animaux/plantes gap, never fixed — `dépendants_HUMAINS.csv` has 0/88 bestsellers novels; the headline 37.2% active-agent figure is unverified against ~9% of the corpus.
- **Multilingual name run is 7.8% done, not resumed** — full run is ~33-52h CPU time (estimates vary), zero GPU contention, can run alongside any GPU work; decision on resuming not yet made.
- **Fictional-character names** (Tintin, Yoda, Don Quichotte, Minotaure, Schtroumpf Grognon) are currently being counted as "human" by the multilingual pipeline — worth asking Riccardo whether that's intended, since they're clearly intentional literary references, not extraction noise.
- **No formal accuracy number exists for the multilingual pipeline** — only qualitative bug-fixing via manual inspection (the 4 fixes above). A defensible accuracy claim would need a small hand-annotated sample.
- **Tokenization artifacts** from line-break hyphenation not being rejoined (e.g. "Ra- chid Hchicha", "Veil-lette") also pollute the multilingual-only name list — no safe automated fix identified.

**New Task 2 / Task 4.5 gold set already shared with Riccardo** (2026-07-11): `métaphore/gold_task2_task45_FINAL.csv`, 200 rows (100 animaux + 100 plantes), drawn from this project's own corrected Task 1 output and manually verified row-by-row to be genuinely figurative. Waiting on his annotation.

---

<a id="task-45"></a>
## 7. Task 4.5 — Compare-Target Classification

### What it is
For each figurative mention, classifies WHAT the animal/plant is being compared TO — 6 categories: **CH** (corps humain), **P** (psychologique), **NH** (non-humain vivant), **O** (objet), **E** (élément naturel), **A** (abstrait). Terminology: comparant = vehicle = the animal (the "lion" in "Paul est fort comme un lion"); comparé = tenor/target = what's being compared (Paul in that example). Can only run after Task 1 (needs figurative-only cases). Same 200-item gold set as Task 2 (Riccardo annotated both on one sheet to save time).

### Category definitions (received 2026-07-08, `métaphore/Catégories analyse comparés.docx`)
- **O** — Objets et structures artificiels (man-made objects/technological artifacts)
- **NH** — Créatures non humaines vivantes et processus biologiques (animals, plants, biological processes in non-human living things)
- **E** — Éléments naturels inanimés et processus naturels (landscapes, geological formations, weather, non-living natural world)
- **CH** — Corps humain et processus biologiques (human body, physiological functions, biological processes)
- **A** — Concepts abstraits (politics, religion, art, social institutions like marriage)
- **P** — États psychologiques et fonctions cognitives (emotions, sensations, memory, imagination)

Before this, no processing script and no written definitions existed anywhere — only Riccardo's verbal description from the first meeting.

### Academic source of the 6-category typology — Caracciolo (2021), previously unattributed in this project's own records
The O/NH/E/CH/A/P typology traces to **Marco Caracciolo, *Narrating the Mesh: Form and Story in the Anthropocene*, University of Virginia Press, 2021** — found in `old_report_to_add.md`, not previously cited anywhere else in this project's documentation despite the categories being used throughout Task 4.5. Caracciolo's own category definitions (slightly fuller wording than Riccardo's verbal/`.docx` versions above, functionally the same categories): **O** — objects and artificial structures (man-made artefacts, technology); **NH** — non-human living creatures and biological processes; **E** — inanimate natural elements and natural processes (landscapes, geology, weather); **CH** — human body and biological processes occurring in the human body; **A** — abstract concepts, social practices and institutions (politics, religion, marriage); **P** — psychological states and cognitive functions (emotions, memory, imagination). Worth citing explicitly in the paper as the theoretical source, rather than presenting the 6 categories as if this project invented them.

### Johanna's prior Task 4.5 work (comparé classification) — exact method, for comparison
File: `métaphore/RESULTAT_typologie_compare_animaux.csv` — animals only, done with GPT-4 (not this project's qwen3 pipeline). **Johanna's headline result, worth citing since it's a direct predecessor finding**: 73% of figurative animal comparés involve the human body/attitude (CH category) — i.e. animality in this corpus mostly serves to define humanity, not the reverse. Then Objects (8%), Abstract concepts (6.2%). This 73%-CH finding is also cited in Riccardo's own published paper (see below) as one of the project's headline results, predating this project's Task 4.5 rework — worth checking whether the reworked pipeline's own category distribution (once run at scale) still shows a similar CH-dominant pattern, as a sanity check against Johanna's earlier finding.

Johanna's exact prompt architecture: XML-tagged (`<phrase>`, `<comparant>`, `<reponse>`, `<analyse>`, `<compare>`, `<label>`), with the comparant explicitly pre-tagged in the input sentence (e.g. `<comparant>lion</comparant>`) so the model only had to identify the comparé and its category, not also re-detect the vehicle. Worked examples given to the model: tortue→O (a ship), lion→CH (implicit human), moule→O (a building). Temperature 0.1-0.2, batched by novel file (`partition_by(by="fichier")`), parsed via regex on the `<label>` XML tag. An extra **X** category was used for "context insufficient to determine comparé" or "comparant is not actually being used as an animal" — this project's own 6-category scheme (CH/P/NH/O/E/A) does not currently have an equivalent catch-all category, which may be worth reconsidering given how often "insufficient context" comes up in this project's own confusion-matrix diagnoses (see below). Models Johanna tested for this specific sub-task: `gpt-4o-mini` (main production), `o3-mini` (reasoning model, single-example tests only), `gpt-4.1-nano` (cheaper alternative), `gpt-4.1-mini` (used for régime narratif and temporalité in her Task 0 work, not Task 4.5 specifically).

### THE major reframe — categories = target's ontological entity type, not the trait's semantic domain
**This is a standing rule from Riccardo (email, 2026-07-10), not a one-off tiebreaker — do not re-litigate against it.**

The six categories classify **what kind of entity the metaphor's target (comparé) actually is**, not what quality/trait the comparison illustrates. Riccardo's example: *"Je bats lâchement en retraite... comme un rat"* — target = "il" (a person) → **CH**, regardless of the fact that the illustrated trait (cowardice) is psychological. Contrast: *"Mes émotions se cachaient comme des rats"* → target = "mes émotions" → **P**. *"L'île ressemblait à un rat"* → target = "l'île" → **E**. Same vehicle, same rough action, different category purely by what the target *is*.

**This overturned an earlier same-day fix** (the CH/P "Piège fréquent" prompt patch telling the model "personality traits → P, not CH"), which was built on the wrong theory and is the likely explanation for that fix's accuracy regression (77.9%→68.3% on the 104-row gold set). It also means a batch of "gold mislabel" candidates found earlier the same session (12+ CH rows with personality-trait fondement) were **not errors at all** — gold was right, the category's meaning was misunderstood.

### Update — the rule is more nuanced than "target=person → always CH"
Implementing the rule verbatim still produced 7 wrong predictions (all CH-predicted-but-gold-P, all person-referent rows: jument/elle, singe/elle, ânes/ils, porc/tu, aigle/"Henri Beyle", chacal/"Pierre Castaneda", citrouille/"Max"). Riccardo's clarification, sent these exact contrastive examples:

> "It is a little more complicated than that. In these cases it depends if the pronoun is referring to the physical dimension of the person or to the psychological one. In the case of the rats, I judged that the fact of 'battre en retraite' was bound to the physical dimension of the body, the way the body moved — even if I guess you can consider otherwise. In the case Pierre Castaneda for instance I judge that the referent was not the body of Castaneda, but his behavior, so P."

So **when the cible is a person, there is a second-level split**: physical/bodily dimension (body itself, physical movement/action, physiological process) → **CH**; psychological/behavioral dimension (character, conduct, moral/personality trait) → **P**. A genuinely fine distinction Riccardo acknowledges is itself judgment-call-dependent.

He also clarified a second case, the fougère row ("...apparenté en mon penser au lycopode, à la fougère", gold=CH): the cible is **not** "mon penser" taken literally — "you have to extend the sentence" to find the real referent, which (given the fuller context: narrator lying immobile, "en parfait état de légumerie") is his **physical body**, lying vegetative/inert. Always check whether the wider sentence/paragraph reveals a different true referent, especially a physical body described via a mental-sounding turn of phrase.

**File status**: `comparison/run_task45_compare_category.py` is **frozen** at its known-good, tested 85/104=81.7% state (entity-type + bucket-1/2 + few-shot-examples version, no physical/psychological split) — per explicit instruction, not to be edited further. The physical/psychological refinement was implemented in a **new sibling file**, `comparison/run_task45_compare_category_v2_physical_psych.py` (own output `resultats_task45_compare_category_v2_physical_psych.csv`), so it won't clobber the frozen 81.7% result. **Never tested — GPU freeze began the same day.**

### Version-by-version accuracy history
| Version | Result | N | What changed |
|---|---|---|---|
| Original (pre-fix) | ~30% | — | Pre tenor/vehicle rewrite |
| Tenor/vehicle prompt rewrite (method basis: [tenor-vehicle-ground extraction, arxiv 2010.05633](https://arxiv.org/abs/2010.05633) — validate via the shared "ground" property before classifying) | 63.5% (66/104) | 104 | First substantial jump |
| CMT (Conceptual Metaphor Theory) sequential-question redesign — vehicule→cible→fondement_commun→verification→code, based on arxiv 2502.01901 (claimed F1 82.59 on a comparable task) | **39.4% (41/104) — a regression from 63.5%** | 104 | Contradicted the literature's finding for this setup |
| (Root cause diagnosed) qwen3 truncation bug | 46% (48/104) UNKNOWN rows | — | `num_predict=3000` too low for the 5-step chain; the CMT technique itself was never actually tested until fixed |
| Truncation fix (`num_predict`→8000, `context[:300]` removed) + explicit CH/P/A disambiguation clause | **77.9% (81/104)** | 104 | Real, confirmed win — resumed from 10/104 |
| First CH/P "Piège fréquent" patches (added 2026-07-10, before the entity-type reframe) | Not separately isolated — later found still live and never fully implemented; contributed to a since-corrected 68.3% regression reading | — | Built on wrong theory (personality→P not CH), overturned by Riccardo's reframe |
| Entity-type rewrite (first round) | **78.8% (82/104)** | 104 | Cible = literal referent; classify referent's entity type only, fondement_commun not used to pick category |
| Bucket-1/2 fixes (voice/chant misattribution to CH fixed; cible-extraction-too-literal-on-idioms fixed) | 6/7 fixed on smoke test, full rerun launched | 112 | See buckets below |
| Few-shot examples added on top of bucket-fix (mixed methodology in one file — flagged) | **85/104 = 81.7% (final)** | 104 | Best result of the project |

### Confusion-matrix diagnosis of the 78.8% run — 3 buckets
Per-category: CH 93.1%(67/72), O 85.7%(6/7), E 75%(3/4), A 45.5%(5/11), **P 10%(1/10)**.

1. **Bug introduced by this project, fixed same session**: an added prompt example "voice/chant attributed to a person → CH" was wrong, caused 2 real errors (id=45 gnous/"le chant va déferler" gold=A; id=121 guimauve/"une voix... annonça" gold=A) — both have the voice/chant itself as grammatical subject, not a person. Fix: removed the bad example, added guidance distinguishing "voice is the subject → A" from "person is subject, voice is a detail → CH".
2. **Cible-extraction too literal on idioms/rhetoric, fixed same session**: ids 23 (porc — real cible "la beauté," abstract aesthetics, model anchored on pronoun "elle"), 75 (chèvre — "ménager la chèvre et le chou" fixed idiom, should resolve to abstract compromise/indecision), 81 (mouton/carpe — rhetorical list of incompatible pairs, cible = abstract notion of difference), 135 (loup/chemin — poetic reading-sensation description, **still unfixed** after this round), 169 (chien/"être composite" — describes a person's grotesque appearance, cible=that person=CH, model took the composite-creature description literally as NH). Guidance added: identify what the sentence is REALLY about before taking the nearest noun literally.
3. **Genuine gold P/CH contradiction — NOT fixable by prompting, needs Riccardo's ruling**: 8/10 P-category errors have an explicit human referent with a psychological/behavioral fondement — structurally identical to Riccardo's rat/il/CH example, yet gold=P (ids 67 jument, 68 singe, 123 ânes, 172 porc, 173 aigle, 186 chacal). Exact opposite contradiction also exists: id=91 fougère reads as textbook P (cognitive faculty as cible) yet gold=**CH**. Also id=17 citrouille (self-image/status delusion, arguably P not A). This is what triggered the physical/psychological second-level split Riccardo later provided.

Bucket 1+2 fix smoke-tested on 7 affected rows: **6/7 fixed** (only id=135/loup, the hardest/most poetic case, still wrong). No regressions. Old 78.8% backed up to `resultats_task45_compare_category_PRE_BUCKETFIX_20260710.csv`.

### Few-shot round (45-minute sprint, 2026-07-10 evening)
One invented (never-gold-set) contrastive example per category (CH/P/NH/O/E/A) added directly after the category list — e.g. "Pierre courait comme un lièvre, le souffle court" → CH (person target); "Sa jalousie rôdait comme un loup affamé" → P (emotion is its own grammatical subject); "Le mariage, cette cage dorée, l'étouffait" → A (institution). Applied on top of the already-mid-run bucket-fix (which was at 20/112, 85% on those rows) via the script's built-in `--resume` done-id skip — **this deliberately mixes two methodologies in one output file** (first 20 rows bucket-fix-only, rest bucket-fix+few-shot), a speed tradeoff under a 45-minute GPU-window constraint, flagged explicitly in case the final number looks anomalous (check for a discontinuity at row 20). **Final: 85/104 = 81.7%** — best result of the project for this task.

### Post-hoc analysis of the 81.7% result — 4 more error buckets found, not fixed
Bucket 2 (voice/chant→A fix over-firing on bodily-effect passages), Bucket 3 (missed idioms like "sa pomme"/"les chiens ne font pas des chats"), Bucket 4 (genuinely ambiguous E/O/A boundary cases). **Not yet addressed.**

### Structural gold-set gap
**Zero NH (non-human living-thing target) examples across all 200 gold rows** (`categorie_compare` distribution: 72 CH / 11 A / 10 P / 7 O / 4 E / 0 NH) — any future NH accuracy claim cannot be validated against this gold set as-is. Flagged as a requirement for the next gold-set redraw (ask Riccardo to ensure NH coverage).

### Other flagged individual mislabel candidates (lower priority, unresolved)
"ver luisant"/mamelon arguably CH not E; "myrtilles"/béton-stain arguably O not E — about the physical-object-vs-natural-element boundary, not affected by the CH/P reframe, still worth Riccardo's eyes.

### Current state at GPU freeze
`run_task45_compare_category.py` (v1, frozen) at **85/104 = 81.7%**, best-of-project. `run_task45_compare_category_v2_physical_psych.py` (untested physical/psychological split) built but never run — **first thing to validate once GPU access returns.**

---

<a id="task-5"></a>
## 8. Task 5 — Deployable Front-End (deprioritized)

A deployable front-end system + external novel database. **Explicitly deprioritized by Riccardo in both meetings** — "too much of a stretch." Joanna already built the entity-extraction pipeline underlying it; no further work planned. Note: "Task 4" (singular, no ".5") is not a real separate task — confirmed by search, it's just an old name for Task 0/narratology used once in `task1_report.md`.

---

<a id="biodiversity-indices"></a>
## 9. Biodiversity Indices (new, self-directed by Riccardo)

Shannon index already implemented by Joanna (`scripts/shannon_rarefied.py`, visualized in `visualisations/Indice_Shannon.png`). Riccardo met a biologist/statistician expert in biodiversity measurement who suggested applying additional ecological indices to the textual corpus (e.g. equitability index and others) — purely statistical formulas applied to entity count distributions, not AI/LLM work. Riccardo received slides/documents from this expert but hadn't studied them as of the second meeting. Framed as **his own side-exploration** for theoretical interest ("I think I can do it myself... it's just applying new calculation to data we already have"), not a hard ask of Labiba, though he left the door open ("let me know if you cannot do it"). Theoretical interest: comparing ecologists' methodology with what's possible in digital humanities. **No further work logged on this by Labiba's side as of the last session.**

**Important theoretical clarification Riccardo gave** (from `old_report_to_add.md`, not previously captured elsewhere): Shannon here "measures a probabilistic information structure, not an ontological quality of living things. We are not measuring a biological ecosystem but the informational organisation of a living lexicon in a text." Worth keeping this framing explicit in any paper section discussing the index, since it heads off the misreading that the project is claiming to measure real ecological biodiversity rather than its textual/lexical representation.

**Specific additional indices named as candidates** (documents still pending from Riccardo's biologist contact as of the last update — none of these have been implemented):
- **Pielou's equitability index** (J = H / ln(S), where S = number of species) — normalizes Shannon's H by the maximum possible diversity for that many species, isolating "evenness" from raw richness.
- **Simpson's index** (1 − Σpᵢ²) — the probability that two randomly-picked individual mentions belong to different species; a different weighting of the same richness/evenness tradeoff Shannon captures, more sensitive to dominant species than to rare ones.
- **Chao1 estimator** — estimates the *true* species richness of a corpus/novel from observed data, correcting for species present in reality but never sampled/mentioned; relevant here because any given novel's text is itself a finite "sample" of the author's full underlying biodiversity vocabulary.
- **Beta diversity** — measures the difference in species composition *between* novels or corpora, rather than within a single one; the only one of these four that would let the project compare corpora (e.g. Prix-Écologie novels vs. the general corpus) rather than just rank individual novels.

All four are described as pure statistical calculations over the existing token-frequency distributions already produced by the Task 1/entity-extraction pipeline — not AI-based, and expected to be comparatively quick to implement once the reference documents are actually reviewed.

---

<a id="dh-humanistica"></a>
## 10. DH Humanistica App (separate side project)

A Streamlit RAG (retrieval-augmented generation) app for digital humanities researchers, separate from the core écopoétique pipeline work, built for "Formation HANDS — Sorbonne Université." Originally named "Ask Labiba," rebranded to "DH Humanistica." Runs on `localhost:8505` via `streamlit run pipeline/ask_labiba.py`.

### Ownership/access model
Source lives at `/home/malrahabi/ragHumanistica/pipeline/ask_labiba.py`, owned by a different Linux account (`malrahabi`), process run as **root**. `lfarooq` has no read/write access and no sudo there. Labiba has sudo under her own `labiba` account on the same box (`obtic-gpu1`) and does all privileged operations herself, pasting terminal output back. Working copy: `/home/lfarooq/ask_labiba.py` (pulled and chowned by `labiba` for direct editing).

### Fixes applied (2026-07-09/10)
1. **Rebrand**: title "Ask Labiba"→"🤖 DH Humanistica", subtitle→"by Obtic · SCAI", Contact section added linking `labibafarooq23@gmail.com`.
2. **Qwen3 30B empty-answer bug — root cause found and fixed.** `call_ollama()` used `num_predict=max_tokens` (sidebar slider default 512). Qwen3 reasons internally before answering and burns the entire budget on reasoning — confirmed live at 512 tokens, `done_reason: "length"`, `response` came back empty. Fixed by flooring `num_predict` to ≥1500 specifically for `qwen3:30b`. **Second layer of the same bug**: even with `"think": false` passed to the Ollama API, Qwen3 still emitted raw reasoning text inline in `response` (sometimes with no opening `<think>` tag, only a stray closing `</think>`) — first fix attempt (regex `<think>.*?</think>` removal) silently failed to match this asymmetric case, letting chain-of-thought leak into the UI. Real fix: `if "</think>" in answer: answer = answer.rsplit("</think>", 1)[1]`. Verified end-to-end against the live server using the actual edited function. Same failure pattern as this project's own Task 2/4.5 qwen3 truncation bug.
3. **Model dropdown trimmed to reality.** Checked the actual Ollama server: only `qwen2.5:7b` and `qwen3:30b` are real working text models; `qwen2.5vl:72b`/`qwen72b-limited` are vision-language variants, not usable as plain-text 72B. No 14B or LLaMA 3.1 model exists on the server. Removed Qwen2.5 14B, Qwen2.5 72B, LLaMA 3.1 8B from both the sidebar list and `call_llm()`'s routing map.
4. **Onboarding wizard modal** — built first in a standalone HTML mockup artifact, later ported into real code (see below).
5. **Light/dark theme inconsistency — found and fixed.** Custom CSS only overrode specific classes; Streamlit's own native chrome (⋮ menu, untouched native widgets) fell back to Streamlit's base theme following "Use system setting," fighting the hardcoded-dark custom elements. Not a client-side bug. Fix: `/home/malrahabi/ragHumanistica/.streamlit/config.toml` with explicit `[theme]` block (`base="dark"`, matching the app palette: `primaryColor="#c9a96e"`, `backgroundColor="#0f1117"`, `secondaryBackgroundColor="#161b27"`, `textColor="#e6edf3"`).

### Deploy procedure (repeatable, established)
1. Edit `/home/lfarooq/ask_labiba.py`.
2. Labiba backs up the live file: `sudo cp .../ask_labiba.py .../ask_labiba_BACKUP_<timestamp>.py`
3. `sudo cp /home/lfarooq/ask_labiba.py /home/malrahabi/ragHumanistica/pipeline/ask_labiba.py`
4. `sudo pkill -f "streamlit run pipeline/ask_labiba.py --server.port 8505"`, verify with `ps aux | grep ask_labiba` that nothing remains before relaunching (same discipline as the Task 1 duplicate-process incident).
5. Relaunch: `sudo bash -c 'cd /home/malrahabi/ragHumanistica && source venv/bin/activate && nohup streamlit run pipeline/ask_labiba.py --server.port 8505 > /tmp/ask_labiba.log 2>&1 &'` (needs the `sudo bash -c` wrapper since a plain `cd` into that directory is permission-denied for `labiba`'s own shell).
6. Restart verified from the `lfarooq` side via `ps aux`/`ss -tlnp`/`curl localhost:8505` — process/port/HTTP state visible even without file access.

### Rebrand + onboarding modal ported to real code (later session)
Title/subtitle/page-title updated in real code. Contact block added to both side info-rail (fr/en) and the new onboarding modal. Onboarding modal implemented with real `st.dialog()` (Streamlit ≥1.31) — forced-read popup on first load, dismiss sets `st.session_state.onboarding_seen=True`. Includes a feature-detection fallback (`hasattr(st, "dialog")`) for older Streamlit versions — unconfirmed which path fires on this server. The mockup's stale sidebar model list was NOT copied back; the already-trimmed 2-model list was kept. Deployed, new process confirmed listening on 8505 (PID 3757271 at deploy time).

### Not yet done as of last session
- Confirm whether `st.dialog` is actually available in the server's Streamlit version.
- Visual/UX confirmation from Labiba that the onboarding modal renders/dismisses correctly.
- Visual confirmation that the light/dark theme fix actually resolved the white-patch issue.

---

<a id="lessons"></a>
## 11. Cross-Cutting Lessons & Workflow Feedback

These are standing rules distilled from repeated incidents across the project, not one-off notes — apply them by default going forward.

### Experiment iteration discipline
1. **Always test a fix on a handful of items before relaunching a full run.** Confirmed working well for the Task 0 v6 thinking-mode bug: diagnose root cause via direct API test, apply fix, validate on the specific previously-failing item, THEN stop+archive the partial buggy run and relaunch clean. Don't patch-and-resume on top of a partial run generated under a different/buggy methodology — mixes inconsistent generation processes in one results file.
2. **Confirm before stopping or restarting a multi-hour background run**, even when reversible/cheap — Labiba appreciates being asked.
3. **Don't over-interpret accuracy numbers from small samples.** Both v6 and mapreduce_v6 showed wild, misleading swings in the first ~15-35 novels before settling. State running numbers but flag "too early to read into this."
4. **When asked for "an update," check actual process/file state directly** (ps, log tail, CSV row counts) rather than estimating from elapsed time.
5. **For "do X automatically while I'm asleep" requests, prefer a plain detached OS-level background process** (nohup, polling/sleeping) over an LLM-prompt-based scheduler — a cron job re-invoking the agent depends on the session being idle/responsive, a weaker guarantee than a sleeping shell process. Make any backup/fallback trigger idempotent (check target process isn't already running) to avoid duplicates.
6. **Watch for timezone mismatches in relative-time requests.** A relative offset ("after 3.5 hours") sidesteps ambiguity better than computing an absolute wall-clock target.
7. **Before proposing a fix for a weak-accuracy criterion, empirically replay actual API calls on known-misclassified examples — don't just theorize from a confusion matrix.** "Investigate first" surfaced a much bigger root cause (a context-truncation bug cutting visible text to ~10% of the novel) once, that an initial 3-item fix plan would have completely missed.
8. **No gold-set examples or specific corpus novels in prompts.** Prompt text must stay purely definitional/generic — never reference a specific novel's plot, title, or gold label. Applies to all future prompt-engineering (Tasks 0 and 1 alike, and later explicitly reapplied to Task 2).
9. **A small validation batch can hide a full-corpus regression.** RÉGIME NARRATIF's fix looked like a clean win on a 15-novel sample (53%→66.7%) but regressed on the full 76-novel run (72.7%→63.2%) because the new rule overcorrected. Treat a small batch as "safe to proceed to a full run," not as final confirmation.
10. **When a per-chunk categorical judgment field keeps collapsing to one default answer, stop rewording it and change the architecture instead.** Three different wordings of an INTRIGUE per-chunk field (`narrative_unit_type`, `plot_threads`, `section_texture`) all independently collapsed to the "simple/coherent" default. What worked: drop the per-chunk categorical judgment entirely, keep only concrete factual extractions, move the comparative judgment to the REDUCE step. **General principle**: fields asking for FACTS reliably vary; fields asking for ABSTRACT CLASSIFICATION at the chunk level tend to collapse to the modal answer, especially at temperature=0 with `format:json` forcing immediate generation with no deliberation space. (Same failure family later diagnosed in Task 0's v10c FOCALISATION FOC_ELARG collapse, and the ESPACE/REG_FANT/TEMP_DESORD default-collapse pattern.)
11. **Verify "I found this in the transcript" claims from another session against the live files before trusting them.** Twice, another session's claimed quote/recollection of file contents turned out not to match what's actually on disk, including one claim that source files had been "erased" when they demonstrably still existed.
12. **Watch for leaky model selection, not just leaky training.** `train_chunk_classifier_60novels.py` tried 3 classifiers (LogReg/RF/GB) per criterion and reported whichever scored highest on the same leave-one-out loop being reported — inflating results +5.3pp overall (up to +13.4pp on ESPACE). Fix: nested CV. Distinct failure mode from #9 — can happen even on the full eval set, whenever "try N approaches, report the winner's score-on-the-same-set" is the pattern.
13. **When Labiba says "wait, I remember getting X," actually re-derive it from files rather than assuming she's misremembering.** Her recollections of past numbers have been reliable ground truth to check against, not noise to wave away.
14. **A "frozen" result file's predictions differing from a live rerun is not uniformly old-worse or live-worse — check per-criterion.** Across all 7 narratology criteria once, 3 improved live, 3 regressed live, 1 tied — traced to real pipeline/model changes, not noise.
15. **A leaky model-selection bug can live in more than one script that reuses the same pattern** — found by directly reading the code, not assuming.
16. **Always re-score against the live current gold file before repeating a "best method" claim, even one already sitting in memory.** Earlier memory asserted "v3 mapreduce is best" for several criteria, true against an old gold set/scheme; `chunk_classifier_60novels.csv` beat it on 4/7 criteria against the current gold — this applies the "verify recalled numbers" principle to the agent's own past-session memory, not just Labiba's recollections.
17. **Two non-comparable gold sets can silently coexist for the same task.** Always check for code-vocabulary drift (not just row-count drift) before treating old and new gold files as interchangeable, even for criteria that look "unchanged" — individual labels can still be corrected.
18. **Small-N "winners" must be explicitly discarded, not just footnoted.** A top-ranked file with N=5-8 is noise; treat this as a standing requirement.
19. **Always use the small-batch-with-regression-check protocol before any full gold-set re-run.** Confirmed twice in one session: Task 2's catch-all fix (real win, small-batch-tested first) vs. Task 4.5's second CH/P fix (real regression, went straight to the full set without a small-batch check) — the protocol correctly predicted both outcomes in advance.

### qwen3 truncation pattern (general bug, found independently in 3 places)
qwen3:30b (via Ollama, thinking mode on) counts its invisible `<think>...</think>` reasoning against the SAME `num_predict` budget as its visible answer. Any prompt asking the model to work through several sequential questions (decision trees, CMT-style chains) gives it a lot to narrate through in `<think>` — if `num_predict` is too low, the model can burn the entire budget reasoning about the first question and never emit the final JSON at all. Found 2026-07-09 in Task 2's 14-step decision tree (had 17/114 UNKNOWN at `num_predict=3000`), Task 4.5's 5-step CMT chain (had 48/104 UNKNOWN, worse than the simpler prompt it replaced), and separately in the DH Humanistica app's `call_ollama()`.

**How to diagnose directly** (don't guess from the UNKNOWN rate alone) — reproduce one failing row outside the pipeline and check `done_reason`/`eval_count`/content:
```python
resp = requests.post(OLLAMA_URL, json={"model": MODEL, "messages": [...],
    "stream": False, "options": {"temperature": 0, "num_predict": N, "num_ctx": 16384}})
data = resp.json()
print(data.get("done_reason"), data.get("eval_count"), repr(data["message"].get("content","")))
```
`done_reason: "length"` + `eval_count == num_predict` + empty `content` (with `thinking` full of unfinished reasoning) is the unambiguous signature — distinct from a genuine parse failure (malformed JSON still has content) and distinct from `ERROR` rows (a separate, undiagnosed connection/timeout issue, 3/111 in Task 2's case).

**Fix**: raise `num_predict` to ~8000 for anything asking for 3+ sequential reasoning steps — sufficient for both Task 2 and Task 4.5 (single call ~30-80s, well under a 300s timeout). **Always re-validate BOTH the old and new prompt at the higher budget before concluding which is actually better** — a "regression" found at low `num_predict` may just measure who burned through their thinking budget faster, not real prompt quality (this is exactly what happened to Task 4.5's CMT redesign, initially misread as a bad technique).

### GPU sharing discipline
This machine has one shared GPU (A40, 46GB), no sudo/MPS access, no true hard resource-splitting. All qwen3 jobs (Task 0/1/2/4.5) queue on the same Ollama instance — running two at once measurably slows both (e.g. Task 1 dropping from 4s/row to 8-9s/row when another job runs concurrently). **Getting permission to make a code fix is NOT the same as getting permission to immediately run/validate it**, if doing so shares the GPU with another job currently prioritized. Before launching any qwen3/Ollama job: check whether another job is running (`pgrep -af run_task`); if so, ask explicitly whether it's OK to share the GPU right now. This applies symmetrically to Tasks 0/1/2/4.5.

**Incident**: applied a Task 2 fix, then re-ran its gold validation to verify — without asking first, putting it back on the GPU alongside Task 1, which Labiba wanted running alone. She corrected: "why did you start task 2? let the gpu only run on task 1 for now."

**Exception, not a new default**: during active back-and-forth rapid-iteration sessions (e.g. 2026-07-10 with up to 4 concurrent qwen3 jobs at Labiba's explicit direction each time), deliberate GPU sharing is fine — but don't generalize this as new default behavior; still ask first outside that mode.

### Finding true process output
When a background process's real progress/log output isn't in an obviously-named file, check what its stdout/stderr file descriptors actually point to:
```bash
ls -la /proc/<PID>/fd | grep -i log
readlink -f /proc/<PID>/fd/1
```
A script's own internal progress log (with authoritative row counts, percentage, speed, ETA) is always more trustworthy than deriving stats externally from file sizes/row counts. Check for one before computing anything.

**Sudo interactivity limit**: the agent's Bash tool runs non-interactively and cannot supply a sudo password or reuse an already-authenticated sudo session, even moments after the user typed their password in their own terminal. Any sudo command on `obtic-gpu1` must be run by Labiba herself, output pasted back.

### Proactive checkpointing
Save a project-status memory update at natural checkpoints — end of session, after a significant decision, after real progress — without waiting to be asked. **Why**: an entire session's work/decisions were lost once because the most recent memory checkpoint was from the prior afternoon. This does NOT mean logging raw verbatim chat transcripts (buries the signal) — keep entries distilled (facts/decisions/state), same standing-trigger treatment as "investigate first."

### Task 1 duplicate-process incident (full writeup in Task 1 section above)
Never trust a script's own "process stopped" log line — always independently verify via `ps`/`pgrep`. Before trusting any CSV-corruption diagnosis, parse with a real CSV library (respecting quoting/embedded newlines), not `awk`/naive line splitting.

### Task 4.5 category-is-target-entity-type rule
Full writeup in the Task 4.5 section above — standing rule, not a one-off tiebreaker: classify the ontological entity type of the comparison's target, never the semantic domain of the trait/quality. If a prompt fix reads like "trait X belongs to category Y," check it against entity-type framing first.

### Miscellaneous technical gotchas
- **`wc -l` is unreliable for row counts** on any file where a field might contain embedded newlines (Task 1 corpus sizing, multilingual names CSV — 951 raw lines vs. 554 real records). Always trust the actual parser's count (`csv.DictReader`) over raw line count.
- **Isolate one variable per experiment.** Task 0's "v8" changed 5 prompt definitions at once and made results worse with no way to tell why; "v9" changed exactly one thing and gave a clean, interpretable result.
- **For retries/re-runs, import and reuse the exact original functions** rather than re-describing the prompt from scratch — a first Task 1 animaux retry attempt drifted from the production prompt this way and had to be redone. (Reapplied later for the ESPACE-only detour script, which imported every reusable function from v9 unchanged.)
- **Any script reading `dépendants_*.csv` files must use `polars`, not stdlib `csv`** — Python-tuple-repr strings with embedded quotes break stdlib csv's quoting rules and silently shift fields.
- **File-encoding gotcha**: accented filenames (`Catégories analyse comparés.docx`) sometimes fail a literal-quoted `ls "filename"` / direct path match despite visibly existing in `ls -la` (precomposed vs. decomposed Unicode accents from different upload/scp sources). Fix: use a shell glob (`Cat*.docx`) instead of typing the accented name literally.
- **Server clock is UTC; user's local time is UTC+2** — worth remembering when discussing elapsed/ETA times.
- **Monitor/notification cadence**: default to a ~5-minute polling cadence for background-job monitors rather than reporting on every line of underlying progress output.

---

<a id="meetings"></a>
## 12. Meeting Notes & Decisions — Full Chronology

Two full meeting transcripts exist (verbatim in `PROJECT_DOCUMENTATION.md` §7-8): `riccardo_25june_meetingTranscript.md` (first meeting, June 25, 2026) and `métaphore/Riccardo_second_meeting.txt` (second meeting, exact date uncertain from the transcript, content places it ~early July, likely close to the originally-scheduled July 3 11am slot — Task 1 animaux was mid-run, about to finish "tomorrow night," plantes "in two days"). A **third meeting was scheduled for "the 10th of July"** — Riccardo has a personal appointment at 10:45am that day, meeting agreed to be in the afternoon, exact hour not pinned down in the transcript.

### First meeting (June 25, 2026) — key decisions
| Decision | Detail |
|---|---|
| Joanna's disambiguation accepted | ~85% accurate, don't redo it |
| Task 1 approved | Run on ENTITES files, start with main corpus |
| Task 5 deferred | Too complicated, Joanna's pipeline already exists |
| "Espace" subcategory likely dropped | Models can't do it reliably — "I would probably eliminate space at this time" |
| Task 0 ceiling acknowledged | 70-75% is SOTA per literature, document the dead end if needed |
| Gold set format agreed | 200 figurative occurrences, 2 annotation columns (Task 2 subcategory + Task 4.5 comparé category), same sheet for both tasks |
| Documentation named as #1 priority | Everything — what worked, what didn't, why, all models tried |
| Next meeting set | July 3, 2026, 11am |
| Labiba's departure confirmed | July 15, 2026 |
| Riccardo's travel | away July 3 to July 9 |

Task 0 discussion: best result at the time 68.3% (qwen72b with thinking); LoRA fine-tuning failed (dataset too small, 3 gold novels missing from CORPUS_TOTAL); papers cited ~70-75% SOTA; Riccardo suspected the gold set itself might have FOCALISATION errors, proposed cross-model agreement as a diagnostic ("just check if the models agree with each other. If my gold is wrong, it means that the model should agree with each other [but disagree with the gold]"). Next steps agreed: send Riccardo the gold-set items where every model disagrees; try GPT-4 via Riccardo's OpenAI key (~$9/€8 remaining at the time); try fine-tuning.

**Two competing hypotheses for the plateau, offered live in the first meeting**: (1) the gold set itself may have errors, especially for FOCALISATION — Riccardo: "Either the goal sets are not correct... especially for the focalization... Maybe you can check the gold set again... every single time I run, these are the exact results I get mostly from every model"; (2) models simply aren't capable enough yet for this specific task — Riccardo: "I guess it is normal if it doesn't work that well... these models are not trained on these specific things." The second meeting revealed a third factor: the FOCALISATION coding scheme itself changed mid-project, meaning some of the "gold set might be wrong" confusion from meeting 1 may partly have been a moving-target coding scheme, not gold-set errors in the ordinary sense.

**Specific numbers read live off the screen in the second meeting** (some clearly garbled in the speech-to-text transcript, e.g. "68.3" transcribed oddly as "83.63" — preserved as best interpreted): TYPE NARRATEUR ~91%; FOCALISATION 70-75%; RÉGIME NARRATIF 76.7% — Riccardo: "if we could get it up to 80%, that would be amazing"; INTRIGUE 68.3%; TEMPORALITÉ 71%; ESPACE not given as a number, explicitly called the weakest criterion — Riccardo (first meeting): "I would probably eliminate space at this time." Riccardo's overall stance, both meetings: "Are you okay with 70%? ... I think we will do with it. We'll go with it." — a working acceptance of the plateau, while still hoping the paid-model experiment could push specific criteria (RÉGIME especially) toward 80%.

Task 1 discussion: before this project, Joanna got ~47% (or 16%, transcript unclear) accuracy with ChatGPT. Current best figurative accuracy at the time ~89% (fewer few-shot examples worked better — more examples caused hallucination). Overall accuracy ~69.6% (transcript garbled, possibly "96.9%"). After correcting ambiguous gold items, figurative accuracy → 78-80% on Loterre. Riccardo expected ~90% overall once applied to the whole corpus. Riccardo reviewed 15 ambiguous Loterre cases live and gave rulings (see Task 1 section above for the specific cases).

Task 2 discussion: annotation scheme already built and confirmed by Riccardo ("this is already done"). Must use this project's own Task 1 results, not Joanna's ChatGPT-based ones. Gold set needed: 200 randomized figurative occurrences, 100 animals + 100 plants, drawn from this project's own figurative results.

Task 3 discussion: agentivity table confirmed correct by Riccardo, live review of the lion examples (see Task 3 section). Riccardo asked why percentages don't sum to 100% — answer: the "Other" category, needs to be documented explicitly. Multilingual name detection requested (French model misses Arabic/English names) — heuristic proposed: mid-sentence capitalization + multilingual NER, watching for false positives like "Bar" (Arabic name) vs. "bar" (fish), "Fleur" (name) vs. "fleur" (flower).

Task 4.5 discussion: 6 categories identified in the meeting (CH=corps humain, abstract concept, natural element, +3 more Riccardo couldn't recall live — check GitLab/Colab). Terminology clarified (comparant=vehicle, comparé=tenor/target). Can only run after Task 1. Category definitions promised, to be sent later.

New biodiversity-indices task raised (see §9 above) — Riccardo's own side-exploration, not urgent for Labiba.

### Second meeting (~early July, before 2026-07-08) — key new decisions, building on/updating meeting 1

**Task 0 — FOCALISATION coding scheme changed.** Riccardo sent a genuinely different focalization framework (reader-vs-character-knowledge rather than whose-consciousness) plus a new `MOD_DIA` mode category. Action agreed: re-run Task 0 on the new schema file, Riccardo to send a fresh gold set in the new codes before any further focalization comparison is meaningful — old FOCALISATION numbers not comparable post-change.

**Task 0 — paid GPT approved.** Riccardo explicitly OK'd using the OpenAI API budget (~€22-25 estimated for a full run, offered up to €100-200 more if needed), with the instruction to email him before topping up past a set amount. This is what funded the GPT-4o v7 76.1% result.

**Task 1 — approved and confirmed working well.** Riccardo reviewed ~15 ambiguous gold-set disagreements live, agreed most were genuine gold-set errors. Gave the "image within an image" ruling (embroidered/painted birds, drawn mountains → FIGURATIVE, since it's a representation not the real thing) — this is the origin of Task 2's `IMAG` category.

**Task 2 — 3 new subcategories added live during this meeting** (COUL, LOC_IDIOM, IMAG — see Task 2 section for full definitions). No formal written definitions existed yet at this point, only Riccardo's spoken examples — a written definitions doc was requested and later received (`schema_analogies_vivant_complet_0807.csv`, 2026-07-08).

**Task 3 — multilingual names explicitly requested again.** Riccardo asked to see example rows from the human-agentivity results, surprised the % undetermined-gender was so high — origin of `extract_humains_multilingual.py`.

**Documentation — Riccardo's #1 ask, restated with more detail.** Wants as much detail as possible on every method/technique tried and what did/didn't work, "as much as you can, as long as it stays understandable" — **up to ~40 pages is explicitly fine with him.** File-level specifics ("which exact file did you run") matter less than being able to follow the steps and translate the approach into his own understanding. Asked for at least a partial draft by Wednesday (~07-08) so he can read it before the next meeting. **This request is what produced `PROJECT_DOCUMENTATION.md`, and later this master document.**

**New biodiversity-indices task, reconfirmed self-directed** — Riccardo said he'd likely do this analysis himself.

**Task 5 reconfirmed dropped.**

**Deadline logistics confirmed**: last working day effectively **2026-07-13** (July 14 is a public holiday, July 15 is departure). Riccardo explicitly said not to worry about finishing everything by the 13th — remote follow-up after Labiba leaves is fine ("we can communicate online until I give you the final results").

### Riccardo's items delivered 2026-07-08 (resolving 3 of 5 outstanding blockers in one day)
1. **New Task 0 gold set** — `narratologie/GOLD_narratologie_0807.csv` (80 rows/79 novels, new FOCALISATION codes, zero blanks).
2. **Task 2's 3 new-category definitions** — `métaphore/schema_analogies_vivant_complet_0807.csv` (19 total categories).
3. **Task 4.5 definitions file** — `métaphore/Catégories analyse comparés.docx` (6 categories, full text captured in the Task 4.5 section above).

Remaining 2 items at that point: Task 2 gold-set blank completion (69/200 rows), Task 4.5 gold-set blank completion (88/200 rows) + scoring convention for 4 `?` rows.

### Riccardo's email reply on gold-set blanks (2026-07-08), verified against the file
- **72 rows marked `X`/`x`** — per Riccardo, wrongly classified as figurative by Task 1 in the first place; to be replaced with freshly-drawn figurative samples once Task 1 (plantes) finishes, not annotated by design.
- **Blank `categorie_compare`**: 7 IMAG rows all blank (confirmed by design — IMAG has no compare-target). Found 15 more blanks not explained by IMAG or X — mostly LOC_IDIOM (9, same no-compare-target logic), plus COUL and one META_VERB. **One row (id 56) has both columns entirely blank, unexplained** — flagged back to Riccardo, resolution not confirmed.
- **4 rows with `categorie_compare == "?"`** — "maybe exclude," tentative, final confirmation not yet received as of the last update.

### Riccardo's live-meeting email (2026-07-10) — the major reframes
1. **Task 4.5 categories = target entity type, not trait domain** (see Task 4.5 section — overturns the earlier CH/P "Piège fréquent" patch).
2. **META_JUXT eliminated for Task 2**, fold into META_APP (see Task 2 section).

Same email: Riccardo would check his references for the open Task 2 DE_PARANGON/DE_PROP/META_APP questions "first thing tomorrow" (2026-07-11) — follow-up needed if nothing arrived.

Four new pending tasks queued from this live meeting, explicitly held until told to start:
1. New randomized gold sets for Task 2 and Task 4.5, redrawn from the now-fully-corrected Task 1 results, replacing the 72 X-marked rows — should explicitly request NH-target coverage this time.
2. Estimate false-positive-name % in Task 3's 72-novel multilingual partial run.
3. Fix the Récepteur-passif être-auxiliary contamination in Task 3 humans.
4. Compile the GPT-4 (paid API) results table for the ~36 novels processed before the original budget ran out.

### Riccardo's later same-day email (2026-07-10) — physical/psychological refinement
See Task 4.5 section for the full verbatim quote and worked examples (rat/il/CH, Pierre Castaneda/P, fougère/"mon penser"/CH).

---

<a id="gpu-freeze"></a>
## 13. GPU Freeze Period (2026-07-10 → ~2026-07-22)

**Starting 2026-07-10 (end of day), Labiba does not have GPU access for approximately 12 days**, until roughly **2026-07-22**. Cause: a temporary 45-minute GPU window borrowed from someone else that evening had to be handed back, implying the shared A40 is unavailable to her for an extended period afterward.

**Rule for this window**: do NOT launch, resume, or relaunch any script calling Ollama/qwen3:30b (`localhost:11435`) without explicitly checking with Labiba first, even for a "quick validation." Affects every GPU-dependent pipeline: Task 0 (all variants — v9, v10c/v10d), Task 1, Task 2, Task 4.5, and likely the DH Humanistica Streamlit app (uses Qwen3 too — worth confirming before assuming it's fine to touch).

**Task 3 (spaCy dependency parsing) does NOT use the GPU/LLM at all** — safe to continue freely.

**What can still be done without GPU**: prompt/code editing and static review (no live testing); data analysis on already-collected results (gold validation CSVs, confusion matrices); writing up findings, drafting emails to Riccardo; Task 3 work; planning the next round of fixes so they're ready to launch the moment GPU access returns.

### State of each GPU-dependent task when the freeze began (2026-07-10 evening)
- **Task 4.5**: finished its few-shot round at **85/104 = 81.7% (final)** — best result of the session. Physical/psychological refinement built in a new sibling file, `run_task45_compare_category_v2_physical_psych.py` — **never tested**, first thing to validate once GPU returns.
- **Task 2**: **paused mid-run** at 43/114 rows (few-shot version, `métaphore/resultats_task2_gold_validation.csv`), resumable via the script's built-in done-id skip. Early signal weak/flat (69.8-74.2%, not clearly above the 73.7% baseline) — DE_PARANGON/DE_PROP ambiguity likely needs Riccardo's input more than further prompt tuning; email drafted, Riccardo replied he'd answer "first thing tomorrow" (2026-07-11).
- **Task 0 v9** (full 7-criteria, 60/79 novels): finished. Corrected 2026-07-11 (see Task 0 section for full recomputation methodology): TYPE NARRATEUR 90.0% (54/60), MODE NARRATIF 36.7% (22/60), ESPACE 60.0% (36/60), INTRIGUE 41.7% (25/60).
- **Task 0 v10c** (new FOCALISATION scheme): finished, FOC 32.9% / REG 60.8% / TEM 68.4%. FOC_ELARG-collapse bug diagnosed, first fix attempt (v10d) only scored 1/4 on smoke test with a regression — not resolved.
- **REG_FANT and TEMP_DESORD**: both 0% recall, diagnosed but not root-caused (need to replay actual misclassified novels' raw observations first, per "investigate first").
- **ESPACE** (full v9 run): same default-collapse pattern (over-predicts ESP_UNIT) — confirmed to be a real pre-existing model bias, not a resume bug. Undiagnosed/unfixed.

**Recommended next steps for whenever GPU access returns** (from the memory record at freeze time): (1) send Riccardo's email and wait for his answers on the two open ambiguities before touching Task 2/4.5 further; (2) the FOCALISATION/REGIME/TEMPORALITÉ/ESPACE default-collapse family of bugs in Task 0, now a confirmed recurring pattern across 4 different criteria, probably deserves a general architectural fix (evidence-count-based aggregation, tuned better than the v10d attempt) rather than one-off patches per criterion.

---

<a id="current-state"></a>
## 14. Current State Snapshot / Open Items (as of the GPU-freeze cutoff, 2026-07-10 evening)

| Task | Status | Best result | Key open item(s) |
|---|---|---|---|
| §0 Foundations | Done, accepted as-is | — | None (deliberately not redone) |
| Task 0 (narratology) | Active, GPU-frozen | GPT-4o v7: 76.1% (34/60 novels, paid); v9 vs. old 60-novel gold (max/headline): ESPACE 61.7% (37/60), FOCALISATION 76.7% (46/60, old scheme, w/ alternates); v9 vs. current 79-novel gold: TYPE 90.0%/MODE 36.7%/ESPACE 60.0%/INTRIGUE 41.7%; v10c (79/79 novels, new FOCALISATION scheme): RÉGIME 60.8%/TEMPORALITÉ 68.4%/FOCALISATION 32.9% | FOCALISATION new-scheme collapse unresolved; REG_FANT/TEMP_DESORD 0% recall undiagnosed; ESPACE default-collapse undiagnosed; GPT-4o run stuck at 34/60 |
| Task 1 (référentiel/figuré) | **Fully complete** | Animaux 91.8% (corrected), Plantes 98.4% (corrected), Loterre 88.9% (corrected) | None — only task with no open blockers |
| Task 2 (metaphor subcategories) | GPU-frozen mid-run | 73.7% (META_JUXT-eliminated baseline); few-shot round paused at 43/114 | Below 80% scale-up bar; DE_PARANGON/DE_PROP ambiguity awaiting Riccardo's ruling |
| Task 3 (agentivity) | Core findings solid, some refresh work pending | Humans 37.2% > Animals 23.8-24.4% > Plants 11.1-11.8% active agent | Humans bestsellers coverage gap unfixed; passive-voice être-auxiliary contamination unfixed; multilingual names paused at 7.8% coverage, false-positive rate not estimated |
| Task 4.5 (compare-target) | GPU-frozen, awaiting v2 test | 85/104 = 81.7% (frozen v1 file) | Physical/psychological split (v2 file) never tested; 4 more error buckets found post-hoc, not fixed; zero-NH gold-set gap |
| Task 5 (front-end) | Deprioritized/dropped | — | — |
| Biodiversity indices | Riccardo's own side-exploration | — | Not touched by Labiba |
| DH Humanistica app | Deployed, mostly working | — | `st.dialog` availability unconfirmed; visual confirmation of onboarding modal and theme fix pending from Labiba |

### Immediate next actions once GPU access returns
1. Test `run_task45_compare_category_v2_physical_psych.py` against gold — first priority.
2. Follow up with Riccardo on the Task 2 DE_PARANGON/DE_PROP/META_APP boundary-case email if no reply arrived.
3. Resume Task 2's few-shot gold validation from row 43/114, or decide whether to redesign given the weak early signal.
4. Decide on an architectural fix for Task 0's cross-criterion default-collapse bug pattern (FOCALISATION, RÉGIME, TEMPORALITÉ, ESPACE) rather than more one-off patches.
5. Fix Task 3's humans bestsellers coverage gap and passive-voice contamination (both GPU-free, could be done during the freeze).
6. Complete Task 3's multilingual-names false-positive-rate estimate (GPU-free).
7. Compile the GPT-4 paid-API results table for the ~36 novels processed before the original budget ran out (GPU-free, needs the right output files located and novel count verified).
8. Redraw Task 2/Task 4.5 gold sets once Task 1 is confirmed fully stable, replacing the 72 X-marked rows and explicitly requesting NH-target coverage for Task 4.5.

---

<a id="verification-log"></a>
## 15. Verification Log (2026-07-11 re-audit)

A full re-verification pass was run against primary sources — `PROJECT_DOCUMENTATION.md`, all 20 memory files, and the actual raw CSV/log files in `narratologie/`, `métaphore/`, `comparison/`, `morphosyntaxe/`, and `resultats/` — covering every numeric claim, N, filename, and citation in this document. **Summary: roughly 194 distinct claims were spot-checked (Overview/Task 0 ~45, Task 1 ~28, Task 2 ~24, Task 3 ~32, Task 4.5 ~20, Meetings/Lessons/DH-app/Current-State ~45), of which 4 were found to be actually wrong** (an error rate of roughly 2%) — 2 pre-flagged by Labiba before this pass began, 2 newly found during the pass. Everything else checked matched its primary source exactly; unverifiable items (paraphrased meeting quotes, qualitative judgments) were left untouched per instructions.

### Corrections made

1. **Task 0 — v9 full 7-criteria run, wrong headline numbers (pre-flagged by Labiba).** Was: "59.8% overall. TYPE 93.2% strongest, INTRIGUE 42.4% / MODE 39.0% weakest." These were computed against the `GOLD_*` columns embedded inside `resultats_task0_mapreduce_v9.csv` itself (N=59, silently dropping one blank-gold row), not against the actual current gold file. **Corrected** to the true, directly-recomputed numbers (strict match, no "Acceptable aussi" alternates, joined by filename against `narratologie/GOLD_narratologie_0807.csv`): TYPE NARRATEUR 90.0% (54/60), MODE NARRATIF 36.7% (22/60), ESPACE 60.0% (36/60), INTRIGUE 41.7% (25/60) — all from `resultats_task0_mapreduce_v9.csv`, which only covers 60 of the 79 gold novels. For RÉGIME NARRATIF, TEMPORALITÉ, and FOCALISATION (new scheme), the latest full-79-novel technique is `resultats_task0_v10c_reduce_think.csv`: RÉGIME 60.8% (48/79), TEMPORALITÉ 68.4% (54/79), FOCALISATION 32.9% (26/79). No single blended "overall %" is reported anymore since the two files/techniques cover different N's. **Source**: direct Python recomputation against `narratologie/GOLD_narratologie_0807.csv` + the two result CSVs, confirmed independently during this pass. Propagated to 3 locations: the main Task 0 write-up, the GPU Freeze Period section, and the Current State Snapshot table.

2. **Task 0 — stale small-N ESPACE/FOCALISATION picks in the hybrid table (pre-flagged by Labiba).** Was: ESPACE "`resultats_task0_mapreduce_v9.csv` hit 66.7% but only N=15, unconfirmed at scale"; FOCALISATION best pick shown only as `resultats_task0_v10b_calibrated.csv` 60.0% (N=20) with no full-scale figure given. **Corrected**: ESPACE's true full-scale (60-novel) v9 figure is 60.0% (36/60), not 66.7%/N=15 — the N=15 figure was an earlier unconfirmed checkpoint superseded once the full run finished. FOCALISATION's only full-79-novel new-scheme attempt is v10c at 32.9% (26/79), now stated explicitly alongside the small-N v10b figure. **Source**: same recomputation as #1.

3. **Task 1 — batch=5 plantes "corpus days" transcription error.** Was: `| 5 | 3.4s/row | 5.0 | 2.7 | 79.7% |` (batch-size summary table) — the plantes-days column showed 2.7, identical to batch=4's value one row up. **Corrected** to 3.2 days, matching batch=5's actual 3.1s/row plantes speed reported elsewhere in the same section. **Source**: `PROJECT_DOCUMENTATION.md` lines 195 and 1424 (batch=5 plantes speed = 3.1s/row → 3.2 days), found by a verification subagent cross-checking the summary table against the detailed per-category tables in the same document.

4. **Task 3 — animal-side coverage-gap missing-row count.** Was: "Closed by re-parsing 15,337 missing rows." **Corrected** to 14,906, confirmed by directly parsing `morphosyntaxe/dépendants_ANIMAUX_missing_rows.csv` (14,906 rows) and cross-checking the arithmetic: the original file parses to 112,775 rows (ignoring malformed multiline rows), and 112,775 + 14,906 = 127,681, which exactly matches the documented `dépendants_ANIMAUX_COMPLET.csv` merged-master row count (also independently confirmed at 127,681). The wrong "15,337" figure (=13,094 bestsellers + 2,243 corpus_principal, an arithmetic sum rather than the actual re-parsed file's row count) was already present in `PROJECT_DOCUMENTATION.md` and in memory file `project_2026-07-08_session.md` — this pass fixes it in `MASTER_DOCUMENTATION.md` but the earlier files still contain the original error. **Source**: direct polars parse of `dépendants_ANIMAUX_missing_rows.csv` and `dépendants_ANIMAUX_COMPLET.csv`.

### Additions made

5. **Missing citation added — Task 4.5.** [Tenor-vehicle-ground extraction, arxiv 2010.05633](https://arxiv.org/abs/2010.05633) (validate via the shared "ground" property before classifying) was used for Task 4.5's early tenor/vehicle prompt rewrite (the one that reached 63.5%) but was absent from the document despite being used in the actual project work. **Source**: `project_2026-07-08_session.md` line ~141. Added inline next to the "Tenor/vehicle prompt rewrite" row of the version-by-version accuracy table.

6. **Missing citation added — Task 2.** [MIPVU rule-script/decision-procedure prompting, arxiv 2603.10784](https://arxiv.org/abs/2603.10784) is the literature basis for Task 2's 14-step decision-tree redesign (the same technique that also informed Task 0's RÉGIME NARRATIF fix, per the same memory entry). **Source**: `project_2026-07-08_session.md` line ~145. Added inline next to the "Decision-tree redesign (14 steps)" row of the version-by-version accuracy table.

### Noted but not changed (genuine ambiguity in the primary sources themselves, not a documentation error)

- **Task 2's v5 result is stated as both 64.9% (74/114) and, in the v6 row's "up from" comparison, 66.7% (76/114).** Both figures are independently attested in dated session memory files (`project_2026-07-10_session.md` line 44 gives 64.9%; `project_2026-07-10_session3.md` line 38 gives 66.7%) — this is a same-day inconsistency in the underlying research notes, not something introduced by this document. Left as-is, per instructions to flag rather than silently resolve contradictions in primary sources.
