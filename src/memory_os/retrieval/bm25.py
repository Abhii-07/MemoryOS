"""Okapi BM25 over stored ``sparse_terms`` (Week 2 decision: read path never
re-tokenizes documents). Document term frequencies come from the
``sparse_terms`` JSONB column; statistics (df, total term count) are computed
over the *tenant-filtered candidate set only* — cross-tenant vocabulary is
never mixed into IDF/length stats.
"""

from __future__ import annotations

import math
from collections import defaultdict

K1 = 1.5
B = 0.75


def corpus_stats(term_freqs_by_doc: list[dict[str, int]]) -> tuple[int, float, dict[str, int]]:
    """Over the candidate set: (n_total, avg_dl, df).

    avg_dl = mean doc term-count over the same tenant's active candidate rows.
    """
    n_total = len(term_freqs_by_doc)
    total_terms = 0
    df: dict[str, int] = defaultdict(int)
    for freqs in term_freqs_by_doc:
        dl = sum(freqs.values())
        total_terms += dl
        for term in freqs:
            df[term] += 1
    avg_dl = total_terms / n_total if n_total else 0.0
    return n_total, avg_dl, dict(df)


def score(query_terms: list[str], term_freqs: dict[str, int],
          n_total: int, avg_dl: float, df: dict[str, int]) -> float:
    """Okapi BM25 score for one document, sharing the same corpus statistics."""
    if not query_terms or not term_freqs or n_total == 0:
        return 0.0

    dl = sum(term_freqs.values())
    denom_len = (1 - B + B * (dl / avg_dl)) if avg_dl > 0 else 1.0

    total = 0.0
    for term in query_terms:
        tf = term_freqs.get(term, 0)
        if tf == 0:
            continue
        idf = math.log(1.0 + (n_total - df[term] + 0.5) / (df[term] + 0.5))
        total += idf * (tf * (K1 + 1.0)) / (tf + K1 * denom_len)
    return total