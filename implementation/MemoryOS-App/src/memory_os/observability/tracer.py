"""G-M5 observability: typed trace spans with collector-level redaction.

Implements the Week-3/4 adopted pattern (system_design_part3 §12, threat_model
Threat 5): every memory operation — admission, retrieval/ranking, supersession,
decay, eviction, consolidation — is a typed span. Memory CONTENT must live in
span *events* (filterable/droppable), never span *attributes*; the collector
sink redacts sensitive content deterministically before export, and the
redaction rule is itself written down as config-as-code (audit policy) so a
misconfigured deployment fails the audit gate instead of shipping unredacted.

Design de-facto constraints kept here:
- Deterministic: no wall-clock jitter in output ordering — children sort after
  parents by (start_seq, name).
- No extra dependencies: recorder is in-process; export() returns plain JSON.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from memory_os.admission import scrub_pii  # reuse the write-path redactor

# Typed span kinds (system_design_part3 §12 inventory).
SPAN_KINDS = (
    "admission",
    "ranking_decision",
    "retrieval",
    "supersession",
    "decay",
    "eviction",
    "consolidation",
    "context_build",
)


@dataclass
class Span:
    trace_id: str
    span_id: str
    name: str
    kind: str
    parent_id: str | None
    start_seq: int
    end_seq: int | None = None
    status: str = "ok"                     # ok | error
    attributes: dict[str, Any] = field(default_factory=dict)  # NEVER memory content
    events: list[dict[str, str]] = field(default_factory=list)  # content allowed (redacted at collector)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "kind": self.kind,
            "status": self.status,
            "seq": self.end_seq or self.start_seq,
            "attributes": self.attributes,
            "events": self.events,
        }


class MemoryTracer:
    """In-process typed-span tracer. `noop()` returns a tracer that records
    nothing — components default to it so instrumentation is opt-in."""

    def __init__(self):
        self._spans: list[Span] = []
        self._stack: list[str] = []
        self._seq = 0
        self._span_counter = 0
        self._trace = ""

    @classmethod
    def noop(cls) -> "MemoryTracer":
        return _NOOP

    def begin(self, *, name: str, kind: str, attributes: dict[str, Any] | None = None) -> Span:
        if self is _NOOP:
            return _span_placeholder(name, kind)
        self._seq += 1
        self._span_counter += 1
        parent = self._stack[-1] if self._stack else None
        if parent is None:
            self._trace = f"t-{self._span_counter}"
        span = Span(
            trace_id=self._trace,
            span_id=f"s-{self._span_counter}",
            name=name, kind=kind, parent_id=parent,
            attributes=attributes or {},
            start_seq=self._seq,
        )
        self._spans.append(span)
        self._stack.append(span.span_id)
        return span

    def end(self, span: Span, *, status: str = "ok", events: list[dict[str, str]] | None = None) -> None:
        if self is _NOOP:
            return
        self._seq += 1
        span.end_seq = self._seq
        span.status = status
        if events:
            span.events.extend(events)
        if self._stack and self._stack[-1] == span.span_id:
            self._stack.pop()

    def reset(self) -> None:
        self._spans.clear()
        self._stack.clear()
        self._seq = 0
        self._span_counter = 0
        self._trace = ""

    @property
    def spans(self) -> list[Span]:
        return list(self._spans)

    def export(self, *, collector: "Collector | None" = None) -> list[dict[str, Any]]:
        sink = collector or RedactingCollector()
        return sink.emit([s.to_dict() for s in self._spans])


class _NoopTracer(MemoryTracer):
    """Shared no-op instance: instrumentation on components is opt-in and a
    component without a tracer behaves exactly as it always has."""

    def begin(self, *, name: str, kind: str, attributes: dict[str, Any] | None = None) -> "Span":
        return Span(trace_id="", span_id="", name=name, kind=kind,
                    parent_id=None, start_seq=0)

    def end(self, span: Span, *, status: str = "ok",
            events: list[dict[str, str]] | None = None) -> None:
        return None

    def reset(self) -> None:
        return None

    def export(self, *, collector: "Collector | None" = None) -> list[dict[str, Any]]:
        return []


class Collector:
    """Export sink. Subclasses decide redaction/hashing policy."""

    def emit(self, payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return payloads


NoopTracer = _NoopTracer
_NOOP = NoopTracer()

__all__ = [
    "SPAN_KINDS", "Span", "MemoryTracer", "Collector", "RedactingCollector",
    "NoopTracer",
]


class RedactingCollector(Collector):
    """Deterministic scrubber: attributes with names listed in SENSITIVE_KEYS
    are replaced by sha256 hashes; event content is run through the admission
    PII scrub (the same rules the storage path uses) — a value is only kept
    verbatim if it clears it."""

    SENSITIVE_KEYS = frozenset({"query", "text", "content", "memory", "payload", "value"})

    def __init__(self, *, hash_keys: frozenset[str] = SENSITIVE_KEYS):
        self.hash_keys = hash_keys

    def emit(self, payloads: list[dict[str, Any]]) -> list[dict[str, str]]:
        out: list[dict[str, str]] = []
        for p in payloads:
            attrs = {}
            for k, v in p["attributes"].items():
                if k in self.hash_keys:
                    attrs[k] = _h(v) if isinstance(v, str) else v
                else:
                    attrs[k] = v
            merged = dict(p)
            merged["attributes"] = attrs
            merged["events"] = self._redact_events(p)
            out.append(merged)
        return out

    def _redact_events(self, p: dict[str, Any]) -> list[dict[str, str]]:
        redacted: list[dict[str, str]] = []
        for ev in p.get("events", []):
            scrubbed, hits = scrub_pii(ev.get("content", ""))
            e = dict(ev)
            e["content"] = scrubbed
            e["redacted"] = "true" if hits else "false"
            redacted.append(e)
        return redacted


def _h(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]