# Genesis filename mapping — kit canonical vs. handbook required

The AI Engineering Handbook (ProgramAI Engineering Cohort) mandates the following
`.genesis/` artifact names in Deliverable 5:

| Handbook required name | Genesis-kit canonical name (this repo) | Notes |
|---|---|---|
| `.genesis/done.html` | `.genesis/DONE.html` | Same file; handbook name lower-case |
| `.genesis/plan.md` | `.genesis/PLAN.md` | Same file; handbook name lower-case |
| `.genesis/implementation_notes.html` | `.genesis/implementation-notes.html` | Same file; underscore vs. hyphen |
| `.genesis/context_graph/` | `.genesis/context-graph.json` | Single JSON file vs. directory |
| `.genesis/loops/` | `.genesis/LOOPS.md` | Single Markdown file vs. directory |
| `.genesis/checkpoints/` | `.genesis/checkpoints/` | Match |
| `.genesis/wiki/` | `.genesis/wiki/` | Match |
| `.genesis/decisions/` | `.genesis/decisions/` | Match |

We use the genesis-kit canonical names as the single source of truth so the kit's
tooling (`scaffold.sh`, `graphizer.mjs`, the loops) works unmodified. The handbook
permits instructor-approved equivalent formats; if the instructor requires the exact
handbook filenames, add thin pointer files (`done.html`, `plan.md`,
`implementation_notes.html`, plus `context_graph/` and `loops/` directories) that
reference the canonical files above. Do not maintain two divergent copies.

Additional kit files beyond the handbook list (present for tooling):
`genesis.md` (the G0–G6 ritual), `KICKOFF.md` (cold-session resume prompt),
`KICKOFF-INTERVIEW.md` (pre-ritual interview), `AGENT-ADAPTERS.md` (per-agent
invocation mapping).

**Origin.** This spine was adopted from the read-only source repo (initialized 2026-07),
then re-sliced at merge (2026-08-08): milestones M1–M3 now point at `pytest` demo commands
and `src/memory_os/**` per the Python stack decision (D-002); two invariants were added
(`token_budget_per_turn`, `pii_pre_post_guardrail`) on top of the original three.