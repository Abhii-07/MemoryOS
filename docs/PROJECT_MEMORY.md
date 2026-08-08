# Project Memory

> Durable knowledge only — NOT a chronological journal (that's `journal/`). High-signal facts a future agent needs to understand and continue this project.

## Project Purpose
MemoryOS = a persistent **conversational memory intelligence system** for AI assistants: memories are written, retrieved, updated, consolidated, and **deleted** per user intent — not a chat log. Deliverable: a research-grade course repo (D1–D8 per handbook) AND a coherent product narrative ("MemoryOS"). Single source of truth: **this repository** (`D:\Abhii\Projects\MemoryOS`, local-only git).

## Architecture (planned; established in D1/D5, not yet implemented)
- **Three-layer memory:** (1) *core memory* store (per-user, embeddings + metadata), (2) *working/retrieval* layer (hybrid re-rank), (3) *consolidation* (long-term summaries, no-kv-loss edit).
- **Retrieval (design choice, Feb-2026):** hybrid BM25 + dense + RRF fusion (optional cross-encoder) — see DECISIONS D-002, verified claims in research.
- **Injection:** per-turn memory filter → prompt; **single-write** enforcement.
- **Stack (DECISION D-002):** Python; naive baseline = TF-IDF + cosine (from old repo `experiments/naive_baseline/`); pytest for tests; pgvector viable in D6 (ANNS via HNSW).
- **Nothing implemented yet** — repo is documentation + plan + research + baseline glue only.

## Core Concepts
- **Memories = retrieved + injected + consolidated.** Retrieval is a search problem; injection is a context-budget problem; consolidation is a summarization/edit problem.
- **R1–R8** (requirements, handbook): each maps to product capability (see `reconstruction/04_first_principles.md`).
- **C1–C8** (constraints) — e.g., tenant isolation, latency budget, memory lifetime.
- **Deliverable cycle (handbook):** D1 problem–design reconstruction; D2 research; D3 naive baseline; D4 full design; D5 Genesis (this repo's `.genesis`); D6 implementation + correctness; D7 journal; D8 transfer docs.
- **Evidence discipline:** `[P: n]` paper, `[A: …]` assumption, `[O]` verified observation — tagging mandatory in deliverables.

## Important Design Decisions
1. **Single source of truth = MemoryOS repo; old & Opencode repos read-only B.</var> (D-001, D-004)
2. **Python** (matches baseline; fastest path) — not TypeScript from old repo plan. (D-002)
3. **Local-only git, no LICENSE file, no remote.** (D-003)
4. **D1 rigor = this repo's reconstruction (done) + old repo's evidence grafted; PDFs regenerate from markdown — never hand-edit.** (D-005)
5. **D2 research preserved verbatim from old repo + `sources_catalog.md`.** (D-006)
6. **D3 naive baseline actually RUN (was never executed); `productive_failure_report.pdf` documents the gap.** (D-007)
7. **D5 Genesis spine adopted from old repo + re-sliced to Python/pytest + invariants ×5.** (D-008)
8. **Product layer exists** (`product/PRD.md`, `design/edge_cases.md`). (D-009)

## Important Constraints
- Old repo READ-ONLY forever (copy/read only). Never write to `D:\Abhii\Opencode` either.
- 10 directory skeleton at repo root (design, experiments, implementation, journal, product, reconstruction, research, tools, transfer, verification) — DON'T remove.
- PDF pipeline requires Python 3.14 path + Chrome at fixed absolute path (see SESSION_STATE Commands).
- No `LICENSE`, no remote; every claim tagged `[P]`/`[A]`/`[O]`.
- Local-only: no credentials, no `.env`, no tokens.

## Security / Privacy Requirements
- Tenant isolation **at DB level** (not just app flter) — test in D6.
- Deletion must propagate to *consolidated/synth memories* (purge memory-of-memories), test explicitly.
- PII guardrail: pre-write sanitize + OSS (race OOD degradation 0.96→0.18 in PIIBench — must defend).
- No cross-tenant reads under any adversary (ASON06 in OWASP LLM threat model — research references it).

## Data Model (planned — not implemented)
- `MemoryRecord`: id, tenant_id, user_hash, created_at, updated_at, mode (episodic/crontextual/semantic), hooks (source messages), validity window (`valid_until` supersession design), flags (pinned, deleted_ts).
- Retrieval indices: TF-IDF (baseline), dense embeddings (future), optional | RRF fused.
- Journal will track schema evolution (Phase 4+ D6).

## API / Interface Contracts (planned)
- `MemoryStore.counter_memories(tenant_id, user_hash)` → list
- `put_memory`, `delete_memory(id)`, `update_memory(id, new_text)` with supersession
- `Retrieve(query, tenant_id, top_k)` → ranked records
- `Inject(context_budget, working_mem)` → budgeted string
- Tests: pytest classes mirror these (Phase 4). Do NOT change public signatures without DECISIONS entry.

## Testing Strategy
- Phase 4+: pytest `tests/` mirroring the modules; `demo commands` per D5 milestone (e.g., `pytest -m budget`, `pytest -m deletion`), freeze boundaries per milestone.
- D6 correctness: tenant isolation test, deletion propagation test, latency P95 < 150ms test, PII guardrail test.
- PDF artifacts: after every PDF regeneration run `tools/verify_pdf.ps1` or equivalent (headers/footer, page count).

## Research Conclusions (D-heads, citations pending R1 in Phase 6)
- Naive TF-IDF + cosine: one-signal, weak on long conversations; `baseline_results.csv` will quantify gap vs. hybrid.
- Hybrid dense+sparse+RRF is the *settled* community pattern (Mem0, Zep, "40% dense fails" claim → verify).
- PIIBench shows embedding OOD instability (0.96→0.18) — motivation for health-check guardrail.
- `valid_until` supersession pattern common (data_merge design) — adopt for memory updates.
- TOKEN BUDGETS: 4-zone model Appendix: working memory / conversation / longterm storage → caps at injection.

## Known Risks
- `imp.js`-style: losing research claims verification → gate R1 in Phase 1 mitigates.
- **PDF pipeline breaking** if Chrome/paths change → verified once, then regen at every deliverable.
- Baseline never run → results may expose data-gen bugs; protocol document required.
- Scope creep; deferred: cross-encoder, ANNS tuning (pgvector), product UI, benchmarks > 10k docs.

## Known Edge Cases (seed list — static in `design/edge_cases.md`)
Supersisted preference (10x); per-slot contradiction; consent change (legal/data subject); deletion propagating to consolidated artifacts; cross-client adversarial similarity; MemoryTrap-class injection; PIIBench OOD; cold start; empty vocab; zone overflow; concurrent writes; error-reinforcement (explicit self-correction); no-relevant-memory (graceful "don't know").

## Naming Conventions
- Modules: `memory_os` package (underscore), testss `tests/test_<module>.py`.
- Docs: `[P:n]`/`[A:…]`/`[O]` tags; journal `journal/YYYY-MM-DD-<topic>.md`; decisions `D-001…` sequential.
- Commit types: `feat/` `docs/` `chore()` conventional prefixes (see PLAN phase names).

## Repository Conventions
- One commit per phase (status: [ ] NOT STARTED / [- ] IN PROGRESS / [x] COMPLETE / [!] BLOCKED in PLAN.md).
- `git status` clean baseline; nothing committed that is unverified (no placeholders).
- Paths: absolute in scripts; scratch in `C:\Users\CR7\AppData\Local\Temp\opencode`.

## Things That Must NOT Be Changed
- Old repo read-only policy (never edited).
- No LICENSE / no remote; git stays local.
- 10-dir skeleton at root.
- Evidence tagging discipline.
- Invariants list ((Session State / Invariants section) — any relaxation needs a DECISIONS entry.

## Things That Are Intentionally Deferred
- Remote git, GitHub Actions, official license.
- Actual implementation + error handling until D5 (design) + D6 (implementation) — currently only baseline script in old repo, NOT ported yet.
- Benchmark corpus downloads > 50MB; OSS models (choose offline-local path later).
- Product packaging (pip/npm), UI, deployment.