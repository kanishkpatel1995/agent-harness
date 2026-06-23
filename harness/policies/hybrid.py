"""reversible_hybrid — keep the summary in the window AND the raw in the store.
Architecture: HYBRID (the novel arm).

Literally Externalize + Recency composed: push the raw old turns to the store
(so the exact fact is recoverable) and also drop a summary in the window (so the
gist is cheap and in-context). Every other policy keeps ONE thing; this keeps
both — which is why it's never the single best but never in the loser group.
"""

from __future__ import annotations

from .base import summarize, text


class ReversibleHybrid:
    name = "reversible_hybrid"
    architecture = "hybrid"
    retrieves = True
    decision = "Summarize the old turns into the window AND push the raw to the store; retrieve raw at answer time."
    tradeoff = "Hedges both ways (gist + exact fact) — the priciest of the cheap tier, but it never face-plants."
    result = "Top group in EVERY task x model cell — the only arm that is. Robust, not peak."

    def compact(self, old, llm, store):
        for m in old:
            store.add(text(m))
        s, u = summarize(llm, old)
        return [{"role": "system", "content": "[COMPACTED — raw also stored]\n" + s}], u
