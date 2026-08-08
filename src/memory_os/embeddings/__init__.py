"""Embeddings package (ADR-007: local 384-d deterministic embeddings)."""

from memory_os.embeddings.embedder import embed, embedding_dim, is_available

__all__ = ["embed", "embedding_dim", "is_available"]