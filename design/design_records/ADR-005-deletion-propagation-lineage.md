# ADR-005: Deletion Propagation via Consolidation Lineage

**Status:** accepted as requirement; mechanism prototyped, not proven
**Date:** August 2026

## Context

Week 1's four-lever lifecycle framework includes a Merge operation that creates consolidated
records from multiple raw memories. Week 4's research found that deleting a raw memory without
also addressing derived artifacts built from it — a failure mode researchers call "backflow" —
means deletion is, in one survey's words, "only a retrieval edit," not a real deletion.

## Decision Drivers

- Deliverable 6's acceptance check already requires deletion to remove a memory "from both source
  storage and retrieval paths" — backflow directly threatens this requirement's real satisfaction,
  not just its letter.
- This system's architectural priorities rank privacy above cost and above implementation
  simplicity — accepting a harder engineering problem here is consistent with that stated
  priority, not a violation of it.

## Options Considered

1. **No lineage tracking — accept backflow as an unaddressed limitation.** Rejected — directly
   conflicts with the deletion guarantee this project has committed to since Deliverable 1's
   privacy constraint.
2. **Lineage tracking via a `consolidation_lineage` field, with cascading deletion.** Chosen.
3. **Avoid consolidation/merging entirely, to sidestep the problem.** Rejected — this would mean
   giving up Week 1's four-lever lifecycle framework's Merge operation, which exists to bound
   storage growth (system_design.pdf, Section 13). Trading a privacy guarantee problem for a cost
   problem doesn't match this system's stated priority ordering (privacy above cost).

## Decision

Option 2. `data_model.md` specifies `consolidation_lineage` as a GIN-indexed UUID array. The
`DELETE /memory/{id}` endpoint (`api_contracts.md`) walks this graph and cascades re-consolidation
or eviction to every derived record, returning an explicit in-progress status for large chains
rather than a false-positive immediate success.

## Consequences and Trade-offs

This is named consistently, across every document in this deliverable, as the single biggest
unresolved risk in the whole system — not softened here either. The schema makes the requirement
implementable; nothing in this design makes the lineage-walk mechanism's correctness guaranteed
under real consolidation patterns (e.g. a record consolidated from sources that were themselves
already consolidated — multi-level lineage — is a harder case than single-level lineage, and isn't
separately verified by anything in this design yet).

## Validation Plan

Deliverable 6 must include a merge-then-delete test case: create a consolidated record from
multiple sources, delete one source, verify the consolidated record's content no longer reflects
the deleted source. A test that only deletes never-consolidated records would pass without
exercising this decision at all — this is stated explicitly in `threat_model.md`, Threat 4, and
repeated here because it's the single most important test case this project needs to get right.

## Revisit Conditions

If Deliverable 6's testing finds the lineage-walk mechanism doesn't reliably handle multi-level
consolidation (a record derived from already-consolidated records), this decision needs revisiting
— possibly toward a simpler policy (e.g. capping consolidation depth to keep lineage graphs
shallow) rather than a more complex lineage-tracking mechanism.
