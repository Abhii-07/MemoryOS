# ADR-004: Deterministic Tenant Pre-Filter, Amending Namespace Isolation

**Status:** accepted (amends a prior decision)
**Date:** August 2026

## Context

Week 2 originally adopted namespace-based tenant isolation as sufficient for this system's
expected scale. Week 4's dedicated privacy/safety research week found this to be necessary but not
sufficient on its own.

## Decision Drivers

- Week 4's research: vector similarity search is inherently probabilistic; multi-tenancy requires
  a deterministic boundary. Those two properties don't mix safely if tenant scoping is folded into
  similarity scoring rather than applied as a hard filter.
- OWASP's LLM Top 10 (2025 edition) covers cross-tenant collision in hybrid/reranked search under
  LLM-08 (Vector & Embedding Weakness) — a documented risk pattern, not a hypothetical one.
  *(Corrected 2026-08-08 per research pass R3: the original draft cited a nonexistent "OWASP 2026
  ASI06" entry; no such slot exists — see `research/passes/2026-08-08-R3-product-positioning.md`.)*
- This system's architectural priorities (Part 1, Section 3) rank privacy and tenant isolation as
  the single highest priority — above recall, above latency, above cost.

## Options Considered

1. **Namespace isolation only** (the original Week 2 decision). Rejected as insufficient once
   Week 4's research was available — retained namespace partitioning as one layer, but not the
   only one.
2. **Deterministic tenant pre-filter, applied before similarity scoring runs.** Chosen.
3. **Post-hoc filtering** (retrieve broadly, then filter by tenant before returning results).
   Rejected — a cross-tenant candidate would still be scored and potentially logged/traced before
   being filtered, which doesn't fully close the leakage risk even if it's filtered from the final
   response.

## Decision

Option 2. `system_design.pdf` Section 9 specifies the tenant filter as the first operation in the
retrieval pipeline — a cross-tenant candidate is never scored, not just never returned.

## Consequences and Trade-offs

This is a refinement of an already-adopted decision, not a new one — low implementation cost, but
it must be written explicitly into the retrieval implementation rather than assumed to follow
automatically from namespacing, which was the exact gap Week 4 found.

A follow-up risk surfaced during Deliverable 4 drafting (not from the original research): whichever
vector index gets chosen needs to support efficient pre-filtered search — filtering before scoring
can be expensive under some ANN index structures. This wasn't checked against pgvector specifically
(ADR-003) and is carried forward as an open item.

## Validation Plan

Deliverable 6's acceptance check ("no cross-tenant memory returned under adversarial queries")
should specifically include queries deliberately crafted to be semantically close to another
tenant's content, per `threat_model.md`, Threat 1.

## Revisit Conditions

If pre-filtered search proves inefficient at scale under pgvector's HNSW implementation, this may
require either an index restructuring or physical per-tenant partitioning (the upgrade path
already named in Week 4's original research as the stronger, costlier alternative to namespace
isolation).
