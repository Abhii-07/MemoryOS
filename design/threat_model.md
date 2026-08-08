# Threat Model

**Conversational Memory Intelligence System — Deliverable 4**
Abhijeet Hiwale · August 2026

Expands system_design.pdf, Section 11. Grounded in Week 4's research (OWASP LLM AI Security Top 10,
2025 edition: LLM-04 Data & Model Poisoning and LLM-08 Vector & Embedding Weakness — see the
correction note below; the MemoryGraft/MINJA attacks, the Cisco MemoryTrap disclosure against Claude
Code, PIIBench) and
this design's own architectural priorities (privacy & tenant isolation ranked highest, Part 1
Section 3). Every threat below maps to a specific mitigation already committed to in
system_design.pdf — this document does not introduce new mechanisms, it organizes and stress-tests
the ones already adopted.

---

## Methodology

Threats are catalogued by asset (what could be compromised) rather than by attack technique, since
the research surfaced categories of harm — leakage, poisoning, loss of deletion guarantee — that
each have multiple possible attack paths. Each threat is scored on the recoverable/non-recoverable
split from system_design.pdf Section 4: non-recoverable threats get structural prevention (the
architecture makes the bad outcome impossible or near-impossible), recoverable threats get
detection and graceful degradation.

**In scope:** everything inside the system boundary (architecture.pdf, diagram 1) — Admission,
Storage, Retrieval, Ranking, Context Builder, Lifecycle Worker.
**Out of scope, with reasons already stated in system_design.pdf:** upstream authentication
(Part 1, Section 4's assumption — this design enforces isolation given a trusted tenant ID, it
does not authenticate that ID), multi-agent shared memory and cross-modal memory (Section 2's
explicit non-goals), network-layer security (TLS, DDoS) — standard infrastructure concerns not
specific to a memory system.

---

## Threat 1: Cross-Tenant Memory Leakage

**Asset at risk:** tenant isolation — the single highest architectural priority (Part 1, Section 3).

**Attack path:** vector similarity search is probabilistic. In a shared or namespace-partitioned
index, hybrid search and reranking can surface a "close enough" match from a different tenant if
tenant filtering is folded into similarity scoring rather than applied as a hard boundary — this
is documented behavior in production multi-tenant vector systems, not a hypothetical (Week 4
research).

**Classification:** non-recoverable (system_design.pdf, Section 4). Must be structurally prevented,
not detected-and-handled.

**Mitigation already committed:** Section 9's retrieval policy applies the tenant filter
deterministically, *before* similarity scoring runs — a cross-tenant candidate is never scored at
all, let alone ranked. This is stronger than namespace isolation alone (Week 2's original decision),
which Week 4 flagged as necessary but not sufficient. `data_model.md`'s composite index
(`tenant_id, status`) makes the pre-filter cheap rather than a performance tax that creates pressure
to weaken it later.

**Residual risk:** the pre-filter is only as strong as the query construction that applies it. A
bug in the Retrieval component that omits the filter on some code path would silently reopen this
threat. **Verification:** Deliverable 6's acceptance check explicitly requires "no cross-tenant
memory returned under adversarial queries" — this needs to include queries deliberately crafted to
be semantically close to another tenant's content, not just random cross-tenant queries.

---

## Threat 2: Memory Poisoning / Trust Laundering

**Asset at risk:** the integrity of what the system treats as trustworthy memory.

**Attack path:** this is the most consequential finding from Week 4's research, worth restating
precisely: a standard prompt injection dies with the session. A memory injection persists, can
activate arbitrarily far in the future, and — per multiple 2026 sources — is difficult to detect
because the write path doesn't distinguish attacker-supplied content from legitimate content. A
malicious instruction arriving through a tool result, a retrieved document, or even an assistant's
own reasoning over compromised input can be admitted as memory and later "read as trusted context ...
purely because of where it's stored" (Week 4's "trust laundering" framing). This is not
theoretical: OWASP's 2025 LLM Top 10 covers this class across LLM-04 (Data & Model Poisoning) and
LLM-08 (Vector & Embedding Weakness), named attacks exist (MemoryGraft, MINJA), and
Cisco disclosed a real instance — MemoryTrap — against Claude Code specifically, patched by
Anthropic in April–May 2026.

> **Correction note (2026-08-08, verification pass R3):** the original draft cited "OWASP 2026
> ASI06" as a formal taxonomy entry. Research pass R3 (`research/passes/2026-08-08-R3`) verified
> that no ASI06 slot exists in the OWASP LLM Top 10 (2025 edition, LLM01–LLM10); memory-related
> risks are formally covered by LLM-04 and LLM-08. This copy corrects both citations; the design's
> mitigations are unchanged.

**Classification:** non-recoverable in effect (a poisoned memory that goes undetected can
influence behavior indefinitely), though the individual admission event is, in principle,
recoverable if caught early — this is why provenance and expiry matter so much here.

**Mitigation already committed:**
- Every memory carries a `provenance` field (`data_model.md`) set at write time — the schema
  distinguishes `user_stated`, `assistant_generated`, `tool_derived`, and `retrieved_document`.
  This doesn't prevent poisoning by itself; it makes poisoning *attributable* and enables the next
  two mitigations.
- Ranking's `provenance_trust` term (system_design.pdf, Section 9's formula) weights
  `tool_derived` and `retrieved_document` content lower than `user_stated` content, all else equal
  — a poisoned memory arriving via a tool result or document starts at a structural disadvantage
  in ranking, not equal footing with something the user said directly.
- Unverified/low-provenance memory expires by default (Week 4, folded into the four-lever
  lifecycle's decay trigger) — a poisoned memory that's never corroborated loses influence over
  time rather than persisting indefinitely, which is the core of what made the attack category
  dangerous in the first place.

**Residual risk, stated honestly:** this system has no detection mechanism that identifies a
poisoning attempt *at admission time* — the mitigations above reduce the blast radius and duration,
they don't prevent admission of a well-crafted malicious memory that mimics legitimate content
patterns. This is a real gap, not fully closed by this design. **Verification:** Deliverable 6
should include adversarial test cases modeled on the MemoryGraft/MINJA attack patterns, checking
whether provenance-weighted ranking and default expiry measurably reduce a poisoned memory's
influence over a multi-turn interaction, even though full prevention isn't claimed.

---

## Threat 3: Sensitive Content (PII) Retained and Resurfaced

**Asset at risk:** user privacy, directly demonstrated as a live failure in Deliverable 3 (100%
leak rate on the naive baseline's sensitive-info case).

**Attack path:** no attacker required — this is a failure mode that occurs under entirely benign
use, whenever a user mentions something sensitive in passing (Deliverable 3's example: a home
address volunteered while describing a shipping test case).

**Classification:** non-recoverable once leaked to an unintended context, though preventable at
multiple pipeline stages.

**Mitigation already committed:** regex + NER PII detection applied twice — at Admission
(pre-guardrail, before storage) and at Retrieval/Context Builder (post-guardrail, before
injection) — per Week 4's two-detector-type pattern. `data_model.md`'s `pii_scan_result` field
(`pass | flag | redacted`) makes the detection outcome auditable per record, and
`pii_detector_version` makes results reproducible as detectors get updated.

**Residual risk — the one this design refuses to paper over:** Week 4's research found PII
detector accuracy is unstable out-of-distribution, with one benchmarked system's F1 score ranging
from 0.96 down to 0.18 depending on the dataset. This design does not claim a specific detection
accuracy number, because doing so without validating against this project's own conversational
data would be exactly the kind of unearned precision this project has avoided elsewhere
(system_design.pdf, Section 13's treatment of capacity numbers). **Verification:** Deliverable 6's
acceptance check ("sensitive-data policy is tested with positive and negative cases") must
specifically include informal, conversational-style sensitive content — not just clearly
structured PII like a formatted SSN — since that's precisely the distribution shift Week 4's
research flagged as the failure case.

---

## Threat 4: Deletion Failure / Backflow

**Asset at risk:** the deletion guarantee itself — a user's right to actually have something
forgotten.

**Attack path:** not an adversarial attack, but a structural risk — the four-lever lifecycle's
Merge operation creates consolidated records referencing multiple source memories
(`consolidation_lineage`, `data_model.md`). Deleting a source record without propagating that
deletion through every derived artifact means the deleted content's influence survives inside a
summary that was never touched — Week 4's research calls this "backflow," and notes that without
propagation, deletion is "only a retrieval edit," not a real deletion.

**Classification:** non-recoverable (system_design.pdf, Section 4) — explicitly named there as
this design's single biggest risk, and repeated here rather than softened.

**Mitigation already committed:** `consolidation_lineage` (a GIN-indexed UUID array,
`data_model.md`) makes the lineage graph queryable. The `DELETE /memory/{id}` endpoint
(`api_contracts.md`) walks this graph and re-consolidates or evicts every derived record, returning
`202 Accepted` with an explicit in-progress status for large chains rather than a false-positive
immediate success.

**Residual risk — stated as plainly as anywhere in this project:** this is adopted as a hard
requirement with the mechanism only prototyped, not proven. Nothing in this document or the
schema makes lineage-walk correctness guaranteed; it makes it checkable. **Verification:**
Deliverable 6's acceptance check ("deletion removes a memory from both source storage and
retrieval paths within the documented consistency window") must specifically include a
merge-then-delete test case — create a consolidated record from multiple sources, delete one
source, and verify the consolidated record's content no longer reflects the deleted source. A
naive test that only deletes never-consolidated records would pass without exercising this threat
at all.

---

## Threat 5: Collector Misconfiguration Leaking Memory Content via Traces

**Asset at risk:** privacy, via the observability pipeline rather than the memory pipeline itself.

**Attack path:** Week 3 adopted OpenTelemetry spans with memory content in span *events* rather
than span *attributes*, specifically because events can be filtered or dropped at the collector
level. Week 4's self-review of that decision flagged the gap directly: "events can be
filtered/dropped" is a capability, not a guarantee — a misconfigured collector still exports
everything.

**Classification:** recoverable in principle (a misconfiguration can be fixed), but the exposure
window before detection could be significant, so it's treated with non-recoverable-level caution
in this document even though system_design.pdf's Section 4 table doesn't list it explicitly —
worth flagging as a gap in that table's completeness, not a contradiction.

**Mitigation already committed:** redaction/hashing applied at the collector level (Week 3/4).

**Residual risk:** this mitigation depends entirely on collector configuration discipline, which
this design cannot enforce structurally the way the tenant pre-filter (Threat 1) can. **Verification:**
this needs an explicit configuration-as-code check in Deliverable 5/6 (verify the collector's
redaction rules are active as part of deployment, not a manual setup step someone can skip) —
currently unaddressed in this design and worth carrying forward as an open item rather than
assumed solved.

---

## Summary Table

| # | Threat | Class | Primary mitigation | Residual risk honestly stated |
|---|---|---|---|---|
| 1 | Cross-tenant leakage | Non-recoverable | Deterministic pre-filter before scoring | Depends on correct query construction everywhere |
| 2 | Memory poisoning / trust laundering | Non-recoverable (in effect) | Provenance tagging + trust-weighted ranking + default expiry | No admission-time detection; blast radius reduced, not eliminated |
| 3 | PII retained/resurfaced | Non-recoverable (once leaked) | Regex+NER at admission and retrieval | Detector accuracy unvalidated against real conversational data |
| 4 | Deletion failure (backflow) | Non-recoverable | Lineage tracking + cascading deletion | Mechanism prototyped, not proven — biggest open risk in the whole project |
| 5 | Collector misconfiguration | Recoverable, treated cautiously | Redaction at collector level | No structural enforcement; a config-as-code check is still an open item |

This table intentionally has no row where "residual risk: none" — a threat model that claims full
mitigation everywhere would be less credible than one that names what's actually still open,
consistent with this entire project's approach since Deliverable 1.
