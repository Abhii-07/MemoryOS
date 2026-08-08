# ADR-006: TF-IDF Substitution for Deliverable 3's Baseline Retrieval Signal

**Status:** accepted — scoped to Deliverable 3 only, not the production design
**Date:** July 2026

## Context

Deliverable 3 required a naive baseline using "one similarity signal" for retrieval. The intended
signal, consistent with the rest of this project's research (Week 2's hybrid retrieval work),
would ordinarily be a dense neural embedding. The sandboxed environment used to build the baseline
had no network access to a hosted embedding API or a model hub.

## Decision Drivers

- The naive baseline needed to be genuinely runnable and reproducible without external
  dependencies, per the handbook's requirement for a fixed, reproducible workload.
- The substitution needed to not undermine what Deliverable 3 was actually trying to measure —
  the structural failures (contradiction handling, sensitivity filtering, relevance-floor absence)
  that don't depend on embedding quality.

## Options Considered

1. **Skip the baseline's retrieval step, or use a placeholder that always returns fixed results.**
   Rejected — would not produce genuine measurements, defeating the purpose of a productive
   failure baseline entirely.
2. **TF-IDF + cosine similarity as the single similarity signal.** Chosen.
3. **Attempt to route around the network restriction** (e.g. via an allowed domain). Rejected —
   no allowed domain in this environment provides embedding generation, and attempting to disguise
   traffic to reach one would violate the environment's intended constraints rather than legitimately
   work within them.

## Decision

Option 2. `experiments/baseline_protocol.md` documents this substitution explicitly, along with the
reasoning that TF-IDF is, if anything, a harsher test of the semantic-similarity failure mode
Deliverable 1 originally flagged (paraphrased queries), since TF-IDF has no ability to generalize
beyond shared vocabulary at all, where a neural embedding sometimes can.

## Consequences and Trade-offs

Findings from the baseline that show up as pure *retrieval* misses (a paraphrased query failing to
match) may be somewhat worse under TF-IDF than they would be under a neural embedding. Findings
that show up as *ranking or judgment* failures — contradiction handling, sensitivity filtering,
the missing relevance floor — are unaffected by this substitution, since none of those depend on
the quality of the underlying similarity signal. All three of Deliverable 3's headline failures
fall into this second category, so the substitution does not undermine the baseline's core
findings.

## Validation Plan

N/A retroactively — Deliverable 3 is complete and its results stand as measured. This decision's
scope is explicitly limited to that baseline; `system_design.pdf`'s production design assumes a
real dense embedding service (Part 1, Section 4's first assumption), not TF-IDF.

## Revisit Conditions

None — this ADR documents a completed, scoped decision for a specific deliverable, not an ongoing
architectural choice.
