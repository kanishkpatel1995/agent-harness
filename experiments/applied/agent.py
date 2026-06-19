"""The FRAMES research-agent loop.

Read the question's gold Wikipedia articles in sequence (oracle retrieval). When
the window exceeds the budget, compact with the chosen policy. After reading,
optionally retrieve detail from the store, then answer. Score the answer against
the gold answer with a normalized substring match (a cheap, objective proxy for
dev; an LLM-judge is added for the solid run).
"""

from __future__ import annotations

import re

from experiments.bench.window import _toks, _safe_split, _read_msgs
from experiments.bench.logsetup import get

log = get("agent")

ANSWER_SYS = (
    "You are answering a research question using ONLY the provided context. "
    "Think briefly, then end with a line 'Answer: <final answer>'. Be concise and specific."
)


def _norm(s):
    s = (s or "").lower().replace("%", " percent")
    return re.sub(r"\s+", " ", re.sub(r"[,.’']", "", s)).strip()


def is_correct(answer, gold):
    return _norm(gold) in _norm(answer)


def answer_question(item, articles, llm, policy, store, *, budget, keep_recent):
    body, n_comp, tin, tout = [], 0, 0, 0
    for i, art in enumerate(articles):
        body += _read_msgs(i, art)
        inner = 0
        while _toks(body) > budget and len(body) > keep_recent + 1:
            before = _toks(body)
            split = _safe_split(body, len(body) - keep_recent)
            if split <= 0:
                break
            old, recent = body[:split], body[split:]
            block, u = policy.compact(old, llm, store)
            tin += u.get("prompt_tokens", 0)
            tout += u.get("completion_tokens", 0)
            body = block + recent
            n_comp += 1
            inner += 1
            if _toks(body) >= before or inner >= 50:
                break

    window_text = "\n".join((m.get("content") or "") for m in body)
    retrieved = store.retrieve(item.question, k=3) if (policy.retrieves and store is not None) else ""
    ctx = window_text + (("\n\n[RETRIEVED DETAIL]\n" + retrieved) if retrieved else "")

    r = llm.complete([
        {"role": "system", "content": ANSWER_SYS},
        {"role": "user", "content": f"Context:\n{ctx[:14000]}\n\nQuestion: {item.question}\nAnswer:"},
    ], stage="answer")
    tin += r.usage.get("prompt_tokens", 0)
    tout += r.usage.get("completion_tokens", 0)

    ans = r.content or ""
    m = re.search(r"answer:\s*(.+)$", ans, re.I | re.S)
    final = (m.group(1) if m else ans).strip()
    ok = is_correct(final, item.answer)
    log.debug(f"q{item.id} [{policy.name}] correct={int(ok)} comp={n_comp} ans={final[:60]!r}")
    return {
        "correct": int(ok), "answer": final[:200], "gold": item.answer[:120],
        "n_compactions": n_comp, "final_window_tokens": _toks(body),
        "retrieved_chars": len(retrieved),
        "tokens_in": tin, "tokens_out": tout, "tokens_total": tin + tout,
    }
