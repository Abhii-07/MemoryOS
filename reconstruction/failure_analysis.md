# Failure Analysis — Prior and Simpler Approaches, Their Assumptions, and Their Failure Cases

> Deliverable 1, Part 3. Five approaches that predate or approximate a
> conversational memory layer. For each: **assumptions**, a **concrete
> failure case**, and the **constraints it violates**. This is the evidence
> base for `first_principles.md`: every required capability below is derived
> from at least one failure here.
>
> Claim tags: `[P:n]` paper-supported (see `sources.md`); `[A: …]` assumption
> to be validated by the naive baseline (Deliverable 3); `[O]` observed in
> practice. Constraints C1–C8 are defined in `01_problem.md` §3.

---

## Summary of approaches

| # | Approach | Central assumption | Where it fails | Constraints violated |
|---|---|---|---|---|
| A1 | Stateless per-turn call | Each turn is self-contained | No continuity across calls/sessions | C4, C5, C6 (by omission) |
| A2 | Full-conversation replay | History fits; all of it relevant | Overflow, stale pollution, cost | C1, C2, C3, C4 |
| A3 | Keyword / symbolic lookup | Literal match approximates relevance | Paraphrase misses; false positives; no lifecycle | C4, C8 |
| A4 | Naive dense retrieval over raw transcript | Store everything; similarity is sufficient | No admission, ranking, lifecycle, or isolation | C1 (by quality), C4, C5, C6, C8 |
| A5 | Prompt-level instruction ("remember this") | A prompt statement persists | Nothing durable | C4, C5, C6 (by omission) |

---

## A1 — Stateless per-turn call

**Approach.** Each user message is sent to the model with only a small, fixed
prompt. Nothing from previous turns or sessions is available.

**Assumptions.**

1. Each turn is self-contained and carries all needed context.
2. Nothing said previously is needed to answer current or future turns.
3. Users never need continuity.

**Failure case (concrete).** On Monday the user says: *"I am lactose
intolerant — please keep me on dairy-free cooking."* The assistant
acknowledges. On Tuesday the user asks: *"What should I have for breakfast?"*
The assistant recommends yogurt and paneer. The user must restate the
constraint; if they forget, the recommendation is actively harmful. The same
failure recurs for every durable fact: allergies, medications, deadlines,
travel plans, work commitments, partner names, and consent instructions like
*"never share my details with third parties."*

**Failure mechanism.** The failure is structural, not a tuning problem: the
model has no state beyond its context window, and nothing persists across
calls [P:4]. The external-memory literature exists precisely because of this
limit [P:1][P:2][P:3][P:9].

**Violations.** C4 by omission — the current truth about the user is never
recorded, so the assistant cannot act on it; C5 and C6 by omission — there is
no store, so nothing is governed. (These by-omission violations look tame
but are the reason severity is highest when the assistant is used in
high-stakes settings, §2 of `01_problem.md`.)

**To be validated in the naive baseline.** [A: cross-session continuity —
the baseline measures how often required facts from prior sessions are simply
absent.]

---

## A2 — Full-conversation replay

**Approach.** Store the entire conversation history and prepend it (or its
longest fitting prefix) to each new turn, so the model "sees" the past.

**Why it is attractive.** Trivial to implement, lossless with respect to what
was said, and it gives real continuity for short conversations [O].

**Assumptions.**

1. The full history fits inside the context window.
2. All past statements remain relevant.
3. More context monotonically improves answers.
4. Older and newer statements have equal standing (no recency).

**Failure case (concrete).** A ninety-day renovation conversation grows past
the memory limit. The system truncates the oldest, which contained the
budget ceiling, the contractor deadline, and the guest list. Next week the
assistant proposes spending that exceeds the budget. Separately, the user
changed a preference in week two (*"no pine countertops"*) and reversed it in
week three (*"pine countertops after all"*). Replay injects both lines with
equal weight; the model cannot know which is authoritative, and produces
contradictory orders in different turns. [A: same-language-vs-current
precedence]

**Failure mechanism.** Finite context: attention is bounded [P:4], so a
growing transcript is truncated — and the discarded content is the oldest,
which is often the most consequential (constraints, commitments). Contradiction
is never arbitrated: replay carries both poles and no mechanism to resolve
them. Cost and latency scale linearly with history length [P:4][O: measured
in naive-baseline runs], degrading p95
latency and per-tenant economics as conversation length grows.

**Constraints violated.** C1 (overflow and truncation), C2 (latency), C3
(cost), C4 (contradiction and staleness replayed as-is).

**Assessment.** Replay fixes A1's absence of memory only by exhausting every
other constraint. The problem is not *seeing the history* — it is *showing
the right history*. That distinction is the seed of A4 and the whole
reconstruction.

---

## A3 — Keyword / symbolic lookup over stored notes

**Approach.** Store user facts as structured or literal notes; at query time,
find notes by literal keyword, exact-match, or regex, and inject the matches.

**Assumptions.**

1. Literal term overlap measures relevance.
2. The user phrases queries and notes with shared vocabulary.
3. An exact match is sufficient to decide what to present.

**Failure case (concrete).** The user's notes store: *"salsa makes me sick,"
"no dairy for guests," "deadline Nov 3."* On Friday the user asks: *"What
should I make for the party?"* No term overlaps any stored note — the system
retrieves nothing, and the system's allergy and dietary constraints vanish
silently. Combine with the false-positive case: the user asks *"What about
salsa?"* and the exact match deposits the health warning for cooking ideas —
a lexical hit with the wrong meaning. Both directions fail: paraphrase
(no hit when there should be) and polysemy (hit when there should not be). [A:
lexical-gap vs. paraphrase]

**Failure mechanism.** Relevance is a semantic property; keyword matching
only catches same-vocabulary/literal cases. One query can also retrieve
stale notes forever — the index never expires, corrects, or deletes (C8),
and there is no ranking by importance or recency.

**Constraints violated.** C4 (relevant content missed; irrelevant content can
be injected), C8 concerns (store grows stale without lifecycle).

---

## A4 — Naive dense retrieval over a raw transcript

**Approach.** Embed the full chat transcript as chunks; at query time compute
vector similarity (FAISS [P:10], HNSW [P:11]) and inject the top-k matches
into the prompt.

**Why it is attractive.** It bounds the injection (C1), replaces lexical
matching with semantic similarity (fixes A3), and avoids truncation (no
window overflow — the entire store stays searchable). This is the fairest
"naive" design: all the modern building blocks, none of the memory-subsystem
structure. It is the baseline the handbook's acceptance comparison expects.

**Assumptions.**

1. Everything said is worth storing and retrieving (store-everything).
2. Semantic similarity between query and chunk is a sufficient ranking
   signal.
3. The most similar chunk is the correct answer, *and* retrieval is safe
   (no sensitive distinctions).
4. Chunk content is uniformly valuable — no distinction between durable
   preference, transient remark, sensitive fact, or contradiction.

**Failure case (concrete).** In a single week:

- (a) *Contradiction.* The user says *"I like X"* on Monday and *"I broke
  with X, I prefer Y"* on Wednesday. Both chunks are stored and both rank
  high; a Friday query returns both; the assistant answers with X or Y
  depending on embedding noise. [A]
- (b) *Sensitive content.* The user mentions a new phone number in passing.
  It embeds into the index with no admission rule. Any later query about
  "number," "reaching me," "contact" surfaces it — to any caller with a
  plausible query, and across sessions without consent or retention. [A]
- (c) *Cross-tenant risk.* Two tenants discuss similar topics. The index is
  global; a retrieval query can return the other tenant's snippets. [A]
- (d) *Recency ignored.* The correct answer is in a month-old turn, but a
  similar-sounding more recent turn outranks it; the decisive detail is
  lost. [A]

**Failure mechanism.** The design is tuned to *what is similar* but never
asks *what should be stored, what should be shown, what is current, who may
see it, and how long it lives.* The top-k answers are therefore often coherent
but wrong — the signature of a system, memory, and policy.

**Constraints violated.** C4 (he *system's own strongest weakness: the
injected context is the wrong context*), C5 (sensitive data retrievable), C6
(cross-tenant leakage risk), C8 (the store grows unboundedly), and C1 *by
quality*: the budget is filled with plausible-but-irrelevant content, so the
actual signal injected is low. There is no lifecycle (nothing is removed,
consolidated, or expired).

**Why this is the core evidence.** A4 takes all the correct scientific
taking (embeddings, similarity search) and fails for *structural* reasons —
the absence of curation, ranking, and governance is exactly what the next
append has to add. The similar baseline will measure these failures in the
naive protocol (Deliverable 3), giving the final design (Deliverable 4) a
quantified route.

---

## A5 — Prompt-level instruction ("remember this")

**Approach.** Add a phrase to the system prompt: *"Remember everything the
user says and always take it into account."* No external storage, no
retrieval.

**Assumptions.** 1. A sentence in the prompt creates durable memory. The
model can maintain "memory" across calls. Back-end no extra components
needed.

**Failure case (concrete).** The user states: *"Remember I live in
Amsterdam and I work for ABB."* The assistant replies *"Remembered!"* The
next session they ask: *"How long have I been in the country?"* The
assistant has no record — the "memory" was just tokens in a single call.
The agree-script makes the user believe there is continuity when there is
none; the system cannot detect its own forgetting.

**Failure mechanism.** The prompt can name a behavior but cannot create
storage. The model has no persistent memory beyond the context window [P:4];
everything else is words-look-like-a-signal [O].

**Constraints violated.** C4, C5, C6 by omission — and because the user is
told the memory exists, the omission is *worse* than A1, it is
soft-instrumented deception.

---

## What the five failures, taken together, prove

| Failure | Root cause | Required capability |
|---|---|---|
| A1: no continuity | No record at all | Presence — something must be retained |
| A2: overflow + pollution | Stored but uncurated | Selection of what is injected; lifecycle |
| A3: wrong matches | Stored but matched mechanically | Semantic, multi-signal retrieval |
| A4: plausible-but-wrong answers | Stored, retrieved; no admission/ranking/lifecycle/isolation | Governed store: admission, ranking, lifecycle, isolation |
| A5: fake continuity | Stored nothing at all, claims it did | Honesty, and observable state |

Lay the five gaps side by side and the required system writes itself: decide
what enters the store; represent it well with provenance; store isolated and
safe; retrieve and rank by multiple signals; build the injection within a
token budget; keep it alive with correction/decay/deletion; and observe it so
behavior is always explainable. That derivation is the subject of
`first_principles.md`.

---

*End of failure analysis. Continue to `first_principles.md`.*