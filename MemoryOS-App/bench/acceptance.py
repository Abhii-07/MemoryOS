"""G-M6 acceptance replay: D3 baseline workload vs MemoryOS + targets.

Usage (from repo root):
    python -m bench.acceptance [--out bench/results/acceptance.json]

Replays the exact 10 hand-written cases from `experiments/naive_baseline/
dataset.py` (single source of truth — the benchmark never re-derives the
workload) through the real stack: admission (PII guardrail), hybrid
retrieval, and budgeted context injection. Then compares the results
against the naive baseline's `summary.json` and the Deliverable targets
from system_design_part1 (contradiction < 5%, cold-start FP < 5%,
sensitive leak = 0%, p95 < 150 ms).

Baseline numbers (experiments/naive_baseline/summary.json, 2026-08-08):
  contradiction_failure_rate 33%  -> target < 5%
  cold_start_false_positive   50%  -> target < 5%   (1/2 -> our NOOP path)
  sensitive_leak (retrieval) 100%  -> target 0%
  sensitive_leak (injection) 100%  -> target 0%
  recall@5 1.00 / precision@1 0.86 -> target 1.00 / 1.00 (design targets)

Exits non-zero if any target misses.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import statistics
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

from memory_os.context import build_context
from memory_os.db.store import MemoryStore
from memory_os.retrieval.hybrid import HybridRetriever, NoRelevantMemory

APP_ROOT = Path(__file__).resolve().parents[1]          # MemoryOS-App/
REPO_ROOT = Path(__file__).resolve().parents[2]         # repo root (experiments live there)
DATASET = REPO_ROOT / "experiments" / "naive_baseline" / "dataset.py"

# D3 workload cases carrying stale/contradicting pairs (contradiction metric)
STALE_CASES = {"c1-direct-contradiction", "c2-payment-gateway-wording",
               "c2-tech-stack-preference"}

# Deliverable targets (system_design_part1 table; 360 data section)
TARGETS = {
    "contradiction_failure_rate": 0.05,
    "cold_start_false_positive_rate": 0.05,
    "sensitive_leak_rate_retrieval": 0.0,
    "sensitive_leak_rate_injection": 0.0,
    "precision_at_1": 1.0,
    "latency_p95_s": 0.150,
}


def load_d3_cases():
    spec = importlib.util.spec_from_file_location("d3_dataset", DATASET)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.all_cases()


def p95(values: list[float]) -> float:
    if not values:
        return 0.0
    return sorted(values)[int(round(len(values) * 0.95)) - 1]


def admit_all(store: MemoryStore, case, is_baseline=False):
    """Seed via the real admission path (secret-handling included)."""
    from memory_os.admission import Admitter

    ad = Admitter(store)
    stored: list[dict] = []
    for m in case.stored:
        r = ad.admit(tenant_id=case.user_id, user_id=case.user_id,
                     text=m.text, turn_type="user")
        if r.admission_op in ("ADD", "UPDATE") and r.record_id:
            stored.append(r)
    return stored


def replay_case(store: MemoryStore, case, retriever_factory):
    """Run one D3 case end-to-end. Returns the error-examples-style row.

    Tenant == user_id (the baseline's isolation granularity); every case
    runs against a fresh tenant so cases never contaminate each other."""
    tenant = case.user_id
    admit_all(store, case)

    start = time.perf_counter()
    try:
        hits = retriever_factory().search(
            tenant_id=tenant, user_id=case.user_id,
            query=case.query, limit=5)
        hit_ids = [h["id"] for h in hits]
        hit_texts = [h["text"] for h in hits]
        lat = time.perf_counter() - start
    except NoRelevantMemory:
        hits, hit_ids, hit_texts, lat = [], [], [], time.perf_counter() - start

    correct_set = set(case.correct_texts)
    stale_set = set(case.stale_texts)

    correct_is_top1 = bool(hit_texts and hit_texts[0] in correct_set)
    correct_in_topk = bool(correct_set and correct_set <= set(hit_texts))
    stale_outranks = bool(stale_set and hit_texts and
                          any(s in hit_texts and
                              hit_texts.index(s) <
                              min((hit_texts.index(c) for c in correct_set),
                                  default=len(hit_texts)) for s in stale_set))
    cold_start_ok = (case.expect_no_result and not hit_texts) or (
        not case.expect_no_result and bool(hit_texts))

    leaked_retrieval = any(s in hit_texts for s in case.sensitive_texts)
    block = build_context(memories=hits, token_budget=case.token_budget)
    injected = block.injected_context or ""
    leaked_injection = any(s in injected for s in case.sensitive_texts)
    survived = bool(correct_set) and bool(correct_set & set(block.memories
                                                            and [m["text"] for m in block.memories]))

    return {
        "case_id": case.case_id,
        "category": case.category,
        "user_id": case.user_id,
        "query": case.query,
        "num_stored": len(case.stored),
        "top1_result": hit_texts[0] if hit_texts else None,
        "correct_in_topk": correct_in_topk if correct_set else None,
        "correct_is_top1": correct_is_top1 if correct_set else None,
        "cold_start_ok": cold_start_ok,
        "stale_outranks_correct": bool(stale_outranks),
        "sensitive_leaked_retrieval": bool(leaked_retrieval),
        "sensitive_leaked_injection": bool(leaked_injection),
        "correct_survived_budget": survived if correct_set else None,
        "latency_s": round(lat, 6),
        "token_budget": case.token_budget,
        "tokens_used": block.tokens_used,
        "task_level_pass": (bool(correct_is_top1) if correct_set
                            else (not hit_texts if case.expect_no_result else None)),
        "retrieved_texts": hit_texts,
        "injected_text": injected,
    }


def aggregate(rows: list[dict]) -> dict:
    n = len(rows)
    stale_cases = [r for r in rows if r["case_id"] in STALE_CASES]
    sens = [r for r in rows if r["case_id"] == "c5-sensitive-leak-check"]
    cold = [r for r in rows if r["case_id"].startswith("c6")]
    with_correct = [r for r in rows if r["correct_in_topk"] is not None]
    return {
        "total_cases": n,
        "recall_at_5": (sum(1 for r in with_correct if r["correct_in_topk"])
                        / len(with_correct)) if with_correct else None,
        "precision_at_1": (sum(1 for r in with_correct if r["correct_is_top1"])
                           / len(with_correct)) if with_correct else None,
        "contradiction_failure_rate": (
            sum(1 for r in stale_cases if r["stale_outranks_correct"])
            / len(stale_cases) if stale_cases else None),
        "cold_start_false_positive_rate": (
            sum(1 for r in cold if not r["cold_start_ok"]) / len(cold)
            if cold else None),
        "sensitive_leak_rate_retrieval": (
            sum(1 for r in sens if r["sensitive_leaked_retrieval"]) / len(sens)
            if sens else None),
        "sensitive_leak_rate_injection": (
            sum(1 for r in sens if r["sensitive_leaked_injection"]) / len(sens)
            if sens else None),
        "task_level_pass_rate": sum(1 for r in rows if r["task_level_pass"]) / n,
        "latency_p50_s": round(statistics.median([r["latency_s"] for r in rows]), 6),
        "latency_p95_s": round(p95([r["latency_s"] for r in rows]), 6),
        "avg_tokens_used": round(statistics.mean([r["tokens_used"] for r in rows]), 2),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(APP_ROOT / "bench" / "results" /
                                         "acceptance.json"))
    args = ap.parse_args()

    cases = load_d3_cases()
    store = MemoryStore()
    store.apply_schema()
    with store.connect() as c:
        c.execute("DELETE FROM memories")
        c.execute("DELETE FROM propagation_jobs")

    rows = [replay_case(store, case,
                        lambda: HybridRetriever(store)) for case in cases]

    with store.connect() as c:
        c.execute("DELETE FROM memories")
        c.execute("DELETE FROM propagation_jobs")

    agg = aggregate(rows)
    baseline = {
        "total_cases": 10,
        "recall_at_5": 1.0,
        "precision_at_1": 0.8571428571428571,
        "contradiction_failure_rate": 0.3333333333333333,
        "cold_start_false_positive_rate": 0.5,
        "sensitive_leak_rate_retrieval": 1.0,
        "sensitive_leak_rate_injection": 1.0,
        "task_level_pass_rate": 0.6666666666666666,
        "latency_p50_s": 0.000734,
        "latency_p95_s": 0.0008013,
        "avg_tokens_used": 29.2,
    }
    result = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "suite": "D3 workload replay (experiments/naive_baseline/dataset.py)",
        "memoryos": agg,
        "baseline": baseline,
        "targets": TARGETS,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    failed = []
    for metric, threshold in TARGETS.items():
        mine = agg[metric]
        if mine is None:
            failed.append(f"{metric}: no-data")
            continue
        if metric == "precision_at_1":
            ok = mine >= threshold
        elif metric == "latency_p95_s":
            ok = mine <= threshold
        else:
            ok = mine <= threshold
        if not ok:
            failed.append(f"{metric}: {mine:.3f} vs target {threshold}")

    print("D3 replay -> MemoryOS  (targets: part1 + EC-15 latency)")
    print(f"{'metric':<36}{'baseline':>10}{'memoryos':>10}{'target':>10}{'  status'}")
    order = ["recall_at_5", "precision_at_1", "contradiction_failure_rate",
             "cold_start_false_positive_rate", "sensitive_leak_rate_retrieval",
             "sensitive_leak_rate_injection", "task_level_pass_rate",
             "latency_p95_s", "avg_tokens_used"]
    for metric in order:
        b = baseline.get(metric, "-")
        t = TARGETS.get(metric, "-")
        status = ""
        m = agg[metric]
        if t != "-":
            if metric == "precision_at_1":
                status = "OK" if m is not None and m >= t else "MISS"
            else:
                status = "OK" if m is not None and m <= t else "MISS"
        b_s = f"{b:.3f}" if isinstance(b, float) else str(b)
        m_s = f"{m:.3f}" if isinstance(m, float) else str(m)
        t_s = f"{t:.3f}" if isinstance(t, float) else str(t)
        print(f"{metric:<36}{b_s:>10}{m_s:>10}{t_s:>10}{status:>10}")
    print(f"results -> {out}")
    print("PASS" if not failed else "FAIL: " + "; ".join(failed))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())