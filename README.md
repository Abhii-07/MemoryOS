# MemoryOS

**Persistent memory for AI assistants** — a deterministic conversational-memory
engine where memories are stored, retrieved, updated, consolidated, and
deleted per user intent. No LLM calls on any write/read/delete path:
everything is reproducible, testable, and safe by construction.

> MemoryOS began as a research-grade engineering project (first-principles
> reconstruction → research → baseline → design → build) and is now a working
> system with a full test gate and an adversarial-security replay suite. The
> repository keeps the whole journey visible: design docs, research catalog,
> failure analysis, and engineering logs alongside the code.

## Why it exists

Assistants forget. MemoryOS gives an AI assistant a real memory system:

- **Write** — a turn is classified (ADD / UPDATE / DELETE / NOOP) without
  any LLM, and personally-identifiable content is scrubbed before storage.
- **Read** — hybrid retrieval (BM25 + dense embeddings + RRF fusion) with
  provenance-weighted ranking: what *you* stated always outranks what the
  assistant inferred.
- **Update** — correcting a fact supersedes the old one by slot key; derived
  summaries are consolidated along the lineage.
- **Delete** — deletion propagates through derived rows via a propagation
  queue, so a forgotten fact never resurfaces.
- **Contain** — tenant isolation at the database level; malicious directives
  hidden in retrieved text (MemoryGraft/MINJA-class attacks) are stored
  verbatim but inert.

Against the D3 naive baseline, MemoryOS turns 33% contradiction, 50%
cold-start false positives, and 100% sensitive-content leakage into
**0% / 0% / 0%** — with precision@1 at 1.0 and p95 latency well under the
150 ms budget.

## Repo layout

```
implementation/MemoryOS-App/   the application (src, tests, bench, audit policy, venv)
  src/memory_os/               db · admission · retrieval · context · lifecycle · observability
  tests/                       8 gate files, 97 tests
  bench/                       D3 acceptance replay + latency profiling
docs/                          setup guide, decisions, continuity docs
design/                        system design (3 parts), data model, API contracts, threat model, ADRs
research/                      landscape review + sources catalog
reconstruction/                first-principles problem reconstruction
experiments/                   naive baseline: protocol, results, failure analysis
product/                       PRD + product narrative
journal/                       engineering session logs
.genesis/                      build-planning spine (LOOPS, context graph)
```

## Setup & run

Requires **Windows 10/11 + PowerShell**, **Python 3.11+** (project uses 3.14),
and **PostgreSQL 17 + pgvector** (portable install, no admin rights needed).
Full human-friendly instructions: [`docs/SETUP_AND_RUN.md`](docs/SETUP_AND_RUN.md).

```powershell
# 0. Portable Postgres 17 + pgvector — see docs/SETUP_AND_RUN.md §2 (install dir is
#    your choice; the guide uses $PGROOT\17 and $PGROOT\data)
#    venv (inside the app):
cd implementation\MemoryOS-App
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

# 1. Start the server (detached, so it survives the shell session)
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
  CommandLine = '"<PGROOT>\17\bin\pg_ctl.exe" -D "<PGROOT>\data" -l "<PGROOT>\data\postgres.log" start' }
& "<PGROOT>\17\bin\pg_isready.exe" -h localhost -p 5432

# 2. Run the gates (97 tests)
$env:MEMORYOS_DB_DSN="postgresql://memoryos@localhost:5432/memoryos"
.venv\Scripts\python.exe -m pytest -q

# 3. D3 acceptance replay (all Deliverable targets)
.venv\Scripts\python.exe -m bench.acceptance

# 4. Latency profile (EC-15, p95 budget < 150 ms)
.venv\Scripts\python.exe -m bench.latency_profile --rows 500 --queries 30
```

The embedding model (`all-MiniLM-L6-v2`) downloads once on first run
(~80 MB, stored in `.hf-cache/` next to the app); afterwards everything
works offline.

**Architecture:** PostgreSQL 17 + pgvector · hybrid retrieval (BM25 + dense
`all-MiniLM-L6-v2` + RRF k=60) · deterministic admission (ADD/UPDATE/DELETE/NOOP)
· slot-key supersession · zone-budgeted context injection · lineage-based
delete propagation · typed trace spans with collector-level redaction ·
config-as-code audit gate.

## Status

- **Build:** milestones G-M1…G-M6 implemented and green — 97 tests, D3
  acceptance replay PASS (all targets), audit gate 8/8, DB left empty after
  runs. See `design/sprint_plan.md`.
- **Roadmap:** interactive documentation site (design/research/metrics
  dashboards); product-grade branching (curated `main` + protected `develop`);
  packaging and API surface.

## Key docs

- `docs/RESUME.md` — shortest handoff
- `docs/SESSION_STATE.md` — canonical state
- `docs/DECISIONS.md` — design decisions D-001…
- `design/sprint_plan.md` — milestone map with demo commands

## Note

No license file — all rights reserved (see your jurisdiction's defaults).
No CI configured; nothing here is affiliated with any company.