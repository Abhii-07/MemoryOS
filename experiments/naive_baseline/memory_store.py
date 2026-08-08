"""
Naive memory store.

Per the handbook's definition of "naive": stores every candidate memory that comes in,
with no admission filtering, no deduplication, no consolidation, and no decay. This is
deliberately the simplest possible persistence layer -- a flat list per user, nothing more.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import itertools

_id_counter = itertools.count(1)


@dataclass
class MemoryRecord:
    id: int
    user_id: str
    text: str
    timestamp: datetime
    sensitive: bool = False  # ground-truth label for evaluation only, not used by the system


class NaiveMemoryStore:
    """Stores every memory it's given. No filtering, no merging, no expiry."""

    def __init__(self):
        self._records: list[MemoryRecord] = []

    def add(self, user_id: str, text: str, timestamp: datetime, sensitive: bool = False) -> MemoryRecord:
        record = MemoryRecord(
            id=next(_id_counter),
            user_id=user_id,
            text=text,
            timestamp=timestamp,
            sensitive=sensitive,
        )
        self._records.append(record)
        return record

    def all_for_user(self, user_id: str) -> list[MemoryRecord]:
        # Naive storage does no per-user isolation at the index level -- it filters
        # by user_id at query time, which is exactly the kind of application-layer-only
        # isolation Week 2's research flagged as a real (if common) risk.
        return [r for r in self._records if r.user_id == user_id]

    def count(self) -> int:
        return len(self._records)

    def storage_bytes(self) -> int:
        # Rough proxy for storage growth: total character count of all stored text.
        return sum(len(r.text.encode("utf-8")) for r in self._records)
