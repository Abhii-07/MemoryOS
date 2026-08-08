# MemoryOS — Implementation Plan

> One plan, machine-parseable. Statuses: `[ ] NOT STARTED` · `[-] IN PROGRESS` · `[x] COMPLETE` · `[!] BLOCKED`.
> Nothing is COMPLETE until verified. Full narrative in `docs/SESSION_STATE.md`; the shortest handoff is `docs/RESUME.md`.

**Project:** MemoryOS — conversational memory intelligence system (course D1–D8 + product).
**Constraint highlights:** old repo `Conversational-Memory-Intelligence-System-` READ-ONLY; local-only git; no LICENSE; every claim tagged `[P]/[A]/[O]`.

---

## Phase 0 — Bootstrap MemoryOS repository

**Objective:** Repo skeleton + continuity checkpoint + build tooling, so any fresh session can resume from files alone.

**Deliverables:** `README.md`, `AGENTS.md`, `.gitignore`, 10 skeleton dirs (exist), `tools/build_pdfs.py` (port), `docs/*` continuity set, `journal/`, `CURRENT.md`, `PLAN.md`.

**Acceptance criteria:**
- `git status` clean after commit; `docs(continuity)` is the FIRST commit (single commit).
- Fresh agent can resume (verified via RESUME/SESSION/CURRENT reading).
- PDF pipeline verified (builds one smoke PDF from a fixture).

**Dependencies:** none.

**Status:** [-] IN PROGRESS — dirs + git init done (user); continuity docs being written now; port of `build_pdfs.py` REMAINING (plus smoke test).

---

## Phase 1 — D1 Merged Reconstruction

**Objective:** Final D1 (problem reconstruction) as merged text; regenerate both PDFs from the merged markdown (source of truth = md).

**Deliverables:** `reconstruction/01_problem.md` (incl. old-repo `[O]` personal evidence), `02_timeline.md`, `failure_analysis.md`, `first_principles.md` (incl. stage→requirement table + OQ9 user memory controls), `sources.md`; PDFs `problem_reconstruction.pdf`, `historical_timeline.pdf`.

**Acceptance criteria:**
- All claims tagged; hand-crafted approach list A–E with reasoning.
- PDFs regenerated (6p + 4p); page counts match; no placeholder text anywhere.

**Dependencies:** Phase 0 (tools).

**Status:** [ ] NOT STARTED

---

## Phase 2 — D2 Research Copy + Sources Catalog

**Objective:** Preserve 4 weeks of research verbatim; harden with catalog for citation verification.

**Deliverables:** `research/**` (verbatim copy of old repo weeks 1–4), `research/sources_catalog.md`, `research/README.md`.

**Acceptance criteria:** byte-identical copy to old repo (except README/catalog); catalog links every tool/paper (Mem0, Zep, Letta, Cognee, LangMem, MIRIX, A-MEM, Supermemory, OWASP ASI06, PIIBench, MemoryGraft, MINJA, Cisco MemoryTrap, pgvector/FAISS/RRF).

**Dependencies:** none.

**Status:** [ ] NOT STARTED

---

## Phase 3 — D3 Naive Baseline: first real run

**Objective:** Prove the naive baseline quantitatively; produce falsification story.

**Deliverables:** `.venv` (scikit-learn, numpy), `experiments/naive_baseline/` port, `baseline_results.csv`, `error_examples.jsonl`, `summary.json`, `baseline_protocol.md`, `productive_failure_report.pdf`, `assumption_to_result.md` (map `[A:…]` → results).

**Acceptance criteria:**
- Run completes; artifacts exist and are committed.
- Report quantifies gap vs hybrid (claims cited) and records min-of-5 latency sampling (env jitter mitigation).
- Reproducible: rerun yields same headline numbers (documented in protocol).

**Dependencies:** Python 3.11 `.venv` creation.

**Status:** [ ] NOT STARTED

---

## Phase 4 — D5 Genesis Spine (initialized)

**Objective:** Ship the initialized Genesis spine (plan, invariants, milestones) re-sliced to Python/pytest demo commands.

**Deliverables:** `.genesis/**` (from old repo + adaptation): PLAN.md, DONE.html, context-graph.json (5 invariants: #1 tenant isolation, #2 deletion guarantee, #3 retrieval <150ms, #4 token-budget per turn, #5 PII pre/post guardrail), MAPPING.md, README.md; reset `CURRENT.md`/`KICKOFF.md`.

**Acceptance criteria:**
- Milestones M1–M3 have exact `pytest`/python demo commands; freeze boundaries.
- `git` shows genesis content committed under `chore(genesis)`.
- Zero build loops until design frozen (D4/D6).

**Dependencies:** Phase 2 (research informs approach).

**Status:** [ ] NOT STARTED

---

## Phase 5 — Product: PRD + Edge-Case Ledger

**Objective:** Product layer (MemoryOS) + exhaustive edge-case ledger mapped to R-capabilities and D6 tests.

**Deliverables:** `product/PRD.md` (vision, personas, R1–R8 as capabilities, competitive context), `design/edge_cases.md` (supersession, contradiction, consent change, deletion propagation, cross-client adversarial similarity, MemoryTrap injection, PIIBench OOD, cold start, empty vocab, zone overflow, concurrent writes, error reinforcement, no-relevant-memory).

**Acceptance criteria:** every edge case has: trigger, expected behavior, mapped requirement, D6 test reference.

**Dependencies:** research (Phase 2).

**Status:** [ ] NOT STARTED

---

## Phase 6 — Research Verification Passes (R1–R3)

**Objective:** Verify/cite every claim used in deliverables; de-risk D4 design.

**Deliverables:** dated addenda in `research/` (R1 claim/citation verify; R2 D4-readiness: LoCoMo, Mem0 evolution, Letta, Zep, RRF %, pgvector ANNS at scale; R3 product positioning/API/retention).

**Acceptance criteria:** no uncited claim in any deliverable; each pass updates `research_landscape.md`.

**Dependencies:** Phase 2.

**Status:** [ ] NOT STARTED

---

## Phase 7 — Final Journal Merge + Acceptance Gates

**Objective:** Close out the merge: AI-assistance disclosure, end-of-merge verification, handbook §F gate.

**Deliverables:** `journal/2026-08-08-merge.md` (disclosure + merge decisions), verification report (PDF pipeline recheck, baseline rerun, placeholder scan, dir diff vs old repo).

**Acceptance criteria:**
- All phases `[x]`; §F checklist green; every deliverable tagged; docs consistent; single clean history (commits per phase).
- Answer "can fresh session continue?" == YES (verified).

**Dependencies:** Phases 1–6.

**Status:** [ ] NOT STARTED

---

## Commit Map (planned order)

1. `docs(continuity): persist session state and resume checkpoint` — Phase 0 (this session)
2. `chore: port PDF build tooling` (or merged into #1 — see status note) — Phase 0
3. `feat(d1): merged reconstruction` — Phase 1
4. `feat(d2): research weeks 1-4 + sources catalog` — Phase 2
5. `feat(d3): baseline run + reports` — Phase 3
6. `chore(genesis): spine initialized for MemoryOS` — Phase 4
7. `docs(product): PRD + edge cases` — Phase 5
8. `docs(research): verification passes` — Phase 6
9. `docs(handoff): merge journal + gates` — Phase 7