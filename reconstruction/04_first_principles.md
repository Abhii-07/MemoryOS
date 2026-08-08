# First-Principles Derivation of the Minimum Required Capabilities

> Deliverable 1, Part 4. We derive — from the problem statement
> (`01_problem.md`), the historical chain (`02_timeline.md`), and the
> measured-in-design failures (`03_failure_analysis.md`) — the **minimum
> set of capabilities** any credible solution to the conversational-memory
> problem must have. The argument runs from constraints and failures to
> capabilities; it does not assume any particular architecture.
>
> Claim tags: `[P:n]` paper-supported (see `sources.md`); `[A: …]` assumption
> to be validated by the naive baseline (Deliverable 3).

---

## 0. Method

A capability is *required* if one of the following holds:

1. **Constraint-derived.** Without it, a hard constraint (C1–C8) is violated
   by construction.
2. **Failure-derived.** Without it, one of the observed failures (A1–A5) in
   `failure_analysis.md` recurs.
3. **Transition-derived.** Without it, one of the historical bottlenecks in
   `02_timeline.md` re-opens.

Everything below is a consequence of applying these three tests to the
reconstruction. The final design (Deliverable 4) must map each component to
at least one capability, and each capability to at least one of these
derivations.

---

## 1. Capability R1 — Admission: decide what is worth retaining

**From which pressure.** A4 stores everything and fails on quality and
governance (C5: sensitive data retrievable; C1-by-quality: wrong content
injects); A2 stores everything and overflows (C1). A store with no admission
policy cannot satisfy C4, C5, or C8: it inevitably accumulates the
irrelevant, the transient, and the sensitive alongside the durable.

**Derived requirement.** The system must decide, before storing, whether a
candidate is worth keeping: durable preference vs. transient remark;
personal fact vs. trivia; sensitive vs. non-sensitive; with an explicit,
justified policy and a confidence attached. This is the first decision point
of the whole system. [A: admission accuracy, threshold behavior]

**Minimum shape.** A predicate (heuristic or learned) over the candidate and
its context, with the decision recorded for observability. The exact
thresholds and signals are a design problem, not a requirement problem.

---

## 2. Capability R2 — Representation: type, provenance, confidence

**From which pressure.** A3 fails because stored content cannot be ranked by
anything but literal match. A4 fails because all content is treated as
equally valid "chunks" — the type of statement (preference vs. fact vs.
episode), its source, and its certainty are invisible to ranking (C4). The
memory literature consistently represents memories with structured fields
(type, importance, confidence, source) to enable later reasoning [P:2][P:3]
[P:8][P:9].

**Derived requirement.** Each retained item must carry, at minimum: a **type**
(what kind of statement), **provenance** (when/who/where it came from), and a
**confidence** (how sure the admission was). These fields are the raw
material for every later capability (ranking, lifecycle, audit).

**Minimum shape.** A schema (or structured representation) that guarantees
these fields exist per item, persisted with the item. This is what makes the
system auditable (C5) and rankable (C4).

---

## 3. Capability R3 — Safe, isolated, governed storage

**From which pressure.** C6 (tenant isolation) is a non-negotiable gate. A4's
global index makes cross-tenant leakage possible [A]. C5 requires retention,
correction, and deletion to be enforceable — impossible on a store that
cannot delete or scope.

**Derived requirement.** The store must enforce: **isolation** between
tenants (data-level, index-level, retrieval-level — to be decided in design),
**deletion** that removes content from both storage and retrieval paths, and
**retention** policies with auditability. Storage growth must be bounded
(C8): prunable, not monotonic.

**Minimum shape.** A storage layer where every read/write is tenant-scoped,
with an explicit deletion path and a documented retention/expiration policy.

---

## 4. Capability R4 — Retrieval and multi-signal ranking

**From which pressure.** A3 proves lexical matching is insufficient; A4 proves
single-signal similarity is insufficient (contradictions, recency, importance
ignored). C4 requires the *current* truth to win. The literature's answer is
multi-signal ranking: relevance, recency, importance, confidence, and
diversity combined into a policy [P:5][P:8][P:9][P:10][P:11].

**Derived requirement.** Retrieval must be able to rank candidates by
multiple justified signals — not a single similarity score — and to resolve
conflicts (a newer statement superseding an older one). The ranking policy
must be explicit, testable, and calibratable.

**Minimum shape.** A ranked retrieval interface whose score is a documented
function of ≥2 signals; the function is part of the design (Deliverable 4)
and its parameters are measured, not guessed.

---

## 5. Capability R5 — Context construction within a token budget

**From which pressure.** C1 is physical: the model's window is finite [P:4].
A2 overflows because nothing was selected; A4 fills the budget with the wrong
items. The literature introduces explicit budget/paging mechanisms for this
(MemGPT's paging and main-memory metaphor [P:9]).

**Derived requirement.** The system must select, order, and inject content
into the context under a defined token budget — with fallback behavior when
nothing is relevant (cold start, no-relevant-memory) and protection against
adversarial content inside memory.

**Minimum shape.** A context-construction step that takes a budget + a set of
candidate items and returns a bounded, ordered, well-formed context. Budget
overshoot must be impossible (enforced, not aspirational).

---

## 6. Capability R6 — Lifecycle: update, consolidate, decay, delete

**From which pressure.** A2/A4 both suffer because retained content never
changes: contradictions coexist, superseded preferences survive, and the
store grows without bound (C8). The literature's lifecycle mechanisms —
reflection and summarization (Generative Agents [P:8]), paging/hierarchical
memory (MemGPT [P:9]), and the general notion of forgetting/decay — exist
precisely to answer this. [A: decay policy]

**Derived requirement.** The system must support: **correction** (a new
statement invalidates an old one), **consolidation** (many low-level items
into higher-level ones), **decay/expiration** (items lose relevance or
expire), and **deletion** (policy-driven removal). It must not reinforce
errors by repeatedly retrieving them (error reinforcement — a recognised
follow-on concern argued in retrieval-decision literature, not raised by
Generative Agents themselves). [A: error-reinforcement guard]

**Minimum shape.** Background jobs and update paths with defined semantics
for each lifecycle operation; each operation recorded for observability.

---

## 7. Capability R7 — Observability: decisions exposed

**From which pressure.** The handbook's evaluation framework and non-negotiable
gates require that critical claims be backed by reproducible evidence, and
that known failures be reported. Without logs and traces of admission,
retrieval, and ranking decisions, the system is a black box that cannot be
verified (C7).

**Derived requirement.** The system must record, per decision: what was
admitted/rejected and why; what was retrieved and how it was ranked; what was
injected and within what budget. Outputs must be comparable against a fixed
evaluation set offline.

**Minimum shape.** Structured logs/traces of memory decisions plus an offline
evaluation harness with fixed datasets and seeds (C7).

---

## 8. Capability R8 — Reproducible offline evaluation

**From which pressure.** C7 and the evaluation framework. A system whose
behavior cannot be reproduced cannot be verified — and verification is the
non-negotiable gate.

**Derived requirement.** Fixed evaluation datasets, fixed seeds, defined
metrics (retrieval quality, end-to-end quality, p50/p95 latency, storage
growth, token usage, failure taxonomy), and a repeatable command that produces
results. The naive baseline (Deliverable 3) implements the first such
harness; the final system must be compared against it.

---

## 9. Capability map — every capability traced to its origin

| Capability | Derived from (constraint / failure / transition) |
|---|---|
| R1 Admission | C5, C8; A2 (store-everything), A4 (store-everything) |
| R2 Representation | C4; A3 (untagged content), A4 (untagged content) |
| R3 Safe/isolated storage | C5, C6, C8; A4 (global index, PII retrievable) |
| R4 Retrieval + multi-signal ranking | C4; A3 (lexical), A4 (single-signal) |
| R5 Context construction + budget | C1, C2, C3; A2 (overflow), A4 (wrong items) |
| R6 Lifecycle | C4, C8; A2 (contradiction), A4 (no decay), [P:8][P:9] |
| R7 Observability | C7; evaluation gates; handbook §11 |
| R8 Reproducible evaluation | C7; verification gates |

**Note.** The naive baseline (Deliverable 3) will *measure* R4/R5/R6's
absence; until then, the links from A2/A4 marked `[A]` are clearly-labelled
assumptions rather than measurements. No capability in this table depends on
a measured claim; each is derivable from a hard constraint or a structurally
forced failure.

**Stage → requirement mapping.** The historical stages of `02_timeline.md`
map one-to-one onto the capability set — each stage was forced forward by the
absence of a capability, and each capability is therefore also a *stage
requirement*:

| Stage (timeline) | The bottleneck of that stage | Capability that removes it |
|---|---|---|
| Stage 0 — implicit model context | Amnesia across calls/sessions | Persistence → R1/R3 (store with admission) |
| Stage 1 — full-conversation replay | Overflow; pollution; cost | Selective injection → R5 + R4 (budgeted, ranked retrieval) |
| Stage 2 — external store + retrieval (RAG) | Store-everything; single-signal ranking; no lifecycle; no isolation | R1 (admission) + R4 (multi-signal ranking) + R6 (lifecycle) + R3 (isolation) |
| Stage 3 — managed memory (hierarchy, reflection, paging, governance) | (open) — correctness over time, governance, auditable behavior | R5–R8 (budget, lifecycle, observability, reproducibility) |

Reading the table bottom-up reproduces the historical chain; reading it
top-down reproduces the capability set. This is the stage↔requirement
correspondence promised in the reconstruction: every capability is a
chain, opened by a bottleneck and closed by a requirement.

---

## 10. Open questions that will shape the design

These are the unresolved questions from `01_problem.md` §8, restated as the
design hypotheses they will become:

1. **Importance vs. recency.** What is the correct relative weight, and is it
   per-type (preference vs. fact vs. episode)? (R4)
2. **Supersession.** Is a newer statement always authoritative, or only when
   it explicitly corrects? (R4/R6)
3. **Budget policy.** How are tokens allocated across types, and what is the
   floor for cold start? (R5)
4. **Admission minimality.** What is the smallest policy that keeps both
   low-value and sensitive content out? (R1)
5. **Decay vs. deletion.** Do items expire gracefully or are they deleted by
   policy, and how does each interact with the hard deletion guarantee? (R3/R6)
6. **Error reinforcement.** How is a wrong memory corrected end-to-end without
   being retrieved again and reinforced? (R6)
7. **Isolation depth.** Storage, index, retrieval — at which layers, and at
   what cost, must isolation be enforced? (R3)
8. **Falsification.** What experiment would show admission/ranking matter less
   than raw recall? (The naive baseline is the first attempt.)
9. **User control of memory.** Should users be able to inspect, edit, delete,
   or disable specific memories directly, and how do those controls interact
   with the background lifecycle (consolidation, decay)? This is the
   product-facing surface of R3/R6 (storage + lifecycle) and determines the
   API of the memory editor. [A: user memory controls — naive baseline
   measures what happens when a user deletes or corrects a memory]

---

## 11. Completion check

The handbook's completion standard (Deliverable 1): *"Another engineer who
has not seen the target architecture can explain why it is needed, which
simpler designs fail, and what requirements follow from those failures."*

- Why needed → `01_problem.md` (bottleneck, users, consequences)
- Which simpler designs fail → `03_failure_analysis.md` (A1–A5, each with
  failure + violated constraint)
- What requirements follow → this document (R1–R8, each traced to a
  constraint or failure)
- Historical chain → `historical_timeline.pdf`

A reader holding all four documents can derive the capability set
independently of the eventual architecture — which is exactly the goal.

*End of first-principles derivation.*