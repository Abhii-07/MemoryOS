# Current Work

> One question: **"Where exactly are we RIGHT NOW?"** — keep this file extremely practical. If chat context compacts, open this file and continue.

## Current Objective
**Consolidate all Genesis-built code into `MemoryOS-App\`** (fully self-contained app folder). Move is done and verified (97 passed, acceptance PASS, DB 0/0 — all run from the new location); commit pending.

## Current Phase
Repo restructure (post-M7). History: G-M1 `d2d8e02` → G-M6 `caac791`, then `ce6bad0` (docs sync). All design milestones implemented; this is an organizational refactor, not new functionality.

## Current Task
Commit the move: `refactor(app): consolidate genesis-built code under MemoryOS-App`. Then verify tree clean + log.

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
- RENAMED (git mv, history preserved): `src/`, `tests/`, `bench/`, `audit/policy.toml`, `pytest.ini`, `requirements.txt` → `MemoryOS-App/`
- MODIFIED: `MemoryOS-App/bench/acceptance.py` (APP_ROOT/REPO_ROOT split), `docs/SETUP_AND_RUN.md`, `docs/RESUME.md`, `docs/SESSION_STATE.md`, `CURRENT.md`
- NEW: `MemoryOS-App/README.md`, `journal/2026-08-09-session-gm6b.md`
- UNTRACKED-ignored: `.venv/`, `.hf-cache/` moved physically (gitignored)

## What I Was About To Do Next
Commit the refactor; then any new work starts with `cd MemoryOS-App`.

## Immediate Next 3 Actions
1. `git add -A` + commit `refactor(app): consolidate genesis-built code under MemoryOS-App`.
2. Verify: `git status` clean; `git log --oneline -3` shows the refactor on top of `ce6bad0`.
3. Optional: treelist sanity (`Get-ChildItem MemoryOS-App`) to confirm layout.

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
After the refactor commit: `git status` clean; `git log --oneline -3` shows `refactor(app)` on top of `ce6bad0`; from `MemoryOS-App\`: `pytest -q` → 97 passed; DB `0 | 0`.

## Resume From Here
`docs/RESUME.md` → `docs/SESSION_STATE.md` → `CURRENT.md` → `journal/2026-08-09-session-gm6b.md`.