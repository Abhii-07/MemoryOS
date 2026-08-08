# Resume Instructions

> The shortest file a fresh agent needs. Read FIRST, then the files in "Read Next Order".
> **If chat context was lost, trust ONLY these files** — do not re-derive state.

## Read First
1. `docs/SESSION_STATE.md` — canonical state, decisions, invariants, commands, resume point
2. `CURRENT.md` — where exactly we are now
3. `PLAN.md` — full plan with statuses
4. `docs/DECISIONS.md` — decisions D-001…D-010
5. `journal/2026-08-08-session.md` — today's chronology (append, don't rewrite)

## Current State
MemoryOS repo exists (`D:\Abhii\Projects\MemoryOS`), branch `main`, **0 commits**, skeleton dirs + continuity docs committed (this checkpoint = repo's FIRST commit). Old repo and Opencode are read-only sources.

## Current Objective
Execute the locked 7-phase plan: **Phase 0 (finish) → Phase 1 (D1 merge) → … → Phase 7 (gates)**. Every phase = one commit; history clean; final answer "fresh session can continue" must be YES only after verification.

## Last Completed Step
[2026-08-08] Wrote continuity docs and this checkpoint; `git init` was already done by the user (0 commits at that point).

## Next Step
1. `git -C D:\Abhii\Projects\MemoryOS add -A`
2. `git -C D:\Abhii\Projects\MemoryOS commit -m "docs(continuity): persist session state and resume checkpoint"`
3. Verify `git status` clean → **then Phase 0 remaining**: port `C:\Users\CR7\AppData\Local\Temp\opencode\build_pdfs.py` → `tools/build_pdfs.py` and run a smoke PDF build.
4. Then Phase 1 (D1 merge).

## Important Constraints
- Old repo `Conversational-Memory-Intelligence-System-`: **READ-ONLY forever** — never write/edit.
- `D:\Abhii\Opencode` is **not a git repo** — it's an unversioned source to copy from.
- Local-only git; no LICENSE; no secrets; no placeholders ("TODO") in deliverables.
- Every claim tagged `[P]/[A]/[O]` in deliverable docs.
- PDFs generated from markdown via `tools/build_pdfs.py` (Python 3.14 path), never hand-edited.
- Python 3.14 = PDF/tooling; Python 3.11 (or `.venv`) = baseline/scikit-learn.

## Verification (remember to run)
- `git -C D:\Abhii\Projects\MemoryOS status` (expect CLEAN after each phase commit)
- `git log --oneline` (one commit per phase)
- PDF smoke: after any change to `tools/`, rebuild a fixture PDF; check page count.
- Baseline (Phase 3): rerun `run_baseline.py` → CSVs/JSONL produced; numbers stable.

## Do NOT
- Write to old repo or `D:\Abhii\Opencode`.
- Re-create skeleton dirs (already exist).
- Mark `[x]` anything unverified (gate rule).
- Introduce `LICENSE`, remote, GitHub Actions.

## Definition of Done (project-wide)
- Every deliverable D1–D8 present with real artifacts (no placeholder), committed.
- All claims cited with `[P]/[A]/[O]`; PDFs regenerated & page counts stable.
- All invariants (#1–#5) checkable in D4/D6 (tests to exist).
- `docs/*` + `CURRENT.md` + `journal` all consistent with final state.
- Fresh-session question answered YES after verification.