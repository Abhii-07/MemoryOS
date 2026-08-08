# PLAN — MemoryOS (Conversational-Memory-Intelligence-System)

The machine-parseable implementation plan. Mirrors the milestone table in `DONE.html` (DONE.html is the
human/visual view; this is the one loops read). Sliced so each milestone ships in one L1 BUILD pass.

> Slicing rule: a milestone must have (a) a single clear outcome, (b) an exact **demo command** that
> proves it, and (c) a freeze boundary of files it may touch. If you can't write the demo command,
> the milestone is too vague — split it.
>
> **Stack note (D-002).** Implementation language is Python; demo commands are `pytest ...`
> (re-sliced from the TypeScript/`npm test` versions during the 2026-08-08 repo merge).

---

## Brainstorm (G0.5 — fill before slicing milestones)

> Three fundamentally different approaches to the cognitive job. Pick one. Record the rationale.
> This is the cheapest design decision — you haven't written a line of code yet.

### Approach A — Graph-Based Entity-Relationship Memory
Store memories as a property graph where nodes are entities/concepts and edges are relationships, utilizing bitemporal timestamps for edge recency.
- Strengths: Excellent for tracking complex relationships, multi-hop reasoning, and semantic entity linking.
- Weaknesses: High implementation complexity, slow queries at scale, difficult schema evolution.

### Approach B — Relational Memory with Deterministic Supersession (pgvector)
Store episodic and semantic memories in Postgres using pgvector for hybrid retrieval, resolving conflicts deterministically using explicit timestamps and a `valid_until` column rather than LLM context comparison.
- Strengths: Transactional consistency, simple multi-tenant namespace isolation, fast indexing, robust, and simple to implement.
- Weaknesses: No native graph-based transitive relationship traversal.

### Approach C — File-Based Volatile Memory System
- Store memories in structured JSON files per tenant and load/save segments dynamically into the system context on each turn.
- Strengths: Minimal infrastructure dependencies, easy local prototyping, simple backup/restore.
- Weaknesses: High latency/cost at scale, file write lock contention risk, poor scaling for large memory histories.

### Chosen: Approach B — Relational Memory with Deterministic Supersession (pgvector)
- Rationale: It leverages standard, production-ready relational architecture + pgvector for tenant isolation, while solving the recency/freshness tracking problem deterministically outside of the LLM context using explicit timestamps, which balances performance, correctness, and complexity.

---

## Milestones

### M1 — Relational Schema & Tenant Isolation
- **Outcome:** The `memories` table (single storage table per `design/data_model.md`; episodic/semantic abstracted as a `memory_type` column) initialized in SQLAlchemy on Postgres+pgvector with enforced tenant filtering. *(Harmonized 2026-08-08 with D4: the design defines ONE `memories` table — no separate episodic/semantic tables; see `design/sprint_plan.md`.)*
- **Phase (swe-master):** Phase 1: System Architecture Design & Phase 3: Backend Engineering
- **Files / freeze boundary:** `src/memory_os/db/**`, `tests/test_db.py`
- **Demo command:** `pytest tests/test_db.py -q`
- **Success criteria:** Tables migrate cleanly on the local Postgres 17 + pgvector instance; queries for tenant A never return tenant B's rows; DELETE actions physically purge rows from the store; `valid_until` column present and nullable; HNSW index (`dense_embedding vector(384)` per ADR-007) created.
- **Loops:** L1, L4
- **Skills:** canon + tdd + data-systems-engineering, modular-architecture
- **Token budget:** 50000

### M2 — Hybrid Retrieval & RRF Fusion
- **Outcome:** Retrieval engine fusing BM25 sparse results (via `sparse_terms`) with vector dense results (via `dense_embedding` from the ADR-007 local embedder) using Reciprocal Rank Fusion (RRF, k=60); deterministic latency well under invariant.
- **Phase (swe-master):** Phase 6: Memory Architecture
- **Files:** `src/memory_os/retrieval/**`; `src/memory_os/embeddings/**`; `tests/test_retrieval.py`
- **Skills:** canon + tdd + data-systems-engineering
- **Demo command:** `pytest tests/test_retrieval.py -q`
- **Success criteria:** outputs citation-attached ranked candidates; retrieval is deterministic (no LLM) and runs <150ms; empty store returns empty gracefully.
- **Loops:** L1, L3 (research), L4

### M3 — Admission Control & Context Construction
- **Outcome:** Fact extractor classifying updates as ADD/UPDATE/DELETE/NOOP, marking conflicts superseded via `valid_until`, and packing results into zone-budgeted prompts.
- **Files:** `src/memory_os/admission/**`, `src/memory_os/context/**`; `tests/test_admission.py`, `tests/test_context.py`
- **Demo command:** `pytest tests/test_admission.py -q`
- **Success criteria:** utterances parsed into operations; conflicting facts marked superseded; prompt construction respects guaranteed zone budgets (no overshoot).
- **Loops:** L1, L2, L4
- **Skills:** canon + tdd + llmops-ai-agents, production-readiness

---

## Progress

- _(none yet — first loop fills this)_