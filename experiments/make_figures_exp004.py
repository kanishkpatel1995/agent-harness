"""EXP-004 figure: does the compaction ranking transfer across task types?

A two-column slope chart, FRAMES (multi-hop factual QA) on the left and LoCoMo
(conversational memory) on the right, one line per compaction arm, both on the 8b agent.
Lines that cross show the ranking inverting between domains: summary arms lead on FRAMES
and fall on LoCoMo, retrieval arms do the opposite, and the reversible hybrid stays in the
top group on both. FRAMES numbers come from the EXP-003b run; LoCoMo from EXP-004.

    python experiments/make_figures_exp004.py
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
RUNS = Path("experiments/runs")
ARMS = ["truncate", "externalize", "importance", "semantic", "reversible_hybrid"]


def _acc_by_policy(results_csv):
    g = defaultdict(list)
    for r in csv.DictReader(results_csv.open()):
        g[r["policy"]].append(int(r["correct"]))
    return {p: st.mean(v) for p, v in g.items() if v}


def _latest(glob):
    runs = sorted(RUNS.glob(glob))
    if not runs:
        raise SystemExit(f"no run found for {glob}")
    return runs[-1] / "results.csv"


def main():
    frames = _acc_by_policy(_latest("EXP-003b__*"))   # FRAMES, 8b, high pressure
    locomo = _acc_by_policy(_latest("EXP-004__*"))     # LoCoMo, 8b

    print("\n=== EXP-004: cross-domain transfer (8b, judged) ===")
    print(f"{'arm':<18}{'FRAMES':>10}{'LoCoMo':>10}")
    for p in ARMS:
        print(f"{p:<18}{frames.get(p, float('nan')):>10.2f}{locomo.get(p, float('nan')):>10.2f}")

    figstyle.apply(seed=42)
    fig, ax = plt.subplots(figsize=(7.0, 4.8))
    for pol in ARMS:
        if pol not in frames or pol not in locomo:
            continue
        ax.plot([0, 1], [frames[pol], locomo[pol]], marker="o", markersize=8, linewidth=1.8,
                color=figstyle.POLICY_COLORS.get(pol, "#444444"), label=pol)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["FRAMES\n(multi-hop factual)", "LoCoMo\n(conversational memory)"])
    ax.set_xlim(-0.25, 1.25)
    ax.set_ylim(0.05, 0.65)
    figstyle.finish(ax, "Task domain", "Answer accuracy, LLM-judged (fraction)",
                    title="Does the compaction ranking transfer across task types?")
    OUT.mkdir(parents=True, exist_ok=True)
    figstyle.save(fig, OUT / "EXP-004_transfer_v1.pdf")
    fig.savefig(OUT / "EXP-004_transfer_v1.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("\nrendered EXP-004_transfer_v1.{pdf,png}")


if __name__ == "__main__":
    main()
