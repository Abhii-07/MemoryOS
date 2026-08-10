# Current Work

> One question: **"Where exactly are we RIGHT NOW?"** — keep this file extremely practical. If chat context compacts, open this file and continue.

## Current Objective
**Move the whole app (including tests) under `implementation/`** per the handbook D6 layout: `implementation/MemoryOS-App/` — move done + one code fix applied; verification (pytest/bench/audit/DB) pending; commit pending.

## Current Phase
Repo layout pass (post-M7 restructure #2). History: G-M1 `d2d8e02` → G-M6 `caac791`, `ce6bad0` docs sync, `08ef825` consolidation (MemoryOS-App/), now D6 placement (implementation/MemoryOS-App/).

## Current Task
Verify everything from the new depth and commit `refactor(repo): move app under implementation/ per D6 layout`:
1. `.venv` still imports (psycopg/numpy/sentence-transformers) at the moved path.
2. From `implementation\MemoryOS-App`: `pytest -q` → 97 passed; `python -m bench.acceptance` → PASS; audit gate → PASS; DB `0 | 0`.
3. `git add -A` + commit; `git status` clean.

## Last Completed Action
[2026-08-09] Moved `MemoryOS-App` → `implementation\MemoryOS-App` physically (Move-Item; `.venv`/`.hf-cache` traveled with it). `git add -A` → all tracked files registered as R100 renames. Applied the only code fix needed: `bench/acceptance.py` `REPO_ROOT = parents[2] → parents[3]` (dataset stays at repo root `experiments/`; `APP_ROOT=parents[1]`, checker/test policy `parents[3]`, embedder `.hf-cache`, pytest.ini `testpaths=tests` all verified depth-immune). Rewrote `implementation/README.md` (no longer a placeholder). Docs updated: `docs/SETUP_AND_RUN.md`, `docs/RESUME.md`, `docs/SESSION_STATE.md`, root `README.md` (layout + quick summary now `cd implementation\MemoryOS-App`), `implementation/MemoryOS-App/README.md` (link depth). `verification/` intentionally left as-is (empty placeholder — user's call).

## Last Command Executed
`Move-Item MemoryOS-App implementation\MemoryOS-App` → OK (src/bench/.venv/.hf-cache all present). `git add -A` staged 40 R100 renames.

## Last Meaningful Result
The handbook layout is now truthful: `implementation/` holds the real D6 implementation (whole app incl. tests, venv, cache), `verification/` stays empty per user decision. App-relative path logic means the entire app moves with exactly ONE mechanism change (`REPO_ROOT` depth).

## Currently Modified Files (for this commit)
- RENAMED (R100 via git): `MemoryOS-App/*` → `implementation/MemoryOS-App/*` (40 tracked files: src, tests, bench, audit, pytest.ini, requirements.txt, README.md, bench/results/acceptance.json)
- MODIFIED: `implementation/MemoryOS-App/bench/acceptance.py` (REPO_ROOT parents[3]), `implementation/README.md` (rewrite), `implementation/MemoryOS-App/README.md` (link depth), `README.md`, `docs/SETUP_AND_RUN.md`, `docs/RESUME.md`, `docs/SESSION_STATE.md`, `CURRENT.md`
- UNTRACKED-ignored: `.venv/`, `.hf-cache/` moved physically (gitignored)
- UNTOUCHED by design: `verification/` (stays empty), `journal/2026-08-09-session-gm6b.md` (historical)

## What I Was About To Do Next
Run the verify loop (venv import → pytest 97 → acceptance PASS → audit PASS → DB 0/0) then commit.

## Immediate Next 3 Actions
1. `.venv\Scripts\python.exe -c "import psycopg, numpy, sentence_transformers"` at `implementation\MemoryOS-App`.
2. `pytest -q` → 97 passed; `python -m bench.acceptance` → PASS; audit gate → PASS; DB counts → `0 | 0`.
3. `git add -A` + commit `refactor(repo): move app under implementation/ per D6 layout`; verify clean.

## Known Problems
- Default `python` (3.11) lacks heavy libs — always use `implementation\MemoryOS-App\.venv\Scripts\python.exe`.
- Postgres must be **detached-started** (WMI) or shell-tool job object kills it (`0xC0000142`).
- HF Hub unauthenticated warning on every embedder load — harmless, expected.
- `decay_candidates` returns UUID ids (not str) — compare via `str(c["id"])`.
- Relevance floor needs ≥2 shared lexemes — acceptance/adversarial queries must share tokens with seed text or the case raises `NoRelevantMemory` (that IS the honest cold-start outcome).
- ALWAYS run commands from `implementation\MemoryOS-App\` unless the task is repo-root doc work — pytest.ini, venv, and src all live there now.

## Do Not Repeat
- No writes to old repo (`D:\Abhii\Projects\Conversational-Memory-Intelligence-System-`); data_model.md canonical.
- No `psycopg.connect` outside db/; no raw memory content in span attributes.
- Do not run Python from `%TEMP%`; work from `implementation\MemoryOS-App\` (or repo root for docs).
- Don't seed `store.add(...)` positionally — keyword-only.
- REAL comparisons → `::float4`.

## Verification Required
`git status` clean after commit; log shows the move on top of `d680142`; from `implementation\MemoryOS-App\`: `pytest -q` → 97 passed; `bench.acceptance` PASS; DB `0 | 0`.

## Resume From Here
`docs/RESUME.md` → `docs/SESSION_STATE.md` → `CURRENT.md` → `implementation/MemoryOS-App/README.md`.