"""Deterministic classification grammar for admission (ADR-008).

Pure functions of text — no LLM, no network, same input → same verdict on any
machine. This module is the *entire* grammar; extend it here + freeze with
tests, never touch the pipeline.

Priority order (checked top-to-bottom in `Admitter.admit`):
  PII scrub → DELETE → NOOP → UPDATE (correction marker + existing slot) → ADD.
"""

from __future__ import annotations

import re

# --- PII pre-guardrail (invariant #5): regex patterns ------------------------
# Redaction REPLACES the secret with a placeholder at write time, so the raw
# value never exists in the store (EC-07: measured leak 0.0).

PII_VERSION = "memoryos-pii-2026-08-08"

_PII_RULES: list[tuple[str, re.Pattern[str], str]] = []


def _pii(name: str, pattern: str, redaction: str) -> None:
    _PII_RULES.append((name, re.compile(pattern, re.IGNORECASE), redaction))


_pii("email",          r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",      "[EMAIL]")
_pii("phone",          r"\b(?:\+?\d{1,3}\s?)?\d{3}[-. ]\d{3}[-. ]\d{4}\b",        "[PHONE]")
_pii("ssn",            r"\b\d{3}-\d{2}-\d{4}\b",                                 "[SSN]")
_pii("credit_card",    r"\b(?:\d[ -]?){12,}\d{3,}\b",                            "[CARD]")
_pii("api_key",        r"\b(?:sk|pk|AKIA)[A-Za-z0-9]{16,}\b",                    "[API_KEY]")
_pii("password_value", r"\b(?:password|passwd|pwd|passphrase|secret|token|api[_ ]?key)\b\s*(?:is|[:=]|was|used)\s*\S+", "[REDACTED]")
_pii("secret_word",    r"\b(?:password|passwd|pwd|passphrase|secret|token|apikey|api[_ ]?key)\b", "[REDACTED]")
_pii("ipv4",           r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",                "[IP]")


def scrub_pii(text: str) -> tuple[str, list[str]]:
    """Replace PII matches with placeholders.

    Returns (scrubbed_text, [rule names that fired]) — deterministic, pure.
    A rule fires when at least one placeholder substitution was made.
    """
    hits: list[str] = []
    for name, pattern, redaction in _PII_RULES:
        new_text, n = pattern.subn(redaction, text)
        if n:
            hits.append(name)
        text = new_text
    return text, hits


# ─── DELETE target parsing ───────────────────────────────────────────────────
_DELETE_RE = re.compile(
    r"\b(forget|delete|remove|erase|drop|purge|discard)\b"
    r"(?:\s+(?:all|any|everything|my|the|that|those))?"
    r"\s*(?:about|regarding|tied to)?\s*(?P<target>.+?)\s*\.?\s*$",
    re.IGNORECASE,
)


def parse_delete_target(text: str) -> str | None:
    """Extract the target of a delete directive; None if not a delete turn."""
    m = _DELETE_RE.search(text)
    if not m:
        return None
    target = m.group("target").strip(" .,!?")
    target = re.sub(r"^(?:the|a|an|my|all(?: of)?)\s+", "", target, flags=re.IGNORECASE)
    return target or None


# ─── NOOP: neutral / generic utterances (EC-017) ─────────────────────────────
_NOOP_WORDS = frozenset(
    """hmm hm mmm okay yeah yep nope sure fine good great thanks thank thx bye
    goodbye hey hi hello lol aha ah um er oh welp ok got move sounds indeed
    right fine then""".split()
)

_NOOP_EMPTY = re.compile(r"^[^a-z0-9]{0,4}$", re.IGNORECASE)


def is_noop(cleaned: str) -> bool:
    """True for greetings/filler/neutral single or multi-word utterances.

    "hmm ok", "thanks!", "👍", "got it" -> True; anything with a content word
    -> False. The token set is frozen here (ADR-008: grammar lives in this
    module).
    """
    if _NOOP_EMPTY.match(cleaned):
        return True
    from memory_os.retrieval.tokenizer import tokenize

    tokens = tokenize(cleaned)
    if not tokens:
        return True  # stopword-only (EC-09)
    return all(t in _NOOP_WORDS for t in tokens)


# ─── Correction markers (UPDATE signal) ───────────────────────────────────────
CORRECTION_MARKERS = (
    "no", "actually", "instead", "switched", "changed", "no longer",
    "not anymore", "rather", "correction", "update", "wait",
)


def has_correction_marker(text: str) -> bool:
    """True when the turn reads like a correction (UPDATE candidate)."""
    lowered = text.lower()
    return any(m in lowered for m in CORRECTION_MARKERS)


# ─── Slot grammar (ADR-008): text -> slot_key. Deterministic signatures.
# Collision policy: variants of the SAME real-world slot must yield the SAME
# key ("uses Postgres" vs "switched to Node" both = tool:choice) so supersession
# fires; unrelated facts must NOT collide ("favorite coffee" vs "favorite
# bread" stay separate because the object noun is captured).
_SLOT_RULES: list[tuple[re.Pattern[str], str]] = []


def _slot(pattern: str, prefix: str) -> None:
    _SLOT_RULES.append((re.compile(pattern, re.IGNORECASE), prefix))


# favorite <noun> — noun captured so favorites of different things stay apart
_slot(r"\bfavorite\b\s+(coffee|tea|drink|food|dish|color|city|place|spot|team|movie|music|brand|book|thing)\b", "preference:favorite")
# preference/liking verbs (prefer/like/love/want) — any object is the slot
_slot(r"\b(?:prefers?|like[sd]?|love[sd]?|wants?|wanted)\s+", "preference:liking")
# tool/stack choice — the D3 c2/c3 "switched to" / "uses" / "no longer" cases
_slot(r"\b(?:uses?|use|switched|switching|moved)\s+(?:to|from)?\s*", "tool:choice")
_slot(r"\b(?:stack|framework|language|backend|frontend)\b", "project:stack")
_slot(r"\b(?:database|db|schema|postgres|mongo)\b", "project:database")
_slot(r"\b(?:hosting|hosted|host|deploy|deployment|cloud|aws|azure)\b", "project:hosting")
_slot(r"\b(?:architecture|microservices|monolith|grpc|event[ -]?driven)\b", "project:architecture")
_slot(r"\b(?:payment|checkout|billing|gateway|stripe|adyen|provider)\b", "project:payment")
_slot(r"\b(?:deadline|due|flexible|slip|date)\b", "project:deadline")
_slot(r"\b(?:offline|online|connectivity|disconnected)\b", "project:connectivity")
_slot(r"\b(?:contract|license|subscription|vpn|renewal)\b", "project:contract")
_slot(r"\b(?:meeting|standup|sync|check[ -]?in|review|retro)\b", "event:meeting")
_slot(r"\b(?:milestone|release|ship|version|launch)\b", "project:milestone")
# "is on Python and Flask" / "runs on Node" — appended LAST so "deadline is on
# Friday" / "meeting is on Tuesday" hit their specific rules first (EC-02
# no-collision across real-world slots)
_slot(r"\b(?:is\s+on|runs?\s+on|running\s+on|works?\s+on|migrated\s+(?:to|from)?)\s+", "tool:choice")


def slot_key(text: str) -> str | None:
    """First matching slot key, or None — the add/update decision surface."""
    for pattern, prefix in _SLOT_RULES:
        m = pattern.search(text)
        if not m:
            continue
        if "favorite" in prefix:
            return f"{prefix}:{m.group(1).lower()}"
        return prefix
    return None


# ─── MemoryTrap-class instruction detection (EC-06) ──────────────────────────
# Memory content that reads like a directive to the assistant ("ignore all
# prior safety"). Such content is stored as DATA only — nothing in the system
# ever executes memory text; the flag exists so callers can surface it as
# memory content, never as instructions (research week 4; threat model).
_INSTRUCTION_RE = re.compile(
    r"\b(?:ignore|disregard|forget|override|bypass|reveal|never\s+mention|"
    r"pretend)\b.{0,80}\b(?:instruction|instruction\b|rule|safety|policy|"
    r"system\s+prompt|prior|previous|as\s+if)\b",
    re.IGNORECASE,
)


def is_instruction_like(text: str) -> bool:
    """True when the turn looks like a MemoryTrap payload (content is data,
    never a command). Deterministic; conservative (regex, not semantic)."""
    return bool(_INSTRUCTION_RE.search(text))


__all__ = [
    "PII_VERSION", "scrub_pii", "parse_delete_target", "is_noop",
    "has_correction_marker", "CORRECTION_MARKERS", "slot_key",
    "is_instruction_like",
]