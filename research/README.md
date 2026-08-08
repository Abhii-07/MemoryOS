# MemoryOS — Research (Deliverable 2)

Four weeks of component scan notes for the **Conversational Memory Intelligence System**,
copied **verbatim** from the read-only source repo (bytes identical to source, verified
2026-08-08). These notes are the evidence base for Deliverable 2 (research) and the
justification inputs for Deliverable 4 (design).

## Layout

```
week-1/   admission · ranking · lifecycle (memory extraction, conflict resolution, reflection)
week-2/   retrieval augmentation · attention/context construction · index & storage
week-3/   evaluation · observability · benchmarks
week-4/   privacy · safety · isolation (OWASP ASI06, PII, memory-attack surface)
design_backlog.md      running candidate ideas + disposition (feeds D4)
research_landscape.md  component map, settled-vs-open status, names worth tracking
sources_catalog.md     INDEX of every tool/paper/attack referenced anywhere (this addition)
```

Each week has: `challenge_notes.md` (what the week set out to answer), `component_scan.md`
(full scan), `idea_evaluation_matrix.md` (ideas scored), and `design_opportunities.pdf`
(condensed visual handoff to design).

## Status of each component (as of end of research)

| Component | Status | Where |
|---|---|---|
| Memory extraction & admission | Scanned, active research | week-1 |
| Ranking & conflict resolution | Scanned, active research | week-1 |
| Reflection & lifecycle (decay/consolidation) | Scanned, active research | week-1 |
| Retrieval augmentation | Scanned, largely converged practice | week-2 |
| Attention & context construction | Scanned, largely converged practice | week-2 |
| Index & storage layer | Scanned, largely converged practice | week-2 |
| Evaluation & observability | Scanned, largely converged practice | week-3 |
| Privacy, safety, isolation | Scanned — threat landscape is current & named (MemoryGraft, MINJA, Cisco MemoryTrap) | week-4 |
| Memory model & representation | Not scanned by design — folded into D4 | (D4) |

## Verification passes (Phase 6) — done 2026-08-08

- [x] R1: every `sources_catalog.md` claim + `[P:n]` citation used in D1 verified (11/11; 2 claim-level edits) → `passes/2026-08-08-R1-citation-verification.md`
- [x] R2: D4-readiness rows — LoCoMo benchmark, Mem0 lifecycle, Letta (MemGPT) current state, Zep/Graphiti temporal edges, RRF recall numbers, pgvector/ANNS at scale → `passes/2026-08-08-R2-d4-readiness.md`
- [x] R3: product positioning vs Supermemory / Mem0 / Zep; API + retention story for the PRD → `passes/2026-08-08-R3-product-positioning.md`