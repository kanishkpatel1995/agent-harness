"""Publication-grade matplotlib styling — the house style for ALL data figures.

Spec (act as a Senior Academic Data Scientist, publication-ready figures):
  1. color-blind-friendly palette  — Okabe-Ito (qualitative), cividis (sequential)
  2. Times New Roman for all text   — graceful serif fallback if not installed
  3. no vertical gridlines; light horizontal gridlines at major ticks only
  4. legend upper-right, transparent background
  5. all axes labelled with units in parentheses, e.g. "Tokens billed (count)"
Constraints: deterministic (seeded), high-resolution PDF output.

Usage:
    from experiments import figstyle
    figstyle.apply(seed=42)
    fig, ax = plt.subplots()
    ax.plot(x, y, color=figstyle.POLICY_COLORS["recency"], label="recency")
    figstyle.finish(ax, "Tokens billed (count)", "Needle recall (facts)")
    figstyle.save(fig, run_dir / "figures" / "EXP-001_pareto_v1.pdf")

matplotlib is imported lazily, so importing this module never requires it.
"""

from __future__ import annotations

import random

# Okabe-Ito: the canonical color-blind-safe qualitative palette.
OKABE_ITO = ["#000000", "#E69F00", "#56B4E9", "#009E73",
             "#F0E442", "#0072B2", "#D55E00", "#CC79A7"]

# Stable per-policy colours (all color-blind safe) so a policy reads the same in
# every figure of the paper.
POLICY_COLORS = {
    "truncate": "#999999",    # grey — the floor
    "recency": "#0072B2",     # blue
    "importance": "#D55E00",  # vermillion
    "semantic": "#009E73",    # bluish green
    "baseline": "#CC79A7",    # reddish purple — the no-compaction control
}


def sequential(n):
    """n colours from a color-blind-safe SEQUENTIAL map (cividis), for ordered
    categories such as token budgets."""
    import matplotlib.cm as cm
    import numpy as np

    return [cm.cividis(x) for x in np.linspace(0.12, 0.88, max(1, n))]


def apply(seed: int = 42):
    """Set the publication rcParams and seed RNGs. Call once before plotting."""
    import matplotlib as mpl

    random.seed(seed)
    try:
        import numpy as np

        np.random.seed(seed)
    except Exception:
        pass

    mpl.rcParams.update({
        # (2) Times New Roman, with a graceful serif fallback chain
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Times", "Nimbus Roman", "DejaVu Serif", "serif"],
        "mathtext.fontset": "stix",
        "font.size": 11,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        # (3) horizontal gridlines only, light, at major ticks
        "axes.grid": True,
        "axes.grid.axis": "y",
        "axes.grid.which": "major",
        "grid.color": "#B0B0B0",
        "grid.linewidth": 0.5,
        "grid.alpha": 0.5,
        # clean spines
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#333333",
        "axes.linewidth": 0.8,
        # (4) legend upper-right, transparent
        "legend.loc": "upper right",
        "legend.frameon": False,
        "legend.fontsize": 10,
        # high-resolution output
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "axes.prop_cycle": mpl.cycler(color=OKABE_ITO),
    })


def finish(ax, xlabel: str, ylabel: str, title: str | None = None):
    """Set axis labels (caller MUST include units in parentheses) + the legend.

    Rule 5 is enforced softly: a warning fires if a label has no '(unit)'.
    """
    if "(" not in xlabel or "(" not in ylabel:
        import warnings

        warnings.warn("Axis labels must include units in parentheses, "
                      "e.g. 'Needle recall (facts)'.", stacklevel=2)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    if ax.get_legend_handles_labels()[0]:
        ax.legend(loc="upper right", framealpha=0.0)


def save(fig, path):
    """tight-layout and write a high-resolution PDF (rule: always vector PDF)."""
    from pathlib import Path

    fig.tight_layout()
    p = Path(path)
    if p.suffix.lower() != ".pdf":
        p = p.with_suffix(".pdf")
    p.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(p, format="pdf", bbox_inches="tight")
    print("saved", p)
    return p
