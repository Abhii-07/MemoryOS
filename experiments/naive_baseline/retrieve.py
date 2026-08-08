"""
Naive retrieval: a single similarity signal, nothing else.

Design note on the embedding choice: this environment has no network access to a hosted
embedding API or a model hub, so this baseline uses TF-IDF + cosine similarity as its one
similarity signal, refit fresh over each user's full memory set at query time. This is a
legitimate (if old-fashioned) instance of "naive vector similarity retrieval" -- it is
lexical rather than truly semantic, which if anything makes it a *fair or slightly harsher*
stand-in for the failure mode this deliverable is trying to surface, since Deliverable 1's
approach-4 failure case (semantically-similar-but-differently-worded memories) applies just as
much, if not more, to TF-IDF as it does to a neural embedding. This is documented as a scoping
limitation in baseline_protocol.md, not hidden.

Beyond the choice of signal, retrieval here is deliberately naive in the way the handbook
specifies: one similarity signal, no recency weighting, no importance weighting, no
deduplication, no contradiction handling.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from memory_store import MemoryRecord


def retrieve(query: str, candidates: list[MemoryRecord], top_k: int = 5) -> list[tuple[MemoryRecord, float]]:
    """Return the top_k candidates ranked purely by TF-IDF cosine similarity to the query."""
    if not candidates:
        return []

    corpus = [r.text for r in candidates] + [query]
    vectorizer = TfidfVectorizer()
    try:
        matrix = vectorizer.fit_transform(corpus)
    except ValueError:
        # Empty vocabulary (e.g. query and all memories are pure stopwords/punctuation)
        return []

    query_vec = matrix[-1]
    memory_vecs = matrix[:-1]
    sims = cosine_similarity(query_vec, memory_vecs)[0]

    ranked_idx = np.argsort(-sims)[:top_k]
    return [(candidates[i], float(sims[i])) for i in ranked_idx if sims[i] > 0]
