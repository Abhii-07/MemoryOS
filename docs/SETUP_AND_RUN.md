# Setup & Run Guide — MemoryOS

> Written for a human with no AI agent. Copy-paste everything below.
> Last updated: 2026-08-08 (G-M1 gate). Extends with G-M2/G-M3 commands as those gates land.

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
# From the repo root
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

# Sanity
.venv\Scripts\python.exe -m pip list | findstr /i "psycopg pgvector pytest SQLAlchemy"
```

**Connection string** is read from the environment (never hardcoded in code):

```powershell
$env:MEMORYOS_DB_DSN = "postgresql://memoryos@localhost:5432/memoryos"
```

The default in `src/memory_os/db/store.py` already is `postgresql://memoryos@localhost:5432/memoryos`, 
so you can skip the env var on this machine — but any other machine must set it.

---

## 6. Run the gates (verify the build)

```bash
$env:MEMORYOS_DB_DSN="postgresql://memoryos@localhost:5432/memoryos"
.venv\Scripts\python.exe -m pytest tests/ -v
```

Expected (G-M1):

```
tests\test_db.py .............                     [100%]
12 passed in 2.19s
```

The DB schema is applied automatically by test fixtures (`apply_schema`, idempotent),
so no manual migration step.

### Currently written milestone gates

| Milestone | Command | Status |
|---|---|---|
| G-M1 Storage & tenant isolation | `.venv\Scripts\python.exe -m pytest tests/test_db.py -q` | PASS (12 tests) |
| G-M2 Hybrid retrieval + RRF | `pytest tests/test_retrieval.py -q` | not yet shipped → docs updated when landed |
| G-M3 Admission + context | `pytest tests/test_admission.py -q`, `pytest tests/test_context.py -q` | not yet shipped → docs updated when landed |

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
run (`clean_table` fixture), so re-running tests afterwards is always safe. This is
a G-M1 (storage) manual check only. Watch for:

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

- `design/data_model.md` — the single `memories` table + index design (schema.sql is byte-matched)
- `design/sprint_plan.md` — milestone map G-M1…G-M3
- `src/memory_os/db/schema.sql` — DDL, idempotent
- `src/memory_os/db/store.py` — `MemoryStore` (connect / apply_schema / add / supersede / delete / get_active / search_dense / index_names)
- `tests/test_db.py` — 12 tests incl. tenant isolation, hard delete, HNSW rank, concurrency
- `pytest.ini` — `testpaths=tests`, `pythonpath=src`

*End of guide (G-M1). Later gates append their docs here.*