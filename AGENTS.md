# AGENTS.md — Agent and Repository Guidance

> Repository-local instructions for any AI coding agent (OpenCode, Claude Code, etc.).

## Context Continuity Rules

**The repository is the source of truth for project state — never the chat context.**

### Before beginning work
1. Read `docs/RESUME.md` — shortest summary, mandatory first
2. Read `docs/SESSION_STATE.md` — canonical state
3. Read `CURRENT.md` — where we are exactly now
4. Read `PLAN.md` — priorities and phase statuses
5. Read relevant `journal/` entries (latest first)
6. Run `git -C D:\Abhii\Projects\MemoryOS status` and `git log --oneline -5`

### During long-running work
- Persist important decisions immediately:
  - Decisions → `docs/DECISIONS.md` (D-XXX entry)
  - Durable knowledge changes → `docs/PROJECT_MEMORY.md`
  - Chronological record → `journal/YYYY-MM-DD-<topic>.md`
- Update `CURRENT.md` after every meaningful milestone (or before any pause).
- Update `docs/SESSION_STATE.md` periodically (at least before context compaction).
- Record test/research conclusions in the relevant `research/`, `tests/`, `verification/` file.
- Never rely on chat context as a source of truth.

### Before context compaction (IMPORTANT — do not defer)
- Update `CURRENT.md` and `docs/SESSION_STATE.md`.
- Update `docs/PROJECT_MEMORY.md` if durable knowledge changed.
- Update the current journal file.
- Record: exact next action, uncommitted changes, test status, blockers.
- If pre-empting compaction: **stop nonessential work and checkpoint first**.

### After context compaction
- Re-read the continuity files (RESUME → SESSION_STATE → CURRENT → PLAN → latest journal).
- Do NOT assume conversational knowledge survived; do NOT redo completed (verified) work.
- Verify repository state (`git status`, `git log`) before continuing.

---

## Project-Specific Rules

### Write/read permissions
- **NEVER WRITE TO** `D:\Abhii\Projects\Conversational-Memory-Intelligence-System-` — this is a frozen, read-only source archive.
- **NEVER WRITE TO** `D:\Abhii\Opencode` — unversioned source, import-only.
- All new work lands in **this repo** (MemoryOS, `D:\Abhii\Projects\MemoryOS`).

### Evidence discipline (course requirement)
Every claim in deliverable documents must be tagged:
- `[P: <source>]` — external paper/observation
- `[A: <assumption>]` — explicit assumption
- `[O]` — verified observation

Never invent citations; verify before citing (research pass R1 in Phase 6).

### Git conventions
- Commit per phase (see `PLAN.md` commit map), conventional prefixes (`feat`, `docs`, `chore`, `fix`).
- Never commit: `.env`, secrets, credentials, generated PDFs until regenerated at phase boundary, `__pycache__/`, `*.pyc`.
- No `LICENSE` file, no remote — stay local-only.

### Environment notes
- PDF pipeline: Python 3.14 absolute path (`C:\Users\CR7\AppData\Local\Python\pythoncore-3.14-64\python.exe`) + Chrome headless args (`--headless --print-to-pdf`).
- Baseline venv: `D:\Abhii\Projects\MemoryOS\.venv` (scikit-learn, numpy) — create in Phase 3.
- Scratch: `C:\Users\CR7\AppData\Local\Temp\opencode`.

### Checkpoint after (minimum)
- Phase completion (update CURRENT + SESSION + journal; commit)
- Research pass completion
- Architectural decision (write DECISIONS.md entry)
- Blocker discovered (update SESSION_STATE blockers + CURRENT)
- CRITICAL: before context compaction can be triggered.

### Do not
- Re-create skeleton dirs; don't modify old repo/Opencode; don't mark unverified work `[x]`; don't add placeholders; don't add remote/license.