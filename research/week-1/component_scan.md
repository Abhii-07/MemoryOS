# Week 1 — Component Scan

**Focus this week:** memory admission, ranking & conflict resolution, reflection & lifecycle.
Chosen because they map to the least-resolved open questions from Deliverable 1 (what to store,
how to rank, how to resolve contradiction, how to decay).

---

## 1. Memory extraction & admission

**Sources glimpsed:** Memory-R1 (Yan et al., 2026), AgeMem (Yu et al., 2026), A-MAC (Zhang et al.,
2026), MemGPT (Packer et al., 2023), Mem0's 2026 state-of-the-field report.

**Mechanisms / ideas found:**
- The field has largely converged on treating admission as an explicit operation set — ADD,
  UPDATE, DELETE, NOOP — rather than a binary "store or don't." Memory-R1 trains an RL policy over
  exactly these four actions.
- A-MAC decomposes the admission decision into three interpretable factors: utility, confidence,
  and novelty, instead of a single relevance score. That's a meaningfully different design than
  "embed it and store if similarity is low enough to existing memories."
- Mem0's 2026 report flags something that's easy to miss: systems that only extract from
  user-stated facts under-cover the conversation. Agent-generated facts and recommendations
  (things the assistant itself concluded or committed to) need to be admitted with the same
  weight, or the assistant forgets its own prior commitments even when the user's statements are
  all captured correctly.

**Relevance to this system:** Deliverable 1 flagged "distinguish durable knowledge from transient
context" as an open question with no answer yet. The ADD/UPDATE/DELETE/NOOP framing gives a
concrete decision space instead of a fuzzy threshold, and the utility/confidence/novelty
decomposition gives a testable basis for tuning it later, rather than one opaque score.

---

## 2. Ranking & conflict resolution

**Sources glimpsed:** "Don't Ask the LLM to Track Freshness" (2026), Graphiti/Zep's bitemporal
model, TOKI (bitemporal operator algebra for contradiction resolution), the Nuanced Perspective
write-up on agentic memory design (2026).

**Mechanisms / ideas found:**
- The most useful — and most surprising — finding this week: letting the LLM itself judge which
  of two conflicting facts is more current performs badly, even when the model is told explicitly
  that higher serial numbers mean newer facts. On the Memory Agent Bench fact-consolidation task,
  every evaluated system (including strong long-context baselines) scored well under what you'd
  expect from a task that's supposed to be a simple recency check. The paper's conclusion is that
  freshness tracking has to be handled deterministically, outside the model, not delegated to
  in-context reasoning.
- Graphiti's approach is to give every memory an explicit `valid_until` field rather than relying
  on recency-as-a-similarity-adjustment. When a new fact supersedes an old one, the old one gets
  closed out with a timestamp instead of just sitting there at lower rank.
- A recurring warning across sources: mixing episodic memory (specific dated events) and semantic
  memory (general facts/preferences) into one similarity index degrades retrieval for both. They
  need separate handling, not one shared embedding space with recency as an afterthought.

**Relevance to this system:** This directly attacks Deliverable 1's Open Question 3 (how to
resolve conflicting memories). It also reframes Open Question 4 — the answer isn't "add recency as
one more weighted signal into a similarity score," it's "don't let similarity-plus-recency make
this decision at all; make supersession an explicit, structural operation."

---

## 3. Reflection & lifecycle (decay, consolidation, forgetting)

**Sources glimpsed:** Hindsight's "Consolidation Problem in Agent Memory" write-up, FiFA benchmark
/ "forgetting-by-design" (Alqithami, 2025), a selective-forgetting taxonomy (Gu et al., 2026), the
"Always-On Agents" survey (2026).

**Mechanisms / ideas found:**
- A clean framing worth borrowing directly: consolidation runs on four separate levers —
  *importance* (does this become a memory at all), *merge* (do multiple facts about the same
  entity unify into one record), *decay* (does confidence in an old fact degrade over time), and
  *eviction* (does the memory leave the system entirely). Treating these as four independent
  decisions instead of one "cleanup job" is more tractable to implement and reason about.
- The selective-forgetting taxonomy splits forgetting into passive decay, active deletion,
  safety-triggered removal, and adaptive reinforcement — different mechanisms for different
  reasons a memory should lose influence, rather than one global decay rate.
- Repeated point across sources: forgetting shouldn't mean destructive deletion by default —
  reducing a memory's *accessibility* (lower rank, eventually excluded from retrieval) is
  different from actually removing it, and the two need different triggers. Destructive deletion
  is really its own category, driven by explicit user request or a privacy/safety trigger, not by
  ordinary staleness.

**Relevance to this system:** Maps to Open Question 2 (how memories evolve) directly, and also
sharpens the privacy requirement — "deletion" as a user-facing guarantee (Deliverable 1,
Constraint 4) is a different mechanism than "decay" as a ranking behavior, and conflating them
would be a design mistake worth avoiding before Deliverable 4.
