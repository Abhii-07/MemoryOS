# MemoryOS — Product Requirements Document (PRD)

> The product face of the same system the course documents describe. This is the
> "what & why" for a user; `design/edge_cases.md` and the D4 design are the "how".
> Tagged claims use the same discipline as deliverables: `[P:n]`, `[A: …]`, `[O]`.

---

## 1. Vision

**MemoryOS is an assistant memory layer that remembers what stays, forgets what
shouldn't, and always knows which version of the truth is current.**

The punishing experience the baseline measured (D3: contradiction failure 0.33,
100% sensitive-leak injection) becomes the market reality: models get better at
*responding*, but a user cannot trust an assistant that forgets a preference,
repeats a superseded decision, or surfaces a pasted password. MemoryOS is the
durable substrate between model and user.

## 2. Who it is for (personas)

| Persona | Pain (D1 §1, `[O]`) | What MemoryOS does for them |
|---|---|---|
| **The returning builder** — dev/design/ops hybrid | Re-stating project context after every break; contradictory suggestions | Persistent, ranked, supersession-aware project memory |
| **The caretaker (health / finance / family)** | Forgetting allergies, budgets, legal constraints = wrong actions | Correct-fact-wins retrieval with PII guardrails |
| **The organization** | Retention/deletion accountability; tenant isolation | Auditable, deletable, per-tenant-scoped memory |
| **The platform operator** | Cost/latency growth; one-tenant-leaks-into-another | Bounded budgets, tenant isolation gates, deterministic <150ms retrieval |

## 3. Product capabilities (R1–R8 → market terms)

| Capability (D1) | Product feature/contract | Acceptance (D6 shape) |
|---|---|---|
| R1 Admission | "Worth keeping?" classification at ingest; user sees *why* something was kept or dropped | admission logs surfaced; threshold tunable |
| R2 Representation | Memory records with type, when/where it came from, confidence | memory inspector displays fields |
| R3 Safe isolated storage + deletion | Hard delete request physically removes memory, no traces; per-tenant separation | deletion test: memory not retrievable after delete |
| R4 Multi-signal retrieval (RRF hybrid) | Hybrid search; preferences/purpose/fact typed ranking | LoCoMo-eval band: ≥68% LLM-judge accuracy (Mem0 parity) and ≥ recall@5 1.0 / precision@1 ≥0.85 on in-repo eval; 91%+ recall@10 hybrid figure is a practitioner benchmark (Supermemory hybrid-search guide, 2026-04) [O: verified in R2] |
| R5 Token-budget context | Zone-budgeted context (conversation / episodic / semantic) — never over budget | enforce; no overshoot |
| R6 Lifecycle | `ADD/UPDATE/DELETE/NOOP` per utterance; superseded via `valid_until`; decay | update invalidates old; decay policy on a schedule |
| R7 Observability | Decision traces: what was admitted/retrieved/injected and why | trace log inspectable per turn |
| R8 Reproducible eval | Fixed harness; metrics on memory quality | offline run reproducible |

## 4. User-facing memory controls (OQ9 from D1)

Derived directly from the open question the reconstruction left open — a user
must be able to:

- **Inspect** memories: searchable list of what MrOS holds about them.
- **Edit** a memory: correct it as if it were spoken again (UPDATE path).
- **Delete** one or a class of memories: synchronous, physical purge (invariant
  : delete).
- **Disable** memory entirely (opt-out, retention off).
- Understand *when* the system says no: cold-start fallback ("no memory about X
  "), never a fabricated match. [O: measured cold-start false-positive 0.5 in D3]

These map 1:1 onto D4's API surface described in the course docs (`put_memory`,
`delete_memory`, `update_memory`, `Retrieve`), which is intentional: product and
code share the same contract.

## 5. What MemoryOS is NOT (non-goals, keep explicit)

- Not a chat log / full-replay store (replay measured broken in D3: overflow & staleness).
- Not a graph RAG alone (research: graphs powerful but heavy for this product's scale [A]).
- Not a UI / deployment product for this course; UI/visit later (list of personas already makes the UX contract testable).
- No vector-only gradient; hybrid dense+sparse+RRF is the design [week-2 research].
- No anonymous tenant; tenant is a first-class isolation boundary.

## 6. Competitive context (from research weeks 1–4 [A: verify claims in R3])

| Market | Model | Angle that matters to MemoryOS |
|---|---|---|
| Mem0 | memory as API | strongest "admission+API" comparison; so does the memory editors' UX |
| Zep / Graphiti | temporal graph | "current truth" via graph edges |
| Letta (MemGPT) | memory paging | token-budget precedent (R5) |
| Supertune | per-user long-term memory | product-contract comparison |

MemoryOS wins on: deterministic supersession (no LLM-in-the-loop), DB-level
tenant isolation, and the *demonstrated* gap evidence in D3 (its competitor is
the status quo that the naive baseline describes).

## 7. Success criteria (product-level)

1. A returning user cannot observe a forgotten preference (D6 correct_action test).
2. Delete/disable is perceived as trusted (post-delete audit shows purge).
3. p95 retrieval < 150 ms on realistic corpus (invariant).
4. Sensitive content leak rate: 0.0 on the D3 workload after guardrails (D6 gate).
5. User can explain, in 30 seconds, why the assistant knows something (R7).

## 8. Milestone linking

Product milestones = Genesis milestones (`.genesis/PLAN.md` M1–M3) = D6
implementation milestones. Product documents don't create a separate plan;
`PRD.md` is the "why" and `.genesis/DONE.html` is the "what/when".