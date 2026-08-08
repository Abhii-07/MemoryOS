# System Design — Conversational Memory Intelligence System

**Deliverable 4 · Draft, Part 1 of 3 (Sections 1–6) — Revised**
Abhijeet Hiwale · August 2026
*(Revised after external technical review — see change notes at end of file.)*

---

## 1. Executive Summary and Scope

This system decides what conversational information is worth remembering, stores it safely,
retrieves and ranks it against a live query, injects it into model context within a fixed budget,
and manages how it changes or fades over time. It is the direct answer to Deliverable 1's core
problem: a stateless assistant re-initializes its understanding of the user every session, forcing
repeated re-explanation and producing contradictory suggestions once a decision is forgotten.

Deliverable 3's naive baseline confirmed four specific, measured failure modes that this design
exists to fix — not hypothetical ones:

1. Stale facts outrank current facts when both are lexically similar to a query (33% failure rate
   on the baseline's contradiction cases).
2. Sensitive content has no mechanism to be caught before it's retrieved and injected (100% leak
   rate on the baseline's sensitive-info case).
3. The system has no concept of "nothing relevant exists" — it always returns its best available
   match regardless of actual relevance (50% false-positive rate on cold-start cases).
4. Cases that *did* pass did so because of lexical luck (distinctive vocabulary), not because the
   underlying mechanism is robust — this is a latent risk, not a solved problem.

### System boundary

**Outside this system:** the end user, the calling LLM/assistant application, and the
application's own conversation-turn handling. **Inside this system:** admission, storage,
retrieval, ranking, context construction, and lifecycle management, all reachable only through the
Memory Service interface described in Section 5. The calling application sends conversation turns
in and a query out; it never talks to an internal component directly.

## 2. Users, Use Cases, and Non-Goals

**Primary user:** a single end user interacting with a conversational assistant across multiple
sessions, where continuity of context (project state, preferences, prior decisions) has direct
value — the scenario Deliverable 1's problem statement is built around.

**In scope:**
- Single-user conversational memory across sessions (the primary use case).
- Multi-tenant deployment (multiple users' memories coexisting, isolated from each other) — this
  is required by Deliverable 1's privacy constraint and Week 4's isolation research, even though
  the primary narrative use case is single-user.
- Text-based conversational memory only — no image, audio, or structured-document memory.

**Explicitly out of scope for this design** (deferred, not ignored — each has a stated reason):
- Multi-agent shared memory (one memory pool accessed by multiple cooperating agents). Week 4's
  research on cross-tenant/cross-agent memory poisoning applies here, but this design treats
  single-tenant, single-agent memory as the harder-to-get-right foundation first.
- Cross-modal memory (remembering things from images or audio). No research week covered this;
  adding it would require its own admission/representation research this project hasn't done.
- Real-time collaborative memory (multiple users editing a shared memory space simultaneously).
  Deliverable 1's scope never required this, and it introduces concurrency problems (conflicting
  simultaneous writes) this design doesn't attempt to solve.

## 3. Inputs, Outputs, Constraints, Priorities, and Success Metrics

**Inputs:** conversation turns (both user and assistant, per Week 1's finding that
assistant-generated commitments need admission too), each turn's user ID and timestamp, and a
per-query token budget from the calling application.

**Outputs:** a ranked, budget-respecting block of injected context for a given query; structured
logs/traces of every memory operation (per Week 3's OpenTelemetry decision); and an explicit
"nothing relevant" signal when no memory clears a configurable relevance threshold — a first-class
output this design adds specifically because Deliverable 3 showed a naive system can't produce it.

**Constraints** (carried directly from Deliverable 1, unchanged):
context/token budget, latency (retrieval sits on the critical path), cost/scale (bounded growth,
not indefinite accumulation), privacy/isolation (per-user enforcement, not just correctness in the
common case), correctness over time (staleness and relevance are ongoing judgment calls, not
one-time decisions), and safety (memory can't be used to bypass safety behavior or resurface
content the user didn't intend to persist).

**Architectural priorities.** These constraints conflict with each other in practice, so this
design states explicitly what wins when they do:

| Priority | Attribute |
|---|---|
| Highest | Privacy & tenant isolation |
| High | Correctness (contradiction/staleness handling) |
| High | Latency |
| Medium | Cost |
| Medium | Recall |
| Low | Storage efficiency |

Concretely: this design will accept a recall loss to enforce a relevance floor or a privacy filter
(Section 4's invariants), and will accept storage growth before it accepts a shortcut on
correctness. This explains, for example, why Section 5's retrieval component applies a hard
tenant pre-filter even where it costs a small amount of retrieval flexibility.

**Success metrics, with target values.** These are engineering objectives chosen to represent
acceptable interactive performance, not values derived from an existing benchmark or a specific
prior system — there's no published number this project is trying to match, so these targets
should be read as this project's own bar, revisable once Deliverable 6 produces real measurements
against them. They also need a caveat the numbers alone don't carry: Deliverable 3's naive baseline
already hit 100% recall@5, but on a 10-case, hand-built dataset with no real scale or paraphrase
pressure. The targets below are for a realistic-scale workload, not a bar the baseline already
cleared.

| Metric | Target |
|---|---|
| Recall@5 | > 90% |
| Precision@1 | > 95% |
| Contradiction/staleness failure rate | < 5% (naive baseline measured 33%) |
| False-positive relevance rate | < 5% (naive baseline measured 50%) |
| Retrieval latency (p95) | < 100ms |
| Context construction latency | < 20ms |
| Sensitive-content leak rate | 0% (naive baseline measured 100%) |

These map directly back to Deliverable 1's actual user-facing goal — fewer re-explanations, no
contradicted decisions — rather than being treated as ends in themselves, per Week 3's challenge
notes on keeping proxy metrics honest.

## 4. Assumptions, Invariants, and Failure Modes

**Assumptions** (stated explicitly, since an unstated assumption is an unreviewed one):

- Dense embeddings are available from an external service or local model at acceptable latency
  (Deliverable 3's TF-IDF baseline was a sandbox-forced substitute, not the production plan).
- Clocks across the system are reasonably synchronized — `valid_until` supersession depends on
  consistent ordering of writes.
- Tenant IDs arriving at the Memory Service are already authenticated upstream; this design does
  not implement authentication itself, only enforces isolation given a trusted tenant ID.
- pgvector's performance holds at the dataset sizes this system expects at MVP scale (per Week 2's
  adopted decision) — this assumption has an explicit revisit trigger in Section 13 (capacity).
- Conversational turns are assumed to arrive in order, per user, at the admission boundary, for this MVP scope. Out-of-order or duplicate delivery is not handled by this design and is explicit future work, not a hidden limitation.

**Invariants** (things that must always hold, regardless of implementation detail):

- A memory belonging to tenant A must never be returned for a query from tenant B. (Week 4:
  namespace isolation is necessary but not sufficient — this invariant requires a deterministic
  pre-filter, not a similarity-based one.)
- A deletion request must remove a memory's influence from every derived artifact built from it,
  not just the source record. (Week 4's "backflow" finding — this is the hardest invariant to
  guarantee in the whole system, flagged honestly rather than assumed solved.)
- When two memories conflict, the system must be able to identify which is current without relying
  on an LLM's in-context judgment of freshness. (Week 3's benchmark finding: LLM-judged freshness
  fails even with explicit instructions.)
- The system must be able to say "nothing relevant" rather than always returning a best-available
  match. (Directly added in response to Deliverable 3's Failure 3.)
- Every retrieved memory must be traceable back to its originating conversation turn through its
  stored provenance record. (This turns Week 4's provenance-tagging decision into an enforced
  invariant rather than an optional field — directly closes the self-review finding that
  provenance "must change real downstream behavior, not just exist in the schema.")

**Failure modes, split by recoverability** — a distinction the initial draft collapsed, and
shouldn't have, since these are different engineering problems with different acceptable
responses:

| Recoverable (degrade gracefully, retry, or correct on next write) | Non-recoverable (must be prevented structurally, not just handled) |
|---|---|
| Retrieval miss (relevant memory not in top-k) | Cross-tenant leak |
| Relevance false positive (irrelevant memory surfaces) | Deletion propagation failure (backflow) |
| Stale memory outranks current, but current is still in top-k | Sensitive data persisted with no provenance trail to remove it |
| Budget truncation drops a lower-priority memory | |

Recoverable failures degrade quality; non-recoverable failures are the ones the architectural
priorities table above exists to protect against even at a cost to recall or latency.

## 5. Architecture Overview

The architecture consists of six loosely coupled components, each introduced to address a
specific limitation identified during the research phase or Deliverable 3's evaluation, all
orchestrated by a single **Memory Service** that owns the request flow — no calling application
talks to an individual component directly.

```
                    Client Application
                            |
                      Memory Service
                     /              \
          Online Request Path      Background Worker
    Admission -> Storage ->          Lifecycle
    Retrieval -> Ranking ->    (decay, merge, consolidation,
    Context Builder            deletion propagation)
```

**Synchronous vs. asynchronous.** Admission, storage writes, retrieval, ranking, and context
construction all happen on the synchronous online path — a query cannot return until these
complete, so their latency budget is real and enforced (Section 3's targets). Decay, merge,
consolidation, and deletion propagation run as an asynchronous background process, per Week 1's
original lifecycle design — they are not on any request's critical path, which is precisely what
keeps the online path's latency bounded regardless of how much lifecycle work is pending.

1. **Admission** — classifies each candidate memory as ADD / UPDATE / DELETE / NOOP (Week 1),
   requires entity/slot-linking as a prerequisite capability, tags every record with provenance
   (Week 4), and applies PII detection as a pre-guardrail before anything is stored (Week 4).
   *Input: a conversation turn. Output: a memory operation (one of ADD/UPDATE/DELETE/NOOP) plus
   its provenance tag.*
2. **Storage** — pgvector-backed (Week 2, MVP-scoped), partitioned by tenant with deterministic
   filtering (Week 2 + Week 4 amendment), storing typed records with provenance and validity
   windows attached. *Input: a memory operation. Output: a stored memory ID and confirmation.*
3. **Retrieval** — hybrid BM25 + dense + RRF fusion (Week 2), no LLM inference on the critical
   request path, which keeps retrieval latency low and deterministic. Applies an explicit,
   configurable relevance threshold below which nothing is returned (new — closes Deliverable 3's
   Failure 3 gap). *Input: a query plus tenant ID. Output: a ranked candidate set, or an explicit
   empty result.*
4. **Ranking & conflict resolution** — deterministic `valid_until` supersession (Week 1) with a
   low-confidence fallback that keeps both records retrievable rather than silently closing one
   out (per Week 1's self-review). *Input: retrieval's candidate set. Output: a final ordered
   list with superseded records marked or excluded.*
5. **Context construction** — explicit per-zone token budgets including a dedicated tool-output
   zone (Week 2), applying the context-rot finding as a hard design constraint rather than relying
   on window size. *Input: the ranked list plus the caller's token budget. Output: the injected
   context block.*
6. **Lifecycle & consolidation** — four-lever framework (importance/merge/decay/eviction, Week 1),
   decay as reduced accessibility distinct from hard deletion (Week 1), unverified/low-provenance
   memory expiring by default (Week 4), and deletion propagation through consolidation lineage
   (Week 4's hardest open requirement). *Input: storage state on a schedule, plus explicit
   deletion requests. Output: updated/merged/evicted records, propagated through any derived
   artifacts.*

Each component's detailed responsibilities, interfaces, and data flow are specified further in
`architecture.pdf` and `data_flow.pdf`. Section 6 below summarizes the responsibility boundaries.

## 6. Component Responsibility Boundaries

A short table clarifying what each component is and is not responsible for, since several of
Deliverable 3's failures came from responsibilities that were implicitly nobody's job:

| Component | Responsible for | Explicitly NOT responsible for |
|---|---|---|
| Admission | Classifying ADD/UPDATE/DELETE/NOOP, provenance tagging, PII pre-filtering | Ranking retrieved results, deciding what's "relevant" to a query |
| Storage | Persistence, tenant partitioning, validity-window fields | Similarity scoring, relevance judgments |
| Retrieval | Hybrid search, relevance floor, tenant pre-filter | Deciding which of two conflicting results is current (that's Ranking) |
| Ranking & conflict resolution | Supersession, low-confidence fallback, final ordering | Storage, admission-time filtering |
| Context construction | Token budgeting, zone allocation, truncation | Which memories were retrieved in the first place |
| Lifecycle & consolidation | Decay, merge, eviction, deletion propagation | Real-time retrieval-path decisions (this runs as a background process, not inline — see Section 5's sync/async split) |

---

*Continues in Part 2 (Sections 7–11: data model/provenance/lifecycle, data flow, retrieval/ranking/
context-budget policy in detail, API contracts summary, privacy/threat model summary) and Part 3
(Sections 12–16: observability, capacity/cost, alternatives/decision records, milestones, risks).*

---

*Design-process notes — which decisions came from external review vs. original drafting, and why —
are logged in `design/decision_records/` rather than inline here, per this project's own
accountability requirement (Section 12 of the handbook) to record material AI assistance and the
decisions that followed from it.*
