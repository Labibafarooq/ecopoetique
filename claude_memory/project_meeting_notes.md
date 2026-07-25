---
name: project-meeting-notes
description: "Key decisions from both Riccardo meetings (June 25 + a second one ~early July 2026) covering all tasks in the écopoétique project; next meeting mentioned as July 10"
metadata: 
  node_type: memory
  type: project
  originSessionId: 084f12f4-cd69-4190-b1d1-cbbc6040022d
---

**Two meeting transcripts now exist** — both read in full 2026-07-07:
1. `/home/lfarooq/ecopoetique/riccardo_25june_meetingTranscript.md` — first meeting, June 25, 2026 (notes below)
2. `/home/lfarooq/ecopoetique/métaphore/Riccardo_second_meeting.txt` — second meeting, exact date uncertain from the transcript itself but content places it ~early July (Task 1 animaux was mid-run, about to finish "tomorrow night"; plantes "in two days") — see new section at the bottom of this file. **A third meeting was mentioned as scheduled for "the 10th of July"** (a Friday) — not yet happened as of 2026-07-07. Per the transcript (~line 637-646), Riccardo has a personal appointment at **10:45am** on the 10th, and they agreed the Riccardo meeting itself would be in the **afternoon** — no exact hour pinned down beyond that; confirm precise time separately (likely by email).

Meeting with supervisor Riccardo Barontini, June 25, 2026. Next meeting after that one was originally set for **July 3, 2026 at 11am** — the second transcript is very likely that meeting (or a close reschedule of it).

**Why:** Alignment meeting to approve Task 1 results and plan remaining work before Labiba leaves July 15, 2026.

**How to apply:** Use to understand what is "done", what is "approved", and what is "next" for each task.

---

## Task 0 — Narratology / Focalization (biggest headache)

- Best result so far: **68.3% with Qwen72b** (with "thinking"/"intelligence" mode)
- Previously tried: GPT4o-mini, Mistral API (free), Groq (free), LoRA fine-tuning
- LoRA failed: training dataset too small + 3 novels in gold set not present in CORPUS_TOTAL (those 3 are probably Bestsellers-only novels) — needed 200+ examples, not feasible to ask Riccardo to write that many
- Labiba ran on **60 novels** from the gold set (not 76 — the 76-novel run had lower accuracy, possibly due to rushing or the 3 missing novels)
- Papers show **~70-75% is state of the art** for narratology with LLMs — Labiba's results are competitive
- Riccardo suspects **gold set may have errors** for focalization subcategory — wants the specific items where ALL models consistently disagree with gold label so he can check them
- **"Espace" (space/setting) subcategory → likely to be eliminated** — models don't do well on it at all (mostly just answers "no")
- "Intrigue" (plot) works sometimes but inconsistently
- "Type of narrator" was the best-performing subcategory
- Next steps:
  1. Send Riccardo the gold set items where every model disagrees → he checks if gold is wrong
  2. Try GPT-4 via Riccardo's OpenAI API key (~$9 USD / €8 remaining). Key sent to Labiba by email during meeting. Can use any GPT model, costs differ per token.
  3. Try fine-tuning a model on the existing gold labels (Labiba planned for next day, working from home)
- Riccardo's position: "It can be defended that it's not possible to do better than this with current tools. We can document the dead end — useful for other researchers."

---

## Task 1 — Literal vs. Figurative Classification (APPROVED, ready to run)

- **APPROVED by Riccardo** — "task one is okay with me, you can go ahead and apply to the entire corpus"
- Before Labiba's work: Joanna got ~**47%** (or 16%) accuracy on figurative with ChatGPT
- Current best figurative accuracy: ~**89%** (with FEWER few-shot examples — counterintuitively, more examples caused hallucination/overcomplexity)
- Overall accuracy (all classes): ~**69.6%** (or possibly 96.9% — transcript unclear, "overall the 696")
- After correcting ambiguous gold items → figurative accuracy goes to ~**78-80%** on Loterre
- Riccardo expects final result to be around **90%** overall once applied to whole corpus

**Ambiguous Loterre gold set cases (15 issues out of 41 figurative):**
- 5 were genuinely the model's fault (fixable with more examples)
- Riccardo's rules for the ambiguous ones:
  - **"Picture within a picture"** (tableau showing sea, curtain with bird motifs, gallery showing mountain drawings) → **FIGURATIVE** — it's a representation, not the real thing
  - **"Mountain of toys"** = metaphorical use of mountain to mean big quantity → **FIGURATIVE**
  - **"Animal farm to his room"** → ambiguous/lacking context, look into it, probably **FIGURATIVE**
  - **"Lac/étoile" (star bar structure)** → if it's "lac" (lake/luck), then REFERENTIAL; if it's "star", figurative — Riccardo thinks it's "lac" so probably REFERENTIAL
  - **Case #12 (ruins on shore of lake)** → she is described as ruins on the lake shore, Riccardo agrees it could go either way but leans FIGURATIVE

**What to run Task 1 on:**
- NOT the raw novels — run on the already-extracted ENTITES files in the `resultats/` folder
- `resultats/corpus_principal/ENTITES_contexte_animaux.csv` → ~**80 hours** (114,851 unique pairs × 2.5s with qwen3:30b)
- `resultats/corpus_principal/ENTITES_contexte_plantes.csv` → ~**44 hours** (63,594 unique pairs × 2.5s)
- `resultats/bestsellers/BESTSELLERS_contexte_animaux.csv` and plantes → run separately
- **Deduplicate**: write code to skip if same source+context already processed (some novels appear in both corpora)
- Total runtime: ~**5 full days** (80 + 44 hours = 124 hours = ~5 days)
- Start with main corpus first, then bestsellers

**Do NOT redo Joanna's homograph disambiguation** — accept ~85% accuracy as-is. Too costly (would mean redoing entire extraction pipeline). Some non-animals/plants will remain in the data — "so be it."

**Correction to do:** Fix the ambiguous Loterre gold items Riccardo flagged → rerun to get clean accuracy number for the research paper. Send Riccardo the updated results.

---

## Task 2 — Subcategory Classification (structure of figurative metaphor)

- The annotation scheme/categories are already built (Riccardo confirmed "this is already done")
- Previous work by Joanna was run on ChatGPT results (wrong) — **must use Labiba's own Task 1 results**
- Labiba tested a few rows manually on Joanna's data and results looked correct, but didn't run all (no point until Task 1 is done)
- Running Task 2 will also take several days compute (same order of magnitude as Task 1)
- **Gold set needed from Riccardo:** 200 randomized figurative occurrences
  - **100 animals + 100 plants** (randomized from YOUR figurative results, not Joanna's)
  - Riccardo will annotate with **TWO columns on the same gold set**:
    1. Sub-structure of the metaphor (type/form — the categories already in RESULTAT_typologie_compare_animaux.csv)
    2. Comparé category (what the animal/plant is being compared to — the 6 categories)
  - Riccardo said: "I gain time if I do the two at the same time"
- **Action for Labiba:** Generate the 200-item randomized gold CSV and send to Riccardo

---

## Task 3 — Agentivity (ESSENTIALLY DONE, needs documentation)

**Confirmed correct results (Riccardo approved the table):**

| Category | N | Active Agent | Passive | Object | Noun Complement | Other |
|---|---|---|---|---|---|---|
| HUMANS (all) | 219,651 | 37.2% | 1.4% | 12.8% | 20.1% | ~28.4% |
| Humans masculine | 118,142 | 38.2% | 1.3% | 13.2% | 18.8% | — |
| Humans feminine | 44,529 | 37.7% | 1.8% | 12.9% | 21.2% | — |
| ANIMALS (referential) | 95,243 | 24.4% | 0.7% | 20.2% | 33.6% | ~21.0% |
| PLANTS (all, mixed) | 64,269 | 11.8% | 0.4% | 15.1% | 49.5% | ~23.1% |

**Why percentages don't add to 100%:** The "Other" column (~21-28%) = syntactic dependency relations that don't fit the 4 main categories (prepositional phrases, appositions, existential constructions "il y a des lions", etc.)

**The lion examples Riccardo discussed — all confirmed correct:**
| Sentence | Lion's role | Classification |
|---|---|---|
| "Julien tua le lion" | direct object | Object |
| "Le lion fut tué par Julien" | passive subject (nsubj:pass) | Passive receiver |
| "Le lion mangea Julien" | subject of active verb | Active agent |
| "Julien fut mangé par **le lion**" | oblique agent (obl:agent) of passive | **Active agent** ← lion IS doing the action even in passive sentence |

**What Riccardo asked about the "Other":** He noticed the percentages don't sum to 100% and asked what's left. The report already contains the "Other" row — just make sure it's visible in the documentation/presentation.

**Remaining for Task 3:**
- Run Task 1 on plants → get referential-only plants → re-run dependency extraction → cleaner plant stats
- Run Task 1 on animals → re-run with our classifier (better than Joanna's manual filter) → cleaner animal stats
- **Human names:** Current model detects French names well but misses Arabic, English, African names. Riccardo said: "Not fundamental but could be cool." Solution discussed: use mid-sentence capitalization as heuristic (proper nouns are capitalized mid-sentence in French), and/or run multilingual NER model. Risk: might confuse "Bar" (Arabic name) with "bar" (fish). Also "Fleur" = name OR flower — need context.
- **Document "Other" category** explicitly in report

---

## Task 4.5 — Comparé/Comparant Classification

- Identifying WHAT the animal/plant is being compared TO in figurative uses (which of 6 categories)
- **6 categories** (labels seen in RESULTAT_typologie_compare_animaux.csv):
  - CH = corps humain (human body/attitude) — e.g., "elle a une peau d'anguille" → CH
  - Abstract concept (psychological state, abstract idea) — e.g., "la jeunesse est un chat insomniac" → abstract
  - Natural element — e.g., "l'île de Cuba ressemble à un lézard" → natural element
  - + 3 more categories (Riccardo has the full list, couldn't find it during meeting — check GitLab/Google Colab)
- **Terminology** (French/English):
  - Comparant = vehicle = the animal (the lion in "Paul est fort comme un lion")
  - Comparé = tenor/target = what is being compared to the animal (Paul in that example)
- **Can ONLY run after Task 1** is done (needs figurative-only cases)
- Same 200-item gold set as Task 2 (Riccardo annotates both tasks on same sheet = saves time)
- Joanna did a previous version with ChatGPT (in RESULTAT_typologie_compare_animaux.csv) — **use your own system, not Joanna's**
- Category definitions: Riccardo will find and send (probably in GitLab or Google Colab notebook)

---

## New Task — Additional Biodiversity Indices

- Shannon index already done by Joanna (in `scripts/shannon_rarefied.py`, visualised in `visualisations/Indice_Shannon.png`)
- Riccardo met a biologist/statistician expert in statistical biodiversity measurement
- That person suggested applying more ecological indices to the textual corpus — e.g., **equitability index** + others
- Riccardo received slides/documents from this biologist but didn't have time to study them yet
- **Not AI — just statistical formulas** applied to entity count distributions
- Riccardo will send slides/documents to Labiba during the week
- Discuss at **July 3rd meeting** with full details
- Theoretical interest: comparing methodology used by ecologists with what can be done in digital humanities

---

## Corpus Structure Clarification

- `CORPUS_TOTAL/` = **925 novels** (main corpus) — this is what Labiba has been running on
- There may also be a **1,074-novel version** (Labiba mentioned she wasn't sure which folder was which)
- `CORPUS_Bestsellers/` = ~**85 novels** (separate, some overlap with main corpus)
- The ENTITES extraction files exist separately for each:
  - `resultats/corpus_principal/` = main corpus entities
  - `resultats/bestsellers/` = bestseller entities
- **The 3 novels missing from Riccardo's narratology gold set** = they're in the Bestsellers corpus only, not in CORPUS_TOTAL
- For Task 1 application: run on BOTH `resultats/` folders, deduplicate by (source + context) to avoid running same sentence twice
- Task 5 (pipeline for frontdesk) = Joanna already did the entity extraction pipeline. **Deferred** for now.

---

## Decisions Made in This Meeting

| Decision | Detail |
|---|---|
| Joanna's disambiguation accepted | ~85% accurate, don't redo it |
| Task 1 approved | Run on ENTITES files, start with main corpus |
| Task 5 deferred | Too complicated, Joanna's pipeline already exists |
| "Espace" subcategory likely dropped | Models can't do it reliably |
| Task 0 ceiling acknowledged | 70-75% is SOTA, document the dead end |
| Gold set format | 200 figurative occurrences, 2 annotation columns, same sheet for Task 2 + Task 4.5 |
| Documentation is #1 priority | Everything — what worked, what didn't, why, all models tried |
| Next meeting | **July 3, 2026 at 11am** |
| Labiba leaves | July 15, 2026 |
| Riccardo away | July 3 to July 9 |

---

## Context from Today's Session (June 28, 2026)

- Confirmed: the agentivity table is correct, classification is correct
- Confirmed: the "Other" category is why percentages don't sum to 100%
- Confirmed: running Task 1 on `resultats/corpus_principal/ENTITES_contexte_*.csv` files (NOT raw novels)
- The transcript file is at: `/home/lfarooq/ecopoetique/riccardo_25june_meetingTranscript.md`
- Project folder fully explored: CORPUS_TOTAL, CORPUS_Bestsellers, TOKENS, lexiques, scripts, resultats, homographie, métaphore, morphosyntaxe, narratologie, visualisations all mapped

---

## Second meeting (`métaphore/Riccardo_second_meeting.txt`) — key new decisions

Builds on/updates the first meeting above. See [[project-task0-task1-status]] for the current numeric status these decisions feed into.

**Task 0 — FOCALISATION coding scheme changed.** Riccardo sent a new file with a genuinely different focalization framework ("more or less the same, but different codes" — later confirmed elsewhere to be reader-vs-character-knowledge rather than whose-consciousness) plus a new `MOD_DIA` mode category. **Action: Labiba must re-run Task 0 on this new schema file and Riccardo must send a fresh gold set annotated in the new FOCALISATION codes** before any further focalization comparison is meaningful — old FOCALISATION numbers are not comparable post-change.

**Task 0 — paid GPT approved.** Riccardo explicitly OK'd using the OpenAI API budget for this (~€22-25 estimated for a full run, explicitly offered up to €100-200 more if needed), with the one instruction to email him before topping up past a set amount rather than silently hitting the old $8-9 limit again. This is what funded the GPT-4o v7 76.1% result recorded in [[project-task0-task1-status]].

**Task 1 — approved and confirmed working well.** Riccardo reviewed ~15 ambiguous gold-set disagreements live; agreed most were genuine gold-set errors (not model errors), gave rulings on specific ambiguous cases (an "image within an image" — e.g. embroidered/painted birds, drawn mountains — should be scored FIGURATIVE, not referential, since it's a representation not the real thing). This is the origin of Task 2's new `IMAG` category.

**Task 2 — 3 new subcategories added live during this meeting**, discovered while Riccardo corrected the gold set:
- `COUL` — plant/animal term used purely to name a color (e.g. "vert pomme" = apple green) — Riccardo was unsure whether to keep this as its own category or fold it elsewhere; decided to add it as a category for now.
- `LOC_IDIOM` — fully lexicalized idiom where the animal/plant no longer evokes the real thing at all (his example: the French equivalent of "finding a needle in a haystack").
- `IMAG` — a depiction/representation of the animal/plant (drawing, embroidery, painting) rather than the animal/plant itself.
No formal written definitions for these 3 exist yet — captured only as Riccardo's spoken examples in the transcript. **Still need to ask him for a written definitions doc.**

**Task 3 — multilingual names explicitly requested again.** Riccardo asked to see actual example rows from the human-agentivity results and was surprised the % undetermined-gender was so high; confirmed this is very likely because the extraction only used a French-trained spaCy model and the corpus (925 novels, many with Francophone-Africa/Maghreb settings) plausibly contains many Arabic-origin and some English-origin names it can't recognize. Explicitly asked for this to be extended — this is the origin of `extract_humains_multilingual.py`.

**Documentation — Riccardo's #1 ask.** Wants as much detail as possible on every method/technique tried and what did/didn't work, "as much as you can, as long as it stays understandable" — up to ~40 pages is fine with him. Explicitly said file-level specifics ("which exact file did you run") matter less than being able to follow the steps and translate the approach into his own understanding. Asked for at least a partial draft by Wednesday so he can read it before the next meeting. **This request is what produced `PROJECT_DOCUMENTATION.md`.**

**New "biodiversity indices" task, deprioritized/self-directed by Riccardo.** He's been in contact with a biologist/statistician who does real-world biodiversity measurement and sent him additional statistical indices beyond Shannon (already implemented) that could in principle be applied to the corpus the same way. Riccardo said he'd likely do this analysis himself ("I think I can do it myself... it's just applying new calculation to data we already have") — framed as his own side-exploration for theoretical interest, not a hard ask of Labiba, though he left the door open ("let me know if you cannot do it").

**Task 5 reconfirmed dropped**, same reasoning as first meeting.

**Deadline logistics confirmed:** last working day effectively **2026-07-13** (July 14 is a public holiday, July 15 is departure). Riccardo explicitly said not to worry about finishing everything by the 13th — remote follow-up after Labiba leaves is fine ("we can communicate online until I give you the final results").
