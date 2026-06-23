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
        peek = " ".join((articles[0] if articles else "").split())[:100]
        stored = len(getattr(store, "texts", [])) if store is not None else 0
        if store is not None:
            move = f"moved the raw turns to a store ({_C.B}{stored} chunks{_C.E}{_C.D}, searchable)"
        else:
            move = "dropped the old turns"
        bar = "─" * 54
        print(f"\n{_C.P}{_C.B}┌─ policy: {policy.name} {bar[:42]}{_C.E}")
        print(f"{_C.P}│{_C.E} {_C.B}DATASET{_C.E}  the agent reads {len(articles)} sources (chat sessions / articles)")
        print(f"{_C.P}│{_C.E}   {_C.D}peek › {peek}…{_C.E}")
        print(f"{_C.P}│{_C.E} {_C.B}COMPACT{_C.E}  window crossed the {budget}-tok budget {n_comp}× → {policy.name} {_C.D}{move}{_C.E}")
        print(f"{_C.P}│{_C.E}   the window the model will actually see: {_C.B}{_toks(body)} tokens{_C.E}")
        print(f"{_C.P}└{'─' * 52}{_C.E}")
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
        model_name = getattr(llm, "model", "model").split("/")[-1]
        chunks = [c for c in retrieved.split("\n\n") if c.strip()] if retrieved else []
        ctx_note = f"the {_toks(body)}-tok compacted window"
        if policy.retrieves and chunks:
            ctx_note += f" + {len(chunks)} retrieved chunks"
        raw_out = " ".join((r.content or "").split())
        verdict = f"{_C.G}✓ CORRECT{_C.E}" if ok else f"{_C.R}✗ WRONG{_C.E}"
        grader = "70B judge" if judge_llm is not None else "substring match"
        print(f"\n  {_C.B}❓ QUESTION{_C.E} (from the dataset)")
        print(f"     {(question or '')[:110]}")
        print(f"     {_C.D}↳ gold answer the dataset expects: \"{(gold or '')[:60]}\"{_C.E}")
        if policy.retrieves and chunks:
            print(f"  {_C.P}🔎 RETRIEVED{_C.E} {len(chunks)} chunks from the store (this is what 'memory' pulls back):")
            for c in chunks[:3]:
                print(f"     {_C.D}› {' '.join(c.split())[:92]}{_C.E}")
        elif policy.retrieves:
            print(f"  {_C.P}🔎 RETRIEVED{_C.E} {_C.D}nothing matched in the store{_C.E}")
        print(f"  {_C.P}📨 INPUT to {model_name}{_C.E} {_C.D}({r.usage.get('prompt_tokens', 0)} tokens go in):{_C.E}")
        print(f"     {_C.D}system  │ {ANSWER_SYS[:72]}…{_C.E}")
        print(f"     {_C.D}context │ [{ctx_note}]{_C.E}")
        print(f"     {_C.D}question│ {(question or '')[:72]}{_C.E}")
        print(f"  {_C.P}📥 OUTPUT{_C.E} (what {model_name} actually said, raw):")
        print(f"     {_C.B}{raw_out[:150]}{_C.E}")
        print(f"  {_C.P}⚖️  GRADE{_C.E} ({grader}): \"{(final or '')[:42]}\" vs gold \"{(gold or '')[:34]}\"  →  {verdict}")
        print(f"  {_C.D}💾 SAVED → results.csv:  correct={int(ok)} · retrieved_chars={len(retrieved)} · tokens={tin + tout}{_C.E}")
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
