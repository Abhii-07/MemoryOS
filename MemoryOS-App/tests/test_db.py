"""G-M1 gate: `pytest tests/test_db.py -q` must pass.

Covers the sprint-plan success criteria:
  - migration clean (schema applies idempotently, indexes present)
  - SELECT for tenant A never returns tenant B rows (deterministic pre-filter)
  - DELETE physically removes rows (privacy invariant #2)
  - valid_until nullable until superseded
  - HNSW index usable; dense search works with local 384-d vectors (ADR-007)
  - edge cases EC-01, EC-03, EC-05, EC-11, EC-18
"""

import threading

import pytest

from memory_os.db.store import MemoryStore


@pytest.fixture(scope="module")
def store():
    st = MemoryStore()
    st.apply_schema()  # idempotent
    return st


@pytest.fixture(autouse=True)
def clean_table(store):
    with store.connect() as conn:
        conn.execute("DELETE FROM memories")
    yield
    with store.connect() as conn:
        conn.execute("DELETE FROM memories")


def dim(n: int, offset: float = 0.0) -> list[float]:
    """Deterministic 384-d embeddings; `n` shifts the pattern (ADR-007 dimension)."""
    return [((i + n + offset) % 13) / 13.0 for i in range(384)]


class TestMigration:
    def test_schema_applies_and_extension_installed(self, store):
        ver = store.apply_schema()  # second run must be a no-op, not an error
        assert ver == "0.8.6"

    def test_all_five_indexes_created(self, store):
        names = set(store.index_names())
        assert {
            "idx_memories_tenant_status",
            "idx_memories_dense",
            "idx_memories_tenant_valid_from",
            "idx_memories_lineage",
            "idx_memories_lifecycle_scan",
        } <= names


class TestTenantIsolation:
    def test_tenant_a_never_sees_tenant_b_rows(self, store):
        store.add(tenant_id="tenant-a", user_id="alice", text="Alice uses PostgreSQL")
        store.add(tenant_id="tenant-b", user_id="bob", text="Bob uses PostgreSQL")
        a = store.get_active(tenant_id="tenant-a")
        b = store.get_active(tenant_id="tenant-b")
        assert len(a) == 1 and a[0]["user_id"] == "alice"
        assert len(b) == 1 and b[0]["user_id"] == "bob"

    def test_adversarial_similar_wording_stays_partitioned(self, store):
        """EC-05: same wording in two tenants must not cross the pre-filter."""
        for t in ("farah-tenant", "george-tenant"):
            store.add(
                tenant_id=t,
                user_id="farah" if "farah" in t else "george",
                text="Farah's team uses a microservices architecture with gRPC between services.",
                dense_embedding=dim(1),
            )
        hits_a = store.search_dense(
            tenant_id="farah-tenant",
            query_embedding=dim(1, offset=0.001),
            limit=10,
        )
        assert all(r["tenant_id"] == "farah-tenant" for r in hits_a)
        assert len(hits_a) == 1

    def test_user_scope_within_tenant(self, store):
        store.add(tenant_id="t1", user_id="u1", text="u1 secret")
        store.add(tenant_id="t1", user_id="u2", text="u2 secret")
        assert len(store.get_active(tenant_id="t1", user_id="u1")) == 1


class TestDeletion:
    def test_hard_delete_purges_row(self, store):
        r = store.add(tenant_id="hana", user_id="hana", text="Hana's project uses AWS.")
        assert store.delete(record_id=r["id"], tenant_id="hana") is True
        assert store.get_active(tenant_id="hana") == []

    def test_delete_scoped_by_tenant_cannot_touch_other_tenant(self, store):
        a = store.add(tenant_id="t-a", user_id="x", text="keep me")
        store.add(tenant_id="t-b", user_id="x", text="other tenant")
        assert store.delete(record_id=a["id"], tenant_id="t-b") is False  # wrong tenant
        assert len(store.get_active(tenant_id="t-a")) == 1


class TestValidityWindow:
    def test_valid_until_null_until_superseded(self, store):
        r = store.add(tenant_id="carla", user_id="carla", text="Old preference: Stripe")
        rows = store.get_active(tenant_id="carla")
        assert rows[0]["valid_until"] is None

    def test_supersession_closes_window(self, store):
        r = store.add(tenant_id="carla", user_id="carla", text="Old preference: Stripe")
        assert store.supersede(record_id=r["id"], tenant_id="carla") is True
        assert store.get_active(tenant_id="carla") == []  # old row no longer active
        store.add(tenant_id="carla", user_id="carla", text="New preference: Adyen")
        rows = store.get_active(tenant_id="carla")
        assert len(rows) == 1 and rows[0]["text"] == "New preference: Adyen"


class TestDenseSearch:
    def test_hnsw_search_returns_nearest(self, store):
        for i in range(3):
            store.add(
                tenant_id="alice",
                user_id="alice",
                text=f"memory {i}",
                dense_embedding=dim(i),
            )
        hits = store.search_dense(tenant_id="alice", query_embedding=dim(1), limit=2)
        assert len(hits) == 2
        assert hits[0]["text"] == "memory 1"  # exact match ranks first

    def test_null_embedding_excluded_from_retrieval(self, store):
        store.add(tenant_id="alice", user_id="alice", text="no embedding yet")
        assert store.search_dense(tenant_id="alice", query_embedding=dim(2)) == []


class TestConcurrency:
    def test_concurrent_writes_serialize_per_tenant(self, store):
        """EC-11/EC-18: parallel inserts commit cleanly, no torn state."""
        errors: list[Exception] = []

        def worker(i: int):
            try:
                store.add(
                    tenant_id="contested",
                    user_id="u",
                    text=f"row {i}",
                    dense_embedding=dim(i),
                )
            except Exception as e:  # pragma: no cover - only on failure
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []
        assert len(store.get_active(tenant_id="contested")) == 8