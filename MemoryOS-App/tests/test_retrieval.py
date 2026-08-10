"""G-M2 gate: `pytest tests/test_retrieval.py -q`.

Sprint-plan success criteria:
  - retrieval uses the dense_embedding + sparse_terms columns
  - empty store -> graceful "no relevant memory"      [EC-08]
  - stopword-only query -> graceful empty result       [EC-09]
  - relevance floor drops below-threshold candidates   [EC-13]
  - D3's exact failing cases pass:
      c1 stale-outranks-current (fixed via supersession, not scoring)
      c6 false-positive relevance (fixed via the floor)
  - exact slot values (1992 != 1990)                   [EC-16]
  - No LLM on the request path (pure Python determinism)
"""

import pytest

from memory_os.db.store import MemoryStore
from memory_os.embeddings import embed, is_available
from memory_os.retrieval import HybridRetriever, NoRelevantMemory
from memory_os.retrieval.bm25 import corpus_stats, score
from memory_os.retrieval.rrf import fuse
from memory_os.retrieval.tokenizer import numeric_tokens, term_frequencies

DENSE = is_available()

requires_dense = pytest.mark.skipif(
    not DENSE,
    reason="all-MiniLM-L6-v2 not downloadable (offline); BM25-only fallback verified",
)


def put(store: MemoryStore, tenant: str, text: str) -> dict:
    """Store a row with dense (when the model is up) + sparse signals."""
    vecs = embed([text])
    return store.add(
        tenant_id=tenant, user_id=tenant, text=text,
        dense_embedding=vecs[0] if vecs else None,
        sparse_terms=term_frequencies(text),
    )


@pytest.fixture(scope="module")
def store():
    st = MemoryStore()
    st.apply_schema()
    return st


@pytest.fixture(autouse=True)
def clean(store):
    with store.connect() as c:
        c.execute("DELETE FROM memories")
    yield
    with store.connect() as c:
        c.execute("DELETE FROM memories")


@pytest.fixture()
def r(store):
    return HybridRetriever(store)


class TestColdStartAndVocabulary:
    def test_empty_store_returns_no_result(self, r):
        with pytest.raises(NoRelevantMemory):
            r.search(tenant_id="ivan", query="what did we agree on for deployment")

    def test_stopword_only_query_is_graceful(self, r, store):
        store.add(tenant_id="j", user_id="x", text="unrelated",
                  sparse_terms=term_frequencies("unrelated"))
        with pytest.raises(NoRelevantMemory):
            r.search(tenant_id="j", query="as if")


class TestRRFUnits:
    def test_fuse_rank_weighting_and_k60(self):
        a = fuse([["x", "y", "z"]])
        assert a["x"] == pytest.approx(1 / 61)
        assert a["y"] == pytest.approx(1 / 62)
        assert a["x"] > a["y"] > a["z"]  # rank 1 weighs more than rank 2, etc.

    def test_fuse_two_signals(self):
        two = fuse([["a", "b"], ["c", "a"]])
        assert two["a"] == pytest.approx(1 / 61 + 1 / 62)
        assert two["b"] == pytest.approx(1 / 62)
        assert two["c"] == pytest.approx(1 / 61)

    def test_fuse_k_default_60(self):
        one = fuse([["a"]])
        assert one["a"] == pytest.approx(1 / 61)


class TestBM25Units:
    def test_shared_terms_positive(self):
        corpi = [term_frequencies("alice runs the build"),
                 term_frequencies("bob tests the build")]
        n, avg, df = corpus_stats(corpi)
        s = score(["alice", "run"], term_frequencies("alice runs"), n, avg, df)
        assert s > 0

    def test_no_overlap_zero(self):
        n, avg, df = corpus_stats([term_frequencies("aaa")])
        assert score(["zzz"], term_frequencies("aaa"), n, avg, df) == 0.0


class TestSparseOnly:
    def test_sparse_only_row_retrieved(self, r, store):
        store.add(tenant_id="b", user_id="bob", text="Bob runs the build",
                  sparse_terms=term_frequencies("Bob runs the build"))
        res = r.search(tenant_id="b", query="who runs the build")
        assert res and res[0]["text"] == "Bob runs the build"

    def test_empty_sparse_terms_without_dense_falls_through(self, r, store):
        store.add(tenant_id="b", user_id="bob", text="no sparse terms",
                  sparse_terms=None, dense_embedding=None)
        with pytest.raises(NoRelevantMemory):
            r.search(tenant_id="b", query="does nothing match")


class TestD3FailingCases:
    @requires_dense
    def test_c1_stale_outranks_current_fixed(self, r, store):
        """c1 (D3): stale ('flexible') used to outrank 'now hard'. Here the
        superseded row leaves the candidate set before ranking. This still
        matters: on this embedder the stale row scores HIGHER (0.880 vs
        0.752) — so only supersession can keep it out; scoring can't."""
        stale = put(store, "bob", "Bob said the project deadline is flexible and can slip a week")
        put(store, "bob", "Bob later said the deadline is now hard -- no slippage")
        assert store.supersede(record_id=stale["id"], tenant_id="bob")
        res = r.search(tenant_id="bob", query="is Bob's project deadline flexible?")
        assert len(res) == 1
        assert "now hard" in res[0]["text"]

    @requires_dense
    def test_c6_no_relevant_memory_is_empty(self, r, store):
        """c6 (D3): unrelated lunch spot + Markdown notes must NOT answer the
        testing-framework question. Both candidates land below the floor
        (0.438 / 0.470 < 0.5) → explicit no-result instead of a wrong guess."""
        put(store, "julia", "Julia's favorite lunch spot is the taco place near the office.")
        put(store, "julia", "Julia likes her documentation written in Markdown.")
        with pytest.raises(NoRelevantMemory):
            r.search(tenant_id="julia",
                     query="What testing framework does Julia want to use for the new service?")

    @requires_dense
    def test_hybrid_paraphrase_hits(self, r, store):
        """MiniLM reach: the D3 paraphrase the TF-IDF-only signal missed now
        maps to cosine 0.801 (over the 0.5 floor) and ranks first."""
        put(store, "carla", "Carla is using a checkout integration built on Adyen instead of Stripe.")
        res = r.search(tenant_id="carla",
                       query="Which provider is Carla using for checkout integration?")
        assert res and "Adyen" in res[0]["text"]

    @requires_dense
    def test_c4_identical_wording_never_leaks_across_tenants(self, r, store):
        put(store, "farah", "Farah's team uses a microservices architecture with gRPC.")
        put(store, "george", "George's team uses a microservices architecture with gRPC too.")
        res = r.search(tenant_id="farah",
                       query="What architecture does Farah's team use?")
        assert res
        assert all("george" not in row["text"].lower() for row in res)


class TestExactSlotEC16:
    @requires_dense
    def test_year_slot_survives_embedding_fuzz(self, r, store):
        """1992 vs 1990 — the embedder treats both as 'the same era', so the
        sparse signal pins the exact number: the 1992 record surfaces, 1990
        never overtakes it."""
        put(store, "a", "Alice born in 1992.")
        put(store, "a", "Alice has been working since 1990.")
        res = r.search(tenant_id="a", query="when was Alice born? in 1992")
        assert res and res[0]["text"] == "Alice born in 1992."
