#!/usr/bin/env python3
"""Policy-taxonomy diagram: the eight compaction policies as a 2D map, annotated with the
production frameworks that ship each (grounded in Table 1 of the paper).

Axes: what survives in the window (rows: recent raw turns -> free-text summary -> structured
facts) x whether dropped content is recoverable from a store (cols: lossy -> retrievable). The
story the figure tells: the widely-deployed defaults sit in the lossy column (truncate, recency),
the most capable production stacks live in the retrievable column (externalize, reversible
hybrid, structured/graph), and our reversible_hybrid is the cell those stacks converge on.

    python -m experiments.make_figures_taxonomy
"""

from __future__ import annotations

from experiments import figstyle

# Explicit (x, y) so nothing overlaps. Left column = lossy, right column = retrievable.
# Vertical position tracks the in-window artifact: raw (bottom) -> summary -> structured (top).
CW, CH = 3.7, 1.18
CELLS = [
    (0.0, 0.0, "truncate", "truncate",
     "LangChain window,\nOpenAI last_messages, Anthropic clear-tools", "#999999"),
    (0.0, 1.55, "importance", "importance",
     "Generative Agents (scoring half)", "#D55E00"),
    (0.0, 3.30, "recency", "recency",
     "LangChain summary-buffer,\nClaude auto-compact, OpenAI compaction", "#0072B2"),
    (0.0, 5.05, "semantic", "semantic", "(topic-cluster summary)", "#009E73"),
    (0.0, 6.60, "subagent", "subagent", "Claude Code sub-agents", "#CC79A7"),
    (4.5, 0.78, "externalize", "externalize",
     "BabyAGI, HippoRAG,\nGen. Agents memory stream", "#56B4E9"),
    (4.5, 3.55, "reversible_hybrid", "reversible hybrid (ours)",
     "MemGPT, Letta, AutoGPT, Cognee", "#009E73"),
    (4.5, 6.30, "structured", "structured / graph",
     "Mem0, Zep / Graphiti,\nHippoRAG, Cognee", "#E69F00"),
]
COL_LABELS = ["dropped, not recoverable (lossy)", "paged to a store, recoverable (lossless)"]


def main():
    figstyle.apply()
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    fig, ax = plt.subplots(figsize=(9.0, 6.2))
    for x, y, key, title, fws, color in CELLS:
        ours = "ours" in title
        box = FancyBboxPatch((x, y), CW, CH, boxstyle="round,pad=0.02,rounding_size=0.10",
                             linewidth=1.8 if ours else 0.9,
                             edgecolor="#111111" if ours else "#555555",
                             facecolor=color, alpha=0.24)
        ax.add_patch(box)
        ax.text(x + CW / 2, y + CH - 0.33, title, ha="center", va="center",
                fontsize=10.5, fontweight="bold")
        ax.text(x + CW / 2, y + 0.34, fws, ha="center", va="center", fontsize=7.7, color="#333333")

    ax.set_xlim(-1.9, 8.6)
    ax.set_ylim(-1.3, 8.5)
    for j, lab in enumerate(COL_LABELS):
        ax.text(j * 4.5 + CW / 2, 8.1, lab, ha="center", va="center", fontsize=9.5,
                fontweight="bold", color="#222222")
    # vertical artifact-richness arrow + label
    ax.annotate("", xy=(-1.5, 7.6), xytext=(-1.5, -0.1),
                arrowprops=dict(arrowstyle="->", color="#777777", lw=1.0))
    ax.text(-1.78, 3.8, "richer in-window artifact  (raw -> summary -> structured)",
            ha="center", va="center", fontsize=8.5, rotation=90, color="#777777")
    ax.annotate("", xy=(8.4, -1.05), xytext=(-0.2, -1.05),
                arrowprops=dict(arrowstyle="->", color="#777777", lw=1.0))
    ax.text(4.0, -1.28, "increasing recoverability of dropped content", ha="center",
            fontsize=8.5, color="#777777")
    ax.axis("off")
    p = figstyle.save(fig, "presentation/figures/policy_taxonomy_v1.pdf")
    fig.savefig(str(p).replace(".pdf", ".png"), dpi=200, bbox_inches="tight")
    print("saved png too")


if __name__ == "__main__":
    main()
