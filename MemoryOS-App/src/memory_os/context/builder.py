"""G-M3 Context Construction: per-zone token-budgeted memory injection.

Read flow (system_design_part2 §8): retrieval -> ranking -> Context Builder
(per-zone token budgeting) -> injected context.

api_contracts.md Endpoint 2: `zone_budgets` optional; defaults derived from the
Week-2 research (~40% retrieved memory, 50% output reserve on large windows);
the sum of zone budgets must not exceed the total `token_budget` (400 otherwise).
Memories are injected in final rank order into the `retrieved_memory` zone
only, until that zone's ceiling — nothing ever overflows into another zone's
allocation (EC-010: zone overflow; Week 2 context-rot finding).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Token estimate consistent with the D3 baseline (words * 1.3) so the gate
# reproduces the 40-token long-conversation case exactly.
TOKENS_PER_WORD = 1.3

ZONE_ORDER = (
    "system_prompt",
    "retrieved_memory",
    "history",
    "tool_output",
    "input",
    "output_reserve",
)

DEFAULT_ZONE_WEIGHTS: dict[str, float] = {
    "system_prompt": 0.10,
    "retrieved_memory": 0.40,
    "history": 0.10,
    "tool_output": 0.05,
    "input": 0.05,
    "output_reserve": 0.30,
}


def estimate_tokens(text: str) -> int:
    """Token approximation consistent with D3 baseline (`words * 1.3`)."""
    return int(len(text.split()) * TOKENS_PER_WORD)


@dataclass
class ContextBudget:
    """Resolved per-zone ceilings; `sum(budgets) <= token_budget` enforced."""
    token_budget: int
    zones: dict[str, int]
    _used: dict[str, int] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if sum(self.zones.values()) > self.token_budget:
            raise ValueError(
                f"zone budgets {sum(self.zones.values())} exceed "
                f"token_budget {self.token_budget} (api_contracts: 400)"
            )

    @classmethod
    def from_budget_map(
        cls, token_budget: int, zone_budgets: dict[str, int] | None = None
    ) -> "ContextBudget":
        """Resolve explicit zone budgets (api_contracts Endpoint 2): provided
        zones override the default weights; omitted zones inherit defaults.
        """
        if zone_budgets:
            unknown = set(zone_budgets) - set(ZONE_ORDER)
            if unknown:
                raise ValueError(f"unknown zones: {sorted(unknown)}")
            provided_sum = sum(zone_budgets.values())
            if provided_sum > token_budget:
                raise ValueError(
                    f"zone budgets {provided_sum} exceed token_budget "
                    f"{token_budget} (api_contracts: 400)"
                )
            other = {
                z: w for z, w in DEFAULT_ZONE_WEIGHTS.items()
                if z not in zone_budgets
            }
            w_sum = sum(other.values())
            remaining = token_budget - provided_sum
            zones = {
                z: int(remaining * w / w_sum) for z, w in other.items()
            }
            zones.update(zone_budgets)
            return cls(token_budget=token_budget, zones=zones)
        zones = {
            zone: int(token_budget * weight)
            for zone, weight in DEFAULT_ZONE_WEIGHTS.items()
        }
        return cls(token_budget=token_budget, zones=zones)

    @property
    def used(self) -> dict[str, int]:
        return dict(self._used)

    def take(self, zone: str, n: int) -> bool:
        remaining = self.zones[zone] - self._used.get(zone, 0)
        if n > remaining:
            return False
        self._used[zone] = self._used.get(zone, 0) + n
        return True


@dataclass(frozen=True)
class ContextResult:
    result_type: str                # memory_found | no_relevant_memory
    injected_context: str | None
    tokens_used: int
    zones_used: dict[str, int] = field(default_factory=dict)
    memories: list[dict[str, Any]] = field(default_factory=list)


def build_context(
    *,
    memories: list[dict[str, Any]],
    token_budget: int,
    zone_budgets: dict[str, int] | None = None,
    zone: str = "retrieved_memory",
) -> ContextResult:
    """Build the injected context block within a per-zone budget.

    `memories` are already ranked (retrieval order = final ordering per
    system_design_part2 §9.2). Each memory is prefixed `- ` and admitted only
    if its token cost fits the zone's remaining ceiling. Everything over the
    ceiling stays out — nothing overflows into another zone.
    """
    budget = ContextBudget.from_budget_map(token_budget, zone_budgets)

    if not memories:
        return ContextResult(
            result_type="no_relevant_memory",
            injected_context=None,
            tokens_used=0,
            zones_used={zone: 0},
        )

    lines: list[str] = []
    block_tokens = 0
    placed: list[dict[str, Any]] = []
    for mem in memories:
        line = f"- {mem['text']}"
        cost = estimate_tokens(line)
        if not budget.take(zone, cost):
            break  # zone ceiling hit (EC-010): never overflow
        lines.append(line)
        placed.append(mem)
        block_tokens += cost

    if not lines:
        return ContextResult(
            result_type="no_relevant_memory",
            injected_context=None,
            tokens_used=0,
            zones_used={zone: 0},
        )

    return ContextResult(
        result_type="memory_found",
        injected_context="\n".join(lines),
        tokens_used=block_tokens,
        zones_used={zone: block_tokens},
        memories=placed,
    )


__all__ = [
    "TOKENS_PER_WORD", "estimate_tokens", "DEFAULT_ZONE_WEIGHTS", "ZONE_ORDER",
    "ContextBudget", "ContextResult", "build_context",
]