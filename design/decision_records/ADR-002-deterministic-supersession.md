# ADR-002: Deterministic Supersession Over LLM-Judged Freshness

**Status:** accepted
**Date:** August 2026

## Context

Deliverable 1's Open Question 3 asked how the system should resolve two memories that describe
the same thing differently — e.g. a preference that changed. The obvious first-instinct answer is
letting the model judge, from context, which of two conflicting facts is more current.

## Decision Drivers

- Deliverable 3's naive baseline measured a 33% contradiction-failure rate using similarity-only
  ranking with no supersession mechanism at all — the problem is real, not hypothetical.
- Week 3's research found a 2026 benchmark study showed every evaluated memory system, including
  strong long-context baselines, performed far below expectation on a fact-consolidation task —
  even when told explicitly that higher serial numbers meant newer facts.
- Production systems in this space (Zep/Graphiti) use explicit validity-window fields rather than
  relying on in-context freshness judgment.

## Options Considered

1. **LLM-judged freshness at retrieval time.** Simple to implement, no schema changes needed.
   Rejected — directly contradicted by Week 3's benchmark evidence.
2. **Deterministic `valid_until` supersession**, set by the Admission component when a new memory
   is linked to an existing one via entity/slot matching. Chosen.
3. **Timestamp-only recency weighting** (no explicit supersession, just favor newer records in
   ranking). Considered as a lighter-weight alternative; rejected because it doesn't actually
   resolve the conflict, it just biases toward one side of it — a stale record could still surface
   for a query where the new record's wording doesn't match well lexically.

## Decision

Option 2. Every memory record carries `valid_from` and `valid_until` (`data_model.md`). When
Admission classifies a new memory as `UPDATE` against an existing entity/slot, the prior record's
`valid_until` is set explicitly rather than left to ranking-time inference.

## Consequences and Trade-offs

This requires entity/slot-linking as a working capability at admission time — matching a new
memory to the existing record it supersedes. That capability has no detailed design of its own yet
(flagged as an open risk in `system_design.pdf` Section 16) and is a real dependency this decision
introduces, not a free upgrade.

To avoid a new failure mode — a false-positive supersession silently destroying access to a memory
that wasn't actually stale — low-confidence supersessions keep both records retrievable and marked
as conflicting rather than closing one out (Week 1's self-review fallback).

## Validation Plan

Deliverable 6's acceptance check requires "stale preferences never override current ones," tested
against Deliverable 3's exact failing case (`c1-direct-contradiction`) plus new cases specifically
targeting the entity/slot-linking capability's accuracy.

## Revisit Conditions

If entity/slot-linking proves unreliable at scale (high false-positive or false-negative
supersession rates), this decision should be revisited — the low-confidence fallback is a partial
mitigation, not a complete one.
