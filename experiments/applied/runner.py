"""EXP-003a runner: sweep compaction policies over FRAMES questions and write a
self-contained run directory (manifest + prompts + results), then report
accuracy-vs-cost by policy.

    python -m experiments.applied -v               # default config
    python -m experiments.applied --n 30 -vv       # small, full logs
"""

from __future__ import annotations

import argparse
import collections
import csv
import statistics as st
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from experiments.nim import NimLLM
from experiments.bench.run_context import RunContext
from experiments.bench.logsetup import setup, get
from experiments.applied import frames, wiki
from experiments.applied.embed import EmbedStore
from experiments.applied.policies import POLICIES
from experiments.applied.agent import answer_question

log = get("runner")

FIELDS = ["policy", "qid", "correct", "n_compactions", "final_window_tokens",
          "retrieved_chars", "tokens_in", "tokens_out", "tokens_total"]


@dataclass
class Config:
    exp_id: str = "EXP-003a"
    slug: str = "frames-compaction"
    hypothesis: str = (
        "On FRAMES multi-hop QA, summary-based and reversible-hybrid compaction preserve "
        "more answer accuracy per token than truncation; the reversible-hybrid (summary "
        "plus retrievable raw) sits on or above the cost-quality frontier."
    )
    assumptions: tuple = (
        "Oracle retrieval (gold Wikipedia articles) isolates compaction from search quality.",
        "Articles capped at 6000 chars and N per question still overflow the budget and force compaction.",
        "Normalized substring match against the gold answer is a cheap, objective accuracy proxy for dev.",
        "8b is a dev model; final numbers and an LLM-judge come with the 70b solid run.",
    )
    model: str = "meta/llama-3.1-8b-instruct"
    use_judge: bool = False
    judge_model: str = "meta/llama-3.3-70b-instruct"
    policies: tuple = ("truncate", "recency", "externalize", "reversible_hybrid")
    n_questions: int = 50
    max_articles: int = 6
    budget: int = 2000
    keep_recent: int = 4
    seed: int = 0
    cache_dir: str = "experiments/.cache"


def run(cfg):
    ctx = RunContext(cfg)
    llm = NimLLM(model=cfg.model, cache_dir=cfg.cache_dir, transcript_path=ctx.transcript_path)
    judge_llm = (NimLLM(model=cfg.judge_model, cache_dir=cfg.cache_dir,
                        transcript_path=ctx.transcript_path) if cfg.use_judge else None)
    items = frames.load(cfg.n_questions, cfg.seed)
    log.info(f"loaded {len(items)} FRAMES questions; policies={list(cfg.policies)}; "
             f"model={cfg.model}; budget={cfg.budget}; max_articles={cfg.max_articles}")

    # Pre-fetch the gold articles once (cached on disk), capped per question.
    for it in items:
        arts = [wiki.fetch(u) for u in it.wiki_urls[:cfg.max_articles]]
        it.articles = [a for a in arts if a.strip()]
    items = [it for it in items if it.articles]
    log.info(f"{len(items)} questions have fetchable articles")

    with ctx.results_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for pname in cfg.policies:
            pol = POLICIES[pname]
            corr = 0
            for it in items:
                store = EmbedStore() if pol.retrieves else None
                try:
                    row = answer_question(it, it.articles, llm, pol, store,
                                          budget=cfg.budget, keep_recent=cfg.keep_recent,
                                          judge_llm=judge_llm)
                except Exception as e:  # one bad question must not kill the sweep
                    log.error(f"{pname} q{it.id} FAILED: {type(e).__name__}: {e}")
                    continue
                row.update({"policy": pname, "qid": it.id})
                w.writerow({k: row.get(k) for k in FIELDS})
                f.flush()
                corr += row["correct"]
            log.info(f"[{pname}] accuracy {corr}/{len(items)} = {corr / max(1, len(items)):.2f}")
    log.info(f"sweep complete -> {ctx.results_path}")
    return ctx


def report(results_path):
    rows = list(csv.DictReader(open(results_path)))
    g = collections.defaultdict(list)
    for r in rows:
        g[r["policy"]].append((int(r["correct"]), int(r["tokens_total"]), int(r["n_compactions"])))
    print("\n=== EXP-003a: FRAMES accuracy vs cost by policy ===")
    print(f"{'policy':<18}{'accuracy':>10}{'mean_tokens':>13}{'mean_comp':>11}{'n':>5}")
    for p in ("truncate", "recency", "importance", "semantic",
              "externalize", "reversible_hybrid", "subagent"):
        if p in g:
            a = g[p]
            acc = sum(c for c, _, _ in a) / len(a)
            tok = st.mean(t for _, t, _ in a)
            comp = st.mean(c for _, _, c in a)
            print(f"{p:<18}{acc:>10.2f}{tok:>13.0f}{comp:>11.1f}{len(a):>5}")


def main():
    ap = argparse.ArgumentParser(description="EXP-003a: FRAMES compaction bake-off")
    ap.add_argument("-v", action="count", default=0)
    ap.add_argument("--n", type=int, default=None, help="number of questions")
    ap.add_argument("--model", default=None)
    ap.add_argument("--policies", default=None, help="comma list")
    ap.add_argument("--budget", type=int, default=None)
    ap.add_argument("--max-articles", type=int, default=None)
    ap.add_argument("--judge", action="store_true", help="grade with the LLM judge, not substring")
    a = ap.parse_args()
    setup("DEBUG" if a.v >= 2 else "INFO")
    cfg = Config()
    if a.n:
        cfg.n_questions = a.n
    if a.model:
        cfg.model = a.model
    if a.policies:
        cfg.policies = tuple(a.policies.split(","))
    if a.budget:
        cfg.budget = a.budget
    if a.max_articles:
        cfg.max_articles = a.max_articles
    if a.judge:
        cfg.use_judge = True
    ctx = run(cfg)
    report(ctx.results_path)


if __name__ == "__main__":
    main()
