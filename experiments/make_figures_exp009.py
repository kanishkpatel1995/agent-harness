#!/usr/bin/env python3
"""EXP-009 figure: the agentic regime amplifies the compaction-policy gap.

Grouped bars, oracle FRAMES (fed articles) versus agentic FRAMES (the agent searches and reads
itself), for truncate / externalize / reversible_hybrid, with 95% bootstrap CIs. The visual point:
the three bars are close under oracle retrieval and spread apart on a real agent transcript,
because blind truncation throws away evidence the agent gathered and cannot recover it.

    python experiments/make_figures_exp009.py
"""

from __future__ import annotations

import csv
import glob
import random

from experiments import figstyle

ARMS = ["truncate", "externalize", "reversible_hybrid"]
LABELS = {"truncate": "truncate", "externalize": "externalize", "reversible_hybrid": "reversible hybrid"}
COLORS = {"truncate": "#999999", "externalize": "#56B4E9", "reversible_hybrid": "#009E73"}


def _load(path):
    rows = list(csv.DictReader(open(path)))
    return {arm: [int(r["correct"]) for r in rows if r["policy"] == arm] for arm in ARMS}


def _ci(vals, n_boot=5000, seed=0):
    rng = random.Random(seed)
    n = len(vals)
    means = sorted(sum(vals[rng.randrange(n)] for _ in range(n)) / n for _ in range(n_boot))
    return sum(vals) / n, means[int(0.025 * n_boot)], means[int(0.975 * n_boot)]


def _pick(pattern):
    dirs = sorted(glob.glob(pattern), key=lambda p: p.rsplit("__", 1)[-1])
    return dirs[-1] + "/results.csv"


def main():
    oracle = _load(_pick("experiments/runs/EXP-003b__frames-pressure__*"))     # n=200, fed articles
    agentic = _load(_pick("experiments/runs/EXP-009__agentic-frames__*"))       # n=60, agent-driven

    figstyle.apply()
    import matplotlib.pyplot as plt
    import numpy as np

    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    groups = [f"Oracle FRAMES\n(fed articles, n={len(oracle['truncate'])})",
              f"Agentic FRAMES\n(agent searches, n={len(agentic['truncate'])})"]
    x = np.arange(2)
    width = 0.26
    for i, arm in enumerate(ARMS):
        accs, lo, hi = [], [], []
        for data in (oracle, agentic):
            m, l, h = _ci(data[arm])
            accs.append(m); lo.append(m - l); hi.append(h - m)
        ax.bar(x + (i - 1) * width, accs, width, yerr=[lo, hi], capsize=3,
               color=COLORS[arm], edgecolor="#333333", linewidth=0.6, label=LABELS[arm])
        for xi, a in zip(x + (i - 1) * width, accs):
            ax.text(xi, a + 0.01, f"{a:.2f}", ha="center", va="bottom", fontsize=8.5)

    ax.set_xticks(x)
    ax.set_xticklabels(groups)
    ax.set_ylim(0, 0.55)
    figstyle.finish(ax, "Retrieval regime (oracle vs agent-driven)", "Answer accuracy (judged, fraction)")
    p = figstyle.save(fig, "presentation/figures/EXP-009_agentic_amplification_v1.pdf")
    fig.savefig(str(p).replace(".pdf", ".png"), dpi=200, bbox_inches="tight")
    print("saved png too")


if __name__ == "__main__":
    main()
