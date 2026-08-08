# Data Model

**Conversational Memory Intelligence System — Deliverable 4**
Abhijeet Hiwale · August 2026

Expands system_design.pdf, Section 7. Every field here traces to either a research week decision,
a Deliverable 3 finding, or a Deliverable 1 requirement — nothing was added speculatively.

---

## Core Table: `memories`

```sql
CREATE TABLE memories (
    -- Identity
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id             TEXT NOT NULL,        -- hard partition key; never null (Week 4)
    user_id               TEXT NOT NULL,        -- sub-partition within a tenant

    -- Content
    text                  TEXT NOT NULL,
    dense_embedding       vector(384),          -- pgvector; dimension per ADR-007 (local model)
    sparse_terms          JSONB,                -- BM25 term frequencies (Week 2: hybrid retrieval)

    -- Admission metadata (Week 1)
    admission_op          TEXT NOT NULL         -- ADD | UPDATE | DELETE | NOOP
                          CHECK (admission_op IN ('ADD','UPDATE','DELETE','NOOP')),
    provenance            TEXT NOT NULL         -- user_stated | assistant_generated |
                          CHECK (provenance IN   --   tool_derived | retrieved_document
                              ('user_stated','assistant_generated',
                               'tool_derived','retrieved_document')),
    confidence            REAL NOT NULL         -- 0.0–1.0; gates low-confidence supersession fallback
                          CHECK (confidence >= 0.0 AND confidence <= 1.0),

    -- PII (Week 4)
    pii_scan_result       TEXT NOT NULL
                          CHECK (pii_scan_result IN ('pass','flag','redacted')),
    pii_detector_version  TEXT,                 -- logged so results are reproducible

    -- Validity window (Week 1: deterministic supersession)
    valid_from            TIMESTAMPTZ NOT NULL DEFAULT now(),
    valid_until           TIMESTAMPTZ,          -- null until superseded; set by UPDATE admission

    -- Lifecycle (Week 1: four-lever framework)
    status                TEXT NOT NULL DEFAULT 'active'
                          CHECK (status IN ('active','decayed','merged','evicted','deleted')),
    importance_score      REAL,                 -- set at admission; drives decay eligibility

    -- Lineage (Week 4: deletion propagation / backflow prevention)
    consolidation_lineage UUID[],               -- source record IDs if this is a consolidated record

    -- Audit
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### Notes on specific field choices

**`dense_embedding vector(384)`** — dimension matches the deterministic local embedder
(`sentence-transformers/all-MiniLM-L6-v2`, 384-d) chosen for MVP by **ADR-007** (added
2026-08-08). The original draft assumed OpenAI's `text-embedding-3-small` (1536-d) as an external
service; the MemoryOS stack requires local, deterministic embeddings (no network at request
time, dev/prod consistency). If a different model is chosen later, only this dimension value
and the index's `vector_ops` change — never the schema structure — plus a re-embed + index
rebuild per the migration path at the end of this file.

**`sparse_terms JSONB`** — BM25 term frequencies stored as a key-value map at write time rather
than computed at query time, so retrieval doesn't re-tokenize on every read. Week 2's hybrid
retrieval decision drives this.

**`status` includes `'merged'`** — data_flow.pdf (background flow) showed that source records
don't get deleted when a consolidated record is created; they're retained with `status = 'merged'`
for lineage integrity. This is the fifth status value (Section 7 listed four; `'merged'` was
implicit in the data flow's behaviour but not explicitly named — this schema names it explicitly).

**`consolidation_lineage UUID[]`** — a Postgres array of source record IDs. When the Lifecycle
Worker evicts a record in response to a deletion request, it queries for all records whose
`consolidation_lineage` contains the deleted ID, and re-consolidates or evicts those too (Week 4's
backflow-prevention requirement). This is still the least-proven part of the design — the field
makes it implementable; Deliverable 6 verifies it actually works.

---

## Indexes

```sql
-- Tenant isolation: every retrieval query pre-filters on tenant_id (Week 4)
CREATE INDEX idx_memories_tenant_status
    ON memories (tenant_id, status)
    WHERE status = 'active';

-- Dense vector retrieval: HNSW for approximate nearest-neighbor (Week 2)
CREATE INDEX idx_memories_dense
    ON memories
    USING hnsw (dense_embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Validity window: supersession lookup (Week 1)
CREATE INDEX idx_memories_tenant_valid_from
    ON memories (tenant_id, valid_from DESC)
    WHERE status = 'active';

-- Lineage walk: deletion propagation (Week 4)
-- GIN index on the UUID array for efficient "does this array contain X" queries
CREATE INDEX idx_memories_lineage
    ON memories
    USING gin (consolidation_lineage);

-- Lifecycle worker: candidate scan for decay/eviction
CREATE INDEX idx_memories_lifecycle_scan
    ON memories (status, provenance, importance_score, valid_from)
    WHERE status = 'active';
```

### Index rationale

The HNSW index parameters (`m=16`, `ef_construction=64`) are conservative starting-point defaults
consistent with pgvector's own documentation for an MVP workload — they are not tuned values, and
they should be revisited once Deliverable 6 produces real recall/latency numbers at realistic
query volume (Week 2's self-review flag on pgvector re-validation applies here specifically).

The GIN index on `consolidation_lineage` exists entirely to support the backflow-prevention
deletion walk — without it, finding all derived records that reference a given source ID requires
a full table scan, which degrades the deletion consistency window in proportion to dataset size.

---

## Constraints and Integrity Rules

Beyond the column-level `CHECK` constraints above, the following are application-level rules
enforced by the Admission component, not by the database:

- `tenant_id` arriving at Admission must match a tenant ID authenticated upstream (Part 1,
  Section 4's assumption that authentication is external).
- When `admission_op = UPDATE`, Admission links the new record to the prior same-entity/slot
  record by setting the prior record's `valid_until = now()` — the entity/slot-linking step
  (Week 1's self-review flagged this as an unresolved prerequisite; it's not in this schema
  because it's a lookup problem, not a storage problem).
- `dense_embedding` may be null only while an async embedding call is in flight at admission
  time; a record with a null embedding is not eligible for retrieval until it is populated.
  This is the embedding-service failure mode from system_design.pdf, Section 16: BM25-only
  retrieval is the per-request fallback, not a system-wide mode.

---

## Migration Path

On schema changes (e.g. adding a new provenance type or a new status value):

- `CHECK` constraints are additive-safe via `ALTER TABLE ... DROP CONSTRAINT ... ADD CONSTRAINT`.
- `consolidation_lineage` array growth is backward-compatible (existing null values stay valid).
- Any change to `dense_embedding` dimensions requires a full re-embed of existing records and
  index rebuild — this is an expensive migration that reinforces Week 2's "don't switch embedding
  services without measuring the full cost" point.
