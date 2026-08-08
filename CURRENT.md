# Current Work

> One question: **"Where exactly are we RIGHT NOW?"** — keep this file extremely practical. If chat context compacts, open this file and continue.

## Current Objective
G-M2 (hybrid retrieval) is built and gated — **commit pending**. Then G-M3 (admission + context) per `design/sprint_plan.md`.

## Current Phase
Genesis milestones 1–2 done, gated, committed except the final G-M2 commit; next is G-M3.

## Current Task
Commit G-M2: `feat(g-m2): hybrid retrieval + RRF + EC-15 latency`, then open G-M3.

## Last Completed Action
[2026-08-08 evening] G-M2 implementation complete:
- Local 384-d embedder (sentence-transformers `all-MiniLM-L6-v2`) in `.hf-cache/`, lazy + thread-locked, BM25-only fallback when unavailable.
- `retrieval/`: tokenizer, Okapi BM25 (tenant-scoped stats), RRF k=60, `HybridRetriever` with two-signal relevance floor (cosine ≥ 0.5 AND ≥2 shared terms, OR ≥ 0.75 paraphrase carve-out).
- D3 exact-string calibration; c1 closed by supersession (stale scores 0.876 > current 0.657 — proves filtering, not scoring), c6 by the floor, c4 by pre-filter.
- 14 retrieval tests + EC-15 latency gate (`pytest -m latency`, 500 rows, p95 < 150ms) → **27 passed**.
- EC-15 fix: psycopg3 `__exit__` closes connections → `MemoryStore.session()` persistent connection, p95 206ms → ~20ms.
- Sprint risk #4 closed: planner escalates to HNSW at scale (EXPLAIN 20k rows → `idx_memories_dense`).
- Setup doc + requirements updated for G-M2; scratch data (20562 rows) purged.

## Last Command Executed
`pytest tests/test_db.py test_retrieval.py test_latency.py -q` → 27 passed.

## Last Meaningful Result
G-M2 gate green with real embeddings: `hits/query 4.5`, p95 = 19.6ms @ 500 rows (invariant < 150ms). DB empty of scratch data. Working tree = exactly the G-M2 commit set (uncommitted).

## Currently Modified Files (for this commit)
- NEW: `src/memory_os/embeddings/{__init__,embedder}.py`, `src/memory_os/retrieval/{__init__,tokenizer,bm25,rrf,hybrid}.py`, `tests/test_retrieval.py`, `tests/test_latency.py`, `bench/latency_profile.py`
- MODIFIED: `src/memory_os/db/store.py` (Jsonb fix + `session()`), `requirements.txt` (+sentence-transformers/pytorch), `pytest.ini` (latency marker), `.gitignore` (`.hf-cache/`), `docs/SETUP_AND_RUN.md`, `journal/2026-08-08-session.md`

## What I Was About To Do Next
Commit G-M2 as `feat(g-m2): hybrid retrieval + RRF + EC-15 latency gate`, update checkpoint, then start G-M3 (admission + context, per sprint_plan.md; gates `tests/test_admission.py -q`, `tests/test_context.py -q`).

## Immediate Next 3 Actions
1. `git add -A` + commit `feat(g-m2): hybrid retrieval + RRF + EC-15 latency gate` → confirm clean status.
2. Report G-M2 completion + latency story (206ms → 20ms) to user; await approval to open **G-M3** (admission ADD/UPDATE/DELETE/NOOP + deterministic supersession, context zones + PII guardrail).
3. If approved: G-M3 build; gate commands `pytest tests/test_admission.py -q` and `pytest tests/test_context.py -q`.

## Known Problems
- Default `python` (3.11) lacks heavy libs — always use `.venv\Scripts\python.exe` (Python 3.14).
- Postgres must be **detached-started** (WMI) or shell-tool job object kills it (`0xC0000142`).
- psycopg import failures (missing pq wrapper) seen **only when scripts run in non-repo dirs** (`%LocalTemp%\opencode`) — work from repo root; pytest fine.
- `.hf-cache/` is a one-time ~80MB download; deleting it drops dense retrieval until re-download (suite skips those tests).

## Do Not Repeat
- No writes to old repo (`D:\Abhii\Projects\Conversational-Memory-Intelligence-System-`, no `memory_type` column resurrection; data_model.md is canonical).
- No `with conn:` + fresh `psycopg.connect()` on hot paths (closes conn on exit / 30ms per op) — use `store.session()`.
- Do not run Python code files from `%TEMP%` with the repo venv; keep scripts under `D:\Abhii\Projects\MemoryOS`.

## Verification Required
After G-M2 commit: `git status` clean; `git log` shows the new `feat(g-m2)` on top of `60cc6a3`.

## Resume From Here
`docs/RESUME.md` → `docs/SESSION_STATE.md` → `CURRENT.md` → `journal/2026-08-08-session.md`.