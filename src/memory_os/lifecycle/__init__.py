"""G-M4 lifecycle: four-lever consolidation + deletion propagation (EC-04/06)."""

from memory_os.lifecycle.manager import (
    DECAY_DEFAULT_MIN_IMPORTANCE,
    MAX_LINEAGE_DEPTH,
    MAX_SYNC_DERIVED,
    DeletionResult,
    LifecycleError,
    LifecycleManager,
    RecordNotFound,
    SUMMARY_PREFIX,
)

__all__ = [
    "LifecycleManager", "DeletionResult", "LifecycleError", "RecordNotFound",
    "MAX_LINEAGE_DEPTH", "MAX_SYNC_DERIVED", "SUMMARY_PREFIX",
    "DECAY_DEFAULT_MIN_IMPORTANCE",
]