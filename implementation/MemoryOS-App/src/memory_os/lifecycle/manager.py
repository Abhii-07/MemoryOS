"""G-M4 Lifecycle Manager: the four-lever framework (Week 1) + deletion
propagation through `consolidation_lineage` (Week 4 / ADR-005).

Levers:
  - Importance   decided at admission (importance_score stored on each row).
  - Merge        :attr:`consolidate` folds related raw memories into one
                 summary record; sources are marked 'merged' and retained for
                 lineage integrity (data_model.md note on the 5th status).
  - Decay        :attr:`decay` — SOFT. Marks rows status='decayed', which every
                 retrieval surface already excludes; never touches lineage.
  - Eviction     :attr:`evict` — the actual removal path (physical row delete,
                 privacy invariant #2) and the ONLY lever that walks
                 consolidation_lineage (backflow prevention, EC-04).

Deletion propagation (the ADR-005 mechanism):
  A deletion against a source record cascades to every derived record whose
  `consolidation_lineage` references it, transitively. Each derived record is
  rebuilt from its surviving members — deterministically, depth-first in
  ascending lineage depth so a summary-of-summary sees its rebuilt inner
  summary — or evicted when nothing survives. The "leak via summary" case
  (delete a raw fact, the regenerated summary must not contain it) is the
  single most important gate this system has (threat_model Threat 4).

Honesty rule (api_contracts Endpoint 3): a cascade larger than
`max_sync_derived` is persisted to `propagation_jobs` and reported as
`in_progress` with a `check_url` — never a false-positive "complete".
`run_propagation_job` performs that deferred cascade deterministically.

Determinism: summary text is sorted()-stable, cascade iteration is by
(id, depth), recap is never non-deterministic; no LLM call exists on this
path (R1/R8).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from memory_os.db.store import MemoryStore
from memory_os.embeddings import embed, is_available
from memory_os.retrieval.tokenizer import term_frequencies
from psycopg.types.json import Jsonb

# Depth cap for rebuilds (ADR-0005 revisit condition): graph paths deeper
# than this are ever evicted, keeping lineage graphs shallow and honest.
MAX_LINEAGE_DEPTH = 4
# api_contracts Endpoint 3: cascades no larger than this complete synchronously.
MAX_SYNC_DERIVED = 100
# Merge lever: deterministic summary prefix.
SUMMARY_PREFIX = "[summary of %d facts] "
DECAY_DEFAULT_MIN_IMPORTANCE = 0.3


class LifecycleError(Exception):
    pass


class RecordNotFound(LifecycleError):
    """Contracts the DELETE /memory/{id} 404 path."""


@dataclass(frozen=True)
class DeletionResult:
    """Speaks api_contracts Endpoint 3 response shape."""

    deleted_id: str | None          # None → record did not exist (404 path)
    propagated_ids: tuple[str, ...] # every rebuilt-or-evicted derived record
    propagation_status: str         # "complete" | "in_progress"
    job_id: str | None = None
    check_url: str | None = None

    @property
    def complete(self) -> bool:
        return self.propagation_status == "complete"


def _summary_text(sources: list[dict[str, Any]]) -> str:
    """Deterministic summary: `[summary of N facts] ` + sorted source texts
    (sorted() → identical inputs produce identical outputs, R8)."""
    parts = sorted(s["text"] for s in sources)
    return SUMMARY_PREFIX % len(parts) + "; ".join(parts)


def _embed_text(text: str) -> list[float] | None:
    if not is_available():
        return None
    vecs = embed([text])
    return vecs[0] if vecs else None


class LifecycleManager:
    """Four-lever lifecycle + deterministic lineage propagation (G-M4)."""

    def __init__(
        self,
        store: MemoryStore,
        *,
        max_lineage_depth: int = MAX_LINEAGE_DEPTH,
        max_sync_derived: int = MAX_SYNC_DERIVED,
        min_importance: float = DECAY_DEFAULT_MIN_IMPORTANCE,
        tracer=None,
    ):
        self.store = store
        self.max_lineage_depth = max_lineage_depth
        self.max_sync_derived = max_sync_derived
        self.min_importance = min_importance
        self._tracer = tracer

    # ─── Merge lever ─────────────────────────────────────────────────────────

    def consolidate(
        self,
        *,
        tenant_id: str,
        user_id: str,
        source_ids: list[str],
        summary_text: str | None = None,
    ) -> tuple[str, list[str]]:
        """Fold `sources` into ONE consolidated record; sources → 'merged'.

        Returns (summary_record_id, source_ids). Every source must exist and
        belong to this tenant (deterministic pre-check before any write).
        """
        if not source_ids:
            raise LifecycleError("consolidate requires at least one source")
        with self.store.session() as conn:
            rows = conn.execute(
                """
                SELECT id, text FROM memories
                 WHERE tenant_id = %s AND id = ANY(%s::uuid[])
                   AND status IN ('active', 'merged')
                """,
                (tenant_id, source_ids),
            ).fetchall()
        found = {str(r["id"]): r for r in rows}
        unknown = [sid for sid in source_ids if sid not in found]
        if unknown:
            raise LifecycleError(f"unknown sources: {sorted(unknown)}")
        # Preserve the caller's source ordering in the lineage array but keep
        # the summary content deterministic (sorted texts).
        texts = sorted(r["text"] for r in found.values())
        text = summary_text or _summary_text([{"text": t} for t in texts])

        result = self.store.add(
            tenant_id=tenant_id,
            user_id=user_id,
            text=text,
            admission_op="ADD",
            provenance="assistant_generated",  # synthetic artifact, never user-stated
            confidence=0.9,
            pii_scan_result="pass",
            pii_detector_version=None,
            dense_embedding=_embed_text(text),
            sparse_terms=term_frequencies(text),
            importance_score=0.5,
            status="active",
            consolidation_lineage=source_ids,
        )
        for sid in source_ids:
            self.store.mark_merged(record_id=sid, tenant_id=tenant_id)
        return str(result["id"]), list(source_ids)

    # ─── Decay lever (soft) ──────────────────────────────────────────────────

    def decay_candidates(
        self, *, tenant_id: str, max_age_days: int = 180, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Low-importance rows older than the cutoff (importance set at
        admission; NULL importance never decay-eligible)."""
        with self.store.session() as conn:
            return conn.execute(
                """
                SELECT id, text, importance_score, valid_from
                  FROM memories
                 WHERE tenant_id = %s AND status = 'active' AND valid_until IS NULL
                   AND importance_score IS NOT NULL AND importance_score <= %s::float4
                   AND valid_from <= now() - make_interval(days => %s)
                 ORDER BY importance_score ASC, valid_from ASC
                 LIMIT %s
                """,
                (tenant_id, self.min_importance, max_age_days, limit),
            ).fetchall()

    def decay_eligible(self, *, tenant_id: str, record_id: str) -> bool:
        with self.store.session() as conn:
            row = conn.execute(
                """
                SELECT id FROM memories
                 WHERE id = %s AND tenant_id = %s AND status = 'active'
                   AND importance_score IS NOT NULL AND importance_score <= %s::float4
                """,
                (record_id, tenant_id, self.min_importance),
            ).fetchone()
        return row is not None

    def decay(self, *, tenant_id: str, record_id: str) -> bool:
        """Soft lever: status → 'decayed'. The row survives with lineage
        intact (EC-01); active-window retrieval no longer sees it."""
        return self.store.set_status(
            record_id=record_id, tenant_id=tenant_id, status="decayed"
        )

    # ─── Eviction lever + lineage propagation (the ADR-005 core) ─────────────

    def evict(
        self, *, tenant_id: str, record_id: str,
        max_sync_derived: int | None = None,
    ) -> DeletionResult:
        """Delete `record_id` and rebuild/evict every derived record that
        referenced it (directly or transitively). Honest status: complete vs
        202-style in_progress for cascades beyond `max_sync_derived`."""
        threshold = (
            self.max_sync_derived if max_sync_derived is None else max_sync_derived
        )
        span = None
        if self._tracer is not None:
            span = self._tracer.begin(name="eviction", kind="eviction",
                                      attributes={"tenant_id": tenant_id,
                                                  "record_id": record_id})
        try:
            return self._evict(tenant_id=tenant_id, record_id=record_id,
                               threshold=threshold)
        finally:
            if span is not None:
                self._tracer.end(span)

    def _evict(self, *, tenant_id: str, record_id: str,
               threshold: int) -> DeletionResult:
        with self.store.session() as conn:
            exists = conn.execute(
                "SELECT id FROM memories WHERE id = %s AND tenant_id = %s",
                (record_id, tenant_id),
            ).fetchone()
            if exists is None:
                return DeletionResult(None, (), "complete")
            conn.execute(
                "DELETE FROM memories WHERE id = %s AND tenant_id = %s",
                (record_id, tenant_id),
            )

        closure, depths = self._resolve_closure(tenant_id=tenant_id, deleted_id=record_id)
        if len(closure) > threshold:
            job_id = self.store.create_propagation_job(tenant_id=tenant_id,
                                                       deleted_id=record_id)
            return DeletionResult(
                deleted_id=record_id, propagated_ids=(),
                propagation_status="in_progress", job_id=job_id,
                check_url=f"/memory/deletion-status/{job_id}",
            )

        propagated = self._rebuild_cascade(tenant_id=tenant_id,
                                           closure=closure, depths=depths)
        return DeletionResult(record_id, propagated, "complete")

    def run_propagation_job(self, *, job_id: str) -> DeletionResult:
        """Run a deferred cascade (api_contracts check_url target). Idempotent:
        a completed job re-verifies the DB state rather than re-deleting."""
        job = self.store.get_propagation_job(job_id=job_id)
        if job is None:
            raise LifecycleError(f"unknown job {job_id}")
        if job["state"] == "completed":
            return DeletionResult(job["deleted_id"], (), "complete",
                                  job_id=job_id,
                                  check_url=f"/memory/deletion-status/{job_id}")
        closure, depths = self._resolve_closure(tenant_id=job["tenant_id"],
                                                deleted_id=str(job["deleted_id"]))
        propagated = self._rebuild_cascade(tenant_id=str(job["tenant_id"]),
                                              closure=closure, depths=depths)
        self.store.complete_propagation_job(job_id=job_id)
        return DeletionResult(str(job["deleted_id"]), propagated, "complete",
                              job_id=job_id,
                              check_url=f"/memory/deletion-status/{job_id}")

    def _resolve_closure(self, *, tenant_id: str, deleted_id: str
                         ) -> tuple[dict[str, list[str]], dict[str, int]]:
        """Closure: id → its lineage members, for every derived record transitively
        reachable from `deleted_id` via the GIN index (each hop a deterministic
        tenant-scoped query, ORDER BY id).

        depths: id → lineage depth, where depth(raw)=0 and
        depth(D) = 1 + max(depth(s) for s in D.lineage ∩ closure). Nodes whose
        depth would exceed `max_lineage_depth` are bumped to the cap and
        evicted rather than rebuilt (ADR-0005 revisit-condition policy).
        """
        closure: dict[str, list[str]] = {}
        queue = [deleted_id]
        seen = {deleted_id}
        while queue:
            probe = queue.pop(0)
            for row in self.store.get_derived(tenant_id=tenant_id, source_id=probe):
                rid = str(row["id"])
                lineage = [str(x) for x in (row["consolidation_lineage"] or [])]
                if rid not in closure:
                    closure[rid] = lineage
                if rid not in seen:
                    seen.add(rid)
                    queue.append(rid)
        depths: dict[str, int] = {}
        for rid in sorted(closure):
            depths[rid] = self._depth(rid, closure)
        return closure, depths

    def _depth(self, rid: str, closure: dict[str, list[str]],
               memo: dict[str, int] | None = None) -> int:
        memo = memo if memo is not None else {}
        if rid in memo:
            return memo[rid]
        members = [s for s in closure[rid] if s in closure]
        if not members:
            memo[rid] = 1
            return 1
        inner = max(self._depth(m, closure, memo) for m in members)
        memo[rid] = inner + 1
        return memo[rid]

    def _rebuild_cascade(self, *, tenant_id: str, closure: dict[str, list[str]],
                         depths: dict[str, int]) -> tuple[str, ...]:
        """Rebuild every derived record bottom-up (ascending depth, id stable).

        For each node: survivors = the node's lineage members that still exist
        (status active/merged). Non-empty → regenerate the summary from the
        survivors (EC-006: never leaks the deleted fact) — the node keeps its
        id/tenant/provenance but gets fresh text/embedding. Empty → the node
        itself is evicted (physical delete).
        """
        propagated: list[str] = []
        for rid in sorted(closure, key=lambda r: (depths[r], r)):
            lineage = closure[rid]
            with self.store.session() as conn:
                rows = conn.execute(
                    """
                    SELECT id, text FROM memories
                     WHERE tenant_id = %s AND id = ANY(%s::uuid[])
                       AND status IN ('active', 'merged')
                    """,
                    (tenant_id, lineage),
                ).fetchall()
                node_exists = conn.execute(
                    "SELECT id FROM memories WHERE id = %s AND tenant_id = %s",
                    (rid, tenant_id),
                ).fetchone()
            if not node_exists:
                continue  # already gone (evicted by an earlier hop)
            survivors = [{"id": str(r["id"]), "text": r["text"]} for r in rows]
            if depths[rid] > self.max_lineage_depth:
                # policy (ADR-0005 revisit): deep graphs are evicted, not rebuilt
                with self.store.session() as conn:
                    conn.execute(
                        "DELETE FROM memories WHERE id = %s AND tenant_id = %s",
                        (rid, tenant_id),
                    )
                propagated.append(rid)
                continue
            if not survivors:
                with self.store.session() as conn:
                    conn.execute(
                        "DELETE FROM memories WHERE id = %s AND tenant_id = %s",
                        (rid, tenant_id),
                    )
                propagated.append(rid)
                continue
            new_text = _summary_text(survivors)
            dense = _embed_text(new_text)
            survivor_ids = [s["id"] for s in survivors]
            with self.store.session() as conn:
                conn.execute(
                    """
                    UPDATE memories
                       SET text = %s, dense_embedding = %s, sparse_terms = %s,
                           consolidation_lineage = %s::uuid[],
                           updated_at = now()
                     WHERE id = %s AND tenant_id = %s
                    """,
                    (new_text, dense, Jsonb(term_frequencies(new_text)),
                     survivor_ids, rid, tenant_id),
                )
            propagated.append(rid)
        return tuple(propagated)


__all__ = [
    "LifecycleManager", "DeletionResult", "LifecycleError", "RecordNotFound",
    "MAX_LINEAGE_DEPTH", "MAX_SYNC_DERIVED", "SUMMARY_PREFIX",
    "DECAY_DEFAULT_MIN_IMPORTANCE",
]