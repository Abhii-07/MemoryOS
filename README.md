# MemoryOS

**Conversational memory intelligence system** — persistent memory for AI assistants, where memories are stored, retrieved, updated, consolidated, and deleted per user intent.

This repository is a research-grade course deliverable (handbook D1→D8) **and** a product concept ("MemoryOS").

## Repo layout
```
.genesis/        D5 Genesis spine: PLAN, DONE.html, LOOPS, wiki, checkpoints, decisions
design/          D4 design: system_design (3 parts + PDF), data_model, api_contracts, threat_model, ADRs, sprint_plan
experiments/     D3 naive baseline: protocol, results.csv, error_examples.jsonl, failure-report PDF
implementation/  D6 implementation + tests (later)
journal/         chronological session logs (this: 2026-08-08)
product/         PRD + product narrative (Phase 5)
reconstruction/  D1 first-principles reconstruction (Phase 1, merged)
research/        D2 landscape + sources catalog (Phase 2, verbatim copy)
tools/           build scripts (PDF pipeline, …)
transfer/        D8 handoff/training artifacts (later)
verification/    D6 verification evidence (later)
contribution/    D8 Genesis/ecosystem contribution (later)
docs/            continuity docs: SESSION_STATE, PROJECT_MEMORY, DECISIONS, RESUME
CURRENT.md       live checkpoint file
PLAN.md          phase plan with statuses
AGENTS.md        continuity rules (this repo)
```

## Setup & run

**Human-only instructions — see [`docs/SETUP_AND_RUN.md`](docs/SETUP_AND_RUN.md)**
(Postgres 17 + pgvector install, server start, DB bootstrap, venv, gates, troubleshooting).

Quick summary (full guide linked above):

```powershell
# 0. Env
#   - Postgres 17.10 portable at C:\Users\CR7\Postgres\17, cluster at C:\Users\CR7\Postgres\data
#   - pgvector 0.8.6 (Windows prebuilt) installed into the PG dirs
#   - venv:  py -3 -m venv .venv;  .venv\Scripts\python.exe -m pip install -r requirements.txt

# 1. Start the server (detached, survives the session)
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
  CommandLine = '"C:\Users\CR7\Postgres\17\bin\pg_ctl.exe" -D "C:\Users\CR7\Postgres\data" -l "C:\Users\CR7\Postgres\data\postgres.log" start' }
& "C:\Users\CR7\Postgres\17\bin\pg_isready.exe" -h localhost -p 5432

# 2. Milestone gates (G-M1 … G-M3, see design/sprint_plan.md)
$env:MEMORYOS_DB_DSN="postgresql://memoryos@localhost:5432/memoryos"
.venv\Scripts\python.exe -m pytest tests/ -v

# 3. D3 naive baseline — reproduce the measured failures
.venv\Scripts\python.exe experiments\naive_baseline\run_baseline.py
#      outputs: experiments\baseline_results.csv, experiments\error_examples.jsonl,
#               experiments\naive_baseline\summary.json

# 4. PDFs (D1/D4) — rebuild markdown → PDFs via headless Chrome (see tools/build_pdfs.py)
python tools\build_pdfs.py
```

**Architecture (target, D4 + ADR-001…007):** Postgres 17 + pgvector; hybrid retrieval
(BM25 + dense `all-MiniLM-L6-v2` embeddings + RRF k=60), deterministic supersession,
token-budgeted injection, PII/lifecycle guardrails, tenant isolation invariants in
`.genesis/context-graph.json`.

## Status
- **Phase:** D4 frozen (approved), handbook naming compliance done (67ddbcf); D6 build in progress — G-M1 (storage + tenant isolation) gate PASSED (12 tests, commit d2d8e02); G-M2/G-M3 next.
- **Architecture:** hybrid retrieval (BM25+dense+RRF), Python, local-only git, no license. See `docs/DECISIONS.md`.
- Implementation in `src/memory_os/` (Postgres 17 + pgvector); research + baseline merged from read-only source repos.

## Key docs
- `docs/RESUME.md` — shortest handoff (read first)
- `docs/SESSION_STATE.md` — canonical state
- `PLAN.md` — phase plan
- `journal/` — session chronology

## Source repos (read-only)
- `D:\Abhii\Projects\Conversational-Memory-Intelligence-System-` — weeks 1–4 research, naive baseline, genesis.
- `D:\Abhii\Opencode` — unversioned intermediates (new D1 drafts).

## Note
Local-only git repository: no remote, no LICENSE, no external pushes.