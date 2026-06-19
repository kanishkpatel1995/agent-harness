"""Founsi-brand matplotlib styling for every research figure in the deck.

So all appendix graphs share one look: off-white surface, purple-tinted grid,
ink text, the brand series colours, no top/right spines, and a small "Founsi."
wordmark in the corner.

    from presentation.brand.chart_style import apply, SERIES, save
    apply()
    fig, ax = plt.subplots()
    ax.plot(x, y, color=SERIES[0])
    save(fig, "presentation/figures/pareto.png")

Matplotlib is only needed when rendering figures (pip install matplotlib).
"""

from __future__ import annotations

PALETTE = {
    "purple": "#9378FF", "purple_dark": "#7B5EF0", "ink": "#2E2C32",
    "grey": "#655E74", "mid": "#7E7A8A", "light": "#A09DAC",
    "purple_light": "#D4C9FF", "purple_wash": "#E4DDFF", "purple_mist": "#EFEBFF",
    "bg": "#FAFAFE", "surface": "#FFFFFF",
    "green": "#2DA44E", "amber": "#D4880F", "red": "#E5534B",
}

# Ordered series colours. Map the four policies in a stable order so every
# figure uses the same colour for the same policy.
SERIES = ["#9378FF", "#2E2C32", "#655E74", "#7B5EF0", "#D4C9FF", "#D4880F"]
POLICY_COLORS = {
    "truncate": "#A09DAC",   # the floor — muted grey
    "recency": "#9378FF",    # brand purple — the default we test
    "importance": "#7B5EF0", # purple-dark
    "semantic": "#2E2C32",   # ink
    "baseline": "#E5534B",   # red — the no-compaction control / overflow risk
}


def apply():
    """Set Founsi brand rcParams. Call once before plotting."""
    import matplotlib as mpl

    mpl.rcParams.update({
        "figure.facecolor": PALETTE["bg"],
        "savefig.facecolor": PALETTE["bg"],
        "axes.facecolor": PALETTE["surface"],
        "axes.edgecolor": PALETTE["light"],
        "axes.labelcolor": PALETTE["ink"],
        "axes.titlecolor": PALETTE["ink"],
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.labelsize": 11,
        "text.color": PALETTE["ink"],
        "xtick.color": PALETTE["grey"],
        "ytick.color": PALETTE["grey"],
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "axes.grid": True,
        "grid.color": PALETTE["purple"],
        "grid.alpha": 0.12,
        "grid.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.family": "sans-serif",
        "font.sans-serif": ["Manrope", "DejaVu Sans", "Arial", "sans-serif"],
        "lines.linewidth": 2.4,
        "lines.markersize": 6,
        "legend.frameon": False,
        "legend.fontsize": 10,
        "figure.dpi": 140,
        "axes.prop_cycle": mpl.cycler(color=SERIES),
    })


def save(fig, path, wordmark=True):
    """Tight-layout, stamp a 'Founsi.' wordmark, and write the file."""
    from pathlib import Path

    fig.tight_layout()
    if wordmark:
        fig.text(0.99, 0.01, "Founsi", ha="right", va="bottom",
                 fontsize=10, fontweight="bold", color=PALETTE["ink"])
        fig.text(1.0, 0.01, ".", ha="right", va="bottom",
                 fontsize=10, fontweight="bold", color=PALETTE["purple"])
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
    print("saved", path)
