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


class _C:
    """Tiny ANSI palette for --story narration (live terminal)."""
    B = "\033[1m"; D = "\033[2m"; G = "\033[38;5;71m"; R = "\033[38;5;167m"; P = "\033[38;5;141m"; E = "\033[0m"


ANSWER_SYS = (
    "You are answering a research question using ONLY the provided context. "
    "Think briefly, then end with a line 'Answer: <final answer>'. Be concise and specific."
)


def _norm(s):
    s = (s or "").lower().replace("%", " percent")
    return re.sub(r"\s+", " ", re.sub(r"[,.’']", "", s)).strip()


def is_correct(answer, gold):
    return _norm(gold) in _norm(answer)


def read_and_compact(articles, summarizer, policy, store, *, budget, keep_recent, story=False):
    """Read text chunks in order, compacting with the policy whenever the window exceeds
    the budget. Returns (body, n_comp, tokens_in, tokens_out). Domain-agnostic — FRAMES
    articles or LoCoMo sessions — so both runners share one compaction implementation."""
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
            block, u = policy.compact(old, summarizer, store)
            tin += u.get("prompt_tokens", 0)
            tout += u.get("completion_tokens", 0)
            body = block + recent
            n_comp += 1
            inner += 1
            if _toks(body) >= before or inner >= 50:
                break
    if story:
        stored = len(getattr(store, "texts", [])) if store is not None else 0
        extra = f"  ->  {_C.B}stored {stored} chunks{_C.E}" if store is not None else ""
        print(f"\n{_C.P}{_C.B}━━ {policy.name} ━━{_C.E}  read {len(articles)} sources  ->  "
              f"{n_comp} compactions  ->  window {_toks(body)} tok{extra}")
    return body, n_comp, tin, tout


def answer_from_window(body, store, question, gold, llm, policy, *, judge_llm=None, story=False):
    """Answer one question from an already-compacted window. LoCoMo compacts a conversation
    once and asks many questions of the same window, so this is split out from the read.
    Returns (correct, final_answer, retrieved_chars, tokens_in, tokens_out)."""
    window_text = "\n".join((m.get("content") or "") for m in body)
    retrieved = store.retrieve(question, k=3) if (policy.retrieves and store is not None) else ""
    ctx = window_text + (("\n\n[RETRIEVED DETAIL]\n" + retrieved) if retrieved else "")

    r = llm.complete([
        {"role": "system", "content": ANSWER_SYS},
        {"role": "user", "content": f"Context:\n{ctx[:14000]}\n\nQuestion: {question}\nAnswer:"},
    ], stage="answer")
    tin = r.usage.get("prompt_tokens", 0)
    tout = r.usage.get("completion_tokens", 0)

    # Reasoning models wrap chain-of-thought in <think>...</think>; strip it so we judge the
    # final answer, not the scratchpad (no-op for instruct models).
    ans = re.sub(r"<think>.*?</think>", "", (r.content or ""), flags=re.I | re.S).strip()
    m = re.search(r"answer:\s*(.+)$", ans, re.I | re.S)
    final = (m.group(1) if m else ans).strip()
    ok = is_correct(final, gold)
    if judge_llm is not None:
        from experiments.applied.judge import judge as _judge
        jok, ju = _judge(judge_llm, question, final, gold)
        tin += ju.get("prompt_tokens", 0)
        tout += ju.get("completion_tokens", 0)
        ok = bool(jok)
    if story:
        print(f"  {_C.B}Q{_C.E} \"{(question or '')[:90]}\"")
        if policy.retrieves and retrieved:
            print(f"    {_C.D}retrieved (the chunks it pulled back to answer):{_C.E}")
            for chunk in [c for c in retrieved.split('\n\n') if c.strip()][:3]:
                print(f"    {_C.D}  › {' '.join(chunk.split())[:96]}{_C.E}")
        elif policy.retrieves:
            print(f"    {_C.D}retrieved: (nothing matched in the store){_C.E}")
        verdict = f"{_C.G}✓ correct{_C.E}" if ok else f"{_C.R}✗ wrong{_C.E}"
        print(f"    answer: {_C.B}\"{(final or '')[:70]}\"{_C.E}   gold: \"{(gold or '')[:50]}\"   judge: {verdict}")
    return ok, final, len(retrieved), tin, tout


def answer_question(item, articles, llm, policy, store, *, budget, keep_recent, judge_llm=None,
                    summarizer_llm=None, story=False):
    # summarizer_llm lets compaction run on a different (fast) model than the agent that
    # answers (used for the reasoning tier). Defaults to the agent model, so every other tier
    # is unchanged (same model summarizes and answers).
    sm = summarizer_llm or llm
    body, n_comp, tin, tout = read_and_compact(articles, sm, policy, store,
                                               budget=budget, keep_recent=keep_recent, story=story)
    ok, final, rchars, atin, atout = answer_from_window(
        body, store, item.question, item.answer, llm, policy, judge_llm=judge_llm, story=story)
    tin += atin
    tout += atout
    log.debug(f"q{item.id} [{policy.name}] correct={int(ok)} comp={n_comp} ans={final[:60]!r}")
    return {
        "correct": int(ok), "answer": final[:200], "gold": item.answer[:120],
        "n_compactions": n_comp, "final_window_tokens": _toks(body),
        "retrieved_chars": rchars,
        "tokens_in": tin, "tokens_out": tout, "tokens_total": tin + tout,
    }
