"""LangChainSummary — wrap LangChain's ConversationSummaryBufferMemory as a
COMPACT policy, so the framework's shipped default is just another bench arm.

This is the head-to-head the talk promises: does LangChain's summary-buffer beat
our 15-line `recency`? Architecturally they're identical — a rolling summary plus
a recent buffer, flushed by token length. (ConversationSummaryBufferMemory is
deprecated as of LangChain 0.3.1; the modern equivalent is a LangGraph
summarization node, which wires the same way — feed turns in, read summary out.)

    pip install langchain langchain-openai
    LangChainSummary(lc_llm=ChatOpenAI(model="gpt-4o-mini"))
"""

from __future__ import annotations

try:
    from langchain.memory import ConversationSummaryBufferMemory
except Exception:  # pragma: no cover - optional dep / moved in 1.x
    ConversationSummaryBufferMemory = None

from ..base import ZERO, text


class LangChainSummary:
    name = "langchain_summary"
    architecture = "compact"
    retrieves = False
    decision = "Use LangChain's ConversationSummaryBufferMemory: a rolling summary + recent buffer, flushed by token length."
    tradeoff = "The literal framework default — same summary blur as our recency, plus a framework dependency. The point is to measure it, not assume it."
    result = "Baseline arm: does the shipped default beat 15 hand-rolled lines? (Bench it.)"

    def __init__(self, lc_llm=None, max_token_limit: int = 256):
        if ConversationSummaryBufferMemory is None:
            raise ImportError("pip install langchain langchain-openai")
        if lc_llm is None:
            raise ValueError("pass a LangChain chat model, e.g. ChatOpenAI(model='gpt-4o-mini')")
        self.mem = ConversationSummaryBufferMemory(
            llm=lc_llm, max_token_limit=max_token_limit, return_messages=False)

    def compact(self, old, llm, store):
        # feed the evicted turns into LangChain's memory, then read back the
        # summary + buffer it produces — exactly how you'd use it in an LC app.
        for m in old:
            self.mem.save_context({"input": text(m)}, {"output": ""})
        history = self.mem.load_memory_variables({}).get("history", "")
        return [{"role": "system", "content": "[LANGCHAIN SUMMARY-BUFFER]\n" + str(history)}], dict(ZERO)
