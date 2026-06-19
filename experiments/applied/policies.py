"""The four applied compaction policies for EXP-003a.

Common interface: compact(old, llm, store) returns (replacement_block, usage).
The `retrieves` flag tells the agent whether to pull from the store at answer time.

  truncate           : drop the old turns. No store, no retrieval.
  recency            : one summary in the window. No store.
  externalize        : drop from window, push raw to store, retrieve at answer.
  reversible_hybrid  : summary in window AND raw pushed to store + retrieve at
                       answer. The novel arm: lossy summary plus reversible raw.
"""

from __future__ import annotations

from experiments.policies import _summarize, _text, ZERO
from experiments.bench.logsetup import get

log = get("policy")


class Truncate:
    name = "truncate"
    retrieves = False

    def compact(self, old, llm, store):
        return [{"role": "system", "content": f"[{len(old)} earlier turns dropped]"}], dict(ZERO)


class Recency:
    name = "recency"
    retrieves = False

    def compact(self, old, llm, store):
        s, u = _summarize(llm, old)
        return [{"role": "system", "content": "[COMPACTED]\n" + s}], u


class Externalize:
    name = "externalize"
    retrieves = True

    def compact(self, old, llm, store):
        for m in old:
            t = _text(m)
            if t:
                store.add(t)
        return [{"role": "system", "content":
                 f"[{len(old)} earlier turns moved to the store; retrievable on demand]"}], dict(ZERO)


class ReversibleHybrid:
    name = "reversible_hybrid"
    retrieves = True

    def compact(self, old, llm, store):
        for m in old:
            t = _text(m)
            if t:
                store.add(t)
        s, u = _summarize(llm, old)
        return [{"role": "system", "content": "[COMPACTED, raw also stored]\n" + s}], u


POLICIES = {p.name: p for p in [Truncate(), Recency(), Externalize(), ReversibleHybrid()]}
