"""EXP-003c figure: the model axis.

Does the EXP-003b policy ranking hold as the agent model gets stronger? We plot
LLM-judged FRAMES accuracy for each compaction arm across three model tiers, so a
line that stays flat means the policy is model-robust and lines that cross mean the
ranking reorders with capability. The 8b numbers come from the EXP-003b high-pressure
run; the 70b and reasoning numbers come from the EXP-003c run dirs. Each run is keyed
to its model by the manifest's config.model field. Renders whatever tiers exist, so it
is safe to run mid-experiment. Publication style via figstyle.

    python experiments/make_figures_exp003c.py
"""

from __future__ import annotations

import csv
import re
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

# The model axis, in capability order. Label is what appears on the x-axis.
MODEL_ORDER = [
    ("meta/llama-3.1-8b-instruct", "Llama 3.1 8B\n(small instruct)"),
    ("meta/llama-3.3-70b-instruct", "Llama 3.3 70B\n(large instruct)"),
    ("nvidia/nemotron-3-nano-30b-a3b", "Nemotron 30B-A3B\n(reasoning)"),
]
# The five arms that separated in EXP-003b and carry across the model axis.
ARMS = ["truncate", "externalize", "importance", "semantic", "reversible_hybrid"]


def _manifest_model(rundir):
    """Pull config.model from a run's manifest (first top-level 'model:' line;
    'judge_model:' does not match the anchor)."""
    mf = rundir / "manifest.yaml"
    if not mf.exists():
        return None
    for line in mf.read_text().splitlines():
        m = re.match(r"\s*model:\s*(\S+)", line)
        if m:
            return m.group(1)
    return None


def _acc_by_policy(results_csv):
    g = defaultdict(list)
    for r in csv.DictReader(results_csv.open()):
        g[r["policy"]].append(int(r["correct"]))
    return {p: st.mean(v) for p, v in g.items() if v}, {p: len(v) for p, v in g.items()}


def collect():
    """model -> {policy -> (accuracy, n)} from every EXP-003b/EXP-003c run dir."""
    data = defaultdict(dict)
    for rundir in sorted(RUNS.glob("EXP-003b__*")) + sorted(RUNS.glob("EXP-003c__*")):
        rc = rundir / "results.csv"
        if not rc.exists():
            continue
        model = _manifest_model(rundir)
        if not model:
            continue
        acc, n = _acc_by_policy(rc)
        for p, a in acc.items():
            # Later run dirs win (resumed/complete runs overwrite partials).
            data[model][p] = (a, n[p])
    return data


def main():
    data = collect()
    present = [(mid, lab) for mid, lab in MODEL_ORDER if mid in data]
    if not present:
        raise SystemExit("no EXP-003b/003c run data found yet")

    xs = list(range(len(present)))
    xlabels = [lab for _, lab in present]
    print("\n=== EXP-003c: model axis (judged accuracy by arm) ===")
    header = "arm".ljust(18) + "".join(lab.replace("\n", " ")[:14].rjust(16) for _, lab in present)
    print(header)

    figstyle.apply(seed=42)
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    for pol in ARMS:
        ys, xpts, cells = [], [], []
        for x, (mid, _) in zip(xs, present):
            if pol in data[mid]:
                a, n = data[mid][pol]
                ys.append(a); xpts.append(x); cells.append(n)
        if not ys:
            continue
        ax.plot(xpts, ys, marker="o", markersize=8, linewidth=1.8,
                color=figstyle.POLICY_COLORS.get(pol, "#444444"), label=pol)
        row = pol.ljust(18) + "".join(
            (f"{data[mid][pol][0]:.2f} (n{data[mid][pol][1]})".rjust(16)
             if pol in data[mid] else "-".rjust(16))
            for mid, _ in present)
        print(row)

    ax.set_xticks(xs)
    ax.set_xticklabels(xlabels)
    ax.set_xlim(-0.3, len(present) - 1 + 0.9)  # room for right-side labels
    ax.set_ylim(0.2, 0.85)
    figstyle.finish(ax, "Agent model (increasing capability)",
                    "Answer accuracy, LLM-judged (fraction)",
                    title="FRAMES compaction: does the policy ranking hold across models?")
    OUT.mkdir(parents=True, exist_ok=True)
    figstyle.save(fig, OUT / "EXP-003c_modelaxis_v1.pdf")
    fig.savefig(OUT / "EXP-003c_modelaxis_v1.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("\nrendered EXP-003c_modelaxis_v1.{pdf,png}")


if __name__ == "__main__":
    main()
