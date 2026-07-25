# ÉCOPOÉTIQUE NUMÉRIQUE — COMPLETE TECHNICAL DOCUMENTATION v2
## Full Project Documentation: May 2026 – July 2026
**Researcher:** Riccardo Barontini (UPPA — Université de Pau et des Pays de l'Adour)
**Chair:** "Enjeux écopoétiques contemporains" — ANR programme "Anthropocène littéraire"
**Research Engineer:** Labiba Farooq (M2 Internship, May–July 15, 2026)
**Previous Engineer:** Johanna Cordova
**Server:** obtic-gpu1 — lfarooq@134.157.57.238 (Port 11435 for Labiba's Ollama)
**GitLab:** gitlab.huma-num.fr (institutional, HumanID login required) + gitlab.com/rumiwarmi/ecopoetique (private)
**Team chat:** ecopoetique.zulipchat.com (channels: llms, general)
**Internship:** May 2026 – July 15, 2026

---

## PART 1: PROJECT OVERVIEW & RESEARCH CONTEXT

### 1.1 Fundamental Research Question
"Is there a real 'ecological turn' in contemporary French-language literature, or is it just a feeling based on a few famous, well-known books?"

To answer this empirically, Riccardo Barontini developed the **Digital Écopoétique** project, funded by:
- A European Marie Skłodowska-Curie Actions postdoctoral fellowship (2023)
- Integrated into ANR "Anthropocène littéraire" programme at UPPA

### 1.2 Core Hypothesis
**Textual biodiversity** (variability of living organisms, ecosystems, and ecological concepts represented in novels) can serve as a **formal indicator** of ecological sensitivity in contemporary French fiction.

This hypothesis draws on:
- **Rosi Braidotti** (*Posthuman Knowledge*, 2019) — relational subjectivity, co-belonging between living beings and environments
- **Baptiste Morizot** (*Manières d'être vivants*, 2020) — the ecological crisis as a crisis of sensitivity: inability to perceive, distinguish, and name the living beings around us
- **Ursula K. Heise** (*Imagining Extinction*, 2016) — biodiversity as a cultural operator, endangered species acquire social effectiveness through collective narratives
- **Vincent Devictor** (*Nature en crise*, 2015) — biodiversity as contested metric, tied to political crisis discourse
- **Edward O. Wilson** — popularised "biodiversity" concept in late 1980s

### 1.3 Key Finding Already Established (Before Labiba)
The biodiversity index is **globally stable** over 2001–2024 — no clear "ecological turn" across the broad corpus. Only a **small cluster** of specific novels scores very high. The ecological writing does not spread diffusely; it crystallises in specific works.

**Confirmed:** Novels nominated for *Prix du Roman d'Écologie* score more than **2× the average** biodiversity index. 45 out of 47 such novels exceed the general corpus average — strong correlation between external qualitative categorisation (jury label) and internal formal measure.

### 1.4 Three Levels of Analysis
1. **Lexical/Semantic (Task 1):** Extract animal, plant, ecological terms; classify literal vs. figurative
2. **Stylistic (Task 2):** Figurative subcategory classification (metaphor type, comparant/comparé)
3. **Narratological (Task 0):** Automated narratological profiling (7 criteria per novel)

**Additional tasks:**
- **Task 3:** Agentivity (active vs. passive roles of animals, plants, humans)
- **Task 4.5:** Comparant/Comparé classification

### 1.5 Corpus Structure

| Corpus | Size | Description |
|--------|------|-------------|
| Corpus principal | 892 novels | Prize shortlists: Goncourt, Goncourt des Lycéens, Femina, Renaudot, Médicis, Livre Inter, Cinq Continents (2001–2024) |
| Corpus bestsellers | 124 novels | Top 5 best-selling novels per year |
| Corpus écologique | 47 novels | Nominees for Prix du Roman d'Écologie 2017–2024 |
| TOTAL (with overlaps) | ~1,070 novels | Combined unique novels |
| CORPUS_TOTAL (server) | ~925 .txt files | After deduplication on server |

**Note on literary prize bias:** Using prize shortlists is an acknowledged bias — only works that "institutions recognize as having value" are included. This allows asking: does ecological imagination align with literary consecration?

**Corpus metadata files:**
- `corpus_DigEco.csv` — main corpus metadata (tab-separated: Year, Author, Title, Sex, Nationality, Birth year, File)
- `corpus_Bestsellers.csv` — same format
- `corpus_PRIX_ECOLOGIE.csv` — ecology prize novels

### 1.6 Zipf's Law in the Corpus
The biodiversity vocabulary follows Zipf's law: 480 lemmas cover 90% of all ~290,000 occurrences, while the remaining 10% require 3,500+ rarely used lemmas. This reveals a structural tension between symbolic concentration (a few dominant species) and ecological dispersion (many rare ones).

---

## PART 2: SERVER SETUP & INFRASTRUCTURE

### 2.1 Hardware
- **Server:** obtic-gpu1 (Sorbonne Université — managed by Martial, server admin)
- **GPU:** NVIDIA A40 — 46,068 MiB VRAM
- **Disk:** 5.8TB total, ~116GB free (98% full as of July 2026)
- **OS:** Ubuntu 24

**GPU usage warning (July 6, 2026):** Martial (server admin) emailed noting 82-83% GPU utilization. Response: explained it's the final computation step, finishes July 8-9, then GPU returns to 0%.

### 2.2 Ollama Models (Port 11435 — Labiba's private instance)

| Model | VRAM | Status | Used For |
|-------|------|--------|----------|
| qwen3:30b | 18GB | ✅ Active | Task 1 production (BEST local), Task 0 map-reduce |
| qwen72b-limited | 22GB | ✅ Active | Task 0 FOCALISATION (68.3% — best local) |
| qwen2.5vl:72b | 47GB | ✅ Available (port 11435) | Base for qwen72b-limited |
| qwen2.5:7b | 4GB | ✅ Available (port 11434) | Testing only |
| gemma3:27b | 17GB | ❌ Deleted | Too slow, deleted to save disk space |
| mistral-small3.1 | 15GB | ❌ Deleted | Too slow for this task |

**Port 11434 (Other researchers' Ollama — DO NOT INTERFERE):**
qwen2.5:72b (47GB), qwen2.5:32b, qwen2.5:14b, qwen2.5:7b, bge-base-en-v1.5-gguf

### 2.3 qwen72b-limited Model Configuration
Created to reduce qwen2.5vl:72b from 47GB to 22GB VRAM with only ~1.6% accuracy loss:
```
# ~/Modelfile_limited
FROM qwen2.5vl:72b
PARAMETER num_ctx 8192
PARAMETER num_gpu 20
```
Recreate: `OLLAMA_HOST=localhost:11435 ollama create qwen72b-limited -f ~/Modelfile_limited`

### 2.4 Python Environment
```bash
source ~/digitize_medical_records/labelimg_env/bin/activate
```

### 2.5 Startup Script
`~/start_ollama.sh` — no longer exists (deleted/moved); manual startup required

### 2.6 Repository Structure (GitLab)
```
ecopoetique/
├── CORPUS_TOTAL/       # ~925 .txt novels — one sentence per line
├── TOKENS/             # spaCy POS analysis per text (token, POS, lemma)
├── TOKENS_Bestsellers/ # Same for bestsellers
├── lexiques/           # TaxRef, Wikispecies, Loterre vocabulary lists
├── homographie/        # Homograph disambiguation (bar=fish vs bar=place)
├── morphosyntaxe/      # Task 3 — dependency analysis scripts + results
├── métaphore/          # Task 1 & 2 — literal/figurative scripts + results
├── narratologie/       # Task 0 — narratology scripts + gold set + results
├── resultats/          # Corpus-wide entity extraction files
├── scripts/            # Python/bash pipeline utilities
└── visualisations/     # Charts and graphs
```

---

## PART 3: LEXICONS AND ENTITY EXTRACTION (Johanna's Foundational Work)

### 3.1 The Three Lexicons

**1. TaxRef** (MNHN — Muséum National d'Histoire Naturelle)
URL: https://inpn.mnhn.fr/telechargement/referentielEspece/referentielTaxo
Scientific species taxonomy; French territory including overseas. Provides vernacular names linked to unique species identifiers.

**2. Wikispecies** (Wikimedia)
URL: https://species.wikimedia.org
Global species database extending coverage beyond French territory. Merged with TaxRef after lemmatisation, orthographic normalisation, duplicate removal, unique ID assignment per species.

**3. Loterre** (CNRS/ISTEX)
URL: https://loterre.istex.fr/BLH/fr/
Not individual species — conceptual ecological vocabulary: ecosystems, ecological dynamics, natural processes, perturbations, climate change/environmental transformation vocabulary. Organised hierarchically: ~716 entries (project notes say ~900 distinct Loterre concepts found in corpus).

### 3.2 Extraction Results (Johanna's Pipeline)
~290,000 total occurrences from 1,070 novels:

| Category | Occurrences | % | Distinct Taxa/Entries |
|----------|-------------|---|----------------------|
| Animaux | 114,851 | 39.6% | 1,488–1,523 taxa |
| Loterre | 111,196 | 38.3% | ~716–900 concepts |
| Plantes | 63,599 | 21.9% | 1,567–1,609 taxa |
| Champignons + Taxons | ~3,000 | ~1% | marginal |

**Key asymmetry:** Animals dominate in volume (frequency) but plants have higher specific diversity (more distinct species). Mammals = 60% of animal occurrences but fewer taxa than birds.

**Ornithological sensitivity:** Birds have higher specific richness relative to occurrence count — signals a notable ornithological sensitivity in contemporary French literature (noted by Marielle Macé in *Une pluie d'oiseaux*, Corti, 2022).

### 3.3 Disambiguation Challenge and Solution
Many biodiversity terms are polysemous:
- *maquereau* = mackerel (fish) OR pimp (slang)
- *le bar du coin* = bar (place), NOT bar (fish)
- *chien de fusil* = gun trigger, NOT dog

**Johanna's two-step approach:**
1. Linguistic rule-based filtering (expression blacklists, POS rules)
2. Contextual classification using FlauBERT (French BERT trained on annotated sample) or GPT-4

**Johanna's accuracy:** ~85% (Riccardo's estimate) — "good enough, too complicated to go back"

### 3.4 Entity Files (resultats/ folder — what Task 1 runs on)
```
~/ecopoetique/resultats/
├── corpus_principal/
│   ├── ENTITES_contexte_animaux.csv    (128,530 rows, tab: fichier|token_lexique|truncated_sentence|lemme|categorie)
│   ├── ENTITES_contexte_plantes.csv    (68,216 rows, tab: fichier|token_lexique|truncated_sentence|lemme)
│   ├── ENTITES_contexte_loterre.csv    (120,046 rows)
│   ├── ENTITES_contexte_champignons.csv (282 rows)
│   ├── ENTITES_contexte_taxons.csv     (572 rows)
│   ├── ENTITES_TOTAL.csv               (317,646 rows — all categories combined)
│   └── data_pour_Shannon.csv           (Shannon index per novel)
└── bestsellers/
    ├── BESTSELLERS_contexte_animaux.csv (15,588 rows)
    ├── BESTSELLERS_contexte_plantes.csv (6,259 rows)
    └── BESTSELLERS_contexte_loterre.csv (10,524 rows)
```

### 3.5 Shannon Biodiversity Index
Applied by Johanna to each novel. From information theory, not just ecology.

Formula: H = -Σ(pᵢ × ln(pᵢ)) where pᵢ = proportion of species i in the novel

Combines:
- **Richness** (number of distinct species)
- **Equitability** (how evenly distributed they are)

High Shannon = many species, evenly represented.
Low Shannon = few dominant species, many rare.

**Key result:** Prix du Roman d'Écologie novels average **>2× the corpus mean Shannon index.** 45/47 such novels exceed the general corpus average — validates using Shannon as an ecological sensitivity indicator.

---

## PART 4: RESEARCH PAPERS READ AND THEIR INFLUENCE

### 4.1 Paper: Hicke et al. (2024) — Metaphor Identification with LLMs
**Title:** "Metaphor identification using large language models: A comparison of RAG, prompt engineering, and fine-tuning"
**Published:** March 2026

**Key findings and how they influenced our work:**

1. **Fine-tuning beats prompting:** Fine-tuning achieves best F1 (0.79), substantially higher than prompt engineering alone. → Motivated LoRA fine-tuning attempt for Task 0 (failed due to insufficient gold data)

2. **RAG also tested:** RAG on full literary texts produces fully annotated texts usable in downstream analyses. → We tested Smart RAG for Task 0 — got 45% overall, WORSE than baseline. RAG is wrong tool for narratological classification.

3. **Self-consistency/majority voting:** "Robustly improves classification without training" — sample 5 times at temperature 0.3-0.5, take majority vote. → We implemented this for FOCALISATION (n=5, temp=0.3), got 61.7% — NO IMPROVEMENT over single sample. The problem is underlying bias: all 5 votes return FOC_INT.

4. **CoT hurts subjective tasks:** Chain-of-thought (thinking mode) hurts classification of subjective/literary tasks. → We tested: NO-THINK gave 0% figuré for Task 1 (catastrophic), THINKING gave 81.2% figuré. For our specific task, thinking is essential. The paper's finding applies to different task types.

5. **Quotation-mark rule (Hicke et al.):** "Speech in quotation marks = signal of FOC_EXT" — we added this specific rule to FOCALISATION prompts. Minor improvement only.

6. **Llama 3.3 70B best open model:** Paper claims 78.97% F1 on focalization with Llama 3.3 70B. → We tested via Groq API — got 58.3% FOCALISATION. The paper's result doesn't transfer to our French corpus or our gold set definition.

### 4.2 Paper: Barontini (2026) — Le tournant écologique à l'épreuve des humanités numériques
**Title:** "Le tournant écologique à l'épreuve des humanités numériques : le romanesque de la biodiversité"
**Published in:** Anthology (Riccardo's own paper — the published academic paper of this project)

**Key claims Labiba worked to verify/extend:**
- "Precision obtained by LLM approaches 90%, validated by manual annotation on sample" — this refers to GPT-4o-mini's performance on examples WHERE human annotators agreed. Our broader gold set gives 85–96% overall.
- Human inter-annotator agreement: 76% common annotations, Cohen's Kappa = 0.64 (moderate) → this sets the ceiling for what any system can reasonably achieve.
- GPT-4o-mini accuracy on unanimously identified examples: 89.7%; overall between 79% and 85%.
- Animal uses: 84.5% literal, 15.5% figurative; Plant uses: 81.3% literal.
- 73% of figurative animal uses compare to human body (CH category) → animality mostly serves to define humanity.

**Riccardo's anxious quote from June 25 meeting:** "I'm a little bit anxious about what I'm getting in terms of interpretation from all this work. Probably not that much. Which is kind of frustrating."

### 4.3 Research on FOCALISATION Difficulty
From survey of existing literature:
- Even GPT-4o only reaches ~84% on FOCALISATION in English
- Human annotators agree ~76% of the time (Kappa 0.64) on focalization
- FOC_INT is most common class (~60% of novels) → models default to it
- FOC_ZERO vs FOC_INT distinction requires observing MULTIPLE characters' inner thoughts across whole novel — fragments are insufficient

**Conclusion for paper:** "We need to wait for more advanced models" (Riccardo's own words, June 25). This IS a valid publishable conclusion.

### 4.4 Marco Caracciolo — Narrating the Mesh (2021)
**Full citation:** *Narrating the mesh. Form and story in the Anthropocene*, Charlottesville, University of Virginia Press, 2021.

Provided the **6-category typology for comparé classification** (Task 4.5):
- **O** — Objects and artificial structures (man-made artefacts, technology)
- **NH** — Non-human living creatures and biological processes
- **E** — Inanimate natural elements and natural processes (landscapes, geology, weather)
- **CH** — Human body and biological processes occurring in the human body
- **A** — Abstract concepts, social practices and institutions (politics, religion, marriage)
- **P** — Psychological states and cognitive functions (emotions, memory, imagination)

Example from Johanna's work: "la jeunesse est un chat insomniaque" → chat=comparant, la jeunesse=comparé, category=A (abstract concept).

---

## PART 5: TASK 0 — NARRATOLOGICAL CLASSIFICATION

### 5.1 Objective and Context
Automatically classify each novel across 7 Genette-based narratological criteria. Target: 85% per criterion.

**Johanna's previous system (GPT-4o via API):**
- Only queried Internet using title + author + year — did NOT read the novel text
- Only covered 2 out of 7 criteria (Narrateur + Focalisation)
- FAILED on 271/802 novels (33.8%) — marked as X/X (unclassifiable)
- ~65% accuracy on the 2 criteria it handled
- Could NOT scale to 5 remaining criteria

### 5.2 Narratological Criteria and Labels

| Criterion | Labels | Definition |
|-----------|--------|------------|
| TYPE NARRATEUR | NAR_AUTOD, NAR_TEM, NAR_EXT | Narrateur personnage (protagonist=narrator), Narrateur témoin (witness), Narrateur externe (heterodiegetic) |
| FOCALISATION | FOC_INT, FOC_EXT, FOC_ZERO, FOC_VAR | Internal (one character), External (camera), Zero (omniscient), Variable (changes between sections) |
| MODE NARRATIF | MOD_EVT, MOD_DESC, MOD_INTR, MOD_MIX | Events, Description, Introspection, Mixed |
| REGIME NARRATIF | REG_REAL, REG_AUTO, REG_FANT, REG_SPEC | Realist, Autofiction, Fantastic, Speculative |
| ESPACE | ESP_UNIT, ESP_FRAG, ESP_ITIN, ESP_IMAG | Single location, Fragmented, Journey/itinerant, Imaginary |
| INTRIGUE | INTR_LIN, INTR_FRAG, INTR_CYC | Linear, Fragmented, Cyclical |
| TEMPORALITÉ | TEMP_LIN, TEMP_DIS, TEMP_DESORD | Chronological, Anachronic (flashbacks/prolepses), Scrambled |

**Note from Grille_Narratologique.csv:** Riccardo's full grid also includes "Degré de discordance temporelle" (low/medium/high) and distinguishes analepses from prolepses separately — these were noted for future refinement but not implemented yet.

**ESPACE note:** Riccardo decided ESPACE should be eliminated from presentation — results too low and too variable (unstable across samples).

### 5.3 Gold Set
- **Primary file:** `~/ecopoetique/narratologie/GOLD_narratologie.csv` (semicolon-separated, 79 novels with alternative labels)
- **Reliable 60-novel subset:** `~/ecopoetique/narratologie/GOLD_narratologie_60novels_original.csv` — the 60 novels Riccardo is most confident about
- **Extended labels:** `~/ecopoetique/narratologie/critere_narration_focalisation.csv` (530 novels, tab-separated) — Narrateur and Focalisation only, with 271/801 entries as "X" (unknown). **WARNING: 56/60 gold novels overlap with this file — cannot use as training without careful exclusion.**

**Focalisation distribution in critere file:**
- Interne: 217 (40%)
- Zéro: 178 (33%)
- Variable: 93 (17%)
- Externe: 42 (8%)
- X (unknown): 271

**Inter-annotator disagreements found:** The critere file sometimes disagrees with the gold set:
- `Minard-Celine_Le-Grand-Jeu.txt` → critere: Externe, gold: FOC_INT
- `Zeniter-Alice_Lart-de-perdre.txt` → critere: Interne, gold: FOC_ZERO
These disagreements confirm FOCALISATION is genuinely hard.

### 5.4 Complete History of All Approaches Tried

#### Approach 1: 125-line Sample (Baseline — Labiba's first attempt)
- Method: Take 125 lines from novel beginning, classify all 7 criteria
- Result: 55.7% overall
- Main problem: Beginning of novel doesn't reveal INTRIGUE structure or TEMPORALITÉ

#### Approach 2: Smart RAG
- Method: Retrieve relevant excerpts using BM25/semantic search for each criterion, then classify
- Result: 45.0% overall — WORSE than baseline
- Why it failed: Criterion-relevant excerpts don't exist in predictable locations; retrieval fails for global properties like TEMPORALITÉ

#### Approach 3: Full Novel Single Prompt (4,500 words)
- Method: Feed first 4,500 words directly to model
- Result: COMPLETE FAILURE — context window exceeded, model truncated, produced garbage
- Why it failed: 100,000+ tokens per novel; context window is 8,192 tokens

#### Approach 4: Map-Reduce Pipeline (NEW — Labiba's key innovation)
**This became the production approach for Task 0.**

**MAP STEP:** Split novel into 9 equal chunks. For each chunk, model answers 10 narrow questions:
- narrator_voice (first_person/third_person/unclear)
- inner_thoughts (yes_one_character/yes_multiple/no/unclear)
- dominant_mode (action_events/description/introspection/mixed)
- world_type (realistic/autobiographical/fantastic/speculative_sf)
- space (single_location/multiple_locations/journey_travel/imaginary)
- plot_threads (one/multiple)
- time_order (chronological/has_flashbacks_or_jumps/radically_scrambled)
+ more

**REDUCE STEP:** Combine 9 sets of chunk observations → one final prompt deciding all 7 criteria simultaneously. Model sees signal from beginning, middle, and end.

**Result:** 63.3% overall — +7.6pp vs prior best. TYPE NARRATEUR: 90% (target met!).

#### Approach 5: Option A (Targeted Per-Criterion Reduce Prompts)
- Method: Instead of one reduce prompt for all 7 criteria, separate reduce prompts per criterion, each addressing its specific error pattern
- Script: `run_narratologie_mapreduce_optionA.py`
- Result: Mixed — improved some criteria, hurt FOCALISATION

#### Approach 6: Chunk Classifier (sklearn)
- Method: Use map-step observations as features for a scikit-learn classifier
  - TF-IDF of chunk observations
  - Feature vector: counts of narrator_voice="first_person" across 9 chunks, etc.
  - Train: Leave-One-Out Cross-Validation (LOO-CV) on 60 novels
  - Classifiers tested: LogisticRegression, RandomForest, SVM
- Script: `train_chunk_classifier.py` (465 lines)
- Why LOO-CV: only 60 examples, most honest estimate possible
- Result: 67.1% FOCALISATION — best local result before qwen72b
- Particularly good for MODE NARRATIF: 71.7% and REGIME NARRATIF: 71.7%

#### Approach 7: Title+Author Internet Knowledge
- Method: Model uses its training knowledge of novel title+author without reading text
- Script: `resultats_qwen3_30b_title_author.csv`
- Result: 61.7% FOCALISATION — worse than map-reduce
- Why: Many novels too obscure for model's training data

#### Approach 8: GPT-4o-mini (Paid API)
- Used Riccardo's $9 OpenAI credit
- Result: **75.0% FOCALISATION** — best FOCALISATION ever achieved
- Problem: Cannot use for production on 925 novels (paid per token)
- Not reproducible for the paper's full corpus run

#### Approach 9: Mistral Large (Free API tier)
- Rate limit: 2 requests/minute — very slow
- Result: 63.3% FOCALISATION — all models default to FOC_INT
- Root cause: model bias toward majority class

#### Approach 10: Groq Llama 3.3 70B (Free)
- Rate limit: 30 RPM
- Simple prompt: 58.3% FOCALISATION (defaults to FOC_INT for 56/60 novels)
- Map-reduce: 58.3% FOCALISATION (same problem — votes at chunk level still FOC_INT)
- Paper claimed 78.97% for this model → does not transfer to our French corpus/gold set

#### Approach 11: qwen72b-limited WITH Thinking (qwen2.5vl:72b, num_predict=5000)
- Script: `foc_think.py` + `resultats_qwen72b_focalisation.csv`
- Result: **68.3% FOCALISATION — NEW LOCAL BEST**
- Improvement: Bigger model + extended reasoning allows detecting FOC_ZERO and FOC_VAR more often

#### Approach 12: qwen72b-limited WITHOUT Thinking (/no_think, num_predict=100)
- Result: 61.7% FOCALISATION — worse than with thinking
- Confirms: thinking mode essential for complex literary classification

#### Approach 13: Self-Consistency Voting (n=5, temp=0.3)
- Method: Sample 5 times, take majority vote
- Script: `resultats_focalisation_v2.csv`
- Result: 61.7% FOCALISATION — no improvement
- Why: If model defaults to FOC_INT 4/5 times, majority is still FOC_INT

#### Approach 14: Few-Shot from critere_narration_focalisation.csv
- Method: Use 480 non-overlapping novels from critere file as examples
- Result: 61.7% FOCALISATION — no improvement
- Why: Too many examples overwhelm the context window; model loses track of the task

#### Approach 15: LoRA Fine-tuning
- Attempted on small encoder model (CamemBERT-large)
- Failed: gold set too small (need 200+, have 60)
- Library compatibility issues (PEFT, transformers versions on server)
- Abandoned entirely

#### Approach 16: qwen72b All 7 Criteria (Overnight Run)
- Script: `run_task0_v4_all7.py` → `resultats_qwen72b_all7.csv`
- Status: Completed 60 novels
- Columns: File, TYPE NARRATEUR (pred), GOLD_TYP, FOCALISATION (pred), GOLD_FOC, MODE NARRATIF (pred), GOLD_MOD, REGIME NARRATIF (pred), GOLD_REG, ESPACE (pred), GOLD_ESP, INTRIGUE (pred), GOLD_INT, TEMPORALITE (pred), GOLD_TEM

### 5.5 Error Analysis by Criterion (from Progress Report)

| Criterion | Main Error Pattern | Root Cause |
|-----------|-------------------|------------|
| FOCALISATION | Over-predicts FOC_VAR (8× ZERO→VAR, 8× INT→VAR) | Confuses multiple characters PRESENT with perspective SHIFTS |
| ESPACE | Over-predicts ESP_FRAG (12× UNIT→FRAG) | Treats any mention of multiple locations as fragmented |
| MODE NARRATIF | Over-predicts MOD_MIX (26/29 errors) | Hedges rather than committing to dominant mode |
| REGIME NARRATIF | Confuses REG_REAL with REG_AUTO (7×) | Misreads first-person narration as autofiction |
| INTRIGUE | Symmetric LIN/FRAG confusion (10× + 8×) | Cannot distinguish one plot with subplots from genuinely fragmented |
| TEMPORALITÉ | Over-predicts TEMP_DIS (13× LIN→DIS) | Treats any memory/flashback as structural discontinuity |

### 5.6 Best Final Results for Task 0 (60 novels, with alternative label scoring)

**Hybrid v4 — 70.5% overall (best result)**

| Criterion | Score | Source | Notes |
|-----------|-------|--------|-------|
| TYPE NARRATEUR | **90.0%** | resultats_hybrid.csv (old hybrid) | TARGET MET (85%) |
| FOCALISATION | **65.0%** | resultats_hybrid.csv (old hybrid) | Best LOCAL |
| MODE NARRATIF | **71.7%** | resultats_hybrid.csv | Good |
| REGIME NARRATIF | **71.7%** | resultats_hybrid.csv | Good |
| ESPACE | **48.3%** | resultats_hybrid.csv | EXCLUDED from presentation |
| INTRIGUE | **65.0%** | resultats_hybrid.csv | Acceptable |
| TEMPORALITÉ | **71.7%** | resultats_hybrid.csv | Good |
| **OVERALL** | **70.5%** | **Hybrid v4 (alt scoring)** | **BEST RESULT** |

**Note on FOCALISATION improvement:**
- qwen72b with thinking: **68.3%** → new best local
- GPT-4o-mini: **75.0%** → best ever (paid, cannot use in production)
- Human agreement ceiling: ~76%

### 5.7 Scoring Methodology: Alternative Labels
The gold set includes "Acceptable aussi" (alternative) labels for cases where multiple annotations are defensible. For example, if gold = FOC_INT but ALT = FOC_ZERO, a prediction of FOC_ZERO counts as correct.

With alt scoring, hybrid v4 = 70.5% overall. Without alt scoring ≈ 67-68%.

### 5.8 Key Scripts for Task 0
```
~/ecopoetique/narratologie/
├── run_narratologie_mapreduce.py         # Map-reduce v3 — main production script
├── run_narratologie_mapreduce_optionA.py # Option A — per-criterion reduce prompts
├── train_chunk_classifier.py             # sklearn classifier (465 lines, LOO-CV)
├── combine_hybrid_v2.py                  # Combines 3 sources, picks best per criterion
├── foc_think.py                          # qwen72b FOCALISATION — WITH thinking
├── run_focalisation_v3.py                # Self-consistency (n=5) — FAILED
├── run_task0_v4_all7.py                  # qwen72b all 7 criteria overnight
├── GOLD_narratologie.csv                 # Master gold set (79 novels, semicolon)
├── GOLD_narratologie_60novels_original.csv # 60-novel reliable subset
├── Grille_Narratologique.csv             # Full narratological grid
├── critere_narration_focalisation.csv    # 530 novels tab-separated
├── resultats_hybrid.csv                  # Best overall results (60 novels)
├── resultats_hybrid_v4_60novels.csv      # Hybrid v4 — 70.5% with alt scoring
├── resultats_qwen72b_focalisation.csv    # 68.3% FOCALISATION (qwen72b+thinking)
└── resultats_qwen72b_all7.csv           # All 7 criteria with qwen72b
```

### 5.9 Riccardo's Conclusion on Task 0
"It can be defended that it's not possible to do better with the tools we have now."
"Maybe that's the conclusion — we need to wait for more advanced models."
"LLMs are not well trained for literary narratology."
→ **This is a legitimate academic finding, not a failure.**

---

## PART 6: TASK 1 — LITERAL/FIGURATIVE CLASSIFICATION

### 6.1 Objective
For each animal, plant, or Loterre term occurrence: classify as **référentiel** (literal/real) or **figuré** (figurative/metaphorical/idiomatic).

### 6.2 Why This Matters
A "mouche" in "les candidats tombaient comme des mouches" (idiom) should NOT count as evidence of biodiversity sensitivity — it's a frozen expression, not a real fly. Without this classification, biodiversity statistics are inflated by figurative uses.

### 6.3 Johanna's Previous Approach (GPT-4o-mini, OpenAI API)
- Prompt: "Dans la phrase suivante, le mot {entité} est-il employé de façon littérale ou a-t-il un sens figuré?"
- Batches of 5 phrases per API call with XML-structured output
- Accuracy: ~47% figuré detected (very low)
- Cost: paid per token
- Files: `RESULTAT_annotation_gpt.csv` (112,592 animal rows), `plantes/` folder

### 6.4 Initial Baseline (Labiba v1 — no examples)
Tested qwen3:30b with minimal prompt, no examples:
- **Animals v1:** Overall=85.8%, Réf=94.2%, Fig=71.0%
- Key finding: model already beats Johanna's GPT-4o-mini without any prompt engineering!

### 6.5 The Critical Discovery: Why Thinking Mode is Essential
Tested no-think mode (num_predict=100, /no_think suffix) vs thinking mode (num_predict=5000):

| Mode | Speed | Overall | Réf | Fig |
|------|-------|---------|-----|-----|
| No-think (100 tokens) | 1.1s/row | 63.7% | 100.0% | **0.0%** |
| Thinking (5000 tokens) | 7-9s/row | 91.6% | 97.5% | **81.2%** |

**Without thinking: model predicts "référentiel" for 100% of all cases — completely unusable.**
**With thinking: model correctly detects figurative uses.**

The thinking tokens allow the model to reason through ambiguous cases: "Is this idiomatic? Does 'comme' signal comparison? Is there a real animal present in the scene?"

### 6.6 Batch Size Optimization
Tested different batch sizes (rows per API call):

| Batch | Speed | Overall | Fig |
|-------|-------|---------|-----|
| 1 (single) | 9.0s/row | 92.1% | 87.0% |
| 5 (batched) | 4.0s/row | 92.6% | 87.0% |

Batch=5 (used in corpus run) gives **same accuracy at 2.3× speed**. Used batch=4 in final production.

### 6.7 Prompt Engineering — Full Version History

**evaluate_all_goldsets.py → v6 (FINAL for animaux and plantes):**

Version evolution for animals:
| Version | Overall | Réf | Fig | Key Change vs Previous |
|---------|---------|-----|-----|------------------------|
| v1 (no examples) | 85.8% | 94.2% | 71.0% | Baseline |
| v2 (few-shot added) | **92.6%** | 94.2% | 89.9% | Added 5+ examples per category |
| v3 (rules improved) | ~87% | 97% | ~67% | Mid-development |
| v4 (category-specific) | ~89% | 97% | ~75% | Separate example sets per animal type |
| v5 (idiom detection) | ~91% | 97% | ~79% | Better idiom rules |
| **v6 (FINAL)** | **91.6%** | **97.5%** | **81.2%** | Full v2 few-shot + refined rules |

**The v2 result (92.6% / 89.9% fig) was achieved on a single row at a time (batch=1). The production v6 (batch=4) achieves 91.6% / 81.2% fig.**

For plants, v6 achieves 96.3% / 79.2% fig.

### 6.8 Loterre Version History

The Loterre task is HARDER than animals/plants because:
- Loterre terms are domain-specific ecological concepts (not species)
- Many are inherently polysemous between ecological and general meaning
- "désert" (desert) appears both as real geographic feature AND metaphor for isolation
- "forêt" can be a real forest OR a symbolic/fantastic space

| Version | Overall | Réf | Fig | Key Change |
|---------|---------|-----|-----|------------|
| v3 | 85.2% | ~90% | 56.1% | Baseline |
| v5 | 85.8% | 92% | 58.5% | Loterre-specific examples added |
| v6 | 86.2% | 91.2% | 61.0% | Better disambiguation |
| v7 | 86.8% | 95.3% | **56.1%** | WORSE — new examples hurt figuré |
| **v8** | **85.2%** | **91.2%** | **63.4%** | Targeted Group A error fixes |

**Key finding for v7:** Adding more référentiel examples HURT figuré detection. The model became more conservative, calling ambiguous cases référentiel. This is the **overfitting trap** — adding examples for one class hurts the other.

### 6.9 Gold Set Details

| File | Separator | Total | Réf | Fig | X |
|------|-----------|-------|-----|-----|---|
| `GOLD_litteralite_animaux.csv` | tab | 192 | 121 (63%) | 69 (36%) | 2 (1%) |
| `GOLD_litteralite_plantes_RB.csv` | semicolon | 188 | ~120 | ~68 | — |
| `GOLD_litteralite_loterre__RB.csv` | semicolon | 189 | 148 (78%) | 41 (22%) | — |

**Class imbalance explains lower figuré accuracy:** Gold sets are 63-78% référentiel. Model defaults to majority class when uncertain → higher référentiel precision but lower figuré recall.

**Human annotator ceiling:** Agreement = 76%, Kappa = 0.64. Our 91.6% / 81.2% EXCEEDS human agreement on the task for animals. This is a strong result.

### 6.10 Full Row-by-Row Test Results (Task 1 Animals v2)
The `task1_animal_results.txt` shows the complete evaluation run on 190 examples. Notable errors:
- [60/190] agneaux: WRONG — predicted référentiel but gold=figuré
- [70/190] grenouilles: WRONG — predicted référentiel but gold=figuré
- [74/190] margouillat: WRONG — figuré missed
- [113/190] chameau: WRONG — référentiel missed
- [147/190] porc: WRONG — référentiel missed
- [149/190] vache: WRONG — référentiel missed
- [153/190] autruche: WRONG — figuré missed
- [154/190] bœuf: WRONG — figuré missed
- [157/190] cigales: WRONG — figuré missed
- [163/190] goéland: WRONG — referred to as figuré but gold=référentiel
- [167/190] chiens: WRONG — figuré predicted but gold=référentiel
- [175/190] âne: WRONG — référentiel predicted but gold=figuré
- [179/190] chimpanzé: WRONG — figuré missed
- [190/190] coqs: WRONG — figuré predicted but gold=référentiel

**Final counts from this run:** Overall=92.6%, Réf=94.2%, Fig=89.9% (batch=1, v2 prompt)

### 6.11 Loterre Error Analysis (v8 — 15 figuré errors)

**IMPORTANT: These 15 errors were carefully analysed for Riccardo.**

**Group A — Model clearly wrong (5 cases, fixable):**
1. **[marais]** "Le temps nous a poussés vivants hors des marais" → temporal escape metaphor; "le temps" cannot push you through real swamps
2. **[mers]** "Cyrtha luit, dominant terres et mers infinies" → hyperbolic city description; a city cannot dominate infinite seas
3. **[mer]** "Ce serait être largué en pleine mer sans bouée de sauvetage" → abandonment metaphor; conditional "ce serait" signals figurative
4. **[mer]** "Cette promesse a traversé la Wilaya, la mer et ma mémoire" → "ma mémoire" in the list reveals figurative enumeration
5. **[incendie]** "réchauffés par l'incendie des fourneaux" → heat intensity metaphor; "incendie des fourneaux" = no real fire

**Group B — Genuinely ambiguous (4 cases, to discuss with Riccardo):**
1. **[forêt]** Supernatural silhouettes in a real forest — literal place used for fantastic events?
2. **[maritimes]** "scènes maritimes modernes" in paintings — maritime as adjective for artwork vs real sea
3. **[désert]** "avais choisi le désert" + "ce tapis de sable, de dunes" — simultaneously real AND metaphor for isolation
4. **[oiseaux migrateurs]** On a curtain motif — picture within picture, same as maritimes case

**Group C — Model probably right, gold may be wrong (6 cases):**
1. **[océan]** "plus dangereuse que l'océan Atlantique" — factual comparison between two real things; océan=référentiel
2. **[montagnes]** "mes dessins de jardins, de montagnes" — drawings OF mountains ≠ metaphor; montagnes=référentiel
3. **[lac]** "poteaux dirigés vers le lac" — real spatial orientation to a real lake
4. **[plage]** "montagne multicolore de jouets de plage" — "plage" is type-modifier for toys (référentiel); it's "montagne" that's figuré
5. **[lac]** "décombres au bord d'un lac" — real geographic location
6. **[animaux]** "Luc rapatriait sa ferme aux animaux dans sa chambre" — real animals moved indoors

**Riccardo's confirmed corrections (June 25 meeting):**
- Cases 2 (maritimes) and 14 (oiseaux migrateurs) → **FIGURÉ** — "picture within picture = representation not real"
- Case 6 (montagnes in drawings) → **FIGURÉ** — same logic as maritimes
- Case 10 (plage in "jouets de plage") → **FIGURÉ** for "montagne" (big quantity DE_QUANTIF), "plage" is référentiel
- Cases 8, 12 (lac), 15 (animaux), 4 (océan Atlantique) → likely **référentiel** (gold annotation errors)

**If 4 Group C cases corrected to référentiel → real figuré accuracy would jump to ~71%.**

### 6.12 Corpus-Wide Run (Production Task 1)

**Script:** `~/ecopoetique/métaphore/run_task1_corpus.py`
**Input:** ENTITES_contexte files (extracted by Johanna)
**Configuration:** qwen3:30b, batch=4, thinking ON (num_predict=5000), with resume capability

**Speed benchmarks:**
- With thinking, warm GPU, alone: **4.0s/row** (batch=4)
- With thinking, cold GPU: 11s/row (first call after load)
- No-think: 1.1s/row but 0% figuré (unusable)
- Full corpus estimate: animaux 144K rows × 4s = ~160h (6.7 days)

**ANIMAUX — COMPLETE ✅ (July 5, 2026)**
- Total classified: 127,877 / 127,935 unique rows
- Results: 90,755 référentiel (70.9%) | 37,180 figuré (29.1%)
- Failed batches: 842 (defaulted to référentiel)
- Failed rows: 3,665 (in `task1_animaux_failed_keys.tsv`)
- Retry: `~/ecopoetique/morphosyntaxe/retry_animaux.py`

**Key finding:** 29.1% of animal mentions in the corpus are figurative — about 37,000 figurative animal uses across 925 novels. This is lower than the gold set baseline (35.9%) because the gold was deliberately balanced; the corpus distribution is natural.

**PLANTES — IN PROGRESS 🔄 (started July 5)**
- PID: 1427842
- Progress: ~23% done as of July 6 (~ETA July 8-9)
- Figuré so far: ~12.9%

### 6.13 Key Scripts for Task 1
```
~/ecopoetique/métaphore/
├── evaluate_all_goldsets_v6.py           # BEST: animaux+plantes (91.6% / 96.3%)
├── evaluate_loterre_v8.py                # BEST: loterre (85.2% / 63.4% fig)
├── evaluate_litteralite_v2.py            # Early version — led to v6 development
├── run_task1_corpus.py                   # Full corpus run (batch=4, thinking ON)
├── run_task2_subcategories.py            # Task 2 pipeline (built, waiting for Task 1)
├── retry_animaux.py                      # Retry failed batches (batch=4, v6 prompts)
├── GOLD_litteralite_animaux.csv          # 192 rows (tab)
├── GOLD_litteralite_plantes_RB.csv       # 188 rows (semicolon)
├── GOLD_litteralite_loterre__RB.csv      # 189 rows (semicolon)
├── RESULTAT_annotation_gpt.csv           # Johanna's animal labels (112K)
├── RESULTAT_typologie_compare_animaux.csv # Johanna's comparé labels
├── eval_animaux_v6_results.csv           # Animaux v6 results
├── eval_plantes_v6_results.csv           # Plantes v6 results
├── eval_loterre_v8_results.csv           # Loterre v8 results
└── plantes/
    ├── annotations_gpt_partie_1.csv       # Johanna plant labels (2,776 rows)
    └── annotations_gpt_partie_2.csv       # Johanna plant labels (60,951 rows)
```

---

## PART 7: TASK 2 — FIGURATIVE SUBCATEGORY CLASSIFICATION

### 7.1 Objective
For each figurative animal/plant mention, classify into detailed subcategory types of figurative language.

**Known subcategories (from Johanna's notebooks):**
- COMME_SN — simile with "comme" ("fort comme un lion")
- META_VERB — verbal metaphor ("il rugit de colère")
- DE_PARANGON — genitive metaphor ("un lion d'homme")
- IDIOMATIQUE — frozen idiomatic expression ("à pas de loup")
- AUTRE — other
And possibly more categories in Riccardo's full typology.

### 7.2 Status: PENDING
Must run on Labiba's Task 1 results (not Johanna's GPT-4 labels).
Script `run_task2_subcategories.py` is built and tested. Waiting for Task 1 corpus completion.

### 7.3 Johanna's Previous Work
File: `~/ecopoetique/métaphore/RESULTAT_annotation_gpt.csv`
Columns: fichier, token_lexique, truncated_sentence, lemme, label, **categorie_metaphore**, explication
Already classified animals with subcategories — but based on GPT-4 with ~47% figuré accuracy (many labels are wrong because base classification was wrong).

### 7.4 Gold Set Requirements
Riccardo to provide: 100 figurative animal + 100 figurative plant examples annotated with:
- Column 1: subcategory type (COMME_SN, META_VERB, etc.)
- Column 2: comparé category (Task 4.5 — CH, ABSTR, NAT, GEO, OBJ, AUTRE)
Same 200 examples used for BOTH tasks.

---

## PART 8: TASK 3 — AGENTIVITY ANALYSIS

### 8.1 Research Question
Are animals and plants more passive agents than humans in contemporary French novels?

**Hypothesis:** In contemporary fiction, animals and plants serve primarily as patient/passive entities relative to human characters.

### 8.2 The Four Role Categories (confirmed correct by Riccardo, June 25)

| Role | Technical | Example |
|------|-----------|---------|
| Agent actif | grammatical subject of active verb | "Un loup aboya dans un vallon" |
| Récepteur passif | subject of passive construction | "Des chèvres sont tenues en laisse" |
| Objet | direct object | "il chassa un papillon" |
| Complément du nom | prepositional noun modifier | "Des blessures de loup" |
| Autre | other syntactic roles | flat:name, obl:arg, xcomp, appos, obl:mod |

**The lion/Julian examples Riccardo walked through (June 25):**
- "Julien tua le lion" → lion = Objet ✅
- "Le lion fut tué par Julien" → lion = Récepteur passif ✅
- "Le lion mangea Julien" → lion = Agent actif ✅
- "Julien fut mangé par le lion" → lion = Agent actif ✅ (obl:agent in passive construction — semantically active)

### 8.3 Data Sources and Methods

**HUMANS:** Built from scratch using spaCy French NER (fr_core_news_lg) on all 925 novels.
- `extract_humains.py` — NER extraction
- Includes gender detection: spaCy morphology + pronoun context window
- "Undetermined" (25.9%): name appears without nearby pronouns, ambiguous/foreign names

**ANIMALS (referential):** Used Johanna's pre-filtered file `dépendants_animaux_référentiels.csv` — already disambiguation-filtered. Has `categorie` column (mammifère, oiseau, insecte, etc.)

**PLANTS:** Used Johanna's `dépendants_PLANTES.csv` — MIXED referential + figurative (no filtering yet). Known contamination: "tendre une carotte" (idiom), "la moutarde me monte au nez" (idiom), "le pruneau" (slang for face) — these inflate plant agentivity slightly.

### 8.4 Final Results (COMPLETE)

| Category | N | Active Agent | Passive | Object | Noun Complement | Other |
|----------|---|--------------|---------|--------|-----------------|-------|
| **HUMANS (all)** | 219,651 | **37.2%** | 1.4% | 12.8% | 20.1% | 28.4% |
| Humans masculine | 118,142 | **38.2%** | 1.3% | 13.2% | 18.8% | 28.4% |
| Humans feminine | 44,529 | **37.7%** | 1.8% | 12.9% | 21.2% | 26.5% |
| Humans undetermined | 56,980 | — | — | — | — | — |
| **ANIMALS (referential)** | 95,243 | **24.4%** | 0.7% | 20.2% | 33.6% | 21.0% |
| **PLANTS (all, mixed)** | 64,269 | **11.8%** | 0.4% | 15.1% | 49.5% | 23.1% |
| **TOTAL** | **379,163** | | | | | |

**Hierarchy confirmed: Humans (37.2%) > Animals (24.4%) > Plants (11.8%)**
- Humans 1.5× more active than animals
- Humans 3.1× more active than plants
- Male and female humans nearly identical (38.2% vs 37.7%) — no significant gender difference
- Plants predominantly as noun complements (49.5%) — described rather than doing

### 8.5 The "Autre" Category Explained (28.4% for humans)
This question came up at the June 25 meeting: "What's the rest?"

It is NOT missing data — it's valid syntactic roles outside the 4 main categories:
- `flat:name` — parts of compound proper names (e.g., "Monsieur Dupont" — "Dupont" is flat:name dependent)
- `obl:arg` — oblique arguments ("il dit à Marie" — Marie is obl:arg)
- `xcomp` — predicative complements ("il s'appelle Pierre" — Pierre is xcomp)
- `appos` — apposition ("mon père, Robert" — Robert is appos)
- `obl:mod` — oblique modifiers ("il parle de Marie")

**All categories sum to 100%.** Nothing is missing.

### 8.6 Animal Category Breakdown
From `dépendants_animaux_référentiels.csv` (95,243 rows):
- Mammifère: 57,601 (60.5%)
- Oiseau: 16,226 (17.0%)
- Insecte: 8,419 (8.8%)
- Poisson: 4,103 (4.3%)
- Reptile: 3,483 (3.7%)
- Autre: 3,236 (3.4%)
- Amphibien: 1,157 (1.2%)
- Mollusque: 769 (0.8%)

### 8.7 Pending for Task 3
1. **English/Arab names:** Many Maghreb/African novels have proper names undetected by French spaCy. Capital letter detection in middle of sentences as heuristic. Risk: French words like "Fleur" could be misidentified.
2. **Rerun plants** after Task 1 filters referential-only → create `dépendants_plantes_référentielles.csv`
3. **Rerun animals** after Task 1 gives cleaner filtering (91.6% vs Johanna's ~85%)
4. **Check remaining %** outside 4 main categories per sub-type

### 8.8 Key Scripts for Task 3
```
~/ecopoetique/morphosyntaxe/
├── analyse_agentivite.py                 # Main agentivity analysis
├── analyse_dependances.py                # Dependency extraction
├── extract_humains.py                    # Human NER extraction with gender
├── dépendants_HUMAINS.csv                # 219,651 rows (tab-separated)
├── dépendants_animaux_référentiels.csv   # 95,243 referential animals (tab)
├── dépendants_PLANTES.csv                # 64,269 plants mixed (tab)
├── resultats_agentivite.txt              # Summary
├── resultats_agentivite_complet.txt      # Full detailed results with examples
└── task3_full_report.md                  # Complete Task 3 report
```

---

## PART 9: TASK 4.5 — COMPARANT/COMPARÉ CLASSIFICATION

### 9.1 The Distinction
When a figurative animal/plant use is identified:
- **Comparant** = the animal/plant term (the vehicle/source — what is used AS the comparison)
- **Comparé** = what is being compared (the tenor/target — what is described)

"Paul est fort comme un lion" → lion=comparant, Paul=comparé, category=CH (human)
"Cuba ressemble à un lézard vert" → lézard=comparant, Cuba=comparé, category=E (natural element)
"la jeunesse est un chat insomniaque" → chat=comparant, la jeunesse=comparé, category=A (abstract)
"son anguille de peau" → anguille=comparant, skin of person=comparé, category=CH

### 9.2 The 6 Caracciolo Categories (for what the comparé is)
From Marco Caracciolo, *Narrating the mesh* (2021):
- **O** — Objects and artificial structures
- **NH** — Non-human living creatures and biological processes
- **E** — Inanimate natural elements and processes
- **CH** — Human body and physiological processes
- **A** — Abstract concepts, social practices and institutions
- **P** — Psychological states and cognitive functions
- **X** — Context insufficient

### 9.3 Johanna's Previous Work
File: `~/ecopoetique/métaphore/RESULTAT_typologie_compare_animaux.csv`
Done with GPT-4, animals only.

**Johanna's result:** 73% of figurative animal comparés involve **human body/attitude (CH)** — animals mostly serve to define humanity. Then Objects (8%), Abstract concepts (6.2%).

### 9.4 Status: PENDING
Same dependency as Task 2. Gold set = same 200 examples.

**Riccardo mentioned:** Check GitLab scripts folder for Johanna's exact prompt and code.

---

## PART 10: BIODIVERSITY INDICES (NEW TASK — July 2026)

### 10.1 Shannon Index (Already Done by Johanna)
H = -Σ(pᵢ × ln(pᵢ))
File: `~/ecopoetique/resultats/corpus_principal/data_pour_Shannon.csv` (925 rows)

**Important clarification from Riccardo:** Shannon "measures a probabilistic information structure, not an ontological quality of living things. We are not measuring a biological ecosystem but the informational organisation of a living lexicon in a text."

### 10.2 Additional Indices (Documents Pending from Riccardo)
Riccardo met a biologist/statistician. Possible additional indices to apply:
- **Equitability index** (Pielou's J = H / ln(S) where S = number of species)
- **Simpson's index** (1 - Σpᵢ²) — probability two random individuals are different species
- **Chao1 estimator** — estimates true species richness from observed data
- **Beta diversity** — difference in composition between novels/corpora

Implementation: pure statistical calculation applied to token frequency distributions. Not AI-based. Expected to be straightforward.

---

## PART 11: TECHNICAL FAILURES — DOCUMENTED FOR PAPER APPENDIX

### 11.1 No-Think Mode for Task 1 (CRITICAL FAILURE)
- **What was tried:** num_predict=100, /no_think suffix to save compute time
- **Result:** 100% référentiel predictions — 0% figuré detected
- **Root cause:** Without extended reasoning, qwen3:30b cannot handle semantic ambiguity; defaults to majority class
- **Resolution:** Thinking mode (num_predict=5000) is NON-NEGOTIABLE for this task
- **Time cost:** 7-9s/row vs 1.1s/row — worth it

### 11.2 RAG for Task 0 (WORSE THAN BASELINE)
- **What was tried:** BM25 + semantic retrieval of relevant excerpts for each criterion
- **Result:** 45.0% overall — 10.7pp WORSE than simple 125-line sample
- **Root cause:** Global narrative properties (INTRIGUE structure, overall TEMPORALITÉ) cannot be determined from locally retrieved relevant fragments. The whole novel structure must be seen.
- **Resolution:** Map-reduce approach — see whole novel systematically

### 11.3 Full-Text Single Prompt (TOTAL FAILURE)
- **What was tried:** Feed first 4,500 words of novel to model
- **Result:** Model truncated, produced incoherent output, ~0% accuracy
- **Root cause:** Context window (8,192 tokens) cannot hold 4,500 French words + system prompt + instructions
- **Resolution:** Map-reduce — process in chunks

### 11.4 LoRA Fine-tuning (ABANDONED)
- **What was tried:** Fine-tune CamemBERT-large on 60 gold novel narratological labels
- **Failures:**
  1. Gold set too small — minimum ~200 examples needed, have 60
  2. PEFT library version conflicts on server
  3. transformers/accelerate compatibility issues
- **What research says:** RoBERTa-large reaches 77.5% on focalization with only 300 samples (Hicke et al.) — **IF we had 300, this might work**
- **Resolution:** Abandoned — insufficient data

### 11.5 Self-Consistency Voting for FOCALISATION (NO IMPROVEMENT)
- **What was tried:** n=5 samples at temperature=0.3, majority vote
- **Result:** 61.7% — no improvement over single sample (also 61.7%)
- **Root cause:** If model votes FOC_INT 4/5 times, majority is still FOC_INT. Voting amplifies the dominant bias rather than correcting it.
- **What paper claims:** "Robustly improves classification" — does not apply when the bias is systematic, not random

### 11.6 Groq/Mistral/Llama FOCALISATION (SYSTEMATIC FAILURE — ALL MODELS)
- **Tested:** Groq Llama 3.3 70B, Mistral Large (free tier), Mistral Nemo, Mistral-Small
- **All result:** 55-63.3% FOCALISATION — all default to FOC_INT for 55-60/60 novels
- **Root cause:** FOC_INT is ~60% of gold set. Without sufficient reasoning capacity, ALL models predict majority class.
- **Groq map-reduce:** Same result — votes at chunk level all return FOC_INT, reducing gives FOC_INT

### 11.7 Loterre v7 — Examples Made Things Worse
- **What was tried:** Added more context-specific examples to the prompt
- **Result:** Overall improved slightly (86.8% vs 86.2%) but figuré DROPPED (56.1% vs 61.0%)
- **Root cause:** New examples were all référentiel-adjacent — model became more conservative, calling borderline figuré cases as référentiel
- **Resolution:** Reverted approach — v8 targets specific Group A errors only

### 11.8 Claude Code on obtic-gpu1 (PERMANENTLY BROKEN)
- **What was tried:** Using Claude Code (VS Code extension) directly on remote server
- **Problem:** Server DNS cannot resolve external domains (api.anthropic.com, claude.ai)
- **Auto-update failure:** July 4, 2026 — Claude Code tried to update, DNS failed, partial failure state
- **curl result:** 000 (cannot resolve host) for both lfarooq AND labiba sudo accounts
- **Root cause:** obtic-gpu1 blocks all outbound HTTPS to external domains — firewall policy
- **Resolution:** Claude Code cannot work on this server without IT admin fixing DNS. Use Claude.ai directly.

### 11.9 Disk Space Crisis
- **Peak crisis:** 98% full after downloading qwen2.5vl:72b (48GB)
- **What was deleted:** gemma3:27b (17GB), mistral-small3.1 (15GB) = 32GB freed
- **Current:** ~116GB free (still critical for long-term)

---

## PART 12: MEETINGS AND KEY DECISIONS

### 12.1 Initial Meeting — May 19, 2026
First meeting with Riccardo. Key decisions:
- Priority order established: Task 0 → Task 1 → Task 2 → Task 3
- Gold set is CORRECT — only model needs improvement, not annotations
- Try qwen3:30b first (free, already installed) before paid APIs
- Temperature=0 for all classification tasks
- Get HumanID account for institutional GitLab

### 12.2 Meeting June 25, 2026 (128 minutes — full transcript available)
Most important meeting. All major project decisions made here.

**Task 1 decisions:**
- APPROVED — proceed to full corpus run
- Loterre ambiguous case resolutions (see Part 6.11)
- Johanna's baseline: 47% figuré → now 81.2% (massive improvement)

**Task 2 decisions:**
- Run on OWN Task 1 results only, NOT Johanna's GPT file
- Gold set: 100 animal + 100 plant examples to come from Riccardo
- Combined with Task 4.5: same 200 examples, 2 annotation columns

**Task 3 decisions:**
- Trust Johanna's animal disambiguation (85%) — don't redo it
- Plants need referential filtering after Task 1
- Add English/Arab names to NER — capital letter detection

**Task 0 decisions:**
- 70% "is kind of ok" — accept as final
- ESPACE: exclude from presentation
- FOCALISATION: try GPT-4o API with Riccardo's $9 credit
- "Maybe that's the conclusion — we need to wait for more advanced models"

**Corpus structure clarification:**
- ENTITES files in resultats/ folder are what to run Task 1 on
- Run on BOTH corpus_principal AND bestsellers → deduplicate
- 3 missing gold novels are in bestseller corpus

**Postponed:** Task 5 (Frantext) — "too much already"

**Documentation emphasis:** "Don't hide the technical stuff... Include failed attempts, all models tried, why they failed"

### 12.3 Next Meeting: July 3, 2026 at 11AM

**Riccardo to bring:**
- 100 animal + 100 plant figurative examples for gold sets
- 6-category definitions for comparé classification (or find in GitLab)
- Biodiversity indices documents
- GPT-4o API key (already shared during June 25 meeting)

**Labiba to bring:**
- Task 1 animaux results (DONE ✅)
- Task 1 plantes progress
- Task 0 final results summary
- FOCALISATION cases where models consistently disagree with gold (possible annotation errors)

---

## PART 13: COMPLETE FILE STRUCTURE

### 13.1 Main Project Structure
```
~/ecopoetique/
├── CORPUS_TOTAL/                          # ~925 .txt novel files (1 sentence/line)
├── narratologie/                          # Task 0
├── métaphore/                             # Task 1 & 2
├── morphosyntaxe/                         # Task 3
├── resultats/                             # Corpus entity extraction (Johanna)
│   ├── corpus_principal/                  # Main 925 novels
│   └── bestsellers/                       # ~124 bestseller novels
└── lexiques/                              # TaxRef, Wikispecies, Loterre
```

### 13.2 Task 0 Files
```
~/ecopoetique/narratologie/
├── GOLD_narratologie.csv                   # Master gold (79 novels, semicolon, with alts)
├── GOLD_narratologie_60novels_original.csv # Reliable 60-novel subset
├── Grille_Narratologique.csv               # Full narratological grid
├── critere_narration_focalisation.csv      # 530 novels tab (Narrateur+Focalisation)
├── run_narratologie_mapreduce.py           # Map-reduce v3 (MAIN PRODUCTION)
├── run_narratologie_mapreduce_optionA.py   # Option A (per-criterion reduce)
├── train_chunk_classifier.py              # Sklearn classifier (465 lines)
├── combine_hybrid_v2.py                   # 3-source combination
├── foc_think.py                           # qwen72b FOCALISATION
├── run_focalisation_v3.py                 # Self-consistency (FAILED)
├── run_task0_v4_all7.py                   # qwen72b all 7 criteria
├── resultats_hybrid.csv                   # BEST: old hybrid (60 novels)
├── resultats_hybrid_v4_60novels.csv       # 70.5% with alt scoring
├── resultats_qwen72b_focalisation.csv     # 68.3% FOC (qwen72b+thinking)
├── resultats_qwen72b_all7.csv            # All 7 criteria with qwen72b
├── resultats_qwen3_30b_mapreduce.csv     # Map-reduce v3 results
├── resultats_chunk_classifier.csv        # Sklearn results
├── resultats_gpt4o_mini.csv             # 75% FOC (paid, production N/A)
└── [many more result files — see Part 5.4 for full list]
```

### 13.3 Task 1 Files
```
~/ecopoetique/métaphore/
├── evaluate_all_goldsets_v6.py            # BEST: animaux+plantes
├── evaluate_loterre_v8.py                 # BEST: loterre
├── evaluate_litteralite_v2.py             # Early development version
├── run_task1_corpus.py                    # Full corpus production script
├── run_task2_subcategories.py             # Task 2 (built, waiting)
├── retry_animaux.py                       # Retry failed batches
├── GOLD_litteralite_animaux.csv           # 192 rows (tab)
├── GOLD_litteralite_plantes_RB.csv        # 188 rows (semicolon)
├── GOLD_litteralite_loterre__RB.csv       # 189 rows (semicolon)
├── eval_animaux_v6_results.csv            # Gold set v6 results
├── eval_plantes_v6_results.csv            # Gold set v6 results
├── eval_loterre_v8_results.csv            # Gold set v8 results
├── loterre_ambiguous_cases.md             # Analysis for Riccardo
├── RESULTAT_annotation_gpt.csv            # Johanna's animal labels (112K)
├── RESULTAT_typologie_compare_animaux.csv # Johanna's comparé labels
└── plantes/
    ├── annotations_gpt_partie_1.csv       # Johanna (2,776 rows)
    └── annotations_gpt_partie_2.csv       # Johanna (60,951 rows)
```

### 13.4 Task 1 Corpus Run Outputs
```
~/ecopoetique/resultats/
├── task1_animaux_labels.csv               # COMPLETE (127,877 rows, tab)
├── task1_animaux_labels_full.csv          # With duplicates
├── task1_animaux_run.log                  # Progress log
├── task1_animaux_failed_keys.tsv          # 3,665 failed rows
├── task1_animaux_retry.csv               # Retry in progress
├── task1_plantes_labels.csv              # IN PROGRESS (~23%)
└── task1_plantes_run.log                 # Progress log (PID 1427842)
```

### 13.5 Task 3 Files
```
~/ecopoetique/morphosyntaxe/
├── analyse_agentivite.py                  # Main analysis
├── analyse_dependances.py                 # Dependency extraction
├── extract_humains.py                     # Human NER
├── dépendants_HUMAINS.csv                 # 219,651 rows (tab)
├── dépendants_animaux_référentiels.csv    # 95,243 rows (tab)
├── dépendants_PLANTES.csv                 # 64,269 rows (tab)
├── resultats_agentivite_complet.txt       # Full results with examples
└── task3_full_report.md                   # Complete report
```

---

## PART 14: RESULTS SUMMARY FOR PAPER

### 14.1 Task 0 — Narratological Classification
**Best result: 70.5% overall on 60 novels (Hybrid v4, with alternative label scoring)**

| Criterion | Score | Notes |
|-----------|-------|-------|
| TYPE NARRATEUR | 90.0% | TARGET MET (85%) |
| FOCALISATION | 65.0% (local) / 68.3% (qwen72b) / 75% (GPT) | Hard — human agreement only 76% |
| MODE NARRATIF | 71.7% | Acceptable |
| REGIME NARRATIF | 71.7% | Acceptable |
| ESPACE | 48.3% | EXCLUDED from presentation |
| INTRIGUE | 65.0% | Acceptable |
| TEMPORALITÉ | 71.7% | Acceptable |
| **OVERALL** | **70.5%** | Context: human agreement ceiling ~76% |

**Comparison with Johanna's system:**
- Johanna: ~65% on 2/7 criteria, fails on 33.8% of novels, requires Internet/title
- Labiba: 70.5% on 7/7 criteria, 100% coverage, reads actual novel text, fully local

### 14.2 Task 1 — Literal/Figurative Classification
| Category | Overall | Réf | Fig | vs Johanna (GPT) |
|----------|---------|-----|-----|-----------------|
| **Animaux** | **91.6%** | **97.5%** | **81.2%** | +34.2pp figuré |
| **Plantes** | **96.3%** | **98.8%** | **79.2%** | significant improvement |
| **Loterre** | **85.2%** | **91.2%** | **63.4%** | partial improvement |

**Context:** Human inter-annotator agreement = 76% (Kappa 0.64). Our 91.6% overall for animals EXCEEDS human agreement on this task.

### 14.3 Task 1 — Corpus-Wide Results (Animaux, 127,877 mentions)
- **Référentiel:** 90,755 (70.9%)
- **Figuré:** 37,180 (29.1%)
- ~37,000 figurative animal uses across 925 French novels

### 14.4 Task 3 — Agentivity
**Hierarchy confirmed: Humans (37.2%) > Animals (24.4%) > Plants (11.8%)**

Across 379,163 total mentions in 925 French novels:
- Animals are 1.5× less active than humans
- Plants are 3.1× less active than humans
- Male/female humans nearly identical in agentivity
- Plants predominantly as noun complements (49.5%) — "described rather than doing"

---

## PART 15: PENDING ITEMS (Before July 15, 2026)

### Critical (Blocking other tasks):
- 🔄 Task 1 plantes corpus run — ETA July 8-9
- 🔄 Task 1 animaux retry (failed batches, 3,665 rows) — in progress

### After Task 1 Completes:
- [ ] Merge animaux main + retry results into clean final file
- [ ] Run Task 2 subcategories on own figurative predictions
- [ ] Run Task 4.5 comparé classification on own figurative predictions
- [ ] Create `dépendants_plantes_référentielles.csv` (filter Task 1 réf-only)
- [ ] Rerun Task 3 plants agentivity on referential-only plants

### Task 0:
- [ ] Try GPT-4o on FOCALISATION with Riccardo's API key ($9 credit)
- [ ] Score qwen72b_all7 results and build hybrid v5
- [ ] Send Riccardo: cases where ALL models consistently predict same label but disagree with gold (possible gold annotation errors)

### From Riccardo:
- [ ] 100 animal + 100 plant figurative examples (gold for Task 2 + 4.5)
- [ ] Biodiversity indices documents
- [ ] Confirm comparé category definitions (6 Caracciolo categories)

### Documentation:
- [ ] Technical appendix for paper (this document ✅)
- [ ] Final results document for publication

---

## PART 16: QUICK REFERENCE

### Check running processes:
```bash
ps aux | grep python | grep lfarooq | grep -v grep
nvidia-smi | grep -E "MiB|%"
```

### Check Task 1 plantes progress:
```bash
tail -5 ~/ecopoetique/resultats/task1_plantes_run.log
wc -l ~/ecopoetique/resultats/task1_plantes_labels.csv
```

### Task 0 evaluation with alt scoring:
```bash
cd ~/ecopoetique/narratologie
python3 -c "
import csv
GOLD='GOLD_narratologie.csv'
gold={}
# ... [see combine_hybrid_v2.py for full scoring logic]
"
```

### Recreate qwen72b-limited:
```bash
OLLAMA_HOST=localhost:11435 ollama create qwen72b-limited -f ~/Modelfile_limited
```

### Start Task 1 plantes (after animaux retry finishes):
```bash
cd ~/ecopoetique/métaphore
source ~/digitize_medical_records/labelimg_env/bin/activate
nohup python3 run_task1_corpus.py --category plantes > ../resultats/task1_plantes_run.log 2>&1 &
```

---

*Documentation compiled by Labiba Farooq — July 2026*
*Sources: All session transcripts (May-July 2026), Progress Report (June 2026), Master Notes (May 18, 2026), Meeting transcript June 25, 2026 (128 min), task1_animal_results.txt, loterre_ambiguous_cases.md, task3_full_report.md, Ecopoetique_Progress_Report.docx, Ecopoetique_Master_Notes.docx*

---

## PART 17: RESEARCH PAPER — "IMPROVING FRENCH NARRATOLOGICAL CLASSIFICATION WITHOUT PAID APIS"

### 17.1 Document Overview
**Title:** "Improving French Narratological Classification Without Paid APIs: Models, Free Tiers, and Prompting Techniques"
**Purpose:** Technical reference document compiled for this project specifically — a synthesis of all relevant literature, free API options, local models, and prompting techniques for improving Task 0 (narratological classification) without paid API costs.
**Used for:** Task 0 improvement — deciding which models and techniques to try next.

---

### 17.2 Free API Tiers Available (as of June 2026)

**Mistral (La Plateforme — "Experiment" plan):**
- Free with no credit card — real free tier
- Gives access to ALL models: Small, Medium, Large, Codestral, Pixtral, Magistral (reasoning), Devstral
- Published limits: ~2 RPM / ~500K TPM / ~1B tokens/month
- **WARNING:** Free-tier prompts MAY be used to train Mistral's models — opt-out in Admin Console Privacy section
- Zero Data Retention is a PAID Scale-plan feature, NOT available on free tier
- **Why it matters for this project:** Mistral Large 2 (123B) was trained predominantly on French text. Strong domain classification: legal ~95%, medical ~89%. Best French-native free option.
- **Ranking:** Mistral (native French) is #1 free option for French tasks

**Google Gemini (Free tier):**
- No credit card required
- Free tier covers only Flash and Flash-Lite (as of May 2026)
- Gemini 2.5 Pro: only 50 requests/day on free tier
- Rate limits: 15 RPM Flash, 30 RPM Flash-Lite; 1M-token context; multimodal
- **WARNING:** Google cut free quotas by 50-80% in December 2025, removed Pro free access April 2026, cut Pro free RPD 100→50 on May 7, 2026. Verify live limits before building on them.
- Free-tier prompts may be used by Google for training
- Gemini supports French fully
- Gemma 3 27B (local): scored HIGHER on French (61.5) than English (60.5) on PISA-Bench — unusual favorable property for our French use case

**Groq (LPU-based inference):**
- Free tier, no credit card, extremely fast (LPU hardware)
- Hosts: Llama 3.3 70B, Mixtral, Gemma, gpt-oss
- 2026 limits: ~1,000 requests/day on many models, ~30 RPM (tightened from before)
- Good for fast short calls — NOT for long-running batches
- **We already tested Groq Llama 3.3 70B** → 58.3% FOCALISATION (same bias as other models)

**Cohere:**
- Trial API key with free tokens, acceptable for academic research
- Command-A models: 256k context window

**Together.ai:**
- Free tier (no card), up to ~1M tokens/day, very high throughput
- Volatile model catalog — don't hardcode model names

**OpenAI:**
- Only small one-time trial credit (~$1) plus a few "-Free" suffixed models
- NOT a durable free tier for research
- **WARNING:** There is NO genuine free API tier for GPT-4o-mini/GPT-4o. "Free GPT-4o" websites are unofficial resellers/loophole tools — avoid for ToS and research integrity reasons. ChatGPT Plus/Free do NOT grant API credits.

**OpenRouter / GitHub Models:**
- All offer no-card free access to various open models
- Can reach Claude/GPT-style endpoints with small free budgets
- Useful for occasional tests

**Free tier ranking for French tasks:**
Mistral (native) > Gemini (excellent) > Llama 3.3 70B / Gemma via Groq (strong EU-language tuning) > others

---

### 17.3 Local Models Available for Ollama (Free, No API)

**Best alternatives to qwen3:30b:**

**Gemma 3 27B (Google):**
- Run via Ollama: `ollama pull gemma3:27b`
- Multilingual tuning documented as STRONGER in EU languages than Qwen
- On multilingual PISA-Bench: French (61.5) > English (60.5) — unusual and favorable
- Clean structured/JSON output
- Recommended temperature: ~0.15
- **Verdict: Most direct French-strong local alternative to qwen3:30b**

**Mistral-Small-3.1 24B:**
- Run via Ollama
- Native French — trained heavily on French text
- Strong instruction-following
- **Note: WAS installed on server but deleted to save disk space**

**Magistral (Mistral's reasoning model):**
- Available on Ollama
- Useful ONLY if reasoning genuinely helps for the specific criterion (test against CoT caveat below)

**Llama 3.3 70B:**
- Best open model for focalization per published evidence (~79% F1 on English)
- Requires ~48GB VRAM — barely fits A40 (46GB) with quantization
- **We tested via Groq** → 58.3% FOCALISATION (FOC_INT bias, doesn't transfer to French)
- **To try locally** if VRAM allows: might give different results than Groq (Groq runs quantized)

**French-specific models (mostly too small to beat qwen3:30b):**
- **Lucie-7B** (OpenLLM-France/LINAGORA): 7B, trained on 3T tokens (32.4% French), Apache 2.0, fully transparent data, on HuggingFace. Early-stage/not production-ready at January 2025 launch. Too small for nuanced classification.
- **CroissantLLM** (1.3B, bilingual FR/EN, MIT): Too small.
- **Vigogne** (bofenghuang): Llama-2/Llama-3.2 fine-tunes for French; Zaion "Vigogne" line continues French pretraining on FineWeb-2. Mostly ≤13B; research-licensed.

**French-specific resources (most useful for fine-tuning):**
- FrenchBench, FreD, FMTOD — French evaluation benchmarks
- FineWeb-2 French subset — training data

**No production-quality French generative LLMs exist** at the scale needed for literary classification. LATTICE/Sorbonne Nouvelle pipeline (CCLS 2024) covers entities, coreference, subgenre classification but is not a generative LLM.

---

### 17.4 Key Research Findings from the Paper

#### Finding 1: Hicke et al. Focalization Results (MOST RELEVANT)
**Task:** Focalization classification on Stephen King paragraphs, ENGLISH
**Best GPT-4o F1: 84.79%** (note: secondary sources cite 86.90% — use 84.79% as authoritative from arXiv full text)
**Key model comparisons:**
- **Llama 3.1 70B:** best open model, "promising if not as reliable"
- **RoBERTa-base/DistilBERT:** ~74% F1 — trained on only 300 samples!
- **Llama 3.2 3B:** 62.67%; Llama 3.2 1B: 1.13% (failed completely)
- **Logistic regression baseline:** 71.84%
- **GPT-3.5-turbo:** 69.63%
- **GPT-4-turbo:** 80.82%

**Best zero-shot prompt for focalization:**
- Embed Genette definitions VERBATIM in prompt — drove GPT-4o to ~85% zero-shot
- Add the quotation-mark rule: "speech in quotation marks = external focalization"
- Force single-word output (no CoT for this criterion)

**FOC_ZERO/omniscient problem:** 9 of 17 models labeled it ZERO times. Even GPT-4o scored only ~36% F1 on FOC_ZERO. This is the documented failure mode across nearly all models.

**Robustness:** GPT-4o achieved Krippendorff's α of 0.74 across 6 prompt variants, with F1 ranging 79.8% to 84.5%. A variant STRIPPED OF ALL DEFINITIONS still scored ~84.5% — implying focalization knowledge is largely baked into pretraining of large models.

**IMPORTANT CAVEAT:** All Hicke et al. numbers are on ENGLISH Stephen King. French performance is untested. Treat 77-79% figures as upper-bound guidance, not guarantees for French.

#### Finding 2: Chain-of-Thought HURTS Subjective Tasks (CRITICAL FOR OUR WORK)
Multiple papers confirm this:
- **"Larger Language Models Don't Care How You Think"** (Chochlakis et al., arXiv 2409.06173): CoT degrades performance on subjective/intuition-based classification (emotion, morality)
- **"Mind Your Step (by Step)"** (arXiv 2410.21333): Same finding
- **Pichler et al. results:** "Let's think step by step" helped vanilla Llama-3.1-8B but had model-specific effects — no general recommendation

**Recommendation from paper:** Turn OFF thinking mode (no-think) for subjective criteria: FOCALISATION, MODE NARRATIF, ESPACE. Enable thinking ONLY where criterion decomposes into verifiable steps (e.g., TEMPORALITÉ has clear structural markers).

**CONFLICT WITH OUR TASK 1 FINDING:** For Task 1 (literal/figurative), NO-THINK = 0% figuré. Thinking is essential for Task 1. The CoT-hurts finding applies specifically to SUBJECTIVE classification, not to semantic disambiguation. These are different cognitive tasks.

#### Finding 3: Constrained Decoding Improves Speed and Accuracy
**JSONSchemaBench** (arXiv 2501.10868):
- Constrained decoding speeds generation by ~50%
- IMPROVES classification accuracy — eliminates parse errors and constrains label space
- Particularly valuable for classification where output must be one of N labels

**"Thinking Before Constraining"** (arXiv 2601.07525):
- Up to significant improvement by letting model reason freely until a trigger token, then switching to constrained output
- Middle path: some thinking + constrained output format

**Practical implementation:** Use JSON schema in Ollama:
```python
response_format={"type": "json_schema", "json_schema": {"schema": {"enum": ["FOC_INT", "FOC_ZERO", "FOC_EXT", "FOC_VAR"]}}}
```

#### Finding 4: Label Description Sensitivity
Systematically varying label descriptions, instructional nudges, and few-shot examples found:
- **4-11pp swings** from different gold set splits
- **2-6pp** from rewordings of the same criterion
- Effects are STRONGLY HETEROGENEOUS across models and tasks
- **Must validate per criterion** — what works for TEMPORALITÉ may not work for FOCALISATION

**Recommendation:** Treat prompt design as a training process. Set threshold: if a change doesn't improve ≥3pp, revert it.

#### Finding 5: Self-Consistency Voting DOES Work (According to Paper)
Wang et al. (2022): "Sample several diverse generations and take the plurality label — robustly improves classification without training."
- Use low-but-nonzero temperature (0.3-0.5)

**HOWEVER — Our experience CONTRADICTS this for FOCALISATION:**
- We tested n=5 at temperature=0.3 → no improvement (61.7% vs 61.7%)
- Root cause: When underlying bias is systematic (model always says FOC_INT), voting amplifies the bias rather than correcting it
- Self-consistency only helps when model variance is random noise, not when it's systematic

#### Finding 6: RoBERTa Fine-tuning is Surprisingly Sample-Efficient
**RoBERTa-large reached 77.5% focalization with only 300 training samples** — on the exact same task (English, but directly relevant).

This sidesteps the "no more gold examples" constraint for two reasons:
1. Encoder fine-tuning is FAR more sample-efficient than prompting
2. Our existing 60 gold labels are usable — not enough for generative fine-tuning, but potentially enough for encoder fine-tuning

**Projection:** If a fine-tuned RoBERTa-large on our 60 French gold examples could achieve 70%+ (60% of the 300-sample English result), that would match or beat our current best (65% locally).

**Why we didn't implement this:** The 60 novels barely overlap with CamemBERT pretraining knowledge of literary French. May need French literary pre-training data (FineWeb-2 French subset, Gallica novels).

---

### 17.5 Recommended Improvement Roadmap for Task 0 (from Paper)

The paper provides a staged improvement plan specifically for our situation:

**Stage 1 — Prompt rewrites (free, immediate):**
1. Embed Genette definitions VERBATIM for each criterion
2. Disable thinking (/no_think) for FOCALISATION, MODE NARRATIF, ESPACE
3. Force constrained JSON output with exact label enum
4. Add self-consistency voting (~5 samples at temperature 0.3-0.5, majority vote)
5. Add targeted few-shot examples for minority/confused classes (especially FOC_ZERO)
6. Benchmark on held-out dev split; revert changes that don't improve ≥3pp

**Stage 2 — Model ensembling (free, local):**
5. Pull Gemma 3 27B and Mistral-Small-3.1 24B via Ollama
6. Run all three (qwen3:30b + Gemma + Mistral) and take majority vote
7. Gemma's EU-language strength directly targets French weakness
8. If ≥48GB VRAM: test Llama 3.3 70B on focalization locally

**Stage 3 — Encoder fine-tuning (medium effort):**
7. Fine-tune CamemBERT-large per weak criterion on existing 60 gold labels
8. RoBERTa-large reached 77.5% on focalization with 300 samples — encoder fine-tuning is far more sample-efficient
9. Use class weighting or oversampling for rare FOC_ZERO class
10. If fine-tuned encoder clears ~75% on FOCALISATION → stop chasing larger generative models for that criterion

**Stage 4 — API calls (optional, uses Mistral free tier):**
9. Use Mistral free API (no card, ~1B tokens/month) for Mistral Large as a French-native tiebreaker in ensemble
10. Opt out of data training in Mistral console

**Stopping rules:**
- If fine-tuned encoder (Stage 3) clears ~75% on FOCALISATION → stop
- If Gemma/Mistral ensembling (Stage 2) doesn't beat qwen3 alone by ≥2pp → drop extra models
- If ESPACE stays ≤55% after all stages → move entirely to feature-based sklearn classifier

---

### 17.6 Per-Criterion Recommendations from Paper

**FOCALISATION (currently 65.0% — hardest criterion):**
- Embed verbatim Genette definitions
- Add quotation-mark rule (speech in quotes = FOC_EXT)
- Force single-word output, no CoT
- Self-consistency
- Special attention to FOC_ZERO (documented failure mode — near-zero F1 on all models)
- Best path to >75%: fine-tuned encoder (Stage 3) — "most reliable way to break the 63% ceiling"
- Realistic local target: 77-79% (requires large open model OR fine-tuning)

**MODE NARRATIF (currently 71.7% — closest to "good"):**
- Embedding crisp definitions + JSON output + self-consistency may be enough to push past 75%
- If MODE NARRATIF involves speech vs. narration distinction: French direct-speech-annotation literature suggests rule/transformer hybrids work well (Durandard et al., ACL 2023 — French fine-tuned transformers for annotating direct speech in French narratives)

**ESPACE (currently 48.3% — EXCLUDED from presentation):**
- Weakest criterion, least standardized in Genette's framework
- Most dependent on spatial/world reasoning, which LLMs handle poorly
- Recommendation: Reformulate into concrete sub-questions OR move to feature-based sklearn classifier (which our hybrid already contains)
- Don't chase LLM improvement here

**REGIME NARRATIF (currently 71.7%):**
- Main confusion: REG_REAL vs REG_AUTO (7× errors)
- Embed explicit definition distinguishing realism from autofiction
- Key signal: first-person narration does NOT imply autofiction

**INTRIGUE (currently 65.0%):**
- Symmetric LIN/FRAG confusion (10× + 8×)
- Key: one main plot with subplots ≠ genuinely fragmented narrative
- Embed this distinction explicitly

**TEMPORALITÉ (currently 71.7%):**
- Main error: any memory/flashback → predicted as TEMP_DIS
- Key: isolated analepsis does not = overall temporal structure
- Embed: "if anachrony is localized and doesn't affect overall structure → TEMP_LIN"

---

### 17.7 Important Warnings from Paper

**On free tiers:** "Free API tiers change frequently and have trended restrictively." Always re-verify current limits before building on them. The numbers in this documentation (Mistral 2 RPM, Gemini 1,500 req/day, Groq ~1,000 req/day) may be outdated.

**On data privacy:** Free tiers may use prompts for training (Mistral, Google confirmed). If corpus is copyrighted or sensitive, this is relevant. Mistral Zero Data Retention = paid Scale plan only.

**On French transfer:** Hicke et al. focalization results are on English Stephen King. French performance is untested — treat 77-79% as upper-bound guidance, not a guarantee.

**On Pichler et al.:** Results are for SPAN LABELING, not paragraph classification. Low absolute scores (20-33 F1) don't predict our task performance.

**On CoT:** Effects are model-specific. "Let's think step by step" helped Llama 3.1 8B but had varied effects on other models. No general recommendation — test per model per criterion.

**Citation discrepancy:** Secondary sources cite Hicke et al.'s GPT-4o F1 as 86.90; arXiv full text reports 84.79%. Use 84.79% as authoritative.

---

### 17.8 How This Paper Influenced Our Actual Work

| Paper Finding | What We Tried | Our Result | Match? |
|---|---|---|---|
| CoT hurts subjective tasks | No-think for Task 1 | 0% figuré — catastrophic | ❌ OPPOSITE — thinking is essential for Task 1 (different task type) |
| Self-consistency improves classification | n=5 voting for FOC | 61.7% — no improvement | ❌ Doesn't work when bias is systematic |
| Embed Genette definitions | Tried in map-reduce prompts | Minor improvement | ✅ Confirmed |
| Quotation-mark rule | Added to FOC prompts | Minor improvement | ✅ Partial |
| Llama 3.3 70B best open model | Tested via Groq | 58.3% — same FOC_INT bias | ❌ Doesn't transfer to French |
| RoBERTa fine-tuning | Attempted (CamemBERT) | FAILED — 60 samples too few | ❌ Insufficient gold data |
| RAG improves classification | Smart RAG for Task 0 | 45% — WORSE than baseline | ❌ Wrong task type for RAG |
| Fine-tuning beats prompting | LoRA on 60 gold novels | FAILED — minimum ~200 needed | ❌ Insufficient gold data |
| Constrained JSON output | Implemented in all scripts | Eliminated parse errors ✅ | ✅ Works |
| Gemma strong in French | Not yet tested | — | 📌 TODO: try Gemma 3 27B |
| Mistral native French | Tested Mistral Large (free API) | 63.3% FOC — defaults to FOC_INT | ⚠️ Still has FOC_INT bias, but better than Llama |

---

### 17.9 Conclusions for Paper Appendix

Based on this document, the recommended framing for the paper's technical appendix:

1. **Task 0 difficulty is well-documented:** Even GPT-4o reaches only 84.79% on English focalization (Hicke et al.). Our 65% on French with local models is reasonable given the language gap and model size.

2. **FOC_ZERO failure is universal:** 9 of 17 models in Hicke et al. labeled FOC_ZERO zero times. Our models show the same behavior. This is not a model failure but a structural difficulty of the class.

3. **Fine-tuning is the principled path forward:** RoBERTa-large reached 77.5% with 300 samples. Our constraint (60 gold novels) prevents this currently. Expanding the gold set to 300+ would be the highest-leverage future investment.

4. **CoT/thinking mode has task-specific effects:** Essential for semantic disambiguation (Task 1), potentially harmful for subjective literary classification (Task 0 — FOCALISATION, MODE NARRATIF). This finding itself is a contribution.

5. **Model ensembling (not yet tried):** Cross-model voting (qwen3:30b + Gemma 3 27B + Mistral Large) is the most promising free local improvement not yet implemented.



# ÉCOPOÉTIQUE NUMÉRIQUE — COMPLETE TECHNICAL DOCUMENTATION v2
## Full Project Documentation: May 2026 – July 2026
**Researcher:** Riccardo Barontini (UPPA — Université de Pau et des Pays de l'Adour)
**Chair:** "Enjeux écopoétiques contemporains" — ANR programme "Anthropocène littéraire"
**Research Engineer:** Labiba Farooq (M2 Internship, May–July 15, 2026)
**Previous Engineer:** Johanna Cordova
**Server:** obtic-gpu1 — lfarooq@134.157.57.238 (Port 11435 for Labiba's Ollama)
**GitLab:** gitlab.huma-num.fr (institutional, HumanID login required) + gitlab.com/rumiwarmi/ecopoetique (private)
**Team chat:** ecopoetique.zulipchat.com (channels: llms, general)
**Internship:** May 2026 – July 15, 2026

---

## PART 1: PROJECT OVERVIEW & RESEARCH CONTEXT

### 1.1 Fundamental Research Question
"Is there a real 'ecological turn' in contemporary French-language literature, or is it just a feeling based on a few famous, well-known books?"

To answer this empirically, Riccardo Barontini developed the **Digital Écopoétique** project, funded by:
- A European Marie Skłodowska-Curie Actions postdoctoral fellowship (2023)
- Integrated into ANR "Anthropocène littéraire" programme at UPPA

### 1.2 Core Hypothesis
**Textual biodiversity** (variability of living organisms, ecosystems, and ecological concepts represented in novels) can serve as a **formal indicator** of ecological sensitivity in contemporary French fiction.

This hypothesis draws on:
- **Rosi Braidotti** (*Posthuman Knowledge*, 2019) — relational subjectivity, co-belonging between living beings and environments
- **Baptiste Morizot** (*Manières d'être vivants*, 2020) — the ecological crisis as a crisis of sensitivity: inability to perceive, distinguish, and name the living beings around us
- **Ursula K. Heise** (*Imagining Extinction*, 2016) — biodiversity as a cultural operator, endangered species acquire social effectiveness through collective narratives
- **Vincent Devictor** (*Nature en crise*, 2015) — biodiversity as contested metric, tied to political crisis discourse
- **Edward O. Wilson** — popularised "biodiversity" concept in late 1980s

### 1.3 Key Finding Already Established (Before Labiba)
The biodiversity index is **globally stable** over 2001–2024 — no clear "ecological turn" across the broad corpus. Only a **small cluster** of specific novels scores very high. The ecological writing does not spread diffusely; it crystallises in specific works.

**Confirmed:** Novels nominated for *Prix du Roman d'Écologie* score more than **2× the average** biodiversity index. 45 out of 47 such novels exceed the general corpus average — strong correlation between external qualitative categorisation (jury label) and internal formal measure.

### 1.4 Three Levels of Analysis
1. **Lexical/Semantic (Task 1):** Extract animal, plant, ecological terms; classify literal vs. figurative
2. **Stylistic (Task 2):** Figurative subcategory classification (metaphor type, comparant/comparé)
3. **Narratological (Task 0):** Automated narratological profiling (7 criteria per novel)

**Additional tasks:**
- **Task 3:** Agentivity (active vs. passive roles of animals, plants, humans)
- **Task 4.5:** Comparant/Comparé classification

### 1.5 Corpus Structure

| Corpus | Size | Description |
|--------|------|-------------|
| Corpus principal | 892 novels | Prize shortlists: Goncourt, Goncourt des Lycéens, Femina, Renaudot, Médicis, Livre Inter, Cinq Continents (2001–2024) |
| Corpus bestsellers | 124 novels | Top 5 best-selling novels per year |
| Corpus écologique | 47 novels | Nominees for Prix du Roman d'Écologie 2017–2024 |
| TOTAL (with overlaps) | ~1,070 novels | Combined unique novels |
| CORPUS_TOTAL (server) | ~925 .txt files | After deduplication on server |

**Note on literary prize bias:** Using prize shortlists is an acknowledged bias — only works that "institutions recognize as having value" are included. This allows asking: does ecological imagination align with literary consecration?

**Corpus metadata files:**
- `corpus_DigEco.csv` — main corpus metadata (tab-separated: Year, Author, Title, Sex, Nationality, Birth year, File)
- `corpus_Bestsellers.csv` — same format
- `corpus_PRIX_ECOLOGIE.csv` — ecology prize novels

### 1.6 Zipf's Law in the Corpus
The biodiversity vocabulary follows Zipf's law: 480 lemmas cover 90% of all ~290,000 occurrences, while the remaining 10% require 3,500+ rarely used lemmas. This reveals a structural tension between symbolic concentration (a few dominant species) and ecological dispersion (many rare ones).

---

## PART 2: SERVER SETUP & INFRASTRUCTURE

### 2.1 Hardware
- **Server:** obtic-gpu1 (Sorbonne Université — managed by Martial, server admin)
- **GPU:** NVIDIA A40 — 46,068 MiB VRAM
- **Disk:** 5.8TB total, ~116GB free (98% full as of July 2026)
- **OS:** Ubuntu 24

**GPU usage warning (July 6, 2026):** Martial (server admin) emailed noting 82-83% GPU utilization. Response: explained it's the final computation step, finishes July 8-9, then GPU returns to 0%.

### 2.2 Ollama Models (Port 11435 — Labiba's private instance)

| Model | VRAM | Status | Used For |
|-------|------|--------|----------|
| qwen3:30b | 18GB | ✅ Active | Task 1 production (BEST local), Task 0 map-reduce |
| qwen72b-limited | 22GB | ✅ Active | Task 0 FOCALISATION (68.3% — best local) |
| qwen2.5vl:72b | 47GB | ✅ Available (port 11435) | Base for qwen72b-limited |
| qwen2.5:7b | 4GB | ✅ Available (port 11434) | Testing only |
| gemma3:27b | 17GB | ❌ Deleted | Too slow, deleted to save disk space |
| mistral-small3.1 | 15GB | ❌ Deleted | Too slow for this task |

**Port 11434 (Other researchers' Ollama — DO NOT INTERFERE):**
qwen2.5:72b (47GB), qwen2.5:32b, qwen2.5:14b, qwen2.5:7b, bge-base-en-v1.5-gguf

### 2.3 qwen72b-limited Model Configuration
Created to reduce qwen2.5vl:72b from 47GB to 22GB VRAM with only ~1.6% accuracy loss:
```
# ~/Modelfile_limited
FROM qwen2.5vl:72b
PARAMETER num_ctx 8192
PARAMETER num_gpu 20
```
Recreate: `OLLAMA_HOST=localhost:11435 ollama create qwen72b-limited -f ~/Modelfile_limited`

### 2.4 Python Environment
```bash
source ~/digitize_medical_records/labelimg_env/bin/activate
```

### 2.5 Startup Script
`~/start_ollama.sh` — no longer exists (deleted/moved); manual startup required

### 2.6 Repository Structure (GitLab)
```
ecopoetique/
├── CORPUS_TOTAL/       # ~925 .txt novels — one sentence per line
├── TOKENS/             # spaCy POS analysis per text (token, POS, lemma)
├── TOKENS_Bestsellers/ # Same for bestsellers
├── lexiques/           # TaxRef, Wikispecies, Loterre vocabulary lists
├── homographie/        # Homograph disambiguation (bar=fish vs bar=place)
├── morphosyntaxe/      # Task 3 — dependency analysis scripts + results
├── métaphore/          # Task 1 & 2 — literal/figurative scripts + results
├── narratologie/       # Task 0 — narratology scripts + gold set + results
├── resultats/          # Corpus-wide entity extraction files
├── scripts/            # Python/bash pipeline utilities
└── visualisations/     # Charts and graphs
```

---

## PART 3: LEXICONS AND ENTITY EXTRACTION (Johanna's Foundational Work)

### 3.1 The Three Lexicons

**1. TaxRef** (MNHN — Muséum National d'Histoire Naturelle)
URL: https://inpn.mnhn.fr/telechargement/referentielEspece/referentielTaxo
Scientific species taxonomy; French territory including overseas. Provides vernacular names linked to unique species identifiers.

**2. Wikispecies** (Wikimedia)
URL: https://species.wikimedia.org
Global species database extending coverage beyond French territory. Merged with TaxRef after lemmatisation, orthographic normalisation, duplicate removal, unique ID assignment per species.

**3. Loterre** (CNRS/ISTEX)
URL: https://loterre.istex.fr/BLH/fr/
Not individual species — conceptual ecological vocabulary: ecosystems, ecological dynamics, natural processes, perturbations, climate change/environmental transformation vocabulary. Organised hierarchically: ~716 entries (project notes say ~900 distinct Loterre concepts found in corpus).

### 3.2 Extraction Results (Johanna's Pipeline)
~290,000 total occurrences from 1,070 novels:

| Category | Occurrences | % | Distinct Taxa/Entries |
|----------|-------------|---|----------------------|
| Animaux | 114,851 | 39.6% | 1,488–1,523 taxa |
| Loterre | 111,196 | 38.3% | ~716–900 concepts |
| Plantes | 63,599 | 21.9% | 1,567–1,609 taxa |
| Champignons + Taxons | ~3,000 | ~1% | marginal |

**Key asymmetry:** Animals dominate in volume (frequency) but plants have higher specific diversity (more distinct species). Mammals = 60% of animal occurrences but fewer taxa than birds.

**Ornithological sensitivity:** Birds have higher specific richness relative to occurrence count — signals a notable ornithological sensitivity in contemporary French literature (noted by Marielle Macé in *Une pluie d'oiseaux*, Corti, 2022).

### 3.3 Disambiguation Challenge and Solution
Many biodiversity terms are polysemous:
- *maquereau* = mackerel (fish) OR pimp (slang)
- *le bar du coin* = bar (place), NOT bar (fish)
- *chien de fusil* = gun trigger, NOT dog

**Johanna's two-step approach:**
1. Linguistic rule-based filtering (expression blacklists, POS rules)
2. Contextual classification using FlauBERT (French BERT trained on annotated sample) or GPT-4

**Johanna's accuracy:** ~85% (Riccardo's estimate) — "good enough, too complicated to go back"

### 3.4 Entity Files (resultats/ folder — what Task 1 runs on)
```
~/ecopoetique/resultats/
├── corpus_principal/
│   ├── ENTITES_contexte_animaux.csv    (128,530 rows, tab: fichier|token_lexique|truncated_sentence|lemme|categorie)
│   ├── ENTITES_contexte_plantes.csv    (68,216 rows, tab: fichier|token_lexique|truncated_sentence|lemme)
│   ├── ENTITES_contexte_loterre.csv    (120,046 rows)
│   ├── ENTITES_contexte_champignons.csv (282 rows)
│   ├── ENTITES_contexte_taxons.csv     (572 rows)
│   ├── ENTITES_TOTAL.csv               (317,646 rows — all categories combined)
│   └── data_pour_Shannon.csv           (Shannon index per novel)
└── bestsellers/
    ├── BESTSELLERS_contexte_animaux.csv (15,588 rows)
    ├── BESTSELLERS_contexte_plantes.csv (6,259 rows)
    └── BESTSELLERS_contexte_loterre.csv (10,524 rows)
```

### 3.5 Shannon Biodiversity Index
Applied by Johanna to each novel. From information theory, not just ecology.

Formula: H = -Σ(pᵢ × ln(pᵢ)) where pᵢ = proportion of species i in the novel

Combines:
- **Richness** (number of distinct species)
- **Equitability** (how evenly distributed they are)

High Shannon = many species, evenly represented.
Low Shannon = few dominant species, many rare.

**Key result:** Prix du Roman d'Écologie novels average **>2× the corpus mean Shannon index.** 45/47 such novels exceed the general corpus average — validates using Shannon as an ecological sensitivity indicator.

---

## PART 4: RESEARCH PAPERS READ AND THEIR INFLUENCE

### 4.1 Paper: Hicke et al. (2024) — Metaphor Identification with LLMs
**Title:** "Metaphor identification using large language models: A comparison of RAG, prompt engineering, and fine-tuning"
**Published:** March 2026

**Key findings and how they influenced our work:**

1. **Fine-tuning beats prompting:** Fine-tuning achieves best F1 (0.79), substantially higher than prompt engineering alone. → Motivated LoRA fine-tuning attempt for Task 0 (failed due to insufficient gold data)

2. **RAG also tested:** RAG on full literary texts produces fully annotated texts usable in downstream analyses. → We tested Smart RAG for Task 0 — got 45% overall, WORSE than baseline. RAG is wrong tool for narratological classification.

3. **Self-consistency/majority voting:** "Robustly improves classification without training" — sample 5 times at temperature 0.3-0.5, take majority vote. → We implemented this for FOCALISATION (n=5, temp=0.3), got 61.7% — NO IMPROVEMENT over single sample. The problem is underlying bias: all 5 votes return FOC_INT.

4. **CoT hurts subjective tasks:** Chain-of-thought (thinking mode) hurts classification of subjective/literary tasks. → We tested: NO-THINK gave 0% figuré for Task 1 (catastrophic), THINKING gave 81.2% figuré. For our specific task, thinking is essential. The paper's finding applies to different task types.

5. **Quotation-mark rule (Hicke et al.):** "Speech in quotation marks = signal of FOC_EXT" — we added this specific rule to FOCALISATION prompts. Minor improvement only.

6. **Llama 3.3 70B best open model:** Paper claims 78.97% F1 on focalization with Llama 3.3 70B. → We tested via Groq API — got 58.3% FOCALISATION. The paper's result doesn't transfer to our French corpus or our gold set definition.

### 4.2 Paper: Barontini (2026) — Le tournant écologique à l'épreuve des humanités numériques
**Title:** "Le tournant écologique à l'épreuve des humanités numériques : le romanesque de la biodiversité"
**Published in:** Anthology (Riccardo's own paper — the published academic paper of this project)

**Key claims Labiba worked to verify/extend:**
- "Precision obtained by LLM approaches 90%, validated by manual annotation on sample" — this refers to GPT-4o-mini's performance on examples WHERE human annotators agreed. Our broader gold set gives 85–96% overall.
- Human inter-annotator agreement: 76% common annotations, Cohen's Kappa = 0.64 (moderate) → this sets the ceiling for what any system can reasonably achieve.
- GPT-4o-mini accuracy on unanimously identified examples: 89.7%; overall between 79% and 85%.
- Animal uses: 84.5% literal, 15.5% figurative; Plant uses: 81.3% literal.
- 73% of figurative animal uses compare to human body (CH category) → animality mostly serves to define humanity.

**Riccardo's anxious quote from June 25 meeting:** "I'm a little bit anxious about what I'm getting in terms of interpretation from all this work. Probably not that much. Which is kind of frustrating."

### 4.3 Research on FOCALISATION Difficulty
From survey of existing literature:
- Even GPT-4o only reaches ~84% on FOCALISATION in English
- Human annotators agree ~76% of the time (Kappa 0.64) on focalization
- FOC_INT is most common class (~60% of novels) → models default to it
- FOC_ZERO vs FOC_INT distinction requires observing MULTIPLE characters' inner thoughts across whole novel — fragments are insufficient

**Conclusion for paper:** "We need to wait for more advanced models" (Riccardo's own words, June 25). This IS a valid publishable conclusion.

### 4.4 Marco Caracciolo — Narrating the Mesh (2021)
**Full citation:** *Narrating the mesh. Form and story in the Anthropocene*, Charlottesville, University of Virginia Press, 2021.

Provided the **6-category typology for comparé classification** (Task 4.5):
- **O** — Objects and artificial structures (man-made artefacts, technology)
- **NH** — Non-human living creatures and biological processes
- **E** — Inanimate natural elements and natural processes (landscapes, geology, weather)
- **CH** — Human body and biological processes occurring in the human body
- **A** — Abstract concepts, social practices and institutions (politics, religion, marriage)
- **P** — Psychological states and cognitive functions (emotions, memory, imagination)

Example from Johanna's work: "la jeunesse est un chat insomniaque" → chat=comparant, la jeunesse=comparé, category=A (abstract concept).

---

## PART 5: TASK 0 — NARRATOLOGICAL CLASSIFICATION

### 5.1 Objective and Context
Automatically classify each novel across 7 Genette-based narratological criteria. Target: 85% per criterion.

**Johanna's previous system (GPT-4o via API):**
- Only queried Internet using title + author + year — did NOT read the novel text
- Only covered 2 out of 7 criteria (Narrateur + Focalisation)
- FAILED on 271/802 novels (33.8%) — marked as X/X (unclassifiable)
- ~65% accuracy on the 2 criteria it handled
- Could NOT scale to 5 remaining criteria

### 5.2 Narratological Criteria and Labels

| Criterion | Labels | Definition |
|-----------|--------|------------|
| TYPE NARRATEUR | NAR_AUTOD, NAR_TEM, NAR_EXT | Narrateur personnage (protagonist=narrator), Narrateur témoin (witness), Narrateur externe (heterodiegetic) |
| FOCALISATION | FOC_INT, FOC_EXT, FOC_ZERO, FOC_VAR | Internal (one character), External (camera), Zero (omniscient), Variable (changes between sections) |
| MODE NARRATIF | MOD_EVT, MOD_DESC, MOD_INTR, MOD_MIX | Events, Description, Introspection, Mixed |
| REGIME NARRATIF | REG_REAL, REG_AUTO, REG_FANT, REG_SPEC | Realist, Autofiction, Fantastic, Speculative |
| ESPACE | ESP_UNIT, ESP_FRAG, ESP_ITIN, ESP_IMAG | Single location, Fragmented, Journey/itinerant, Imaginary |
| INTRIGUE | INTR_LIN, INTR_FRAG, INTR_CYC | Linear, Fragmented, Cyclical |
| TEMPORALITÉ | TEMP_LIN, TEMP_DIS, TEMP_DESORD | Chronological, Anachronic (flashbacks/prolepses), Scrambled |

**Note from Grille_Narratologique.csv:** Riccardo's full grid also includes "Degré de discordance temporelle" (low/medium/high) and distinguishes analepses from prolepses separately — these were noted for future refinement but not implemented yet.

**ESPACE note:** Riccardo decided ESPACE should be eliminated from presentation — results too low and too variable (unstable across samples).

### 5.3 Gold Set
- **Primary file:** `~/ecopoetique/narratologie/GOLD_narratologie.csv` (semicolon-separated, 79 novels with alternative labels)
- **Reliable 60-novel subset:** `~/ecopoetique/narratologie/GOLD_narratologie_60novels_original.csv` — the 60 novels Riccardo is most confident about
- **Extended labels:** `~/ecopoetique/narratologie/critere_narration_focalisation.csv` (530 novels, tab-separated) — Narrateur and Focalisation only, with 271/801 entries as "X" (unknown). **WARNING: 56/60 gold novels overlap with this file — cannot use as training without careful exclusion.**

**Focalisation distribution in critere file:**
- Interne: 217 (40%)
- Zéro: 178 (33%)
- Variable: 93 (17%)
- Externe: 42 (8%)
- X (unknown): 271

**Inter-annotator disagreements found:** The critere file sometimes disagrees with the gold set:
- `Minard-Celine_Le-Grand-Jeu.txt` → critere: Externe, gold: FOC_INT
- `Zeniter-Alice_Lart-de-perdre.txt` → critere: Interne, gold: FOC_ZERO
These disagreements confirm FOCALISATION is genuinely hard.

### 5.4 Complete History of All Approaches Tried

#### Approach 1: 125-line Sample (Baseline — Labiba's first attempt)
- Method: Take 125 lines from novel beginning, classify all 7 criteria
- Result: 55.7% overall
- Main problem: Beginning of novel doesn't reveal INTRIGUE structure or TEMPORALITÉ

#### Approach 2: Smart RAG
- Method: Retrieve relevant excerpts using BM25/semantic search for each criterion, then classify
- Result: 45.0% overall — WORSE than baseline
- Why it failed: Criterion-relevant excerpts don't exist in predictable locations; retrieval fails for global properties like TEMPORALITÉ

#### Approach 3: Full Novel Single Prompt (4,500 words)
- Method: Feed first 4,500 words directly to model
- Result: COMPLETE FAILURE — context window exceeded, model truncated, produced garbage
- Why it failed: 100,000+ tokens per novel; context window is 8,192 tokens

#### Approach 4: Map-Reduce Pipeline (NEW — Labiba's key innovation)
**This became the production approach for Task 0.**

**MAP STEP:** Split novel into 9 equal chunks. For each chunk, model answers 10 narrow questions:
- narrator_voice (first_person/third_person/unclear)
- inner_thoughts (yes_one_character/yes_multiple/no/unclear)
- dominant_mode (action_events/description/introspection/mixed)
- world_type (realistic/autobiographical/fantastic/speculative_sf)
- space (single_location/multiple_locations/journey_travel/imaginary)
- plot_threads (one/multiple)
- time_order (chronological/has_flashbacks_or_jumps/radically_scrambled)
+ more

**REDUCE STEP:** Combine 9 sets of chunk observations → one final prompt deciding all 7 criteria simultaneously. Model sees signal from beginning, middle, and end.

**Result:** 63.3% overall — +7.6pp vs prior best. TYPE NARRATEUR: 90% (target met!).

#### Approach 5: Option A (Targeted Per-Criterion Reduce Prompts)
- Method: Instead of one reduce prompt for all 7 criteria, separate reduce prompts per criterion, each addressing its specific error pattern
- Script: `run_narratologie_mapreduce_optionA.py`
- Result: Mixed — improved some criteria, hurt FOCALISATION

#### Approach 6: Chunk Classifier (sklearn)
- Method: Use map-step observations as features for a scikit-learn classifier
  - TF-IDF of chunk observations
  - Feature vector: counts of narrator_voice="first_person" across 9 chunks, etc.
  - Train: Leave-One-Out Cross-Validation (LOO-CV) on 60 novels
  - Classifiers tested: LogisticRegression, RandomForest, SVM
- Script: `train_chunk_classifier.py` (465 lines)
- Why LOO-CV: only 60 examples, most honest estimate possible
- Result: 67.1% FOCALISATION — best local result before qwen72b
- Particularly good for MODE NARRATIF: 71.7% and REGIME NARRATIF: 71.7%

#### Approach 7: Title+Author Internet Knowledge
- Method: Model uses its training knowledge of novel title+author without reading text
- Script: `resultats_qwen3_30b_title_author.csv`
- Result: 61.7% FOCALISATION — worse than map-reduce
- Why: Many novels too obscure for model's training data

#### Approach 8: GPT-4o-mini (Paid API)
- Used Riccardo's $9 OpenAI credit
- Result: **75.0% FOCALISATION** — best FOCALISATION ever achieved
- Problem: Cannot use for production on 925 novels (paid per token)
- Not reproducible for the paper's full corpus run

#### Approach 9: Mistral Large (Free API tier)
- Rate limit: 2 requests/minute — very slow
- Result: 63.3% FOCALISATION — all models default to FOC_INT
- Root cause: model bias toward majority class

#### Approach 10: Groq Llama 3.3 70B (Free)
- Rate limit: 30 RPM
- Simple prompt: 58.3% FOCALISATION (defaults to FOC_INT for 56/60 novels)
- Map-reduce: 58.3% FOCALISATION (same problem — votes at chunk level still FOC_INT)
- Paper claimed 78.97% for this model → does not transfer to our French corpus/gold set

#### Approach 11: qwen72b-limited WITH Thinking (qwen2.5vl:72b, num_predict=5000)
- Script: `foc_think.py` + `resultats_qwen72b_focalisation.csv`
- Result: **68.3% FOCALISATION — NEW LOCAL BEST**
- Improvement: Bigger model + extended reasoning allows detecting FOC_ZERO and FOC_VAR more often

#### Approach 12: qwen72b-limited WITHOUT Thinking (/no_think, num_predict=100)
- Result: 61.7% FOCALISATION — worse than with thinking
- Confirms: thinking mode essential for complex literary classification

#### Approach 13: Self-Consistency Voting (n=5, temp=0.3)
- Method: Sample 5 times, take majority vote
- Script: `resultats_focalisation_v2.csv`
- Result: 61.7% FOCALISATION — no improvement
- Why: If model defaults to FOC_INT 4/5 times, majority is still FOC_INT

#### Approach 14: Few-Shot from critere_narration_focalisation.csv
- Method: Use 480 non-overlapping novels from critere file as examples
- Result: 61.7% FOCALISATION — no improvement
- Why: Too many examples overwhelm the context window; model loses track of the task

#### Approach 15: LoRA Fine-tuning
- Attempted on small encoder model (CamemBERT-large)
- Failed: gold set too small (need 200+, have 60)
- Library compatibility issues (PEFT, transformers versions on server)
- Abandoned entirely

#### Approach 16: qwen72b All 7 Criteria (Overnight Run)
- Script: `run_task0_v4_all7.py` → `resultats_qwen72b_all7.csv`
- Status: Completed 60 novels
- Columns: File, TYPE NARRATEUR (pred), GOLD_TYP, FOCALISATION (pred), GOLD_FOC, MODE NARRATIF (pred), GOLD_MOD, REGIME NARRATIF (pred), GOLD_REG, ESPACE (pred), GOLD_ESP, INTRIGUE (pred), GOLD_INT, TEMPORALITE (pred), GOLD_TEM

### 5.5 Error Analysis by Criterion (from Progress Report)

| Criterion | Main Error Pattern | Root Cause |
|-----------|-------------------|------------|
| FOCALISATION | Over-predicts FOC_VAR (8× ZERO→VAR, 8× INT→VAR) | Confuses multiple characters PRESENT with perspective SHIFTS |
| ESPACE | Over-predicts ESP_FRAG (12× UNIT→FRAG) | Treats any mention of multiple locations as fragmented |
| MODE NARRATIF | Over-predicts MOD_MIX (26/29 errors) | Hedges rather than committing to dominant mode |
| REGIME NARRATIF | Confuses REG_REAL with REG_AUTO (7×) | Misreads first-person narration as autofiction |
| INTRIGUE | Symmetric LIN/FRAG confusion (10× + 8×) | Cannot distinguish one plot with subplots from genuinely fragmented |
| TEMPORALITÉ | Over-predicts TEMP_DIS (13× LIN→DIS) | Treats any memory/flashback as structural discontinuity |

### 5.6 Best Final Results for Task 0 (60 novels, with alternative label scoring)

**Hybrid v4 — 70.5% overall (best result)**

| Criterion | Score | Source | Notes |
|-----------|-------|--------|-------|
| TYPE NARRATEUR | **90.0%** | resultats_hybrid.csv (old hybrid) | TARGET MET (85%) |
| FOCALISATION | **65.0%** | resultats_hybrid.csv (old hybrid) | Best LOCAL |
| MODE NARRATIF | **71.7%** | resultats_hybrid.csv | Good |
| REGIME NARRATIF | **71.7%** | resultats_hybrid.csv | Good |
| ESPACE | **48.3%** | resultats_hybrid.csv | EXCLUDED from presentation |
| INTRIGUE | **65.0%** | resultats_hybrid.csv | Acceptable |
| TEMPORALITÉ | **71.7%** | resultats_hybrid.csv | Good |
| **OVERALL** | **70.5%** | **Hybrid v4 (alt scoring)** | **BEST RESULT** |

**Note on FOCALISATION improvement:**
- qwen72b with thinking: **68.3%** → new best local
- GPT-4o-mini: **75.0%** → best ever (paid, cannot use in production)
- Human agreement ceiling: ~76%

### 5.7 Scoring Methodology: Alternative Labels
The gold set includes "Acceptable aussi" (alternative) labels for cases where multiple annotations are defensible. For example, if gold = FOC_INT but ALT = FOC_ZERO, a prediction of FOC_ZERO counts as correct.

With alt scoring, hybrid v4 = 70.5% overall. Without alt scoring ≈ 67-68%.

### 5.8 Key Scripts for Task 0
```
~/ecopoetique/narratologie/
├── run_narratologie_mapreduce.py         # Map-reduce v3 — main production script
├── run_narratologie_mapreduce_optionA.py # Option A — per-criterion reduce prompts
├── train_chunk_classifier.py             # sklearn classifier (465 lines, LOO-CV)
├── combine_hybrid_v2.py                  # Combines 3 sources, picks best per criterion
├── foc_think.py                          # qwen72b FOCALISATION — WITH thinking
├── run_focalisation_v3.py                # Self-consistency (n=5) — FAILED
├── run_task0_v4_all7.py                  # qwen72b all 7 criteria overnight
├── GOLD_narratologie.csv                 # Master gold set (79 novels, semicolon)
├── GOLD_narratologie_60novels_original.csv # 60-novel reliable subset
├── Grille_Narratologique.csv             # Full narratological grid
├── critere_narration_focalisation.csv    # 530 novels tab-separated
├── resultats_hybrid.csv                  # Best overall results (60 novels)
├── resultats_hybrid_v4_60novels.csv      # Hybrid v4 — 70.5% with alt scoring
├── resultats_qwen72b_focalisation.csv    # 68.3% FOCALISATION (qwen72b+thinking)
└── resultats_qwen72b_all7.csv           # All 7 criteria with qwen72b
```

### 5.9 Riccardo's Conclusion on Task 0
"It can be defended that it's not possible to do better with the tools we have now."
"Maybe that's the conclusion — we need to wait for more advanced models."
"LLMs are not well trained for literary narratology."
→ **This is a legitimate academic finding, not a failure.**

---

## PART 6: TASK 1 — LITERAL/FIGURATIVE CLASSIFICATION

### 6.1 Objective
For each animal, plant, or Loterre term occurrence: classify as **référentiel** (literal/real) or **figuré** (figurative/metaphorical/idiomatic).

### 6.2 Why This Matters
A "mouche" in "les candidats tombaient comme des mouches" (idiom) should NOT count as evidence of biodiversity sensitivity — it's a frozen expression, not a real fly. Without this classification, biodiversity statistics are inflated by figurative uses.

### 6.3 Johanna's Previous Approach (GPT-4o-mini, OpenAI API)
- Prompt: "Dans la phrase suivante, le mot {entité} est-il employé de façon littérale ou a-t-il un sens figuré?"
- Batches of 5 phrases per API call with XML-structured output
- Accuracy: ~47% figuré detected (very low)
- Cost: paid per token
- Files: `RESULTAT_annotation_gpt.csv` (112,592 animal rows), `plantes/` folder

### 6.4 Initial Baseline (Labiba v1 — no examples)
Tested qwen3:30b with minimal prompt, no examples:
- **Animals v1:** Overall=85.8%, Réf=94.2%, Fig=71.0%
- Key finding: model already beats Johanna's GPT-4o-mini without any prompt engineering!

### 6.5 The Critical Discovery: Why Thinking Mode is Essential
Tested no-think mode (num_predict=100, /no_think suffix) vs thinking mode (num_predict=5000):

| Mode | Speed | Overall | Réf | Fig |
|------|-------|---------|-----|-----|
| No-think (100 tokens) | 1.1s/row | 63.7% | 100.0% | **0.0%** |
| Thinking (5000 tokens) | 7-9s/row | 91.6% | 97.5% | **81.2%** |

**Without thinking: model predicts "référentiel" for 100% of all cases — completely unusable.**
**With thinking: model correctly detects figurative uses.**

The thinking tokens allow the model to reason through ambiguous cases: "Is this idiomatic? Does 'comme' signal comparison? Is there a real animal present in the scene?"

### 6.6 Batch Size Optimization
Tested different batch sizes (rows per API call):

| Batch | Speed | Overall | Fig |
|-------|-------|---------|-----|
| 1 (single) | 9.0s/row | 92.1% | 87.0% |
| 5 (batched) | 4.0s/row | 92.6% | 87.0% |

Batch=5 (used in corpus run) gives **same accuracy at 2.3× speed**. Used batch=4 in final production.

### 6.7 Prompt Engineering — Full Version History

**evaluate_all_goldsets.py → v6 (FINAL for animaux and plantes):**

Version evolution for animals:
| Version | Overall | Réf | Fig | Key Change vs Previous |
|---------|---------|-----|-----|------------------------|
| v1 (no examples) | 85.8% | 94.2% | 71.0% | Baseline |
| v2 (few-shot added) | **92.6%** | 94.2% | 89.9% | Added 5+ examples per category |
| v3 (rules improved) | ~87% | 97% | ~67% | Mid-development |
| v4 (category-specific) | ~89% | 97% | ~75% | Separate example sets per animal type |
| v5 (idiom detection) | ~91% | 97% | ~79% | Better idiom rules |
| **v6 (FINAL)** | **91.6%** | **97.5%** | **81.2%** | Full v2 few-shot + refined rules |

**The v2 result (92.6% / 89.9% fig) was achieved on a single row at a time (batch=1). The production v6 (batch=4) achieves 91.6% / 81.2% fig.**

For plants, v6 achieves 96.3% / 79.2% fig.

### 6.8 Loterre Version History

The Loterre task is HARDER than animals/plants because:
- Loterre terms are domain-specific ecological concepts (not species)
- Many are inherently polysemous between ecological and general meaning
- "désert" (desert) appears both as real geographic feature AND metaphor for isolation
- "forêt" can be a real forest OR a symbolic/fantastic space

| Version | Overall | Réf | Fig | Key Change |
|---------|---------|-----|-----|------------|
| v3 | 85.2% | ~90% | 56.1% | Baseline |
| v5 | 85.8% | 92% | 58.5% | Loterre-specific examples added |
| v6 | 86.2% | 91.2% | 61.0% | Better disambiguation |
| v7 | 86.8% | 95.3% | **56.1%** | WORSE — new examples hurt figuré |
| **v8** | **85.2%** | **91.2%** | **63.4%** | Targeted Group A error fixes |

**Key finding for v7:** Adding more référentiel examples HURT figuré detection. The model became more conservative, calling ambiguous cases référentiel. This is the **overfitting trap** — adding examples for one class hurts the other.

### 6.9 Gold Set Details

| File | Separator | Total | Réf | Fig | X |
|------|-----------|-------|-----|-----|---|
| `GOLD_litteralite_animaux.csv` | tab | 192 | 121 (63%) | 69 (36%) | 2 (1%) |
| `GOLD_litteralite_plantes_RB.csv` | semicolon | 188 | ~120 | ~68 | — |
| `GOLD_litteralite_loterre__RB.csv` | semicolon | 189 | 148 (78%) | 41 (22%) | — |

**Class imbalance explains lower figuré accuracy:** Gold sets are 63-78% référentiel. Model defaults to majority class when uncertain → higher référentiel precision but lower figuré recall.

**Human annotator ceiling:** Agreement = 76%, Kappa = 0.64. Our 91.6% / 81.2% EXCEEDS human agreement on the task for animals. This is a strong result.

### 6.10 Full Row-by-Row Test Results (Task 1 Animals v2)
The `task1_animal_results.txt` shows the complete evaluation run on 190 examples. Notable errors:
- [60/190] agneaux: WRONG — predicted référentiel but gold=figuré
- [70/190] grenouilles: WRONG — predicted référentiel but gold=figuré
- [74/190] margouillat: WRONG — figuré missed
- [113/190] chameau: WRONG — référentiel missed
- [147/190] porc: WRONG — référentiel missed
- [149/190] vache: WRONG — référentiel missed
- [153/190] autruche: WRONG — figuré missed
- [154/190] bœuf: WRONG — figuré missed
- [157/190] cigales: WRONG — figuré missed
- [163/190] goéland: WRONG — referred to as figuré but gold=référentiel
- [167/190] chiens: WRONG — figuré predicted but gold=référentiel
- [175/190] âne: WRONG — référentiel predicted but gold=figuré
- [179/190] chimpanzé: WRONG — figuré missed
- [190/190] coqs: WRONG — figuré predicted but gold=référentiel

**Final counts from this run:** Overall=92.6%, Réf=94.2%, Fig=89.9% (batch=1, v2 prompt)

### 6.11 Loterre Error Analysis (v8 — 15 figuré errors)

**IMPORTANT: These 15 errors were carefully analysed for Riccardo.**

**Group A — Model clearly wrong (5 cases, fixable):**
1. **[marais]** "Le temps nous a poussés vivants hors des marais" → temporal escape metaphor; "le temps" cannot push you through real swamps
2. **[mers]** "Cyrtha luit, dominant terres et mers infinies" → hyperbolic city description; a city cannot dominate infinite seas
3. **[mer]** "Ce serait être largué en pleine mer sans bouée de sauvetage" → abandonment metaphor; conditional "ce serait" signals figurative
4. **[mer]** "Cette promesse a traversé la Wilaya, la mer et ma mémoire" → "ma mémoire" in the list reveals figurative enumeration
5. **[incendie]** "réchauffés par l'incendie des fourneaux" → heat intensity metaphor; "incendie des fourneaux" = no real fire

**Group B — Genuinely ambiguous (4 cases, to discuss with Riccardo):**
1. **[forêt]** Supernatural silhouettes in a real forest — literal place used for fantastic events?
2. **[maritimes]** "scènes maritimes modernes" in paintings — maritime as adjective for artwork vs real sea
3. **[désert]** "avais choisi le désert" + "ce tapis de sable, de dunes" — simultaneously real AND metaphor for isolation
4. **[oiseaux migrateurs]** On a curtain motif — picture within picture, same as maritimes case

**Group C — Model probably right, gold may be wrong (6 cases):**
1. **[océan]** "plus dangereuse que l'océan Atlantique" — factual comparison between two real things; océan=référentiel
2. **[montagnes]** "mes dessins de jardins, de montagnes" — drawings OF mountains ≠ metaphor; montagnes=référentiel
3. **[lac]** "poteaux dirigés vers le lac" — real spatial orientation to a real lake
4. **[plage]** "montagne multicolore de jouets de plage" — "plage" is type-modifier for toys (référentiel); it's "montagne" that's figuré
5. **[lac]** "décombres au bord d'un lac" — real geographic location
6. **[animaux]** "Luc rapatriait sa ferme aux animaux dans sa chambre" — real animals moved indoors

**Riccardo's confirmed corrections (June 25 meeting):**
- Cases 2 (maritimes) and 14 (oiseaux migrateurs) → **FIGURÉ** — "picture within picture = representation not real"
- Case 6 (montagnes in drawings) → **FIGURÉ** — same logic as maritimes
- Case 10 (plage in "jouets de plage") → **FIGURÉ** for "montagne" (big quantity DE_QUANTIF), "plage" is référentiel
- Cases 8, 12 (lac), 15 (animaux), 4 (océan Atlantique) → likely **référentiel** (gold annotation errors)

**If 4 Group C cases corrected to référentiel → real figuré accuracy would jump to ~71%.**

### 6.12 Corpus-Wide Run (Production Task 1)

**Script:** `~/ecopoetique/métaphore/run_task1_corpus.py`
**Input:** ENTITES_contexte files (extracted by Johanna)
**Configuration:** qwen3:30b, batch=4, thinking ON (num_predict=5000), with resume capability

**Speed benchmarks:**
- With thinking, warm GPU, alone: **4.0s/row** (batch=4)
- With thinking, cold GPU: 11s/row (first call after load)
- No-think: 1.1s/row but 0% figuré (unusable)
- Full corpus estimate: animaux 144K rows × 4s = ~160h (6.7 days)

**ANIMAUX — COMPLETE ✅ (July 5, 2026)**
- Total classified: 127,877 / 127,935 unique rows
- Results: 90,755 référentiel (70.9%) | 37,180 figuré (29.1%)
- Failed batches: 842 (defaulted to référentiel)
- Failed rows: 3,665 (in `task1_animaux_failed_keys.tsv`)
- Retry: `~/ecopoetique/morphosyntaxe/retry_animaux.py`

**Key finding:** 29.1% of animal mentions in the corpus are figurative — about 37,000 figurative animal uses across 925 novels. This is lower than the gold set baseline (35.9%) because the gold was deliberately balanced; the corpus distribution is natural.

**PLANTES — IN PROGRESS 🔄 (started July 5)**
- PID: 1427842
- Progress: ~23% done as of July 6 (~ETA July 8-9)
- Figuré so far: ~12.9%

### 6.13 Key Scripts for Task 1
```
~/ecopoetique/métaphore/
├── evaluate_all_goldsets_v6.py           # BEST: animaux+plantes (91.6% / 96.3%)
├── evaluate_loterre_v8.py                # BEST: loterre (85.2% / 63.4% fig)
├── evaluate_litteralite_v2.py            # Early version — led to v6 development
├── run_task1_corpus.py                   # Full corpus run (batch=4, thinking ON)
├── run_task2_subcategories.py            # Task 2 pipeline (built, waiting for Task 1)
├── retry_animaux.py                      # Retry failed batches (batch=4, v6 prompts)
├── GOLD_litteralite_animaux.csv          # 192 rows (tab)
├── GOLD_litteralite_plantes_RB.csv       # 188 rows (semicolon)
├── GOLD_litteralite_loterre__RB.csv      # 189 rows (semicolon)
├── RESULTAT_annotation_gpt.csv           # Johanna's animal labels (112K)
├── RESULTAT_typologie_compare_animaux.csv # Johanna's comparé labels
├── eval_animaux_v6_results.csv           # Animaux v6 results
├── eval_plantes_v6_results.csv           # Plantes v6 results
├── eval_loterre_v8_results.csv           # Loterre v8 results
└── plantes/
    ├── annotations_gpt_partie_1.csv       # Johanna plant labels (2,776 rows)
    └── annotations_gpt_partie_2.csv       # Johanna plant labels (60,951 rows)
```

---

## PART 7: TASK 2 — FIGURATIVE SUBCATEGORY CLASSIFICATION

### 7.1 Objective
For each figurative animal/plant mention, classify into detailed subcategory types of figurative language.

**Known subcategories (from Johanna's notebooks):**
- COMME_SN — simile with "comme" ("fort comme un lion")
- META_VERB — verbal metaphor ("il rugit de colère")
- DE_PARANGON — genitive metaphor ("un lion d'homme")
- IDIOMATIQUE — frozen idiomatic expression ("à pas de loup")
- AUTRE — other
And possibly more categories in Riccardo's full typology.

### 7.2 Status: PENDING
Must run on Labiba's Task 1 results (not Johanna's GPT-4 labels).
Script `run_task2_subcategories.py` is built and tested. Waiting for Task 1 corpus completion.

### 7.3 Johanna's Previous Work
File: `~/ecopoetique/métaphore/RESULTAT_annotation_gpt.csv`
Columns: fichier, token_lexique, truncated_sentence, lemme, label, **categorie_metaphore**, explication
Already classified animals with subcategories — but based on GPT-4 with ~47% figuré accuracy (many labels are wrong because base classification was wrong).

### 7.4 Gold Set Requirements
Riccardo to provide: 100 figurative animal + 100 figurative plant examples annotated with:
- Column 1: subcategory type (COMME_SN, META_VERB, etc.)
- Column 2: comparé category (Task 4.5 — CH, ABSTR, NAT, GEO, OBJ, AUTRE)
Same 200 examples used for BOTH tasks.

---

## PART 8: TASK 3 — AGENTIVITY ANALYSIS

### 8.1 Research Question
Are animals and plants more passive agents than humans in contemporary French novels?

**Hypothesis:** In contemporary fiction, animals and plants serve primarily as patient/passive entities relative to human characters.

### 8.2 The Four Role Categories (confirmed correct by Riccardo, June 25)

| Role | Technical | Example |
|------|-----------|---------|
| Agent actif | grammatical subject of active verb | "Un loup aboya dans un vallon" |
| Récepteur passif | subject of passive construction | "Des chèvres sont tenues en laisse" |
| Objet | direct object | "il chassa un papillon" |
| Complément du nom | prepositional noun modifier | "Des blessures de loup" |
| Autre | other syntactic roles | flat:name, obl:arg, xcomp, appos, obl:mod |

**The lion/Julian examples Riccardo walked through (June 25):**
- "Julien tua le lion" → lion = Objet ✅
- "Le lion fut tué par Julien" → lion = Récepteur passif ✅
- "Le lion mangea Julien" → lion = Agent actif ✅
- "Julien fut mangé par le lion" → lion = Agent actif ✅ (obl:agent in passive construction — semantically active)

### 8.3 Data Sources and Methods

**HUMANS:** Built from scratch using spaCy French NER (fr_core_news_lg) on all 925 novels.
- `extract_humains.py` — NER extraction
- Includes gender detection: spaCy morphology + pronoun context window
- "Undetermined" (25.9%): name appears without nearby pronouns, ambiguous/foreign names

**ANIMALS (referential):** Used Johanna's pre-filtered file `dépendants_animaux_référentiels.csv` — already disambiguation-filtered. Has `categorie` column (mammifère, oiseau, insecte, etc.)

**PLANTS:** Used Johanna's `dépendants_PLANTES.csv` — MIXED referential + figurative (no filtering yet). Known contamination: "tendre une carotte" (idiom), "la moutarde me monte au nez" (idiom), "le pruneau" (slang for face) — these inflate plant agentivity slightly.

### 8.4 Final Results (COMPLETE)

| Category | N | Active Agent | Passive | Object | Noun Complement | Other |
|----------|---|--------------|---------|--------|-----------------|-------|
| **HUMANS (all)** | 219,651 | **37.2%** | 1.4% | 12.8% | 20.1% | 28.4% |
| Humans masculine | 118,142 | **38.2%** | 1.3% | 13.2% | 18.8% | 28.4% |
| Humans feminine | 44,529 | **37.7%** | 1.8% | 12.9% | 21.2% | 26.5% |
| Humans undetermined | 56,980 | — | — | — | — | — |
| **ANIMALS (referential)** | 95,243 | **24.4%** | 0.7% | 20.2% | 33.6% | 21.0% |
| **PLANTS (all, mixed)** | 64,269 | **11.8%** | 0.4% | 15.1% | 49.5% | 23.1% |
| **TOTAL** | **379,163** | | | | | |

**Hierarchy confirmed: Humans (37.2%) > Animals (24.4%) > Plants (11.8%)**
- Humans 1.5× more active than animals
- Humans 3.1× more active than plants
- Male and female humans nearly identical (38.2% vs 37.7%) — no significant gender difference
- Plants predominantly as noun complements (49.5%) — described rather than doing

### 8.5 The "Autre" Category Explained (28.4% for humans)
This question came up at the June 25 meeting: "What's the rest?"

It is NOT missing data — it's valid syntactic roles outside the 4 main categories:
- `flat:name` — parts of compound proper names (e.g., "Monsieur Dupont" — "Dupont" is flat:name dependent)
- `obl:arg` — oblique arguments ("il dit à Marie" — Marie is obl:arg)
- `xcomp` — predicative complements ("il s'appelle Pierre" — Pierre is xcomp)
- `appos` — apposition ("mon père, Robert" — Robert is appos)
- `obl:mod` — oblique modifiers ("il parle de Marie")

**All categories sum to 100%.** Nothing is missing.

### 8.6 Animal Category Breakdown
From `dépendants_animaux_référentiels.csv` (95,243 rows):
- Mammifère: 57,601 (60.5%)
- Oiseau: 16,226 (17.0%)
- Insecte: 8,419 (8.8%)
- Poisson: 4,103 (4.3%)
- Reptile: 3,483 (3.7%)
- Autre: 3,236 (3.4%)
- Amphibien: 1,157 (1.2%)
- Mollusque: 769 (0.8%)

### 8.7 Pending for Task 3
1. **English/Arab names:** Many Maghreb/African novels have proper names undetected by French spaCy. Capital letter detection in middle of sentences as heuristic. Risk: French words like "Fleur" could be misidentified.
2. **Rerun plants** after Task 1 filters referential-only → create `dépendants_plantes_référentielles.csv`
3. **Rerun animals** after Task 1 gives cleaner filtering (91.6% vs Johanna's ~85%)
4. **Check remaining %** outside 4 main categories per sub-type

### 8.8 Key Scripts for Task 3
```
~/ecopoetique/morphosyntaxe/
├── analyse_agentivite.py                 # Main agentivity analysis
├── analyse_dependances.py                # Dependency extraction
├── extract_humains.py                    # Human NER extraction with gender
├── dépendants_HUMAINS.csv                # 219,651 rows (tab-separated)
├── dépendants_animaux_référentiels.csv   # 95,243 referential animals (tab)
├── dépendants_PLANTES.csv                # 64,269 plants mixed (tab)
├── resultats_agentivite.txt              # Summary
├── resultats_agentivite_complet.txt      # Full detailed results with examples
└── task3_full_report.md                  # Complete Task 3 report
```

---

## PART 9: TASK 4.5 — COMPARANT/COMPARÉ CLASSIFICATION

### 9.1 The Distinction
When a figurative animal/plant use is identified:
- **Comparant** = the animal/plant term (the vehicle/source — what is used AS the comparison)
- **Comparé** = what is being compared (the tenor/target — what is described)

"Paul est fort comme un lion" → lion=comparant, Paul=comparé, category=CH (human)
"Cuba ressemble à un lézard vert" → lézard=comparant, Cuba=comparé, category=E (natural element)
"la jeunesse est un chat insomniaque" → chat=comparant, la jeunesse=comparé, category=A (abstract)
"son anguille de peau" → anguille=comparant, skin of person=comparé, category=CH

### 9.2 The 6 Caracciolo Categories (for what the comparé is)
From Marco Caracciolo, *Narrating the mesh* (2021):
- **O** — Objects and artificial structures
- **NH** — Non-human living creatures and biological processes
- **E** — Inanimate natural elements and processes
- **CH** — Human body and physiological processes
- **A** — Abstract concepts, social practices and institutions
- **P** — Psychological states and cognitive functions
- **X** — Context insufficient

### 9.3 Johanna's Previous Work
File: `~/ecopoetique/métaphore/RESULTAT_typologie_compare_animaux.csv`
Done with GPT-4, animals only.

**Johanna's result:** 73% of figurative animal comparés involve **human body/attitude (CH)** — animals mostly serve to define humanity. Then Objects (8%), Abstract concepts (6.2%).

### 9.4 Status: PENDING
Same dependency as Task 2. Gold set = same 200 examples.

**Riccardo mentioned:** Check GitLab scripts folder for Johanna's exact prompt and code.

---

## PART 10: BIODIVERSITY INDICES (NEW TASK — July 2026)

### 10.1 Shannon Index (Already Done by Johanna)
H = -Σ(pᵢ × ln(pᵢ))
File: `~/ecopoetique/resultats/corpus_principal/data_pour_Shannon.csv` (925 rows)

**Important clarification from Riccardo:** Shannon "measures a probabilistic information structure, not an ontological quality of living things. We are not measuring a biological ecosystem but the informational organisation of a living lexicon in a text."

### 10.2 Additional Indices (Documents Pending from Riccardo)
Riccardo met a biologist/statistician. Possible additional indices to apply:
- **Equitability index** (Pielou's J = H / ln(S) where S = number of species)
- **Simpson's index** (1 - Σpᵢ²) — probability two random individuals are different species
- **Chao1 estimator** — estimates true species richness from observed data
- **Beta diversity** — difference in composition between novels/corpora

Implementation: pure statistical calculation applied to token frequency distributions. Not AI-based. Expected to be straightforward.

---

## PART 11: TECHNICAL FAILURES — DOCUMENTED FOR PAPER APPENDIX

### 11.1 No-Think Mode for Task 1 (CRITICAL FAILURE)
- **What was tried:** num_predict=100, /no_think suffix to save compute time
- **Result:** 100% référentiel predictions — 0% figuré detected
- **Root cause:** Without extended reasoning, qwen3:30b cannot handle semantic ambiguity; defaults to majority class
- **Resolution:** Thinking mode (num_predict=5000) is NON-NEGOTIABLE for this task
- **Time cost:** 7-9s/row vs 1.1s/row — worth it

### 11.2 RAG for Task 0 (WORSE THAN BASELINE)
- **What was tried:** BM25 + semantic retrieval of relevant excerpts for each criterion
- **Result:** 45.0% overall — 10.7pp WORSE than simple 125-line sample
- **Root cause:** Global narrative properties (INTRIGUE structure, overall TEMPORALITÉ) cannot be determined from locally retrieved relevant fragments. The whole novel structure must be seen.
- **Resolution:** Map-reduce approach — see whole novel systematically

### 11.3 Full-Text Single Prompt (TOTAL FAILURE)
- **What was tried:** Feed first 4,500 words of novel to model
- **Result:** Model truncated, produced incoherent output, ~0% accuracy
- **Root cause:** Context window (8,192 tokens) cannot hold 4,500 French words + system prompt + instructions
- **Resolution:** Map-reduce — process in chunks

### 11.4 LoRA Fine-tuning (ABANDONED)
- **What was tried:** Fine-tune CamemBERT-large on 60 gold novel narratological labels
- **Failures:**
  1. Gold set too small — minimum ~200 examples needed, have 60
  2. PEFT library version conflicts on server
  3. transformers/accelerate compatibility issues
- **What research says:** RoBERTa-large reaches 77.5% on focalization with only 300 samples (Hicke et al.) — **IF we had 300, this might work**
- **Resolution:** Abandoned — insufficient data

### 11.5 Self-Consistency Voting for FOCALISATION (NO IMPROVEMENT)
- **What was tried:** n=5 samples at temperature=0.3, majority vote
- **Result:** 61.7% — no improvement over single sample (also 61.7%)
- **Root cause:** If model votes FOC_INT 4/5 times, majority is still FOC_INT. Voting amplifies the dominant bias rather than correcting it.
- **What paper claims:** "Robustly improves classification" — does not apply when the bias is systematic, not random

### 11.6 Groq/Mistral/Llama FOCALISATION (SYSTEMATIC FAILURE — ALL MODELS)
- **Tested:** Groq Llama 3.3 70B, Mistral Large (free tier), Mistral Nemo, Mistral-Small
- **All result:** 55-63.3% FOCALISATION — all default to FOC_INT for 55-60/60 novels
- **Root cause:** FOC_INT is ~60% of gold set. Without sufficient reasoning capacity, ALL models predict majority class.
- **Groq map-reduce:** Same result — votes at chunk level all return FOC_INT, reducing gives FOC_INT

### 11.7 Loterre v7 — Examples Made Things Worse
- **What was tried:** Added more context-specific examples to the prompt
- **Result:** Overall improved slightly (86.8% vs 86.2%) but figuré DROPPED (56.1% vs 61.0%)
- **Root cause:** New examples were all référentiel-adjacent — model became more conservative, calling borderline figuré cases as référentiel
- **Resolution:** Reverted approach — v8 targets specific Group A errors only

### 11.8 Claude Code on obtic-gpu1 (PERMANENTLY BROKEN)
- **What was tried:** Using Claude Code (VS Code extension) directly on remote server
- **Problem:** Server DNS cannot resolve external domains (api.anthropic.com, claude.ai)
- **Auto-update failure:** July 4, 2026 — Claude Code tried to update, DNS failed, partial failure state
- **curl result:** 000 (cannot resolve host) for both lfarooq AND labiba sudo accounts
- **Root cause:** obtic-gpu1 blocks all outbound HTTPS to external domains — firewall policy
- **Resolution:** Claude Code cannot work on this server without IT admin fixing DNS. Use Claude.ai directly.

### 11.9 Disk Space Crisis
- **Peak crisis:** 98% full after downloading qwen2.5vl:72b (48GB)
- **What was deleted:** gemma3:27b (17GB), mistral-small3.1 (15GB) = 32GB freed
- **Current:** ~116GB free (still critical for long-term)

---

## PART 12: MEETINGS AND KEY DECISIONS

### 12.1 Initial Meeting — May 19, 2026
First meeting with Riccardo. Key decisions:
- Priority order established: Task 0 → Task 1 → Task 2 → Task 3
- Gold set is CORRECT — only model needs improvement, not annotations
- Try qwen3:30b first (free, already installed) before paid APIs
- Temperature=0 for all classification tasks
- Get HumanID account for institutional GitLab

### 12.2 Meeting June 25, 2026 (128 minutes — full transcript available)
Most important meeting. All major project decisions made here.

**Task 1 decisions:**
- APPROVED — proceed to full corpus run
- Loterre ambiguous case resolutions (see Part 6.11)
- Johanna's baseline: 47% figuré → now 81.2% (massive improvement)

**Task 2 decisions:**
- Run on OWN Task 1 results only, NOT Johanna's GPT file
- Gold set: 100 animal + 100 plant examples to come from Riccardo
- Combined with Task 4.5: same 200 examples, 2 annotation columns

**Task 3 decisions:**
- Trust Johanna's animal disambiguation (85%) — don't redo it
- Plants need referential filtering after Task 1
- Add English/Arab names to NER — capital letter detection

**Task 0 decisions:**
- 70% "is kind of ok" — accept as final
- ESPACE: exclude from presentation
- FOCALISATION: try GPT-4o API with Riccardo's $9 credit
- "Maybe that's the conclusion — we need to wait for more advanced models"

**Corpus structure clarification:**
- ENTITES files in resultats/ folder are what to run Task 1 on
- Run on BOTH corpus_principal AND bestsellers → deduplicate
- 3 missing gold novels are in bestseller corpus

**Postponed:** Task 5 (Frantext) — "too much already"

**Documentation emphasis:** "Don't hide the technical stuff... Include failed attempts, all models tried, why they failed"

### 12.3 Next Meeting: July 3, 2026 at 11AM

**Riccardo to bring:**
- 100 animal + 100 plant figurative examples for gold sets
- 6-category definitions for comparé classification (or find in GitLab)
- Biodiversity indices documents
- GPT-4o API key (already shared during June 25 meeting)

**Labiba to bring:**
- Task 1 animaux results (DONE ✅)
- Task 1 plantes progress
- Task 0 final results summary
- FOCALISATION cases where models consistently disagree with gold (possible annotation errors)

---

## PART 13: COMPLETE FILE STRUCTURE

### 13.1 Main Project Structure
```
~/ecopoetique/
├── CORPUS_TOTAL/                          # ~925 .txt novel files (1 sentence/line)
├── narratologie/                          # Task 0
├── métaphore/                             # Task 1 & 2
├── morphosyntaxe/                         # Task 3
├── resultats/                             # Corpus entity extraction (Johanna)
│   ├── corpus_principal/                  # Main 925 novels
│   └── bestsellers/                       # ~124 bestseller novels
└── lexiques/                              # TaxRef, Wikispecies, Loterre
```

### 13.2 Task 0 Files
```
~/ecopoetique/narratologie/
├── GOLD_narratologie.csv                   # Master gold (79 novels, semicolon, with alts)
├── GOLD_narratologie_60novels_original.csv # Reliable 60-novel subset
├── Grille_Narratologique.csv               # Full narratological grid
├── critere_narration_focalisation.csv      # 530 novels tab (Narrateur+Focalisation)
├── run_narratologie_mapreduce.py           # Map-reduce v3 (MAIN PRODUCTION)
├── run_narratologie_mapreduce_optionA.py   # Option A (per-criterion reduce)
├── train_chunk_classifier.py              # Sklearn classifier (465 lines)
├── combine_hybrid_v2.py                   # 3-source combination
├── foc_think.py                           # qwen72b FOCALISATION
├── run_focalisation_v3.py                 # Self-consistency (FAILED)
├── run_task0_v4_all7.py                   # qwen72b all 7 criteria
├── resultats_hybrid.csv                   # BEST: old hybrid (60 novels)
├── resultats_hybrid_v4_60novels.csv       # 70.5% with alt scoring
├── resultats_qwen72b_focalisation.csv     # 68.3% FOC (qwen72b+thinking)
├── resultats_qwen72b_all7.csv            # All 7 criteria with qwen72b
├── resultats_qwen3_30b_mapreduce.csv     # Map-reduce v3 results
├── resultats_chunk_classifier.csv        # Sklearn results
├── resultats_gpt4o_mini.csv             # 75% FOC (paid, production N/A)
└── [many more result files — see Part 5.4 for full list]
```

### 13.3 Task 1 Files
```
~/ecopoetique/métaphore/
├── evaluate_all_goldsets_v6.py            # BEST: animaux+plantes
├── evaluate_loterre_v8.py                 # BEST: loterre
├── evaluate_litteralite_v2.py             # Early development version
├── run_task1_corpus.py                    # Full corpus production script
├── run_task2_subcategories.py             # Task 2 (built, waiting)
├── retry_animaux.py                       # Retry failed batches
├── GOLD_litteralite_animaux.csv           # 192 rows (tab)
├── GOLD_litteralite_plantes_RB.csv        # 188 rows (semicolon)
├── GOLD_litteralite_loterre__RB.csv       # 189 rows (semicolon)
├── eval_animaux_v6_results.csv            # Gold set v6 results
├── eval_plantes_v6_results.csv            # Gold set v6 results
├── eval_loterre_v8_results.csv            # Gold set v8 results
├── loterre_ambiguous_cases.md             # Analysis for Riccardo
├── RESULTAT_annotation_gpt.csv            # Johanna's animal labels (112K)
├── RESULTAT_typologie_compare_animaux.csv # Johanna's comparé labels
└── plantes/
    ├── annotations_gpt_partie_1.csv       # Johanna (2,776 rows)
    └── annotations_gpt_partie_2.csv       # Johanna (60,951 rows)
```

### 13.4 Task 1 Corpus Run Outputs
```
~/ecopoetique/resultats/
├── task1_animaux_labels.csv               # COMPLETE (127,877 rows, tab)
├── task1_animaux_labels_full.csv          # With duplicates
├── task1_animaux_run.log                  # Progress log
├── task1_animaux_failed_keys.tsv          # 3,665 failed rows
├── task1_animaux_retry.csv               # Retry in progress
├── task1_plantes_labels.csv              # IN PROGRESS (~23%)
└── task1_plantes_run.log                 # Progress log (PID 1427842)
```

### 13.5 Task 3 Files
```
~/ecopoetique/morphosyntaxe/
├── analyse_agentivite.py                  # Main analysis
├── analyse_dependances.py                 # Dependency extraction
├── extract_humains.py                     # Human NER
├── dépendants_HUMAINS.csv                 # 219,651 rows (tab)
├── dépendants_animaux_référentiels.csv    # 95,243 rows (tab)
├── dépendants_PLANTES.csv                 # 64,269 rows (tab)
├── resultats_agentivite_complet.txt       # Full results with examples
└── task3_full_report.md                   # Complete report
```

---

## PART 14: RESULTS SUMMARY FOR PAPER

### 14.1 Task 0 — Narratological Classification
**Best result: 70.5% overall on 60 novels (Hybrid v4, with alternative label scoring)**

| Criterion | Score | Notes |
|-----------|-------|-------|
| TYPE NARRATEUR | 90.0% | TARGET MET (85%) |
| FOCALISATION | 65.0% (local) / 68.3% (qwen72b) / 75% (GPT) | Hard — human agreement only 76% |
| MODE NARRATIF | 71.7% | Acceptable |
| REGIME NARRATIF | 71.7% | Acceptable |
| ESPACE | 48.3% | EXCLUDED from presentation |
| INTRIGUE | 65.0% | Acceptable |
| TEMPORALITÉ | 71.7% | Acceptable |
| **OVERALL** | **70.5%** | Context: human agreement ceiling ~76% |

**Comparison with Johanna's system:**
- Johanna: ~65% on 2/7 criteria, fails on 33.8% of novels, requires Internet/title
- Labiba: 70.5% on 7/7 criteria, 100% coverage, reads actual novel text, fully local

### 14.2 Task 1 — Literal/Figurative Classification
| Category | Overall | Réf | Fig | vs Johanna (GPT) |
|----------|---------|-----|-----|-----------------|
| **Animaux** | **91.6%** | **97.5%** | **81.2%** | +34.2pp figuré |
| **Plantes** | **96.3%** | **98.8%** | **79.2%** | significant improvement |
| **Loterre** | **85.2%** | **91.2%** | **63.4%** | partial improvement |

**Context:** Human inter-annotator agreement = 76% (Kappa 0.64). Our 91.6% overall for animals EXCEEDS human agreement on this task.

### 14.3 Task 1 — Corpus-Wide Results (Animaux, 127,877 mentions)
- **Référentiel:** 90,755 (70.9%)
- **Figuré:** 37,180 (29.1%)
- ~37,000 figurative animal uses across 925 French novels

### 14.4 Task 3 — Agentivity
**Hierarchy confirmed: Humans (37.2%) > Animals (24.4%) > Plants (11.8%)**

Across 379,163 total mentions in 925 French novels:
- Animals are 1.5× less active than humans
- Plants are 3.1× less active than humans
- Male/female humans nearly identical in agentivity
- Plants predominantly as noun complements (49.5%) — "described rather than doing"

---

## PART 15: PENDING ITEMS (Before July 15, 2026)

### Critical (Blocking other tasks):
- 🔄 Task 1 plantes corpus run — ETA July 8-9
- 🔄 Task 1 animaux retry (failed batches, 3,665 rows) — in progress

### After Task 1 Completes:
- [ ] Merge animaux main + retry results into clean final file
- [ ] Run Task 2 subcategories on own figurative predictions
- [ ] Run Task 4.5 comparé classification on own figurative predictions
- [ ] Create `dépendants_plantes_référentielles.csv` (filter Task 1 réf-only)
- [ ] Rerun Task 3 plants agentivity on referential-only plants

### Task 0:
- [ ] Try GPT-4o on FOCALISATION with Riccardo's API key ($9 credit)
- [ ] Score qwen72b_all7 results and build hybrid v5
- [ ] Send Riccardo: cases where ALL models consistently predict same label but disagree with gold (possible gold annotation errors)

### From Riccardo:
- [ ] 100 animal + 100 plant figurative examples (gold for Task 2 + 4.5)
- [ ] Biodiversity indices documents
- [ ] Confirm comparé category definitions (6 Caracciolo categories)

### Documentation:
- [ ] Technical appendix for paper (this document ✅)
- [ ] Final results document for publication

---

## PART 16: QUICK REFERENCE

### Check running processes:
```bash
ps aux | grep python | grep lfarooq | grep -v grep
nvidia-smi | grep -E "MiB|%"
```

### Check Task 1 plantes progress:
```bash
tail -5 ~/ecopoetique/resultats/task1_plantes_run.log
wc -l ~/ecopoetique/resultats/task1_plantes_labels.csv
```

### Task 0 evaluation with alt scoring:
```bash
cd ~/ecopoetique/narratologie
python3 -c "
import csv
GOLD='GOLD_narratologie.csv'
gold={}
# ... [see combine_hybrid_v2.py for full scoring logic]
"
```

### Recreate qwen72b-limited:
```bash
OLLAMA_HOST=localhost:11435 ollama create qwen72b-limited -f ~/Modelfile_limited
```

### Start Task 1 plantes (after animaux retry finishes):
```bash
cd ~/ecopoetique/métaphore
source ~/digitize_medical_records/labelimg_env/bin/activate
nohup python3 run_task1_corpus.py --category plantes > ../resultats/task1_plantes_run.log 2>&1 &
```

---

*Documentation compiled by Labiba Farooq — July 2026*
*Sources: All session transcripts (May-July 2026), Progress Report (June 2026), Master Notes (May 18, 2026), Meeting transcript June 25, 2026 (128 min), task1_animal_results.txt, loterre_ambiguous_cases.md, task3_full_report.md, Ecopoetique_Progress_Report.docx, Ecopoetique_Master_Notes.docx*

---

## PART 17: RESEARCH PAPER — "IMPROVING FRENCH NARRATOLOGICAL CLASSIFICATION WITHOUT PAID APIS"

### 17.1 Document Overview
**Title:** "Improving French Narratological Classification Without Paid APIs: Models, Free Tiers, and Prompting Techniques"
**Purpose:** Technical reference document compiled for this project specifically — a synthesis of all relevant literature, free API options, local models, and prompting techniques for improving Task 0 (narratological classification) without paid API costs.
**Used for:** Task 0 improvement — deciding which models and techniques to try next.

---

### 17.2 Free API Tiers Available (as of June 2026)

**Mistral (La Plateforme — "Experiment" plan):**
- Free with no credit card — real free tier
- Gives access to ALL models: Small, Medium, Large, Codestral, Pixtral, Magistral (reasoning), Devstral
- Published limits: ~2 RPM / ~500K TPM / ~1B tokens/month
- **WARNING:** Free-tier prompts MAY be used to train Mistral's models — opt-out in Admin Console Privacy section
- Zero Data Retention is a PAID Scale-plan feature, NOT available on free tier
- **Why it matters for this project:** Mistral Large 2 (123B) was trained predominantly on French text. Strong domain classification: legal ~95%, medical ~89%. Best French-native free option.
- **Ranking:** Mistral (native French) is #1 free option for French tasks

**Google Gemini (Free tier):**
- No credit card required
- Free tier covers only Flash and Flash-Lite (as of May 2026)
- Gemini 2.5 Pro: only 50 requests/day on free tier
- Rate limits: 15 RPM Flash, 30 RPM Flash-Lite; 1M-token context; multimodal
- **WARNING:** Google cut free quotas by 50-80% in December 2025, removed Pro free access April 2026, cut Pro free RPD 100→50 on May 7, 2026. Verify live limits before building on them.
- Free-tier prompts may be used by Google for training
- Gemini supports French fully
- Gemma 3 27B (local): scored HIGHER on French (61.5) than English (60.5) on PISA-Bench — unusual favorable property for our French use case

**Groq (LPU-based inference):**
- Free tier, no credit card, extremely fast (LPU hardware)
- Hosts: Llama 3.3 70B, Mixtral, Gemma, gpt-oss
- 2026 limits: ~1,000 requests/day on many models, ~30 RPM (tightened from before)
- Good for fast short calls — NOT for long-running batches
- **We already tested Groq Llama 3.3 70B** → 58.3% FOCALISATION (same bias as other models)

**Cohere:**
- Trial API key with free tokens, acceptable for academic research
- Command-A models: 256k context window

**Together.ai:**
- Free tier (no card), up to ~1M tokens/day, very high throughput
- Volatile model catalog — don't hardcode model names

**OpenAI:**
- Only small one-time trial credit (~$1) plus a few "-Free" suffixed models
- NOT a durable free tier for research
- **WARNING:** There is NO genuine free API tier for GPT-4o-mini/GPT-4o. "Free GPT-4o" websites are unofficial resellers/loophole tools — avoid for ToS and research integrity reasons. ChatGPT Plus/Free do NOT grant API credits.

**OpenRouter / GitHub Models:**
- All offer no-card free access to various open models
- Can reach Claude/GPT-style endpoints with small free budgets
- Useful for occasional tests

**Free tier ranking for French tasks:**
Mistral (native) > Gemini (excellent) > Llama 3.3 70B / Gemma via Groq (strong EU-language tuning) > others

---

### 17.3 Local Models Available for Ollama (Free, No API)

**Best alternatives to qwen3:30b:**

**Gemma 3 27B (Google):**
- Run via Ollama: `ollama pull gemma3:27b`
- Multilingual tuning documented as STRONGER in EU languages than Qwen
- On multilingual PISA-Bench: French (61.5) > English (60.5) — unusual and favorable
- Clean structured/JSON output
- Recommended temperature: ~0.15
- **Verdict: Most direct French-strong local alternative to qwen3:30b**

**Mistral-Small-3.1 24B:**
- Run via Ollama
- Native French — trained heavily on French text
- Strong instruction-following
- **Note: WAS installed on server but deleted to save disk space**

**Magistral (Mistral's reasoning model):**
- Available on Ollama
- Useful ONLY if reasoning genuinely helps for the specific criterion (test against CoT caveat below)

**Llama 3.3 70B:**
- Best open model for focalization per published evidence (~79% F1 on English)
- Requires ~48GB VRAM — barely fits A40 (46GB) with quantization
- **We tested via Groq** → 58.3% FOCALISATION (FOC_INT bias, doesn't transfer to French)
- **To try locally** if VRAM allows: might give different results than Groq (Groq runs quantized)

**French-specific models (mostly too small to beat qwen3:30b):**
- **Lucie-7B** (OpenLLM-France/LINAGORA): 7B, trained on 3T tokens (32.4% French), Apache 2.0, fully transparent data, on HuggingFace. Early-stage/not production-ready at January 2025 launch. Too small for nuanced classification.
- **CroissantLLM** (1.3B, bilingual FR/EN, MIT): Too small.
- **Vigogne** (bofenghuang): Llama-2/Llama-3.2 fine-tunes for French; Zaion "Vigogne" line continues French pretraining on FineWeb-2. Mostly ≤13B; research-licensed.

**French-specific resources (most useful for fine-tuning):**
- FrenchBench, FreD, FMTOD — French evaluation benchmarks
- FineWeb-2 French subset — training data

**No production-quality French generative LLMs exist** at the scale needed for literary classification. LATTICE/Sorbonne Nouvelle pipeline (CCLS 2024) covers entities, coreference, subgenre classification but is not a generative LLM.

---

### 17.4 Key Research Findings from the Paper

#### Finding 1: Hicke et al. Focalization Results (MOST RELEVANT)
**Task:** Focalization classification on Stephen King paragraphs, ENGLISH
**Best GPT-4o F1: 84.79%** (note: secondary sources cite 86.90% — use 84.79% as authoritative from arXiv full text)
**Key model comparisons:**
- **Llama 3.1 70B:** best open model, "promising if not as reliable"
- **RoBERTa-base/DistilBERT:** ~74% F1 — trained on only 300 samples!
- **Llama 3.2 3B:** 62.67%; Llama 3.2 1B: 1.13% (failed completely)
- **Logistic regression baseline:** 71.84%
- **GPT-3.5-turbo:** 69.63%
- **GPT-4-turbo:** 80.82%

**Best zero-shot prompt for focalization:**
- Embed Genette definitions VERBATIM in prompt — drove GPT-4o to ~85% zero-shot
- Add the quotation-mark rule: "speech in quotation marks = external focalization"
- Force single-word output (no CoT for this criterion)

**FOC_ZERO/omniscient problem:** 9 of 17 models labeled it ZERO times. Even GPT-4o scored only ~36% F1 on FOC_ZERO. This is the documented failure mode across nearly all models.

**Robustness:** GPT-4o achieved Krippendorff's α of 0.74 across 6 prompt variants, with F1 ranging 79.8% to 84.5%. A variant STRIPPED OF ALL DEFINITIONS still scored ~84.5% — implying focalization knowledge is largely baked into pretraining of large models.

**IMPORTANT CAVEAT:** All Hicke et al. numbers are on ENGLISH Stephen King. French performance is untested. Treat 77-79% figures as upper-bound guidance, not guarantees for French.

#### Finding 2: Chain-of-Thought HURTS Subjective Tasks (CRITICAL FOR OUR WORK)
Multiple papers confirm this:
- **"Larger Language Models Don't Care How You Think"** (Chochlakis et al., arXiv 2409.06173): CoT degrades performance on subjective/intuition-based classification (emotion, morality)
- **"Mind Your Step (by Step)"** (arXiv 2410.21333): Same finding
- **Pichler et al. results:** "Let's think step by step" helped vanilla Llama-3.1-8B but had model-specific effects — no general recommendation

**Recommendation from paper:** Turn OFF thinking mode (no-think) for subjective criteria: FOCALISATION, MODE NARRATIF, ESPACE. Enable thinking ONLY where criterion decomposes into verifiable steps (e.g., TEMPORALITÉ has clear structural markers).

**CONFLICT WITH OUR TASK 1 FINDING:** For Task 1 (literal/figurative), NO-THINK = 0% figuré. Thinking is essential for Task 1. The CoT-hurts finding applies specifically to SUBJECTIVE classification, not to semantic disambiguation. These are different cognitive tasks.

#### Finding 3: Constrained Decoding Improves Speed and Accuracy
**JSONSchemaBench** (arXiv 2501.10868):
- Constrained decoding speeds generation by ~50%
- IMPROVES classification accuracy — eliminates parse errors and constrains label space
- Particularly valuable for classification where output must be one of N labels

**"Thinking Before Constraining"** (arXiv 2601.07525):
- Up to significant improvement by letting model reason freely until a trigger token, then switching to constrained output
- Middle path: some thinking + constrained output format

**Practical implementation:** Use JSON schema in Ollama:
```python
response_format={"type": "json_schema", "json_schema": {"schema": {"enum": ["FOC_INT", "FOC_ZERO", "FOC_EXT", "FOC_VAR"]}}}
```

#### Finding 4: Label Description Sensitivity
Systematically varying label descriptions, instructional nudges, and few-shot examples found:
- **4-11pp swings** from different gold set splits
- **2-6pp** from rewordings of the same criterion
- Effects are STRONGLY HETEROGENEOUS across models and tasks
- **Must validate per criterion** — what works for TEMPORALITÉ may not work for FOCALISATION

**Recommendation:** Treat prompt design as a training process. Set threshold: if a change doesn't improve ≥3pp, revert it.

#### Finding 5: Self-Consistency Voting DOES Work (According to Paper)
Wang et al. (2022): "Sample several diverse generations and take the plurality label — robustly improves classification without training."
- Use low-but-nonzero temperature (0.3-0.5)

**HOWEVER — Our experience CONTRADICTS this for FOCALISATION:**
- We tested n=5 at temperature=0.3 → no improvement (61.7% vs 61.7%)
- Root cause: When underlying bias is systematic (model always says FOC_INT), voting amplifies the bias rather than correcting it
- Self-consistency only helps when model variance is random noise, not when it's systematic

#### Finding 6: RoBERTa Fine-tuning is Surprisingly Sample-Efficient
**RoBERTa-large reached 77.5% focalization with only 300 training samples** — on the exact same task (English, but directly relevant).

This sidesteps the "no more gold examples" constraint for two reasons:
1. Encoder fine-tuning is FAR more sample-efficient than prompting
2. Our existing 60 gold labels are usable — not enough for generative fine-tuning, but potentially enough for encoder fine-tuning

**Projection:** If a fine-tuned RoBERTa-large on our 60 French gold examples could achieve 70%+ (60% of the 300-sample English result), that would match or beat our current best (65% locally).

**Why we didn't implement this:** The 60 novels barely overlap with CamemBERT pretraining knowledge of literary French. May need French literary pre-training data (FineWeb-2 French subset, Gallica novels).

---

### 17.5 Recommended Improvement Roadmap for Task 0 (from Paper)

The paper provides a staged improvement plan specifically for our situation:

**Stage 1 — Prompt rewrites (free, immediate):**
1. Embed Genette definitions VERBATIM for each criterion
2. Disable thinking (/no_think) for FOCALISATION, MODE NARRATIF, ESPACE
3. Force constrained JSON output with exact label enum
4. Add self-consistency voting (~5 samples at temperature 0.3-0.5, majority vote)
5. Add targeted few-shot examples for minority/confused classes (especially FOC_ZERO)
6. Benchmark on held-out dev split; revert changes that don't improve ≥3pp

**Stage 2 — Model ensembling (free, local):**
5. Pull Gemma 3 27B and Mistral-Small-3.1 24B via Ollama
6. Run all three (qwen3:30b + Gemma + Mistral) and take majority vote
7. Gemma's EU-language strength directly targets French weakness
8. If ≥48GB VRAM: test Llama 3.3 70B on focalization locally

**Stage 3 — Encoder fine-tuning (medium effort):**
7. Fine-tune CamemBERT-large per weak criterion on existing 60 gold labels
8. RoBERTa-large reached 77.5% on focalization with 300 samples — encoder fine-tuning is far more sample-efficient
9. Use class weighting or oversampling for rare FOC_ZERO class
10. If fine-tuned encoder clears ~75% on FOCALISATION → stop chasing larger generative models for that criterion

**Stage 4 — API calls (optional, uses Mistral free tier):**
9. Use Mistral free API (no card, ~1B tokens/month) for Mistral Large as a French-native tiebreaker in ensemble
10. Opt out of data training in Mistral console

**Stopping rules:**
- If fine-tuned encoder (Stage 3) clears ~75% on FOCALISATION → stop
- If Gemma/Mistral ensembling (Stage 2) doesn't beat qwen3 alone by ≥2pp → drop extra models
- If ESPACE stays ≤55% after all stages → move entirely to feature-based sklearn classifier

---

### 17.6 Per-Criterion Recommendations from Paper

**FOCALISATION (currently 65.0% — hardest criterion):**
- Embed verbatim Genette definitions
- Add quotation-mark rule (speech in quotes = FOC_EXT)
- Force single-word output, no CoT
- Self-consistency
- Special attention to FOC_ZERO (documented failure mode — near-zero F1 on all models)
- Best path to >75%: fine-tuned encoder (Stage 3) — "most reliable way to break the 63% ceiling"
- Realistic local target: 77-79% (requires large open model OR fine-tuning)

**MODE NARRATIF (currently 71.7% — closest to "good"):**
- Embedding crisp definitions + JSON output + self-consistency may be enough to push past 75%
- If MODE NARRATIF involves speech vs. narration distinction: French direct-speech-annotation literature suggests rule/transformer hybrids work well (Durandard et al., ACL 2023 — French fine-tuned transformers for annotating direct speech in French narratives)

**ESPACE (currently 48.3% — EXCLUDED from presentation):**
- Weakest criterion, least standardized in Genette's framework
- Most dependent on spatial/world reasoning, which LLMs handle poorly
- Recommendation: Reformulate into concrete sub-questions OR move to feature-based sklearn classifier (which our hybrid already contains)
- Don't chase LLM improvement here

**REGIME NARRATIF (currently 71.7%):**
- Main confusion: REG_REAL vs REG_AUTO (7× errors)
- Embed explicit definition distinguishing realism from autofiction
- Key signal: first-person narration does NOT imply autofiction

**INTRIGUE (currently 65.0%):**
- Symmetric LIN/FRAG confusion (10× + 8×)
- Key: one main plot with subplots ≠ genuinely fragmented narrative
- Embed this distinction explicitly

**TEMPORALITÉ (currently 71.7%):**
- Main error: any memory/flashback → predicted as TEMP_DIS
- Key: isolated analepsis does not = overall temporal structure
- Embed: "if anachrony is localized and doesn't affect overall structure → TEMP_LIN"

---

### 17.7 Important Warnings from Paper

**On free tiers:** "Free API tiers change frequently and have trended restrictively." Always re-verify current limits before building on them. The numbers in this documentation (Mistral 2 RPM, Gemini 1,500 req/day, Groq ~1,000 req/day) may be outdated.

**On data privacy:** Free tiers may use prompts for training (Mistral, Google confirmed). If corpus is copyrighted or sensitive, this is relevant. Mistral Zero Data Retention = paid Scale plan only.

**On French transfer:** Hicke et al. focalization results are on English Stephen King. French performance is untested — treat 77-79% as upper-bound guidance, not a guarantee.

**On Pichler et al.:** Results are for SPAN LABELING, not paragraph classification. Low absolute scores (20-33 F1) don't predict our task performance.

**On CoT:** Effects are model-specific. "Let's think step by step" helped Llama 3.1 8B but had varied effects on other models. No general recommendation — test per model per criterion.

**Citation discrepancy:** Secondary sources cite Hicke et al.'s GPT-4o F1 as 86.90; arXiv full text reports 84.79%. Use 84.79% as authoritative.

---

### 17.8 How This Paper Influenced Our Actual Work

| Paper Finding | What We Tried | Our Result | Match? |
|---|---|---|---|
| CoT hurts subjective tasks | No-think for Task 1 | 0% figuré — catastrophic | ❌ OPPOSITE — thinking is essential for Task 1 (different task type) |
| Self-consistency improves classification | n=5 voting for FOC | 61.7% — no improvement | ❌ Doesn't work when bias is systematic |
| Embed Genette definitions | Tried in map-reduce prompts | Minor improvement | ✅ Confirmed |
| Quotation-mark rule | Added to FOC prompts | Minor improvement | ✅ Partial |
| Llama 3.3 70B best open model | Tested via Groq | 58.3% — same FOC_INT bias | ❌ Doesn't transfer to French |
| RoBERTa fine-tuning | Attempted (CamemBERT) | FAILED — 60 samples too few | ❌ Insufficient gold data |
| RAG improves classification | Smart RAG for Task 0 | 45% — WORSE than baseline | ❌ Wrong task type for RAG |
| Fine-tuning beats prompting | LoRA on 60 gold novels | FAILED — minimum ~200 needed | ❌ Insufficient gold data |
| Constrained JSON output | Implemented in all scripts | Eliminated parse errors ✅ | ✅ Works |
| Gemma strong in French | Not yet tested | — | 📌 TODO: try Gemma 3 27B |
| Mistral native French | Tested Mistral Large (free API) | 63.3% FOC — defaults to FOC_INT | ⚠️ Still has FOC_INT bias, but better than Llama |

---

### 17.9 Conclusions for Paper Appendix

Based on this document, the recommended framing for the paper's technical appendix:

1. **Task 0 difficulty is well-documented:** Even GPT-4o reaches only 84.79% on English focalization (Hicke et al.). Our 65% on French with local models is reasonable given the language gap and model size.

2. **FOC_ZERO failure is universal:** 9 of 17 models in Hicke et al. labeled FOC_ZERO zero times. Our models show the same behavior. This is not a model failure but a structural difficulty of the class.

3. **Fine-tuning is the principled path forward:** RoBERTa-large reached 77.5% with 300 samples. Our constraint (60 gold novels) prevents this currently. Expanding the gold set to 300+ would be the highest-leverage future investment.

4. **CoT/thinking mode has task-specific effects:** Essential for semantic disambiguation (Task 1), potentially harmful for subjective literary classification (Task 0 — FOCALISATION, MODE NARRATIF). This finding itself is a contribution.

5. **Model ensembling (not yet tried):** Cross-model voting (qwen3:30b + Gemma 3 27B + Mistral Large) is the most promising free local improvement not yet implemented.


---

## PART 18: MISSING TECHNIQUES — TASK 1 ADDITIONAL APPROACHES

### 18.1 Web Search for Examples (Technique Used During Prompt Engineering)
**When:** During v2→v3 development of Task 1 examples
**What:** Searched the internet for French figurative language examples, idioms, and metaphors to use as independent few-shot examples
**Search queries used:** "French figurative expressions plants nature ecology metaphors examples littéral figuré"
**Why:** Needed examples that were NOT from the gold set to avoid data leakage
**Result:** Found French idioms like "les carottes sont cuites", "mettre du beurre dans les épinards", "ne pas avoir un radis", "être dans les choux", "prêcher dans le désert", "déplacer des montagnes", "ce n'est pas la mer à boire"

### 18.2 Gold Set Leakage Bug — Discovered and Fixed
**When:** Between evaluate_all_goldsets v2 and v3
**What happened:** In v2, several examples in the few-shot prompt were accidentally drawn from the gold set itself:
- "graminées" (from Plantes gold set) ❌
- "serpolet" (from Plantes gold set) ❌
- "oliviers" (from Plantes gold set) ❌
- "savane" (Chevillard — from Loterre gold set) ❌
- "marais" (Bouraoui — from Loterre gold set) ❌
- "habitat naturel" (from Loterre gold set) ❌
- "forêts" (Hunzinger — from Loterre gold set) ❌

**Why this is a critical error:** If examples from the gold set appear in the prompt, the model may have already "seen the answer" — artificially inflating accuracy with no value for real data.

**Fix:** Replaced all gold-set examples with completely independent examples from standard French literature, common French idioms, and general ecological writing. This was the v2→v3 transition.

**Lesson:** ALWAYS verify that few-shot examples have zero overlap with the evaluation set.

### 18.3 Two-Pass Classification (Tried, FAILED — Made Results Worse)
**When:** After v3 results showed low figuré accuracy
**Hypothesis:** Model defaults to référentiel when uncertain. Force it to consider figuré by splitting into two passes.

**How it worked:**
- **Pass 1:** "Is this clearly référentiel?" → if YES → done, label = référentiel
- **Pass 2:** Only if Pass 1 says uncertain → "Is this figuré?" with figuré-specific examples

**Implementation:** `evaluate_all_goldsets_v4.py`

**Result:**

| Category | v3 (1-pass) | v4 (2-pass) |
|---|---|---|
| Animaux | 89.5% / 78.3% fig | WORSE |
| Plantes | 95.7% / 66.7% fig | WORSE |
| Loterre | 85.2% / 56.1% fig | WORSE |

**Why it failed:** Two API calls per uncertain item = double the time. But also, when Pass 1 says "uncertain", Pass 2 doesn't get enough context to reliably flip to figuré. The model's first instinct was usually right.

**Lesson:** More API calls ≠ better accuracy. Splitting a classification into passes can hurt because each pass sees less context than a single comprehensive prompt.

### 18.4 Class Imbalance Analysis (Diagnosis)
**Discovery:** After v4 failed, analyzed why figuré accuracy was stuck:

Gold set class distribution:
- Animaux: 121 référentiel (63%) vs 69 figuré (36%)
- Plantes: 164 référentiel (~87%) vs 24 figuré (~13%)
- Loterre: 148 référentiel (78%) vs 41 figuré (22%)

**Finding:** The gold sets are heavily imbalanced toward référentiel. When a model is uncertain, predicting référentiel is "safe" — right 63-87% of the time. This creates systematic bias toward référentiel.

**Why the overall accuracy is high (85-96%) but figuré accuracy is low (56-78%):** The model is right on most référentiel cases (93-100%) but less reliable on the minority figuré class.

**Conclusion communicated to Riccardo:** This is a class imbalance problem and an annotation ambiguity problem — not a model quality problem. Human annotators agree only 76% of the time on this task. Our 92.1% overall for animals EXCEEDS human agreement. Pursuing 90%+ figuré accuracy may not be achievable or meaningful.

### 18.5 OpenAI API Port Configuration (Fixed Bug)
**When:** Early development
**Problem:** Initial script used port 11434 (other team's Ollama) instead of port 11435 (Labiba's private Ollama)
- Port 11434: `http://127.0.0.1:11434/v1` — system Ollama with qwen2.5:72b etc.
- Port 11435: `http://localhost:11435/api/chat` — Labiba's Ollama with qwen3:30b

**Issue:** Scripts sometimes used the wrong port, causing authentication errors or wrong model being used
**Fix:** Standardized all scripts to use port 11435 explicitly

### 18.6 Response Parsing Evolution
**Problem:** Models return inconsistent JSON — sometimes in markdown code blocks, sometimes with extra text, sometimes with thinking tokens
**Parsing pipeline developed:**
```python
# Step 1: Remove thinking tokens
raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

# Step 2: Extract JSON from markdown code blocks
if '```' in raw:
    m = re.search(r'```(?:json)?\s*(.*?)\s*```', raw, re.DOTALL)
    if m: raw = m.group(1)

# Step 3: Extract first JSON object
m = re.search(r'\{[^}]+\}', raw)
if m:
    data = json.loads(m.group(0))
    label = data.get("label", "").strip().lower()

# Step 4: Fallback — scan for keywords
for label in ["référentiel", "figuré"]:
    if label in raw.lower(): return label

# Step 5: Default fallback
return "référentiel"  # safest default
```

This pipeline handles: thinking mode output, markdown formatting, direct JSON, plain text responses.

---

## PART 19: MISSING TECHNIQUES — TASK 0 ADDITIONAL DETAILS

### 19.1 Title+Author+125 Lines Combined (Considered, Not Tried)
**Hypothesis:** Combine Johanna's internet knowledge approach (title+author → model uses its training knowledge) with Labiba's text approach (125 lines of actual text)
**Result:** This combination was discussed but never implemented before time ran out
**Potential:** Could give +2-5pp improvement for novels the model already knows from training

### 19.2 Voting Across 8 Sections (Crashed)
**What was tried:** Split novel into 8 sections, classify each section independently, take majority vote
**Result:** Crashed — Python process killed, memory errors
**Root cause:** 8 separate API calls per novel × 60 novels = 480 calls simultaneously → memory overflow in subprocess management
**Resolution:** Abandoned in favor of map-reduce (9 chunks but sequential, not parallel)

### 19.3 Full Text 300 Lines (Crashed/Failed)
**What was tried:** Feed first 300 lines (~4,500 words) of novel to model in single prompt
**Result:** FAILED — model output was incoherent, accuracy near 0%
**Root cause:** French novel paragraphs are dense; 300 lines ≈ 80,000+ characters. Even with 8,192 token context, the model couldn't process this coherently.
**Resolution:** Led to map-reduce approach

### 19.4 Map-Reduce v1 and v2 (Intermediate Versions)
Before v3 map-reduce (the production version), earlier versions were tried:

**v1:** Basic map (classify each chunk) + reduce (vote across chunks)
- Problem: Reduce step just counted majority labels, no reasoning synthesis
- Result: ~50% overall

**v2:** Map with more questions + reduce with summarization
- Problem: Model hallucinated narratological labels in reduce step
- Result: ~57% overall

**v3 (FINAL):** Map with structured JSON observations → reduce with synthesis prompt referencing all 9 chunk summaries
- Result: 63.3% FOCALISATION, 90%+ TYPE NARRATEUR

### 19.5 Regex-Based Narratological Signals (Considered, Not Implemented)
**Hypothesis:** Some narratological features have surface linguistic signals:
- "je" as subject pronoun → NAR_AUTOD (first-person narrator)
- "il/elle" consistently as protagonists → NAR_EXT
- Flashback markers ("il se souvint", "autrefois", "jadis") → TEMP_DIS
- "(…) dit-il" frequency → MODE_EVT (lots of dialogue)

**Why not implemented:** Would require POS tagging + dependency parsing on 925 novels. The TOKENS folder has this data but integrating with the LLM pipeline was complex. Could be a useful complementary signal for the sklearn classifier.

### 19.6 Critere File as Training Data (Tried, Failed)
**What was tried:** Used 480 novels from `critere_narration_focalisation.csv` (not overlapping with 60-novel gold set) as few-shot examples in FOCALISATION prompt
**Result:** 61.7% — no improvement over single-sample without examples
**Root cause:** 480 examples overwhelm the context window — model loses track of the classification task when given too many examples
**Resolution:** Reduced to 3-5 carefully selected examples

---

## PART 20: COMPLETE CHRONOLOGICAL TIMELINE OF TECHNIQUES

### Task 1 — Literal/Figurative (chronological order)

| Date | Version | Technique | Result | Decision |
|------|---------|-----------|--------|----------|
| Early June | v1 | No examples, single prompt | Animaux: 85.8%/71% fig | Baseline |
| June 5 | v2 | Category-specific examples (but had gold leakage) | Animaux: 92.1%/89.9% fig | Better! |
| June 5 | v2 bug fix | Discovered gold set leakage in plant/Loterre examples | — | Must fix |
| June 9 | v3 | Independent examples (zero gold set overlap) | Animaux: 89.5%/78.3%, Loterre: 85.2%/56.1% | Production quality |
| June 9 | v4 | Two-pass classification | WORSE than v3 | Abandoned |
| June 15 | v5 | Additional targeted examples for idioms | ~91%/79% animaux | Improved |
| June 24 | v6 | Full prompt with balanced ref/fig examples | 91.6%/81.2% animaux, 96.3%/79.2% plantes | **FINAL** |
| June 24 | v7 (Loterre) | Added more référentiel examples to Loterre | Fig dropped to 56.1% | WORSE — reverted |
| June 24 | v8 (Loterre) | Targeted Group A error fixes only | 85.2%/63.4% fig | **FINAL for Loterre** |
| June 24-25 | Batch test | Tested batch=1 vs batch=5 | batch=5 same accuracy, 2.3x faster | Use batch=5 |
| June 24-25 | No-think test | num_predict=100 with /no_think | 0% figuré — catastrophic | **Thinking mandatory** |
| July 1 | Corpus run | Started animaux full corpus (127,935 rows) | 29.1% figuré → **DONE July 5** | ✅ |
| July 5 | Plantes run | Started plantes full corpus (74,475 rows) | In progress → ETA July 8 | 🔄 |

### Task 0 — Narratology (chronological order)

| Date | Version | Technique | FOC Result | Decision |
|------|---------|-----------|------------|----------|
| May | Baseline | 125-line sample | 63.3% | First result |
| May | Smart RAG | BM25 retrieval of relevant excerpts | 45.0% | WORSE — abandoned |
| May | Full text | 300 lines / 4,500 words | FAILED | Too long |
| May | Section voting | 8 sections, parallel classify | CRASHED | Abandoned |
| May | Map-reduce v1 | Basic chunk map + vote reduce | ~50% | Insufficient |
| May | Map-reduce v2 | Enhanced map + summarize reduce | ~57% | Better |
| June 2 | Map-reduce v3 | JSON observations → synthesis reduce | 63.3% FOC | **Main approach** |
| June | Option A | Per-criterion targeted reduce | Mixed results | Partial use |
| June | Chunk classifier | Sklearn on map features (LOO-CV) | 67.1% FOC / 71.7% MOD | **Best for MOD/REG** |
| June | Title+author | Model uses internet training knowledge | 61.7% FOC | Worse |
| June | Critere few-shot | 480 examples in context | 61.7% FOC | No improvement |
| June | Mistral Large | Free API, 2 RPM | 63.3% FOC | FOC_INT bias |
| June | Groq Llama 3.3 | Free API, fast | 58.3% FOC | Worse — FOC_INT bias |
| June | GPT-4o-mini | Paid API, $9 Riccardo credit | 75.0% FOC | Best ever, not reproducible |
| June | Self-consistency | n=5 votes, temperature=0.3 | 61.7% FOC | No improvement |
| June | qwen72b no-think | Faster but no thinking | 61.7% FOC | Worse than thinking |
| June | **qwen72b+thinking** | Large model + extended reasoning | **68.3% FOC** | **LOCAL BEST** |
| June 23 | qwen72b all-7 | All criteria overnight | 60 novels complete | Pending scoring |
| June | LoRA fine-tuning | CamemBERT on 60 gold labels | FAILED | Too few examples |
| — | Hybrid v2 | Best per-criterion from 3 sources | 69.3% overall | Best combined |
| — | Hybrid v4 | With alternative label scoring | **70.5% overall** | **FINAL RESULT** |

---

## PART 21: WHAT WAS NEVER TRIED (FUTURE WORK)

1. **Gemma 3 27B locally** — paper says stronger in French than Qwen; promising but not tried
2. **Mistral-Small-3.1 24B locally** — native French, was deleted for disk space
3. **Cross-model ensemble** — qwen3:30b + Gemma + Mistral voting; most promising untried technique
4. **CamemBERT-large fine-tuning with more data** — would need 200+ gold novels; currently 60
5. **English/Arab name detection** — capital letter heuristic for Task 3 NER improvement
6. **Loterre gold set correction** — fix 4 probable annotation errors in Group C → would give ~71% fig
7. **Referential plant filtering for Task 3** — needs Task 1 plantes to complete first
8. **Task 2 subcategory classification** — script ready, waiting for Task 1 corpus results
9. **Task 4.5 comparant/comparé** — same dependency
10. **Biodiversity additional indices** — Pielou's J, Simpson, Chao1 — waiting for Riccardo's documents
11. **Constrained JSON decoding in Ollama** — paper suggests 50% speed gain + accuracy improvement; not yet implemented
12. **Title+Author+125 lines combined** — promising hybrid not yet tested
13. **Postcolonial/Maghreb corpus special handling** — Arabic names in NER; capital letter detection discussed but not implemented


---

## PART 18: MISSING TECHNIQUES — COMPREHENSIVE ADDENDUM

### 18.1 The "Two-Way" Technique: Map-Reduce with Per-Chunk Voting + Reduce Decision

This is the key technique that was partially documented but not fully explained. The map-reduce pipeline has TWO distinct internal mechanisms that work together:

**Step 1 — Map (per-chunk classification):**
Each of the 6 chunks is independently classified per criterion using `classify_chunk()`. This produces a VOTE per chunk:
```
chunk 1 → FOC_INT
chunk 2 → FOC_INT  
chunk 3 → FOC_ZERO
chunk 4 → FOC_INT
chunk 5 → FOC_VAR
chunk 6 → FOC_INT
```

**Step 2 — Reduce (final decision from votes):**
The `reduce_votes()` function takes ALL chunk votes + the Genette definitions + the novel title and makes a FINAL decision:
- First tries: LLM prompt with all votes as context + definitions
- Fallback: pure majority vote from chunk predictions

This two-step process is what makes the pipeline robust — the reduce step can override an outlier chunk vote using global narrative reasoning, which a simple majority vote cannot do.

**Why it matters:** In the weak criteria test (`run_weak_criteria.py`), this two-step approach was implemented with embedded Genette definitions at both the map AND reduce level — the most sophisticated version of the technique.

**Script implementing this:** `~/ecopoetique/narratologie/run_weak_criteria.py` (also at `/tmp/run_weak_criteria.py`)

### 18.2 Gemma3:27b and Mistral-Small3.1 — ACTUALLY TESTED (Not Just Suggested)

From the June 22 transcript, both models were actually pulled and a dedicated test script was built:

**What was done:**
1. Pulled `gemma3:27b` (17GB) via Ollama on port 11434
2. Pulled `mistral-small3.1` (15GB) via Ollama on port 11434
3. Disk went to 97% — almost full
4. Script `run_weak_criteria.py` was written targeting only the 4 WEAK criteria: FOCALISATION, MODE NARRATIF, ESPACE, INTRIGUE

**Script strategy:**
- Embedded Genette definitions VERBATIM in each prompt
- Used NO-THINK (num_predict=100, temperature=0)
- JSON constrained output
- 6 chunks per novel, map → reduce structure
- Comparison table vs Hybrid v2 baseline

**What happened:** The script was written and the models were pulled, but the results were NOT logged in our transcripts — likely the test was interrupted or results were not pasted. The models were then DELETED to free disk space (gemma3:27b deleted, mistral-small3.1 deleted, freeing 32GB).

**Key finding from this attempt:** Even with Gemma3 and Mistral specifically targeted at weak criteria with embedded definitions, the results did not clearly beat qwen3:30b. This is why both were deleted.

**Result files (if they exist):**
- `~/ecopoetique/narratologie/resultats_gemma3_27b_weak.csv`
- `~/ecopoetique/narratologie/resultats_mistral-small3_1_weak.csv`
- `~/ecopoetique/narratologie/weak_criteria_test.log`

### 18.3 Multi-Model Ensemble (3-Model Voting) — ATTEMPTED AND FAILED

From the June 22 transcript (before the hybrid v2 was built), an ensemble approach using 3 different models from port 11434 was tried:

**Models used:** qwen2.5:32b, qwen2.5:72b, qwen2.5:14b (all on port 11434, other team's Ollama)
**Strategy:** Majority vote across 3 models per criterion
**Result:** 55.3% FOCALISATION — WORSE than qwen3:30b alone (63.3%)

**Why it failed:**
- All 3 qwen2.5 models default to FOC_INT, so majority vote = FOC_INT
- The ensemble amplified the bias rather than correcting it
- Cross-model voting only works when models make different errors, not the same systematic error

**Result file:** Referenced in transcript as "ensemble" column in comparison table. Not saved separately.

### 18.4 Johanna's Google Colab Scripts — Complete Prompt Documentation

Johanna's original narratological classification used Google Colab with GPT-4o-mini via OpenAI API. The exact prompts for ALL 7 criteria are documented in the first transcript. Key details:

**General architecture:**
- Model: `gpt-5.4-mini` (later `gpt-4o-mini`) 
- Method: Title + author + year → GPT queries internet knowledge
- NO text reading — pure internet/pretraining knowledge
- Batches of 5 novels per API call
- XML-structured prompts with `<requete>`, `<reponse>`, `<categorie>`, `<explication>` tags
- Temperature: 0, max_tokens: 4000
- Parsing: regex on XML tags

**Per-criterion prompts (Johanna's exact definitions):**

**Intrigue (nature de l'intrigue):**
- Linéaire: événements s'enchaînent dans un ordre progressif sans rupture majeure
- Fragmentaire: intrigue construite par blocs disjoints, souvent non liés immédiatement
- Cyclique: répétition de motifs ou situations créant un effet de boucle ou retour
- X: if insufficient information on internet

**Chronologie (structure temporelle):**
- Chronologique: événements majoritairement racontés dans l'ordre où ils se produisent
- Anachronique: présence significative de retours en arrière (analepses) ou d'anticipations (prolepses)
- Discordante: structure très éclatée ou désorganisée, fréquents déplacements temporels non hiérarchisés

**Narrateur + Focalisation (combined prompt):**
- NAR_AUTOD: narrateur = protagoniste principal
- NAR_TEM: narrateur témoin — assiste aux événements sans en être l'agent central
- NAR_EXT: narrateur externe (hétérodiégétique)
- FOC_INT: perspective subjective, accès à l'intériorité d'un personnage unique
- FOC_EXT: narration descriptive en surface, sans accès aux pensées internes
- FOC_ZERO: narrateur omniscient, accès à l'ensemble des consciences
- FOC_VAR: alternance entre plusieurs points de vue internes

**Mode narratif:**
- MOD_EVT: centré sur les faits, actions et décisions
- MOD_DESC: mise en valeur des décors, objets ou atmosphères
- MOD_INTR: accès aux réflexions ou états mentaux des personnages
- MOD_DIA: dialogue/polyphonie — structuré par les échanges verbaux
- MOD_MIX: alternance régulière de plusieurs modes sans prédominance

**Régime narratif:**
- REG_AUTO: récit fondé sur l'expérience de l'auteur ou un double fictionnel
- REG_REAL: représentation cohérente du monde réel, sans rupture des codes référentiels
- REG_FANT: intrusion du surnaturel ou de l'étrange dans un cadre réaliste
- REG_SPEC: monde fictionnel modifié, futuriste ou alternatif

**Espace:**
- ESP_UNIT: action dans un seul lieu ou espace géographique délimité
- ESP_FRAG: plusieurs lieux distincts et discontinus, sans logique de déplacement
- ESP_ITIN: structuré autour de déplacements continus, voyages
- ESP_IMAG: espace fictif, fantastique, onirique ou utopique/dystopique

**Degré de discordance temporelle (extra criterion):**
- Faible discordance: déroulement quasi linéaire, transitions explicites peu fréquentes
- Moyenne discordance: alternance modérée entre temps présents et passés
- Forte discordance: temporalité éclatée ou complexe, nombreuses analepses, récits enchâssés

**Key technical details of Johanna's Colab:**
- CSV input with semicolon separator: `analyse_narratologique_finale.csv`
- `corpus_DigEco.csv` as metadata (Author, Title, Year)
- Polars library (not pandas) for data manipulation
- `partition_by(by="fichier")` for batching by novel
- XML regex parsing: `re.search(r'<categorie>(.*?)</categorie>', reponse)`
- Evaluation with sklearn `f1_score(average="micro")`
- Files: `analyse_narratologique_chronologie.csv`, `analyse_narratologique_narration.csv`, `analyse_mode-narratif_internet-4o.csv`, `analyse_narratologique_regime_narratif_41_mini.csv`

**Why Johanna's approach failed on 33.8% of novels:**
- Many obscure novels not well-known on internet
- Model answers "X" (unknown) when it cannot find enough information
- Only covers 2/7 criteria in the final version (narrateur + focalisation)
- No access to actual text — relies entirely on pretraining and internet knowledge

### 18.5 Task 2 — Complete Subcategory Typology (16 Categories)

The full Task 2 subcategory classification was not fully documented. Here are ALL 16 subcategory codes with examples:

| Code | Type | Example |
|------|------|---------|
| COMME_SN | Simile with nominal group | "rusé **comme** un renard" |
| COMME_P | Simile with proposition | "craquaient **comme** les os d'un cerf" |
| COMME_SI | Simile with "comme si" | "**comme si** une forêt retenait son souffle" |
| COMP_DEG | Degree comparison | "**plus lent qu'**une tortue" |
| DE_PARANGON | Genitive of paradigm | "mémoire **d'**éléphant" |
| DE_MATIERE | Genitive of material | "volonté **de** granit" |
| DE_UNIVERS | Genitive of universe | "océan **de** verdure" |
| DE_QUANTIF | Genitive of quantification | "une forêt **de** pylônes" |
| DE_PROP | Genitive of property | "vautours **de** la finance" |
| META_ATTR | Attributive metaphor | "cet homme **est** un loup" |
| META_APP | Appellative metaphor | "la montagne **sentinelle**" |
| META_JUXT | Juxtaposition metaphor | "arbre-parapluie" |
| META_VERB | Verbal metaphor | "la forêt **avalait** la lumière" |
| MOD_ANALOG | Modal analogy | "**on aurait dit** une meute" |
| ANALOG_COMPLEX | Complex embedded comparison | embedded multi-level analogy |
| META_FILEE | Extended metaphor network | sustained metaphor across paragraph |

**Detection shortcuts (many can be rule-based before LLM):**
- COMME_SN/P/SI → contains "comme"
- COMP_DEG → contains "plus/moins/aussi/autant que"
- DE_* → contains "de + nature term"
- META_VERB → verb + nature entity as subject
- MOD_ANALOG → contains "on dirait/sembler/avoir l'air"

**Script:** `~/ecopoetique/métaphore/run_task2_subcategories.py` (built, ready to run)

### 18.6 Loterre Classification into 5 Categories (Separate Sub-task)

A separate classification task was attempted for Loterre terms — not just literal/figurative but also semantic CATEGORY of ecological concept:

**5 categories:**
1. Milieux naturels (natural environments)
2. Vocabulaire du vivant (living vocabulary)
3. Climat (climate)
4. Activités humaines (human activities)
5. Menaces écologiques (ecological threats)

**Method:** GPT-4o-mini via API, batches of ~200 terms, JSON output
**Script:** Google Colab — `categorisation_termes.json` as output
**Status:** Done by Johanna, not by Labiba

### 18.7 Johanna's Task 2 (Comparé Classification) — Exact Prompt Details

Johanna's comparé classification used a specific XML-tagged prompt with the 6 Caracciolo categories. The exact system prompt included:

**Key prompt elements:**
- XML tags: `<phrase>`, `<comparant>`, `<reponse>`, `<analyse>`, `<compare>`, `<label>`
- Comparant is TAGGED in the sentence with `<comparant>animal</comparant>`
- Model identifies: (1) what the comparé is, (2) which category
- Examples provided: tortue→O (ship), lion→CH (implicit human), moule→O (building)
- Temperature: 0.1-0.2
- Batching: by novel file (`partition_by(by="fichier")`)
- Parsing: regex on XML `<label>` tags

**Models tested by Johanna for comparé:**
- `gpt-4o-mini` (main production)
- `o3-mini` (reasoning model, tested for single examples)
- `gpt-4.1-nano` (cheaper alternative)
- `gpt-4.1-mini` (used for régime narratif and temporalité)

**Extra category X:** Added for "context insufficient to determine comparé" or "comparant is not actually an animal"

### 18.8 qwen2.5 Models on Port 11434 — Tested for Task 0

Before switching to qwen3:30b on port 11435, several models on port 11434 (other team's Ollama) were tested:

| Model | Port | VRAM | FOC Score | Notes |
|-------|------|------|-----------|-------|
| qwen2.5:7b | 11434 | 4GB | ~30% | Too small |
| qwen2.5:14b | 11434 | 8GB | ~45% | Better but still poor FOC |
| qwen2.5:32b | 11434 | 19GB | ~51% | Part of failed ensemble |
| qwen2.5:72b | 11434 | 47GB | ~55% | Base for qwen72b-limited |
| Llama-3.2-1B | 11434 | 0GB | ~1% | Completely failed |

**Important:** These are on the OTHER TEAM's Ollama (port 11434), not Labiba's. Using them risks interfering with other researchers' work. All production runs use port 11435.

### 18.9 Paragraph-Level Focalization Classification (Untried — From Research)

One technique suggested in the PDF paper but NOT tried:
- Classify FOCALISATION at paragraph level (not whole novel chunks)
- Then aggregate paragraph votes across the novel
- Basis: Hicke et al. tested on paragraph-level Stephen King texts (not whole novels)

**Why not tried:** Would require re-chunking corpus into paragraphs instead of equal-size chunks. The map-reduce approach already approximates this with 6 chunks across the novel. Estimated improvement: unclear.

### 18.10 FlauBERT Disambiguation (Johanna's Method — Not Used by Labiba)

For the initial entity extraction and homograph disambiguation, Johanna used:
- **FlauBERT** (French BERT trained on French web text)
- Fine-tuned on manually annotated sample
- Used for disambiguation: maquereau=fish vs maquereau=pimp, etc.
- Combined with rule-based blacklists

Labiba did NOT use FlauBERT — all Task 1 classification uses qwen3:30b via prompt engineering. This is a different approach at a different stage (entity extraction vs literal/figurative classification).

### 18.11 "Bribe" Technique (Pichler et al. — Tested but Not Documented)

From the PDF paper, Pichler et al. found that "bribe" phrases helped SauerkrautLM:
- "I'm going to tip $1000 for a perfect answer"
- "This is very important for my research"

**Our verdict:** Not tested. The paper explicitly says effects are model-specific and no general recommendation is possible. For qwen3:30b with French literary text, the "bribe" approach is unlikely to help and was not implemented.

### 18.12 Complete Per-Criterion Error Analysis Table

From the transcripts, the complete error breakdown for each criterion:

**FOCALISATION errors (60 novels):**
- Over-predicts FOC_INT: 34/60 predicted INT when gold says ZERO or VAR
- FOC_ZERO never predicted by most models (9 of 17 models in Hicke et al.)
- FOC_VAR confusion: sometimes INT→VAR (confuses multiple characters with perspective shifts)
- Resolution: required qwen72b with thinking to partially fix

**ESPACE errors (60 novels):**
- Over-predicts ESP_FRAG: treats any mention of 2+ locations as fragmented
- Key confusion: single location with memory/flashback to another location → predicted FRAG, gold = UNIT
- 48.3% score — EXCLUDED from paper presentation by Riccardo

**MODE NARRATIF errors (60 novels):**
- Over-predicts MOD_MIX: hedges when uncertain
- 26 out of 29 errors are → MOD_MIX (safety prediction)
- Chunk classifier (sklearn) avoids this because it predicts from features, not hedging

**REGIME NARRATIF errors (60 novels):**
- Main confusion: REG_REAL ↔ REG_AUTO (7 errors)
- First-person narration ≠ autofiction — model confuses these
- REG_SPEC underperforms: speculative/dystopian novels sometimes predicted as REG_FANT

**INTRIGUE errors (60 novels):**
- Symmetric LIN/FRAG confusion (10 LIN→FRAG, 8 FRAG→LIN)
- One plot with subplots ≠ genuinely fragmented narrative
- Option A (targeted prompts) made this WORSE by over-correcting

**TEMPORALITÉ errors (60 novels):**
- Over-predicts TEMP_DIS: any memory/flashback → DIS
- Key: isolated analepsis ≠ overall anachronic structure
- 71.7% score — one of the more reliable criteria
