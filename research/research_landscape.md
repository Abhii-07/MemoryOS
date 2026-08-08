# Research Landscape

**Conversational Memory Intelligence System — running document, updated each week.**

This tracks which components have been scanned, what's been found so far, and where the open
gaps still are. It's not a literature review — it's a map of where I've looked and what's worth
looking at next.

## Component map

| Component | Status | Last scanned |
|---|---|---|
| Memory extraction & admission | Scanned | Week 1 |
| Ranking & conflict resolution | Scanned | Week 1 |
| Reflection & lifecycle (decay/consolidation) | Scanned | Week 1 |
| Retrieval augmentation | Scanned | Week 2 |
| Attention & context construction | Scanned | Week 2 |
| Index & storage layer | Scanned | Week 2 |
| Evaluation & observability | Scanned | Week 3 |
| Privacy, safety, isolation | Scanned | Week 4 |
| Memory model & representation | Not scanned — folded into Deliverable 4 directly | — |

## Note on how settled each component is

Weeks 1 (admission, ranking, lifecycle) are still active research questions. Weeks 2 and 3
(retrieval, context budgeting, storage/index, evaluation, observability) are largely converged
production practice. Week 4 (privacy/safety/isolation) is a mixed case worth calling out
specifically: the *mitigation frameworks* are settled (OWASP's 2026 ASI06 taxonomy, the regex+NER
detection pattern), but the *threats themselves* are extremely current — named attacks (MemoryGraft,
MINJA) and a real disclosed vulnerability against a shipping product (Cisco's MemoryTrap finding
against Claude Code, patched April-May 2026) all surfaced within the last few months. Treat week
4's findings as a floor for Deliverable 4's threat model, not a ceiling.

## Why week 4 got added, and why there's no week 5

Week 4 was added specifically because Deliverable 4 requires a `threat_model.md` as a required
artifact, and privacy/safety had only ever been scanned as a side effect of other components, never
directly. That's a concrete gate, not a general "more research is better" instinct — which is also
why weekly scanning stops here. Memory model/representation remains unscanned by design: Week 1's
admission work (typed records) and Week 2's episodic/semantic index split already cover most of
what that component would surface, so it gets folded directly into Deliverable 4's design instead
of getting its own week.

## Running list of names worth tracking

Mem0, Zep/Graphiti, MemGPT/Letta, Cognee, LangMem, MIRIX, A-MEM, Supermemory, vstash, Braintrust,
OpenObserve, OWASP ASI06, OpenAI Privacy Filter — these keep showing up across every component.
Worth returning to any of these as reference implementations once Deliverable 4 gets concrete,
rather than treating any single one as the architecture to copy wholesale.

See `week-1/` through `week-4/component_scan.md` for weekly detail and `design_backlog.md` for the
running list of candidate ideas and their disposition.
