"""
Naive context injection.

Per the handbook: "injects results without sophisticated context allocation." This takes
the retrieved memories in similarity-rank order and appends them to the prompt until a
crude token budget (approximated as whitespace-split word count * 1.3) is hit, truncating
mid-list if needed. No per-zone budgeting, no prioritization beyond similarity rank, no
awareness of which memories might contradict each other.
"""

from memory_store import MemoryRecord

TOKENS_PER_WORD = 1.3  # rough approximation, consistent across the whole baseline


def estimate_tokens(text: str) -> int:
    return int(len(text.split()) * TOKENS_PER_WORD)


def inject(retrieved: list[tuple[MemoryRecord, float]], token_budget: int) -> tuple[str, int]:
    """
    Concatenate retrieved memories in rank order until the token budget is exhausted.
    Returns (injected_context_text, tokens_used).
    """
    lines = []
    tokens_used = 0
    for record, _score in retrieved:
        line = f"- {record.text}"
        line_tokens = estimate_tokens(line)
        if tokens_used + line_tokens > token_budget:
            break
        lines.append(line)
        tokens_used += line_tokens
    return "\n".join(lines), tokens_used
