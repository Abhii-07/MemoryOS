"""G-M4 gate: `pytest tests/test_lifecycle.py -q`.

Sprint-plan success criteria (post-G-M3 follow-up):
  - four-lever consolidation: merge / decay / eviction as designed (Week 1)
  - `consolidation_lineage` walks: a deletion request against a source record
    removably affects every derived artifact               [EC-04 / ADR-005]
  - no lineage guarantees until here — the "leak via summary" test must be a
    real merge-then-delete case (threat_model Threat-4 validation plan)
  - multi-level lineage (summary-of-summary) rebuilt correctly — the hardest
    case named in ADR-005   [ADR-005 revisit condition exercised]
  - api_contracts Endpoint 3 semantics: complete vs 202 in_progress with a
    check_url, idempotent retries, 404 for missing records
  - growth is bounded/prunable: decay + eviction shrink the working set
    [EC-14]
  - every cascade is tenant-scoped (B never affected by A's delete)
"""

import uuid

import pytest

from memory_os.db.store import MemoryStore
from memory_os.lifecycle import (
    DeletionResult,
    LifecycleError,
    LifecycleManager,
    SUMMARY_PREFIX,
)


@pytest.fixture(scope="module")
def store():
    st = MemoryStore()
    st.apply_schema()  # idempotent
    return st


@pytest.fixture(autouse=True)
def clean(store):
    with store.connect() as c:
        c.execute("DELETE FROM memories")
        c.execute("DELETE FROM propagation_jobs")
    yield
    with store.connect() as c:
        c.execute("DELETE FROM memories")
        c.execute("DELETE FROM propagation_jobs")


@pytest.fixture()
def lm(store):
    return LifecycleManager(store)


def add(store, text, *, importance=0.5, tenant="t", user="alice", lineage=None):
    return str(
        store.add(
            tenant_id=tenant, user_id=user, text=text,
            importance_score=importance,
            consolidation_lineage=lineage or None,
        )["id"]
    )


class TestMerge:
    def test_consolidate_marks_sources_merged(self, store, lm):
        a = add(store, text="uses Postgres for payments")
        b = add(store, text="uses Adyen as gateway")
        summary_id, sources = lm.consolidate(tenant_id="t", user_id="alice",
                                             source_ids=[a, b])
        assert sources == [a, b]
        assert summary_id != a
        with store.connect() as c:
            rows = c.execute(
                "SELECT id, status, consolidation_lineage FROM memories "
                " WHERE id = ANY(%s::uuid[])",
                ([summary_id],),
            ).fetchall()
        assert rows[0]["status"] == "active"
        assert rows[0]["consolidation_lineage"] == [uuid.UUID(a), uuid.UUID(b)]
        # sources retained for lineage integrity — but no longer retrievable
        active = [r["id"] for r in store.get_active(tenant_id="t")]
        assert a not in [str(i) for i in active]
        assert str(summary_id) in [str(i) for i in active]

    def test_consolidate_summary_is_deterministic(self, store, lm):
        a = add(store, "beta drift")
        b = add(store, "alpha burn")
        s1, _ = lm.consolidate(tenant_id="t", user_id="alice", source_ids=[a, b])
        s2, _ = lm.consolidate(tenant_id="t", user_id="alice", source_ids=[a, b])
        with store.connect() as c:
            t1 = c.execute("SELECT text FROM memories WHERE id=%s", (s1,)).fetchone()["text"]
            t2 = c.execute("SELECT text FROM memories WHERE id=%s", (s2,)).fetchone()["text"]
        assert t1 == t2

    def test_consolidate_rejects_foreign_source(self, store, lm):
        a = add(store, "tenant A fact", tenant="tenant-a")
        with pytest.raises(LifecycleError):
            lm.consolidate(tenant_id="tenant-b", user_id="bob", source_ids=[a])
        with pytest.raises(LifecycleError):
            lm.consolidate(tenant_id="t", user_id="alice", source_ids=["00000000-0000-0000-0000-000000000000"])

    def test_summary_provenance_is_synthetic(self, store, lm):
        a = add(store, "some fact")
        sum_id, _ = lm.consolidate(tenant_id="t", user_id="alice", source_ids=[a])
        with store.connect() as c:
            prov = c.execute(
                "SELECT provenance FROM memories WHERE id = %s", (sum_id,)
            ).fetchone()
        assert prov["provenance"] == "assistant_generated"  # never user_stated


class TestEvictionBasics:
    def test_missing_record_is_404_shaped(self, store, lm):
        r = lm.evict(tenant_id="t", record_id=str(uuid.uuid4()))
        assert r.deleted_id is None
        assert r.complete
        assert r.propagated_ids == ()

    def test_evict_with_no_derived_is_complete(self, store, lm):
        a = add(store, "lonely fact")
        r = lm.evict(tenant_id="t", record_id=a)
        assert r.deleted_id == a
        assert r.propagated_ids == ()
        assert r.complete
        with store.connect() as c:
            gone = c.execute(
                "SELECT 1 FROM memories WHERE id = %s", (a,)
            ).fetchone()
        assert gone is None  # physical purge, no soft flag (invariant #2)


class TestLeakViaSummary:
    """EC-04 / ADR-005 validation: the merge-then-delete test that actually
    exercises the decision — delete a raw source, the regenerated summary
    must not contain its fact (threat_model Threat-4)."""

    def test_summary_regenerated_without_deleted_fact(self, store, lm):
        a = add(store, "taco place is near the office")
        b = add(store, "server maintenance is Saturday midnight")
        sum_id, _ = lm.consolidate(tenant_id="t", user_id="alice", source_ids=[a, b])
        with store.connect() as c:
            before = c.execute(
                "SELECT text FROM memories WHERE id = %s", (sum_id,)
            ).fetchone()["text"]
        assert "taco" in before

        r = lm.evict(tenant_id="t", record_id=a)
        assert r.complete
        assert sum_id in r.propagated_ids
        with store.connect() as c:
            after = c.execute(
                "SELECT text, consolidation_lineage FROM memories WHERE id = %s",
                (sum_id,),
            ).fetchone()
        assert "taco" not in after["text"]          # EC-004: no leak via summary
        assert "server maintenance" in after["text"]
        assert set(str(x) for x in after["consolidation_lineage"]) == {b}
        assert after["text"].startswith(SUMMARY_PREFIX % 1)

    def test_derived_with_no_survivors_is_evicted(self, store, lm):
        a = add(store, "fact one")
        b = add(store, "fact two")
        sum_id, _ = lm.consolidate(tenant_id="t", user_id="alice", source_ids=[a, b])
        lm.evict(tenant_id="t", record_id=a)
        r = lm.evict(tenant_id="t", record_id=b)
        assert sum_id in r.propagated_ids
        with store.connect() as c:
            gone = c.execute(
                "SELECT 1 FROM memories WHERE id = %s", (sum_id,)
            ).fetchone()
        assert gone is None


class TestMultiLevelLineage:
    """ADR-005's hardest named case: a record derived from already-consolidated
    records (summary-of-summary) must rebuild both levels on one delete."""

    def test_deep_cascade_never_leaks(self, store, lm):
        s1 = add(store, "alpha the original")
        s2 = add(store, "beta the second")
        s3 = add(store, "gamma the third")
        c1, _ = lm.consolidate(tenant_id="t", user_id="alice", source_ids=[s1, s2])
        c2, _ = lm.consolidate(tenant_id="t", user_id="alice", source_ids=[c1, s3])

        r = lm.evict(tenant_id="t", record_id=s1)
        assert r.complete
        assert {c1, c2} <= set(r.propagated_ids)
        with store.connect() as c:
            t1 = c.execute("SELECT text FROM memories WHERE id = %s", (c1,)).fetchone()["text"]
            t2 = c.execute("SELECT text FROM memories WHERE id = %s", (c2,)).fetchone()["text"]
        assert "original" not in t1
        assert "second" in t1
        assert "original" not in t2
        assert "second" in t2 and "third" in t2

    def test_depth_cap_evicts_rather_than_rebuild(self, store):
        lm = LifecycleManager(store, max_lineage_depth=2)
        s1 = add(store, "first fact")
        s2 = add(store, "second fact")
        c1, _ = lm.consolidate(tenant_id="t", user_id="alice", source_ids=[s1, s2])
        c2, _ = lm.consolidate(tenant_id="t", user_id="alice", source_ids=[c1])
        c3, _ = lm.consolidate(tenant_id="t", user_id="alice", source_ids=[c2])
        r = lm.evict(tenant_id="t", record_id=s1)
        with store.connect() as c:
            alive = c.execute(
                "SELECT id FROM memories WHERE tenant_id='t' ORDER BY id"
            ).fetchall()
        ids = {str(x["id"]) for x in alive}
        assert c3 not in ids          # depth 3 > cap 2 → evicted (ADR-005 policy)
        assert c2 in ids              # depth 2 == cap → rebuilt from survivor c1
        assert c1 in ids              # rebuilt from survivor s2
        with store.connect() as c:
            t1 = c.execute(
                "SELECT text FROM memories WHERE id = %s", (c1,)
            ).fetchone()["text"]
        assert "first fact" not in t1
        assert "second fact" in t1


class TestDecaySoft:
    def test_decay_candidates_find_low_importance_old(self, store, lm):
        a = add(store, "forgettable detail", importance=0.1)
        b = add(store, "critical fact", importance=0.9)
        with store.connect() as c:
            c.execute(
                "UPDATE memories SET valid_from = now() - interval '200 days' "
                " WHERE id = ANY(%s::uuid[])",
                ([a, b],),
            )
        cands = lm.decay_candidates(tenant_id="t", max_age_days=180)
        assert [r["id"] for r in cands] == [uuid.UUID(a)]

    def test_decay_is_soft_and_removes_from_active(self, store, lm):
        a = add(store, "this will fade", importance=0.1)
        assert lm.decay_eligible(tenant_id="t", record_id=a)
        assert lm.decay(tenant_id="t", record_id=a)
        with store.connect() as c:
            row = c.execute(
                "SELECT status FROM memories WHERE id = %s", (a,)
            ).fetchone()
        assert row["status"] == "decayed"          # soft: row still exists
        assert str(a) not in [str(r["id"]) for r in store.get_active(tenant_id="t")]
        assert not lm.decay_eligible(tenant_id="t", record_id=a)


class TestGrowthBound:
    """EC-014: a long-lived tenant is bounded — prune path actually shrinks."""

    def test_decay_then_evict_reduces_population(self, store, lm):
        for i in range(20):
            add(store, f"minor detail {i}", importance=0.1)
        add(store, "kept fact", importance=0.99)
        with store.connect() as c:
            c.execute(
                "UPDATE memories SET valid_from = now() - interval '400 days' "
                " WHERE importance_score <= 0.1::float4"
            )
        cands = lm.decay_candidates(tenant_id="t", max_age_days=180, limit=50)
        assert len(cands) == 20
        for c in cands:
            lm.decay(tenant_id="t", record_id=str(c["id"]))
        active = store.get_active(tenant_id="t")
        assert len(active) == 1
        # eviction shrinks even the physical rows
        for c in cands:
            lm.evict(tenant_id="t", record_id=str(c["id"]))
        with store.connect() as c:
            left = c.execute("SELECT COUNT(*) AS n FROM memories").fetchone()["n"]
        assert left == 1


class TestEvictionSemantics:
    def test_202_shaped_in_progress_for_large_cascade(self, store):
        lm = LifecycleManager(store, max_sync_derived=1)
        s1 = add(store, "one")
        d1, _ = lm.consolidate(tenant_id="t", user_id="alice", source_ids=[s1])
        s2 = add(store, "two")
        d2, _ = lm.consolidate(tenant_id="t", user_id="alice", source_ids=[s1, s2])
        r = lm.evict(tenant_id="t", record_id=s1)
        assert r.propagation_status == "in_progress"
        assert r.job_id is not None
        assert r.check_url == f"/memory/deletion-status/{r.job_id}"
        assert r.propagated_ids == ()   # honest: nothing claimed done yet

        done = lm.run_propagation_job(job_id=r.job_id)
        assert done.complete
        assert {d1, d2} <= set(done.propagated_ids)

        # idempotent retry of the check target verifies completed state
        replay = lm.run_propagation_job(job_id=r.job_id)
        assert replay.complete
        assert replay.propagated_ids == ()

    def test_cascade_within_threshold_completes_sync(self, store, lm):
        s1 = add(store, "root fact")
        d1, _ = lm.consolidate(tenant_id="t", user_id="alice", source_ids=[s1])
        r = lm.evict(tenant_id="t", record_id=s1)
        assert r.complete
        assert r.propagated_ids == (d1,)


class TestTenantScopingPropagation:
    def test_tenant_a_delete_never_touches_tenant_b(self, store, lm):
        a = add(store, "tenant A fact", tenant="tenant-a")
        b = add(store, "tenant B fact", tenant="tenant-b")
        # tenant B holds a summary whose lineage references A's id
        bsum = add(store, "B has a summary too", tenant="tenant-b",
                   lineage=[a])
        r = lm.evict(tenant_id="tenant-a", record_id=a)
        assert r.complete
        with store.connect() as c:
            b_row = c.execute(
                "SELECT text FROM memories WHERE id = %s", (b,)
            ).fetchone()
            bsum_row = c.execute(
                "SELECT text FROM memories WHERE id = %s", (bsum,)
            ).fetchone()
        assert b_row is not None
        assert bsum_row is not None  # not rebuilt, not touched, no false shadow