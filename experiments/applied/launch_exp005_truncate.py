#!/usr/bin/env python3
"""EXP-005 — the truncation baseline on FRAMES (the floor every arm must beat).

A single-arm run on purpose: truncate alone, graded by the held-constant 70B LLM
judge, under high compaction pressure (small budget + chunked reads). The point is
not to compare policies here but to establish ONE unambiguous number — the cheapest
possible policy's accuracy — and to demonstrate the run-directory contract end to
end (manifest -> prompts -> results), so a stranger can reproduce it with one line:

    python experiments/applied/launch_exp005_truncate.py

Everything stochastic is seeded; the model, budget, judge, and questions are pinned
in the manifest the run writes. Re-running replays the response cache for free.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Repo root on the path so `python experiments/applied/launch_exp005_truncate.py`
# works as a plain script (not only as `python -m ...`).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.applied.runner import Config, run, report  # noqa: E402
from experiments.bench.logsetup import setup  # noqa: E402

CFG = Config(
    exp_id="EXP-005",
    slug="frames-truncate-baseline",
    hypothesis=(
        "Truncation (keep the recent turns, drop the rest, no LLM call) sets the "
        "accuracy floor on FRAMES multi-hop QA under high compaction pressure: it is "
        "the cheapest policy and the baseline every summary/retrieval arm must beat."
    ),
    assumptions=(
        "Oracle retrieval (gold Wikipedia articles) isolates compaction from search quality.",
        "Chunked reads at budget 1500 force many compaction events per question.",
        "The 70b LLM judge credits paraphrased-correct answers; substring is biased toward verbatim.",
        "n=30 at one seed is a dev-scale point estimate; the 95% CI is wide (cf. experiments/stats.py).",
    ),
    model="meta/llama-3.1-8b-instruct",
    use_judge=True,
    policies=("truncate",),
    max_articles=6,
    n_questions=30,
    budget=1500,
    chunk_chars=1500,
    keep_recent=4,
    seed=7,
)


if __name__ == "__main__":
    setup("INFO")
    results_path = run(CFG)
    report(results_path)
