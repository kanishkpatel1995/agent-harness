"""externalize — drop the old turns from the window, push the raw text to the
store, retrieve at answer time. Architecture: EXTERNALIZE.

This is the RAG / MemGPT-archival / Mem0 family: the window holds a pointer, the
bytes live in a store, and you pull the relevant ones back when you need them.
"""

from __future__ import annotations

from .base import ZERO, text


class Externalize:
    name = "externalize"
    architecture = "externalize"
    retrieves = True
    decision = "Move the raw old turns to the store; keep only a pointer in the window; retrieve at answer time."
    tradeoff = "Keeps the literal fact (no summary blur) — but depends on retrieval hitting, and carries no compressed reasoning chain."
    result = "FRAMES-8B 0.40 · the winner on memory tasks (LoCoMo), where exact scattered facts matter."

    def compact(self, old, llm, store):
        for m in old:
            store.add(text(m))
        return [{"role": "system",
                 "content": f"[{len(old)} earlier turns moved to the store; retrievable on demand]"}], dict(ZERO)
