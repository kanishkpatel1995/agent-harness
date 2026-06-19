"""The window loop — where the budget axis and the max-window failure mode live.

Two arms:
  run_compaction : stream chunks in; whenever the window exceeds BUDGET B, compact
                   the old middle with the chosen policy. Measures fidelity + probe
                   recall and the token cost, for a given (policy, budget).
  run_baseline   : NO compaction. Grow the raw context, measure recall-vs-length,
                   and record a context_overflow death the moment it would exceed
                   the model's hard max window. This is the control AND the reason
                   compaction exists.

Heavily logged: at DEBUG you see every read, token check, compaction, and score.
"""

from __future__ import annotations

from harness.context import approx_tokens
from . import metrics
from .logsetup import get

log = get("window")


def _toks(body):
    return sum(approx_tokens(str(m)) for m in body)


def _safe_split(body, proposed):
    """Never let the kept tail start on a 'tool' message (must follow its call)."""
    idx = max(0, min(proposed, len(body)))
    while idx < len(body) and body[idx].get("role") == "tool":
        idx += 1
    return idx


def _read_msgs(i, page):
    """The two messages a real agent appends when it reads a source."""
    return [
        {"role": "assistant", "content": f"Reading source {i + 1}.",
         "tool_calls": [{"id": f"c{i}", "type": "function",
                         "function": {"name": "fetch_url", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": f"c{i}", "content": page},
    ]


def run_compaction(policy, sample, llm, *, budget, keep_recent, model_max_tokens):
    body, n_comp, tin, tout = [], 0, 0, 0
    log.info(f"[{policy.name} B={budget}] start: {len(sample.chunks)} chunks, keep_recent={keep_recent}")
    for i, page in enumerate(sample.chunks):
        body += _read_msgs(i, page)
        log.debug(f"[{policy.name} B={budget}] read source {i + 1}: window={_toks(body)} tok, {len(body)} msgs")
        inner = 0
        while _toks(body) > budget and len(body) > keep_recent + 1:
            before = _toks(body)
            split = _safe_split(body, len(body) - keep_recent)
            if split <= 0:
                log.debug(f"[{policy.name} B={budget}] cannot split safely, stop compacting")
                break
            old, recent = body[:split], body[split:]
            block, u = policy.compact(old, llm)
            spent = u.get("prompt_tokens", 0) + u.get("completion_tokens", 0)
            tin += u.get("prompt_tokens", 0)
            tout += u.get("completion_tokens", 0)
            body = block + recent
            n_comp += 1
            inner += 1
            after = _toks(body)
            log.info(f"[{policy.name} B={budget}] COMPACT #{n_comp}: {before}->{after} tok "
                     f"(evicted {len(old)} msgs, kept {len(recent)} recent, +{spent} tok billed)")
            # PROGRESS GUARD: if the window didn't shrink, the kept tail alone
            # exceeds the budget (or the policy can't compress further). Accept the
            # tail-bound window instead of spinning forever. (This is the bug that
            # silently hung 'importance' before — a multi-message block keeps
            # len(body) > keep_recent+1 true while tokens never drop.)
            if after >= before or inner >= 50:
                log.warning(f"[{policy.name} B={budget}] not converging "
                            f"(window={after} > budget {budget} after {inner} tries); "
                            "accepting tail-bound window")
                break

    window_text = "\n".join((m.get("content") or "") for m in body)
    final_tok = _toks(body)
    if final_tok > model_max_tokens:
        log.warning(f"[{policy.name} B={budget}] window {final_tok} > model_max {model_max_tokens} "
                    "(budget should be < max so this should not happen)")
    fid = metrics.fidelity(window_text, sample.needles)
    pr, u = metrics.probe(llm, window_text, sample.needles)
    tin += u.get("prompt_tokens", 0)
    tout += u.get("completion_tokens", 0)
    log.info(f"[{policy.name} B={budget}] done: fidelity={len(fid)}/{len(sample.needles)} "
             f"probe={len(pr)}/{len(sample.needles)} comp={n_comp} tok_billed={tin + tout}")
    return {
        "arm": "compaction", "policy": policy.name, "budget": budget,
        "needles_total": len(sample.needles), "fidelity": len(fid), "probe": len(pr),
        "n_compactions": n_comp, "final_window_tokens": final_tok, "overflow": 0,
        "tokens_in": tin, "tokens_out": tout, "tokens_total": tin + tout,
    }


def run_baseline(sample, llm, *, model_max_tokens):
    """No compaction: grow the raw context, measure recall@length, hit the wall."""
    body, overflow_at = [], 0
    log.info(f"[baseline] start: {len(sample.chunks)} chunks, model_max={model_max_tokens}")
    for i, page in enumerate(sample.chunks):
        candidate = body + _read_msgs(i, page)
        t = _toks(candidate)
        if t > model_max_tokens:
            overflow_at = i + 1
            log.warning(f"[baseline] CONTEXT OVERFLOW at source {i + 1}: {t} > model_max "
                        f"{model_max_tokens} -> a real agent DIES here without compaction")
            break
        body = candidate
        log.debug(f"[baseline] read source {i + 1}: raw window={t} tok")

    window_text = "\n".join((m.get("content") or "") for m in body)
    final_tok = _toks(body)
    fid = metrics.fidelity(window_text, sample.needles)
    pr, u = metrics.probe(llm, window_text, sample.needles)
    log.info(f"[baseline] done: raw_window={final_tok} tok, probe={len(pr)}/{len(sample.needles)}, "
             f"overflow={'yes@' + str(overflow_at) if overflow_at else 'no'}")
    return {
        "arm": "baseline", "policy": "none", "budget": 0,
        "needles_total": len(sample.needles), "fidelity": len(fid), "probe": len(pr),
        "n_compactions": 0, "final_window_tokens": final_tok, "overflow": overflow_at,
        "tokens_in": u.get("prompt_tokens", 0), "tokens_out": u.get("completion_tokens", 0),
        "tokens_total": u.get("prompt_tokens", 0) + u.get("completion_tokens", 0),
    }
