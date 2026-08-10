# Session State

> Canonical, machine-readable/human-readable state of this project. **The repository is the source of truth, not chat context.** If any file contradicts this one, SESSION_STATE.md wins (and the contradiction must be fixed).

## Last Updated
- Date/time: 2026-08-09 (late session, post-G-M6)
- Current git branch: `main`
- Current commit SHA: `caac791` (`feat(g-m6): adversarial replay of memory poisoning + D3 acceptance gate`)

## Project
- Project name: **MemoryOS** (course deliverable: *Conversational Memory Intelligence System*)
- Overall objective: Build, from first principles, a production-grade conversational-memory system — persistent, retrievable, deletable memory for an AI assistant — as a research-grade course repo (D1–D8) AND a coherent product ("MemoryOS").
- Current milestone: **all design milestones implemented (G-M1…G-M6 committed; M1–M7 from `sprint_plan.md` have passing demo commands)**.

## Overall Plan (Genesis gates)
| Gate | Outcome | Commit | Status |
|---|---|---|---|
| G-M1 | Relational schema + tenant isolation (Postgres 17 + pgvector) | `d2d8e02` | [x] 12 tests |
| G-M2 | Hybrid retrieval + RRF + EC-15 latency | `bff78f9` | [x] 14+1 tests |
| G-M3 | Deterministic admission + context gates | `92c9490` | [x] 27 tests |
| G-M4 | Lifecycle four levers + deletion propagation | `8ab43f1` | [x] 16 tests |
| G-M5 | Observability spans + provenance-weighted ranking | `161c6ca` | [x] 18 tests |
| G-M6 | Adversarial replay + D3 acceptance run | `caac791` | [x] 9 tests + bench PASS |
| — | Full suite / acceptance | — | **97 passed; `bench.acceptance` PASS; DB 0/0** |

## Decisions (current rulings, full log in `docs/DECISIONS.md`)
- D-001..D-016 from the merge phase (single source of truth; local-only git; old repo read-only; evidence tags; Postgres+pgvector only, no SQLite).
- ADR-002 deterministic supersession (`valid_until` window).
- ADR-004 deterministic tenant pre-filter (isolation never by similarity).
- ADR-005 deletion propagation via `consolidation_lineage` (G-M4; depth cap 4; 202-jobs beyond max_sync_derived=100).
- ADR-007 local deterministic embedder (all-MiniLM-L6-v2, no network at runtime).
- ADR-008 admission is deterministic classification (ADD/UPDATE/DELETE/NOOP, slot-key supersession).
- Provenance-weighted ranking (user_stated 1.0 > assistant_generated 0.85 > tool_derived 0.6 > retrieved_document 0.5) — Threat-2 mitigation.
- Observability: in-process typed spans, content only in events, collector-level redaction + hashed attributes; audit gate = config-as-code (`audit/policy.toml`).

## Constraints (operational)
1. Always `.venv\Scripts\python.exe` (3.14) + `$env:PYTHONPATH="src"`, cwd = `MemoryOS-App\`.
2. App code is consolidated in `MemoryOS-App\` (`src/`, `tests/`, `bench/`, `audit/`, `pytest.ini`,
   `requirements.txt`, `.venv/`, `.hf-cache/`) — fully self-contained; the repo root holds course
   deliverables (`design/`, `docs/`, `experiments/`, `research/`, `journal/`, `.genesis/`, …) and
   `bench.acceptance` reaches the D3 dataset via the repo-root path (`parents[2]`).
3. Postgres must be started **detached** (WMI) — a shell job object kills it (`0xC0000142`). DSN default `postgresql://memoryos@localhost:5432/memoryos`.
4. No LLM anywhere on write/read/lifecycle paths (audit rule `no_llm`).
5. Hot paths use `store.session()`; never raw `psycopg.connect` outside `db/` (audit rule).
6. Memory content never in span attributes — events only, redacted at collector export.
7. REAL column comparisons need `::float4` casts; `decay_candidates` returns UUID ids.
8. PII pre-guardrail scrubs before persistence (invariant #5) — verified statically by audit rule.

## Invariants (enforced by `tests/test_observability.py` audit gate + suite)
- Tenant isolation is real at all three layers (storage/index/retrieval filtering).
- Deletion propagates to consolidated/derived artifacts (leak-via-summary closed).
- Retrieval p95 < 150 ms (measured 12 ms on D3 workload; 500-row gate in test_latency).
- Token budget per turn enforced (`build_context` zone ceilings; overflow never crosses zones).
- PII pre/post guardrail — 0% leak on D3 c5 replay (baseline: 100%).
- No soft-delete writes in service code; purge is physical.

## Test Status
`pytest -q` → **97 passed, 0 failed**. Per file: test_db 12 · test_retrieval 14 · test_latency 1 · test_admission 24 · test_context 3 · test_lifecycle 16 · test_observability 18 · test_adversarial 9.
Markers: `latency` (EC-15), `adversarial` (Threat 1/2 replay). Fixtures leave DB empty (memories 0, propagation_jobs 0).

## Acceptance Status (G-M6, vs D3 naive baseline)
`python -m bench.acceptance` → PASS. precision@1 **1.0** (0.857) · contradiction **0.0** (0.333) · cold-start FP **0.0** (0.5) · sensitive leak retrieval/injection **0.0** (1.0/1.0) · task-level **0.9** (0.667) · p95 **12 ms** (<150 ms). Artifact: `bench/results/acceptance.json`.

## Git State
- branch: main; latest: `caac791` (G-M6); history: `d2d8e02` G-M1 · `bff78f9` G-M2 · `92c9490` G-M3 · `8ab43f1` G-M4 · `161c6ca` G-M5 · `caac791` G-M6 (+ docs commits before G-M1).
- Tree clean; nothing in flight.

## Important Files
| File | Purpose |
|---|---|
| `MemoryOS-App/src/memory_os/db/{store.py,schema.sql}` | storage; propagation_jobs table |
| `MemoryOS-App/src/memory_os/admission/{patterns,admitter}.py` | deterministic classification + PII scrub |
| `MemoryOS-App/src/memory_os/retrieval/{hybrid,bm25,rrf}.py` | tenant-prefiltered RRF fusion + provenance weights |
| `MemoryOS-App/src/memory_os/context/builder.py` | zone-budgeted injection |
| `MemoryOS-App/src/memory_os/lifecycle/manager.py` | merge/decay/evict + lineage cascade |
| `MemoryOS-App/src/memory_os/observability/tracer.py` | typed spans + RedactingCollector |
| `MemoryOS-App/src/memory_os/audit/checker.py` + `MemoryOS-App/audit/policy.toml` | config-as-code audit gate |
| `MemoryOS-App/bench/{acceptance,latency_profile}.py` | D3 acceptance + EC-15 profiles |
| `MemoryOS-App/tests/` | 8 gate files, 97 tests |
| `design/` | canonical design set (D4) incl. sprint_plan, threat_model, api_contracts |

## Commands (all from `MemoryOS-App\`)
- Suite: `$env:PYTHONPATH="src"; .venv\Scripts\python.exe -m pytest -q`
- Acceptance: `$env:PYTHONPATH="src"; .venv\Scripts\python.exe -m bench.acceptance`
- Audit gate: `$env:PYTHONPATH="src"; .venv\Scripts\python.exe -c "from memory_os.audit.checker import AuditChecker; print('PASS' if AuditChecker().audit().passed else 'FAIL')"`
- DB check: `& "C:\Users\CR7\Postgres\17\bin\psql.exe" -h localhost -p 5432 -U memoryos -d memoryos -tc "SELECT (SELECT count(*) FROM memories),(SELECT count(*) FROM propagation_jobs);"`
- Latency: `$env:PYTHONPATH="src"; .venv\Scripts\python.exe -m bench.latency_profile --rows 500 --queries 30`

## Resume Instructions
1. Read `docs/RESUME.md` → `docs/SESSION_STATE.md` → `CURRENT.md` → latest journal.
2. `git status` (expect clean) + `git log --oneline -8`.
3. If no new milestone is open in CURRENT.md: pick the next slice (API/HTTP layer, dashboard, deeper adversarial coverage, PDF regenerations) and gate it like prior gates — one outcome, one demo command, one commit.
4. Verify DB empty (0/0) and suite green before/after any run.

## Compaction Protocol (AGENTS.md)
- Repo docs are the source of truth; on context loss, revert to RESUME/SESSION/CURRENT and do not re-derive.
- Update CURRENT.md + journal + this file whenever a gate lands; commit per gate.
