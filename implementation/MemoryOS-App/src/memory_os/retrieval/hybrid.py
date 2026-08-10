"""G-M2 hybrid retrieval: tenant-prefiltered BM25 + dense, fused by RRF.

Read-flow design (§9):
  Query -> tenant pre-filter (deterministic, before any scoring)
         -> BM25 + dense run in parallel over the tenant-filtered set
         -> Reciprocal Rank Fusion (k=60)
         -> relevance floor -> explicit `no_relevant_memory` (never an error)

No LLM anywhere on this path. Deterministic ranking.
"""

from __future__ import annotations

from typing import Any

from memory_os.db.store import MemoryStore
from memory_os.embeddings import embed, is_available
from memory_os.retrieval import bm25, rrf
from memory_os.retrieval.tokenizer import numeric_tokens, tokenize

# Relevance floor (§9 step 4): a fused candidate survives only if it clears a
# two-signal bar — dense cosine ≥ FLOOR_COSINE AND at least MIN_SHARED lexical
# terms in common with the query (numbers count: EC-16). A high-cosine
# carve-out (PARAPHRASE_COSINE) admits pure paraphrase hits (ADR-006: TF-IDF
# alone misses those) that share almost no surface tokens.
#
# Calibrated 2026-08-08 on D3's exact strings with all-MiniLM-L6-v2 (ADR-007):
#   keep: c1 0.657 · c2 0.731 · c4-farah 0.557 · ec16-92 0.945 · aws 0.867
#   drop: c6-lunch 0.426 · c6-docs 0.517 · c4-george 0.236 · ec16-90 0.721
# (c1's stale row scores 0.876 — HIGHER than current truth — so supersession,
# not the floor, is what keeps it out; that is the c1 regression proof.)
RELEVANCE_FLOOR_COSINE = 0.5
MIN_SHARED_TERMS = 2
PARAPHRASE_COSINE = 0.75
DENSE_TOP_N = 20
SPARSE_TOP_N = 20

# Provenance-weighted trust factor (system_design_part2 §9 final ordering;
# threat_model Threat-2 mitigation): content that entered via a channel an
# attacker controls is structurally disadvantaged in ranking, never on equal
# footing with something the user said directly.
PROVENANCE_WEIGHTS: dict[str, float] = {
    "user_stated": 1.0,
    "assistant_generated": 0.85,
    "tool_derived": 0.6,
    "retrieved_document": 0.5,
}


class NoRelevantMemory(Exception):
    """Explicit 'nothing relevant found' — a valid, expected outcome."""


class HybridRetriever:
    """Tenant-prefiltered BM25 + dense retrieval fused by RRF (k=60)."""

    def __init__(
        self,
        store: MemoryStore,
        *,
        floor: float = RELEVANCE_FLOOR_COSINE,
        min_shared: int = MIN_SHARED_TERMS,
        paraphrase_cosine: float = PARAPHRASE_COSINE,
        dense_top_n: int = DENSE_TOP_N,
        sparse_top_n: int = SPARSE_TOP_N,
        provenance_weights: dict[str, float] | None = None,
        tracer=None,
    ):
        self.store = store
        self.floor = floor
        self.min_shared = min_shared
        self.paraphrase_cosine = paraphrase_cosine
        self.dense_top_n = dense_top_n
        self.sparse_top_n = sparse_top_n
        self.provenance_weights = provenance_weights or dict(PROVENANCE_WEIGHTS)
        self._dense_available = is_available()
        self._tracer = tracer

    @property
    def dense_available(self) -> bool:
        return self._dense_available

    def search(self, *, tenant_id: str, query: str, limit: int = 5,
               user_id: str | None = None) -> list[dict[str, Any]]:
        """Hybrid search. Raises NoRelevantMemory when nothing passes the floor.

        Tenants can never see each other: candidates come only from rows whose
        WHERE tenant_id = %s matched, and BM25 corpus stats (df, avg-dl) are
        computed over that same pre-filtered set.
        """
        span = None
        if self._tracer is not None:
            span = self._tracer.begin(name="retrieval", kind="retrieval",
                                      attributes={"tenant_id": tenant_id})
        try:
            return self._search_impl(tenant_id=tenant_id, query=query,
                                     limit=limit, user_id=user_id)
        finally:
            if span is not None:
                self._tracer.end(span, events=[{"name": "query_content",
                                                "content": query[:200]}])

    def _search_impl(self, *, tenant_id: str, query: str, limit: int,
                     user_id: str | None) -> list[dict[str, Any]]:
        """Core search: tenant pre-filter, BM25 + dense, RRF fusion, floor."""
        q_tokens = tokenize(query)
        q_numbers = numeric_tokens(query)
        if not q_tokens and not q_numbers:
            raise NoRelevantMemory("empty vocabulary (EC-09)")

        query_embedding = None
        if self._dense_available:
            vecs = embed([query])
            query_embedding = vecs[0] if vecs else None

        # Signal 1 — dense (tenant-scoped HNSW, local 384-d embeddings).
        dense_rows: list[dict[str, Any]] = []
        if query_embedding is not None:
            dense_rows = self.store.search_dense(
                tenant_id=tenant_id, query_embedding=query_embedding,
                limit=self.dense_top_n, user_id=user_id)

        # Signal 2 — BM25 over the same tenant-filtered active rows.
        sparse_ids, sparse_rows = self._bm25_rank(
            tenant_id=tenant_id, query_tokens=q_tokens, numbers=q_numbers,
            user_id=user_id)

        if not dense_rows and not sparse_rows:
            raise NoRelevantMemory("store empty or no candidates (EC-08)")

        # Fusion: RRF (k=60) over the two ranked lists.
        dense_ids = [r["id"] for r in dense_rows]
        fused = rrf.fuse([dense_ids, sparse_ids])
        dense_by_id = {r["id"]: r for r in dense_rows}

        # Provenance-weighted final ordering (Threat-2 mitigation): the fused
        # score is multiplied by the channel's trust weight so a poisoned
        # tool_derived / retrieved_document row starts structurally lower
        # than the same content the user stated directly.
        picks: list[tuple[float, str]] = []
        for record_id, f_score in fused.items():
            provenance = (dense_by_id.get(record_id) or sparse_rows[record_id])["provenance"]
            effective = f_score * self.provenance_weights.get(provenance, 1.0)
            picks.append((effective, record_id, provenance))
        picks.sort(key=lambda t: t[0], reverse=True)

        results: list[dict[str, Any]] = []
        for effective, record_id, provenance in picks:
            dense_row = dense_by_id.get(record_id)
            cosine_sim = 1.0 - float(dense_row["cosine_dist"]) if dense_row else None
            if not self._passes_floor(record_id, cosine_sim, q_tokens, q_numbers,
                                      sparse_rows.get(record_id)):
                continue  # relevance floor (§9 step 4)
            row = {
                "id": record_id,
                "text": (dense_row or sparse_rows[record_id])["text"],
                "provenance": provenance,
                "confidence": (dense_row or sparse_rows[record_id])["confidence"],
                "fused_score": fused[record_id],
                "effective_score": effective,
            }
            if cosine_sim is not None:
                row["cosine_sim"] = cosine_sim
            if record_id in sparse_rows:
                row["bm25"] = sparse_rows[record_id]["bm25"]
            results.append(row)
            if len(results) >= limit:
                break

        if not results:
            raise NoRelevantMemory("nothing above the relevance floor (EC-13)")
        return results

    def _passes_floor(self, record_id: str, cosine_sim: float | None,
                      q_tokens: list[str], q_numbers: list[str],
                      sparse_row: dict[str, Any] | None) -> bool:
        """Two-signal floor. With no dense signal (BM25-only fallback mode)
        the lexical-shared-terms rule alone must hold."""
        shared = 0
        if sparse_row is not None:
            doc_terms = set(sparse_row.get("sparse_terms") or {})
            shared = len((set(q_tokens) | set(q_numbers)) & doc_terms)

        if cosine_sim is None:
            return shared >= self.min_shared  # BM25-only fallback (part3 §16)
        if cosine_sim >= self.paraphrase_cosine:
            return True  # high-cosine paraphrase: lexical overlap unreliable
        return cosine_sim >= self.floor and shared >= self.min_shared

    def _bm25_rank(self, *, tenant_id: str, query_tokens: list[str],
                   numbers: list[str], user_id: str | None
                   ) -> tuple[list[str], dict[str, dict[str, Any]]]:
        """Fetch the tenant's active rows, rank by BM25 over sparse_terms.

        Returns (ranked_ids, rows_by_id) using the same tenant pre-filter as
        every other read.
        """
        terms = query_tokens + numbers
        if not terms:
            return [], {}

        sql = """
            SELECT id, text, provenance, confidence,
                   COALESCE(sparse_terms, '{}'::jsonb) AS sparse_terms
              FROM memories
             WHERE tenant_id = %s AND status = 'active' AND valid_until IS NULL
               AND sparse_terms IS NOT NULL
        """
        params: list[Any] = [tenant_id]
        if user_id is not None:
            sql += " AND user_id = %s"
            params.append(user_id)

        with self.store.session() as conn:
            rows = conn.execute(sql, params).fetchall()

        term_freqs = [
            {k: int(v) for k, v in row["sparse_terms"].items()}
            for row in rows
        ]
        n_total, avg_dl, df = bm25.corpus_stats(term_freqs)
        rows_by_id: dict[str, dict[str, Any]] = {}
        scored: list[tuple[float, dict[str, Any]]] = []
        for i, row in enumerate(rows):
            s = bm25.score(terms, term_freqs[i], n_total, avg_dl, df)
            rich = dict(row)
            rich["bm25"] = s
            rows_by_id[row["id"]] = rich
            if s > 0:
                scored.append((s, rich))
        scored.sort(key=lambda kv: kv[0], reverse=True)
        ranked_ids = [rich["id"] for s, rich in scored][: self.sparse_top_n]
        return ranked_ids, rows_by_id