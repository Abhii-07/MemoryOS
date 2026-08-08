# ADR-003: pgvector for MVP Storage Layer

**Status:** accepted
**Date:** August 2026

## Context

The system needs a storage and index layer for memory records, supporting both dense vector
similarity search and structured filtering (tenant, status, validity window).

## Decision Drivers

- Near-unanimous recommendation across every 2026 vector-database comparison scanned in Week 2's
  research: under a few million vectors, pgvector on an existing Postgres install is the standard
  choice.
- This system's actual expected scale at MVP is well under that threshold.
- A single system (rather than Postgres plus a separate vector database) means transactional
  consistency between memory records and any other application data, and one backup/monitoring
  stack instead of two.

## Options Considered

1. **pgvector on Postgres.** Chosen for MVP.
2. **Dedicated vector database** (Qdrant, Weaviate, Milvus, Pinecone, Turbopuffer). Rejected for
   MVP as premature infrastructure — Week 2's research found no source recommending this at this
   system's expected scale.
3. **In-memory vector index with periodic persistence** (e.g. FAISS with manual snapshotting).
   Rejected — no transactional guarantees, and this system's correctness priorities (Part 1,
   Section 3: correctness ranks above cost) make an ad-hoc persistence layer a poor trade.

## Decision

Option 1. `data_model.md` specifies the schema as a single Postgres table with an HNSW vector
index, a GIN index for lineage lookups, and composite B-tree indexes for tenant/status filtering.

## Consequences and Trade-offs

Week 2's self-review flagged a real caveat that still applies: the cited recommendations assumed
generic RAG workloads (read-heavy, mostly append-only). This system's supersession and lifecycle
mechanisms make it comparatively write/update/delete-heavy — pgvector's behavior under that access
pattern hasn't been independently verified, only assumed reasonable by extension.

## Validation Plan

Re-validate pgvector's fit once Deliverable 6 produces real update/delete volume, not before —
inventing a number now would be unearned precision this project has avoided elsewhere.

## Revisit Conditions

Migrate to a dedicated vector database if: (a) dataset size crosses into the tens-of-millions of
vectors, or (b) Deliverable 6's measured write/update/delete volume shows pgvector's performance
degrading in a way generic RAG benchmarks didn't predict.
