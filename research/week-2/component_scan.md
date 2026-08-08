# Week 2 — Component Scan

**Focus this week:** retrieval augmentation, attention & context construction, index & storage
layer. These three are the "plumbing" components — less glamorous than admission or ranking, but
this is where a design either holds up under real traffic or falls over. Getting these wrong
doesn't show up in a demo. It shows up three weeks into production as a latency graph that only
goes up and to the right.

---

## 1. Retrieval augmentation

**Sources glimpsed:** production write-ups from Supermemory, Redis, and several 2026 hybrid-search
references; vstash (local-first hybrid retrieval); MemReranker (reasoning-aware reranking for
agent memory); Zep/Graphiti's production retrieval pipeline; a SemEval-2026 multi-turn RAG system
report.

**Where the field has actually settled, not just trending:**

Pure vector search alone fails on a meaningful chunk of real queries — one widely-cited 2026
production guide puts it at roughly 40%, which lines up with what everyone building on top of
embeddings alone eventually discovers: dense retrieval is bad at exact terms, IDs, version
numbers, and anything where phrasing matters more than meaning. The fix that's stopped being
debated is **hybrid retrieval**: run BM25 (or a sparse embedding equivalent) and dense vector
search in parallel, fuse with Reciprocal Rank Fusion, optionally rerank the top candidates with a
cross-encoder. RRF alone is reported to get typical RAG systems to roughly 91% recall@10 — that's
"production-grade" by the standards of most of the write-ups I looked at this week, and it costs
nothing extra at inference beyond running two retrieval paths instead of one.

**Where I'd push back on the hype:** ColBERT-style late-interaction reranking gets recommended a
lot, but every credible source this week qualified it the same way — add it only after you've
actually measured that RRF fusion isn't hitting your recall target, not by default. It's a real
technique with a real cost (infra, latency), and "add ColBERT" has become a bit of a reflexive
answer to "how do I improve retrieval," the same way "just add more retries" is a reflexive answer
to flaky APIs. Measure first.

**The genuinely new piece for a memory system specifically** (as opposed to generic document
RAG): Zep/Graphiti's production pipeline combines BM25, embedding similarity, and graph traversal
*with no LLM call at retrieval time*. That last part matters more than it sounds — a lot of early
memory systems (and a lot of tutorials) lean on an LLM to judge relevance or resolve ties at
retrieval time, which is slow and expensive on every single turn. Pushing that reasoning into the
index structure instead of the retrieval call is the difference between a system that costs
pennies and one that costs dollars per active user per day at scale.

**Relevance to this system:** Deliverable 1 flagged retrieval semantics as a requirement (retrieve
semantically, not lexically) but didn't specify a mechanism. Hybrid retrieval (BM25 + dense + RRF)
is the concrete answer, and it's no longer a research question — it's closer to "why would you
not do this."

---

## 2. Attention & context construction

**Sources glimpsed:** multiple 2026 context-engineering guides (Harness Engineering Academy,
Redis, MyEngineeringPath), a meta-agent prompt-budget paper, Mem0's write-up on context
engineering in multi-turn agents.

**The single most useful thing I found this week, and the one I'd lead with in the review:**
"context rot." Even on million-token context windows, measured performance starts degrading
around the 32K-token mark. This directly kills the naive instinct — which I'd guess most people
in this cohort have had at some point — that a bigger context window makes the memory problem go
away. It doesn't. More room to fill is more opportunity to fill it with the wrong things, and the
model's ability to identify what actually matters degrades well before the window itself fills up.
This is the strongest piece of evidence yet for why *selective* injection isn't a nice-to-have,
it's the whole game.

**The mechanism that's converged on across every serious production write-up:** treat the context
window as a fixed budget split into explicit zones — system prompt, retrieved memory, conversation
history, current input, output reserve — with a hard token ceiling per zone, monitored and alerted
on, not just hoped for. One widely cited breakdown for a 128K window: roughly 2K system prompt, 3K
few-shot, 40K retrieved context, 15K user input, 4K safety buffer, and fully half the window
reserved for output. The exact split is workload-specific, but the pattern — explicit budget per
zone, not "whatever's left" — is the part worth taking.

**A second point that's easy to underweight:** in agentic/multi-turn settings, tool outputs are
often the actual budget killer, not conversation history or retrieved memory. A handful of tool
calls can burn more tokens than the entire visible conversation. A memory system that only budgets
for "history vs. retrieved memory" and ignores tool-output accumulation will look fine in testing
and blow the budget in real agentic use.

**Relevance to this system:** this is the direct mechanism for Deliverable 1's "retrieve
selectively, not by replay" requirement, and it upgrades Open Question 5 (how should the context
window be allocated) from "an open question" to "there's a known pattern — explicit per-zone
budgets with monitoring — that just needs workload-specific numbers."

---

## 3. Index & storage layer

**Sources glimpsed:** multiple 2026 vector-database comparison guides (Firecrawl, Encore,
PingCAP/TiDB, AINative, MarkTechPost, Atlan, RankSquire).

**The honest state of this component: it's the least interesting design decision in the whole
system, and that's good news.** Unlike admission, ranking, and lifecycle — where the "right"
answer is still being actively argued over in papers — storage/index has converged into a boring,
well-understood decision tree:

- Under a few million vectors, already running Postgres → use pgvector. One system, one backup
  path, one team that already knows the tooling, transactional consistency with the rest of your
  data. Every source I looked at agreed on this without much hedging.
- Past tens of millions of vectors, or you need horizontal scaling / strict per-tenant isolation
  → a dedicated vector database (Qdrant, Weaviate, Milvus, Pinecone, Turbopuffer — pick based on
  self-hosted-vs-managed preference, not on marginal recall differences between them).
- Multi-tenancy is the one place actual architecture decisions still matter: namespace-based
  isolation (Pinecone-style — up to 100K namespaces on standard plans) is cheap but has limits at
  high tenant counts; physical per-tenant index isolation (Weaviate-style) costs more but gives a
  harder guarantee against cross-tenant leakage. For a system whose Deliverable 1 constraints
  explicitly require enforced tenant isolation, this is the one place in this component worth
  spending real design time — the rest is closer to a config choice than an architecture decision.

**Relevance to this system:** this component doesn't need a novel idea, it needs a correct,
boring choice made early so it stops being a question. The one place it connects back to a real
requirement is Deliverable 1's privacy/isolation constraint — namespace isolation vs. physical
isolation is a genuine trade-off worth writing into the system design rather than defaulting to
whatever the storage layer happens to make easiest.
