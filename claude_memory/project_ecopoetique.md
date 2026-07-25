---
name: project-ecopoetique
description: "Computational literary analysis project studying biodiversity, figurativity, agentivity, and narratology in a large corpus of contemporary French novels"
metadata: 
  node_type: memory
  type: project
  originSessionId: 084f12f4-cd69-4190-b1d1-cbbc6040022d
---

Project lives at `/home/lfarooq/ecopoetique/`. It is a research project in computational literary studies (écopoétique) applying NLP to analyse how nature/biodiversity is represented in contemporary French fiction.

**Why:** Academic research combining corpus linguistics, NLP, and literary theory to study ecological themes in French literature.

**How to apply:** When working in this directory, assume a research/DH context. Results are CSVs; pipeline scripts are bash + Python + spaCy + GPT/LLM APIs.

---

## Corpora

- `CORPUS_TOTAL/` — ~925 French novels in .txt (one sentence per line, post-OCR cleaned)
- `CORPUS_Bestsellers/` — ~85 bestseller novels (subset)
- `TOKENS/` — spaCy tokenisation of full corpus (token | POS | lemme), 925 files
- `TOKENS_Bestsellers/` — same for bestsellers subset
- Metadata CSVs: `corpus_DigEco.csv` (main, tab-separated), `corpus_Bestsellers.csv`, `corpus_PRIX_ECOLOGIE.csv`

## Lexicons (`lexiques/`)

- `ANIMAUX.txt`, `PLANTES.txt`, `CHAMPIGNONS.txt` — from Wikispecies dump + TaxRef (French biodiversity reference)
- `categories_animales/` — animal categories: AMPHIBIENS, INSECTES, MAMMIFERES, MOLLUSQUES, OISEAUX, POISSONS, REPTILES
- `loterre/` — Loterre thesaurus (climate change / Anthropocene terms): `loterre_filtré.csv`, `classement_termes.json`

## Pipeline (`scripts/`)

bash pipelines: `pipeline_animaux.sh`, `pipeline_plantes.sh`, `pipeline_loterre.sh`
Python helpers: `grep_contexte.py`, `remove_duplicates.py`, `truncate_sentence.py`, `filter_*.py`, `assign_category.py`, `lemmatize.py` (uses LEFFF lemmatiser), `pos_tag_homographe.py`, `biodiv_score.py`, `shannon_rarefied.py`

## Results (`resultats/`)

- `corpus_principal/` — ENTITES_contexte_animaux/plantes/champignons/loterre/taxons.csv + decomptes
- `bestsellers/` — same for bestsellers subset

## Homographie (`homographie/`)

Disambiguation of lexical homographs (e.g. "if" = English word vs. yew tree):
- `isAnimal/` — binary classifier training data + `train_homograph_binary.py`
- `isPlant/` — GPT-4 annotations for plant homographs
- `loterre/` — Loterre ambiguous terms table

## Métaphore / Figurativity (`métaphore/`)

Classifying occurrences as literal vs. figurative:
- GOLD sets for animaux, plantes, loterre (with RB variants)
- GPT-4 evaluation scripts (`evaluate_all_goldsets_v*.py`)
- Results: `eval_animaux_v6_results.csv`, `eval_loterre_v8_results.csv`, etc.
- `plantes/` subfolder for plant-specific work

## Morphosyntaxe / Agentivity (`morphosyntaxe/`)

Syntactic dependency analysis to measure animal/plant agency in narrative:
- `dépendants_ANIMAUX.csv`, `PLANTES.csv`, `HUMAINS.csv`
- `resultats_agentivite.txt`, `resultats_agentivite_complet.txt`
- `task3_full_report.md`

## Narratologie (`narratologie/`)

Focalization / point-of-view classification across corpus:
- Multiple model experiments: GPT-4o-mini, Qwen3-30b, Qwen72b, Llama70b, Mistral, Gemma3-27b
- Techniques tested: RAG, map-reduce, voting, LoRA fine-tuning
- `lora_model/` — fine-tuned LoRA model
- `GOLD_narratologie.csv` — gold standard annotations
- `narrato_extraits/` — text samples per novel for annotation

## Visualisations (`visualisations/`)

PNGs: biodiversity indices by year, agentivity charts, PCA/t-SNE for focalization, Shannon index, figurativity pie charts, etc.
