# Week 2 — Challenge Notes

**Note on format:** self-administered, same reasoning as week 1 — no live review exists in this
cohort's actual format, so this is me re-reading `design_opportunities.pdf` and pushing back on my
own calls rather than leaving the template blank.

## Strongest challenges I'd raise against my own week 2 calls

**Against idea 1 (hybrid retrieval: BM25 + dense + RRF) — "Adopt":**
The 91% recall@10 and 40%-of-queries-fail-on-vector-alone numbers came from production write-ups,
not from anything I measured myself on this project's actual data. Week 2 treated these numbers as
close to settled fact. They're a reasonable prior, not proof this system will see the same
failure rate — this project's queries (preferences, project decisions) may skew differently than
generic RAG corpora the sources were drawn from. **Answer:** keeping the Adopt — the mechanism
costs little to include and hybrid retrieval is very unlikely to be *worse* than vector-only — but
Deliverable 3's baseline should actually measure the vector-only failure rate on this project's
own conversation set instead of assuming the cited 40% transfers directly.

**Against idea 3 (no LLM call at retrieval time) — "Adopt":**
This one leans hard on Week 1's admission/ranking work already being good enough to not need an
LLM safety net at retrieval time. That's an assumption stacked on top of ideas that were
themselves only rated "Prototype" or carry an unresolved false-positive risk (see week-1 challenge
notes on supersession). If admission or supersession makes a mistake, "no LLM check at retrieval"
means nothing catches it before the user sees it. **Answer:** still adopting — the cost/latency
case for keeping the LLM out of the hot path is strong — but this raises the stakes on getting
Week 1's admission and supersession fallback right, since retrieval isn't a second line of
defense the way it might be in a system that does check with an LLM. Worth flagging explicitly as
a dependency in Deliverable 4, not treating the two ideas as independent.

**Against idea 4/5 (per-zone token budgets, tool-output as its own zone) — "Adopt":**
Both were rated low cost as "mostly a policy/monitoring change." That's true for the budgeting
policy itself, but building the *monitoring* — actually tracking token counts per zone in real
time and alerting when a zone is near its ceiling — is real infrastructure, not a config file.
**Answer:** keeping both as Adopt, but downgrading "low cost" to "low design cost, medium
implementation cost" — the policy is simple, the instrumentation to enforce it isn't free.

**Against idea 7 (pgvector for MVP) — "Adopt":**
This was the most confident call of the week, and confident calls are exactly the ones worth
re-checking. The near-unanimous recommendation was for generic RAG workloads at this scale — I
didn't check whether any source specifically addressed a workload with frequent updates/deletes
(this system does a lot of both, per Week 1's decay/deletion work), which stresses an index
differently than a mostly-append-only RAG corpus. **Answer:** keeping the Adopt for MVP — it's
still clearly the right starting point — but noting this needs re-validation once update/delete
volume is actually measured in Deliverable 6, rather than treating "pgvector is fine" as settled
for this system's specific access pattern.

## Where I'd have changed my mind, generously interpreted

If someone had pushed on idea 2 (reranking, marked "Defer") with "you're deferring a technique
every source says genuinely helps, just because it's trendy to defer it" — that's a fair
challenge to the *reasoning*, even if the conclusion is right. Re-checked: the actual justification
holds (measure fusion first, add reranking only if there's a demonstrated gap), so I'm not
reversing the decision, but the original write-up leaned a little on "everyone reaches for this
too fast" as if that alone were the argument. The real argument is simpler: no measured need yet.

## Final disposition per idea (self-reviewed)

| Idea | Original decision | Post-self-review decision | Why |
|---|---|---|---|
| Hybrid retrieval (BM25 + dense + RRF) | Adopt | Adopt (unchanged), validate the failure-rate assumption against this project's own data in D3 | Cited numbers are a prior, not measured fact for this system |
| Cross-encoder / ColBERT reranking | Defer | Defer (unchanged), reasoning tightened to "no measured need yet" | Original justification partly leaned on "overused elsewhere" rather than project evidence |
| No LLM call at retrieval time | Adopt | Adopt (unchanged), flagged as dependent on Week 1's admission/supersession quality | Retrieval isn't a safety net if admission gets something wrong |
| Per-zone token budgets + tool-output zone | Adopt | Adopt (unchanged), cost re-labeled low design / medium implementation | Monitoring infrastructure isn't free even if the policy is simple |
| Context rot as design constraint | Adopt | Adopt (unchanged) | Held up — no real counter-argument found |
| pgvector for MVP | Adopt | Adopt (unchanged), flagged for re-validation once update/delete volume is measured | Cited recommendations may not cover this system's write-heavy access pattern |
| Namespace isolation now, physical as upgrade path | Adopt | Adopt (unchanged) | Held up — trigger condition was already explicit |

## Carried into Deliverable 4

- Measure vector-only retrieval failure rate on this project's own data before trusting the
  cited 40% figure.
- Retrieval's "no LLM call" design depends on admission/supersession being reliable — document
  this dependency explicitly rather than treating components as independent.
- Token-budget monitoring is real implementation work, not just a policy doc.
- Re-check pgvector's fit once real update/delete volume exists, not just read volume.
