"""G-M1: relational storage on PostgreSQL 17 + pgvector.

Schema is the single canonical `memories` table from design/data_model.md
(harlds deterministic supersession via valid_until, tenant isolation by
tenant_id pre-filter, hard-delete purge, and the five documented indexes).
"""