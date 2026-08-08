# System Design — Conversational Memory Intelligence System

**Deliverable 4 · Draft, Part 3 of 3 (Sections 12–16)**
Abhijeet Hiwale · August 2026

---

## 12. Observability and Offline Evaluation

**Tracing** (Week 3's adopted mechanism): every memory operation — admission, ranking decision,
supersession, decay, deletion — is a typed OpenTelemetry span nested under the parent request.
Memory content lives in span *events*, not span *attributes*, with redaction/hashing applied at the
collector level. This is more than a logging choice: Section 11's threat model treats collector
misconfiguration as a real risk, not a footnote, per Week 4's self-review of Week 3's own decision.
Tail-based sampling (capture all errors, sample routine traffic) applies once real traffic volume
exists; not a concern at MVP scale.

**Open item carried forward honestly:** Week 3's self-review flagged that OTEL's "low cost" claim
assumed a framework choice this design still hasn't made. That's still true here — auto-
instrumentation cost is unknown until an implementation framework is picked in Deliverable 5/6.
This section commits to OTEL as the standard; it does not yet commit to an instrumentation cost
estimate, because that would be a number invented without a basis.

**Offline evaluation** uses the metric set established across Week 3 and Deliverable 3: recall@5,
precision@1, the contradiction/staleness rate, latency p50/p95, token efficiency, and the minimal
task-level check (does the system act on the current fact, not a stale one). Per Week 3's revised
decision, full task-level evaluation — memory *use*, not just recall, tested against genuine
multi-step scenarios — is deliberately deferred to Deliverable 6, where a real implementation
exists to test against.

## 13. Capacity, Latency, Cost, and Operational Recovery

**Storage capacity:** pgvector at MVP scale (Week 2), with an explicit re-validation trigger — Week
2's self-review flagged that the cited recommendations assumed generic RAG workloads, not this
system's comparatively write/update/delete-heavy access pattern (driven by supersession and
lifecycle operations). This design does not treat "pgvector is fine" as settled; it's the correct
starting point, re-checked once Deliverable 6 produces real update/delete volume.

**Latency budget:** matches Part 1's targets (retrieval p95 < 100ms, context construction < 20ms).
The write flow (admission) has no equivalently strict budget, since it's decoupled from the read
flow's request/response cycle (Section 8) — a slow admission delays when a memory becomes
retrievable, not the latency of an unrelated concurrent query.

**Cost:** bounded primarily through the four-lever lifecycle (decay and eviction prevent unbounded
storage growth) rather than through aggressive upfront filtering — this follows directly from Part
1's priority table, which ranks storage efficiency lowest. Namespace-based tenant isolation stays
cheap at moderate scale; the documented trigger for upgrading to physical isolation (Week 4) is
tenant count or compliance requirements crossing a threshold to be set once real usage data exists.

**Operational recovery — a distinction this design has to get right, not just describe:** a
retrieval-path *error* (storage unreachable, index corrupted) and a *valid* "no relevant memory
found" result must never be indistinguishable to the caller. Section 10 already draws this line in
the API contract; it matters again here because a naive failure-recovery strategy (silently return
empty results on any retrieval error) would quietly reintroduce Deliverable 3's Failure 3 through
the back door — a caller couldn't tell "genuinely nothing relevant" from "the system is broken and
failing closed." Errors must surface as errors.

**Deletion consistency window:** Deliverable 6's acceptance check requires deletion to remove a
memory "within the documented consistency window." This design commits to stating that window
explicitly once Deliverable 6 measures real lineage-propagation time — it is not fixed here, since
inventing a number without Deliverable 6's data would be exactly the kind of unearned precision
this project has avoided elsewhere (see Deliverable 1's treatment of context-budget zone sizes).

## 14. Alternatives Considered

Full decision records are in `design/decision_records/` (ADR-per-decision). Summary of the major
alternatives this design rejected, and why — each traceable to a specific week's research rather
than asserted:

| Alternative | Rejected in favor of | Why |
|---|---|---|
| LLM-judged freshness/recency at retrieval time | Deterministic `valid_until` supersession | Week 3's benchmark finding: LLM freshness judgment fails even with explicit instructions |
| Full conversation history replay | Selective retrieval with budgeting | Deliverable 1's historical chain — replay breaks the token budget as conversations grow |
| Keyword-only (lexical) search | Hybrid BM25 + dense + RRF | Deliverable 1 required semantic matching; pure keyword search misses paraphrased queries |
| Dedicated vector database at MVP launch | pgvector on existing Postgres | Week 2 — near-unanimous recommendation at this system's expected scale; avoids premature infrastructure |
| Cross-encoder/ColBERT reranking at launch | Deferred, revisit if Deliverable 6 shows a measured gap | Week 2 — real technique, but "add a reranker" was flagged as a reflexive answer, not a measured need |
| Similarity-only tenant isolation | Deterministic pre-filter, applied before ranking | Week 4 — similarity search is probabilistic; multi-tenancy needs a hard boundary |
| Trusting a single PII benchmark number | Mandatory validation on this project's own conversational data | Week 4's PIIBench finding — detector accuracy is unstable out-of-distribution |

## 15. Milestones, Gates, and Acceptance Tests

Proposed build sequence (to be structured into Genesis loops in Deliverable 5, not committed to a
calendar here):

1. **M1 — Storage + Admission.** Typed records, provenance tagging, PII pre-guardrail, tenant
   partitioning. Gate: a stored record round-trips with all required fields intact.
2. **M2 — Retrieval + Ranking (core memory loop).** Hybrid search, relevance floor, supersession
   logic. Gate: Deliverable 3's exact failing cases (stale-outranks-current, false-positive
   relevance) now pass against this implementation.
3. **M3 — Context construction.** Per-zone budgeting, tool-output zone. Gate: budget ceilings are
   never exceeded under the long-conversation stress case from Deliverable 3.
4. **M4 — Lifecycle + deletion propagation.** Four-lever consolidation, lineage tracking. Gate:
   a deletion request against a source record removably affects every derived artifact — this is
   the milestone most likely to slip, given Week 4's honest assessment of its difficulty.
5. **M5 — Privacy hardening.** PII detector validated against real conversational data, threat
   model's non-recoverable failure modes specifically tested.
6. **M6 — Observability.** OTEL instrumentation, redaction at the collector.
7. **M7 — Full verification.** Deliverable 6's acceptance checks run in full, benchmarked directly
   against Deliverable 3's naive baseline numbers.

**Acceptance tests** are Deliverable 6's own required checks, restated here as the target this
design is built to satisfy: relevant memories outrank distractors; stale preferences never override
current ones; no cross-tenant memory returned under adversarial queries; deletion removes a memory
from both source and retrieval paths within the (to-be-measured) consistency window; context
selection respects the token budget; sensitive-data policy is tested with positive and negative
cases; results are compared against Deliverable 3's baseline, not evaluated in isolation.

## 16. Risks and Unresolved Questions

Named honestly rather than smoothed over:

- **Deletion propagation correctness** (Week 4's hardest problem) is this design's single biggest
  risk. `consolidation_lineage` (Section 7) makes it implementable; nothing in this document makes
  it proven. M4 is where this either holds up or doesn't.
- **Entity/slot-linking for admission** — Week 1's self-review flagged this as a load-bearing
  prerequisite for both the ADD/UPDATE/DELETE/NOOP classification and supersession detection, and
  it still has no detailed design of its own. This needs its own decision record before M1/M2
  implementation starts in earnest.
- **Dense embedding availability** — Part 1's first assumption. Deliverable 3's baseline used
  TF-IDF only because this sandbox had no network path to an embedding service; the production
  design assumes one exists. If that assumption doesn't hold in the actual deployment environment,
  Section 9's hybrid retrieval degrades to lexical-only, which reopens Deliverable 1's original
  "keyword search misses paraphrases" failure mode.
- **PII detector validation** is specified as a requirement (Section 11) but has no validated
  detector yet — this can't be resolved on paper, only once Deliverable 6 has real conversational
  data to test against.
- **Pre-filtered search efficiency** — Week 4's self-review flagged that deterministic tenant
  filtering needs checking against whatever index implementation gets chosen; pgvector's specific
  behavior under tenant pre-filtering hasn't been verified, only assumed reasonable.
- **Target metric values** (Part 1, Section 3) are engineering objectives, not derived from a
  benchmark — they may need revision once Deliverable 6 produces the first real measurements
  against a realistic-scale workload rather than Deliverable 3's ten hand-built cases.

---

*This completes the three-part system_design draft (Sections 1–16). Remaining Deliverable 4
artifacts — `architecture.pdf`, `data_flow.pdf` (diagram renders), `data_model.md`,
`api_contracts.md`, `threat_model.md`, `decision_records/`, and `sprint_plan.md` — expand specific
sections above into their own standalone documents, per the handbook's required artifact list.*
