# Current Work

> One question: **"Where exactly are we RIGHT NOW?"** — keep this file extremely practical. If chat context compacts, open this file and continue.

## Current Objective
G-M6 (adversarial replay + D3 final acceptance) is **built and gated green (97 passed; acceptance all targets)** — G-M6 commit pending.

## Current Phase
Genesis milestones 1–6 done, gated, committed through G-M5 (`161c6ca`); G-M6 built, gate green, commit pending. All design milestones (M1–M7) from `system_design_part3.md` §15 are now implemented; tasks beyond this are hardening/extension.

## Current Task
Commit G-M6: `feat(g-m6): adversarial replay of memory poisoning + D3 acceptance gate`. Then update docs/RESUME + SESSION_STATE.

## Last Completed Action
[2026-08-09] G-M6 implementation complete, **97 passed**, acceptance PASS, DB left empty (0/0):
- NEW `tests/test_adversarial.py` (9 tests, `adversarial` marker registered in pytest.ini): MemoryGraft replay (tool_derived directive never outranks user twin; 4-query paraphrase stability; corrigendum supersedes by slot key), MINJA/MemoryTrap (newline-framed directive inert, `- text` data lines only), poison influence over time (decay_candidates picks low-importance poison; decay → zero retrieval presence), cross-tenant adversarial corpus (EC-05).
- NEW `bench/acceptance.py`: replays the exact 10 D3 cases from `experiments/naive_baseline/dataset.py` through admission → retrieval → context injection; aggregates identical keys to `summary.json`; checks Deliverable targets; writes `bench/results/acceptance.json`; non-zero exit on miss.
- Acceptance result: precision@1 1.0 (baseline 0.857), contradiction 0.0 (0.333), cold-start FP 0.0 (0.5), leak retrieval/injection 0.0 (1.0/1.0), task-level 0.9 (0.667), p95 0.012s (0.0008; target <0.15s).

## Last Command Executed
`pytest -q` → 97 passed. `python -m bench.acceptance` → PASS. DB counts → `0 | 0`.

## Last Meaningful Result
The exact workload that broke the naive baseline (33% contradiction, 50% cold-start FP, 100% sensitive leak) now passes all Deliverable targets — including leak 0% on both retrieval and injection — through the real deterministic pipeline (no LLM anywhere). Plus the threat model's own verification language is now executable: poisoned memories lose influence over time and never beat the user's own statement.

## Currently Modified Files (for this commit)
- NEW: `tests/test_adversarial.py`, `bench/acceptance.py`, `bench/results/acceptance.json`, `journal/2026-08-09-session-gm6.md`
- MODIFIED: `pytest.ini` (adversarial marker), `docs/SETUP_AND_RUN.md` (G-M6 section + gates table), `CURRENT.md`

## What I Was About To Do Next
Commit G-M6; then sync `docs/RESUME.md`/`docs/SESSION_STATE.md` to "all design milestones implemented" status.

## Immediate Next 3 Actions
1. `git add -A` + commit `feat(g-m6): adversarial replay of memory poisoning + D3 acceptance gate`.
2. Verify: `git status` clean; log shows G-M6 on top of 161c6ca; DB 0/0.
3. Update `docs/RESUME.md` + `docs/SESSION_STATE.md` for the new steady state.

## Known Problems
- Default `python` (3.11) lacks heavy libs — always use `.venv\Scripts\python.exe` (Python 3.14).
- Postgres must be **detached-started** (WMI) or shell-tool job object kills it (`0xC0000142`).
- HF Hub unauthenticated warning on every embedder load — harmless, expected.
- `decay_candidates` returns UUID ids (not str) — compare via `str(c["id"])`.
- Relevance floor needs ≥2 shared lexemes — acceptance/adversarial queries must share tokens with seed text or the case raises `NoRelevantMemory` (that IS the honest cold-start outcome).

## Do Not Repeat
- No writes to old repo (`D:\Abhii\Projects\Conversational-Memory-Intelligence-System-`); data_model.md canonical.
- No `psycopg.connect` outside db/; no raw memory content in span attributes.
- Do not run Python from `%TEMP%` with the repo venv; work from repo root.
- Don't seed `store.add(...)` positionally — keyword-only.
- REAL comparisons → `::float4`.

## Verification Required
After G-M6 commit: `git status` clean; `git log --oneline -5` shows `feat(g-m6)` on top of 161c6ca; DB `0 | 0`; `pytest -q` → 97 passed; `python -m bench.acceptance` → PASS.

## Resume From Here
`docs/RESUME.md` → `docs/SESSION_STATE.md` → `CURRENT.md` → `journal/2026-08-09-session-gm6.md`.