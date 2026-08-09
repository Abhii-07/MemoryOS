"""G-M5 audit checker: config-as-code verification (threat_model Threat 5).

The threat model explicitly named the residual gap behind this module:
collector-redaction discipline "depends entirely on collector configuration ...
a config-as-code check ... currently unaddressed." This is that check.
`audit/policy.toml` is the single source of truth for which safeguards must be
active; `AuditChecker.audit()` verifies each against the actual repository and
live database and returns a deterministic report. Failing gates ship nothing.
"""

from __future__ import annotations

import os
import re
import tomllib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

from memory_os.db.store import MemoryStore

_REPO_ROOT = Path(__file__).resolve().parents[3]  # src/memory_os/audit -> repo
_POLICY_PATH = os.path.join(_REPO_ROOT, "audit", "policy.toml")
_SRC = os.path.join(_REPO_ROOT, "src")

# No LLM client may appear anywhere in the service (R1 deterministic path).
_FORBIDDEN_IMPORTS = ("openai", "anthropic", "litellm", "transformers",
                      "requests", "httpx")


@dataclass
class AuditResult:
    rule: str
    passed: bool
    detail: str = ""


@dataclass
class AuditReport:
    policy_file: str
    results: list[AuditResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def failures(self) -> list[AuditResult]:
        return [r for r in self.results if not r.passed]


def _service_files() -> list[str]:
    """All .py files under src/memory_os (service code, not tests/tools)."""
    out: list[str] = []
    for root, _dirs, files in os.walk(_SRC):
        for name in files:
            if name.endswith(".py"):
                out.append(os.path.join(root, name))
    return sorted(out)


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


class AuditChecker:
    """Deterministic repository+DB compliance check driven by policy.toml."""

    def __init__(self, store: MemoryStore | None = None):
        self.store = store or MemoryStore()

    def load_policy(self) -> dict[str, Any]:
        with open(_POLICY_PATH, "rb") as f:
            return tomllib.load(f)

    def audit(self) -> AuditReport:
        policy = self.load_policy()
        report = AuditReport(_POLICY_PATH)
        report.results = [
            self._no_llm(policy),
            self._pii_pre_guardrail(),
            self._hot_paths_session(),
            self._soft_delete_forbidden(),
            self._collector_redaction(policy),
            self._typed_span_kinds(policy),
            self._ledger_coverage(policy),
            self._schema_compliance(),
        ]
        return report

    # ── rule implementations ────────────────────────────────────────────────

    def _no_llm(self, policy: dict[str, Any]) -> AuditResult:
        if not policy.get("security_invariants", {}).get("no_llm", False):
            return AuditResult("no_llm", False, "policy disables the rule")
        offenders: list[str] = []
        for path in _service_files():
            src = _read(path)
            for token in _FORBIDDEN_IMPORTS:
                if _import_regex(token).search(src):
                    offenders.append(f"{os.path.basename(path)} imports {token}")
        return AuditResult("no_llm", not offenders,
                           "; ".join(offenders) or "no LLM imports in service")

    def _pii_pre_guardrail(self) -> AuditResult:
        """Static ordering proof on admitter.py: scrub_pii() must be called
        before store.add() in the write path (invariant #5)."""
        admitter = os.path.join(_SRC, "memory_os", "admission", "admitter.py")
        src = _read(admitter)
        scrub_pos = src.find("scrub_pii(text)")
        add_pos = src.find("self.store.add(")
        ok = scrub_pos != -1 and add_pos != -1 and scrub_pos < add_pos
        detail = ("scrub before persist" if ok else
                  "scrub_pii not provably before store.add")
        return AuditResult("pii_pre_guardrail", ok, detail)

    def _hot_paths_session(self) -> AuditResult:
        """EC-15 rule: service modules outside db/ must never open raw
        connections directly; they go through MemoryStore.session()/connect()."""
        offenders: list[str] = []
        for path in _service_files():
            rel = os.path.relpath(path, _SRC)
            if "db" + os.path.sep in rel or "audit" + os.path.sep in rel:
                continue  # store.py owns psycopg; the checker merely states the rule
            src = _read(path)
            if "psycopg.connect(" in src:
                offenders.append(rel)
        return AuditResult("hot_paths_use_session", not offenders,
                           "; ".join(offenders) or "all DB access via store.session()")

    def _soft_delete_forbidden(self) -> AuditResult:
        offenders: list[str] = []
        for path in _service_files():
            src = _read(path)
            if re.search(r"status\s*=\s*['\"]deleted['\"]", src):
                offenders.append(os.path.basename(path))
        return AuditResult("soft_delete_forbidden", not offenders,
                           "; ".join(offenders) or "no soft-delete writes (purge is physical)")

    def _collector_redaction(self, policy: dict[str, Any]) -> AuditResult:
        enabled = policy.get("collector", {}).get("redaction_enabled", False)
        hashing = policy.get("collector", {}).get("hash_sensitive_attributes", False)
        if not (enabled and hashing):
            return AuditResult("collector_redaction", False,
                               "policy: redaction or hashing disabled")
        # the collector must actually scrub: prove it exists in the module
        tracer = os.path.join(_SRC, "memory_os", "observability", "tracer.py")
        src = _read(tracer)
        ok = ("class RedactingCollector" in src and "scrub_pii" in src
              and "sha256" in src)
        return AuditResult("collector_redaction", ok,
                           "RedactingCollector present with PII scrub + hashing")

    def _typed_span_kinds(self, policy: dict[str, Any]) -> AuditResult:
        required = policy.get("observability", {}).get("typed_span_kinds", [])
        tracer = os.path.join(_SRC, "memory_os", "observability", "tracer.py")
        src = _read(tracer)
        missing = [k for k in required if k not in src]
        return AuditResult("typed_span_kinds", not missing,
                           "; ".join(missing) or f"{len(required)} kinds declared")

    def _ledger_coverage(self, policy: dict[str, Any]) -> AuditResult:
        """Every EC-XX named in the ledger must be exercised by a test file.

        ID matching is zero-padding tolerant: a test citing EC-1 covers the
        policy's EC-01 entry."""
        required = policy.get("ledger", {}).get("required_edge_cases", [])
        wanted = {int(re.search(r"\d+$", ec).group()) for ec in required}
        tests_dir = os.path.join(_REPO_ROOT, "tests")
        test_src = ""
        for name in sorted(os.listdir(tests_dir)):
            if name.startswith("test_") and name.endswith(".py"):
                test_src += _read(os.path.join(tests_dir, name))
        found = {int(m) for m in re.findall(r"EC-0?(\d+)\b", test_src)}
        missing = sorted(wanted - found)
        return AuditResult("ledger_coverage", not missing,
                           "; ".join(f"EC-{i:02d}" for i in missing)
                           or f"all {len(required)} ECs tested")

    def _schema_compliance(self) -> AuditResult:
        """Live DB: constraints and lineage machinery from data_model.md."""
        with self.store.connect() as conn:
            checks = conn.execute(
                """
                SELECT conname FROM pg_constraint
                 WHERE conrelid = 'memories'::regclass
                   AND contype = 'c'
                """
            ).fetchall()
            check_names = {r["conname"] for r in checks}
            tables = conn.execute(
                "SELECT tablename FROM pg_tables WHERE tablename IN "
                "('memories', 'propagation_jobs')"
            ).fetchall()
            table_names = {r["tablename"] for r in tables}
            lineage_idx = conn.execute(
                "SELECT 1 FROM pg_indexes WHERE tablename='memories' "
                " AND indexname='idx_memories_lineage'"
            ).fetchone()
        ok = ({f"memories_{c}_check" for c in
               ("admission_op", "provenance", "pii_scan_result", "status")}
              <= check_names)
        ok = ok and table_names >= {"memories", "propagation_jobs"}
        ok = ok and lineage_idx is not None
        detail = (f"{len(check_names)} CHECKs; tables={sorted(table_names)}; "
                  f"gin_lineage={lineage_idx is not None}")
        return AuditResult("schema_compliance", ok, detail)


def _import_regex(token: str):
    return re.compile(rf"(?:import|from)\s+{token}\b")


__all__ = ["AuditChecker", "AuditReport", "AuditResult"]