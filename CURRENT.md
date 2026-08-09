# Current Work

> One question: **"Where exactly are we RIGHT NOW?"** — keep this file extremely practical. If chat context compacts, open this file and continue.

## Current Objective
G-M5 (observability + security hardening) is **built and gated green (88 passed)** — G-M5 commit pending; next is G-M6 per `design/sprint_plan.md`.

## Current Phase
Genesis milestones 1–5 done, gated, committed through G-M4 (`8ab43f1`); G-M5 built, gate green, commit pending; then G-M6.

## Current Task
Commit G-M5: `feat(g-m5): typed trace spans + redacting collector + audit gate`. Then open G-M6.

## Last Completed Action
[2026-08-09] G-M5 implementation complete, **88 passed**, DB left empty (memories 0, propagation_jobs 0):
- NEW `memory_os/observability/tracer.py` (+`__init__`): typed spans (`admission`, `ranking_decision`, `retrieval`, `supersession`, `decay`, `eviction`, `consolidation`, `context_build` — part3 §12 inventory), deterministic ids/parent-child ordering, in-process recorder, plain-JSON `export`; content allowed only in span *events* — never attributes; `MemoryTracer.noop()` shared no-op instance (instrumentation opt-in).
- NEW `RedactingCollector`: hashes sensitive attribute values (`query/text/content/memory/payload/value` → `sha256:`), scrubs event content with the same `scrub_pii` the write path uses, flags each event `redacted: true|false`. Threat 5 closed at the collector.
- NEW `memory_os/audit/checker.py` + `audit/policy.toml`: config-as-code gate (8 rules — no_llm imports, PII-scrub-before-persist ordering, no raw psycopg outside db/, no soft-delete writes, collector redaction enabled, typed kinds declared, ledger EC-01..18 exercised by tests, live-DB schema/constraints/gin lineage/propagation_jobs). Threat model's named residual gap closed: misconfigured deployment fails a psql gate, not a manual promise.
- Instrumented: `Admitter(tracer=...)` (span `admission`, event `turn_content`), `HybridRetriever(tracer=...)` (span `retrieval`, event `query_content`), `LifecycleManager(tracer=...)` (span `eviction`).
- Provenance-weighted ranking in `hybrid.py` (`PROVENANCE_WEIGHTS`: user_stated 1.0 > assistant_generated 0.85 > tool_derived 0.6 > retrieved_document 0.5) — Threat-2 mitigation: identical content from attacker-controlled channels ranks below user-stated; `effective_score` recorded in hits.
- Gates `tests/test_observability.py` (18): collector redaction (scrubbed vs verum pass-through, hashed attributes, no-op tracer), span hierarchy/idempotent ordering, provenance weighting (user_stated > tool_derived; effective_score monotone), audit gate pass + "flip a policy flag → gate FAILS" prove-out.
- Fixed en route: admitter IndentationError from `_span_context` mixing; checker `parents[3]` rooting; psycopg-connect rule self-flagging (exclude db/ + audit/).

## Last Command Executed
`pytest -q` → 88 passed. `SELECT (count(*) FROM memories), (count(*) FROM propagation_jobs)` → `0 | 0`.

## Last Meaningful Result
G-M5 gate green, including: collector provably strips `hunter2`/card numbers while letting benign content through with `redacted=false`; provenance weighting deterministically de-ranks tool-derived identical content (threat_model Threat 2)*; and the audit gate PASSES now but FAILS the moment `redaction_enabled` is switched false — config-as-code is real, not decorative. DB empty. Tree = exactly the G-M5 commit set (uncommitted).

## Currently Modified Files (for this commit)
- NEW: `src/memory_os/observability/{__init__,tracer}.py`, `audit/policy.toml`, `src/memory_os/audit/{__init__,checker}.py` (2 dirs), `tests/test_observability.py`, `journal/2026-08-09-session-gm5.md`
- MODIFIED: `src/memory_os/admission/admitter.py`, `src/memory_os/retrieval/hybrid.py`, `src/memory_os/lifecycle/manager.py`, `src/memory_os/observability/__init__.py` (may be created), `docs/SETUP_AND_RUN.md` (G-M5 section), `CURRENT.md`

## What I Was About To Do Next
Commit G-M5, then start G-M6 per `design/sprint_plan.md` (next milestone after observability).

## Immediate Next 3 Actions
1. `git add -A` + commit `feat(g-m5): observability spans + provenance-weighted ranking`.
2. Verify: `git status` clean; log shows G-M5 on top of 8ab43f1.
3. Open G-M6 per `design/sprint_plan.md`.

## Known Problems
- Default `python` (3.11) lacks heavy libs — always use `.venv\Scripts\python.exe` (Python 3.14).
- Postgres must be **detached-started** (WMI) or shell-tool job object kills it (`0xC0000142`).
- psycopg import failures seen **only when scripts run in non-repo dirs** (`%LocalTemp%\opencode`) — work from repo root; pytest fine.
- REAL `0.1` vs float8 literal: comparisons against REAL columns need `::float4` casts (stored 0.1 = 0.10000000149…).
- `AuditChecker` gate holds its own rule strings (e.g. `psycopg.connect`) — never scan db/ or audit/ dirs in `_hot_path` rule or they self-flag.
- Windows path separators: path matches in checker.go rely on `os.path.sep` — keep `rel`-based checks Windows-safe.

## Do Not Repeat
- No writes to old repo (`D:\Abhii\Projects\Conversational-Memory-Intelligence-System-`); no `memory_type` column resurrection; data_model.md canonical.
- No `with conn:` + fresh `psycopg.connect()` on hot paths — use `store.session()`.
- Do not run Python from `%TEMP%` with the repo venv; keep scripts under `D:\Abhii\Projects\MemoryOS`.
- Don't seed via `store.add(...)` positionally — signature is keyword-only.
- No raw memory content in span **attributes** — content lives in events only (collector redacts at export).
- No `tomli_w`/OTEL assumptions in gate tests — tomllib reads policy; replacement is string-level.

## Verification Required
After G-M5 commit: `git status` clean; `git log --oneline -5` shows `feat(g-m5)` on top of 8ab43f1; DB `COUNT(*) = 0` for both tables; `pytest -q` → 88 passed with 0 failures.

## Resume From Here
`docs/RESUME.md` → `docs/SESSION_STATE.md` → `CURRENT.md` → `journal/2026-08-09-session-gm5.md`.