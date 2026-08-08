# Design Backlog

Running list of every idea surfaced across weekly scans, and its current status. Updated each
week — never rewritten from scratch.

## Adopted (folded into the design as of Deliverable 4, or queued to be)

| Idea | Component | Source week | Notes |
|---|---|---|---|
| ADD / UPDATE / DELETE / NOOP admission actions | Memory admission | Week 1 | Replaces single store/discard threshold |
| Admit agent-generated commitments alongside user facts | Memory admission | Week 1 | Extraction must run over assistant turns too |
| Deterministic `valid_until` supersession | Ranking & conflict resolution | Week 1 | Core fix for Deliverable 1, Open Question 3 |
| Four-lever consolidation (importance / merge / decay / eviction) | Reflection & lifecycle | Week 1 | Organizing structure, not a specific policy yet |
| Decay (soft, rank-affecting) separate from deletion (hard, triggered) | Reflection & lifecycle | Week 1 | Keeps the privacy deletion guarantee clean |
| Hybrid retrieval: BM25 + dense + RRF fusion | Retrieval augmentation | Week 2 | Converged production pattern, not contested |
| No LLM call at retrieval time (structural ranking via fusion + graph traversal) | Retrieval augmentation | Week 2 | Zep/Graphiti's production pattern; keeps cost bounded per turn |
| Explicit per-zone token budgets, monitored | Context construction | Week 2 | System prompt / memory / history / input / output, each with a ceiling |
| Tool-output accumulation as its own budgeted zone | Context construction | Week 2 | Easy to miss until it's a production incident; building it in from day one |
| Context rot as a design constraint | Context construction | Week 2 | Bigger context windows don't remove the need for selective retrieval; to be validated empirically in Deliverable 3 |
| pgvector for MVP scale, dedicated vector DB only past tens of millions of vectors | Index & storage layer | Week 2 | Near-unanimous recommendation at this system's expected scale |
| Namespace isolation now, physical isolation as a documented upgrade trigger | Index & storage layer | Week 2 | Directly serves Deliverable 1's tenant isolation constraint |
| Recall / precision / latency (p50, p95) / token-efficiency as core metrics | Evaluation | Week 3 | Standard four-metric set, converged across every benchmark scanned |
| Contradiction/staleness rate as a 5th, project-specific metric | Evaluation | Week 3 | Fills the gap LoCoMo explicitly doesn't cover |
| No LLM-as-judge for freshness, only for semantic correctness | Evaluation | Week 3 | Follows directly from Week 1's freshness-tracking finding |
| OpenTelemetry GenAI spans as tracing substrate, memory ops as typed spans | Observability | Week 3 | De facto standard; no need to invent tooling |
| Memory content in span events (not attributes), collector-level redaction | Observability | Week 3 | Concrete mechanism for Deliverable 1's privacy constraint |
| Tail-based sampling (all errors, fraction of routine traffic) | Observability | Week 3 | Standard production pattern; not urgent at MVP scale |

## Prototyping (needs a bounded experiment before adoption)

| Idea | Component | Source week | What the prototype needs to show |
|---|---|---|---|
| Utility / confidence / novelty as separate admission scores | Memory admission | Week 1 | Whether three-factor scoring beats one blended score on the same conversation set |
| Separate episodic vs. semantic indexes | Ranking & conflict resolution | Week 1 | Whether splitting the index actually improves retrieval over a single shared index with metadata tagging |

## Deferred

| Idea | Component | Source week | Trigger to revisit |
|---|---|---|---|
| Cross-encoder / ColBERT reranking | Retrieval augmentation | Week 2 | Revisit once Deliverable 6 benchmarks show fusion alone isn't hitting recall targets |
| Task-level (memory *use*) evaluation, full implementation | Evaluation | Week 3 | Build once Deliverable 4's system exists to test against; Deliverable 3 measures recall/precision only |

## Rejected

*(none yet)*

## Adopted from Week 4 (privacy, safety, isolation)

| Idea | Component | Source week | Notes |
|---|---|---|---|
| Regex + NER PII detection at admission and retrieval (pre/post guardrail) | Privacy | Week 4 | Requires explicit minimum precision/recall bar on this project's own data before shipping |
| Provenance tag on every memory record | Privacy & safety | Week 4 | Must change at least one real downstream behavior (e.g. expiry), not just exist in the schema |
| Deterministic tenant filtering at query time (amends Week 2 namespace isolation) | Privacy | Week 4 | Correctness over latency; needs an efficient pre-filtered-search check against whatever index D4 picks |
| Expire unverified/low-provenance memory by default | Privacy & safety | Week 4 | Folds into Week 1's four-lever consolidation as an added decay trigger |

## Adopted-as-requirement, prototype needed

| Idea | Component | Source week | What the prototype needs to show |
|---|---|---|---|
| Deletion propagation to derived/consolidated artifacts (backflow prevention) | Privacy — deletion guarantees | Week 4 | Whether lineage tracking through Week 1's consolidation pipeline can reliably cascade deletion; hardest open problem across all four weeks |

## Not yet scanned (descoped, folded into Deliverable 4 directly)

Memory model & representation — weekly research scanning stops at week 4. This component's ground
is already substantially covered by Week 1 (typed admission records) and Week 2 (episodic/semantic
index split), so it gets folded directly into Deliverable 4's design rather than a fifth research
week.
