# Session journal — 2026-08-09 (G-M6b: MemoryOS-App consolidation)

## Scope
Per user request: "All the code which is developed by Genesis is to be in one
folder only, name it MemoryOS-App." Target: **fully self-contained app
folder** inside the existing repo (single git history).

## What was done

### Layout (repo root after the move)
- `MemoryOS-App/` — ALL Genesis-built code + runtime: `src/`, `tests/`,
  `bench/`, `audit/policy.toml`, `pytest.ini`, `requirements.txt`, `.venv/`,
  `.hf-cache/`, new `README.md`.
- Repo root — course deliverables, untouched: `design/`, `docs/`,
  `experiments/`, `research/`, `reconstruction/`, `product/`, `journal/`,
  `.genesis/`, `tools/`, `contribution/`, `implementation/`, `transfer/`,
  `verification/`, root docs.

### Mechanics
- `git mv` for all tracked items (history preserved — R100 renames).
- `.venv` + `.hf-cache` physically moved; venv verified relocatable
  (psycopg, numpy, sentence-transformers import clean from the new path).
- Path-sensitive code audit:
  - `bench/acceptance.py`: split `APP_ROOT` (parents[1]) from `REPO_ROOT`
    (parents[2]) — the D3 dataset stays at
    `experiments/naive_baseline/dataset.py` in the repo root; results write
    to `APP_ROOT/bench/results/acceptance.json`. Only code change needed.
  - `audit/checker.py` + `test_observability.py` policy path: verified
    correct at the new depth (parents[3] now resolves to MemoryOS-App) —
    zero changes.
- Docs updated: SETUP_AND_RUN (§6 + gates table + §8 layout), RESUME,
  SESSION_STATE (constraints/commands/files), CURRENT, new journal entry.

## Verification (final)
- `cd MemoryOS-App; $env:PYTHONPATH="src"` → `pytest -q` → **97 passed**
- `python -m bench.acceptance` → **PASS** (precision@1 1.0, contradiction 0,
  cold-start FP 0, leaks 0, p95 10 ms)
- Audit gate → **PASS** (8/8 rules)
- DB → `0 | 0`

## Next
Commit `refactor(app): consolidate genesis-built code under MemoryOS-App`.