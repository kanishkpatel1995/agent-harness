"""EXP-003b figure: LLM-judged accuracy vs mean tokens, by policy, high pressure.

The first full 7-arm applied bake-off. One point per policy with a binomial
standard-error bar. Marks the Pareto frontier. Publication style via figstyle.

    python experiments/make_figures_exp003b.py [results.csv]
"""

from __future__ import annotations

import csv
import math
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from experiments import figstyle  # noqa: E402

OUT = Path("presentation/figures")


def _latest():
    runs = sorted(Path("experiments/runs").glob("EXP-003b__*/results.csv"))
    if not runs:
        raise SystemExit("no EXP-003b run found")
    return runs[-1]


def main():
    p = Path(sys.argv[1]) if len(sys.argv) > 1 else _latest()
    rows = list(csv.DictReader(p.open()))
    g = defaultdict(lambda: {"c": [], "t": []})
    for r in rows:
        g[r["policy"]]["c"].append(int(r["correct"]))
        g[r["policy"]]["t"].append(int(r["tokens_total"]))

    figstyle.apply(seed=42)
    fig, ax = plt.subplots(figsize=(6.8, 4.6))
    for pol in ["truncate", "recency", "importance", "semantic",
                "externalize", "reversible_hybrid", "subagent"]:
        if pol not in g:
            continue
        acc = st.mean(g[pol]["c"])
        tok = st.mean(g[pol]["t"])
        n = len(g[pol]["c"])
        se = math.sqrt(max(acc * (1 - acc), 1e-9) / n)
        ax.errorbar([tok], [acc], yerr=[se], marker="o", markersize=9, capsize=4,
                    color=figstyle.POLICY_COLORS.get(pol, "#444444"))
        ax.annotate(pol, (tok, acc), fontsize=8, xytext=(7, 4), textcoords="offset points")
    ax.set_xscale("log")
    ax.set_ylim(0.3, 0.65)
    figstyle.finish(ax, "Tokens billed, log scale (count)",
                    "Answer accuracy, LLM-judged (fraction)",
                    title="FRAMES bake-off: accuracy vs cost (8b, high pressure, judged)")
    OUT.mkdir(parents=True, exist_ok=True)
    figstyle.save(fig, OUT / "EXP-003b_pareto_v1.pdf")
    fig.savefig(OUT / "EXP-003b_pareto_v1.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("rendered EXP-003b_pareto_v1.{pdf,png}")


if __name__ == "__main__":
    main()
