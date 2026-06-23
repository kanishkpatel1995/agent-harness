"""The Policy contract — the seam every architecture plugs into.

A policy answers one question: when the window is over budget, what replaces the
old turns? That's the whole interface. Truncate drops them, recency summarizes
them, externalize stores them, subagent isolates them, hybrid does two at once.
Every arm — including the open-source memory systems wrapped in `adapters/` — is
the same five-line shape:

    compact(old, llm, store) -> (replacement_block, usage)

Read the seven files next to this one side by side; that's the talk.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

Message = dict
ZERO = {"prompt_tokens": 0, "completion_tokens": 0}

SUMMARY_PROMPT = (
    "Compress this agent transcript into a dense factual note. Preserve EVERY "
    "specific number, named term, date, and URL exactly as written. Drop chatter. "
    "Maximum 180 words."
)


def text(m: Message) -> str:
    return m.get("content") or ""


def summarize(llm, msgs):
    """One LLM call that compresses msgs -> (summary_text, usage).

    This is the single shared 'forgetting by compression' primitive. recency,
    importance, semantic, subagent, and hybrid all call it; truncate and
    externalize never do. Swapping the summarizer model swaps it everywhere.
    """
    transcript = "\n".join(f"[{m.get('role')}] {text(m)}" for m in msgs)[:12000]
    r = llm.complete([
        {"role": "system", "content": SUMMARY_PROMPT},
        {"role": "user", "content": transcript},
    ])
    return (getattr(r, "content", "") or "").strip(), getattr(r, "usage", dict(ZERO))


@runtime_checkable
class Policy(Protocol):
    name: str            # registry key
    architecture: str    # truncate | compact | externalize | isolate | hybrid
    retrieves: bool      # does the agent pull from the store at answer time?
    decision: str        # the one design choice this arm makes
    tradeoff: str        # what it gives up
    result: str          # headline bench number, for the tour

    def compact(self, old, llm, store):
        """Return (block, usage). `block` is the message(s) that replace `old`."""
        ...
