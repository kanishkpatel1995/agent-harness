#!/usr/bin/env python3
"""EXP-009 — Agentic-FRAMES: the policies on a REAL agent transcript.

FRAMES and LoCoMo feed the agent oracle sources in sequence, so the agent never drives the
loop. This runner makes the same task agentic: the agent is given the question and three tools
over the question's gold corpus, and it must DECIDE what to do each step:

    SEARCH: <query>     keyword search over the corpus, returns the top passages (id + preview)
    READ:   <id>        read one passage in full
    ANSWER: <text>      commit a final answer

Its own actions and the tool results accumulate into a transcript; when that transcript exceeds
the token budget, the chosen compaction policy compacts it (exactly the seven policies, operating
now on the agent's real trajectory rather than on pre-fetched articles). Retrieving policies page
evicted transcript turns to their store and recover them at answer time. This closes two gaps at
once: the agent drives multi-step tool use (agentic), and retrieval is no longer oracle (the agent
must find the right passages itself).

    python experiments/applied/agentic_runner.py --n 20 --policies truncate,externalize,reversible_hybrid --judge -v
    python experiments/applied/agentic_runner.py --n 1 --policies reversible_hybrid --judge --story
"""

from __future__ import annotations

import argparse
import collections
import csv
import re
import statistics as st
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from experiments.nim import NimLLM
from experiments.bench.run_context import RunContext
from experiments.bench.logsetup import setup, get
from experiments.bench.window import _toks, _safe_split
from experiments.applied import frames, wiki
from experiments.applied.embed import EmbedStore
from experiments.applied.policies import POLICIES
from experiments.applied.judge import judge as judge_call

log = get("agentic")

SYS = (
    "You are a research agent answering a question using a document corpus you can search. "
    "Each turn, reason briefly, then end your message with EXACTLY ONE action line:\n"
    "  SEARCH: <query>   - search the corpus, returns the top matching passages\n"
    "  READ: <id>        - read one passage in full (use an id from a SEARCH result)\n"
    "  ANSWER: <answer>  - give your final answer once you have enough evidence\n"
    "Start by searching. Do not answer until you have read the supporting passage."
)
CHUNK = 700


class Corpus:
    """The question's gold articles, chunked and keyword-searchable. The agent's retrieval target
    (distinct from a policy's externalize store, which holds evicted transcript turns)."""

    def __init__(self, articles):
        self.chunks = []
        for a in articles:
            for i in range(0, len(a), CHUNK):
                c = a[i:i + CHUNK].strip()
                if c:
                    self.chunks.append(c)

    @staticmethod
    def _toks(s):
        return set(re.findall(r"[a-z0-9][a-z0-9\-]+", s.lower()))

    def search(self, query, k=5):
        q = self._toks(query)
        scored = sorted(range(len(self.chunks)),
                        key=lambda i: len(q & self._toks(self.chunks[i])), reverse=True)
        hits = [i for i in scored if q & self._toks(self.chunks[i])][:k]
        if not hits:
            return "(no matching passages)"
        return "\n".join(f"[{i}] {' '.join(self.chunks[i].split())[:120]}..." for i in hits)

    def read(self, cid):
        m = re.search(r"\d+", str(cid))   # the model writes "[13]" or "[13] - the Obama passage"
        if m:
            i = int(m.group())
            if 0 <= i < len(self.chunks):
                return self.chunks[i]
        return f"(no passage with id {cid})"


def _parse_action(text):
    """Pull the last SEARCH/READ/ANSWER action out of the model's message."""
    t = re.sub(r"<think>.*?</think>", "", text or "", flags=re.I | re.S)
    m = None
    for mm in re.finditer(r"(SEARCH|READ|ANSWER):\s*(.+?)\s*$", t, re.I | re.M):
        m = mm
    if not m:
        return ("ANSWER", t.strip()[:300]) if t.strip() else ("SEARCH", "")
    return (m.group(1).upper(), m.group(2).strip())


def solve(item, llm, policy, store, *, budget, keep_recent, max_steps, judge_llm=None, story=False):
    corpus = Corpus(item.articles)
    body = [{"role": "system", "content": SYS},
            {"role": "user", "content": f"Question: {item.question}\n\nYour first action line:"}]
    n_comp = tin = tout = 0
    final, did_answer = "", False
    if story:
        print(f"\n\033[38;5;141m\033[1m━━ {policy.name} · q{item.id} ━━\033[0m  {item.question[:90]}")
        print(f"  \033[2mgold: {item.answer[:60]} | corpus: {len(corpus.chunks)} passages\033[0m")

    for step in range(max_steps):
        while _toks(body) > budget and len(body) > keep_recent + 1:
            split = _safe_split(body, len(body) - keep_recent)
            if split <= 0:
                break
            block, u = policy.compact(body[:split], llm, store)
            tin += u.get("prompt_tokens", 0); tout += u.get("completion_tokens", 0)
            body = block + body[split:]; n_comp += 1
            if story:
                print(f"  \033[2m… compacted (now {_toks(body)} tok, store {len(getattr(store,'texts',[]))} chunks)\033[0m")

        r = llm.complete(body, stage="agent")
        tin += r.usage.get("prompt_tokens", 0); tout += r.usage.get("completion_tokens", 0)
        kind, arg = _parse_action(r.content)
        body.append({"role": "assistant", "content": f"{kind}: {arg}"})

        if kind == "ANSWER":
            final, did_answer = arg, True
            if story:
                print(f"  \033[1mstep {step+1} ANSWER:\033[0m {arg[:80]}")
            break
        elif kind == "READ":
            obs = corpus.read(arg)
        else:  # SEARCH (default)
            obs = corpus.search(arg)
        body.append({"role": "user", "content": f"Observation:\n{obs[:1200]}\n\nYour next action line:"})
        if story:
            print(f"  step {step+1} {kind}: {arg[:50]}  ->  \033[2m{' '.join(obs.split())[:70]}\033[0m")

    # retrieving policies recover evicted detail at answer time, then we judge
    retrieved = store.retrieve(item.question, k=3) if (policy.retrieves and store is not None) else ""
    if not did_answer or (policy.retrieves and retrieved):
        ctx = "\n".join(m.get("content") or "" for m in body) + ("\n\n[RECOVERED]\n" + retrieved if retrieved else "")
        r = llm.complete([{"role": "system", "content": "Answer the question from the context. End with 'Answer: <answer>'."},
                          {"role": "user", "content": f"Context:\n{ctx[:14000]}\n\nQuestion: {item.question}\nAnswer:"}], stage="answer")
        tin += r.usage.get("prompt_tokens", 0); tout += r.usage.get("completion_tokens", 0)
        ans = re.sub(r"<think>.*?</think>", "", r.content or "", flags=re.I | re.S)
        mm = re.search(r"answer:\s*(.+)$", ans, re.I | re.S)
        final = (mm.group(1) if mm else ans).strip()

    if judge_llm is not None:
        ok, ju = judge_call(judge_llm, item.question, final, item.answer)
        tin += ju.get("prompt_tokens", 0); tout += ju.get("completion_tokens", 0)
    else:
        from experiments.applied.agent import is_correct
        ok = int(is_correct(final, item.answer))
    if story:
        mark = "\033[38;5;71m✓\033[0m" if ok else "\033[38;5;167m✗\033[0m"
        print(f"  \033[1mverdict:\033[0m {mark}  final={final[:50]!r}  steps={step+1} comp={n_comp}")
    return {"correct": int(ok), "steps": step + 1, "answered": int(did_answer),
            "n_compactions": n_comp, "final_window_tokens": _toks(body),
            "tokens_in": tin, "tokens_out": tout, "tokens_total": tin + tout}


@dataclass
class Config:
    exp_id: str = "EXP-009"
    slug: str = "agentic-frames"
    hypothesis: str = (
        "On an agent-driven version of FRAMES, where the agent itself searches and reads a corpus "
        "over many steps so the transcript is a real tool-use trajectory, the compaction-policy "
        "ranking holds: keeping the raw retrievable (externalize, reversible_hybrid) preserves the "
        "evidence the agent gathered, while blind truncation drops it and the agent cannot recover."
    )
    assumptions: tuple = (
        "Keyword search over the gold corpus isolates compaction from external search quality while still making retrieval the agent's job.",
        "A small budget plus multi-step tool use forces compaction to fire on the agent's own transcript.",
        "The 70b judge grades the final answer; 8b is the dev agent.",
    )
    model: str = "meta/llama-3.1-8b-instruct"
    use_judge: bool = False
    judge_model: str = "meta/llama-3.3-70b-instruct"
    policies: tuple = ("truncate", "externalize", "reversible_hybrid")
    n_questions: int = 20
    max_articles: int = 6
    budget: int = 1200
    keep_recent: int = 4
    max_steps: int = 8
    seed: int = 0
    cache_dir: str = "experiments/.cache"
    story: bool = False


FIELDS = ["policy", "qid", "correct", "answered", "steps", "n_compactions",
          "final_window_tokens", "tokens_in", "tokens_out", "tokens_total"]


def run(cfg):
    ctx = RunContext(cfg)
    llm = NimLLM(model=cfg.model, cache_dir=cfg.cache_dir, transcript_path=ctx.transcript_path)
    judge_llm = (NimLLM(model=cfg.judge_model, cache_dir=cfg.cache_dir,
                        transcript_path=ctx.transcript_path) if cfg.use_judge else None)
    if cfg.story:
        for c in (llm, judge_llm):
            if c is not None:
                c.spinner = True
    items = frames.load(cfg.n_questions, cfg.seed)
    for it in items:
        it.articles = [a for a in (wiki.fetch(u) for u in it.wiki_urls[:cfg.max_articles]) if a.strip()]
    items = [it for it in items if it.articles]
    log.info(f"{len(items)} agentic-FRAMES questions; policies={list(cfg.policies)}; budget={cfg.budget}; max_steps={cfg.max_steps}")

    with ctx.results_path.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader()
        for pname in cfg.policies:
            pol = POLICIES[pname]
            corr = tot = 0
            for it in items:
                store = EmbedStore() if pol.retrieves else None
                try:
                    row = solve(it, llm, pol, store, budget=cfg.budget, keep_recent=cfg.keep_recent,
                                max_steps=cfg.max_steps, judge_llm=judge_llm, story=cfg.story)
                except Exception as e:
                    log.error(f"{pname} q{it.id} FAILED: {type(e).__name__}: {e}"); continue
                row.update({"policy": pname, "qid": it.id}); w.writerow(row); f.flush()
                corr += row["correct"]; tot += 1
            if tot:
                log.info(f"[{pname}] {corr}/{tot} correct (agentic)")
    log.info(f"sweep complete -> {ctx.results_path}")
    return ctx.results_path


def report(results_path):
    rows = list(csv.DictReader(open(results_path)))
    g = collections.defaultdict(list)
    for r in rows:
        g[r["policy"]].append(r)
    print("\n=== EXP-009: Agentic-FRAMES accuracy vs cost ===")
    print(f"{'policy':<19}{'accuracy':>10}{'answered':>10}{'mean_steps':>12}{'mean_comp':>11}{'mean_tok':>10}{'n':>5}")
    order = ["truncate", "recency", "importance", "semantic", "externalize", "reversible_hybrid", "subagent"]
    for p in [x for x in order if x in g] + [x for x in g if x not in order]:
        a = g[p]
        acc = sum(int(r["correct"]) for r in a) / len(a)
        ans = sum(int(r["answered"]) for r in a) / len(a)
        steps = st.mean(int(r["steps"]) for r in a)
        comp = st.mean(int(r["n_compactions"]) for r in a)
        tok = st.mean(int(r["tokens_total"]) for r in a)
        print(f"{p:<19}{acc:>10.2f}{ans:>10.0%}{steps:>12.1f}{comp:>11.1f}{tok:>10.0f}{len(a):>5}")


def main():
    ap = argparse.ArgumentParser(description="EXP-009: agentic-FRAMES")
    ap.add_argument("-v", action="count", default=0)
    ap.add_argument("--n", type=int, default=None)
    ap.add_argument("--policies", default=None)
    ap.add_argument("--budget", type=int, default=None)
    ap.add_argument("--max-steps", type=int, default=None)
    ap.add_argument("--judge", action="store_true")
    ap.add_argument("--story", action="store_true")
    a = ap.parse_args()
    setup("DEBUG" if a.v >= 2 else "INFO")
    cfg = Config()
    if a.n: cfg.n_questions = a.n
    if a.policies: cfg.policies = tuple(a.policies.split(","))
    if a.budget: cfg.budget = a.budget
    if a.max_steps: cfg.max_steps = a.max_steps
    if a.judge: cfg.use_judge = True
    if a.story:
        cfg.story = True
        import logging
        for n in ("bench.embed", "bench.model"):
            logging.getLogger(n).setLevel(logging.WARNING)
    report(run(cfg))


if __name__ == "__main__":
    main()
