# Decision Log

> Format per IMP.md. Status: ACCEPTED / SUPERSEDED / REJECTED. Only durable architectural/product/research decisions. Trivial implementation details are not logged.

---

## D-001 — MemoryOS = single source of truth (new repo)

Date: 2026-08-08
Status: ACCEPTED

### Decision
Create a fresh repo `D:\Abhii\Projects\MemoryOS` as the canonical home for ALL deliverables and product work. Old repo (`Conversational-Memory-Intelligence-System-`) and `D:\Abhii\Opencode` are **sources only**.

### Context
Three codebodies existed in parallel (old course repo, Opencode D1 work, uncreated repo). The old repo is read-only per user mandate; Opencode is not a git repo and is unversioned.

### Alternatives
- Something with Opencode as the repo → not a git repo, would dupe state into two repos.
- Merge old repo in place → violates READ-ONLY mandate; history pollution.

### Why
Clean, verifiable, local-only git history; complies with read-only mandate; handbook 10-dir skeleton.

### Consequences
ALL commits land in MemoryOS. Old repo & Opencode are import-source archives only. Anyone must never write to them.

---

## D-002 — Python implementation stack

Date: 2026-08-08
Status: ACCEPTED

### Decision
All implementation (baseline, core library, tests, PDF pipeline) is **Python 3.11+** (pinned to pythoncore-3.14 for PDF tooling, see D-007/notes).

### Context
Old repo plan was TypeScript/npm; baseline code is Python (TF-IDF + cosine). Environment has Python 3.11 + 3.14 available; best shim for pytest, pgvector bindings, scientific stack.

### Alternatives
TypeScript (old repo plan) — inferior for linear algebra/embeddings; Java — overhead; Go — fine but obtuse for this domain.

### Why
Fastest path to a running documented baseline; research-grade reproducibility; ecosystem alignment with the field.

### Consequences
- D5 demo commands = `pytest ...`; D6 tests in Python.
- Python 3.14 pythoncore for PDF (pypdf/markdown-it); Python 3.11 for baseline/文 venv (scikit-learn) — see D-007 note.

---

## D-003 — Local-only git; no official LICENSE

Date: 2026-08-08
Status: ACCEPTED

### Context
Course work; no remote requested; user confirmed no license file.

### Decision
- No remote, no GitHub; `git` local only, commits per phase.
- No LICENSE file in repo (user confirmation).

### Alternatives
Adding remote (rejected — not requested), MIT license (rejected — user decision to keep private coursework).

### Consequences
- Fresh clones from nowhere; recovery strictly via git local history. Branch `main` only.

---

## D-004 — Old repo frozen (READ-ONLY), PDFs regenerated from markdown

Date: 2026-08-08
Status: ACCEPTED

### Decision
- Old repo: copy-in source only; ANY write is prohibited (finder/journal/tests).
- PDF deliverables are ALWAYS generated from markdown (script `tools/build_pdfs.py` + Chrome headless); never hand-edit binaries.

### Context
Old repo holds 4 research weeks + naive baseline; Opencode holds rigorous D1. PDFs there are stale; they must match the merged markdown "source of truth".

### Alternatives
- Editing PDF binaries directly → rejected (byte fragmentation).
- Porting stale PDFs → rejected (out-of-date with new D1).

### Consequences
Source markdown is definitive; PDFs regenerated at every phase boundary. Nothing may depend on the old repo being mutated.

---

## D-005 — D1: new-repo rigor + grafted old evidence; markdown is source truth

Date: 2026-08-08
Status: ACCEPTED

### Decision
Merged `reconstruction/01_problem.md` … `first_principles.md` (from Opencode) is the D1 canonical text; append old repo's personal `[O]` evidence rows and "stage→requirement" mapping into `first_principles.md`.

### Context
New D1 (this session) already rigorous (C1–C8, R1–R8, approaches A–E, tags); old repo provided an underexisting map.

### Alternatives
- Use old D1 as-is (3-page, no tags; fell short); use Opcode D1 alone (missing old personal evidence).

### Consequences
Single authored D1 with both rigor and personal experience; PDFs generated from it.

---

## D-006 — D2: research preserved verbatim + catalog

Date: 2026-08-08
Status: ACCEPTED

### Context
Old repo has the deepest months-long research (weeks 1–4: landscapes, databases, RRF/BLER, naive baseline study). Best to keep it intact and add hardening.

### Decision
Copy `research/**` from old repo verbatim into `research/`; add `research/sources_catalog.md` (field map — Mem0, Zep, Letta, Cognee, LangMem, MIRIX, A-MEM, Supermemory, OWASP ASI06, PIIBench, MemoryGraft, MINJA, Cisco MemoryTrap, pgvector/FAISS/RRF) + `research/README.md`.

### Alternatives
Resurface → loss; re-derive → waste.

### Consequences
Research credibility + production-grade citations; catalog enables R1 verification pass (Phase 6).

---

## D-007 — D3: run the naive baseline for real (never run before)

Date: 2026-08-08
Status: ACCEPTED

### Context
Old repo contains `experiments/naive_baseline/` (dataset.py, inject.py, memory_store.py, retrieve.py, run_baseline.py) that was **never executed** (no results committed).

### Decision
- Create `.venv` with scikit-learn + numpy.
- Execute `run_baseline.py` → produce `baseline_results.csv`, `error_examples.jsonl`, `summary.json`.
- Write `baseline_protocol.md` (fairness scoping: TF-IDF single-signal), `productive_failure_report.pdf` (failure taxonomy + falsification of "memories persist" assumption), `assumption_to_result.md` (map every `[A:…]` from D1 → result).
- Latency sampling technique: **min-of-5** reads per query (env jitter mitigation).

### Alternatives
- Skip (would fail handbook D3 gate).
- TypeScript baseline (waste — old code already Python).

### Consequences
First real numbers for the "problem + falsification" story; reproducible per gate.

---

## D-008 — D5 Genesis spine adopted + Python re-slice

Date: 2026-08-08
Status: ACCEPTED

### Context
Old repo `.genesis` (DONE.html/PLAN.md/context-graph.json) is *initialized* (approach chosen, invariants). Course handbook requires D5 to happen at design-frozen stage; implementation must be test-first demo commands.

### Decision
- Adopt old `.genesis` into MemoryOS `.genesis` (in board), PEDIT for Python/pytest, reset CURRENT + KICKOFF.
- Keep 3 existing invariants (tenant isolation, deletion, retrieval perf <150ms).
- ADD 2 invariants: (4) token-budget-per-turn enforcement; (5) PII pre/post guardrail.
- Zero build loops until design (D4) settles — milestones M1–M3 exist but nothing runs before D6.

### Alternatives
Override from scratch (waste), or use Preserve old school (TypeScript tasks) — re-slice.

### Consequences
- Demo commands = `pytest` — eventually runnable; Genesis = the machine-readable plan; new invariants bound design.

---

## D-010 — Local-only env conventions

Date: 2026-08-08
Status: ACCEPTED

### Decision
- All scripts use **absolute paths** (scratch at `C:\Users\CR7\AppData\Local\Temp\opencode`).
- # PDF pipeline uses Python 3.14 absolute path; never `python` on PATH (no pypdf module → ModuleNotFoundError).

### Context
Determined during environment verification (2026-08-08): the default `python` (3.11) cannot import pypdf/markdown-it; the 3.14 pythoncore can.

### Consequences
- Deterministic across sessions; know: use 3.14 for PDF build, and install scikit-learn only inside `.venv` for baseline (see D-007).

---

## D-009 — Product layer: PRD + edge-case ledger

Date: 2026-08-08
Status: ACCEPTED

### Context
This is also a **product concept** (MemoryOS), not just homework; product surface must be designed together with D signs.

### Decision
Create `product/PRD.md` (vision, personas, R1–R8 as capabilities, competitive positioning from research) and `design/edge_cases.md` (leaf of supersession/contradiction/deletion/injection etc. — mapped to R-capabilities and to D6 acceptance tests).

### Consequences
- D4 design derives directly from PRD surfaces; edge-case ledger = quality gate for D6.

---

## D-015 — D4: adopt old-repo design + local embeddings

Date: 2026-08-08
Status: ACCEPTED

### Context
User provided a near-complete D4 in the old repo (`design/`, authored with an external LLM): three-part system design (sections 1–16), data model, API contracts, threat model, 6 ADRs, and 3 rendered PDFs (system_design 15p, architecture 4p, data_flow 4p). Handbook artifact `sprint_plan.md` was missing everywhere — not only in the old repo. Verification pass R3 (2026-08-08) also proved the old draft's "OWASP 2026 ASI06" citation is wrong (no such taxonomy slot; memory risk = LLM-04/LLM-08).

### Decision
- Copy the old D4 set **verbatim** into `MemoryOS/design/` (byte-identical, hash-verified) + `decision_records/` (15 files).
- Rework only what MemoryOS needs: (1) create `design/sprint_plan.md` mapping D4 §15 M1–M7 onto Genesis M1–M3; (2) fix the ASI06→LLM-04/LLM-08 citations in `threat_model.md` + ADR-004 (per R3); (3) add ADR-007 (local deterministic embeddings, 384-d) and dimension note to `data_model.md` (prod-consistent, no external service); (4) harmonize Genesis M1 schema language with the single `memories` table.
- Stack: **Postgres+pgvector only** (no SQLite dev branch) per user's prod-consistency decision.

### Alternatives
- Re-draft D4 from scratch (waste of reviewed work); copy and reuse with evidence (chosen).

### Consequences
- D4 = single committed artifact set in MemoryOS; PDFs remain byte-identical originals (authored evidence), MD sources adapted + documented; Genesis M1–M3 re-sliced consistently with the design.

---

## D-016 — Prod-consistent storage: Postgres+pgvector only

Date: 2026-08-08
Status: ACCEPTED

### Context
User: "Do what we will be doing in PROD, keep consistency all over." Approach B (PG + pgvector) is the chosen architecture (`.genesis/PLAN.md`). Old plan mentioned "SQLite dev / Postgres prod" — rejected for consistency.

### Decision
Postgres 17 + pgvector are the **only** storage stack across dev, test, and prod; no SQLite branch anywhere in the codebase. Install + local `memoryos` database is part of G-M1 pre-flight (before first test run).

### Consequences
- No environment drift; invariants (tenant isolation, latency <150ms) measured against the real engine; `sprint_plan.md` G-M1 loads pgvector into the CI-equivalent run.