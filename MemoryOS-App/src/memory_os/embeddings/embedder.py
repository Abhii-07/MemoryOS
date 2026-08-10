"""Embedding adapter for MemoryOS.

ADR-007: deterministic local embeddings via sentence-transformers
(``all-MiniLM-L6-v2``, 384-d). The model is lazy-loaded once per process and
cached on disk via HF_HOME (`.hf-cache/`). If the model cannot be loaded
(first-run offline), the adapter degrades to ``None`` embeddings — callers use
the BM25-only fallback (part3 §16) and must never silently pretend dense
retrieval happened.
"""

from __future__ import annotations

import os
import threading
from typing import Any

_HF_HOME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".hf-cache")
os.environ.setdefault("HF_HOME", os.path.abspath(_HF_HOME))

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_DIM = 384

_lock = threading.Lock()
_model: Any = None
_model_ready = False


def embedding_dim() -> int:
    return _DIM


def is_available() -> bool:
    """True if the local model is loadable (i.e. dense retrieval is usable)."""
    with _lock:
        _ensure_model()
        return _model_ready


def embed(texts: list[str]) -> list[list[float]] | None:
    """Embed texts → list of 384-d vectors. Returns None when the model is
    unavailable so callers can fall back to BM25-only retrieval."""
    with _lock:
        _ensure_model()
        if not _model_ready:
            return None
        vecs = _model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return [v.tolist() for v in vecs]


def _ensure_model() -> None:
    global _model, _model_ready
    if _model_ready:
        return
    try:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(_MODEL_NAME)
        _model_ready = True
    except Exception:
        _model = None
        _model_ready = False
