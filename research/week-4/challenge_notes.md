# Week 4 — Challenge Notes

**Note on format:** self-administered, consistent with weeks 1-3 — no live review exists in this
cohort's actual format. Written the same way: re-read the design opportunities doc and pushed back
on the adopt calls rather than rubber-stamping them.

## Strongest challenges I'd raise against my own week 4 calls

**Against idea 1 (regex + NER PII detection) — "Adopt, pending validation on own data":**
I flagged the PIIBench OOD finding as a reason to validate before trusting a benchmark number, but
I didn't actually specify what "validation" means operationally. Without a concrete pass/fail bar,
"validate before trusting" is a nice sentence that's easy to skip under deadline pressure.
**Answer:** Deliverable 4 needs to state an actual minimum precision/recall bar on a project-specific
labeled set before any detector ships, not just a note that validation should happen someday.

**Against idea 2 (provenance tagging) — "Adopt":**
This was marked very low cost because it "rides on Week 1's admission framework." That's true for
storing the tag. It's not true for using it correctly everywhere downstream — ranking, consolidation,
and deletion all need to actually consult provenance, not just have it sitting in the schema unused.
A field nobody reads isn't a mitigation. **Answer:** still adopting, but Deliverable 4 needs to name
at least one concrete place provenance changes behavior (e.g., tool-derived memories get a shorter
default expiry than user-stated ones), or this risks becoming metadata for its own sake.

**Against idea 3 (deterministic tenant filtering) — "Adopt, amends Week 2":**
Worth checking: does hard-filtering by tenant before ranking cost anything in retrieval quality?
Filtering before scoring is fine algorithmically, but if the underlying index structure makes
pre-filtering expensive at scale (a real concern with some ANN index types), this could reintroduce
a latency problem Week 2 was trying to avoid. I didn't check this against Week 2's storage choice.
**Answer:** keeping the Adopt — correctness beats latency here, full stop — but flagging that
whichever vector index gets chosen in Deliverable 4 needs to be checked specifically for
efficient pre-filtered search, not just recall and cost in the generic case Week 2 evaluated.

**Against idea 5 (deletion propagation / backflow) — "Adopt as requirement, prototype mechanism":**
This is the one I was most tempted to soften into a vaguer "we'll consider lineage tracking
later." Is that reasonable given how hard it is? **Answer:** no — softening this would directly
contradict Deliverable 6's own acceptance check, which already requires deletion to actually work.
Keeping this as a hard requirement, not a stretch goal, even though it's the hardest unsolved
problem across all four research weeks. Better to flag it honestly now than discover it during
Deliverable 6's verification step.

## Where I'd have changed my mind, generously interpreted

If someone had pushed with "you're adding a 4th research week — where does this stop, why not a
5th week on some other angle" — that's a fair challenge to scope creep. **Answer:** this week was
justified by a specific gate (Deliverable 4 needs a `threat_model.md`, which had zero dedicated
research behind it), not by a general sense that "more research is better." That's a real
stopping rule, and it's the reason I'm not proposing a week 5.

## Final disposition per idea (self-reviewed)

| Idea | Original decision | Post-self-review decision | Why |
|---|---|---|---|
| Regex + NER PII detection, pre/post guardrails | Adopt, validate on own data | Adopt, with an explicit minimum precision/recall bar required before shipping | "Validate before trusting" needed a concrete bar, not just a good intention |
| Provenance tagging on every memory record | Adopt | Adopt, with at least one concrete behavior change required (e.g. expiry tied to provenance) | A stored-but-unused field isn't a real mitigation |
| Deterministic tenant filtering (pre-rank) | Adopt, amends Week 2 | Adopt (unchanged), flagged for a pre-filtered-search efficiency check against whatever index Deliverable 4 picks | Correctness over latency, but the interaction with index choice wasn't checked |
| Expire unverified memory | Adopt, folds into Week 1 decay lever | Adopt (unchanged) | Held up |
| Deletion propagation / backflow prevention | Adopt as requirement, prototype mechanism | Adopt (unchanged) — resisted the urge to soften this into a stretch goal | Directly required by Deliverable 6's existing acceptance check |
| Validate PII detector on project's own data | Adopt | Adopt (unchanged), now tied to the same explicit bar as idea 1 | Consistent with the above |

## Carried into Deliverable 4

- Define a concrete minimum precision/recall bar for the PII detector before it ships, not just
  "validate it."
- Provenance must change at least one real downstream behavior (ranking, expiry, or admission),
  not just exist as an unused field.
- Whichever vector index gets chosen needs an explicit check for efficient pre-filtered
  (tenant-first) search, not just the generic recall/cost comparison from Week 2.
- Deletion propagation (backflow prevention) stays a hard requirement in the threat model, not a
  stretch goal — directly tied to Deliverable 6's acceptance check.
