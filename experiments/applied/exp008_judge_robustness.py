#!/usr/bin/env python3
"""EXP-008 — judge robustness: defend the LLM-as-judge with a cross-family panel.

The bake-off grades answers with a single open 70B Llama judge. Reviewers will (rightly)
attack that: judges carry position and self-preference bias (Zheng et al. 2306.05685), and
reference-based judges can override the gold reference under conflict (2601.07506). Llama
also grades answers produced by Llama agents, a self-family risk.

This experiment replays the EXACT judge prompts already logged in prior runs' prompts.jsonl
to TWO additional, different-family judges (Qwen, DeepSeek), and reports inter-judge agreement
(raw + Cohen's kappa), 3-judge majority stability, and how often each LLM judge diverges from
the naive substring metric (tying to the metric-inversion result). No agent is re-run; only the
new judges make calls, so the agent answers are unchanged.

    python experiments/applied/exp008_judge_robustness.py [--sample 200]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.nim import NimLLM
from experiments.bench.logsetup import setup, get
from experiments.applied.agent import is_correct  # the naive substring metric

log = get("exp008")

JUDGE1 = "meta/llama-3.3-70b-instruct"        # the existing judge (verdicts already in the logs)
PANEL = {                                      # the added cross-family judges
    "qwen": "qwen/qwen3.5-122b-a10b",
    "deepseek": "deepseek-ai/deepseek-v4-pro",
}
RUN_GLOBS = ["experiments/runs/EXP-003b__frames-pressure__20260622-1808",  # FRAMES n=200
             "experiments/runs/EXP-004__locomo-transfer__20260622-0233"]    # LoCoMo n=100


def _verdict(text):
    v = (text or "").strip().upper()
    return int(("CORRECT" in v) and ("INCORRECT" not in v))


def _collect_judge_calls():
    """Every logged judge call: its exact messages, the judge-1 verdict, and the parsed
    gold/candidate (for the substring comparison)."""
    seen, out = set(), []
    for d in RUN_GLOBS:
        p = Path(d) / "prompts.jsonl"
        if not p.exists():
            continue
        for line in p.open():
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if rec.get("stage") != "judge":
                continue
            msgs = rec.get("messages")
            user = next((m.get("content", "") for m in msgs if m.get("role") == "user"), "")
            key = hashlib.sha256(user.encode()).hexdigest()[:16]
            if key in seen:
                continue
            seen.add(key)
            gold = re.search(r"Gold answer:\s*(.*?)\nCandidate answer:", user, re.S)
            cand = re.search(r"Candidate answer:\s*(.*?)\nVerdict", user, re.S)
            out.append({
                "key": key, "messages": msgs,
                "j1": _verdict(rec.get("response")),
                "gold": (gold.group(1).strip() if gold else ""),
                "cand": (cand.group(1).strip() if cand else ""),
            })
    return out


def _kappa(a, b):
    """Cohen's kappa for two binary verdict lists."""
    n = len(a)
    if n == 0:
        return 0.0
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pa1, pb1 = sum(a) / n, sum(b) / n
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def main():
    ap = argparse.ArgumentParser(description="EXP-008 judge robustness (cross-family panel)")
    ap.add_argument("--sample", type=int, default=200, help="triples to re-grade (stratified by j1)")
    ap.add_argument("-v", action="count", default=0)
    args = ap.parse_args()
    setup("DEBUG" if args.v >= 2 else "INFO")

    calls = _collect_judge_calls()
    log.info(f"collected {len(calls)} unique judge triples from {len(RUN_GLOBS)} runs")
    # stratified sample: balance j1=correct / j1=incorrect so agreement is not dominated by one class
    rng = random.Random(0)
    pos = [c for c in calls if c["j1"] == 1]
    neg = [c for c in calls if c["j1"] == 0]
    half = args.sample // 2
    rng.shuffle(pos); rng.shuffle(neg)
    sample = pos[:half] + neg[:half]
    rng.shuffle(sample)
    log.info(f"sampled {len(sample)} ({min(half,len(pos))} j1-correct + {min(half,len(neg))} j1-incorrect)")

    judges = {name: NimLLM(model=mid, transcript_path=None) for name, mid in PANEL.items()}

    rows = []
    for i, c in enumerate(sample):
        rec = {"key": c["key"], "j1_llama": c["j1"],
               "substring": int(is_correct(c["cand"], c["gold"])) if c["gold"] else ""}
        for name, jllm in judges.items():
            r = jllm.complete(c["messages"], stage="judge")
            rec[f"j_{name}"] = _verdict(r.content)
        rows.append(rec)
        if (i + 1) % 25 == 0:
            log.info(f"  {i+1}/{len(sample)} re-graded")

    out_dir = Path("experiments/runs/EXP-008__judge-robustness")
    out_dir.mkdir(parents=True, exist_ok=True)
    cols = ["key", "j1_llama", "j_qwen", "j_deepseek", "substring"]
    with (out_dir / "results.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in cols})

    # --- agreement report ---
    labels = {"j1_llama": "Llama-3.3-70B", "j_qwen": "Qwen3.5-122B", "j_deepseek": "DeepSeek-V4"}
    keys = list(labels)
    print(f"\n=== EXP-008: judge agreement (n={len(rows)}) ===")
    print(f"{'pair':<34}{'raw agree':>11}{'kappa':>8}")
    for a, b in itertools.combinations(keys, 2):
        va = [r[a] for r in rows]
        vb = [r[b] for r in rows]
        raw = sum(1 for x, y in zip(va, vb) if x == y) / len(rows)
        print(f"{labels[a]+' vs '+labels[b]:<34}{raw:>10.1%}{_kappa(va, vb):>8.2f}")
    # majority-vote stability + vs substring
    maj = [1 if (r["j1_llama"] + r["j_qwen"] + r["j_deepseek"]) >= 2 else 0 for r in rows]
    unanimous = sum(1 for r in rows if r["j1_llama"] == r["j_qwen"] == r["j_deepseek"]) / len(rows)
    sub_rows = [r for r in rows if r["substring"] != ""]
    sub_agree = (sum(1 for r in sub_rows if r["substring"] == (1 if (r["j1_llama"]+r["j_qwen"]+r["j_deepseek"])>=2 else 0))
                 / len(sub_rows)) if sub_rows else 0
    print(f"\n3-judge unanimous on {unanimous:.1%} of items")
    print(f"substring vs 3-judge majority agrees only {sub_agree:.1%}  (the metric-inversion gap, quantified)")
    print(f"\nwrote {out_dir}/results.csv")


if __name__ == "__main__":
    main()
