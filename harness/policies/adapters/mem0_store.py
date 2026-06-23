"""Mem0Memory — wrap Mem0 as an EXTERNALIZE policy.

Mem0's architecture is extract-then-update: an LLM distills salient *facts* from
each turn, compares them to what's stored (vector similarity), and decides
ADD / UPDATE / DELETE / NOOP — so the store holds deduped facts, not raw text.
That's the interesting contrast to our `externalize` (which stores raw chunks):
Mem0 pays an extraction LLM up front for a smaller, cleaner, contradiction-free
memory. Retrieve at answer time.

    pip install mem0ai
"""

from __future__ import annotations

try:
    from mem0 import Memory
except Exception:  # pragma: no cover - optional dep
    Memory = None

from ..base import ZERO, text


class Mem0Memory:
    name = "mem0"
    architecture = "externalize"
    retrieves = True
    decision = "Route evicted turns through Mem0: an LLM extracts + dedupes facts into a vector/graph store; retrieve at answer."
    tradeoff = "Compact, deduped, durable facts — at the cost of an extraction LLM call, and the nuance a raw copy would keep."
    result = "Externalize family: distilled facts vs raw chunks. (Bench it.)"

    def __init__(self, user_id: str = "harness", config: dict | None = None):
        if Memory is None:
            raise ImportError("pip install mem0ai")
        self.mem = Memory.from_config(config) if config else Memory()
        self.user_id = user_id

    def compact(self, old, llm, store):
        for m in old:
            t = text(m)
            if t.strip():
                self.mem.add(t, user_id=self.user_id)
        return [{"role": "system",
                 "content": f"[{len(old)} turns sent to Mem0; deduped facts retrievable]"}], dict(ZERO)

    def retrieve(self, query: str, k: int = 3) -> list[str]:
        """Called by the runner at answer time (mirrors store.search)."""
        res = self.mem.search(query, user_id=self.user_id, limit=k)
        items = res.get("results", res) if isinstance(res, dict) else res
        return [r.get("memory", "") if isinstance(r, dict) else str(r) for r in items]
