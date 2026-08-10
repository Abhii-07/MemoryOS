# Current Work

> One question: **"Where exactly are we RIGHT NOW?"** — keep this file extremely practical. If chat context compacts, open this file and continue.

## Current Objective
**MemoryOS-App consolidation is COMPLETE** (commit `08ef825`): all Genesis-built code lives in `MemoryOS-App\`, tree clean, no pending work.

## Current Phase
Repo restructure (post-M7) — done. History: G-M1 `d2d8e02` → G-M6 `caac791`, `ce6bad0` docs sync, `08ef825` refactor(app). All design milestones implemented; all verification green.

## Current Task
None pending. Next work (if any) starts with `cd MemoryOS-App`.

## Last Completed Action
[2026-08-09] Committed `refactor(app): consolidate genesis-built code under MemoryOS-App` (`08ef825`, 41 files: 36 renames with history preserved, README + journal new). `git status` clean; tree moved fully under `MemoryOS-App\` (src/tests/bench/audit/pytest.ini/requirements.txt/.venv/.hf-cache).

## Last Completed Action
[2026-08-09] MemoryOS-App consolidation:
- `git mv` → `MemoryOS-App/`: `src/`, `tests/`, `bench/`, `audit/policy.toml`, `pytest.ini`, `requirements.txt` (git history preserved, R100).
- Physical move into `MemoryOS-App/`: `.venv/` (verified relocatable: psycopg/numpy/sentence-transformers import OK), `.hf-cache/`.
- Path fixes: `bench/acceptance.py` — `APP_ROOT = parents[1]`, `REPO_ROOT = parents[2]` (D3 dataset stays at repo root `experiments/naive_baseline/dataset.py`); `--out` → `APP_ROOT/bench/results/acceptance.json`. Audit checker + test policy path: verified zero-change (parents[3] still correct at new depth).
- NEW `MemoryOS-App/README.md` (app layout + quick start).
- Docs updated for the new layout: `docs/SETUP_AND_RUN.md` (§6 commands with `cd MemoryOS-App`, gates table, §8 layout prefixed `MemoryOS-App/`), `docs/RESUME.md`, `docs/SESSION_STATE.md` (constraints/commands/important-files).

## Last Command Executed
`cd MemoryOS-App; $env:PYTHONPATH="src"; .venv\Scripts\python.exe -m pytest -q` → 97 passed. `python -m bench.acceptance` → PASS (p95 0.010). Audit gate → PASS (8/8). DB counts → `0 | 0`.

## Last Meaningful Result
The app is now a single self-contained folder — code, tests, benchmarks, audit policy, venv, and model cache all under `MemoryOS-App\` — with the repo root dedicated to course deliverables. Everything green from the new location; only one file (bench/acceptance.py) needed a path change.

## Currently Modified Files (for this commit)
None — tree is clean after `08ef825`.

## What I Was About To Do Next
All planned work is done.

## Immediate Next 3 Actions
1. (none — steady state; next user request starts here)
2. If continuing: pick a hardening/extension task (e.g. R3 retrieval quality, additional EC alignment, packaging) — confirm scope with user first.
3. Any new session: re-verify quickly (`git status`, DB 0/0) before starting.

## Known Problems
- Default `python` (3.11) lacks heavy libs — always use `MemoryOS-App\.venv\Scripts\python.exe`.
- Postgres must be **detached-started** (WMI) or shell-tool job object kills it (`0xC0000142`).
- HF Hub unauthenticated warning on every embedder load — harmless, expected.
- `decay_candidates` returns UUID ids (not str) — compare via `str(c["id"])`.
- Relevance floor needs ≥2 shared lexemes — acceptance/adversarial queries must share tokens with seed text or the case raises `NoRelevantMemory` (that IS the honest cold-start outcome).
- ALWAYS run commands from `MemoryOS-App\` unless the task is repo-root doc work — pytest.ini, venv, and src all live there now.

## Do Not Repeat
- No writes to old repo (`D:\Abhii\Projects\Conversational-Memory-Intelligence-System-`); data_model.md canonical.
- No `psycopg.connect` outside db/; no raw memory content in span attributes.
- Do not run Python from `%TEMP%`; work from `MemoryOS-App\` (or repo root for docs).
- Don't seed `store.add(...)` positionally — keyword-only.
- REAL comparisons → `::float4`.

## Verification Required
Done at commit time: `git status` clean; log shows `08ef825` on top of `ce6bad0`; from `MemoryOS-App\`: `pytest -q` → 97 passed; `bench.acceptance` PASS; DB `0 | 0`.

## Resume From Here
`docs/RESUME.md` → `docs/SESSION_STATE.md` → `CURRENT.md` → `journal/2026-08-09-session-gm6b.md`.