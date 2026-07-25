---
name: feedback-proactive-checkpointing
description: "Labiba wants session progress checkpointed to memory proactively, not only when she explicitly asks — lost a full session's context because nothing was saved"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 965ac941-d986-49de-a846-65fe695931a9
---

Save a project-status memory update at natural checkpoints during a session — end of session, after a significant decision, or after real progress — without waiting to be asked.

**Why:** She asked "do you remember our conversation from last night" and the answer was no — the most recent memory checkpoint was from the prior afternoon, so an entire session's work/decisions were lost. She then said "from now on save everything like chat in memory."

**How to apply:** This does NOT mean logging raw verbatim chat transcripts — the memory system excludes ephemeral conversation content by design, and dumping full transcripts would bury the signal. Instead: treat "significant progress happened" as an implicit trigger for a memory write, the same way [[feedback-ecopoetique-experiments]] already treats "investigate first" as a standing preference rather than something she has to repeat. Concretely, for long-running/multi-session work (e.g. [[project-task0-task1-status]]), update or create the relevant project-status memory before the session ends or before a natural pause, not just when explicitly asked for a checkpoint. Still keep entries distilled (facts/decisions/state), not raw dialogue.
