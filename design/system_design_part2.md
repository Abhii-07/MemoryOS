# System Design — Conversational Memory Intelligence System

**Deliverable 4 · Draft, Part 2 of 3 (Sections 7–11)**
Abhijeet Hiwale · August 2026

---

## 7. Data Model, Provenance, and Lifecycle

**Core record — every stored memory carries these fields:**

| Field | Purpose | Traces to |
|---|---|---|
| `id` | Unique identifier | — |
| `tenant_id` | Hard partition key for isolation | Week 4, Section 4's cross-tenant invariant |
| `text` | The memory content itself | — |
| `dense_embedding`, `sparse_terms` | Two representations for hybrid retrieval | Week 2's BM25+dense+RRF decision |
| `provenance` | One of: `user_stated`, `assistant_generated`, `tool_derived`, `retrieved_document` | Week 4; now an enforced invariant (Part 1, Section 4) |
| `admission_op` | The operation that created/last touched this record: ADD, UPDATE, DELETE, NOOP | Week 1 |
| `valid_from`, `valid_until` | Explicit validity window; `valid_until` is null until superseded | Week 1's deterministic supersession decision |
| `confidence` | Admission-time confidence score, used for the low-confidence supersession fallback | Week 1 self-review |
| `pii_scan_result` | Pass/flag/redacted, plus which detector version ran | Week 4's PII detection decision |
| `status` | `active`, `decayed`, `evicted`, `deleted` | Week 1's four-lever consolidation |
| `consolidation_lineage` | List of source record IDs this record was derived from, if any | Week 4's deletion-propagation ("backflow") requirement |

**Why `consolidation_lineage` exists and what it actually has to do:** this is the field that makes
deletion propagation possible at all. When the Lifecycle component merges or summarizes several raw
memories into one consolidated record (Week 1's "merge" lever), the consolidated record's lineage
field points back to every source it was built from. A deletion request against any source record
triggers a lookup through lineage: every derived record that included the deleted source gets
re-consolidated or evicted, not just the source itself. This is still the least proven part of the
whole design — Week 4 flagged this as adopted-as-a-requirement with the actual mechanism only
prototyped, and that status hasn't changed here. This data model makes the requirement
*implementable*; it doesn't yet make it *guaranteed correct* — that's Deliverable 6's job to verify.

**Lifecycle, tied to the four-lever framework (Week 1):**
- **Importance** — decided at admission, informs whether a memory is a decay candidate at all.
- **Merge** — background process combines related raw memories into a consolidated record, writing
  `consolidation_lineage`.
- **Decay** — reduces a memory's rank/accessibility over time (soft); does not delete it. Now also
  triggered by low provenance/unverified status expiring by default (Week 4).
- **Eviction** — the actual removal path, either from decay reaching a floor or from an explicit
  deletion request; the only lever that touches `consolidation_lineage` propagation.

## 8. Data Flows

Part 1's diagram simplified the online path as one linear chain. That's accurate for a single
query, but it conflates two distinct triggers that don't happen at the same time or on the same
event:

**Write flow** (triggered by a new conversation turn):
```
Conversation turn -> Admission (classify + provenance tag + PII scan) -> Storage
```

**Read flow** (triggered by a query needing memory context):
```
Query -> Retrieval (hybrid search + tenant pre-filter + relevance floor)
       -> Ranking (supersession check + multi-signal scoring)
       -> Context Builder (per-zone token budgeting)
       -> injected context returned to caller
```

**Background flow** (scheduled, not triggered by any single request):
```
Lifecycle Worker: scans Storage on a schedule
    -> applies decay / merge / eviction
    -> on any deletion, walks consolidation_lineage and propagates
```

A single conversational exchange typically triggers both a write (the user's new turn gets
admitted) and a read (the assistant needs context to respond) — but they are independent
operations against the same Storage component, not steps in one pipeline. This matters
operationally: a slow admission shouldn't block a query's retrieval latency budget, and the two
should be allowed to run concurrently rather than serialized.

## 9. Retrieval, Ranking, and Context-Budget Policy

**Retrieval** (Week 2's adopted mechanism, applied in full):
1. Tenant pre-filter applied first and deterministically — not folded into similarity scoring
   (Week 4's amendment to Week 2's namespace isolation; this order matters, since filtering after
   ranking would mean a cross-tenant candidate was scored at all, which is the exact risk Week 4
   flagged).
2. BM25 and dense similarity run in parallel over the tenant-filtered set.
3. Reciprocal Rank Fusion combines the two rankings.
4. A configurable relevance floor is applied to the fused result — anything below it is dropped,
   producing the explicit "nothing relevant" output when everything falls below threshold (closes
   Deliverable 3's Failure 3). No LLM call anywhere in this path (Week 2).

**Ranking & conflict resolution** (Week 1's adopted mechanism):
1. For each retrieved candidate, check `valid_until`. If a candidate has been superseded (another
   record with the same entity/slot has a later `valid_from`), it's excluded from the top position
   — unless supersession confidence was low at write time, in which case both records remain
   retrievable and are marked as conflicting rather than one being silently hidden (Week 1
   self-review fallback).
2. Final ordering combines fused retrieval rank, recency, and a provenance-weighted trust factor
   (user-stated ranks above tool-derived, all else equal) — this is the multi-signal ranking
   Deliverable 1 required and the naive baseline never had.

**Context construction** (Week 2's adopted mechanism):
Per-zone token budgets, each with a hard ceiling: system prompt, retrieved memory, conversation
history, tool-output (its own zone, per Week 2 — not folded into history), current input, output
reserve. Retrieved memories are injected in final-ranked order until their zone's budget is
exhausted; nothing overflows into another zone's allocation. The context-rot finding (Week 2)
is why this system never treats a larger context window as a substitute for this budgeting
discipline, regardless of the underlying model's window size.

## 10. API Contracts (Summary)

Full request/response schemas are specified in `api_contracts.md`. At a high level, three
operations, matching the two online flows plus explicit deletion:

- **`POST /memory/turns`** — admits a conversation turn. Returns the admission operation applied
  (ADD/UPDATE/DELETE/NOOP) and the record ID.
- **`POST /memory/query`** — the read flow. Takes a query and a token budget, returns either an
  injected context block or an explicit `no_relevant_memory` result (not an error — a valid,
  expected outcome per Deliverable 3's Failure 3 and Part 1's invariants).
- **`DELETE /memory/{id}`** — triggers eviction and lineage-based propagation. Returns once
  propagation through the lineage graph completes, or an explicit status indicating propagation is
  still in progress for large lineage chains, rather than a false-positive immediate success.

**Error semantics principle:** "nothing relevant found" and "tenant isolation prevented a match"
are not represented as errors anywhere in this API — they're valid, expected outcomes with their
own response shape. Only genuine failures (storage unavailable, malformed input) are errors. This
distinction exists specifically because Deliverable 3 showed what happens when a system has no way
to express "nothing relevant" as anything other than returning its best (wrong) guess.

## 11. Privacy, Authorization, Isolation, and Threat Model (Summary)

Full threat model is specified in `threat_model.md`. Summary of what this design commits to,
directly from Week 4's research:

- **Tenant isolation** is a deterministic pre-filter (Section 9), not a similarity-adjacent
  guarantee — this is a non-recoverable-class protection (Part 1, Section 4).
- **PII handling** applies regex + NER at admission (pre-guardrail) and again at retrieval/injection
  (post-guardrail), with an explicit minimum precision/recall bar validated against this project's
  own conversational data before shipping — not trusted on a published benchmark number alone
  (Week 4's PIIBench finding).
- **Provenance** is used, not just stored: it gates ranking trust weighting (Section 9) and
  decay/expiry eligibility (Section 7), closing the "unused field" risk flagged in Week 4's
  self-review.
- **Deletion propagation** through `consolidation_lineage` is this design's least-proven guarantee,
  named honestly as such rather than assumed solved.
- Authorization itself (verifying a tenant ID is legitimate) is explicitly out of this system's
  scope per Part 1's assumptions — this design enforces isolation given a trusted tenant ID, it
  does not authenticate that ID.

---

*Continues in Part 3 (Sections 12–16: observability, capacity/cost/recovery, alternatives and
decision records, milestones and acceptance tests, risks and unresolved questions).*
