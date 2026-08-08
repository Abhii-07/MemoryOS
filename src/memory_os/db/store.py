"""G-M1 storage layer: connection + single-table repository.

Config via env vars (no code config in the repo beyond defaults):
  MEMORYOS_DB_DSN   e.g. postgresql://memoryos@localhost:5432/memoryos
  MEMORYOS_PG_BIN    path to the portable PostgreSQL bin dir (optional, for tests)
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from pgvector.psycopg import register_vector

_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def _load_schema() -> str:
    with open(_SCHEMA_PATH, encoding="utf-8") as f:
        return f.read()

DEFAULT_DSN = os.environ.get("MEMORYOS_DB_DSN", "postgresql://memoryos@localhost:5432/memoryos")


class MemoryStore:
    """Hard tenant isolation is enforced at every query surface (never a bare scan)."""

    def __init__(self, dsn: str | None = None):
        self.dsn = dsn or DEFAULT_DSN
        self._persistent: psycopg.Connection | None = None

    def connect(self) -> psycopg.Connection:
        """Fresh connection (caller closes it; `with conn:` closes on exit)."""
        conn = psycopg.connect(self.dsn, row_factory=dict_row)
        register_vector(conn)
        return conn

    @contextmanager
    def session(self) -> Iterator[psycopg.Connection]:
        """Persistent connection: commits/rolls back but never closes.

        EC-15: opening a fresh TCP+auth connection costs ~30 ms on localhost,
        so hot paths reuse a single store-scoped connection.
        """
        conn = self._persistent
        if conn is None or conn.closed:
            conn = self._persistent = psycopg.connect(self.dsn, row_factory=dict_row)
            register_vector(conn)
        try:
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise

    def apply_schema(self) -> str:
        """Idempotent DDL. Returns the pgvector extension version after applying."""
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(_load_schema())
            ver = conn.execute(
                "SELECT extversion FROM pg_extension WHERE extname='vector'"
            ).fetchone()
        return ver["extversion"] if ver else ""

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def add(
        self,
        *,
        tenant_id: str,
        user_id: str,
        text: str,
        admission_op: str = "ADD",
        provenance: str = "user_stated",
        confidence: float = 1.0,
        pii_scan_result: str = "pass",
        pii_detector_version: str | None = None,
        dense_embedding: list[float] | None = None,
        sparse_terms: dict[str, Any] | None = None,
        importance_score: float | None = None,
    ) -> dict[str, Any]:
        """Insert a memory from Admission. Deterministic tenant partition from here on."""
        row_id = uuid.uuid4()
        sparse = Jsonb(sparse_terms) if sparse_terms is not None else None
        with self.session() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO memories (
                      id, tenant_id, user_id, text, dense_embedding, sparse_terms,
                      admission_op, provenance, confidence, pii_scan_result,
                      pii_detector_version, importance_score
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, created_at
                    """,
                    (
                        str(row_id), tenant_id, user_id, text, dense_embedding,
                        sparse, admission_op, provenance, confidence,
                        pii_scan_result, pii_detector_version, importance_score,
                    ),
                )
                row = cur.fetchone()
        return {"id": row["id"], "created_at": row["created_at"]}

    def supersede(self, *, record_id: str, tenant_id: str) -> bool:
        """Deterministic supersession (Week 1): close the validity window of the
        current row for the same entity — always scoped by tenant."""
        closed_at = self._now()
        with self.session() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE memories
                       SET valid_until = %s
                     WHERE id = %s AND tenant_id = %s AND valid_until IS NULL
                    """,
                    (closed_at, record_id, tenant_id),
                )
                return cur.rowcount > 0

    def delete(self, *, record_id: str, tenant_id: str) -> bool:
        """Physical purge — soft-delete flags are forbidden for privacy deletion (invariant 2)."""
        with self.session() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM memories WHERE id = %s AND tenant_id = %s RETURNING id",
                    (record_id, tenant_id),
                )
                return cur.fetchone() is not None

    def get_active(self, *, tenant_id: str, limit: int = 50, user_id: str | None = None) -> list[dict[str, Any]]:
        """Active, in-window rows for a tenant; every read pre-filters tenant_id."""
        sql = """
            SELECT id, user_id, text, admission_op, provenance, confidence,
                   pii_scan_result, valid_from, valid_until, status
              FROM memories
             WHERE tenant_id = %s AND status = 'active' AND valid_until IS NULL
        """
        params: list[Any] = [tenant_id]
        if user_id is not None:
            sql += " AND user_id = %s"
            params.append(user_id)
        sql += " ORDER BY valid_from DESC LIMIT %s"
        params.append(limit)
        with self.session() as conn:
            rows = conn.execute(sql, params).fetchall()
        return rows

    def search_dense(
        self, *, tenant_id: str, query_embedding: list[float], limit: int = 5, user_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Tenant-scoped HNSW search (cosine). Returns rows + distance."""
        sql = """
            SELECT id, text, tenant_id, user_id, provenance, confidence,
                   (dense_embedding <=> %s::vector) AS cosine_dist
              FROM memories
             WHERE tenant_id = %s AND status = 'active' AND valid_until IS NULL
               AND dense_embedding IS NOT NULL
        """
        params: list[Any] = [query_embedding, tenant_id]
        if user_id is not None:
            sql += " AND user_id = %s"
            params.append(user_id)
        sql += " ORDER BY cosine_dist ASC LIMIT %s"
        params.append(limit)
        with self.session() as conn:
            rows = conn.execute(sql, params).fetchall()
        return rows

    def index_names(self) -> list[str]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT indexname FROM pg_indexes
                 WHERE tablename='memories' ORDER BY indexname
                """
            ).fetchall()
        return [r["indexname"] for r in rows]