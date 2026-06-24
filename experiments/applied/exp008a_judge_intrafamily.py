#!/usr/bin/env python3
"""EXP-008a — judge robustness, intra-family edition (free-tier-viable).

The free NIM tier throttles non-Llama judges to near-zero on sustained fresh calls, so a
cross-family panel is impractical here (deferred to a frontier judge in Phase 4). This is the
defense we CAN run now, on the generous Llama models, and it still answers the two questions a
reviewer cares about most:

  1. Model-SIZE robustness: does an 8B judge agree with the 70B judge? (re-grade with 8B)
  2. POSITION robustness: does the 70B judge flip when gold/candidate order is swapped?
     (the classic position-bias probe, Zheng et al. 2306.05685)

We replay the exact logged judge prompts (70B verdicts already in the logs) and report raw
agreement + Cohen's kappa for both, plus how often each diverges from the naive substring
metric. We also dump a spot-check CSV (the disagreement items) for a human pass.

    python experiments/applied/exp008a_judge_intrafamily.py [--sample 200]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.nim import NimLLM
from experiments.bench.logsetup import setup, get
from experiments.applied.agent import is_correct
from experiments.applied.judge import JUDGE_SYS, judge as judge_call

log = get("exp008a")

J8B = "meta/llama-3.1-8b-instruct"        # smaller same-family judge (size robustness)
J70B = "meta/llama-3.3-70b-instruct"      # the original judge, re-run with swapped order
RUN_GLOBS = ["experiments/runs/EXP-003b__frames-pressure__20260622-1808",
             "experiments/runs/EXP-004__locomo-transfer__20260622-0233"]


def _v(text):
    u = (text or "").strip().upper()
    return int(("CORRECT" in u) and ("INCORRECT" not in u))


def _collect():
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
            user = next((m.get("content", "") for m in rec["messages"] if m.get("role") == "user"), "")
            key = hashlib.sha256(user.encode()).hexdigest()[:16]
            if key in seen:
                continue
            seen.add(key)
            q = re.search(r"Question:\s*(.*?)\nGold answer:", user, re.S)
            g = re.search(r"Gold answer:\s*(.*?)\nCandidate answer:", user, re.S)
            c = re.search(r"Candidate answer:\s*(.*?)\nVerdict", user, re.S)
            out.append({"key": key, "messages": rec["messages"], "j_70b": _v(rec.get("response")),
                        "q": q.group(1).strip() if q else "",
                        "gold": g.group(1).strip() if g else "",
                        "cand": c.group(1).strip() if c else ""})
    return out


def _swapped_msg(c):
    """The same judge prompt with candidate listed BEFORE gold (position-bias probe)."""
    return [{"role": "system", "content": JUDGE_SYS},
            {"role": "user", "content": f"Question: {c['q']}\nCandidate answer: {c['cand']}\n"
                                        f"Gold answer: {c['gold']}\nVerdict (CORRECT or INCORRECT):"}]


def _kappa(a, b):
    n = len(a)
    if n == 0:
        return 0.0
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def main():
    ap = argparse.ArgumentParser(description="EXP-008a intra-family judge robustness")
    ap.add_argument("--sample", type=int, default=200)
    ap.add_argument("-v", action="count", default=0)
    args = ap.parse_args()
    setup("DEBUG" if args.v >= 2 else "INFO")

    calls = _collect()
    log.info(f"collected {len(calls)} unique judge triples")
    rng = random.Random(0)
    pos = [c for c in calls if c["j_70b"] == 1]
    neg = [c for c in calls if c["j_70b"] == 0]
    rng.shuffle(pos); rng.shuffle(neg)
    half = args.sample // 2
    sample = pos[:half] + neg[:half]
    rng.shuffle(sample)
    log.info(f"sampled {len(sample)} (balanced {min(half,len(pos))}/{min(half,len(neg))})")

    # Two Llama judges run sequentially per item; each paces at 3s so the combined rate
    # (~40/min) stays under the shared free-tier limit. Llama models are generous, so this holds.
    j8 = NimLLM(model=J8B, transcript_path=None, min_interval=3.0, max_retries=8)
    j70 = NimLLM(model=J70B, transcript_path=None, min_interval=3.0, max_retries=8)

    out_dir = Path("experiments/runs/EXP-008a__judge-intrafamily")
    out_dir.mkdir(parents=True, exist_ok=True)
    rp = out_dir / "results.csv"
    cols = ["key", "j_70b", "j_8b", "j_70b_swap", "substring", "question", "gold", "candidate"]
    done = {r["key"] for r in csv.DictReader(rp.open())} if rp.exists() else set()
    f = rp.open("a", newline=""); w = csv.DictWriter(f, fieldnames=cols)
    if not done:
        w.writeheader()
    for i, c in enumerate(sample):
        if c["key"] in done:
            continue
        try:
            j8v = _v(j8.complete(c["messages"], stage="judge").content)
            j70sv = _v(j70.complete(_swapped_msg(c), stage="judge").content)
        except Exception as e:
            log.warning(f"skip {c['key'][:8]}: {type(e).__name__}")
            continue
        w.writerow({"key": c["key"], "j_70b": c["j_70b"], "j_8b": j8v, "j_70b_swap": j70sv,
                    "substring": int(is_correct(c["cand"], c["gold"])) if c["gold"] else "",
                    "question": c["q"][:200], "gold": c["gold"][:120], "candidate": c["cand"][:200]})
        f.flush()
        if (i + 1) % 25 == 0:
            log.info(f"  {i+1}/{len(sample)} processed")
    f.close()

    rows = list(csv.DictReader(rp.open()))
    iv = lambda r, k: int(r[k]) if r[k] != "" else None
    n = len(rows)
    a70 = [iv(r, "j_70b") for r in rows]
    a8 = [iv(r, "j_8b") for r in rows]
    asw = [iv(r, "j_70b_swap") for r in rows]
    print(f"\n=== EXP-008a: intra-family judge robustness (n={n}) ===")
    print(f"{'comparison':<42}{'raw agree':>11}{'kappa':>8}")
    print(f"{'70B vs 8B  (size robustness)':<42}{sum(x==y for x,y in zip(a70,a8))/n:>10.1%}{_kappa(a70,a8):>8.2f}")
    print(f"{'70B vs 70B-order-swapped  (position)':<42}{sum(x==y for x,y in zip(a70,asw))/n:>10.1%}{_kappa(a70,asw):>8.2f}")
    sub = [r for r in rows if r["substring"] != ""]
    if sub:
        sa = sum(1 for r in sub if int(r["substring"]) == int(r["j_70b"])) / len(sub)
        print(f"{'70B vs substring metric':<42}{sa:>10.1%}{'':>8}   <- the metric-inversion gap")

    # B: spot-check set = the items where 70B and 8B disagree (the interesting ones to adjudicate)
    spot = [r for r in rows if r["j_70b"] != r["j_8b"]]
    sp = out_dir / "spotcheck_disagreements.csv"
    with sp.open("w", newline="") as g:
        ww = csv.DictWriter(g, fieldnames=["j_70b", "j_8b", "substring", "question", "gold", "candidate"])
        ww.writeheader()
        for r in spot:
            ww.writerow({k: r[k] for k in ["j_70b", "j_8b", "substring", "question", "gold", "candidate"]})
    print(f"\nspot-check set (70B/8B disagreements): {len(spot)} items -> {sp}")
    print(f"wrote {rp}")


if __name__ == "__main__":
    main()
