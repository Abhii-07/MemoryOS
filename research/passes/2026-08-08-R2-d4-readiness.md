# Research Pass R2 — D4-Design-Readiness Facts (2026-08-08)

> Goal: verify the external facts the D4 design will lean on — benchmark
> landscape, supersession/lifecycle precedents, retrieval-fusion numbers,
> and pgvector at scale. Method: web verification performed 2026-08-08.
> Outcome: 5/7 fully supported, 1 supported-with-nuance, 1 corrected.

## 1. LoCoMo (long-conversation memory benchmark) — SUPPORTED

- Measures LLM/agent recall over very-long, multi-session dialogues (QA:
  single-hop, temporal, multi-hop, open-domain; event summarization).
  Conversation length: paper reports avg ~300 turns / ~9K tokens per
  conversation (up to 35 sessions). Source: ACL 2024, aclanthology.org/2024.acl-long.747.
- Headline numbers (LLM-as-judge, 2025 reports): full-context 72.9%,
  Mem0-graph 68.4%, Mem0 66.9%, plain RAG 61.0%. MIRIX (2025) later claimed
  SOTA 85.4% vs Zep 79.09%; full-context bound 87.5%.
- Status: still the de-facto long-conversation-memory benchmark in 2026.
- **D4 implication:** our contradiction/staleness metric is explicitly a
  gap-filler "the standard benchmark does not score" (matches old-repo
  week-3 finding; LoCoMo does not score knowledge updates).

## 2. Mem0 (current architecture/lifecycle) — SUPPORTED with nuance

- Confirmed: admission/"ADD" phase + update phase with LLM-classified
  operations (ADD/UPDATE/MERGE, DELETE, NOOP) via tool calls; graph-memory
  variant (entity+relation triplets; ~2pp gain on LoCoMo, 68% vs 67%).
- Retrieval: vector-similarity only in the plain path (sparse+dense hybrid is
  not core); "hybrid" refers to multi-store (vector + graph + KV).
- Supersession: current Mem0 has `expiration_date` (hides, never deletes;
  both Platform and OSS) — analogous to our valid_until, but no
  deterministic supersession cascade. OSS v3 `add()` is ADD-only with MD5
  dedup (no UPDATE/DELETE in that path).
- OpenMemory (mem0 OSS product) sunset around Jul 2026; CVE-2026-59705
  reported against it.
- **D4 implication:** our deterministic valid_until supersession is a
  defensible differentiator vs Mem0's LLM-decided updates + expiry flag.

## 3. Letta (MemGPT) current state — SUPPORTED

- Active 2026: Apache-2.0, ~22.8k stars, v0.16.8 (May 2026); memory blocks
  (persona/human/custom), recall + archival store; agents persist as
  services. LongMemEval-era figure: 93.4% from MemGPT paper lineage.

## 4. Zep / Graphiti — SUPPORTED (streaming claim caveated)

- Bi-temporal model confirmed: valid-time (t_valid/t_invalid) + system-time
  (created/expired); contradiction-driven edge invalidation; non-lossy
  episode subgraph; retriever = semantic + BM25 + BFS with RRF/cross-encoder.
- "Memory streaming"/continuous ingestion is a marketing claim — no formal
  streaming paper.
- **D4 implication:** Zep's bi-temporal model is the closest published
  precedent for our Approach B supersession design.

## 5. RRF numbers — SUPPORTED (corrected attribution)

- k=60 standard (Cormack, Clarke, Büttcher, SIGIR 2009) — default in
  Elasticsearch/OpenSearch/Qdrant.
- The "65% BM25 / 78% dense / 91% recall@10 hybrid" figure is NOT from an
  academic paper and NOT from "Improving Context…" — it traces to a
  practitioner benchmark: supermemory.ai hybrid-search guide (Apr 2026).
- Old-repo week-2 research attributed the figure to "production write-ups"
  (correct); our PRD's "[A: verify in R2]" now resolves to this source.
- **Correction applied:** PRD R4 acceptance row now cites the practitioner
  benchmark explicitly (`[O: supermemory.ai, 2026-04]`).

## 6. pgvector / ANNS at scale — SUPPORTED

- HNSW stable since v0.5.0 (2023); current pgvector ~v0.8.3 (Jun 2026).
- Supabase 1M×1536-dim reference: ~270 QPS @ 0.99 recall on 16 cores,
  ~470 QPS on 32 cores; typical 1M–10M-vector workloads: 10–30 ms
  (ef_search=40) to 30–60 ms (ef_search=100); hybrid 50–100 ms.
- **D4 implication:** p95 <150 ms invariant is comfortably reachable at
  MemoryOS's scale; ANNS parameters (ef_search/HNSW) become tuning knobs.

## 7. MIRIX — CORRECTED (was: "MENO benchmark")

- MIRIX = "Multi-Agent Memory System for LLM-Based Agents" (arXiv:2507.07957,
  Jul 2025): six memory types (core/episodic/semantic/procedural/resource/
  knowledge vault) + Meta Memory Manager; 85.4% SOTA on LoCoMo.
- **No "MENO" benchmark exists in the sources reviewed.**
- **Correction applied:** `research/sources_catalog.md` MIRIX row updated:
  it is a memory-system paper + eval result, not "a benchmark".

## R2 verdict

READY. Facts the D4 design depends on are verified with current sources;
two catalog/PRD rows corrected (MIRIX description, RRF-figure attribution);
benchmark numbers for PRD R4 acceptance updated (LoCoMo SOTA band vs
practitioner hybrid benchmark).
