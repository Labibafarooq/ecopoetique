---
name: feedback-task45-category-is-target-entity-type
description: "Task 4.5's CH/P/NH/O/E/A categories classify the comparison TARGET's ontological entity type, not the semantic domain of the trait being illustrated — a standing rule from Riccardo, not a one-off tiebreaker"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 21f8b9ea-e13d-4990-94e1-6f1c83ebe2a7
---

For Task 4.5 (`comparison/run_task45_compare_category.py`), the six categories (CH, P, NH, O, E, A) classify **what kind of entity the metaphor's target (comparé) actually is**, not what quality/trait the comparison illustrates.

**Why**: Riccardo's explicit clarification (email, 2026-07-10), responding to a diagnosis that found several "CH" gold labels attached to personality traits (lâcheté, indépendance, méchanceté, panique...) which looked like mislabels under a "CH = physiological only" reading of the category doc. His example: "Je bats lâchement en retraite... comme un rat" — target = "il" (a person) → **CH**, regardless of the fact that the illustrated trait (cowardice) is psychological. Contrast: "Mes émotions se cachaient comme des rats" → target = "mes émotions" → **P**. "L'île ressemblait à un rat" → target = "l'île" → **E**. Same vehicle, same action, different category purely by what the target *is*.

This overturned an earlier fix in the same project (2026-07-10, the CH/P "Piège fréquent" prompt patch telling the model "personality traits → P, not CH") which was built on the wrong theory and is the likely explanation for that fix's accuracy regression (77.9%→68.3% on the 104-row gold set). It also means a batch of "gold mislabel" candidates found earlier in the same session (12+ CH rows with personality-trait fondement) were **not errors at all** — gold was right, the category's meaning was misunderstood.

**How to apply**: Before writing or fixing any Task 4.5 prompt logic, first identify the referent of the comparison (who/what is literally being compared to the animal/plant/vehicle — usually the sentence's real subject, e.g. "il," "elle," "les émotions," "l'île"), then classify *that entity's* type. Never classify based on the semantic domain of the adjective/trait/fondement alone. If a prompt fix is proposed that reads like "trait X belongs to category Y," check it against this entity-type framing before applying it — that's exactly the mistake made once already. See [[project_2026-07-10_session3]] for the full incident and the not-yet-implemented prompt rewrite this implies.

## Update 2026-07-10 (later same day): the rule is more nuanced than "target=person → always CH"

Implementing the rule above verbatim (rat/il → CH always when target is a person) still produced 7 wrong predictions on gold, all CH-predicted-but-gold-P, all person-referent rows (jument/elle, singe/elle, ânes/ils, porc/tu, aigle/"Henri Beyle", chacal/"Pierre Castaneda", citrouille/"Max"). Sent Riccardo these exact contrastive examples; his answer:

> "It is a little more complicated than that. In these cases it depends if the pronoun is referring to the physical dimension of the person or to the psychological one. In the case of the rats, I judged that the fact of 'battre en retraite' was bound to the physical dimension of the body, the way the body moved — even if I guess you can consider otherwise. In the case Pierre Castaneda for instance I judge that the referent was not the body of Castaneda, but his behavior, so P."

So **when the cible is a person, there is a second-level split**: is the comparison about the person's **physical/bodily dimension** (the body itself, a physical movement/action, a physiological process) → **CH**, or about their **psychological/behavioral dimension** (character, conduct, moral/personality trait — courage, cowardice, greed, stupidity, intelligence, etc.) → **P**. The rat/il example is CH specifically because "battre en retraite" (retreating) is a physical body-movement in Riccardo's judgment, not because "target=person" alone settles it — a genuinely fine distinction he acknowledges is itself judgment-call-dependent ("even if I guess you can consider otherwise").

He also clarified a second case, the fougère row ("...apparenté en mon penser au lycopode, à la fougère", gold=CH): the cible is **not** "mon penser" taken literally — "you have to extend the sentence" to find the real referent, which (given the fuller context: the narrator lying immobile, "en parfait état de légumerie") is his **physical body**, lying vegetative/inert. The surface noun phrase nearest the vehicle ("mon penser") can be a red herring; always check whether the wider sentence/paragraph reveals a different true referent, especially a physical body being described via a mental-sounding turn of phrase.

**Updated how-to-apply**: after identifying the cible per the original entity-type rule, if the cible IS a person, apply this second split (physical/bodily action or process → CH; character/behavior/conduct → P) before finalizing the category. Do not stop at "it's a person, therefore CH."

**Important — file location**: `comparison/run_task45_compare_category.py` is FROZEN at its known-good, tested 85/104=81.7% state (the entity-type + bucket-1/2 + few-shot-examples version, no physical/psychological split) — per Labiba's explicit instruction (2026-07-10), do not edit this file further. The physical/psychological refinement above was instead implemented in a **new sibling file, `comparison/run_task45_compare_category_v2_physical_psych.py`** (own output file `resultats_task45_compare_category_v2_physical_psych.csv`, so it won't clobber the frozen 81.7% results). **Not yet tested — a GPU freeze began the same day, lasting ~12 days (see [[project_gpu_freeze_20260710]])**. Test the v2 file against the gold set (especially the 7 contrastive rows above, plus citrouille/17 which may now resolve correctly as P) once GPU access returns. If it beats 81.7%, promote it; if not, the frozen original remains the fallback.

Riccardo separately said (same email) he'll check his references for the open Task 2 DE_PARANGON/DE_PROP/META_APP questions "first thing tomorrow" (i.e., 2026-07-11) — worth following up if no answer arrives.
