# ADR-007: Deterministic Local Embeddings (sentence-transformers) for MVP

**Status:** accepted
**Date:** August 2026 (added during the MemoryOS merge, 2026-08-08)

## Context

`system_design_part1.md` §4's first assumption was that dense embeddings come
from an external service (`text-embedding-3-small`, 1536-d, per
`data_model.md` notes), and part3 §16 carried the risk that the baseline
sandbox had *no* network path to an embedding service — leaving a fallback to
lexical-only retrieval, which reopens Deliverable 1's original paraphrase
failure mode.

The MemoryOS stack decision (D-016 in `docs/DECISIONS.md`) requires
dev/prod consistency: anything that runs in development must work identically
in production, and nothing may depend on an external network hop at request
time.

## Decision Drivers

- Determinism: the same text must produce the same vector on every run, on any
  machine — required for reproducible tests (R8) and the "same-team same-test"
  gate.
- No external dependency at runtime; offline-capable architecture in keeping
  with the repo's local-only posture.
- Latency: local inference on CPU at first use; cached embeddings thereafter
  (MVP scale, no cold network round-trip in the retrieval path).
- pgvector compatibility: HNSW index type and `vector_norm(1)` (L2) with
  384-d vectors is fully supported; R2 pass confirms pgvector handles this
  dimensionality at MVP scale comfortably.

## Options Considered

1. **External API embeddings at MVP (OpenAI 1536-d).** Rejected: network
   dependency at write time, non-deterministic across versions, cost per
   request, and contradicts the local-only, reproducible-from-repo rule.
2. **Local sentence-transformers (e.g. `all-MiniLM-L6-v2`, 384-d).** Chosen:
   same model on all machines, offline, deterministic, free, dimension small
   enough for HNSW to be fast on a laptop, licensed Apache-2.0 (MIT),
   embed-table-fast.
3. **TF-IDF/Bag-of-words only.** Rejected for stock MVP: reopens the D1
   paraphrase failure (part3 §16); kept as the automated test fallback for
   `sparse_terms` retrieval when embedding tables are deliberately not
   populated (ADR-006's legacy).

## Decision

Sprint: M2 uses `sentence-transformers` (`all-MiniLM-L6-v2`, 384-d) as the
dense embedding source, run locally. The `dense_embedding` column stays
`vector(384)`. Any future swap (e.g. 1536-d models, or fine-tuned) only
changes the dimension + re-embed + rebuild (the migration cost precedent
already in `data_model.md`), never the schema structure.

## Consequences and Trade-offs

- Requires the model weights at build time (one-time `pip` + HuggingFace Hub
  download; ~80 MB). If the deployment environment cannot download, the
  `sparse_terms`/BM25-only fallback from `system_design_part3.md` §16
  remains the run-time degradation path — documented, not silent.
- Deterministic, cached embeddings keep E2 (R8 reproducibility) cheap.
- Fixed: the previously-open "which embedding service" risk (part3 §16) is
  now decided and testable from sprint plan G-M2 onward.

## Revisit Conditions

If a proprietary/multi-lingual embedding is later required (e.g., legal-grade
agreements, finance docs), revisit per dimension-swap migration path — this
ADR does not preclude replacing the model later; it only locks the local,
deterministic property for MVP.