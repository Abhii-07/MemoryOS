# MemoryOS-App

The MemoryOS application — all Genesis-built code of the MemoryOS project
(Monorepo layout: this folder is the app; the repo root holds the course
deliverables — `design/`, `experiments/`, `research/`, `docs/`, `journal/`,
`.genesis/`, …).

Deterministic conversational-memory system on **PostgreSQL 17 + pgvector**:
persistent, retrievable, deletable memory for an AI assistant. No LLM on
any write/read/lifecycle path — everything is reproducible and testable.

## Layout

| Path | Purpose |
|---|---|
| `src/memory_os/db/` | relational schema + tenant-isolated storage (`propagation_jobs` for async cascades) |
| `src/memory_os/admission/` | deterministic turn classification (ADD/UPDATE/DELETE/NOOP) + PII pre-guardrail |
| `src/memory_os/retrieval/` | tenant-prefiltered BM25 + dense, RRF fusion, provenance-weighted ranking |
| `src/memory_os/context/` | zone-budgeted context injection (`build_context`) |
| `src/memory_os/lifecycle/` | four-lever lifecycle: merge / decay / evict / consolidation lineage |
| `src/memory_os/observability/` | typed trace spans + `RedactingCollector` (content only in events) |
| `src/memory_os/audit/` + `audit/policy.toml` | config-as-code audit gate (fails a misconfigured tree) |
| `tests/` | 8 gate files, 97 tests (markers: `latency`, `adversarial`) |
| `bench/` | `acceptance.py` (D3 workload replay) + `latency_profile.py` (EC-15) |

## Quick start

```powershell
# from MemoryOS-App/
$env:PYTHONPATH="src"
.venv\Scripts\python.exe -m pytest -q            # 97 passed
.venv\Scripts\python.exe -m bench.acceptance     # D3 acceptance (targets PASS)
.venv\Scripts\python.exe -m bench.latency_profile --rows 500 --queries 30
```

Requires a local PostgreSQL 17 + pgvector (`postgresql://memoryos@localhost:5432/memoryos`);
the schema applies itself via `MemoryStore().apply_schema()` (idempotent).
Full environment setup: `../docs/SETUP_AND_RUN.md`.