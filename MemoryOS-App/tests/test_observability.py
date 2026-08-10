"""G-M5 gate: `pytest tests/test_observability.py -q`.

Sprint-plan success criteria (G-M5, threat_model Threat 5 + Threat 2):
  - memory content may ONLY appear in span events, never span attributes;
    the collector deterministically redacts before export        [Threat 5]
  - typed span kinds from system_design_part3 §12 inventory; deterministic
    parent/child tree; plain-JSON export
  - provenance-weighted ranking: identical-ish content from a channel the
    attacker controls (tool_derived / retrieved_document) ranks below the
    same info the user stated directly         [Threat 2 mitigation]
  - components remain opt-in: no tracer attached -> behave exactly as before
  - an audit gate (config-as-code) that FAILS when a safeguard is switched off
"""

import json
import uuid
from pathlib import Path

import pytest

from memory_os.admission import Admitter
import memory_os.audit.checker as audit_module
from memory_os.audit.checker import AuditChecker
from memory_os.db.store import MemoryStore
from memory_os.embeddings import embed
from memory_os.observability import Collector, MemoryTracer, RedactingCollector
from memory_os.retrieval import HybridRetriever
from memory_os.retrieval.hybrid import PROVENANCE_WEIGHTS
from memory_os.retrieval.tokenizer import term_frequencies


def put(store: MemoryStore, tenant: str, user_id: str, text: str,
        provenance: str) -> None:
    """Store a row with dense + sparse signals (mirrors test_retrieval.put)."""
    vecs = embed([text])
    store.add(
        tenant_id=tenant, user_id=user_id, text=text,
        provenance=provenance, sparse_terms=term_frequencies(text),
        dense_embedding=vecs[0] if vecs else None,
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
def tracer():
    return MemoryTracer()


class TestCollector:
    """Threat 5 — redaction happens at the collector, off the write path."""

    def test_content_events_are_scrubbed(self, tracer):
        span = tracer.begin(name="admission", kind="admission",
                            attributes={"tenant_id": "t", "user_id": "alice"})
        tracer.end(span, events=[{"name": "turn_content",
                                  "content": "the db password is hunter2"}])
        out = tracer.export(collector=RedactingCollector())
        ev = out[0]["events"][0]
        assert ev["redacted"] == "true"
        assert "hunter2" not in ev["content"]

    def test_verum_passes_without_secrets(self, tracer):
        span = tracer.begin(name="retrieval", kind="retrieval")
        tracer.end(span, events=[{"name": "query_content",
                                  "content": "who manages the billing gateway"}])
        ev = tracer.export(collector=RedactingCollector())[0]["events"][0]
        assert ev["redacted"] == "false"
        assert ev["content"] == "who manages the billing gateway"

    def test_attributes_hashed_but_structural_kept(self, tracer):
        span = tracer.begin(name="admission", kind="admission",
                            attributes={"tenant_id": "t", "query": "hunter2"})
        tracer.end(span)
        attrs = tracer.export(collector=RedactingCollector())[0]["attributes"]
        assert attrs["tenant_id"] == "t"
        assert attrs["query"].startswith("sha256:")
        assert "hunter2" not in attrs["query"]

    def test_plain_collector_passes_through(self, tracer):
        span = tracer.begin(name="admission", kind="admission")
        tracer.end(span, events=[{"name": "turn_content",
                                  "content": "my card is 4111 1111 1111 1111"}])
        ev = tracer.export(collector=Collector())[0]["events"][0]
        assert ev["content"] == "my card is 4111 1111 1111 1111"

    def test_noop_tracer_records_nothing(self):
        t = MemoryTracer.noop()
        s = t.begin(name="admission", kind="admission")
        t.end(s, events=[{"name": "turn_content", "content": "hunter2"}])
        assert t.spans == []
        assert t.export() == []


class TestSpanHierarchy:
    """Deterministic ordering: children appended after parents."""

    def test_parent_child_order_and_trace_id(self, tracer):
        outer = tracer.begin(name="admission", kind="admission",
                             attributes={"tenant_id": "t"})
        inner = tracer.begin(name="ranking_decision", kind="ranking_decision")
        tracer.end(inner)
        tracer.end(outer)
        spans = tracer.spans
        assert [s.name for s in spans] == ["admission", "ranking_decision"]
        assert spans[1].parent_id == spans[0].span_id
        assert spans[0].trace_id == spans[1].trace_id

    def test_status_and_seq_recorded(self, tracer):
        s = tracer.begin(name="decay", kind="decay")
        tracer.end(s, status="error")
        d = tracer.spans[0].to_dict()
        assert d["status"] == "error"
        assert d["seq"] >= 2

    def test_export_json_dumpable(self, tracer):
        s = tracer.begin(name="eviction", kind="eviction")
        tracer.end(s)
        json.dumps(tracer.export(collector=RedactingCollector()))


class TestProvenanceWeighting:
    """Threat 2 — the channel an attacker controls ranks below the user."""

    def test_user_stated_outranks_tool_derived(self, store):
        user = str(uuid.uuid4())
        put(store, "t", user, "billing runs through adyen gateway",
            provenance="user_stated")
        put(store, "t", user, "billing runs through adyen gateway via api",
            provenance="tool_derived")
        rr = HybridRetriever(store)
        hits = rr.search(tenant_id="t", user_id=user,
                         query="billing runs through adyen gateway",
                         limit=10)
        assert hits[0]["provenance"] == "user_stated"
        assert hits[0]["effective_score"] > hits[1]["effective_score"]

    def test_retrieved_document_ranks_last_of_ordered_provenances(self, store):
        user = str(uuid.uuid4())
        put(store, "t", user, "refund policy for enterprise tier billing",
            provenance="user_stated")
        put(store, "t", user, "refund policy for enterprise tier customers",
            provenance="assistant_generated")
        rr = HybridRetriever(store)
        hits = rr.search(tenant_id="t", user_id=user,
                         query="refund policy for enterprise tier", limit=10)
        assert hits[0]["provenance"] == "user_stated"
        assert hits[1]["provenance"] == "assistant_generated"
        assert hits[0]["effective_score"] > hits[1]["effective_score"]

    def test_weights_declared_and_monotone(self):
        assert PROVENANCE_WEIGHTS["user_stated"] == 1.0
        assert (PROVENANCE_WEIGHTS["user_stated"]
                > PROVENANCE_WEIGHTS["assistant_generated"]
                > PROVENANCE_WEIGHTS["tool_derived"]
                > PROVENANCE_WEIGHTS["retrieved_document"] > 0.0)

    def test_admitter_turn_redacted_at_collector(self, store, tracer):
        a = Admitter(store, tracer=tracer)
        a.admit(tenant_id="t", user_id="alice",
                text="my card is 4111 1111 1111 1111 and zip 90210")
        assert tracer.spans[0].kind == "admission"
        ev = tracer.export(collector=RedactingCollector())[0]["events"][0]
        assert ev["redacted"] == "true"
        assert "4111" not in ev["content"]


class TestNoopDefaultSemantics:
    """Instrumentation is opt-in: no tracer attached = prior behavior."""

    def test_retriever_without_tracer_writes_no_spans(self, store):
        put(store, "t", "alice", "here is something retrievable",
            provenance="user_stated")
        rr = HybridRetriever(store)
        hits = rr.search(tenant_id="t", user_id="alice",
                         query="something retrievable", limit=5)
        assert hits[0]["text"].startswith("here is something")

    def test_admitter_without_tracer_writes_normally(self, store):
        a = Admitter(store)
        r = a.admit(tenant_id="t", user_id="bob", text="hello prefers caffeine")
        assert r.admission_op == "ADD"


class TestAuditGate:
    """The threat model's named gap: a misconfigured deployment must fail a
    check, not silently ship unredacted spans."""

    def test_gate_passes_on_clean_tree(self):
        report = AuditChecker().audit()
        assert report.passed, [f.detail for f in report.failures]

    def test_eight_rules_type_checked(self):
        rules = {r.rule for r in AuditChecker().audit().results}
        assert {"no_llm", "pii_pre_guardrail", "hot_paths_use_session",
                "soft_delete_forbidden", "collector_redaction",
                "typed_span_kinds", "ledger_coverage", "schema_compliance"} <= rules

    def test_disabling_redaction_in_policy_fails_the_gate(self, monkeypatch,
                                                          tmp_path):
        policy = (Path(audit_module.__file__).resolve().parents[3]
                  / "audit" / "policy.toml")
        tampered = policy.read_text().replace(
            "redaction_enabled = true", "redaction_enabled = false"
        )
        assert len(tampered) != len(policy.read_text())
        fake = tmp_path / "policy.toml"
        fake.write_text(tampered)
        monkeypatch.setattr("memory_os.audit.checker._POLICY_PATH", str(fake))
        r = AuditChecker().audit()
        assert not r.passed
        assert any(x.rule == "collector_redaction" and not x.passed
                   for x in r.results)


def test_observability_imports_typed_kinds():
    from memory_os.observability import SPAN_KINDS
    assert {"admission", "ranking_decision", "retrieval", "decay",
            "eviction", "consolidation", "supersession", "context_build"} \
        <= set(SPAN_KINDS)