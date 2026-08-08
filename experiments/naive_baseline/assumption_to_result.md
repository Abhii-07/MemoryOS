# Assumption → Result Map — Deliverable 3

> Every `[A: …]` assumption tagged in the Deliverable 1 reconstruction, mapped to the
> naive baseline's measured result. Status: CONFIRMED (failure reproduced), PARTIALLY
> OBSERVED (workload limitation), or NOT TESTED (explicitly deferred to D4/D6).
> Source of truth for results: `summary.json` (committed with this run, 2026-08-08).

## D1 → D3 assumption map

| D1 assumption tag | Capability | Naive code path | Measured result | Verdict |
|---|---|---|---|---|
| `[A: recency vs relevance vs importance weighting]` | R4 | TF-IDF cosine only; no recency/importance | contradiction_failure_rate = **0.33** (1 of 3 contradiction cases injected the stale fact); task_level_pass_rate = **0.67** | **CONFIRMED** — without multi-signal ranking, current truth loses a third of the time |
| `[A: supersession handling]` | R4/R6 | No supersession; stale texts rank by similarity alone | stale text outranked correct in c1-direct-contradiction (top1 was "deadline is flexible") | **CONFIRMED** |
| `[A: single-signal ranking failures]` | R4 | TF-IDF only | precision@1 = **0.857**; cold_start_false_positive_rate = **0.5** (c6-no-relevant returns taco place for a testing-framework query) | **CONFIRMED** |
| `[A: PII admission + isolation tests]` | R1/R3 | No admission filter; store flag unused by system; query-time user_id filter only | sensitive_leak_rate_retrieval = **1.0**, sensitive_leak_rate_injection = **1.0** (both sensitive memories surfaced, incl. a database password, on a hosting-provider query) | **CONFIRMED** — leak is total, not partial |
| `[A: token-budget discipline]` | R5 | Greedy rank-ordered inject, budget truncation | correct_survived_budget = true in c3 (correct fact survived 40-token budget); avg_tokens_used = **29.2** | **PARTIALLY OBSERVED** — budget holds but ordering is naive; see c3 note |
| `[A: decay policy]` | R6 | No decay by design | N/A (absence is the design) — staleness observed via contradiction rate | **UNTESTED by design** (D6) |
| `[A: error reinforcement]` | R6 | No correction loop | Not modeled; correction loop absent | **UNTESTED** (D4/D6, MemoryTrap-class) |
| `[A: cold start / no-relevant]` | R5 | Similarity floor = any nonzero cosine | c6-cold-start-new-user OK; c6-no-relevant-memory-exists **false positive** (spurious match) | **CONFIRMED** — no-relevant cases fabricate a match |
| `[A: lexical stand-in for semantic]` (protocol §3) | R4 | TF-IDF instead of embedder | Fine: lexical-only misses paraphrase equivalence (see c2-payment wording English vs Adyen split — retrieved because of 'checkout integration' overlap, but contradiction case as tested) | **LIMITATION DISCLOSED** — do not over-read |

## Cross-checks for the falsification argument

- **Precision ≠ correctness.** precision@1 = 0.857 looks decent, yet contradiction (stale wins) and leak rates prove the "plausible-but-wrong" failure mode (D1 A4) is *not* explained by raw similarity quality. Recall@5 = 1.0 shows: the naive system *finds* the right text; the design problem is selection, freshness, and governance — exactly R1/R4/R5/R6, not R8.
- **Task-level proxy**: task_level_pass_rate = 0.67 — an assistant acting only on injected context would act on the *wrong fact* in 1 of 3 contradiction-style turns.

## Open items for D4/D6 (not falsifiable in D3)

1. Cross-tenant leakage under adversarial construction (only similar-wording probed).
2. Generation-level correction of a wrong memory (deferred; proxy used in D3).
3. Decay/consolidation behavior (no lifecycle in baseline by definition).
4. Latency at production scale (in-memory probe is informative only).

## Fallible claim left open

- [A: admission accuracy/threshold] — the baseline *has* no admission; the cost of a policy is only implied, not measured. D4 design + D6 eval must measure admission false-positive/negative rates on this same workload.