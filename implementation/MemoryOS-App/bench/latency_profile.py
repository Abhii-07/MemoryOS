"""EC-15 latency profile: per-phase timing for a hybrid search.

Usage (from repo root):
    python -m bench.latency_profile [--rows 500] [--queries 30]

Prints p50/p95/mean for: embed, dense SQL, bm25 fetch+score, fuse+floor, total.
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
import uuid

from memory_os.db.store import MemoryStore
from memory_os.embeddings import embed, is_available
from memory_os.retrieval.hybrid import HybridRetriever
from memory_os.retrieval.tokenizer import term_frequencies, tokenize

NS = "\x85"  # bookmark char as user separator


def ns() -> float:
    return time.perf_counter()


def p95(values: list[float]) -> float:
    if not values:
        return 0.0
    return sorted(values)[int(round(len(values) * 0.95)) - 1]


def seed(store: MemoryStore, tenant_id: str, rows: int) -> None:
    with store.session() as conn:
        dense_n = conn.execute(
            "SELECT count(*) AS n FROM memories "
            "WHERE tenant_id = %s AND dense_embedding IS NOT NULL",
            [tenant_id],
        ).fetchone()["n"]
    if dense_n >= rows:
        return
    with store.session() as conn:
        conn.execute("DELETE FROM memories WHERE tenant_id = %s", [tenant_id])
    texts = [
        f"Project meeting about delivery milestones on {date}"
        for date in ("2026-01-12", "2026-02-03", "2026-03-21", "2026-04-08")
    ]
    for i in range(rows):
        text = texts[i % len(texts)] + f" (id {i})"
        store.add(
            tenant_id=tenant_id,
            text=text,
            provenance="user_stated",
            user_id="bench-user",
            dense_embedding=embed([text])[0],
            sparse_terms=term_frequencies(text),
        )
    print(f"seeded {rows} rows into tenant '{tenant_id}'")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=500)
    ap.add_argument("--queries", type=int, default=30)
    args = ap.parse_args()

    store = MemoryStore()
    tenant = "load"
    seed(store, tenant, args.rows)

    print("dense available:", is_available())
    retriever = HybridRetriever(store)
    if not retriever.dense_available:
        print("FATAL: no embedder; run with the model cache available.")
        return 2

    queries = [
        "What are the milestones for the delivery project?",
        "when is the next meeting about delivery?",
        "Tell me about project milestones",
        "What did we say about the delivery timeline?",
        "remind me of the delivery date discussion",
        "Which milestones were discussed in January?",
    ]
    while len(queries) < args.queries:
        queries.append(queries[len(queries) % len(queries)])

    # warm up (model load + connection pool)
    for _ in range(3):
        try:
            retriever.search(tenant_id=tenant, query=queries[0])
        except Exception:
            pass

    totals: list[float] = []
    embed_t: list[float] = []
    dense_t: list[float] = []
    bm25_t: list[float] = []
    fuse_t: list[float] = []
    hits = 0

    # Time the component calls separately (search() does one embed + one dense
    # SQL + one bm25 fetch + fuse/floor; totals below measure a real search()).
    for q in queries[: args.queries]:
        q_tokens = tokenize(q)

        t1 = ns()
        vecs = embed([q])
        t2 = ns()
        embed_t.append(t2 - t1)
        query_embedding = vecs[0]

        t3 = ns()
        store.search_dense(
            tenant_id=tenant, query_embedding=query_embedding, limit=20
        )
        t4 = ns()
        dense_t.append(t4 - t3)

        t5 = ns()
        retriever._bm25_rank(
            tenant_id=tenant, query_tokens=q_tokens, numbers=[], user_id=None
        )
        t6 = ns()
        bm25_t.append(t6 - t5)

        t0 = ns()
        try:
            result = retriever.search(tenant_id=tenant, query=q)
            hits += len(result)
        except Exception:
            pass
        t8 = ns()
        fuse_t.append(t8 - t0)
        totals.append(t8 - t0)
        print(f"{q[:40]:42s} total {1e3*(t8-t0):7.1f}ms "
              f"(embed {1e3*(t2-t1):5.1f} dense {1e3*(t4-t3):5.1f} "
              f"bm25 {1e3*(t6-t5):6.1f} fuse {1e3*(t8-t0):5.1f})")

    def report(name: str, values: list[float]) -> None:
        print(f"{name:8s} p50 {1e3*statistics.median(values):7.1f}ms "
              f"p95 {1e3*p95(values):7.1f}ms "
              f"mean {1e3*statistics.mean(values):7.1f}ms")

    report("total", totals)
    report("embed", embed_t)
    report("dense", dense_t)
    report("bm25", bm25_t)
    report("fuse", fuse_t)
    print(f"hits/query {hits / len(totals):.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
