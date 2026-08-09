# ADR-008: Deterministic Entity/Slot-Linking for Admission (MVP)

**Status:** accepted
**Date:** 2026-08-08 (required before G-M3 by `design/sprint_plan.md`, risk watch #2)

## Context

`sprint_plan.md` (risk watch #2) and `system_design_part3.md` §16 both name
entity/slot-linking as a load-bearing prerequisite for the ADD/UPDATE/DELETE/
NOOP classification and for deterministic supersession — and the original D4
left it as "still no detailed design of its own." G-M3 cannot start without
this decision record.

The constraint that shapes everything: **no LLM on the write path** (D3
failure-proofing; Week 1's adopted mechanism; the design's "no LLM on the
request path" invariant). Classification, linking, and supersession must all be
deterministic, reproducible, and unit-testable — same input, same verdict, on
any machine (R8).

## Decision Drivers

- Determinism: identical turns must classify identically on every run and
  machine (R8 reproducibility; the "same-team same-test" gate).
- No LLM/API on the write path; no network; tests must never need a model.
- Supersession correctness: a *correction* turn must deterministically resume
  the prior active memory for the same entity+slot and write `valid_until`.
- Tenant-safe: linking and supersession are always scoped by `tenant_id` and
  `user_id` (G-M1 invariant; never by similarity across users).

## Options Considered

1. **LLM/NER entity linking.** Rejected: violates the no-LLM invariant, needs
   network, non-deterministic across versions, cannot be gated by a pytest.
2. **Heavy NLP (spaCy/Stanford NER).** Rejected for MVP: new deps, model
   download burden, overkill for the conversation shapes the workload
   specifies (D3 dataset has a bounded grammar of preference/fact utterances).
3. **Deterministic pattern slots (chosen).** A small, explicit grammar of
   slot signatures ("favorite <X>", "uses <X>", "deadline", "hosting",
   …) extracts a `slot_key` per turn, and turns that carry a *correction
   marker* ("no", "actually", "instead", "switched", "no longer", "changed")
   resume the prior active row sharing that same slot key on the same
   tenant+user. Everything is a pure function of text; frozen by tests.

## Decision

G-M3's admission implements:

- `ADMISSION_OPS = ADD | UPDATE | DELETE | NOOP`.
- Classification table (deterministic regex priority): PII scrub → DELETE
  target parsing → NOOP utterances (greetings/filler/stopword-only) →
  UPDATE (correction marker + existing slot) → ADD otherwise.
- Entity/slot linking: `links.py` exposes `slot_key(text) -> str | None`
  (e.g. `preference:database`, `project:deadline`); UPDATE supersession asks
  retrieval for the active candidate set of the same tenant+user, binds on
  shared slot_key plus the relevance floor, and superposes via `valid_until`
  — the design's chosen mechanical supersession (Week 1, ADR-002, attributed
  in `store.supersede`).

## Consequences and Trade-offs

- The grammar is a bounded subset of English; anything outside the patterns
  falls through to ADD (never a crash, never an LLM). EC-17's "hmm ok" →
  NOOP; EC-09 stopword-only ("as if") → NOOP.
- EC-12 (error reinforcement) is closed by the same UPDATE path: a correction
  turn supersedes the wrong row, and retrieval subsequently returns the
  corrected row only — the wrong one is deterministically out of
  the candidate set.
- The grammar lives in one module (`memory_os/admission/patterns.py`) and
  every signature is covered by a fixture-level test, so extending the
  grammar (new slot shapes, i18n) is a code+test change, no design change.
- Trade-offs: utterances needing real-world disambiguation (metonyms,
  coreference across turns without surface ties) do not get linked. No
  ranking-simulation burden: the system falls back to ADD; correctness of
  retrieval (not classification) carries those — the disclosure here is the
  limit of the MVP grammar, matching part1 §5's own bounded-MVP posture.

## Revisit Conditions

- If a measured share of turns needing UPDATE never gets linked (e.g. domain
  entities shipped to more than the bounded test grammar), revisit private
  (NLP or bootstrap LLM only on a *write* (never read) path) per a new ADR.
- If the D3 stress corpus grows new slot shapes, extend the slot table in
  `patterns.py` + frozen tests (no ADR change needed).