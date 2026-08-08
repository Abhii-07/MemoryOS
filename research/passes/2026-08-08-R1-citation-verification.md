# Research Pass R1 — Citation Verification (2026-08-08)

> Goal: every `[P:n]` used in the reconstruction is a real, correctly-attributed paper;
> every claim-level usage is actually supported by the cited source. Method: arXiv
> abstract/full-text cross-checks performed 2026-08-08 (web, current). Outcome: 11/11
> citations verified; **2 claim-level issues found and corrected** (see Actions below).

## Citation table

| P-ID | Verdict | Note |
|---|---|---|
| P:1 Neural Turing Machines (1410.5401) | CORRECT | Graves, Wayne, Danihelka, 2014 |
| P:2 End-To-End Memory Networks (1503.08895) | CORRECT | Sukhbaatar, Szlam, Weston, Fergus, 2015 ("et al." covers the omitted 3rd author) |
| P:3 Memory Networks (1410.3916) | CORRECT | Weston, Chopra, Bordes, 2014 |
| P:4 Attention Is All You Need (1706.03762) | CORRECT | Vaswani et al., 2017 |
| P:5 RAG (2005.11401) | CORRECT | Lewis et al., 2020 |
| P:6 RETRO (2112.04426) | CORRECT | Borgeaud et al., 2022 |
| P:7 Memorizing Transformers (2203.08913) | CORRECT | Wu, Rabe, Hutchins, Szegedy, 2022 |
| P:8 Generative Agents (2304.03442) | CORRECT | Park et al., 2023 |
| P:9 MemGPT (2310.08560) | CORRECT | Packer et al., 2023 |
| P:10 FAISS (1702.08734) | CORRECT | Johnson, Douze, Jégou, 2017 |
| P:11 HNSW (1603.09320) | CORRECT (year nuance) | arXiv v1 = 2016; TPAMI published 2018 → cite "2016 (TPAMI 2018)" |

## Claim-level verdicts

1. **[P:4] "context window finite; attention bounded" — SUPPORTED as structural inference.** The paper does not state it as a thesis, but self-attention over the fixed input length is a structural property of the architecture. Framing note added to sources.md.
2. **[P:5] "retrieval exists because context is constrained; replay scales cost" — NOT SUPPORTED as attributed.** RAG itself motivates retrieval by parametric-memory limits, not a finite window. (Impacted doc text: 01_problem §5 "Long-context replay" bullet citing [P:4][P:5]; 02_timeline Stage 1 bullet citing [P:5] for "Token cost and latency grow linearly with history".) **Action: D1 docs keep rationale but re-anchor to [P:4] (window bound) + [O] (observed cost growth); the ~40%-claims are dropped from the attribution.**
3. **The "~40% of dense queries fail" number is NOT in the RAG paper.** Its true origin is the practitioner hybrid-search literature (2025–26 blogs, e.g. supermemory.ai hybrid-search guide; "the 40% bug" (lushbinary); turion.ai). **Action: dropped from project claims; if reused, cite practitioner origin explicitly as `[O] practitioner-benchmark` and verify in R2.**
4. **[P:8] — PARTIALLY SUPPORTED.** observation→reflection→planning + retrieval is genuine; **"consolidation" is not Generative Agents' terminology and "error reinforcement" is not a concern they raise** (their failure modes: retrieval misses, hallucinated embellished memories, memory hacking, §8.3). Correct attribution for error-reinforcement: subsequent literature (Reflexion, BeliefMem). **Action: D1 tone edited — "consolidation" replaced by "reflection/summarization pipeline"; "error reinforcement" re-framed as recognised-follow-on concern ([P]+[A], not presented as paper claim).**
5. **[P:9] MemGPT — SUPPORTED.** Main/external memory, paging vs token budget, interrupts — core contributions.
6. **[P:6][P:7] RETRO/Memorizing Transformers — SUPPORTED.** Retrieval integrated into model memory; internal KV-memory lookup.

## Actions taken (file edits, 2026-08-08)

1. `reconstruction/sources.md` — P:11 note "(arXiv 2016 / TPAMI 2018)"; claim table reworded: P:4 claim is "structural property implied by the architecture"; P:5 claim limited to grounding generation in corpora; added explicit "[O] practitioner" row for hybrid-recall numbers; removed any wording that implies the 40% figure is paper-backed.
2. `reconstruction/01_problem.md` + `03_failure_analysis.md` — the "error reinforcement" and "consolidation" phrasing re-anchored per verdict 3–4 above (kept as `[A]`/observed rather than P-attributed).

## R1 verdict

READY (issues found and corrected). No uncited claim remains; every `[P:n]` in D1 resolves to a verified paper; P:-tags in `sources.md` statement-of-independence remain accurate for the docs as merged.

## Follow-up (R2)

- LoCoMo: benchmark details + SOTA numbers per pass R2.
- 91% recall@10 hybrid figure attribution: Supermemory blog (Apr 2026), not "Improving Context" — re-checked in R2.
- pgvector scale numbers sanity-checked in R2 pass.