"""Reciprocal Rank Fusion — combine two ranked lists into one fused ranking.

k = 60 (Cormack, Clarke & Buettcher 2009; R2 research pass confirmed k=60 as
the standard value). Pure rank-weighted, no score calibration across signals.
"""

from __future__ import annotations

from collections import defaultdict

RANK_FUSION_K = 60


def fuse(ranked_by_signal: list[list[str]], *, k: int = RANK_FUSION_K) -> dict[str, float]:
    """Input: one list of record IDs per retrieval signal (highest first).

    Output: {record_id: fused_score}, score = sum over signals of
    1/(k + rank_of_record_in_that_signal). Record missing from a signal
    contributes 0.
    """
    fused: dict[str, float] = defaultdict(float)
    for ranking in ranked_by_signal:
        for rank, record_id in enumerate(ranking, start=1):
            fused[record_id] += 1.0 / (k + rank)
    return dict(fused)