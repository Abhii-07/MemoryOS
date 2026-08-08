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

**Requirements:** Python 3.11+ (`py -3`), a venv with `pypdf` (used by the PDF tooling) — the baseline venv lives at `.venv`.

```powershell
# 1. Naive baseline (D3) — reproduce the measured failures
.venv\Scripts\python.exe experiments\naive_baseline\run_baseline.py
#      outputs: experiments\baseline_results.csv, experiments\error_examples.jsonl,
#               experiments\naive_baseline\summary.json

# 2. PDFs (D1/D4) — rebuild markdown → PDFs via headless Chrome (see tools/build_pdfs.py)
python tools\build_pdfs.py
```

**Architecture (target, D4 + ADR-001…007):** Postgres 17 + pgvector; hybrid retrieval
(BM25 + dense `all-MiniLM-L6-v2` embeddings + RRF k=60), deterministic supersession,
token-budgeted injection, PII/lifecycle guardrails, tenant isolation invariants in
`.genesis/context-graph.json`.

## Status
- **Phase:** D4 frozen (approved), handbook naming compliance done (67ddbcf); D6 build = next (Logo M1–M3).
- **Architecture:** hybrid retrieval (BM25+dense+RRF), Python, local-only git, no license. See `docs/DECISIONS.md`.
- Implementation pending; research + baseline merged from read-only source repos.

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