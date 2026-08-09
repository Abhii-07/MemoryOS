"""G-M3 Admission: deterministic turn classification and storage outcomes.

Write flow (system_design_part2 §8):
  turn -> Admission (classify + provenance + PII scrub) -> Storage

Every branch is a pure function of the turn + the tenant-scoped active rows
(no LLM, no network; ADR-008). Ops: ADD | UPDATE | DELETE | NOOP (api_contracts
POST /memory/turns). NOOP/DELETE return record_id=None — never an error.

Priority:
  1. PII pre-guardrail scrub (invariant #5) — raw secrets never stored.
  2. NOOP (EC-017: "hmm ok", greetings) / no memory-bearing vocabulary (EC-09).
  3. DELETE directive (EC-03 consent purge — physical, no soft flags).
  4. UPDATE: this tenant+user already has an ACTIVE row with the same slot_key
     (ADR-008; Week 1 supersession; ADR-002) -> supersede prior via valid_until,
     store the new turn (admission_op=UPDATE, confidence lowered).
  5. ADD otherwise.
"""

from __future__ import annotations

from dataclasses import dataclass

from memory_os.admission.patterns import (
    is_noop,
    parse_delete_target,
    scrub_pii,
    slot_key,
)
from memory_os.db.store import MemoryStore
from memory_os.embeddings import embed, is_available
from memory_os.retrieval.tokenizer import term_frequencies, tokenize

PII_VERSION = "memoryos-pii-2026-08-08"

PROVENANCE_BY_TURN_TYPE = {
    "user": "user_stated",
    "assistant": "assistant_generated",
}


@dataclass(frozen=True)
class AdmissionResult:
    admission_op: str                  # ADD | UPDATE | DELETE | NOOP
    record_id: str | None = None       # None for NOOP/DELETE
    provenance: str | None = None
    pii_scan_result: str = "pass"      # pass | redacted
    pii_rule_hits: tuple[str, ...] = ()
    superseded_id: str | None = None   # prior row closed via valid_until
    reason: str = ""


class Admitter:
    """Classifies one conversation turn and persists the storage outcome."""

    def __init__(self, store: MemoryStore, *, scan_limit: int = 200, tracer=None):
        self.store = store
        self.scan_limit = scan_limit
        self._tracer = tracer

    def _span_context(self, *, tenant_id: str, user_id: str):
        """Optional instrumentation (G-M5): a typed 'admission' span; memory
        content only ever lands in span events, which the collector redacts."""
        if self._tracer is None:
            return None
        return self._tracer.begin(name="admission", kind="admission",
                                  attributes={"tenant_id": tenant_id,
                                              "user_id": user_id})

    # ── helpers ──────────────────────────────────────────────────────────────
    def _embed(self, texts: list[str]) -> list[float] | None:
        if not is_available():
            return None
        vecs = embed(texts)
        return vecs[0] if vecs else None

    def _active_rows(self, *, tenant_id: str, user_id: str) -> list[dict]:
        return self.store.get_active(
            tenant_id=tenant_id, user_id=user_id, limit=self.scan_limit
        )

    def _supersede_slot(self, *, tenant_id: str, user_id: str, key: str) -> str | None:
        """Close the valid_until window of active rows sharing the slot key.
        Returns the last superseded id (or None). ADR-002/008."""
        superseded: str | None = None
        for row in self._active_rows(tenant_id=tenant_id, user_id=user_id):
            row_key = slot_key(row["text"])
            if row_key == key:
                if self.store.supersede(record_id=row["id"], tenant_id=tenant_id):
                    superseded = row["id"]
        return superseded

    def _match_delete(self, *, tenant_id: str, user_id: str, target: str) -> list[str]:
        """Active rows that share a lexeme with the delete target. Deterministic
        consent purge: intersection of token sets, never fuzzy similarity."""
        target_tokens = set(tokenize(target))
        if not target_tokens:
            return []
        ids: list[str] = []
        for row in self._active_rows(tenant_id=tenant_id, user_id=user_id):
            if set(tokenize(row["text"])) & target_tokens:
                ids.append(row["id"])
        return ids

    # ── main entry ──────────────────────────────────────────────────────────
    def admit(
        self,
        *,
        tenant_id: str,
        user_id: str,
        text: str,
        turn_type: str = "user",
    ) -> AdmissionResult:
        """Classify + persist one turn (api_contract POST /memory/turns)."""
        provenance = PROVENANCE_BY_TURN_TYPE.get(turn_type, "user_stated")
        span = self._span_context(tenant_id=tenant_id, user_id=user_id)
        try:
            return self._admit(tenant_id=tenant_id, user_id=user_id, text=text,
                               provenance=provenance)
        finally:
            if span is not None:
                self._tracer.end(span, events=[{"name": "turn_content",
                                                "content": text[:200]}])

    def _admit(self, *, tenant_id: str, user_id: str, text: str,
              provenance: str) -> AdmissionResult:
        """Classify + persist one turn (api_contract POST /memory/turns)."""
        # 1) PII pre-guardrail — redact secrets BEFORE persistence
        scrubbed, hits = scrub_pii(text)
        pii_result = "redacted" if hits else "pass"

        # 2) NOOP: neutral/generic utterances and punct-only turns; or turns
        #    whose vocabulary is empty (stopwords only, EC-09)
        no_evidence = not tokenize(scrubbed) or is_noop(scrubbed.lower())
        if no_evidence:
            return AdmissionResult(
                admission_op="NOOP",
                pii_scan_result=pii_result,
                pii_rule_hits=tuple(hits),
                reason="no memory-bearing content",
            )

        # 3) DELETE directive (consent purge — physical delete, no soft flags)
        target = parse_delete_target(scrubbed)
        if target is not None:
            ids = self._match_delete(
                tenant_id=tenant_id, user_id=user_id, target=target
            )
            for record_id in ids:
                self.store.delete(record_id=record_id, tenant_id=tenant_id)
            return AdmissionResult(
                admission_op="DELETE",
                pii_scan_result=pii_result,
                pii_rule_hits=tuple(hits),
                superseded_id=",".join(str(i) for i in ids) or None,
                reason="consent purge",
            )

        # 4) UPDATE if the same (tenant, user, slot) already has an active row
        key = slot_key(scrubbed)
        prior = None if key is None else self._supersede_slot(
            tenant_id=tenant_id, user_id=user_id, key=key
        )

        # 5) store the turn (ADD or UPDATE — with the low-confidence supersession
        #    fallback from Week 1: UPDATE rows carry confidence < 1.0)
        dense = self._embed([scrubbed])
        sparse_terms = term_frequencies(scrubbed)
        row = self.store.add(
            tenant_id=tenant_id,
            user_id=user_id,
            text=scrubbed,
            admission_op="UPDATE" if prior else "ADD",
            provenance=provenance,
            confidence=0.95 if prior else 1.0,
            pii_scan_result=pii_result,
            pii_detector_version=PII_VERSION if pii_result == "redacted" else None,
            dense_embedding=dense,
            sparse_terms=sparse_terms,
        )
        return AdmissionResult(
            admission_op="UPDATE" if prior else "ADD",
            record_id=row["id"],
            provenance=provenance,
            pii_scan_result=pii_result,
            pii_rule_hits=tuple(hits),
            superseded_id=prior,
            reason="correction of existing slot" if prior else None,
        )


__all__ = ["Admitter", "AdmissionResult", "PROVENANCE_BY_TURN_TYPE"]