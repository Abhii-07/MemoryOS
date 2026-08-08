# Sources, Citation Map, and Evidence Discipline

> Claim tags used across `problem_reconstruction.pdf`,
> `historical_timeline.pdf`, `failure_analysis.md`, and `first_principles.md`:
>
> - `[P:n]` — **paper-supported**: the claim is stated in, or directly
>   follows from, the cited primary source below.
> - `[A: …]` — **assumption**: a clearly-labelled assumption to be validated
>   by the naive baseline (Deliverable 3) or a design experiment. Not claimed
>   as measured fact.
> - `[O]` — **observed in practice**: general engineering/industry practice,
>   not from a single paper.
>
> The handbook (section 12) requires that every claim be supported by papers,
> experiments, or clearly labelled assumptions; this file is the ledger that
> makes that discipline auditable.

---

## Primary sources (from the handbook, Appendix G and Section 2.3)

| ID | Citation | arXiv |
|---|---|---|
| [P:1] | A. Graves, G. Wayne, I. Danihelka. *Neural Turing Machines.* 2014. | 1410.5401 |
| [P:2] | S. Sukhbaatar, J. Weston, R. Fergus, et al. *End-To-End Memory Networks.* 2015. | 1503.08895 |
| [P:3] | J. Weston, S. Chopra, A. Bordes. *Memory Networks.* 2014. | 1410.3916 |
| [P:4] | A. Vaswani, N. Shazeer, N. Parmar, et al. *Attention Is All You Need.* 2017. | 1706.03762 |
| [P:5] | P. Lewis, E. Perez, A. Piktus, et al. *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.* 2020. | 2005.11401 |
| [P:6] | S. Borgeaud, A. Mensch, J. Hoffmann, et al. *Improving Language Models by Retrieving from Trillions of Tokens.* 2022. | 2112.04426 |
| [P:7] | Y. Wu, M. Rabe, D. Hutchins, C. Szegedy. *Memorizing Transformers.* 2022. | 2203.08913 |
| [P:8] | J. S. Park, J. C. O'Brien, C. J. Cai, et al. *Generative Agents: Interactive Simulacra of Human Behavior.* 2023. | 2304.03442 |
| [P:9] | C. Packer, S. Wooders, K. Lin, et al. *MemGPT: Towards LLMs as Operating Systems.* 2023. | 2310.08560 |
| [P:10] | J. Johnson, M. Douze, H. Jégou. *Billion-scale Similarity Search with GPUs.* 2017. | 1702.08734 |
| [P:11] | Y. A. Malkov, D. A. Yashunin. *Efficient and Robust Approximate Nearest Neighbor Search Using Hierarchical Navigable Small World Graphs.* 2018. | 1603.09320 |

## How claims map to sources

| Claim type (used in the reconstruction docs) | Source basis |
|---|---|
| Context window is finite; attention is bounded | [P:4] (structural property) |
| Stateless model calls cannot remember across calls | [P:1][P:2][P:3][P:4][P:9] |
| Replay scales cost with history; retrieval bounds context | [P:5] |
| Retrieval into the model's own memory | [P:6][P:7] |
| Retrieval-augmented pipeline framing | [P:5] |
| Lifecycle: memory consolidation and reflection | [P:8] |
| Memory hierarchy (main memory / paging) | [P:9] |
| Content-addressable external memory with read/write | [P:1][P:2][P:3] |
| Indexing/similarity-search substrate | [P:10][P:11] |
| Observed practice (`[O]`) | Oral table summaries, industry practice, embedded model limits |

All `[A: …]` assumptions are explicitly labelled in the body text and are
listed for the naive baseline (Deliverable 3) as hypotheses to measure.

## Statement of independence and AI-assistance disclosure

The problem reconstruction, historical chain, failure analysis, and
first-principles derivation follow the handbook's own method (section 3) and
use the handbook's prescribed starting papers. The author (student) is
responsible for every claim, citation, and assumption in this repository, in
accordance with handbook section 12 ("Working With AI Without Outsourcing
Judgment"). AI assistance was used to draft and iterate the structure and
wording; all scientific claims, evidence grading (`[P]`/`[A]`/`[O]`), and
design decisions were reviewed and owned by the student. Material AI
assistance and resulting decisions are recorded in the project journal
(`journal/`) and README.

*— Evidence discipline complete.*