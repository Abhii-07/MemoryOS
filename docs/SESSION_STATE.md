# Session State

> Canonical, machine-readable/human-readable state of this project. **The repository is the source of truth, not chat context.** If any file contradicts this one, SESSION_STATE.md wins (and the contradiction must be fixed).

## Last Updated
- Date/time: 2026-08-08 13:45 (local)
- Current git branch: `main`
- Current commit SHA: `docs(continuity)` initial commit (see Git State; SHA filled at first commit)

## Project
- Project name: **MemoryOS** (course deliverable: *Conversational Memory Intelligence System*)
- Overall objective: Build, from first principles, a production-grade conversational-memory system — persistent, retrievable, deletable memory for an AI assistant — delivered as a research-grade course repo (D1–D8) AND a coherent product ("MemoryOS").
- Current milestone: none started (repository bootstrap in progress); see "Current Phase".

## Current Phase
- Phase number: **0 (bootstrap)** — partially done, checkpoint being committed
- Phase name: Bootstrap MemoryOS repository
- Current task: Continuity checkpoint per `IMP.md` (context-preservation workflow) — create continuity docs, verify, commit
- Current subtask: writing docs/SESSION_STATE.md, PROJECT_MEMORY.md, CURRENT.md, DECISIONS.md, journal, PLAN.md, RESUME.md, AGENTS.md; README.md + .gitignore
- **Exact point where execution resumes after this commit:**
  1. Phase 0 remainder: port PDF build script + verify (see PLAN.md Phases)
  2. Phase 1: merge D1 reconstruction (copy from `D:\Abhii\Opencode`) → PDFs
  3. Then Phase 2…, each commits separately

## Overall Plan
| Phase | Name | Status | Relevant commit (planned) | Important artifacts | Remaining work |
|---|---|---|---|---|---|
| 0 | Bootstrap + checklist | [-] IN PROGRESS | `docs(continuity)` (this commit); `chore: bootstrap` (partial) | dirs, git init (done by user), plan/checkpoint docs (this commit) | README/.gitignore/AGENTS (in this commit), port `tools/build_pdfs.py` from temp build script; verify PDF pipeline |
| 1 | D1 merged reconstruction | [ ] NOT STARTED | `feat(d1): merged reconstruction` | `reconstruction/01_problem.md` … `04_first_principles.md`, `sources.md`, two PDFs | Copy from `D:\Abhii\Opencode\reconstruction` (already rigorous) + graft old-repo evidence + regenerate PDFs |
| 2 | D2 research copy + catalog | [ ] NOT STARTED | `feat(d2): research weeks 1-4 + sources catalog` | `research/**` (verbatim from old repo), `research/sources_catalog.md`, `research/README.md` | Copy old repo `research/` verbatim; write catalog |
| 3 | D3 baseline run | [ ] NOT STARTED | `feat(d3): baseline run + reports` | `experiments/naive_baseline/` run, `baseline_results.csv`, `error_examples.jsonl`, `summary.json`, `baseline_protocol.md`, `productive_failure_report.pdf` | Create .venv, install scikit-learn+numpy, run `run_baseline.py`, write protocol + report |
| 4 | D5 Genesis spine | [ ] NOT STARTED | `chore(genesis): spine initialized for MemoryOS` | `.genesis/**` (from old repo), MAPPING.md, reset CURRENT/KICKOFF | Copy `D:\Abhii\Opencode\.genesis` old spine; re-slice M1–M3 to Python/pytest demo commands; keep Approach-B brainstorm; invariants ×5; zero build loops until D4/D6 |
| 5 | Product PRD + edge cases | [ ] NOT STARTED | `docs(product): PRD + edge cases` | `product/PRD.md`, `design/edge_cases.md` | Write PRD (R1–R8 → product capabilities) + exhaustive edge-case ledger mapped to R-capabilities and D6 acceptance tests |
| 6 | Research passes R1/R2/R3 | [ ] NOT STARTED | `docs(research): verification passes` | dated addenda in `research/**` | R1 claim/citation verification, R2 D4-readiness (LoCoMo, Mem0, Letta, Zep, RRF %, pgvector ANNS), R3 product position |
| 7 | Journal merge + gates | [ ] NOT STARTED | `docs(research): …` | `journal/2026-08-08-merge.md` (AI-assistance disclosure) | end-of-merge verification (PDF pipeline, baseline rerun, placeholder scan, dir diff, handbook §F checklist) |

## Completed Work
(Verified — do NOT redo.)
- [x] D1 reconstruction authored and verified in `D:\Abhii\Opencode\reconstruction\`: `01_problem.md`, `02_timeline.md`, `03_failure_analysis.md`, `04_first_principles.md`, `sources.md` + generated `problem_reconstruction.pdf` (6 pages), `historical_timeline.pdf` (4 pages). Contains C1–C8, R1–R8, 5 candidate approaches (A–E), evidence tags `[P:…]`/`[A:…]`/`[O]`.
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
- D-008 D5 genesis spine adopted from old repo; milestones re-sliced to pytest/Python; invariants ×5 (3 old + 2 new: token-budget per turn, PII pre/post guardrail)
- D-009 Product layer = `product/PRD.md` + `design/edge_cases.md`

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
- Python PDF build (after Phase 0): `& "C:\Users\CR7\AppData\Local\Python\pythoncore-3.14-64\python.exe" tools/build_pdfs.py`
- Phase 3 venv: `& python3.14 -m venv .venv` then `.venv\Scripts\pip install scikit-learn numpy`
- Git Bash (for genesis tooling): `& "C:\Program Files\Git\bin\bash.exe" -lc "bash tools/scaffold.sh …"`

## Test Status
- None run yet (no code). Planned: pytest suite for baseline + memory ops (Phase 3/4); PDF HTML->PDF smoke via headers/footer check.

## Research Status
- Sources checked (old repo + handbook): weeks 1–4 landscape, RRF/BLER, naive TF-IDF+cosine, PII benchmark notes.
- Claims VERIFIED (this session): tool-chain works (baseline never run; python3.14 present), no mojibake, Chrome path OK.
- Claims needing verification (Phase 6 R1–R3): ~40% dense fail, 91% recall@10 RRF, PIIBench 0.96→0.18, production page-rank/hybrid superiority.
- Conclusions (preliminary, for D1–D3): memories = retrieved + injected + consolidated; retrieval = hybrid dense+sparse+RRF (design), naive gap demonstrated by baseline.

## Git State
- branch: main
- latest commit: (none until this checkpoint; then `docs(continuity)`)
- uncommitted: everything in this checkpoint -> commit now
- what to commit next: Phase 0 remaining files (tools/build_pdfs.py) then Phase 1 artifacts.

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