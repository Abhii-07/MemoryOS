# Week 4 — Component Scan

**Focus this week:** privacy, safety, and isolation. This week was added deliberately outside the
original three-week plan, specifically because Deliverable 4 requires a `threat_model.md` as a
required artifact, and everything on privacy so far has come in as a side effect of scanning other
components rather than from actually researching the attack surface directly. That gap gets closed
this week.

---

## PII detection and redaction

**Sources glimpsed:** 2026 production guides on PII redaction for LLM pipelines (FutureAGI,
Gravitee, PCTechMag), the OpenAI Privacy Filter release notes, a PIIBench evaluation write-up, and
SurrogateShield (2026) on redaction alternatives.

**The standard pattern is genuinely settled:** detect PII with a combination of regex (fast, exact,
good for structured data — card numbers, SSNs, emails) and NER models (better for unstructured
mentions — names, locations, informal context), then either mask it (irreversible, out of scope
for most privacy regs once masked) or tokenize it (reversible, but still counts as regulated data
since the mapping exists somewhere). This two-detector-type combination, not either alone, is the
converged recommendation across every source scanned.

**The finding that should make anyone cautious about trusting a single accuracy number:** PIIBench
tested eight PII detection systems across ten datasets and forty-eight entity types, and found
detector performance is wildly unstable out-of-distribution — one system's F1 fell from 0.96 to as
low as 0.18 depending on the dataset. A detector that looks production-ready on its own benchmark
can fail badly the moment it sees a different distribution of text than it was tuned on. This
matters directly for this project: conversational memory text (informal, personal, project-
specific) is exactly the kind of "different distribution" that a detector benchmarked on formal
documents might not generalize to. Any PII detector chosen for this system needs to be validated on
this project's actual conversational data, not trusted on the strength of a published benchmark
number.

**A distinction worth keeping precise:** pre-guardrails (catch PII before it's even written to
memory) and post-guardrails (catch PII that's about to be surfaced in a generated response) are
different controls with different failure modes, and several sources frame privacy leakage as "a
workflow regression, not a one-time text filter" — meaning both checks are needed, at different
points in the pipeline, not one filter applied once.

**Relevance to this system:** this gives Deliverable 1's privacy constraint an actual mechanism —
regex + NER at admission time (pre-guardrail) and at retrieval/injection time (post-guardrail) —
and a concrete caution: whatever detector gets chosen needs its own validation pass on this
project's conversational data before being trusted.

---

## Cross-tenant isolation and adversarial memory (memory poisoning)

**Sources glimpsed:** OWASP's 2026 Top 10 for Agentic Applications (specifically ASI06: Memory &
Context Poisoning), a 2026 write-up on the MemoryGraft and MINJA attacks, a Medium/production
write-up on multi-tenant shared-memory risk, and a May 2026 disclosure of "MemoryTrap" — a Cisco
finding against Claude Code specifically, patched by Anthropic in v2.1.50.

**This is the most important finding of the whole week, and arguably of the whole research phase
so far:** persistent memory turns prompt injection from a single-session nuisance into something
categorically worse. A standard prompt injection dies when the session ends. A memory injection
persists, can activate weeks later, and is described across multiple sources as "nearly invisible
to detect" because the runtime has no reliable way to distinguish attacker-written memory from
legitimate user-written memory — both arrive through the same write path, and both look identical
once they're sitting in storage. One source calls this "trust laundering": a malicious instruction
that entered through a benign-looking channel (an email, a shared document, a code comment) reads
as trusted context once it's in memory, specifically because it's in memory rather than in the
current prompt.

**Concretely, in a multi-tenant setting:** if multiple tenants' memories share a vector index
without strict filtering, similarity search can produce cross-tenant collisions ("close enough"
matches), hybrid search can blend global and tenant-scoped results, and a reranker can pull a
"high confidence" item that shouldn't be visible to that tenant at all. One source puts this
sharply: vector search is inherently probabilistic, and multi-tenancy requires determinism at the
boundary — those two properties don't mix safely by default, which is exactly why Week 2's
adopted namespace-isolation decision needs to be paired with something stronger at write time, not
just at query time.

**The converged mitigation pattern (OWASP ASI06):** segment memory per tenant, expire unverified
data rather than trusting it indefinitely, and track provenance on every memory record — where it
came from, and whether it's been verified. Provenance tracking in particular is something this
project hasn't explicitly adopted yet, despite Week 1's admission work already producing a natural
place to attach it (every ADD/UPDATE/DELETE operation could carry a provenance tag from day one at
near-zero extra cost).

**Relevance to this system:** this directly threatens two things this system already committed to.
First, Week 1's decision to admit agent-generated commitments as memory (not just user-stated
facts) needs a provenance distinction — an assistant's own conclusion and content lifted from a
tool result or a retrieved document are not equally trustworthy, and treating them the same is
exactly the "trust laundering" failure mode described above. Second, namespace-based tenant
isolation (adopted in Week 2) is a necessary but not sufficient control — it needs to be paired
with deterministic query-time filtering that doesn't rely on similarity thresholds alone to keep
tenants apart.

---

## Deletion guarantees and the right to be forgotten

**Sources glimpsed:** "Agentic Unlearning: When LLM Agent Meets Machine Unlearning" (2026), the
"Always-On Agents" survey's section on deletion propagation, and several 2026 practitioner guides
on right-to-be-forgotten compliance for AI systems.

**The finding that most directly complicates this project's existing deletion requirement:**
researchers use the term "backflow" for a specific failure mode — a deletion request removes a
memory record, but summaries, consolidated notes, or derived artifacts built from that record
before deletion can still cause the model to effectively re-learn the deleted information at
retrieval time. Deleting the source record is necessary but not sufficient; every derived artifact
built from it needs to be tracked and deleted too, or deletion is, in one survey's words, "only a
retrieval edit" rather than a real deletion.

**Why this specifically matters for a system with consolidation already in its design:** Week 1
adopted a four-lever consolidation framework (importance/merge/decay/eviction) that explicitly
produces merged and summarized records from raw memories. That's exactly the mechanism that
creates backflow risk — a summary built from five raw memories, one of which gets a deletion
request, doesn't automatically un-summarize itself. This wasn't visible as a risk until this
week's research connected consolidation (Week 1) to deletion propagation (Week 4).

**Relevance to this system:** Deliverable 6's acceptance check already requires deletion to remove
a memory "from both source storage and retrieval paths within the documented consistency window" —
this week's research shows that requirement needs to explicitly extend to derived/consolidated
artifacts, not just the original record, or it will pass a naive test while failing a real one.

---

## Summary across the three sub-areas

Unlike weeks 2 and 3, this component doesn't split cleanly into "mostly settled." The *mitigation
frameworks* are settled (OWASP ASI06's taxonomy, the regex+NER detection pattern, the
segment/expire/track-provenance triad) — but the *threats themselves* are extremely current, with
named attacks (MemoryGraft, MINJA) and a real disclosed vulnerability against a shipping product
(Cisco's MemoryTrap finding against Claude Code, April-May 2026) all landing within the last few
months. This is a component where the framework for thinking about the problem is mature, but the
specific threat landscape is still actively being discovered — worth treating this week's findings
as a floor, not a ceiling, for what Deliverable 4's threat model needs to cover.
