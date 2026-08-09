# Current Work

> One question: **"Where exactly are we RIGHT NOW?"** — keep this file extremely practical. If chat context compacts, open this file and continue.

## Current Objective
G-M4 (lifecycle four levers + deletion propagation) is **built and gated green (70 passed)** — G-M4 commit pending; next is G-M5 per `design/sprint_plan.md`.

## Current Phase
Genesis milestones 1–4 done, gated, committed through G-M3 (d2d8e02 → 60cc6a3 → bff78f9 → 92c9490); G-M4 built, gate green, commit pending; then G-M5 (observability + security hardening).

## Current Task
Commit G-M4: `feat(g-m4): lifecycle four levers + deletion propagation via lineage`. Then open G-M5.

## Last Completed Action
[2026-08-09] G-M4 implementation complete, **70 passed**, DB left empty (memories 0, propagation_jobs 0):
- `store.py`: `add()` takes `status` + `consolidation_lineage`; new `set_status`, `mark_merged`, `get_derived` (GIN `&&` walk), `create_propagation_job` / `complete_propagation_job` / `get_propagation_job`.
- `lifecycle/manager.py`: `LifecycleManager` — merge lever `consolidate` (summary `assistant_generated`, deterministic `[summary of N facts] ` text, sources → `merged`), soft decay (`decay_candidates`/`decay`, low-importance + age, float4-safe), eviction + lineage walk (`evict`: physical root delete → deterministic rebuild cascade ascending lineage depth, survivors only → leak-via-summary closed; depth > 4 → evicted; survivors empty → evicted), 202-path (`in_progress` + `check_url` beyond `max_sync_derived`; idempotent `run_propagation_job`).
- Async-jobs table `propagation_jobs` (schema.sql).
- Gates `tests/test_lifecycle.py` (16): EC-04 merge-then-delete leak gate, ADR-005 multi-level summary-of-summary rebuild, depth-cap policy, decay softness, 202 vs complete semantics, cross-tenant propagation isolation.
- Bugs fixed: float4 0.1-prece precomparing gotcha (`::float4` casts), lineage prune on rebuild, `()` vs `[]`, UUID joins.

## Last Command Executed
`pytest -q` → 70 passed. `SELECT COUNT(*)` on memories/propagation_jobs → 0/0.

## Last Meaningful Result
G-M4 gate green including the single most important test this project named: `delete a source → regenerated summary omits the fact` (leak via summary = False), plus the ADR-005 multi-level rebuild at depth 2→3. DB empty. Tree = exactly the G-M4 commit set (uncommitted).

## Currently Modified Files (for this commit)
- NEW: `src/memory_os/lifecycle/{__init__,manager}.py`, `tests/test_lifecycle.py`, `journal/2026-08-09-session-gm4.md`
- MODIFIED: `src/memory_os/db/store.py`, `src/memory_os/db/schema.sql` (propagation_jobs), `docs/SETUP_AND_RUN.md` (G-M4 section)

## What I Was About To Do Next
Commit G-M4, then start G-M5 (sprint_plan: OTEL spans w/ redaction, adversarial eval replay of MemoryGraft/MINJA tests, audit config-as-code check).

## Immediate Next 3 Actions
1. `git add -A` + commit `feat(g-m4): lifecycle four levers + deletion propagation via lineage`.
2. Verify: `git status` clean; log shows G-M4 on top of 92c9490.
3. Open G-M5 per `design/sprint_plan.md`.

## Known Problems
- Default `python` (3.11) lacks heavy libs — always use `.venv\Scripts\python.exe` (Python 3.14).
- Postgres must be **detached-started** (WMI) or shell-tool job object kills it (`0xAFC000142`).
- psycopg import failures seen **only when scripts run in non-repo dirs** (`%LocalTemp%\opencode`) — work from repo root; pytest fine.
- **REAL `0.1` vs float8 literal**: comparisons against `importance_score` (REAL) must use `::float4` casts (stored 0.1 = 0.10000000149…).

## Do Not Repeat
- No writes to old repo (`D:\Abhii\Projects\Conversational-Memory-Intelligence-System-`); no `memory_type` column resurrection; data_model.md canonical.
- No `with conn:` + fresh `psycopg.connect()` on hot paths — use `store.session()`.
- Do not run Python from `%TEMP%` with the repo venv; keep scripts under `D:\Abhii\Projects\MemoryOS`.
- Don't seed via `store.add(...)` positionally — signature is keyword-only.
- Lifecycle SQL comparing against REAL columns needs explicit `::float4` casts (stored 0.1 = 0.10000000149…).
- Lifecycle SQL comparisons involve REAL columns — always explicit `::float4` when thresholds == stored values.

## Verification Required
After G-M4 commit: `git status` clean; `git log --oneline -5` shows `feat(g-m4)` on top of 92c9490; DB `COUNT(*) = 0` for both tables.

## Resume From Here
`docs/RESUME.md` → `docs/SESSION_STATE.md` → `CURRENT.md` → `journal/2026-08-09-session-gm4.md`.