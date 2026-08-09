# Current Work

> One question: **"Where exactly are we RIGHT NOW?"** — keep this file extremely practical. If chat context compacts, open this file and continue.

## Current Objective
G-M3 (deterministic admission + context construction) is **built, gated green, and committed** — next is G-M4 per `design/sprint_plan.md`.

## Current Phase
Genesis milestones 1–3 done, gated, committed (d2d8e02 → 60cc6a3 → bff78f9 → G-M3 commit); next milestone G-M4.

## Current Task
G-M3 commit landed; open G-M4 (per sprint_plan.md — admission/context integration surfaces + remaining ECs).

## Last Completed Action
[2026-08-09] G-M3 implementation complete, **54 passed**, DB left empty after runs:
- `admission/patterns.py` — deterministic grammar (ADR-008): PII scrub (`[EMAIL]`, `[REDACTED]`, `[IP]`, …), delete-target parser, NOOP set, correction markers, slot rules (rule order matters: deadline/meeting before generic `is on X`).
- `admission/admitter.py` — `Admitter.admit` → ADD / UPDATE (same tenant+user+slot supersedes via `valid_until`, confidence 0.95) / DELETE (token-intersection, physical purge) / NOOP (EC-017); PII redaction before persistence.
- `context/builder.py` — zone budgets (retrieved_memory 40% etc.), `estimate_tokens` = words×1.3, `build_context` injects in rank order, per-zone ceiling never overflows (EC-010); explicit `zone_budgets` carve out of remaining budget.
- Gates: `tests/test_admission.py` (21) + `tests/test_context.py` (6) → **54 passed**; the D3 c3 40-token stress keeps the buried correct fact.
- Fixed mid-build: tool-rule `is on X` added as LAST rule (avoids deadline/meeting collisions); `ContextBudget` partial-zone merging; autouse `clean` now deletes after `yield` (DB left empty at suite end).
- Docs: SETUP_AND_RUN.md G-M3 section + updated gates table; note in CURRENT.md; journal entry.

## Last Command Executed
`pytest -q` → 54 passed; `SELECT COUNT(*) FROM memories` → 0 (no residue).

## Last Meaningful Result
G-M3 gate green: ADD/UPDATE/DELETE/NOOP classification, supersession convergence (12 slots, corrections), PII pre-guardrail leak rate 0.0 (D3 c5 re-run), tenant isolation never crossed, 40-token budget case survives. DB empty of scratch data. Working tree = exactly the G-M3 commit set (uncommitted).

## Currently Modified Files (for this commit)
- NEW: `src/memory_os/admission/{__init__,patterns,admitter}.py`, `src/memory_os/context/{__init__,builder}.py`, `tests/test_admission.py`, `tests/test_context.py`, `design/decision_records/ADR-008-entity-slot-linking.md`
- MODIFIED: `tests/test_retrieval.py` (clean-after fixture), `docs/SETUP_AND_RUN.md` (G-M3 section), `journal/2026-08-09-session.md` (pending entry)

## What I Was About To Do Next
Commit G-M3 as `feat(g-m3): deterministic admission + context zones`, then start G-M4.

## Immediate Next 3 Actions
1. `git add -A` + commit `feat(g-m3): deterministic admission + context gates` → confirm clean status.
2. Update this checkpoint: G-M3 committed (`git log --oneline` shows it on top of `bff78f9`).
3. Open G-M4 per `design/sprint_plan.md`.

## Known Problems
- Default `python` (3.11) lacks heavy libs — always use `.venv\Scripts\python.exe` (Python 3.14).
- Postgres must be **detached-started** (WMI) or shell-tool job object kills it (`0xC0000142`).
- psycopg import failures seen **only when scripts run in non-repo dirs** (`%LocalTemp%\opencode`) — work from repo root; pytest fine.
- `zone_budgets` with tiny `token_budget` now scales other zones to the *remaining* budget — a strict-`40` D3 case needs `zone_budgets={"retrieved_memory": 40}`.

## Do Not Repeat
- No writes to old repo (`D:\Abhii\Projects\Conversational-Memory-Intelligence-System-`); no `memory_type` column resurrection; data_model.md canonical.
- No `with conn:` + fresh `psycopg.connect()` on hot paths — use `store.session()`.
- Do not run Python code from `%TEMP%` with the repo venv; keep scripts under `D:\Abhii\Projects\MemoryOS`.
- Don't seed via `store.add(...)` positionally — signature is keyword-only (`tenant_id`, `user_id`, `text`, `dense_embedding`, `sparse_terms`).

## Verification Required
After G-M3 commit: `git status` clean; `git log --oneline -4` shows the new `feat(g-m3)` on top of `bff78f9`; DB `COUNT(*) = 0`.

## Resume From Here
`docs/RESUME.md` → `docs/SESSION_STATE.md` → `CURRENT.md` → `journal/` most recent.