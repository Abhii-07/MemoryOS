# Naive Baseline Protocol — Deliverable 3

> What was run, on what workload, with which fairness scoping. This protocol is
> written **before** interpreting results, so the baseline is honest about what
> it does and does not measure. Run date: 2026-08-08 (first execution of this
> workload; the code shipped with the source repo but had never been run).

## 1. What the baseline is

A deliberately naive conversational-memory layer, per the handbook's definition of "naive":

- **Store:** every incoming memory, flat list per user, no admission, no dedup, no consolidation, no decay. Isolation is enforced at query time by `user_id` filter only (application-layer isolation, no index-level or storage-level isolation) — the exact pattern Week 2's research flagged as a real risk.
- **Retrieval:** a single similarity signal — TF-IDF + cosine similarity, refit over each user's memory set per query. No recency, no importance, no contradiction handling.
- **Injection:** retrieved memories concatenated in similarity rank order up to a token budget; no per-zone budgeting, no ordering policy beyond rank.

## 2. Workload (defined before the run, no randomness)

Ten hand-written fixed cases (see `dataset.py`, fully reproducible without a seed), covering every category the handbook requires:

| # | Category | Cases |
|---|---|---|
| 1 | Irrelevant and contradictory memories | c1-irrelevant-noise, c1-direct-contradiction |
| 2 | Preferences that change over time | c2-payment-gateway-wording, c2-tech-stack-preference |
| 3 | Long conversations, constrained context budget | c3-long-history-budget (budget=40 tokens) |
| 4 | Multiple users, similarly worded information | c4-cross-user-similar-wording, c4-cross-user-similar-wording-b |
| 5 | Sensitive information that should not be retained | c5-sensitive-leak-check |
| 6 | Cold-start / no-relevant-memory | c6-cold-start-new-user, c6-no-relevant-memory-exists |

Ground truth is per-case: `correct_texts` (what should rank highest), `stale_texts` (what must not outrank the correct fact), `sensitive_texts` (must never surface), `expect_no_result` (cold start). Case c2-payment-gateway-wording and c2-tech-stack-preference are direct translations of Deliverable 1's personal `[O]` evidence into a measurable workload.

## 3. Fairness scoping — what this baseline is (and is not) allowed to show

- **TF-IDF as the similarity signal.** This environment has no network access to hosted embedding APIs or model hubs, so the baseline cannot use a neural embedder. TF-IDF is documented here as a *fair or slightly harsher* stand-in: D1's approach-4 failure (semantically-similar-but-differently-worded memories) applies to TF-IDF at least as much as to a neural embedding, so the failure story is not overstated by the choice. [A: lexical stand-in for semantic similarity]
- **What is measured.** Retrieval quality (recall@5, precision@1), contradiction/staleness handling, cold-start false positives, sensitive-content leakage (retrieval and injection), budget survival of the correct fact, latency (p50/p95, min-of-5 sampling), storage growth (byte proxy), prompt-token usage, and a minimal task-level proxy (would the injected context produce the *current* fact, not the stale one — no generation call; that is deferred to D6).
- **What is NOT measured (explicitly out of scope for D3).** Real generation quality, user satisfaction, cross-tenant leakage under adversarial construction (only the similar-wording case is present), decay/consolidation behavior (the baseline has none by design), and production-scale latency (this store is an in-memory list; latency here is an upper bound on what retrieval itself costs, not a system number).
- **Latency methodology.** Five timed runs per query; the **min** is reported. A single wall-clock measurement in a shared/virtualized sandbox is noisy (an early run of this exact code showed a multi-second scheduler spike). Min-of-5 is standard microbenchmark practice; this is disclosed rather than smoothed over. Latencies here are indicative, not a latency budget claim — the 150ms invariant applies to the *system* in D4/D6, not this in-memory probe.

## 4. Reproducibility

- No randomness in the workload; the full pipeline is `python run_baseline.py` in this directory.
- Re-run on 2026-08-08 produced identical summary numbers except timing fields (expected, per §3 methodology).
- Outputs committed with the run: `baseline_results.csv` (one row per case), `error_examples.jsonl` (failing cases with full context), `summary.json` (aggregate metrics).

## 5. Failure taxonomy used in the reports

| Failure class | Definition | Metric |
|---|---|---|
| Staleness wins | A superseded/stale text ranks above (or instead of) the correct current text | `stale_outranks_correct` |
| Sensitive leak | Sensitive text appears in retrieval output or injected context | leak rate (retrieval / injection) |
| Cold-start false positive | A no-relevant-memory case returns a spurious match | false-positive rate |
| Budget casualty | The correct fact exists in the store but is dropped during budget-limited injection | `correct_survived_budget` |
| Task-level failure | Injected context would drive a wrong downstream action (stale fact injected, correct absent) | `task_level_pass` |
