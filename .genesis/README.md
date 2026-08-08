# .genesis — project spine (initialized)

This is the project's durable state for the **Genesis engineering workflow** (AI-native
loop-based development), laid down with the genesis-kit and adopted from the read-only
source repo during the 2026-08-08 merge.

**Status: initialized (spine present); no milestone started.** Zero build loops until the
design is stable (D4) — per the handbook, Genesis milestones run from Deliverable 5 forward.

- `DONE.html` — locked cognitive job, definition of done, plan
- `PLAN.md` — brainstorm (Approach B chosen: relational + pgvector, deterministic supersession) + M1–M3 with `pytest` demo commands
- `context-graph.json` — invariants (tenant isolation, deletion, <150ms retrieval, token budget, PII guardrails)
- `implementation-notes.html` — rolling "what is live" state
- `LOOPS.md` — the 5 loops (BUILD/DEBUG/RESEARCH/VERIFY/HEALTH) + 5 gates + G0
- `checkpoints/CURRENT.md`, `wiki/`, `decisions/` — running state
- `MAPPING.md` — handbook↔kit filename mapping
- `KICKOFF.md` — paste to resume a session cold

See `genesis.md` (the ritual) and `MAPPING.md`. Kit location on this machine:
`C:\Users\CR7\Desktop\genesis-kit`.