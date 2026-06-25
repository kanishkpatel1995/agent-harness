#!/usr/bin/env python3
"""EXP-006 figure: under a fixed externalize policy, the memory system is the lever.

Three real open-source memory backends answer the SAME FRAMES questions through the SAME externalize
policy: only the store differs. Bars are judged accuracy with 95% bootstrap CIs. The point: swapping a
general local embedder (Chroma MiniLM) for a retrieval-tuned one (NIM nv-embedqa) buys +0.15, and
Mem0's extract-then-dedupe distillation costs accuracy (and an LLM call per add) on this factual task.

    python -m experiments.make_figures_exp006
"""

from __future__ import annotations

import csv
import glob
import random

from experiments import figstyle

# (label, run-dir glob, colour). Ordered best -> worst so the story reads left to right.
SYSTEMS = [
    ("NIM\nnv-embedqa", "EXP-006__frames-memory-nim__*", "#009E73"),
    ("Mem0\n(deduped facts)", "EXP-006__frames-memory-mem0__*", "#E69F00"),
    ("Chroma\nMiniLM (local)", "EXP-006__frames-memory-chroma__*", "#999999"),
]


def _load(pattern):
    d = sorted(glob.glob(f"experiments/runs/{pattern}"), key=lambda p: p.rsplit("__", 1)[-1])[-1]
    return [int(r["correct"]) for r in csv.DictReader(open(d + "/results.csv"))]


def _ci(vals, n_boot=5000, seed=0):
    rng = random.Random(seed)
    n = len(vals)
    means = sorted(sum(vals[rng.randrange(n)] for _ in range(n)) / n for _ in range(n_boot))
    return sum(vals) / n, means[int(0.025 * n_boot)], means[int(0.975 * n_boot)]


def main():
    figstyle.apply()
    import matplotlib.pyplot as plt
    import numpy as np

    fig, ax = plt.subplots(figsize=(6.0, 4.2))
    labels, colors, n = [], [], 0
    for i, (label, pattern, color) in enumerate(SYSTEMS):
        vals = _load(pattern)
        n = len(vals)
        m, lo, hi = _ci(vals)
        ax.bar(i, m, 0.62, yerr=[[m - lo], [hi - m]], capsize=4,
               color=color, edgecolor="#333333", linewidth=0.6)
        ax.text(i, m + 0.012, f"{m:.2f}", ha="center", va="bottom", fontsize=10)
        labels.append(label)
        colors.append(color)

    ax.set_xticks(range(len(SYSTEMS)))
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 0.68)
    figstyle.finish(ax, f"Memory backend (externalize policy fixed, n={n} each)",
                    "Answer accuracy (judged, fraction)")
    p = figstyle.save(fig, "presentation/figures/EXP-006_memory_bakeoff_v1.pdf")
    fig.savefig(str(p).replace(".pdf", ".png"), dpi=200, bbox_inches="tight")
    print("saved png too")


if __name__ == "__main__":
    main()
