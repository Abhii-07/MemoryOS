CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS memories (
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

-- Tenant isolation: every retrieval query pre-filters on tenant_id (Week 4)
CREATE INDEX IF NOT EXISTS idx_memories_tenant_status
    ON memories (tenant_id, status)
    WHERE status = 'active';

-- Dense vector retrieval: HNSW for approximate nearest-neighbor (Week 2)
CREATE INDEX IF NOT EXISTS idx_memories_dense
    ON memories
    USING hnsw (dense_embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Validity window: supersession lookup (Week 1)
CREATE INDEX IF NOT EXISTS idx_memories_tenant_valid_from
    ON memories (tenant_id, valid_from DESC)
    WHERE status = 'active';

-- Lineage walk: deletion propagation (Week 4)
-- GIN index on the UUID array for efficient "does this array contain X" queries
CREATE INDEX IF NOT EXISTS idx_memories_lineage
    ON memories
    USING gin (consolidation_lineage);

-- Lifecycle worker: candidate scan for decay/eviction
CREATE INDEX IF NOT EXISTS idx_memories_lifecycle_scan
    ON memories (status, provenance, importance_score, valid_from)
    WHERE status = 'active';

-- Deletion-propagation jobs (api_contracts Endpoint 3: the 202 Accepted path).
-- A large lineage cascade is persisted here as 'pending' and completed by a
-- later deterministic run; the API never converts an async cascade into a
-- false-positive immediate success.
CREATE TABLE IF NOT EXISTS propagation_jobs (
    job_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id      TEXT NOT NULL,
    deleted_id     UUID NOT NULL,
    state          TEXT NOT NULL DEFAULT 'pending'
                   CHECK (state IN ('pending', 'completed')),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at   TIMESTAMPTZ
);