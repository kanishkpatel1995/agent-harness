"""The seven compaction policies for the applied (real-task) bake-off.

This is the applied sibling of `experiments/policies.py`. The controlled probe
there summarizes synthetic needle transcripts; here the same policies run against
real FRAMES/LoCoMo tasks, so the interface gains a `store` for retrieval:

    compact(old, llm, store) -> (replacement_block, usage)

The `retrieves` flag tells the agent whether to pull from the store at answer time.

  truncate           : drop the old turns. No store, no retrieval. The cost floor.
  recency            : one summary in the window. No store. The shipped default.
  importance         : keep the highest-signal turns verbatim, summarize the rest.
  semantic           : cluster the old turns by topic, summarize each cluster.
  externalize        : drop from window, push raw to store, retrieve at answer.
  subagent           : isolate the read in a sub-agent, return only its findings.
  reversible_hybrid  : summary in window AND raw pushed to store + retrieve at
                       answer. The novel arm: lossy summary plus reversible raw.

Registered in POLICIES at the bottom; the runner swaps one by name per arm.
"""

from __future__ import annotations

import hashlib
import re

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


class Importance:
    name = "importance"
    retrieves = False

    def __init__(self, keep=2):
        self.keep = keep

    def _score(self, m):
        t = _text(m)
        return (len(re.findall(r"\d", t)) + 3 * len(re.findall(r"https?://", t))
                + 2 * len(re.findall(r"[A-Z][a-z]+-?\d", t)))

    def compact(self, old, llm, store):
        order = sorted(range(len(old)), key=lambda i: self._score(old[i]), reverse=True)
        keep = set(order[: self.keep])
        block = [{"role": "system", "content": "[KEPT verbatim]\n" + _text(old[i])} for i in sorted(keep)]
        rest = [old[i] for i in range(len(old)) if i not in keep]
        usage = dict(ZERO)
        if rest:
            s, usage = _summarize(llm, rest)
            block.append({"role": "system", "content": "[COMPACTED rest]\n" + s})
        return block, usage


class Semantic:
    name = "semantic"
    retrieves = False

    def __init__(self, groups=2):
        self.groups = groups

    def _bucket(self, m):
        h = hashlib.md5(re.sub(r"\d", "", _text(m)[:60]).encode()).hexdigest()
        return int(h, 16) % self.groups

    def compact(self, old, llm, store):
        buckets = {}
        for m in old:
            buckets.setdefault(self._bucket(m), []).append(m)
        block, total = [], dict(ZERO)
        for b, msgs in sorted(buckets.items()):
            s, u = _summarize(llm, msgs)
            total = {k: total[k] + u.get(k, 0) for k in total}
            block.append({"role": "system", "content": f"[TOPIC {b}]\n" + s})
        return block, total


class Subagent:
    """Sub-agent isolation as a policy: summarize each evicted source independently,
    as if a fresh-window sub-agent read it and returned only a summary. Costly
    (one model call per source), which is exactly the trade-off we measure."""
    name = "subagent"
    retrieves = False

    def compact(self, old, llm, store):
        block, total = [], dict(ZERO)
        for m in old:
            if not _text(m).strip():
                continue
            s, u = _summarize(llm, [m])
            total = {k: total[k] + u.get(k, 0) for k in total}
            block.append({"role": "system", "content": "[SUBAGENT SUMMARY]\n" + s})
        return block or [{"role": "system", "content": "[no content]"}], total


POLICIES = {p.name: p for p in [
    Truncate(), Recency(), Importance(), Semantic(),
    Externalize(), ReversibleHybrid(), Subagent(),
]}
