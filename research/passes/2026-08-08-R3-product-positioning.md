# Research Pass R3 — Product Positioning Verification (2026-08-08)

> Goal: check the competitive/positioning claims used in `product/PRD.md` —
> vendor names, ecosystem activity, and regulatory framing. Method: web
> verification performed 2026-08-08. Outcome: 1 name corrected, ecosystem
> activity confirmed, regulatory citation corrected.

## 1. "Supertone/Supermemory" — CORRECTED

- The memory-for-Claude tool is **Supermemory** (supermemory.ai, GitHub
  supermemoryai; founder Dhravya Shah; ~$3M raised; "second brain" app +
  SDKs + Claude Code plugin since Jan 2026; ~2.7k stars; claims 81.6%
  LongMemEval). Alive as of Jul 2026 — not dead.
- **"Supertone" is an unrelated Korean AI-audio company (supertone.ai,
  acquired by HYBE 2023).**
- **Correction applied:** PRD positioning references the vendor as
  "Supermemory"; any "Supertone" mention removed.
- Note: their 91% recall@10 hybrid figure (R2 pass) is a practitioner
  benchmark from their own hybrid-search guide (Apr 2026) — cited as `[O]`.

## 2. Ecosystem activity (Mem0 / Zep / LangMem) — SUPPORTED

- Mem0: active; $24M raised (YC, Basis Set, Peak XV, GitHub Fund, Oct 2025);
  exclusive memory provider in AWS Agent SDK; OpenMemory sunset ~Jul 2026
  (see R2) + CVE-2026-59705. → OSS memory layer is in flux; stable
  commercial API layer continues.
- Zep: active; Graphiti OSS (Apache-2.0); funding undisclosed.
- LangMem: active; LangChain's SDK on LangGraph (2025 launch), less mature.
- **Positioning implication:** an OSS, local-only, deterministic-supersession
  memory layer is defensible against a field that is either platform-tied
  (LangMem), commercial-API (Mem0 Platform), or graph-heavy (Zep).

## 3. OWASP LLM Top 10 (2025) — CORRECTED citation

- **No "Memory and Context Manipulation" / ASI06 entry exists.**
- 2025 list: LLM01 Prompt Injection, LLM02 Sensitive Information Disclosure,
  LLM03 Supply Chain, LLM04 Data & Model Poisoning, LLM05 Improper Output
  Handling, LLM06 Excessive Agency, LLM07 System Prompt Leakage, LLM08
  Vector & Embedding Weaknesses, LLM09 Misinformation, LLM10 Unbounded
  Consumption.
- Memory-related risks are spread across LLM04 (poisoning) and LLM08
  (RAG/embeddings).
- **Correction applied:** governance section of PRD now cites LLM04/LLM08
  rather than a nonexistent memory slot.

## R3 verdict

READY. One naming correction (Supermemory, not Supertone), one citation
correction (OWASP LLM04/LLM08, no ASI06), ecosystem claims verified as of
Aug 2026.
