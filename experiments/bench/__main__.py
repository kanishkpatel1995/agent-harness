"""CLI for the compaction bake-off bench.

  python -m experiments.bench              # dev sweep (8b), INFO logs
  python -m experiments.bench -vv          # dev sweep, DEBUG logs (every step)
  python -m experiments.bench --full       # real sweep (70b), 128k ceiling
  python -m experiments.bench --analyze-only
  python -m experiments.bench --model meta/llama-3.3-70b-instruct --max-window 4000
"""

from __future__ import annotations

import argparse
from dataclasses import replace

from .config import DEV, FULL, EXP002
from .logsetup import setup
from . import runner, analyze

PRESETS = {"DEV": DEV, "FULL": FULL, "EXP002": EXP002}


def main():
    ap = argparse.ArgumentParser(description="Compaction bake-off bench")
    ap.add_argument("-v", action="count", default=0, help="-v INFO, -vv DEBUG")
    ap.add_argument("--full", action="store_true", help="full 70b sweep instead of dev")
    ap.add_argument("--model", default=None, help="override the model id")
    ap.add_argument("--max-window", type=int, default=None, help="override model_max_tokens")
    ap.add_argument("--dataset", default=None, help='override dataset (e.g. "synthetic")')
    ap.add_argument("--policies", default=None, help="comma list, e.g. truncate,recency")
    ap.add_argument("--budgets", default=None, help="comma list of ints, e.g. 1000,2000")
    ap.add_argument("--run-lengths", default=None, help="comma list of ints, e.g. 4,8,16")
    ap.add_argument("--seeds", default=None, help="comma list of ints, e.g. 0,1,2")
    ap.add_argument("--no-baseline", action="store_true", help="skip the no-compaction baseline")
    ap.add_argument("--analyze-only", action="store_true", help="skip the sweep, just report")
    a = ap.parse_args()

    cfg = FULL if a.full else DEV
    overrides = {}
    if a.model:
        overrides["model"] = a.model
    if a.max_window is not None:
        overrides["model_max_tokens"] = a.max_window
    if a.dataset:
        overrides["dataset"] = a.dataset
    if a.policies:
        overrides["policies"] = tuple(a.policies.split(","))
    if a.budgets:
        overrides["budgets"] = tuple(int(x) for x in a.budgets.split(","))
    if a.run_lengths:
        overrides["run_lengths"] = tuple(int(x) for x in a.run_lengths.split(","))
    if a.seeds:
        overrides["seeds"] = tuple(int(x) for x in a.seeds.split(","))
    if a.no_baseline:
        overrides["include_baseline"] = False
    if overrides:
        cfg = replace(cfg, **overrides)

    level = "DEBUG" if a.v >= 2 else "INFO"
    setup(level)

    ctx = None
    if not a.analyze_only:
        ctx = runner.run(cfg)
    analyze.report(cfg, results_path=(ctx.results_path if ctx else None))


if __name__ == "__main__":
    main()
