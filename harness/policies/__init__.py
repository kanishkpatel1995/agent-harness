"""The policy package — seven ways to forget, one interface.

    from harness.policies import POLICIES
    POLICIES["reversible_hybrid"].compact(old, llm, store)

Each policy is one file next to this one, tagged with its `architecture`
(truncate · compact · externalize · isolate · hybrid), the `decision` it makes,
the `tradeoff`, and its bench `result`. Open them side by side — that's the talk.
See ../../docs/ARCHITECTURES.md for the map and the OSS systems on it.
"""

from __future__ import annotations

from .base import Policy, summarize, text  # noqa: F401
from .store import Store  # noqa: F401
from .truncate import Truncate
from .recency import Recency
from .importance import Importance
from .semantic import Semantic
from .externalize import Externalize
from .subagent import Subagent
from .hybrid import ReversibleHybrid

_ARMS = [Truncate(), Recency(), Importance(), Semantic(),
         Externalize(), Subagent(), ReversibleHybrid()]

POLICIES = {p.name: p for p in _ARMS}

# architecture -> the policies that implement it (for the tour / deck)
ARCHITECTURES = {
    "truncate": ["truncate"],
    "compact": ["recency", "importance", "semantic"],
    "externalize": ["externalize"],
    "isolate": ["subagent"],
    "hybrid": ["reversible_hybrid"],
}

__all__ = ["POLICIES", "ARCHITECTURES", "Policy", "Store", "summarize", "text"]
