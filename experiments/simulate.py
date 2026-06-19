"""Mode A: build a needle-bearing transcript, compact it with a policy, probe.

This is the controlled fidelity experiment. We do NOT run a live agent; we
deterministically construct the message list a research agent WOULD accumulate
(assistant 'reading source i' + a tool result page containing needles), run the
same compaction loop the harness uses — but with a chosen policy — and finally
ask the real model to recover the planted facts from the compacted window.

API calls per run = (#compactions) + 1 probe. Truncate makes only the 1 probe.
"""

from __future__ import annotations

import random

from harness.context import approx_tokens
from experiments.needles import NEEDLES, score


def _safe_split(body, proposed):
    """Mirror of ContextManager._safe_split_index: never let the kept tail start
    on a 'tool' message (it must follow the assistant turn that called it)."""
    idx = max(0, min(proposed, len(body)))
    while idx < len(body) and body[idx].get("role") == "tool":
        idx += 1
    return idx


def _toks(body):
    return sum(approx_tokens(str(m)) for m in body)


def build_pages(run_length, needles, seed=0):
    """A VARIED-per-seed layout so repeated seeds are genuine different draws
    (real error bars), not byte-identical copies.

    Each seed randomizes: which pages carry a needle, the needle's DEPTH in its
    page (front..middle..end — the lost-in-the-middle axis), and the filler size
    (which shifts when compaction fires). A given (run_length, seed) is shared
    across all four policies, so the comparison stays controlled — only the
    policy changes, never the data it sees.
    """
    rng = random.Random(seed)
    order = list(range(run_length))
    rng.shuffle(order)
    needle_on = {order[i]: needles[i] for i in range(min(len(needles), run_length))}
    pages = []
    for i in range(run_length):
        n_filler = rng.randint(30, 50)  # vary size -> vary compaction timing
        lines = [f"# Source {i + 1}"] + [
            f"Background detail line {j} for source {i + 1}." for j in range(n_filler)
        ]
        if i in needle_on:
            depth = rng.random()  # 0=front .. 1=end; the position axis
            at = max(1, min(len(lines), int(len(lines) * depth)))
            lines.insert(at, needle_on[i].sentence)
        pages.append("\n".join(lines))
    return pages


def run_probe(policy, llm, *, run_length, budget_tokens=1500, keep_recent=4, seed=0):
    needles = NEEDLES[: min(len(NEEDLES), run_length)]
    pages = build_pages(run_length, needles, seed)

    body, n_comp, tin, tout = [], 0, 0, 0
    for i, page in enumerate(pages):
        body.append({
            "role": "assistant", "content": f"Reading source {i + 1}.",
            "tool_calls": [{"id": f"c{i}", "type": "function",
                            "function": {"name": "fetch_url", "arguments": "{}"}}],
        })
        body.append({"role": "tool", "tool_call_id": f"c{i}", "content": page})
        # Mirror maybe_compact: while over budget, evict + compact the old middle.
        while _toks(body) > budget_tokens and len(body) > keep_recent + 1:
            split = _safe_split(body, len(body) - keep_recent)
            if split <= 0:
                break
            old, recent = body[:split], body[split:]
            block, u = policy.compact(old, llm)
            tin += u.get("prompt_tokens", 0)
            tout += u.get("completion_tokens", 0)
            body = block + recent
            n_comp += 1

    window_text = "\n".join((m.get("content") or "") for m in body)
    recall_window = score(window_text, needles)  # literal survival in the window

    probe = [
        {"role": "system", "content": "List every specific number, named term, and date "
                                       "that appears in the context. Output them plainly."},
        {"role": "user", "content": window_text[:12000]},
    ]
    r = llm.complete(probe)
    tin += r.usage.get("prompt_tokens", 0)
    tout += r.usage.get("completion_tokens", 0)
    recall_probe = score(r.content, needles)  # usable recall by the model

    return {
        "policy": policy.name, "run_length": run_length, "seed": seed,
        "needles_total": len(needles),
        "recall_window": len(recall_window), "recall_probe": len(recall_probe),
        "n_compactions": n_comp,
        "tokens_in": tin, "tokens_out": tout, "tokens_total": tin + tout,
    }
