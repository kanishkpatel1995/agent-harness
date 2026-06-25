#!/usr/bin/env python3
"""EXP-008a figure: the LLM judge is robust (and the substring metric is not).

Horizontal bars of agreement with the fixed 70B judge: across model size (8B judge), across answer
order (the position-bias swap), and against the naive substring metric. The first two are near the
top (the verdict is stable, Cohen's kappa annotated); the third is far lower, which IS the
metric-inversion result, quantified.

    python -m experiments.make_figures_exp008
"""

from __future__ import annotations

import csv
import glob

from experiments import figstyle


def _kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def main():
    path = sorted(glob.glob("experiments/runs/EXP-008a__judge-intrafamily/results.csv"))[-1]
    rows = [r for r in csv.DictReader(open(path)) if r.get("j_70b") not in (None, "")]
    g70 = [int(r["j_70b"]) for r in rows]
    g8 = [int(r["j_8b"]) for r in rows]
    gsw = [int(r["j_70b_swap"]) for r in rows]
    sub = [(int(r["j_70b"]), int(r["substring"])) for r in rows if r.get("substring") not in (None, "")]
    n = len(rows)

    bars = [
        ("70B vs 8B judge\n(model size)", sum(x == y for x, y in zip(g70, g8)) / n, _kappa(g70, g8), "#009E73"),
        ("70B vs order-swapped\n(position bias)", sum(x == y for x, y in zip(g70, gsw)) / n, _kappa(g70, gsw), "#009E73"),
        ("70B vs substring metric\n(the naive baseline)", sum(a == b for a, b in sub) / len(sub), None, "#D55E00"),
    ]

    figstyle.apply()
    import matplotlib.pyplot as plt
    import numpy as np

    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    y = np.arange(len(bars))[::-1]
    for yi, (label, raw, kappa, color) in zip(y, bars):
        ax.barh(yi, raw, color=color, edgecolor="#333333", linewidth=0.6, height=0.6)
        # robustness bars round cleanly to whole %; the substring bar is exactly 74.5%, show the .5
        pct = f"{raw:.0%}" if kappa is not None else f"{raw:.1%}"
        txt = pct + (f"   (kappa {kappa:.2f})" if kappa is not None else "")
        ax.text(raw + 0.01, yi, txt, va="center", fontsize=9.5)
    ax.set_yticks(y)
    ax.set_yticklabels([b[0] for b in bars])
    ax.set_xlim(0, 1.0)
    ax.axvline(1.0, color="#B0B0B0", lw=0.5)
    figstyle.finish(ax, f"Agreement with the fixed 70B judge (fraction, n={n})", "")
    p = figstyle.save(fig, "presentation/figures/EXP-008_judge_robustness_v1.pdf")
    fig.savefig(str(p).replace(".pdf", ".png"), dpi=200, bbox_inches="tight")
    print("saved png too")


if __name__ == "__main__":
    main()
