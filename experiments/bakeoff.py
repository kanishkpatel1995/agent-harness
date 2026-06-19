"""Run the compaction bake-off: policies x run-lengths x seeds.

Checkpointed + resumable: each finished cell is appended to results.csv with a
done-guard, so a rate-limit storm (or Ctrl-C) never loses progress — just rerun.

    python experiments/bakeoff.py [model]        # default: 8b dev model
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from experiments.nim import NimLLM
from experiments.policies import POLICIES
from experiments.simulate import run_probe

RESULTS = Path(__file__).resolve().parent / "results.csv"
FIELDS = ["policy", "run_length", "seed", "needles_total", "recall_window",
          "recall_probe", "n_compactions", "tokens_in", "tokens_out", "tokens_total"]
RUN_LENGTHS = [4, 8, 16]
SEEDS = [0, 1, 2]


def done_cells():
    if not RESULTS.exists():
        return set()
    with RESULTS.open() as f:
        return {(r["policy"], r["run_length"], r["seed"]) for r in csv.DictReader(f)}


def append(row):
    new = not RESULTS.exists()
    with RESULTS.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)


def summarize():
    if not RESULTS.exists():
        return
    agg = defaultdict(lambda: defaultdict(list))
    with RESULTS.open() as f:
        for r in csv.DictReader(f):
            agg[r["policy"]]["win"].append(int(r["recall_window"]))
            agg[r["policy"]]["probe"].append(int(r["recall_probe"]))
            agg[r["policy"]]["tok"].append(int(r["tokens_total"]))
            agg[r["policy"]]["need"].append(int(r["needles_total"]))
    print("\npolicy       recall_window  recall_probe   mean_tokens")
    print("-" * 56)
    for p in ("truncate", "recency", "importance", "semantic"):
        a = agg.get(p)
        if not a:
            continue
        need = sum(a["need"]) / len(a["need"])
        win = sum(a["win"]) / len(a["win"])
        probe = sum(a["probe"]) / len(a["probe"])
        tok = sum(a["tok"]) / len(a["tok"])
        print(f"{p:<12} {win:4.1f}/{need:<4.1f}      {probe:4.1f}/{need:<4.1f}     {tok:8.0f}")


def main():
    model = sys.argv[1] if len(sys.argv) > 1 else "meta/llama-3.1-8b-instruct"
    llm = NimLLM(model=model)
    done = done_cells()
    plan = [(p, L, s) for p in POLICIES for L in RUN_LENGTHS for s in SEEDS]
    print(f"{len(plan)} cells; {len(done)} already done; model={model}")
    for pname, L, s in plan:
        if (pname, str(L), str(s)) in done:
            continue
        try:
            row = run_probe(POLICIES[pname], llm, run_length=L, seed=s)
        except Exception as e:  # one bad cell must not kill the sweep
            print(f"  {pname:<10} L={L:<2} s={s}  ERROR {type(e).__name__}: {e}")
            continue
        append(row)
        print(f"  {pname:<10} L={L:<2} s={s}  win={row['recall_window']}/{row['needles_total']}"
              f"  probe={row['recall_probe']}/{row['needles_total']}"
              f"  tok={row['tokens_total']:<5}  comp={row['n_compactions']}")
    summarize()
    print(f"\nResults: {RESULTS}")


if __name__ == "__main__":
    main()
