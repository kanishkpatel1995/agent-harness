"""Policy registry for the bench.

The four hand-rolled policies live in experiments/policies.py (transparent, so a
reviewer can see exactly what each does). Here we just select them by name and
expose a SEAM for a LangChain baseline arm — so the paper can say "we compared
against the framework default," with LangChain as a competitor to beat, not as
our infrastructure.
"""

from __future__ import annotations

from experiments.policies import Truncate, Recency, Importance, Semantic
from .logsetup import get

log = get("policy")

_BUILTIN = {p.name: p for p in [Truncate(), Recency(), Importance(), Semantic()]}


def build(names):
    """Return {name: policy_instance} for the requested names."""
    out = {}
    for n in names:
        if n in _BUILTIN:
            out[n] = _BUILTIN[n]
        elif n == "langchain_summary":
            p = _make_langchain()
            if p is not None:
                out[n] = p
        else:
            log.warning(f"unknown policy {n!r}, skipping")
    return out


def _make_langchain():
    """SEAM: LangChain's summary memory as a baseline arm. Skipped (with a clear
    message) until langchain is installed — keeps the bench runnable either way."""
    try:
        from langchain.memory import ConversationSummaryMemory  # noqa: F401
    except Exception:
        log.warning("langchain not installed; 'langchain_summary' arm skipped. "
                    "Install with: pip install langchain langchain-community")
        return None
    return _LangChainSummary()


class _LangChainSummary:
    name = "langchain_summary"

    def compact(self, old, llm):  # pragma: no cover — implemented when we add the arm
        raise NotImplementedError(
            "LangChain summary arm not implemented yet. Plan: wrap our NimLLM as a "
            "LangChain ChatModel and drive ConversationSummaryMemory over `old`."
        )
