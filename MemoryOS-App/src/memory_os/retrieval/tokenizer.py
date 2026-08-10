"""Query/document tokenizer for sparse retrieval (BM25).

Stored per-data_model.md as ``sparse_terms`` (term → count) at write time so
the read path never re-tokenizes documents. This module owns the *query*
tokenization plus the helper that builds the write-time term map. Numbers are
kept as whole tokens (EC-16: exact slot values like "1992" must survive).
"""

from __future__ import annotations

import re
from collections import Counter

_STOPWORDS = frozenset(
    """a an and are as at be been but by can could did do does for from had has have
    he her hers him his how i if in into is it its me my no nor not of on or our ours
    out so that the their them then there these they this to too or under up us we what
    were when where which while who whom will with would you your yours""".split()
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Lowercase alnum tokens; drop stopwords and single-char tokens."""
    tokens = [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS and len(t) > 1]
    return tokens


def term_frequencies(text: str) -> dict[str, int]:
    """Write-time sparse map: token → count (what goes in ``sparse_terms``)."""
    return dict(Counter(tokenize(text)))


def numeric_tokens(query: str) -> list[str]:
    """Digits-only tokens (EC-16 exact slot values)."""
    return [t for t in _TOKEN_RE.findall(query.lower()) if t.isdigit() and len(t) >= 2]