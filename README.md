# MemoryOS

**Conversational memory intelligence system** — persistent memory for AI assistants, where memories are stored, retrieved, updated, consolidated, and deleted per user intent.

This repository is a research-grade course deliverable (handbook D1→D8) **and** a product concept ("MemoryOS").

## Repo layout
```
design/          D4 design direction + edge-case ledger (Phase 5)
experiments/     D3 naive baseline + results (Phase 3)
implementation/  D6 implementation + tests (later)
journal/         chronological session logs (this: 2026-08-08)
product/         PRD + product narrative (Phase 5)
reconstruction/  D1 first-principles reconstruction (Phase 1, merged)
research/        D2 landscape + sources catalog (Phase 2, verbatim copy)
tools/           build scripts (PDF pipeline, …)
transfer/        D8 handoff/training artifacts (later)
verification/    D7 verification evidence (later)
docs/            continuity docs: SESSION_STATE, PROJECT_MEMORY, DECISIONS, RESUME
CURRENT.md       live checkpoint file
PLAN.md          phase plan with statuses
AGENTS.md        continuity rules (this repo)
```

## Status
- **Phase:** 0 (bootstrap) — in progress; continuity checkpoint is the repo's `docs(continuity)` first commit.
- **Architecture:** hybrid retrieval (BM25+dense+RRF), Python, local-only git, no license. See `docs/DECISIONS.md`.
- No implementation yet; research + baseline to be merged from read-only source repos.

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