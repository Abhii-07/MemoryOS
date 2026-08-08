# Sprint Plan

**MemoryOS — Deliverable 4 (created 2026-08-08 during the MemoryOS merge)**

This is the missing handbook artifact from the original D4 (the old repo's
design set had no `sprint_plan.md`). It maps the design's build sequence
(`system_design_part3.md` §15, M1–M7) onto the Genesis milestones already
sliced in `.genesis/PLAN.md` (M1–M3), so the two documents agree. Every row
carries: the outcome, demo command, freeze boundary, and the edge-case ledger
entries (`edge_cases.md`, EC-01…EC-18) it verifies.

> Slicing rule (from `.genesis/PLAN.md`): a milestone must have (a) one clear
> outcome, (b) an exact **demo command**, (c) a freeze boundary. Anything not
> expressible as a command is too vague — split it.

## Design-to-genesis mapping (D4 §15 → Genesis)

| D4 build step (system_design_part3 §15) | Genesis milestone (execution slice) | Notes |
|---|---|---|
| M1 — Storage + Admission | **G-M1 + G-M3** | G-M1 owns the schema/tenant piece; admission logic is G-M3 |
| M2 — Retrieval + Ranking | **G-M2** (supersession verified jointly with G-M3) | core memory loop; closes D3 failing cases |
| M3 — Context construction | **G-M3** (context/) | zone budgets; tool-output zone |
| M4 — Lifecycle + deletion propagation | **post-G-M3 follow-up (G-M4+)** | deletion propagation is design risk #1 (ADR-005); own slice, not bundled |
| M5 — Privacy hardening | **G-M3 (PII guardrail) + security suite in G-M5** | invariants #4/#5 |
| M6 — Observability | **G-M5 (OTEL spans)** | deferred; no monitoring on critical path |
| M7 — Full verification vs D3 baseline | **Final acceptance run** | compares against `experiments/naive_baseline/` |

## Environment prerequisites (before G-M1 starts)

1. **PostgreSQL 17+ installed locally** (Windows x64) with the **pgvector**
   extension (prod-consistent stack — no SQLite branch anywhere).
2. Local database `memoryos` created; service start recorded in
   `docs/SESSION_STATE.md` (Commands).
3. `.venv` extended with `psycopg`/`sqlalchemy` (+ `pgvector` python client).
   Embeddings resolved via the deterministic local embedder (ADR-007).

## G-M1 — Relational Schema & Tenant Isolation

- **Outcome:** the `memories` table (single-table schema per `data_model.md`,
  episodic/semantic as a `memory_type` column per the harmonization note)
  migrates on Postgres 17 + pgvector; tenant filtering is enforced at every
  query; `valid_until` present and nullable; hard deletion purges rows.
- **Files / freeze boundary:** `src/memory_os/db/**`, `tests/test_db.py`
- **Demo command:** `pytest tests/test_db.py -q`
- **Success criteria:** migration clean; `SELECT` for tenant A never returns
  tenant B rows (deterministic pre-filter); DELETE physically removes rows;
  `valid_until` nullable until superseded; HNSW indexes created per
  `data_model.md`.
- **Edge cases exercised:** EC-01 (supersession storage), EC-03 (consent purge
  → empty after delete), EC-05 (cross-tenant adversarial similarity), EC-11
  (concurrent writes serialize per tenant), EC-18 (no torn reads).

## G-M2 — Hybrid Retrieval & RRF Fusion

- **Outcome:** tenant-prefiltered BM25 + dense retrieval fused by RRF
  (`k=60`, per research pass R2) with a relevance floor producing the
  first-class `no_relevant_memory` result; deterministic (no LLM on the
  request path); p95 well under the 150 ms invariant (design target 100 ms).
- **Files / freeze boundary:** `src/memory_os/retrieval/**`,
  `src/memory_os/embeddings/**`, `tests/test_retrieval.py`
- **Demo command:** `pytest tests/test_retrieval.py -q`
- **Success criteria:** retrieval from `data_model.md`'s `dense_embedding`
  + `sparse_terms` columns; empty store returns empty gracefully; relevance
  floor drops below-threshold candidates; D3's exact failing cases (stale
  outranks current; false-positive relevance) pass against this
  implementation.
- **Edge cases exercised:** EC-08 (cold start), EC-09 (stopword query), EC-13
  (empty relevance → "I don't know"), EC-15 (latency ceiling), EC-16 (exact
  slot values), EC-01 (superseded excluded from top rank until superset test
  moves to G-M3).

## G-M3 — Admission Control & Context Construction

- **Outcome:** each turn classified ADD/UPDATE/DELETE/NOOP (entity/slot
  linking as the load-bearing prerequisite flagged in part3 §16 — has its own
  ADR before this slice starts); supersession via `valid_until`
  deterministically; per-zone budgeted context never overshoots.
- **Files / freeze boundary:** `src/memory_os/admission/**`,
  `src/memory_os/context/**`, `tests/test_admission.py`, `tests/test_context.py`
- **Demo command:** `pytest tests/test_admission.py -q`
  (and `pytest tests/test_context.py -q`)
- **Success criteria:** utterances classified; conflicts superseded
  deterministically; budget ceilings never exceeded under the long-conversation
  stress case; PII pre/post guardrail wired (invariant #5).
- **Edge cases exercised:** EC-02 (per-slot contradiction), EC-04 (deletion
  propagation — schema + lineage present even though hard-verify lands in G-M4),
  EC-06 (no memory-as-instruction: MemoryTrap class), EC-07 (PII 100% → 0
  leak), EC-09 (stopword → NOOP-shaped path), EC-10 (zone overflow), EC-12
  (error reinforcement loop), EC-14 (storage growth bound), EC-17 (neutral
  utterance → NOOP).

## Post-G-M3 follow-up (new slices, added when reached)

- **G-M4 — Lifecycle + Deletion Propagation (no lineage guarantees until
  here):** four-lever consolidation, `consolidation_lineage` walks, E-03/04
  full enforcement, `202 Accepted` semantics per `api_contracts.md`.
- **G-M5 — Observability & security hardening:** OTEL spans with redaction
  (Threat 5), adversarial eval replay of MemoryGraft/MINJA tests (Threat 2),
  audit config-as-code check.

## Acceptance mapping (R1..R8 → milestones)

| Requirement | Verified in |
|---|---|
| R3 (isolation, deletion) | G-M1, G-M3, G-M4 |
| R1 (admission) | G-M3 |
| R4 (hybrid retrieval, conflict) | G-M2, G-M3 |
| R5 (token budget) | G-M3 |
| R6 (lifecycle) | G-M3 (supersession part) → G-M4 |
| R7 (observability) | G-M5 |
| R8 (reproducible eval) | G-M2/G-M3 test surfaces vs D3 baseline |

## Risk watch (carried from part3 §16)

1. Deletion propagation (EC-03/04) — resolved only at G-M4; design makes it
   implementable, no earlier milestone should claim it done.
2. Entity/slot-linking — needs its own ADR before G-M3.
3. Embeddings — resolved by ADR-007 (local embedder); reopens the
   paraphrase-risk if the deployment env has no model download.
4. Pre-filtered HNSW under pgvector — G-M2 must include an explicit check.

*End of sprint plan (D4).*