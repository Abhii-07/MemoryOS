# Session State

> Canonical, machine-readable/human-readable state of this project. **The repository is the source of truth, not chat context.** If any file contradicts this one, SESSION_STATE.md wins (and the contradiction must be fixed).

## Last Updated
- Date/time: 2026-08-08 (late session)
- Current git branch: `main`
- Current commit SHA: `2de6fa8` (`docs(merge): final journal + end-of-merge checks`) — D4 (Phase 8) commiting next

## Project
- Project name: **MemoryOS** (course deliverable: *Conversational Memory Intelligence System*)
- Overall objective: Build, from first principles, a production-grade conversational-memory system — persistent, retrievable, deletable memory for an AI assistant — delivered as a research-grade course repo (D1–D8) AND a coherent product ("MemoryOS").
- Current milestone: Phase 2 (D2 research copy) — Phases 0–1 complete.

## Current Phase
- Phase number: **2 (D2 research copy + catalog)** — NOT STARTED
- Phase name: Copy old-repo research verbatim + sources catalog
- Current task: copy `research/**` from old repo; write `sources_catalog.md` + `README.md`
- Current subtask: (none — whole phase)
- **Exact point where execution resumes:**
  1. Copy `D:\Abhii\Projects\Conversational-Memory-Intelligence-System-\research\**` → `research\` (verbatim)
  2. Write `research/sources_catalog.md` + `research/README.md`
  3. Commit `feat(d2): research weeks 1-4 + sources catalog`
  4. Phase 3: `.venv` + baseline run

## Overall Plan
| Phase | Name | Status | Relevant commit | Important artifacts | Remaining work |
|---|---|---|---|---|---|
| 0 | Bootstrap + continuity | [x] COMPLETE | `docs(continuity)` (7bd37ca) | dirs, git init, docs/ + CURRENT + PLAN + AGENTS + README + .gitignore; tools/build_pdfs.py | — |
| 1 | D1 merged reconstruction | [x] COMPLETE | `feat(d1)` (2823f40) | `reconstruction/*.md` (5), 2 PDFs (6p/4p), merged OQ9 + stage→req map | — |
| 2 | D2 research copy + catalog | [x] COMPLETE | `feat(d2)` (5f9677e) | `research/**` (verbatim, 18 files hash-verified), catalog, README | — |
| 3 | D3 baseline run | [x] COMPLETE | `feat(d3)` (1ff47a5) | venv, baseline artifacts, reports, productive_failure PDF (3p) | — |
| 4 | Genesis spine | [x] COMPLETE | `chore(genesis)` (aaf37f0) | `.genesis/**`, invariants ×5, pytest re-slice | — |
| 5 | Product PRD + edge cases | [x] COMPLETE | `docs(product)` (ed7ac56) | PRD.md, edge_cases.md (EC-01…18) | — |
| 6 | Research passes R1/R2/R3 | [x] COMPLETE | `docs(research)` (39612c9) | datestamped addenda in `research/passes/` | — |
| 7 | Journal merge + gates | [x] COMPLETE | `docs(merge)` (2de6fa8) | journal/2026-08-08-merge.md, verified checklist | — |
| 8 | D4 system design + sprint plan | [ ] DONE — commit pending | `docs(d4)` (next) | `design/` (15 files verbatim + ADR-007 + sprint_plan.md), fixes per R3 | Commit; then POST-REVIEW — no Genesis M1 start until user approves |

## Post-merge sequence (design step ahead)
- Genesis M1–M2–M3 build loops use `pytest` commands; D6 build = the actual `src/memory_os` implementation. M4–M5 (lifecycle, obs) as follow-up slices per `design/sprint_plan.md`.
- Environment pre-flight for M1: install PostgreSQL 17 + pgvector locally, create `memoryos` DB, `.venv` + psycopg/sqlalchemy/pgvector + sentence-transformers (ADR-007).

## Completed Work
(Verified — do NOT redo.)
- [x] D1 reconstruction authored and verified in `D:\Abhii\Opencode\reconstruction\`: `01_problem.md`, `02_timeline.md`, `failure_analysis.md`, `first_principles.md`, `sources.md` + generated `problem_reconstruction.pdf` (6 pages), `historical_timeline.pdf` (4 pages). Contains C1–C8, R1–R8, 5 candidate approaches (A–E), evidence tags `[P:…]`/`[A:…]`/`[O]`.
- [x] Genesis scaffolded in `D:\Abhii\Opencode\.genesis` via kit `scaffold.sh` (files: PLAN.md, DONE.html, context-graph.json, IMMUNE.md, KICKOFF.md, LOOPS.md, MAPPING.md, README.md, implementation-notes.html, wiki/, decisions/, checkpoints/).
- [x] Old repo (`D:\Abhii\Projects\Conversational-Memory-Intelligence-System-`) inspected **read-only**; research weeks 1–4, naive_baseline, Design, .genesis identified.
- [x] Analysis: no mojibake in old repo files (`U+FFFD` scan clean).
- [x] Environment verified: Python 3.14 at `C:\Users\CR7\AppData\Local\Python\pythoncore-3.14-64\python.exe` (has markdown-it-py, pypdf), Python 3.11 at `C:\Users\CR7\AppData\Local\Programs\Python\Python311\python.exe` (default `python`), Node v24.14.0, Chrome 151 at `C:\Program Files\Google\Chrome\Application\chrome.exe`, Git Bash at `C:\Program Files\Git\bin\bash.exe`.
- [x] PDF pipeline proven with `build_pdfs.py` → 2 PDFs (uses markdown-it-py → styled HTML → Chrome headless `--print-to-pdf --no-pdf-header-footer`).
- [x] MemoryOS directory skeleton + `git init` (branch main) created (by user before this session).
- [x] This continuity checkpoint: docs/ + journal entries + README + AGENTS — committed as repo's **first commit**.

## Current Work
- Writing/verifying the continuity checkpoint (this task).
  - files being created: docs/SESSION_STATE.md, docs/PROJECT_MEMORY.md, CURRENT.md, docs/DECISIONS.md, journal/2026-08-08-session.md, PLAN.md, docs/RESUME.md, AGENTS.md, README.md, .gitignore
  - commands: `git -C D:\Abhii\Projects\MemoryOS add .`; `git commit -m "docs(continuity): persist session state and resume checkpoint"`
  - tests: none (no code in repo yet)
  - expected output: clean tree, first commit, fresh-agent resume success.

## Pending Work
Everything in `Overall Plan` above, in order (Phases 0→7); each phase = one commit; nothing has code yet.
- Immediately next: port `tools/build_pdfs.py` (from `C:\Users\CR7\AppData\Local\Temp\opencode\build_pdfs.py`) and prove Chrome package still renders; then proceed to Phase 1.

## Blockers
- Technical: scikit-learn/numpy NOT installed for Python 3.14 (needed Phase 3) — plan `.venv` install.
- Environment: default `python` on PATH = 3.11, cannot import pypdf/markdown-it (ModuleNotFoundError) — must call pythoncore-3.14 explicitly for PDF pipeline.
- Research uncertainty: RRF ~91% recall@10, PIIBench 0.96→0.18 OOD, "~40% queries fail pure vector" claims come from old repo research; unverified → Phase 6 R1 re-verifies before citing in deliverables.
- Decisions awaiting confirmation: NONE (all settled → DECISIONS.md).

## Decisions
ABBREVIATED — see `docs/DECISIONS.md` for full (Decision/Reason/Alternatives/Consequence). Current rulings:
- D-001 Single source of truth = this repo (MemoryOS)
- D-002 Python stack
- D-003 Local-only; no official LICENSE
- D-004 Old repo frozen/read-only (never write)
- D-005 D1 rigor = new-repo D1 + grafted old evidence; markdown is source truth; PDFs regenerate from markdown
- D-006 D2 research copied verbatim + `sources_catalog.md` hardening
- D-007 D3 naive baseline run for real (was never run); environment-jitter mitigation via min-of-5 latency samples
- D-008 D5 genesis spine adopted from old repo; milestones re-sliced to pytest/Python; invariants ×5 (3 old + 2 new: token budget per turn, PII pre/post guardrail)
- D-009 Product layer = `product/PRD.md` + `design/edge_cases.md`
- D-010 Local env conventions (Python 3.14 for PDFs, .venv for baseline)
- D-011..D-014 Merge discipline (evidence tagging, dated passes, per-phase commits, AI disclosure — journal/2026-08-08-merge.md)
- D-015 D4 adopted from old repo + fixes (sprint_plan.md added, ASI06→LLM-04/08, ADR-007)
- D-016 Prod-consistent storage: Postgres+pgvector only (no SQLite branch)

## Constraints
1. Old repo `D:\Abhii\Projects\Conversational-Memory-Intelligence-System-` is READ-ONLY forever — copy/read only, never write/edit.
2. `D:\Abhii\Opencode` is not a git repo and is unversioned — treat as import-source only; do not init git there.
3. No git remote, no LICENSE file, no secrets/.env in tree.
4. PDFs are generated FROM markdown (headed tool script), never hand-edited; approved formats: problem_reconstruction.pdf, historical_timeline.pdf.
5. Evidence discipline (handbook §12): every claim in deliverable docs tagged `[P: number]` (paper), `[A: …]` (assumption), `[O]` (observation) — baseline run absent, `[O]` only when verified.
6. Non-negotiable gates (handbook §F): citations present; naive baseline reproducible; tenant isolation tests; deletion tests; AI-assistance disclosure; D1–D8 deliverables all in `deliverables/` mirrors.
7. `tools/` scripts use Python 3.14 absolute path (not `python` on PATH).

## Constraints (from plan/D)
- Use only absolute paths everywhere in scripts (temp dir `C:\Users\CR7\AppData\Local\Temp\opencode` for scratch).
- Never modify `D:\Abhii\Opencode` (source), never modify old repo.
- Same env vs. pdf-gold: Chrome 151 flags `--headless --print-to-pdf --no-pdf-header-footer`; markdown-it-py 4.0.0 disable `linkify`.

## Invariants
To hold ALL implementation (check in Phase 4/5 gate):
- Tenant isolation is real (not just app-layer); include DB-level guarantee in D6 tests.
- User deletion propagates to consolidated/synth artifacts (memory of memories purge).
- Retrieval P95 under 150ms for moderate corpus (graded in D2 'industry' standard).
- Token-budget per turn enforced (new #4) — memory injections capped.
- PII pre/post guardrail (new #5) — PIIBench-style OOD drop (0.96→0.18) must be defended + tested.

## Acceptance Criteria
- Repo commit history: 1 commit per phase (7+), all checks green.
- Final acceptance checklist (handbook §F) shows every D (D1–D8) with **artifacts** marked COMPLETE + verification-of artifacts (PDF pipeline report, baseline results + tests, memory leak test)
- `docs/SESSION_STATE.md` + `CURRENT.md` are the canonical handoff — verified at end to be current.
- Answer to "can a fresh session continue from repo alone": YES (verified after each checkpoint).

## Important Files
| File | Purpose | Status |
|---|---|---|
| `docs/SESSION_STATE.md` | canonical state | committed (this checkpoint) |
| `docs/PROJECT_MEMORY.md` | durable knowledge | committed |
| `docs/DECISIONS.md` | decision log D-001–009 | committed |
| `docs/RESUME.md` | shortest handoff | committed |
| `CURRENT.md` | "where are we right now" | committed |
| `journal/2026-08-08-session.md` | chronological session log | committed |
| `PLAN.md` | phase plan + statuses | committed |
| `AGENTS.md` | continuity rules (this tool's context) | committed |
| `README.md` | project overview | committed |
| `.gitignore` | ignore rules (Python/build) | committed |
| `tools/build_pdfs.py` | PDF pipeline (planned port) | PLANNED (Phase 0) |
| `D:\Abhii\Opencode\reconstruction\*` | merged D1 source (unversioned, import-only) | source |
| `D:\Abhii\Projects\Conversational-Memory-Intelligence-System-` experimentation/research | read-only inputs | external |

## Commands
- Checkpoint/status: `git -C D:\Abhii\Projects\MemoryOS status` / `git -C … log --oneline` / `git -C … rev-parse HEAD`
- Chrome PDF: `& "C:\Program Files\Google\Chrome\Application\chrome.exe" --headless=new --disable-gpu --no-pdf-header-footer --print-to-pdf="out.pdf" "file:///…html"`
- Python PDF build: `& "C:\Users\CR7\AppData\Local\Python\pythoncore-3.14-64\python.exe" tools/build_pdfs.py`
- Baseline venv: `& python3.14 -m venv .venv` then `.venv\Scripts\pip install scikit-learn numpy`
- Git Bash (genesis tooling): `& "C:\Program Files\Git\bin\bash.exe" -lc "bash tools/scaffold.sh …"`
- M1 pre-flight (Postgres): install PostgreSQL 17 + pgvector, `psql -U postgres -c "CREATE DATABASE memoryos;"`; record connection string here (never in code)

## Test Status
- No implementation code yet — repository is design-complete (D1–D4 docs). Planned suite: `pytest tests/test_db.py` (G-M1), `tests/test_retrieval.py` (G-M2), `tests/test_admission.py` + `tests/test_context.py` (G-M3), plus PDF smoke via build_pdfs.

## Research Status
- Sources checked (old repo + handbook): weeks 1–4 landscape, RRF/BLER, naive TF-IDF+cosine, PII benchmark notes.
- Claims VERIFIED: tool-chain works, no mojibake, Chrome path OK. **Phase 6 passes DONE (2026-08-08): R1** citations/claims (11/11 papers verified; 2 claim edits — "~40% dense-fail" NOT in RAG paper: practitioner-origin; Generative Agents terms corrected to reflection/summarization); **R2** D4-readiness (LoCoMo ACL-2024 + SOTA numbers, Mem0 graph + expiration, Letta v0.16.8, Zep/Graphiti bi-temporal, RRF k=60 with 91%@10 corrected to Supermemory practitioner blog, pgvector HNSW 10–60ms @ 1M–10M vec, MIRIX = memory-system paper not a benchmark); **R3** product (name corrected: Supermemory; OWASP LLM Top 10 2025 = LLM01–LLM10, no ASI06 — cite LLM04/LLM08; **applied to D4 threat_model.md + ADR-004 during D4 phase**).
- Unverified items remaining: PIIBench 0.96→0.18 OOD figure (flagged in catalog for D6-era verification).
- Conclusions: memories = admission + retention + ranking + life cycle; retrieval = hybrid dense+sparse+RRF; naive gap demonstrated by baseline (falsification recorded).

## Git State
- branch: main
- latest commit: `39612c9` (Phase 6 `docs(research): verification passes R1-R3`), then `2de6fa8` (Phase 7 `docs(merge): final journal + end-of-merge checks`)
- uncommitted: Phase 8 (D4) in progress → design copy + fixes + sprint_plan + ADR-007
- what to commit next: D4 (`docs(d4): system design + sprint plan`) as commit #9

## Resume Instructions
To resume this project:
1. Read `docs/RESUME.md` (1 page, mandatory first)
2. Read `docs/SESSION_STATE.md` (this file)
3. Read `CURRENT.md` (exact next step)
4. Read `PLAN.md` (full priorities)
5. Read latest journal (`journal/2026-08-08-session.md`)
6. Run `git -C D:\Abhii\Projects\MemoryOS status` (expect clean / M docs)
7. Inspect `D:\Abhii\Projects\MemoryOS` tree
8. Continue from the "Exact point where execution resumes" (Phase 1, D1 merge)
9. DO NOT redo completed work (verified list above)
10. Verify Python 3.14 path & Chrome path (see Commands) before any PDF work

## Compaction Protocol (AGENTS.md)
- The repo docs retain the source of truth. If chat context was lost, revert to RESUME/SESSION/CURRENT and do not re-derive.
- Always update CURRENT.md + journal when a milestone/phase milestone lands; commit per phase.