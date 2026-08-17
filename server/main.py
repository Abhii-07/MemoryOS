r"""MemoryOS API — FastAPI service implementing the 3 contract endpoints.

Endpoints (design/api_contracts.md):
  POST /v1/memory/turns   — admit a conversation turn
  POST /v1/memory/query   — retrieve + context-build for a query
  DELETE /v1/memory/{id}  — evict a memory + propagate lineage

Design principles:
  - "Nothing relevant found" is a valid 200, not an error.
  - Deletion returns 200 (complete) or 202 (in-progress), never false-positive.
  - tenant_id is enforced at the API boundary.

Run:
  MEMORYOS_DB_DSN=postgresql://memoryos@localhost:5432/memoryos \
  uvicorn main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import os
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ── engine imports (src/ on PYTHONPATH) ──────────────────────────────────────
_SRC = str(Path(__file__).resolve().parent.parent / "implementation" / "MemoryOS-App" / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from memory_os.admission.admitter import Admitter, AdmissionResult
from memory_os.context.builder import ContextBudget, ContextResult, build_context
from memory_os.db.store import MemoryStore
from memory_os.retrieval.hybrid import HybridRetriever, NoRelevantMemory

# ── config ───────────────────────────────────────────────────────────────────
DEFAULT_DSN = os.environ.get(
    "MEMORYOS_DB_DSN", "postgresql://memoryos@localhost:5432/memoryos"
)
PROPAGATION_SYNC_LIMIT = int(os.environ.get("MEMORYOS_PROPAGATION_SYNC_LIMIT", "20"))

# ── engine singletons (lazy init, thread-safe) ──────────────────────────────
store = MemoryStore(dsn=DEFAULT_DSN)

_engine_lock = threading.Lock()
_engine_ready = False
_admitter: Admitter | None = None
_retriever: HybridRetriever | None = None


def _get_engine() -> tuple[Admitter, HybridRetriever]:
    global _engine_ready, _admitter, _retriever
    if not _engine_ready:
        with _engine_lock:
            if not _engine_ready:
                _admitter = Admitter(store)
                _retriever = HybridRetriever(store)
                _engine_ready = True
    assert _admitter is not None and _retriever is not None
    return _admitter, _retriever


# ── FastAPI app ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="MemoryOS API",
    version="1.0.0",
    description="Conversational Memory Intelligence System — contract endpoints.",
)

_cors_origins = os.environ.get("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    try:
        v = store.apply_schema()
        print(f"[startup] schema ok (pgvector {v})", flush=True)
    except Exception as exc:
        print(f"[startup] apply_schema deferred ({exc!r}); retried on first request", flush=True)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    try:
        with store.connect() as conn:
            conn.execute("SELECT 1")
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"pg unreachable: {exc!r}")
    return {"status": "ok"}


# ── request / response models ────────────────────────────────────────────────
class TurnsRequest(BaseModel):
    tenant_id: str = Field(min_length=1, max_length=128)
    user_id: str = Field(min_length=1, max_length=128)
    text: str = Field(min_length=1, max_length=4000)
    turn_type: str = Field(default="user", pattern="^(user|assistant)$")
    timestamp: str = Field(description="ISO 8601 datetime")


class TurnsResponse(BaseModel):
    record_id: str | None = None
    admission_op: str
    provenance: str | None = None
    pii_scan_result: str
    superseded_id: str | None = None


class QueryRequest(BaseModel):
    tenant_id: str = Field(min_length=1, max_length=128)
    user_id: str = Field(min_length=1, max_length=128)
    query_text: str = Field(min_length=1, max_length=4000)
    token_budget: int = Field(ge=1, le=100000, default=2048)
    zone_budgets: dict[str, int] | None = None


class MemoryHit(BaseModel):
    record_id: str
    text: str
    final_score: float
    provenance: str
    superseded: bool


class QueryMemoryFound(BaseModel):
    result_type: str = "memory_found"
    injected_context: str
    tokens_used: int
    zones_used: dict[str, int]
    memories: list[MemoryHit]


class QueryNoRelevant(BaseModel):
    result_type: str = "no_relevant_memory"
    injected_context: None = None
    tokens_used: int = 0
    memories: list = []


class DeleteComplete(BaseModel):
    deleted_id: str
    propagated_ids: list[str]
    propagation_status: str = "complete"


class DeleteInProgress(BaseModel):
    deleted_id: str
    propagation_status: str = "in_progress"
    check_url: str


class DeletionStatusResponse(BaseModel):
    job_id: str
    propagation_status: str
    deleted_id: str
    propagated_ids: list[str] = []


# ── Endpoint 1: POST /v1/memory/turns ───────────────────────────────────────
@app.post("/v1/memory/turns", response_model=TurnsResponse)
def admit_turn(body: TurnsRequest) -> dict[str, Any]:
    admitter, _ = _get_engine()

    try:
        datetime.fromisoformat(body.timestamp)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="invalid timestamp format; expected ISO 8601")

    with _engine_lock:
        result: AdmissionResult = admitter.admit(
            tenant_id=body.tenant_id,
            user_id=body.user_id,
            text=body.text,
            turn_type=body.turn_type,
        )

    return {
        "record_id": str(result.record_id) if result.record_id else None,
        "admission_op": result.admission_op,
        "provenance": result.provenance,
        "pii_scan_result": result.pii_scan_result,
        "superseded_id": str(result.superseded_id) if result.superseded_id else None,
    }


# ── Endpoint 2: POST /v1/memory/query ───────────────────────────────────────
@app.post("/v1/memory/query")
def query_memory(body: QueryRequest) -> dict[str, Any]:
    if body.zone_budgets:
        total_zones = sum(body.zone_budgets.values())
        if total_zones > body.token_budget:
            raise HTTPException(
                status_code=400,
                detail=f"zone budgets sum ({total_zones}) exceeds token_budget ({body.token_budget})",
            )

    _, retriever = _get_engine()

    with _engine_lock:
        try:
            hits = retriever.search(
                tenant_id=body.tenant_id,
                query=body.query_text,
                limit=5,
                user_id=body.user_id,
            )
        except NoRelevantMemory:
            hits = []

    if not hits:
        return {
            "result_type": "no_relevant_memory",
            "injected_context": None,
            "tokens_used": 0,
            "memories": [],
        }

    ctx: ContextResult = build_context(
        memories=hits,
        token_budget=body.token_budget,
        zone_budgets=body.zone_budgets,
    )

    return {
        "result_type": ctx.result_type,
        "injected_context": ctx.injected_context,
        "tokens_used": ctx.tokens_used,
        "zones_used": ctx.zones_used,
        "memories": [
            {
                "record_id": str(h["id"]),
                "text": h["text"],
                "final_score": round(float(h.get("effective_score") or h.get("fused_score") or 0.0), 4),
                "provenance": h.get("provenance", "user_stated"),
                "superseded": h.get("status") != "active",
            }
            for h in hits
        ],
    }


# ── Endpoint 3: DELETE /v1/memory/{id} ──────────────────────────────────────
@app.delete("/v1/memory/{memory_id}")
def delete_memory(
    memory_id: str,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_user_id: str = Header(..., alias="X-User-ID"),
) -> dict[str, Any]:
    try:
        uuid_obj = uuid.UUID(memory_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid UUID format")

    with _engine_lock:
        deleted = store.delete(record_id=str(uuid_obj), tenant_id=x_tenant_id)

    if not deleted:
        with store.connect() as conn:
            row = conn.execute(
                "SELECT id, tenant_id FROM memories WHERE id = %s",
                (str(uuid_obj),),
            ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="memory not found or already evicted")
        if row["tenant_id"] != x_tenant_id:
            raise HTTPException(status_code=403, detail="memory belongs to a different tenant")
        raise HTTPException(status_code=404, detail="memory not found or already evicted")

    with _engine_lock:
        derived = store.get_derived(tenant_id=x_tenant_id, source_id=str(uuid_obj))

    if len(derived) <= PROPAGATION_SYNC_LIMIT:
        propagated_ids = []
        for d in derived:
            with _engine_lock:
                store.delete(record_id=str(d["id"]), tenant_id=x_tenant_id)
            propagated_ids.append(str(d["id"]))
        return {
            "deleted_id": str(uuid_obj),
            "propagated_ids": propagated_ids,
            "propagation_status": "complete",
        }

    job_id = store.create_propagation_job(tenant_id=x_tenant_id, deleted_id=str(uuid_obj))
    return {
        "deleted_id": str(uuid_obj),
        "propagation_status": "in_progress",
        "check_url": f"/v1/memory/deletion-status/{job_id}",
    }


# ── deletion status check (for 202 async propagation) ──────────────────────
@app.get("/v1/memory/deletion-status/{job_id}", response_model=DeletionStatusResponse)
def deletion_status(job_id: str) -> dict[str, Any]:
    job = store.get_propagation_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return {
        "job_id": job_id,
        "propagation_status": job.get("status", "in_progress"),
        "deleted_id": job.get("deleted_id", ""),
        "propagated_ids": job.get("propagated_ids", []),
    }
