"""semantic — cluster the old turns by topic, summarize each cluster.
Architecture: COMPACT (structure-preserving)."""

from __future__ import annotations

import hashlib
import re

from .base import ZERO, summarize, text


class Semantic:
    name = "semantic"
    architecture = "compact"
    retrieves = False
    decision = "Group the old turns by topic, then summarize each group — one note per theme."
    tradeoff = "Preserves the shape of the work better than one flat summary; costs one LLM call per cluster."
    result = "FRAMES-8B 0.57 · accuracy ceiling on factual reasoning; still loses exact scattered facts."

    def __init__(self, groups: int = 2):
        self.groups = groups

    def _bucket(self, m) -> int:
        # Stable hash (not python hash(), which is salted per process). A crude
        # stand-in for embedding clusters; swap in real embeddings to go deeper.
        h = hashlib.md5(re.sub(r"\d", "", text(m)[:60]).encode()).hexdigest()
        return int(h, 16) % self.groups

    def compact(self, old, llm, store):
        buckets: dict[int, list] = {}
        for m in old:
            buckets.setdefault(self._bucket(m), []).append(m)
        block, total = [], dict(ZERO)
        for b, msgs in sorted(buckets.items()):
            s, u = summarize(llm, msgs)
            total = {k: total[k] + u.get(k, 0) for k in total}
            block.append({"role": "system", "content": f"[TOPIC {b}]\n" + s})
        return block, total
