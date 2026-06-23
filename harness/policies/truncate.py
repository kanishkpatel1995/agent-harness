"""truncate — drop the oldest turns. Architecture: TRUNCATE (the cost floor)."""

from __future__ import annotations

from .base import ZERO


class Truncate:
    name = "truncate"
    architecture = "truncate"
    retrieves = False
    decision = "Keep the most recent turns; drop everything older. No LLM call."
    tradeoff = "Cheapest possible — but an old fact, once dropped, is gone for good."
    result = "FRAMES-8B 0.37 · the floor. (LangGraph's trim_messages is exactly this.)"

    def compact(self, old, llm, store):
        return [{"role": "system", "content": f"[{len(old)} earlier turns dropped]"}], dict(ZERO)
