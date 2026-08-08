# Week 3 — Challenge Notes

**Note on format:** self-administered, same reasoning as weeks 1 and 2 — no live review exists in
this cohort's actual format.

## Strongest challenges I'd raise against my own week 3 calls

**Against idea 1/2 (recall/precision/latency/tokens + contradiction-staleness rate) — "Adopt":**
The matrix presents these as the settled metric set, but "settled across benchmarks" and "right
for this project" aren't automatically the same thing. LoCoMo and friends were built to compare
memory *systems* against each other in the abstract — this project's actual success criterion,
per Deliverable 1's importance section, is closer to "does re-establishing context stop being a
tax on the user." Recall/precision don't directly measure that; they measure a proxy for it.
**Answer:** keeping these as the core metrics — they're still necessary and the field consensus is
real — but Deliverable 6's evaluation should explicitly connect recall/precision numbers back to
the user-facing outcomes from Deliverable 1 (fewer re-explanations, no contradicted decisions)
rather than treating a good recall score as self-evidently the goal.

**Against idea 3 (defer task-level evaluation to Deliverable 6) — "Adopt for D6, defer now":**
This is the call I was most tempted to soften, and it's worth being honest about why: it's
genuinely the harder thing to build, and "defer the hard thing" is always a comfortable decision
to reach for. Is there a cheaper partial version I dismissed too quickly? **Answer:** on
reflection, a lightweight version is actually feasible now — not a full MemoryArena-style
multi-step task suite, but 3-5 hand-written scenarios from Deliverable 1's own failure evidence
(the "contradictory suggestions" and "repeated preference specification" examples) turned into
simple pass/fail checks: does the system's actual output act on the retrieved memory correctly.
**Revising the decision**: build a minimal task-level check in Deliverable 3 alongside the
recall/precision numbers, not a full deferral to Deliverable 6.

**Against idea 5 (OpenTelemetry GenAI spans) — "Adopt":**
Marked low cost with "auto-instrumentation exists for most common frameworks" — but this project
isn't using one of the well-supported frameworks yet (no framework has even been chosen —
that's a Deliverable 4 decision). The low-cost claim assumes a framework choice that hasn't been
made. **Answer:** keeping the Adopt on OTEL as the tracing standard — that decision doesn't depend
on framework choice — but removing the "low cost" assumption until Deliverable 4 picks a stack;
cost should be re-assessed once that's known, since manual instrumentation is real work if no
auto-instrumentor exists for whatever gets chosen.

**Against idea 6 (memory content in span events, not attributes) — "Adopt":**
This is a strong default, but "events can be filtered/dropped at the collector level" quietly
assumes the collector is configured correctly and stays that way. The entry called this a "strong
default, not an absolute guarantee" — which I wrote at the time but then treated as adopted
without qualification in the summary. **Answer:** keeping the Adopt, but this needs to show up in
Deliverable 4's threat model explicitly (collector misconfiguration as a privacy risk), not just
live as a footnote in a research doc that won't get read again.

## Where I'd have changed my mind, generously interpreted

If someone had pushed on "why is task-level evaluation deferred at all if it's this important" —
that's exactly the challenge that led to revising idea 3 above. Good challenges should occasionally
change a decision, not just add caveats to it. This is the one that actually did.

## Final disposition per idea (self-reviewed)

| Idea | Original decision | Post-self-review decision | Why |
|---|---|---|---|
| Recall/precision/latency/tokens as core metrics | Adopt | Adopt (unchanged), must be tied back to Deliverable 1's user-facing outcomes in D6 reporting | Good proxy metrics, but proxies need to stay connected to the real goal |
| Contradiction/staleness rate as 5th metric | Adopt | Adopt (unchanged) | Held up |
| Task-level evaluation | Adopt for D6, defer now | **Revised: build a minimal 3-5 scenario task-level check in Deliverable 3**, full suite still in D6 | A cheap partial version was dismissed too quickly on first pass |
| No LLM-as-judge for freshness | Adopt | Adopt (unchanged) | Directly follows Week 1 evidence, held up fine |
| OpenTelemetry GenAI spans | Adopt | Adopt (unchanged), "low cost" label removed until D4 picks a framework | Cost claim assumed a framework decision that hasn't happened yet |
| Memory content in span events, not attributes | Adopt | Adopt (unchanged), collector misconfiguration must appear in D4's threat model | Was already flagged as "not an absolute guarantee" but not carried through |
| Tail-based sampling | Adopt | Adopt (unchanged) | Not urgent at MVP scale, no real challenge surfaced |

## Carried into Deliverable 4

- Build a minimal task-level evaluation check in Deliverable 3, not a full deferral to
  Deliverable 6.
- Recall/precision reporting should be explicitly tied back to Deliverable 1's user-facing
  success criteria, not treated as the goal itself.
- OTEL instrumentation cost is unknown until a framework is chosen — revisit then.
- Collector misconfiguration needs to be in the threat model, not just a caveat in this file.
