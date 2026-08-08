# Sources Catalog — Conversational Memory Intelligence System

> Index of every tool, framework, paper, benchmark, and vulnerability mentioned across
> the research weeks (D2). Each entry: what it is, why it matters to this project, and
> where it appears in the repo. **Verification status column**: filled during the Phase 6
> research passes (R1 = claim/citation verify, R2 = D4-readiness, R3 = product position).
>
> Claim tags used in deliverables: `[P:n]` → paper/primary source listed here; `[A: …]`
> → assumption; `[O]` → observed/verified in this project.

## Memory frameworks / reference implementations

| Tool / framework | Category | Relevance to MemoryOS | Appears in |
|---|---|---|---|
| Mem0 | Production memory layer (extraction, graph-ish store, retrieval) | Reference for admission + retrieval API surface; popular "memory in a box" | week-1, week-2, research_landscape |
| Zep / Graphiti | Temporal knowledge-graph memory | Reference for temporal graph edges, bi-temporal facts, contradiction handling | week-1, week-2 |
| MemGPT / Letta | OS-memory-metaphor agent memory (paging, main memory) | Primary citation for R5 (context budget) and R6 (hierarchy) — [P:9] | week-1, 02_timeline |
| Cognee | Graph RAG + memory pipelines | Alternative design point: graph-first consolidation | week-1, week-3 |
| LangMem | LangChain memory components | Reference for extraction/consolidation prompts and memory APIs | week-1 |
| MIRIX | Multi-agent memory system paper (arXiv:2507.07957) | 85.4% SOTA on LoCoMo; six memory types | week-3 |
| A-MEM | Agentic memory (Zettelkasten-style) | Alternative representation: link-based memories | week-1 |
| Supermemory | Personal knowledge + memory product | Product-positioning reference (R3), memory editor UX | week-3, week-4 |

## Infrastructure / retrieval components

| Tool | Category | Relevance | Appears in |
|---|---|---|---|
| pgvector (PostgreSQL extension) | Vector store | Candidate D6 store: HNSW + SQL + tenant isolation in one system | week-2 |
| FAISS | Approximate nearest neighbor library | Retrieval substrate for baseline & design — [P:10] | week-2, 03_failure_analysis |
| HNSW | Graph-based ANN index | Index algorithm — [P:11] | week-2, 03_failure_analysis |
| RRF (Reciprocal Rank Fusion) | Rank fusion | Dense+sparse hybrid ranking candidate — [P:5] discussion | week-2 |

## Papers / primary sources (map to `[P:n]` tags in D1)

| Tag | Source | What it establishes |
|---|---|---|
| [P:1] | Neural Turing Machines (Graves et al., 2014) | External read/write memory + differentiable controller |
| [P:2] | End-to-End Memory Networks (Sukhbaatar et al., 2015) | Attention over an external memory store |
| [P:3] | Memory Networks (Weston et al., 2014) | External read/write memory addressed by content |
| [P:4] | Transformer attention (Vaswani et al., 2017) | Finite context window; attention over tokens |
| [P:5] | Retrieval-Augmented Generation (Lewis et al., 2020) | RAG pattern: ground NLG in an external corpus (verification R1: RAG motivates by parametric-memory limits, not finite-context replay; "~40% dense-fail" is practitioner-origin, not paper-backed) |
| [P:6] | RETRO (Borgeaud et al., 2021) | Iterative retrieval at document scale |
| [P:7] | Memorizing Transformers (Wu et al., 2022) | Retrieval integrated into model-internal memory |
| [P:8] | Generative Agents (Park et al., 2023) | Observation → reflection → summarization pipeline; reflection/planning retrieval (verification R1: "consolidation" is not the paper's term) |
| [P:9] | MemGPT (Packer et al., 2023) | Memory hierarchy, paging, token-budget control |
| [P:10] | FAISS (Johnson et al., 2017) | Similarity search library |
| [P:11] | HNSW (Malkov & Yashunin, 2016) | Hierarchical navigable small-world graphs |
| (verified) | LoCoMo (long-conversation memory benchmark) | ACL 2024; full-context 72.9% / Mem0-graph 68.4% / Mem0 66.9% / RAG 61.0%; MIRIX SOTA 85.4% — pass R2, 2026-08-08 |
| (pending) | PIIBench (PII leak benchmark) | OOD PII detection instability (0.96→0.18) — verify with source |

## Evaluation & observability

| Tool | Relevance | Appears in |
|---|---|---|
| Braintrust | Eval harness + evals-as-code | Reference for R8 offline evaluation harness | week-3 |
| OpenObserve | Observability backend | Reference for R7 decision tracing | week-3 |

## Privacy, safety, isolation (week-4 floor for threat model)

| Source | Type | Relevance |
|---|---|---|
| OWASP LLM AI Security 2025 (LLM04 Data & Model Poisoning; LLM08 Vector & Embedding Weaknesses) | Threat taxonomy | Required threat-model vocabulary for D4 `threat_model.md`; verified R3 — no standalone memory-manipulation slot exists |
| OpenAI Privacy Filter | Detection pattern (regex+NER) | Reference for pre/post PII guardrail (invariant #5) |
| MemoryGraft | Named attack | Memory-planting/injection attack class (D4 threat model) |
| MINJA | Named attack | Unauthorized memory read/write class (D4 threat model) |
| Cisco MemoryTrap (disclosed ~Apr–May 2026, patched) | Real disclosed vulnerability against Claude Code | Evidence that prompt-injection-via-memory is a **current**, shipping threat |

## How to use this catalog
1. Every deliverable claim tagged `[P:n]` must resolve to a row above (or be added with its source).
2. Before D4: run research pass **R1** (verify each row's claims + citations) ✅ done 2026-08-08, then **R2** (fill the
   `(pending)` benchmark rows) ✅ done 2026-08-08, then **R3** (product positioning against Supermemory/Mem0/Zep) ✅ done 2026-08-08.
3. Update this file's *verification status* during those passes; never cite a claim marked unverified. The
   `2026-08-08-R1/R2/R3` pass files in `research/passes/` carry the verdicts; remaining unverified: PIIBench OOD figures.