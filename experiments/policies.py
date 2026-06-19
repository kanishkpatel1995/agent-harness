"""The four compaction policies — the independent variable of the bake-off.

Each takes the evicted 'old' messages and returns a SHORT replacement block plus
the token usage it spent. They keep whole turns (never strand a tool result from
its assistant call).

  truncate    : keep nothing but a marker.            0 API calls (cost floor).
  recency     : one LLM summary of everything old.    1 call (repo's default).
  importance  : keep highest-signal turns verbatim,   1 call (+ heuristic).
                summarize the rest.
  semantic    : group old turns by topic, summarize   >=1 call (one per cluster).
                each group.
"""

from __future__ import annotations

import hashlib
import re

ZERO = {"prompt_tokens": 0, "completion_tokens": 0}
SUMMARY = (
    "Compress this agent transcript into a dense factual note. Preserve EVERY "
    "specific number, named term, date, and URL exactly as written. Drop chatter. "
    "Maximum 180 words."
)


def _text(m):
    return m.get("content") or ""


def _summarize(llm, msgs):
    transcript = "\n".join(f"[{m.get('role')}] {_text(m)}" for m in msgs)[:12000]
    r = llm.complete([
        {"role": "system", "content": SUMMARY},
        {"role": "user", "content": transcript},
    ], stage="summarize")
    return r.content.strip(), r.usage


class Truncate:
    name = "truncate"

    def compact(self, old, llm):
        return [{"role": "system", "content": f"[{len(old)} earlier turns dropped]"}], dict(ZERO)


class Recency:
    name = "recency"

    def compact(self, old, llm):
        s, u = _summarize(llm, old)
        return [{"role": "system", "content": "[COMPACTED]\n" + s}], u


class Importance:
    name = "importance"

    def __init__(self, keep=2):
        self.keep = keep

    def _score(self, m):
        t = _text(m)
        return (
            len(re.findall(r"\d", t))
            + 3 * len(re.findall(r"https?://", t))
            + 2 * len(re.findall(r"[A-Z][a-z]+-?\d", t))
        )

    def compact(self, old, llm):
        order = sorted(range(len(old)), key=lambda i: self._score(old[i]), reverse=True)
        keep_idx = set(order[: self.keep])
        block = [
            {"role": "system", "content": "[KEPT verbatim — high signal]\n" + _text(old[i])}
            for i in sorted(keep_idx)
        ]
        rest = [old[i] for i in range(len(old)) if i not in keep_idx]
        usage = dict(ZERO)
        if rest:
            s, usage = _summarize(llm, rest)
            block.append({"role": "system", "content": "[COMPACTED rest]\n" + s})
        return block, usage


class Semantic:
    name = "semantic"

    def __init__(self, groups=2):
        self.groups = groups

    def _bucket(self, m):
        # Stable hash (NOT python hash(), which is salted per process and would
        # break reproducibility). A crude stand-in for embedding clusters.
        h = hashlib.md5(re.sub(r"\d", "", _text(m)[:60]).encode()).hexdigest()
        return int(h, 16) % self.groups

    def compact(self, old, llm):
        buckets = {}
        for m in old:
            buckets.setdefault(self._bucket(m), []).append(m)
        block, total = [], dict(ZERO)
        for b, msgs in sorted(buckets.items()):
            s, u = _summarize(llm, msgs)
            total = {k: total[k] + u.get(k, 0) for k in total}
            block.append({"role": "system", "content": f"[COMPACTED topic {b}]\n" + s})
        return block, total


POLICIES = {p.name: p for p in [Truncate(), Recency(), Importance(), Semantic()]}
