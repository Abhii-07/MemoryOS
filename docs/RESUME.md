# Resume Instructions

> The shortest file a fresh agent needs. Read FIRST, then the files in "Read Next Order".
> **If chat context was lost, trust ONLY these files** — do not re-derive state.

## Read First
1. `docs/SESSION_STATE.md` — canonical state, decisions, invariants, commands, resume point
2. `CURRENT.md` — where exactly we are now
3. `design/sprint_plan.md` — the milestone map (G-M1…G-M6)
4. `docs/DECISIONS.md` — decisions D-001…
5. `journal/` — latest `2026-08-09-session-gm*.md` (append, don't rewrite)

## Current State
MemoryOS repo (`D:\Abhii\Projects\MemoryOS`, branch `main`) — **all six build milestones committed and green**:
`d2d8e02` G-M1 → `bff78f9` G-M2 → `92c9490` G-M3 → `8ab43f1` G-M4 → `161c6ca` G-M5 → `caac791` G-M6, then docs sync `ce6bad0` and consolidation `08ef825` + `c466ae7`.
All app code lives in **`MemoryOS-App\`** (src/tests/bench/audit/pytest.ini/requirements.txt/.venv/.hf-cache — fully self-contained); repo root keeps the course deliverables (design/, docs/, experiments/, research/, journal/, …). Full suite **97 passed**; D3 acceptance replay **PASS** (all targets); DB Postgres 17 + pgvector local, left empty (0/0) after runs.

## Current Objective
Post-M7 steady state: all `sprint_plan.md` milestones (M1–M7, R1–R8) have passing demo commands. No milestone is in flight; next work is hardening/extension slices (e.g. API layer, dashboard, extra adversarial coverage) — nothing is open unless CURRENT.md says so.

## Last Completed Step
[2026-08-09] Consolidation committed (`08ef825` + `c466ae7`) — all Genesis-built code under `MemoryOS-App\` (src/tests/bench/audit/pytest.ini/requirements.txt/.venv/.hf-cache, history preserved via `git mv`). Prior: G-M6 `caac791` — adversarial replay (MemoryGraft/MINJA, 9 tests) + `MemoryOS-App/bench/acceptance.py` D3 final acceptance (contradiction 0% vs 33%, cold-start FP 0% vs 50%, leak 0% vs 100%, precision@1 1.0 vs 0.857, p95 12 ms vs 150 ms target).

## Next Step
None in flight. If starting new work: 1) read `design/sprint_plan.md` / `.genesis/PLAN.md` for the next slice, 2) write it as its own gate + commit.

## Important Constraints
- Old repo `Conversational-Memory-Intelligence-System-`: **READ-ONLY forever**.
- App code is consolidated in `MemoryOS-App\`; run every command from that directory (venv + pytest.ini + src all live there). Root `experiments/` stays accessible to `bench.acceptance` via an absolute path.
- Postgres 17 + pgvector only; no SQLite branch; postmaster must be WMI-detached (job objects kill it, `0xC0000142`).
- Always `.venv\Scripts\python.exe` (3.14) with `$env:PYTHONPATH="src"`, working dir = `MemoryOS-App\` (never `%TEMP%`).
- No LLM anywhere on write/read/lifecycle paths; deterministic, reproducible (R8).
- Memory content only in span *events* (never attributes); collector redacts at export.
- Local-only git; no LICENSE/remote/no secrets; hot paths use `store.session()`.

## Verification (remember to run)
- `git status` clean after commit; from `MemoryOS-App\`: `pytest -q` → 97 passed; DB counts `0 | 0`.
- `python -m bench.acceptance` → PASS (all targets) after any retrieval/admission change.
- `pytest tests/test_observability.py` audit gate must PASS after any policy/security change.

## Do NOT
- Write to old repo or `D:\Abhii\Opencode`.
- Seed `store.add(...)` positionally (keyword-only); compare REAL columns with `::float4`; use `str(c["id"])` for lifecycle UUIDs.
- Put raw memory content in span attributes; bypass the collector.

## Definition of Done (project-wide)
- Every design milestone has a passing demo command (DONE through M7 — verified at G-M6).
- All invariants checkable and tested (audit gate enforces them).
- `docs/*` + `CURRENT.md` + `journal` consistent with the latest commit.
- Fresh-session question "can a fresh session continue from repo alone" = YES (verified this resume file).