"""EXP-004 model-axis figure: does capability change the LoCoMo ranking?

A two-column slope chart, 8B on the left and 70B on the right, one line per compaction
arm, on LoCoMo (conversational memory). The mirror of the FRAMES model axis (EXP-003c):
there, capability lifted the summary arms; here we expect it not to, because the LoCoMo
bottleneck is the summary dropping specific facts, which no model fixes. Both runs come
from the EXP-004 run dirs, keyed to each run's config.model.

    python experiments/make_figures_exp004_modelaxis.py
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
ARMS = ["truncate", "externalize", "importance", "semantic", "reversible_hybrid"]
MODEL_ORDER = [
    ("meta/llama-3.1-8b-instruct", "Llama 3.1 8B\n(small instruct)"),
    ("meta/llama-3.3-70b-instruct", "Llama 3.3 70B\n(large instruct)"),
]


def _manifest_model(rundir):
    mf = rundir / "manifest.yaml"
    for line in (mf.read_text().splitlines() if mf.exists() else []):
        m = re.match(r"\s*model:\s*(\S+)", line)
        if m:
            return m.group(1)
    return None


def _acc(results_csv):
    g = defaultdict(list)
    for r in csv.DictReader(results_csv.open()):
        g[r["policy"]].append(int(r["correct"]))
    return {p: (st.mean(v), *_boot_ci(v)) for p, v in g.items() if v}  # mean, lo, hi


def _boot_ci(vals, n_boot=4000, seed=42):
    import random
    rng = random.Random(seed)
    N = len(vals)
    boots = sorted(sum(vals[rng.randrange(N)] for _ in range(N)) / N for _ in range(n_boot))
    return boots[int(0.025 * n_boot)], boots[int(0.975 * n_boot)]


def main():
    data = {}
    for rundir in sorted(RUNS.glob("EXP-004__*")):
        rc = rundir / "results.csv"
        if not rc.exists():
            continue
        model = _manifest_model(rundir)
        if model:
            data[model] = _acc(rc)  # later (newer) run wins for a given model

    present = [(mid, lab) for mid, lab in MODEL_ORDER if mid in data]
    if len(present) < 2:
        raise SystemExit("need both the 8b and 70b LoCoMo runs")

    print("\n=== EXP-004 LoCoMo model axis (judged accuracy) ===")
    print(f"{'arm':<18}" + "".join(lab.replace(chr(10), ' ')[:14].rjust(16) for _, lab in present))
    for p in ARMS:
        print(f"{p:<18}" + "".join((f"{data[mid][p][0]:.2f}" if p in data[mid] else "-").rjust(16)
                                    for mid, _ in present))

    figstyle.apply(seed=42)
    fig, ax = plt.subplots(figsize=(7.0, 4.8))
    xs = list(range(len(present)))
    for pol in ARMS:
        cells = [data[mid].get(pol) for mid, _ in present]
        if any(c is None for c in cells):
            continue
        ys = [c[0] for c in cells]
        los = [c[0] - c[1] for c in cells]
        his = [c[2] - c[0] for c in cells]
        ax.errorbar(xs, ys, yerr=[los, his], marker="o", markersize=7, linewidth=1.8,
                    capsize=3, elinewidth=1.0,
                    color=figstyle.POLICY_COLORS.get(pol, "#444444"), label=pol)
    ax.set_xticks(xs)
    ax.set_xticklabels([lab for _, lab in present])
    ax.set_xlim(-0.25, len(present) - 1 + 0.25)
    ax.set_ylim(0.0, 0.65)
    figstyle.finish(ax, "Agent model (increasing capability)",
                    "Answer accuracy, LLM-judged (fraction)",
                    title="LoCoMo: capability does not rescue summarization")
    OUT.mkdir(parents=True, exist_ok=True)
    figstyle.save(fig, OUT / "EXP-004_modelaxis_v1.pdf")
    fig.savefig(OUT / "EXP-004_modelaxis_v1.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("\nrendered EXP-004_modelaxis_v1.{pdf,png}")


if __name__ == "__main__":
    main()
