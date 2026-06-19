"""Render the EXP-002 length-degradation figure: needle recall vs context length.

Shows the no-compaction baseline degrading as context grows while summary-based
compaction holds flat. The crossover (around L=16) is where compaction becomes
net-positive, not just survival. Publication style via figstyle.

    python experiments/make_figures_exp002.py [results.csv]
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

from experiments import figstyle  # noqa: E402

OUT = Path("presentation/figures")


def _latest():
    runs = sorted(Path("experiments/runs").glob("EXP-002__*/results.csv"))
    if not runs:
        raise SystemExit("no EXP-002 run found")
    return runs[-1]


def main():
    p = Path(sys.argv[1]) if len(sys.argv) > 1 else _latest()
    rows = list(csv.DictReader(p.open()))
    g = defaultdict(lambda: defaultdict(list))
    for r in rows:
        key = "baseline" if r["arm"] == "baseline" else r["policy"]
        need = max(1, int(r["needles_total"]))
        g[key][int(r["run_length"])].append(int(r["probe"]) / need)

    figstyle.apply(seed=42)
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    for key in ["baseline", "truncate", "recency", "semantic"]:
        if key not in g:
            continue
        xs = sorted(g[key])
        ys = [st.mean(g[key][L]) for L in xs]
        label = "no-compaction baseline" if key == "baseline" else key
        ax.plot(xs, ys, marker="o", label=label, color=figstyle.POLICY_COLORS.get(key))
    ax.set_ylim(0, 1)
    figstyle.finish(ax, "Run length (sources read)", "Needle recall rate (fraction)",
                    title="Compaction holds as context grows; no-compaction degrades (8b)")
    OUT.mkdir(parents=True, exist_ok=True)
    figstyle.save(fig, OUT / "EXP-002_recall_vs_length_v1.pdf")
    fig.savefig(OUT / "EXP-002_recall_vs_length_v1.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("rendered EXP-002_recall_vs_length_v1.{pdf,png}")


if __name__ == "__main__":
    main()
