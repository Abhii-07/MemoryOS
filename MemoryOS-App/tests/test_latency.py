"""EC-15 latency ceiling gate: p95 search latency < 150 ms at hosted scale.

Design (design/edge_cases.md): `pytest -m latency` — deterministic retrieval
must stay inside the invariant as the corpus grows. This seeds one fill of
LATENCY_ROWS (500) memorized rows into a dedicated tenant and times real
hybrid searches over that corpus.
"""

from __future__ import annotations

import time

import pytest

from memory_os.db.store import MemoryStore
from memory_os.embeddings import is_available
from memory_os.retrieval.hybrid import HybridRetriever, NoRelevantMemory

pytestmark = [
    pytest.mark.latency,
    pytest.mark.skipif(
        not is_available(), reason="embedder cache unavailable (ADR-007 offline fallback)"
    ),
]

LATENCY_ROWS = 500        # hosted-scale corpus fill (design EC-15)
QUERIES = 40              # enough samples for a stable p95
INVARIANT_MS = 150.0      # EC-15 ceiling
TENANT = "latency-gate"
USER = "gate-user"


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[int(round(len(ordered) * 0.95)) - 1]


@pytest.fixture(scope="module")
def store() -> MemoryStore:
    return MemoryStore()


@pytest.fixture(scope="module")
def corpus(store: MemoryStore):
    """One fill of LATENCY_ROWS rows with faithful dense+sparse embeddings on a
    dedicated tenant; torn down after the module."""
    from memory_os.embeddings import embed
    from memory_os.retrieval.tokenizer import term_frequencies

    with store.session() as conn:
        conn.execute("DELETE FROM memories WHERE tenant_id = %s", [TENANT])
    base = [
        "Project meeting about delivery milestones on 2026-01-12",
        "Renew the domain contract before March",
        "Team sync: the alpha release shipped with two blockers",
        "Expenses report deadline every first Friday",
        "Server maintenance window is Saturday midnight",
        "Design review mood board colors and finalize palette",
    ]
    for i in range(LATENCY_ROWS):
        text = f"{base[i % len(base)]} (entry {i})"
        store.add(
            tenant_id=TENANT,
            user_id=USER,
            text=text,
            provenance="user_stated",
            dense_embedding=embed([text])[0],
            sparse_terms=term_frequencies(text),
        )
    yield base
    with store.session() as s:
        s.execute("DELETE FROM memories WHERE tenant_id = %s", [TENANT])


def test_latency_p95_under_invariant(store: MemoryStore, corpus) -> None:
    retriever = HybridRetriever(store)
    queries = [
        "What are the milestones for the delivery window?",
        "when is our next delivery review?",
        "Tell me about project delivery",
        "What did we decide in the meeting?",
        "remove the last blockers from maintenance",
        "how many customers reported issues",
        "deadline for the expense report",
        "palette of the mood board update",
    ]
    turned = []
    for q in queries:
        for _ in range(QUERIES // len(queries) + 1):
            turned.append(q)
    turned = turned[:QUERIES]

    # warm-up: embedder + connection + planner caches
    for _ in range(3):
        try:
            retriever.search(tenant_id=TENANT, query="delivery milestones meeting")
        except NoRelevantMemory:
            pass

    samples: list[float] = []
    for q in turned:
        t0 = time.perf_counter()
        try:
            retriever.search(tenant_id=TENANT, query=q)
        except NoRelevantMemory:
            pass
        samples.append((time.perf_counter() - t0) * 1000)

    p95 = _p95(samples)
    assert p95 < INVARIANT_MS, (
        f"EC-15 violated: p95={p95:.1f}ms over {len(samples)} queries "
        f"(invariant < {INVARIANT_MS}ms)"
    )