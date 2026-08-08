# Week 3 — Component Scan

**Focus this week:** evaluation & observability. This is the component that determines whether
Deliverable 3's baseline is actually measuring anything real, so it's deliberately being scanned
before the baseline gets built rather than after.

---

## Evaluation

**Sources glimpsed:** Mem0's 2026 state-of-the-field report, a 2026 benchmark comparison covering
LoCoMo/LongMemEval/BEAM, "Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging
Frontiers" (2026 survey), MemoryAgentBench, MemBench, and the ZenBrain architecture paper's
benchmark section.

**The benchmark landscape has actually settled into a hierarchy, which is worth knowing before
picking metrics for Deliverable 3:**

- **LoCoMo** is the most widely reported number in the field — 1,540+ questions over long
  multi-session dialogues, testing single-hop, multi-hop, temporal, and open-domain recall. It's
  the closest thing to a standard benchmark right now. But it has two acknowledged weaknesses:
  the average conversation length is modest by current standards, and it doesn't explicitly score
  knowledge updates — which is exactly the contradiction-resolution problem Week 1 flagged as
  central to this project. A system can score well on LoCoMo and still be bad at exactly the thing
  Deliverable 1's Open Question 3 is about.
- **LongMemEval** picks up part of that slack — it explicitly includes knowledge-update questions
  alongside multi-session recall.
- **BEAM** pushes scale further (1M and 10M token evaluations) and reported scores drop
  meaningfully at the larger scale (roughly 64% at 1M tokens down to under 50% at 10M in cited
  results) — a useful reminder that recall quality isn't scale-invariant, it degrades as the
  memory store grows, which is directly relevant to this system's long-term storage-growth
  constraint from Deliverable 1.

**The finding I'd flag as the most important one this week, full stop:** a 2026 survey reports
that models scoring near-perfectly on LoCoMo drop to 40-60% on MemoryArena — a benchmark that
embeds memory evaluation inside actual multi-step agentic tasks rather than testing recall in
isolation. That gap is the evaluation equivalent of a car passing every safety test on a
dealership lot and then failing on the first real road. It means recall accuracy in isolation is
close to a vanity metric — the real question is whether a correctly retrieved memory actually gets
*used* correctly in a downstream decision, and that's a materially harder thing to test than
"did the right fact come back."

**The metric set that's converged across sources, worth adopting directly:** memory recall
(fraction of ground-truth facts retrievable), memory precision (fraction of retrieved-top-k that's
actually relevant), latency (p50/p95), and token efficiency (tokens injected per query) as the
baseline four. One 2026 survey extends this into an explicit four-layer stack: task effectiveness
(success rate, factual correctness) sitting on top of memory quality (precision/recall,
contradiction rate, staleness distribution) — which is a cleaner way to organize evaluation than
treating it as one flat metric list, and maps directly onto this project's own two-level concern
(is the memory system working vs. is the assistant actually better because of it).

**Where I'd be skeptical:** several papers still lean on LLM-as-judge scoring for semantic
correctness, and that's a reasonable secondary signal, but Week 1 already surfaced strong evidence
that LLMs are bad at exactly the kind of temporal/freshness judgment this system depends on most.
An LLM judge grading "is this answer correct" is a different, more tractable task than an LLM
judging "is this memory still current" — worth not conflating the two when this system's own eval
suite gets built in Deliverable 6.

**Relevance to this system:** Deliverable 3's baseline needs metrics before it needs code. The
adopted set here — recall, precision, latency, token efficiency, plus a contradiction/staleness
rate specific to this project's ranking work — gives a concrete, reproducible measurement plan
instead of "record some qualitative observations," which the handbook explicitly warns is
insufficient.

---

## Observability

**Sources glimpsed:** 2026 production write-ups from Braintrust, MLflow, OpenObserve, and Uptrace
on OpenTelemetry for LLM/agent systems, plus a 2026 survey on evidence tracing and execution
provenance in LLM agents.

**The infrastructure question here is more settled than I expected going in.** OpenTelemetry's
GenAI semantic conventions have become the de facto standard for tracing LLM and agent
systems — vendor-neutral, and every observability backend I looked at (Braintrust, MLflow,
OpenObserve) treats OTEL spans as the common substrate rather than inventing a proprietary format.
Concretely: tool calls, reasoning steps, state transitions, and — specifically relevant here —
memory operations each get typed as their own nested span under the parent agent run. The OTel
GenAI working group is actively extending the spec to cover memory and multi-agent conventions
directly, which means this isn't a component this project needs to invent tooling for — it needs
to instrument against an existing standard.

**Two operational details worth building in from day one rather than retrofitting:**
- **Content goes in span events, not span attributes.** Attributes are always indexed and
  exported; events can be filtered or dropped at the collector level. Since memory content is
  exactly the kind of thing Deliverable 1's privacy constraint cares about, this is a concrete,
  cheap mechanism for keeping sensitive content out of the observability backend by default rather
  than needing to scrub it after the fact.
  - Redaction/hashing at the collector level (delete or hash prompt/completion content in the
    pipeline) means privacy-safe tracing doesn't require touching application code every time the
    redaction policy changes.
  - Sampling matters at any real volume — tail-based sampling (keep all errors, sample a fraction
    of everything else) is the standard pattern, since LLM calls are slow and spans are large
    enough that capturing 100% of traffic isn't free.

**Relevance to this system:** Deliverable 1 required "expose decisions through logs, traces, and
evaluation outputs" without specifying a mechanism, and Deliverable 4's design needs one. Treating
every memory operation (admission, ranking decision, supersession, decay, deletion) as its own
typed OTEL span, with content in events rather than attributes, gives both the debugging surface
the handbook wants and a built-in privacy boundary — for close to zero novel engineering, since the
tooling already exists.
