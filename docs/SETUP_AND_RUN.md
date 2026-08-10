# Setup & Run Guide — MemoryOS

> Written for a human with no AI agent. Copy-paste everything below.
> Last updated: 2026-08-09 (G-M5 gate). Later gates append their docs here.

Everything in this repo is local: Postgres 17 + pgvector, a Python venv, and `pytest`
gates. No admin rights, no Docker, no WSL, no cloud account, no AI needed.

---

## 1. Prerequisites

- Windows 10/11, PowerShell
- Python 3.11+ installed (`py -3` to check). This project uses **Python 3.14** — any 3.11+ works.
- ~700 MB free disk for Postgres + the data cluster.

---

## 2. Install Postgres 17 + pgvector (portable, no admin)

We use the portable binaries because the machine has no admin rights and no Docker.

### 2.1 Postgres 17.10 (EDB binaries)

```powershell
# Create the target dir and download
New-Item -ItemType Directory -Force -Path "C:\Users\CR7\Postgres" | Out-Null
$zip = "C:\Users\CR7\AppData\Local\Temp\opencode\postgresql-17.10-2-windows-x64-binaries.zip"
Invoke-WebRequest "https://get.enterprisedb.com/postgresql/postgresql-17.10-2-windows-x64-binaries.zip" -OutFile $zip

# Extract (the zip unpacks a `pgsql` folder — we land it at C:\Users\CR7\Postgres\17)
Expand-Archive -Path $zip -DestinationPath "C:\Users\CR7\Postgres" -Force
Rename-Item "C:\Users\CR7\Postgres\pgsql" "C:\Users\CR7\Postgres\17"

# Verify
& "C:\Users\CR7\Postgres\17\bin\pg_config.exe" --version   # → PostgreSQL 17.10
```

### 2.2 pgvector (Windows prebuilt, 0.8.6 for PG 17)

conda-forge has no matching Windows build; compile-from-source needs MSVC. Use the prebuilt release:

```powershell
$v = "C:\Users\CR7\AppData\Local\Temp\opencode\vector.v0.8.6-pg17.zip"
Invoke-WebRequest "https://github.com/andreiramani/pgvector_pgsql_windows/releases/download/0.8.6_17/vector.v0.8.6-pg17.zip" -OutFile $v
Expand-Archive -Path $v -DestinationPath "C:\Users\CR7\AppData\Local\Temp\opencode\vector-extract" -Force

# Copy into the portable PG install
Copy-Item   "C:\Users\CR7\AppData\Local\Temp\opencode\vector-extract\vector.dll"  "C:\Users\CR7\Postgres\17\lib\" -Force
Copy-Item   "C:\Users\CR7\AppData\Local\Temp\opencode\vector-extract\vector.control" "C:\Users\CR7\Postgres\17\share\extension\" -Force
Copy-Item   "C:\Users\CR7\AppData\Local\Temp\opencode\vector-extract\vector--0.8.6.sql" "C:\Users\CR7\Postgres\17\share\extension\" -Force
Copy-Item   "C:\Users\CR7\AppData\Local\Temp\opencode\vector-extract\vector.h" "C:\Users\CR7\Postgres\17\include\server\extension\" -Force
```

(The prebuilt zip must match your PG major version — `0.8.6_17` → PG 17.)

### 2.3 Initialize the cluster

```powershell
& "C:\Users\CR7\Postgres\17\bin\initdb.exe" -D "C:\Users\CR7\Postgres\data" -U memoryos --auth=trust --encoding=UTF8 --locale=C
```

Creates a data cluster owned by the superuser `memoryos` with trust auth (local dev only).

---

## 3. Start the server (the non-obvious part)

**Gotcha:** if you start Postgres from a terminal session that ends (or an automation
tool that kills its child processes on timeout), the postmaster dies with error
`0xC0000142`. Start it **detached** so it survives:

```powershell
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
  CommandLine = '"C:\Users\CR7\Postgres\17\bin\pg_ctl.exe" -D "C:\Users\CR7\Postgres\data" -l "C:\Users\CR7\Postgres\data\postgres.log" start'
}
$r.ProcessId   # parent process id; postmaster is a child of it
```

Checks:

```powershell
& "C:\Users\CR7\Postgres\17\bin\pg_isready.exe" -h localhost -p 5432   # → accepting connections
Get-Content "C:\Users\CR7\Postgres\data\postmaster.pid" | Select-Object -First 1   # → server PID
```

Stop the server (when needed):

```powershell
& "C:\Users\CR7\Postgres\17\bin\pg_ctl.exe" -D "C:\Users\CR7\Postgres\data" stop
```

---

## 4. Create the database + vector extension (once)

```bash
& "C:\Users\CR7\Postgres\17\bin\psql.exe" -h localhost -p 5432 -U memoryos -d postgres -c "CREATE DATABASE memoryos;"
& "C:\Users\CR7\Postgres\17\bin\psql.exe" -h localhost -p 5432 -U memoryos -d memoryos -c "CREATE EXTENSION vector;"
& "C:\Users\CR7\Postgres\17\bin\psql.exe" -h localhost -p 5432 -U memoryos -d memoryos -c "SELECT extversion FROM pg_extension WHERE extname='vector';"   # → 0.8.6
```

`CREATE EXTENSION vector` is idempotent-ish: it fails if already present. Fine — you
run this block once.

---

## 5. Python venv + dependencies

```powershell
# From MemoryOS-App (venv lives with the app)
cd MemoryOS-App
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

# Sanity
.venv\Scripts\python.exe -m pip list | findstr /i "psycopg pgvector pytest SQLAlchemy torch"
```

**First run downloads the embedding model** (ADR-007): the retrieval path uses a local
`sentence-transformers` model (`all-MiniLM-L6-v2`, ~80 MB) stored in `implementation\MemoryOS-App\.hf-cache/`.
The first `pytest` or benchmark run downloads it automatically
(one time, internet needed once). After that everything works offline.

- If the model/cache is missing, the suite **skips** the dense tests and the system
  degrades to BM25-only retrieval (no crash, no fake-dense). To re-download, delete
  `.hf-cache/` and run any test.

**Connection string** is read from the environment (never hardcoded in code):

```powershell
$env:MEMORYOS_DB_DSN = "postgresql://memoryos@localhost:5432/memoryos"
```

The default in `src/memory_os/db/store.py` already is `postgresql://memoryos@localhost:5432/memoryos`, 
so you can skip the env var on this machine — but any other machine must set it.

---

## 6. Run the gates (verify the build)

All app code lives in `implementation\MemoryOS-App\` — run every command from there:

```powershell
cd MemoryOS-App
$env:MEMORYOS_DB_DSN="postgresql://memoryos@localhost:5432/memoryos"
.venv\Scripts\python.exe -m pytest tests/ -v
```

Expected (G-M6):

```
tests\test_admission.py ............................     [100%]
tests\test_adversarial.py .........              [100%]
tests\test_context.py ...............................     [100%]
tests\test_db.py .............                     [100%]
tests\test_latency.py .                            [100%]
tests\test_lifecycle.py ................           [100%]
tests\test_observability.py ..................     [100%]
tests\test_retrieval.py ..............             [100%]
97 passed
```

The DB schema is applied automatically by test fixtures (`apply_schema`, idempotent),
so no manual migration step.

> The suite cleans the `memories` table before AND after every test (autouse
> `clean` fixtures mirror `test_db.py`'s `clean_table`), so the DB is left empty
> after a full run — nothing persists between runs.

### Currently written milestone gates

> All commands below run from `implementation\MemoryOS-App\` (see §6).

| Milestone | Command | Status |
|---|---|---|
| G-M1 Storage & tenant isolation | `.venv\Scripts\python.exe -m pytest tests/test_db.py -q` | PASS (12 tests) |
| G-M2 Hybrid retrieval + RRF + EC-15 latency | `.venv\Scripts\python.exe -m pytest tests/test_retrieval.py tests/test_latency.py -q` | PASS (14 + 1) |
| G-M3 Admission + context | `.venv\Scripts\python.exe -m pytest tests/test_admission.py tests/test_context.py -q` | PASS (24 + 3) |
| G-M4 Lifecycle + deletion propagation | `.venv\Scripts\python.exe -m pytest tests/test_lifecycle.py -q` | PASS (16 tests) |
| G-M5 Observability + audit gate | `.venv\Scripts\python.exe -m pytest tests/test_observability.py -q` | PASS (18 tests) |
| G-M6 Adversarial replay + D3 acceptance | `.venv\Scripts\python.exe -m pytest tests/test_adversarial.py -q` + `python -m bench.acceptance` | PASS (9 tests; all targets) |

### Latency benchmark (EC-15)

The latency gate (`tests/test_latency.py`, marker `-m latency`) seeds 500 memorized
rows and asserts p95 search time < 150 ms. Run it standalone:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_latency.py -v
```

A finer-grained profiler with per-phase breakdown (embed / dense SQL / BM25 / fusion)
is in the repo for manual tuning:

```powershell
cd MemoryOS-App   # app code + venv live here
$env:PYTHONPATH="src"; .venv\Scripts\python.exe -m bench.latency_profile --rows 500 --queries 30
```

> EC-15 note: measured p95 ≈ 20 ms on this machine (was ~206 ms before the
> persistent-connection fix; a fresh TCP+auth connect costs ~30 ms on localhost and
> the hot path reuses one store-scoped connection).

---

## 7. Manual DB checks (feel free to poke)

```bash
& "C:\Users\CR7\Postgres\17\bin\psql.exe" -h localhost -p 5432 -U memoryos -d memoryos
```

```sql
\dt                            -- the memories table
\d memories                    -- columns + CHECKs
SELECT indexname, indexdef FROM pg_indexes WHERE tablename='memories';   -- 5 indexes incl. HNSW
-- tenant filter:
INSERT INTO memories (tenant_id, user_id, text, admission_op, provenance, confidence, pii_scan_result)
VALUES ('acme','alice','Alice uses Postgres','ADD','user_stated',1.0,'pass') RETURNING id;
SELECT text, valid_until FROM memories WHERE tenant_id='acme' AND status='active' AND valid_until IS NULL;
-- supersede:
UPDATE memories SET valid_until = now() WHERE id='<id>' AND tenant_id='acme' AND valid_until IS NULL;
-- the row above is now invisible to the active filter (but still in the table for lineage):
DELETE FROM memories WHERE id='<id>' AND tenant_id='acme' RETURNING id;   -- physical purge
```

⚠️ Manual inserts here persist in the DB; the pytest suite clears the table at every
run (`clean_table` fixture), so re-running tests afterwards is always safe. This
covers the G-M1/G-M2 storage + retrieval manual checks. Watch for:

| Symptom | Cause | Fix |

| Symptom | Cause | Fix |
|---|---|---|
| `connection refused` on :5432 | server not running (or another tool session killed it) | Section 3 detached start; `pg_isready` |
| `FATAL: extension "vector" does not exist` in `CREATE EXTENSION` | pgvector DLL/SQL not copied (Section 2.2) | re-copy from the prebuilt zip |
| `No module named 'psycopg'` | venv deps not installed | Section 5 pip install |
| `0xC0000142` logged | a non-detached postmaster was killed | use WMI detached start (Section 3) |
| port 5432 busy | another PG on the machine | set a different port in `initdb -p`, adjust DSN |

---

## 8. Layout of what the gates verify

> `implementation/MemoryOS-App/` holds all the code below (app-relative prefixes).

- `design/data_model.md` — the single `memories` table + index design (schema.sql is byte-matched)
- `design/sprint_plan.md` — milestone map G-M1…G-M3
- `implementation/MemoryOS-App/src/memory_os/db/schema.sql` — DDL, idempotent
- `implementation/MemoryOS-App/src/memory_os/db/store.py` — `MemoryStore` (session / apply_schema / add / supersede / delete / get_active / search_dense / index_names)
- `implementation/MemoryOS-App/src/memory_os/embeddings/embedder.py` — local sentence-transformers model (ADR-007)
- `implementation/MemoryOS-App/src/memory_os/retrieval/` — tokenizer, BM25, RRF, hybrid fusion (relevance floor)
- `implementation/MemoryOS-App/tests/test_db.py` — 12 tests incl. tenant isolation, hard delete, HNSW rank, concurrency
- `implementation/MemoryOS-App/tests/test_retrieval.py` — 14 tests (D3 regressions, EC-08/09/13/16, RRF/BM25 units)
- `implementation/MemoryOS-App/tests/test_latency.py` — EC-15 gate (`-m latency`, 500-row corpus, p95 < 150 ms)
- `implementation/MemoryOS-App/tests/test_admission.py` — 21 tests (ADD/UPDATE/DELETE/NOOP classification, slot
  supersession per ADR-008, consent purge, PII redaction, MemoryTrap-as-data)
- `implementation/MemoryOS-App/tests/test_context.py` — 6 tests (zone ceilings EC-010, D3 c3 40-token case,
  injection order, `no_relevant_memory` shape, budget arithmetic)
- `implementation/MemoryOS-App/bench/latency_profile.py` — per-phase latency profiler
- `implementation/MemoryOS-App/pytest.ini` — `testpaths=tests`, `pythonpath=src`, `latency` + `adversarial` markers
- `design/decision_records/ADR-008-entity-slot-linking.md` — the deterministic
  slot grammar `admission/patterns.py` implements (rule order matters: specific
  slots like deadline/meeting are checked before the generic `is on X` tool rule)
- `design/decision_records/ADR-005-deletion-propagation-lineage.md` — the
  `consolidation_lineage` mechanism `lifecycle/manager.py` implements
- `src/memory_os/lifecycle/manager.py` — four-lever lifecycle: merge
  (`consolidate`), soft decay (`decay`), eviction + lineage walk (`evict`),
  async 202 jobs (`run_propagation_job`); `propagation_jobs` table
- `tests/test_lifecycle.py` — 16 tests incl. the merge-then-delete "leak via
  summary" gate (EC-04, Threat-4), multi-level lineage rebuild (ADR-005's
  hardest case), depth-cap eviction policy, decay soft-deletion, 202-shaped
  cascade semantics, cross-tenant propagation isolation

### The write path (G-M3 admission)

Every turn goes through `Admitter.admit` (`src/memory_os/admission/admitter.py`):

1. **PII pre-guardrail** — `scrub_pii` replaces secrets with placeholders
   (`[EMAIL]`, `[REDACTED]`, …) *before* persistence (invariant #5)
2. **NOOP** — stopword-only / punctuation-only turns store nothing (EC-017)
3. **DELETE** — "forget the X / taco place" → token-intersection match → physical
   purge (EC-03), no soft flags
4. **UPDATE** — same `(tenant, user, slot_key)` already active → prior row gets
   `valid_until`, new row stored as UPDATE with confidence 0.95 (ADR-002/008)
5. **ADD** — anything else, confidence 1.0

The read path turns retrieval results into a budgeted context block via
`build_context` (`src/memory_os/context/builder.py`): memories are injected in
rank order into the `retrieved_memory` zone until that zone's ceiling — a memory
that doesn't fit is dropped entirely, never overflowed into another zone
(EC-010). Default zone weights: retrieved_memory 40%, output_reserve 30%,
system_prompt/history/input 10%, tool_output 5%; explicit `zone_budgets` carve
out of the *remaining* budget (sum ≤ `token_budget` enforced).

### The lifecycle (G-M4 four-lever + lineage)

`LifecycleManager` (`src/memory_os/lifecycle/manager.py`) implements Week 1's
four levers over the `memories` table:

- **Merge** — `consolidate()` folds related raw memories into one summary
  record (provenance `assistant_generated`) whose `consolidation_lineage`
  points at the sources; sources are kept with `status='merged'` for lineage
  integrity but are no longer retrievable.
- **Decay** — soft: `decay()` sets `status='decayed'` (row survives; every
  retrieval surface already excludes it). `decay_candidates()` finds
  low-importance rows older than a cutoff (importance decided at admission).
- **Eviction** — `evict()` physically purges the record **and walks
  `consolidation_lineage`**: every derived summary is rebuilt from its
  surviving members (deterministically, ascending lineage depth) or evicted
  when nothing survives. This closes the EC-04 "leak via summary" and
  ADR-005's multi-level (summary-of-summary) case. Depth beyond
  `max_lineage_depth` (4) is evicted rather than rebuilt.
- **202 semantics** — cascades larger than `max_sync_derived` persist a
  `propagation_jobs` row and return `in_progress` + `check_url`; the deferred
  job runs via `run_propagation_job` (idempotent).

### Observability + audit gate (G-M5)

`memory_os/observability` (`src/memory_os/observability/tracer.py`) adds typed
trace spans to the hot components, and `memory_os/audit` makes safety a
checked fact of the repository:

- **Spans** — `MemoryTracer.begin/end` opens/ends typed spans (kinds:
  `admission`, `ranking_decision`, `retrieval`, `supersession`, `decay`,
  `eviction`, `consolidation`, `context_build` — system_design_part3 §12).
  Components opt in via a `tracer=` constructor arg; default is a no-op.
  Memory *content* may appear only in span *events*, never in attributes.
- **RedactingCollector** — at export, attribute values whose keys are
  sensitive (`query`, `text`, `content`, `memory`, `payload`, `value`) are
  replaced by `sha256:` hashes; event content is run through the *same* PII
  scrub the write path uses, and each event carries a `redacted: true|false`
  flag. Redaction is deterministic and independent of the write path
  (threat_model Threat 5).
- **Audit gate** — `MemoryStore` + `audit/policy.toml` +
  `memory_os/audit/checker.py`: a config-as-code gate verifying, on every
  run, that: no LLM imports exist in the service; PII scrub precedes
  `store.add`; no raw `psycopg.connect` outside `db/`; no soft-delete writes
  in the service; collector redaction is enabled in policy; every typed
  span kind exists; every EC-XX in the ledger (18) is exercised by a test; and
  the live DB carries the expected CHECK constraints, GIN lineage index, and
  `propagation_jobs` table. A misconfigured deployment **fails the gate**
  rather than shipping unredacted spans.

```powershell
# audit gate standalone (run from implementation\MemoryOS-App\)
cd MemoryOS-App
$env:PYTHONPATH="src"; .venv\Scripts\python.exe -c "from memory_os.audit.checker import AuditChecker; r=AuditChecker().audit(); print('PASS' if r.passed else 'FAIL'); [print(f'  [{\"ok\" if x.passed else \"FAIL\"}] {x.rule}: {x.detail}') for x in r.results]"
```

### Adversarial replay + D3 acceptance run (G-M6)

Two gates close the threat-model verification loops:

- **Adversarial replay** — `tests/test_adversarial.py` (marker
  `adversarial`) replays the named Week-4 attack families against the real
  stack (threat_model Threat 2 verification, line 107-110):
  - *MemoryGraft*: a directive embedded in `tool_derived` output is admitted
    but never outranks its benign `user_stated` twin — provenance-weighted
    ranking holds across paraphrased queries; a correcting user turn
    supersedes the poisoned row via slot key.
  - *MINJA / MemoryTrap class*: newline-framed directive text is stored
    verbatim but inert — `build_context` only ever emits `- <text>` data
    lines, never executable directives.
  - *Influence over time*: low-importance poisoned rows are selected by
    `decay_candidates` and, once decayed, have exactly zero presence in
    retrieval (the design's "default expiry reduces influence" claim).
  - *Cross-tenant corpus* (EC-05 / Threat 1): adversarially crafted
    near-identical and paraphrased queries never surface another tenant's
    rows — including the explicit `no_relevant_memory` outcome.
- **D3 acceptance replay** — `python -m bench.acceptance` (run from
  `implementation\MemoryOS-App\`) re-runs the exact 10 hand-written workload cases from
  `experiments/naive_baseline/dataset.py` (app loads it via the repo-root
  path) through admission → retrieval → budgeted context injection,
  aggregates the same metrics as `summary.json`, and compares against the
  Deliverable targets. Requirement: contradiction < 5%, cold-start FP < 5%,
  sensitive leak 0%, precision@1 = 1.0, p95 < 150 ms. Result vs baseline:

  | metric | baseline | MemoryOS | target |
  |---|---|---|---|
  | precision_at_1 | 0.857 | **1.000** | 1.000 |
  | contradiction_failure_rate | 0.333 | **0.000** | < 0.05 |
  | cold_start_false_positive_rate | 0.500 | **0.000** | < 0.05 |
  | sensitive_leak_rate_retrieval | 1.000 | **0.000** | 0 |
  | sensitive_leak_rate_injection | 1.000 | **0.000** | 0 |
  | latency_p95_s | 0.0008 | **0.012** | < 0.150 |

  Results are written to `implementation/MemoryOS-App/bench/results/acceptance.json`; the run exits
  non-zero on any miss.

*End of guide (G-M6). Later gates append their docs here.*