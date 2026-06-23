"""subagent — isolate each evicted source in a fresh window, return only its
summary. Architecture: ISOLATE.

This is Anthropic's multi-agent research pattern as a compaction policy: instead
of shrinking one window, fan the old turns out to fresh sub-agent windows and
keep only what each returns. Anthropic reports ~90% gains on BROAD, parallel
research — but on a single focused question this bench shows it's a cost trap
(one LLM call per source). Same architecture, opposite verdict; the task shape
decides. (Sakana's Fugu is the frontier of this family — orchestration across
models — but it routes rather than forgets, so we cite it, not bench it.)
"""

from __future__ import annotations

from .base import ZERO, summarize, text


class Subagent:
    name = "subagent"
    architecture = "isolate"
    retrieves = False
    decision = "Treat each evicted source as a fresh-window sub-agent; keep only the summary each returns."
    tradeoff = "Parallel and powerful on broad research (Anthropic) — but one LLM call PER source makes it the priciest, and a cost trap on a single focused task."
    result = "FRAMES-8B 0.50 · Pareto-DOMINATED here (~5x the cost of importance, no accuracy gain)."

    def compact(self, old, llm, store):
        block, total = [], dict(ZERO)
        for m in old:
            if not text(m).strip():
                continue
            s, u = summarize(llm, [m])
            total = {k: total[k] + u.get(k, 0) for k in total}
            block.append({"role": "system", "content": "[SUBAGENT SUMMARY]\n" + s})
        return block or [{"role": "system", "content": "[no content]"}], total
