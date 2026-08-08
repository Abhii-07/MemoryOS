# ADR-001: AI-Assisted Review Process and Recorded Decisions

**Status:** accepted
**Date:** August 2026

## Context

Deliverable 4's `system_design.pdf` was drafted with AI assistance and reviewed by external LLM
instances at two points during drafting. The handbook's Section 12 ("Working With AI Without
Outsourcing Judgment") requires recording material AI assistance and the decisions that resulted
from it, as part of the accountability rule: the student is responsible for every submitted claim
regardless of which tool produced the first draft. This ADR is that record, moved here from an
earlier inline "change notes" section per a review's presentation feedback (see Decision below).

## Decision Drivers

- The handbook's explicit requirement to record material AI assistance and resulting decisions.
- A separate concern, raised by a second external review, that a change-log block reads oddly
  embedded inside a final architecture document.
- The project's established practice (since Deliverable 2's self-administered challenge notes) of
  treating external feedback as input to evaluate, not instructions to follow automatically.

## Options Considered

1. **Keep an inline "change notes" section in `system_design.pdf` itself.** Simple, but a second
   external review correctly noted this reads as revision history embedded in a final report,
   which most technical documents don't do.
2. **Delete the record entirely once revisions were applied.** Satisfies the presentation
   critique, but violates the handbook's explicit accountability requirement — a correct
   presentation fix that creates a compliance gap.
3. **Move the record into `decision_records/` as its own ADR.** Satisfies both: the design
   document stays clean, and the accountability trail is preserved in the location the handbook's
   own required-artifacts list already designates for exactly this kind of record.

## Decision

Option 3. The record of what was reviewed, what was accepted, what was rejected, and why lives
here, not inline in `system_design.pdf`.

### What was reviewed and what happened, specifically

**First review** (of `system_design.pdf` Sections 1-6, first draft): flagged seven missing
architectural-documentation items — an explicit quality-attribute priority table, target values
for success metrics, an assumptions list, a recoverable/non-recoverable failure split, an explicit
orchestration layer and sync/async description, per-component interfaces, and a system boundary
paragraph. All seven were assessed as genuine gaps (not stylistic preference) and incorporated.

**Second review** (of the revised Sections 1-6): seven more points. Five were accepted directly
(justify target numbers, redraw the orchestration diagram as a branch, soften the ordered-turns
assumption into an explicit MVP scope decision, add a provenance-traceability invariant, and the
presentation critique that produced this ADR). One — replacing "orchestrated" with "coordinated" —
was applied but explicitly flagged as not a meaningful change, included only because it cost
nothing. The suggestion to delete the AI-assistance record entirely was **not** followed as
proposed; it was reframed into this ADR instead, per the reasoning in Decision above.

**Third review** (of the completed `system_design.pdf`, all sections): raised nine points, framed
as production-infrastructure gaps (deployment architecture, Kubernetes, Redis caching, sharding,
message-broker choice, invented capacity numbers). Three were accepted as legitimate and
low-cost (a concrete ranking-score formula, an explicit embedding-service failure fallback, and
clarifying the background worker as a scheduled process without naming unneeded technology). Six
were rejected, with reasons recorded at the time: the handbook's Section 2.1 explicitly permits
simplifying the production stack given documented reasons for omissions; a second, earlier review
had already praised this document for staying at the architectural level and explicitly advised
against adding infrastructure technologies without genuine need; and every number and technology
choice in this design traces to a specific research week or Deliverable 3 finding — the rejected
suggestions traced to nothing, which would have broken that discipline.

## Consequences and Trade-offs

Keeping this record separate from the main design document costs a reader one extra file to
understand *why* certain sections look the way they do, but keeps `system_design.pdf` itself
reading as a finished specification rather than a running commentary on its own revision history.

## Validation Plan

N/A — this is a process record, not a technical claim requiring empirical validation.

## Revisit Conditions

None anticipated. This ADR is a historical record of the drafting process, not a decision that
gets revisited as the system evolves.
