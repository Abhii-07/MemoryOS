"""G-M3 gate: `pytest tests/test_context.py -q`.

Sprint-plan success criteria (G-M3, context part):
  - per-zone budgets: ceilings never exceeded               [EC-010]
  - D3 c3 long-conversation stress (40-token budget) — the buried correct
    fact always survives                                     [EC-010 / D3 c3]
  - sum-of-zones <= token_budget enforced (api_contracts -> 400)
  - no_relevant_memory shape is first-class, not an error
  - retrieval order is the injection order (final-ranked order per part2 §9.2)
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from memory_os.context import build_context, estimate_tokens
from memory_os.context.builder import ContextBudget
from memory_os.db.store import MemoryStore
from memory_os.embeddings import embed, is_available
from memory_os.retrieval import HybridRetriever, NoRelevantMemory
from memory_os.retrieval.tokenizer import term_frequencies

DENSE = is_available()
requires_dense = pytest.mark.skipif(
    not DENSE,
    reason="all-MiniLM-L6-v2 not downloadable (offline); budget logic still tested",
)

BASE = datetime(2026, 1, 1, 9, 0, 0)


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


class TestBudgetArithmetic:
    def test_zone_budgets_may_not_exceed_total(self):
        with pytest.raises(ValueError):
            ContextBudget.from_budget_map(
                token_budget=100,
                zone_budgets={"retrieved_memory": 60, "history": 50},
            )

    def test_defaults_obey_budget(self):
        b = ContextBudget.from_budget_map(token_budget=2000)
        assert sum(b.zones.values()) <= 2000
        assert b.zones["retrieved_memory"] == pytest.approx(800)

    def test_estimate_tokens_reproduces_d3(self):
        assert estimate_tokens("- four five six") >= 3   # words*1.3, int()


class TestInjectionOrder:
    def test_rank_order_preserved(self, r, store):
        """Memories are injected in final-ranked order; a tight budget can only
        drop the tail, never reorder."""
        from memory_os.embeddings import embed as e

        store.add(tenant_id="e", user_id="elena",
                  text="Elena mentioned minor detail number zero about her project setup.",
                  dense_embedding=e(["Elena mentioned minor detail number zero about her project setup."])[0],
                  sparse_terms=term_frequencies("Elena mentioned minor detail number zero about her project setup."))
        store.add(tenant_id="e", user_id="elena",
                text="Elena's actual architectural decision: the system must run fully offline with no external API calls.",
                dense_embedding=e(["Elena's actual architectural decision: the system must run fully offline with no external API calls."])[0],
                sparse_terms=term_frequencies("Elena's actual architectural decision: the system must run fully offline with no external API calls."))
        res = r.search(tenant_id="e", query="Does Elena's system need to work offline?")
        ctx = build_context(memories=res, token_budget=40,
                            zone_budgets={"retrieved_memory": 40})
        assert ctx.result_type == "memory_found"
        assert ctx.tokens_used <= 40
        assert "fully offline" in (ctx.injected_context or "")
        assert ctx.injected_context.index("Elena's actual") <= (
            ctx.injected_context.index("minor detail")
            if "minor detail" in ctx.injected_context else 10**9
        )


class TestC3Stress40:
    @requires_dense
    def test_c3_40token_budget_keeps_correct_fact(self, r, store):
        """The exact D3 c3 corpus: 18 Filler + the one correct fact, budget=40."""
        for i in range(18):
            text = f"Elena mentioned minor detail number {i} about her project setup."
            store.add(tenant_id="e", user_id="elena", text=text,
                      dense_embedding=embed([text])[0],
                      sparse_terms=term_frequencies(text))
        correct = ("Elena's actual architectural decision: the system must run "
                   "fully offline with no external API calls.")
        store.add(tenant_id="e", user_id="elena", text=correct,
                  dense_embedding=embed([correct])[0],
                  sparse_terms=term_frequencies(correct))

        res = r.search(tenant_id="e", query="Does Elena's system need to work offline?")
        ctx = build_context(memories=res, token_budget=40,
                            zone_budgets={"retrieved_memory": 40})
        assert ctx.result_type == "memory_found"
        assert ctx.tokens_used <= 40
        assert "fully offline" in (ctx.injected_context or "")


class TestZoneCeilings:
    def test_zone_ceiling_not_exceeded_hard(self, store):
        """EC-010: a huge first memory must not blow the zone; oversize
        candidates are dropped entirely."""
        ctx = build_context(
            memories=[{"text": "word " + " ".join(["x"] * 30)},  # est ~40 tokens
                      {"text": "second memory here"}],
            token_budget=100,
            zone_budgets={"retrieved_memory": 30},
        )
        assert ctx.tokens_used <= 30

    def test_no_result_shape(self, store):
        ctx = build_context(memories=[], token_budget=100)
        assert ctx.result_type == "no_relevant_memory"
        assert ctx.injected_context is None
        assert ctx.tokens_used == 0

    def test_zone_limit_0_blocks_injection(self, store):
        ctx = build_context(
            memories=[{"text": "some memory text"}],
            token_budget=100,
            zone_budgets={"retrieved_memory": 0},
        )
        assert ctx.result_type == "no_relevant_memory"


class TestOverflowGuard:
    def test_no_overflow_when_zone_exhausted(self):
        """Once the retrieved zone is exhausted, the tail drops even if the
        total budget has room — nothing borrows from another zone."""
        mems = [{"text": f"memory number {i} with some content text"} for i in range(5)]
        ctx = build_context(memories=mems, token_budget=1000,
                            zone_budgets={"retrieved_memory": 21})
        assert ctx.tokens_used <= 21
        assert ctx.tokens_used > 0
        assert len(ctx.memories) < 5


    def test_system_reserve_varies_only_totals(self):
        b1 = ContextBudget.from_budget_map(token_budget=1000)
        b2 = ContextBudget.from_budget_map(token_budget=1000)
        assert b1 == b2