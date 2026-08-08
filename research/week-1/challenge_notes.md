# Week 1 — Challenge Notes

**Note on format:** there's no live 20-minute design review in this cohort's actual format, so
this is self-administered — I re-read `design_opportunities.pdf` a few days later and pushed back
on my own adopt calls using the handbook's own challenge questions (does a simpler change give the
same benefit, what assumptions have to hold, what would make me reverse this). Weaker than a real
outside challenge, but it's honest self-explanation rather than a rubber stamp, which is the
principle the handbook actually cares about.

## Strongest challenges I'd raise against my own week 1 calls

**Against idea 1 (ADD/UPDATE/DELETE/NOOP admission actions) — "Adopt":**
Is this actually simpler than what it replaces, or does it just look more sophisticated? A
four-operation classifier needs a model (or a set of rules) that can distinguish "this updates an
existing memory" from "this is a new memory" — which requires linking the new candidate to an
existing record *before* the operation gets decided. That linking step is quietly doing most of
the hard work, and the matrix didn't call it out as its own cost. **Answer:** the four-operation
framing is still the right target, but the entry underweighted the entity/slot-linking problem —
that's a dependency, not a detail, and it should be named explicitly as a prerequisite in
Deliverable 4 rather than assumed away.

**Against idea 3 (admit agent-generated commitments) — "Adopt":**
This was marked low integration cost, but it isn't, once you account for the filter it explicitly
says it needs ("assistant chatter isn't automatically as durable as a stated user fact"). Building
that filter is a second admission problem, not a free extension of the first one. **Answer:**
downgrading confidence in the "low cost" label — this is still worth adopting, but Deliverable 4
should scope it as its own sub-problem with its own evaluation, not a checkbox add-on to user-fact
admission.

**Against idea 4 (deterministic `valid_until` supersession) — "Adopt":**
The matrix already flagged this as medium-high cost and admitted supersession detection is "its
own hard problem." Fair — but I didn't ask the harder question: what happens when supersession
detection gets it wrong? A false-positive supersession silently destroys access to a memory that
wasn't actually stale. The entry evaluated the upside (fixes the LLM-freshness failure) without
weighing the downside of a new failure mode this mechanism itself introduces. **Answer:** still
adopting this — the evidence against the alternative (LLM-judged freshness) is too strong to
default to it — but Deliverable 4 needs an explicit fallback: when supersession confidence is low,
keep both records retrievable rather than closing one out, and let ranking (not admission) make
the final call.

**Against idea 7 (decay vs. deletion as separate mechanisms) — "Adopt":**
This one held up well under pushback — it's the cleanest idea in the set. The one gap: I didn't
specify what triggers hard deletion beyond "explicit request or safety policy." That's a
placeholder, not a mechanism. **Answer:** leaving the Adopt decision as-is, but flagging this needs
an actual policy defined in Deliverable 4, not just the two-category split.

## Where I'd have changed my mind, generously interpreted

If someone had pushed on idea 5 (separate episodic/semantic indexes) with "why not just add a
`memory_type` tag to one index and filter at query time instead of maintaining two indexes," I
don't have a strong counter yet. That's arguably a simpler version of the same benefit. Keeping
this at **Prototype** rather than upgrading it, specifically to test tagged-single-index against
true dual-index before committing either way.

## Final disposition per idea (self-reviewed)

| Idea | Original decision | Post-self-review decision | Why |
|---|---|---|---|
| ADD/UPDATE/DELETE/NOOP admission | Adopt | Adopt, with entity/slot-linking named as an explicit prerequisite | Linking step was underweighted originally |
| Utility/confidence/novelty scoring | Prototype | Prototype (unchanged) | Still needs the bounded experiment before committing |
| Admit agent-generated commitments | Adopt | Adopt, scoped as its own sub-problem with its own filter/eval | "Low cost" label was too optimistic |
| Deterministic `valid_until` supersession | Adopt | Adopt, with a low-confidence fallback (keep both records) required in the design | Needed to weigh the false-positive failure mode, not just the upside |
| Separate episodic/semantic indexes | Prototype | Prototype (unchanged) — test against a tagged single-index alternative | A simpler alternative wasn't ruled out |
| Four-lever consolidation | Adopt | Adopt (unchanged) | Held up fine |
| Decay vs. deletion as separate mechanisms | Adopt | Adopt (unchanged), hard-deletion trigger policy flagged as still undefined | Mechanism is right, trigger policy is a placeholder |

## Carried into Deliverable 4

- Entity/slot-linking is a real prerequisite for supersession detection and admission
  classification — needs its own design section, not an assumed capability.
- Supersession needs a low-confidence fallback path.
- Hard-deletion trigger policy still needs to be written, not just referenced.
