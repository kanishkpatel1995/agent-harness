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


def _boot_ci(vals, n_boot=4000, seed=42):
    import random
    rng = random.Random(seed)
    N = len(vals)
    boots = sorted(sum(vals[rng.randrange(N)] for _ in range(N)) / N for _ in range(n_boot))
    return boots[int(0.025 * n_boot)], boots[int(0.975 * n_boot)]


def _acc_by_policy(results_csv):
    g = defaultdict(list)
    for r in csv.DictReader(results_csv.open()):
        g[r["policy"]].append(int(r["correct"]))
    return {p: (st.mean(v), *_boot_ci(v)) for p, v in g.items() if v}  # mean, lo, hi


def _manifest_model(rundir):
    import re
    mf = rundir / "manifest.yaml"
    for line in (mf.read_text().splitlines() if mf.exists() else []):
        m = re.match(r"\s*model:\s*(\S+)", line)
        if m:
            return m.group(1)
    return None


def _pick(glob, model_key):
    """The run dir matching model_key with the most result rows, so a complete run beats a
    partial one and a larger-N rerun upgrades the figure automatically."""
    best, best_n = None, -1
    for d in sorted(RUNS.glob(glob)):
        rc = d / "results.csv"
        if rc.exists() and (_manifest_model(d) or "") == model_key:
            n = sum(1 for _ in rc.open()) - 1
            if n > best_n:
                best, best_n = rc, n
    if best is None:
        raise SystemExit(f"no run for {glob} model={model_key}")
    return best


def main():
    M8 = "meta/llama-3.1-8b-instruct"
    frames = _acc_by_policy(_pick("EXP-003b__*", M8))   # FRAMES, 8b, high pressure
    locomo = _acc_by_policy(_pick("EXP-004__*", M8))    # LoCoMo, 8b

    print("\n=== EXP-004: cross-domain transfer (8b, judged, 95% bootstrap CI) ===")
    print(f"{'arm':<18}{'FRAMES':>18}{'LoCoMo':>18}")
    for p in ARMS:
        f, l = frames.get(p), locomo.get(p)
        fs = f"{f[0]:.2f} [{f[1]:.2f},{f[2]:.2f}]" if f else "-"
        ls = f"{l[0]:.2f} [{l[1]:.2f},{l[2]:.2f}]" if l else "-"
        print(f"{p:<18}{fs:>18}{ls:>18}")

    figstyle.apply(seed=42)
    fig, ax = plt.subplots(figsize=(7.0, 4.8))
    for pol in ARMS:
        if pol not in frames or pol not in locomo:
            continue
        ys = [frames[pol][0], locomo[pol][0]]
        los = [ys[0] - frames[pol][1], ys[1] - locomo[pol][1]]
        his = [frames[pol][2] - ys[0], locomo[pol][2] - ys[1]]
        ax.errorbar([0, 1], ys, yerr=[los, his], marker="o", markersize=7, linewidth=1.8,
                    capsize=3, elinewidth=1.0,
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
