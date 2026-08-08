"""MemoryOS: conversational memory intelligence system.

Package root. Implementation lives per the D4 design freeze:
- db/      : PostgreSQL 17 + pgvector schema and store (G-M1)
- retrieval/: hybrid BM25+dense+RRF (G-M2, planned)
- admission/ + context/ (G-M3, planned)
"""