"""recency — one rolling summary of the stale middle. Architecture: COMPACT.

This is the policy that ships by default in real harnesses: LangChain's
ConversationSummaryBufferMemory (and the LangGraph summarization node) are this
exact move — a summary of the old turns plus the recent ones. The bench's
surprise is that under pressure it loses to plain truncation.
"""

from __future__ import annotations

from .base import summarize


class Recency:
    name = "recency"
    architecture = "compact"
    retrieves = False
    decision = "Summarize ALL the old turns into one note; keep it plus the recent turns."
    tradeoff = "The shipped default (LangChain summary-buffer). One LLM call — but the exact fact gets blurred into the summary."
    result = "FRAMES-8B 0.37 · Pareto-dominated by truncate under pressure (7x the cost, no gain)."

    def compact(self, old, llm, store):
        s, u = summarize(llm, old)
        return [{"role": "system", "content": "[COMPACTED]\n" + s}], u
