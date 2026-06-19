"""Render EXP-001 publication figures (PDF for the paper, PNG for the deck).

Reads the dev sweep results and produces, in publication house style
(experiments/figstyle.py): a quality-vs-cost Pareto, recall by policy x budget,
and the no-compaction baseline recall-vs-length.

    python experiments/make_figures.py [results.csv]
"""

from __future__ import annotations

import csv
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from experiments import figstyle  # noqa: E402

RESULTS = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("experiments/bench/results.csv")
OUT = Path("presentation/figures")


def load():
    rows = list(csv.DictReader(RESULTS.open()))
    return ([r for r in rows if r["arm"] == "compaction"],
            [r for r in rows if r["arm"] == "baseline"])


def agg_comp(comp):
    g = defaultdict(lambda: defaultdict(list))
    for r in comp:
        need = max(1, int(r["needles_total"]))
        k = (r["policy"], int(r["budget"]))
        g[k]["recall"].append(int(r["probe"]) / need)
        g[k]["tok"].append(int(r["tokens_total"]))
    return {k: (st.mean(a["recall"]),
                st.pstdev(a["recall"]) if len(a["recall"]) > 1 else 0.0,
                st.mean(a["tok"])) for k, a in g.items()}


def _save(fig, stem):
    figstyle.save(fig, OUT / f"{stem}.pdf")
    fig.savefig(OUT / f"{stem}.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def fig_pareto(comp):
    figstyle.apply(seed=42)
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    agg = agg_comp(comp)
    for pol in sorted({k[0] for k in agg}):
        pts = sorted((t, r, sd, b) for (p, b), (r, sd, t) in agg.items() if p == pol)
        ax.errorbar([p[0] for p in pts], [p[1] for p in pts], yerr=[p[2] for p in pts],
                    marker="o", capsize=3, color=figstyle.POLICY_COLORS.get(pol), label=pol)
        for t, r, sd, b in pts:
            ax.annotate(f"B={b}", (t, r), fontsize=7, xytext=(4, 4), textcoords="offset points")
    figstyle.finish(ax, "Tokens billed (count)", "Probe recall rate (fraction)",
                    title="Quality vs cost by compaction policy (8b dev)")
    _save(fig, "EXP-001_pareto_v1")


def fig_recall_bars(comp):
    figstyle.apply(seed=42)
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    agg = agg_comp(comp)
    policies = ["truncate", "recency", "importance", "semantic"]
    budgets = sorted({k[1] for k in agg})
    x = np.arange(len(policies))
    w = 0.8 / max(1, len(budgets))
    colors = figstyle.sequential(len(budgets))
    for i, b in enumerate(budgets):
        ys = [agg.get((p, b), (0, 0, 0))[0] for p in policies]
        es = [agg.get((p, b), (0, 0, 0))[1] for p in policies]
        ax.bar(x + i * w, ys, w, yerr=es, capsize=2, color=colors[i], label=f"B={b}")
    ax.set_xticks(x + w * (len(budgets) - 1) / 2)
    ax.set_xticklabels(policies)
    figstyle.finish(ax, "Compaction policy (category)", "Probe recall rate (fraction)",
                    title="Needle recall by policy and budget (8b dev)")
    _save(fig, "EXP-001_recall_by_policy_v1")


def fig_baseline(base):
    figstyle.apply(seed=42)
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    bg = defaultdict(list)
    for r in base:
        need = max(1, int(r["needles_total"]))
        bg[int(r["run_length"])].append(int(r["probe"]) / need)
    xs = sorted(bg)
    ax.plot(xs, [st.mean(bg[L]) for L in xs], marker="s",
            color=figstyle.POLICY_COLORS["baseline"], label="no-compaction baseline")
    figstyle.finish(ax, "Run length (sources)", "Probe recall rate (fraction)",
                    title="Baseline recall vs context length (8b dev)")
    _save(fig, "EXP-001_baseline_recall_v1")


if __name__ == "__main__":
    comp, base = load()
    OUT.mkdir(parents=True, exist_ok=True)
    fig_pareto(comp)
    fig_recall_bars(comp)
    if base:
        fig_baseline(base)
    print(f"figures -> {OUT}")
