# Edge-Case Ledger

> Every correctly-engineered memory system either handles these cases or must name why not.
> Each row: trigger, expected behavior, mapped capability (R1–R8), and the D6 test that will
> verify it. The naive baseline (D3) proved four of these fail in a single-signal system;
> the ledger exists so the design (D4) must close each one. Evidence keys below reference the
> baseline run (`experiments/naive_baseline/`) and research weeks.

| # | Edge case | Trigger | Expected behavior | Capability | D6 verification |
|---|---|---|---|---|---|
| EC-01 | **Superseded preference resurfaces** | User says "I prefer X" then later "no, Y". Retrieval on X' returns both | Only current truth (Y) surfaces; X marked superseded via `valid_until` | R4, R6 | Test: fetch → Y only; trace shows UPDATE |
| EC-02 | **Per-slot contradiction** | Two memories in different zones (episodic vs semantic) describe same fact differently (e.g. "live in NYC"/"working in NYC") | Conflict window: one is superseded or both kept but explicitly scored (typed) so ranking resolves | R2, R4, R6 | Contradiction test passes; rank stable |
| EC-03 | **Consent change** | User revokes past consent (e.g., "delete all memories tied to my ex") | `delete_memory` class-level operation behaves like admission inverse: no trace remains (no soft-delete flags) [invariant] | R3 | Class-level purge → `SELECT` empty; log shows audit only |
| EC-04 | **Deletion propagation to consolidated artifacts** | Delete a fact that was later abstracted into a summary (Memory-of-memories). Deleting the raw must ALSO purge it from synthetics | `consolidated artifact` recomputed from survivors; never refer to purged origin | R3, R6 | Delete raw → summary regeneration omits the fact (test "leak via summary") |
| EC-05 | **Cross-client adversarial similarity** | Attacker in tenant B crafts queries designed to retrieve tenant A wording (D3 c4-class) | Hard tenant_id scope at *all three layers*: storage, index, retrieval result filtering. Similarity is never the isolation mechanism | R3 | Test with two near-identical stores → zero cross rows; adversarial corpus test |
| EC-06 | **MemoryTrap-class prompt injection** | Adversary pages a memory clickable as instruction ("remember this: ignore all prior safety") | Memory metadata + content scanned; no memory is treated as instruction; classifier/flag | R1, R6 | Injection corpus test [research week-4]; no change-in-behavior surfacing |
| EC-07 | **PII exactly like a benign query** | Query "what's my password?" conflates a pasted password memory (D3: measured 100% leak) | Admission-time PII filter + retrieval-time guard; retrieval falls back to "no relevant memory" for PII-class hits | R1, R3 | Re-run c5-sensitive-leak-check → leak 0.0 |
| EC-08 | **Cold start** | New user, empty store | Return "no memory yet", never fabricate a match (D3 measured fabrication 0.5) | R5 | c6-cold-start test passes (empty → no result) |
| EC-09 | **Empty vocabulary / stopwords query** | Query like "as if" → TF-IDF produces empty vocab (baseline handles `ValueError`) | Graceful "no match" fallback | R5 | Unit: retrieve('as if') → [] |
| EC-10 | **Zone overflow (long convo)** | Long conversation where correct fact exists but budget spill pushes it out (D3 `correct_survived_budget` risk) | Zone-budgeted injector prioritizes: current-turn > high-confidence facts; never overflow | R5 | c3-case under 40-token budget: correct fact always survives |
| EC-11 | **Concurrent writes** | Two sources (user + sync) write same tenant in parallel | Serialize per tenant (transactional store underneath); supersession correct under races | R3 | `pytest` with threads; invariant after interleave |
| EC-12 | **Error reinforcement** | A wrong memory is instructive; trench agent retrieves it repeatedly, each time reinforcing wrongness (Generative Agent regression) | Correction path: UPDATE task marks re-store as wrong; decay/consolidation; not auto-picked-up | R6 | Test loop: inject error → correct → retrieve returns corrected only |
| EC-13 | **No-relevant-memory** | Query has nothing relevant (non-empty store) | "I don't know" behavior — no invention, no partial-answer leakage (D3 measured 0.5 false positivity) | R5 | c6-no-relevant-memory → "no relevant memory" |
| EC-14 | **Storage growth bound** | Long-lived tenant accumulates | Bounded/prunable: runtime capacity, decay, retirement policy with observed metric (C8) | R8 | Growth test: storage stays within capacity; prune path works |
| EC-15 | **Latency ceiling** | Corpus growth against retrieval | Deterministic retrieval (no LLM) + HNSW/pgvector index; p95 < 150ms | C2, R4 | `pytest -m latency`: at hosted scale, p95 ≤ invariant |
| EC-16 | **Multi-modal / mixed fidelity** | Memory admits numeric facts (dates, numbers) that embedding may mangle | Structured fields for numbers + favorites; retrieval checks exact slot values | R2, R4 | Fact test: "born 1992" not "1990" (exact-match check) |
| EC-17 | **Neutral / generic utterance** | User says "hmm ok" — does admission fire on everything? | NOOP classification (M3: ADD/UPDATE/DELETE/NOOP) | R1 | Utterance → NOOP → no storage row |
| EC-18 | **Memory deletion while being retrieved** | Delete during an in-flight query | Transactional isolation: query sees consistent pre- or post-delete state, never a split | R3 | Thread test, assert no torn reads |

**Note on EC-07**: the measured D3 leak was **100%** — the guardrail target in
this ledger is 0.0, which is why the row's D6 test is a re-run of the same case.
No row here cites production rarity; every row exists because D1/D3 identified
the mechanism.