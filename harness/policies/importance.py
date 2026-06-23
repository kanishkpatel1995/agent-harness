"""importance — keep the highest-signal turns verbatim, summarize the rest.
Architecture: COMPACT (selective). The structure-preserving move."""

from __future__ import annotations

import re

from .base import ZERO, summarize, text


class Importance:
    name = "importance"
    architecture = "compact"
    retrieves = False
    decision = "Score each turn by signal (numbers, names, URLs); keep the top few verbatim, summarize the rest."
    tradeoff = "Keeps exact facts a summary would smooth away — at the cost of a heuristic and more tokens."
    result = "FRAMES-8B 0.50 · accuracy leader on factual tasks; collapses on memory tasks."

    def __init__(self, keep: int = 2):
        self.keep = keep

    def _score(self, m) -> int:
        t = text(m)
        return (
            len(re.findall(r"\d", t))
            + 3 * len(re.findall(r"https?://", t))
            + 2 * len(re.findall(r"[A-Z][a-z]+-?\d", t))
        )

    def compact(self, old, llm, store):
        order = sorted(range(len(old)), key=lambda i: self._score(old[i]), reverse=True)
        keep = set(order[: self.keep])
        block = [
            {"role": "system", "content": "[KEPT verbatim — high signal]\n" + text(old[i])}
            for i in sorted(keep)
        ]
        rest = [old[i] for i in range(len(old)) if i not in keep]
        usage = dict(ZERO)
        if rest:
            s, usage = summarize(llm, rest)
            block.append({"role": "system", "content": "[COMPACTED rest]\n" + s})
        return block, usage
