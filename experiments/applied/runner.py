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
    chunk_chars: int = 0   # >0 splits each article into chunks read as separate steps
    keep_recent: int = 4
    seed: int = 0
    cache_dir: str = "experiments/.cache"
    resume: bool = False


RUNS_DIR = Path("experiments/runs")


def _latest_run_dir(exp_id):
    dirs = sorted(RUNS_DIR.glob(f"{exp_id}__*"))
    return dirs[-1] if dirs else None


def _done_cells(results_path):
    if not Path(results_path).exists():
        return set()
    with open(results_path) as f:
        return {(r["policy"], r["qid"]) for r in csv.DictReader(f)}


# EXP-003b: high compaction pressure (small budget, articles read in chunks so
# compaction fires many times per question), all seven arms, LLM judge. The regime
# where policy should matter, unlike the low-pressure EXP-003a where they tied.
EXP003B = Config(
    exp_id="EXP-003b",
    slug="frames-pressure",
    hypothesis=(
        "Under high compaction pressure (small budget, chunked reads forcing many "
        "compaction events per question), the policies separate on FRAMES answer "
        "accuracy, and the reversible-hybrid (summary plus retrievable raw) sits on "
        "or above the cost-quality frontier, unlike the low-pressure EXP-003a tie."
    ),
    assumptions=(
        "Oracle retrieval (gold Wikipedia articles) isolates compaction from search quality.",
        "Chunked reads at budget 1500 force roughly 10-20 compactions per question (cf. EXP-002 pressure).",
        "The 70b LLM judge credits paraphrased-correct answers (substring biased toward verbatim).",
        "8b is a dev model; the model axis (70b, reasoning) comes in EXP-003c.",
    ),
    model="meta/llama-3.1-8b-instruct",
    use_judge=True,
    policies=("truncate", "recency", "importance", "semantic",
              "externalize", "reversible_hybrid", "subagent"),
    n_questions=30,
    max_articles=6,
    budget=1500,
    chunk_chars=1500,
    keep_recent=4,
    seed=0,
)


def run(cfg):
    # Resume reuses the latest run dir for this experiment and skips finished
    # cells, so an interrupted run loses nothing (the response cache also replays
    # any redone calls for free).
    done = set()
    if getattr(cfg, "resume", False) and _latest_run_dir(cfg.exp_id) is not None:
        rundir = _latest_run_dir(cfg.exp_id)
        results_path = rundir / "results.csv"
        transcript_path = rundir / "prompts.jsonl"
        done = _done_cells(results_path)
        log.info(f"RESUMING {rundir.name}: {len(done)} cells already done, skipping those")
    else:
        ctx = RunContext(cfg)
        results_path = ctx.results_path
        transcript_path = ctx.transcript_path

    llm = NimLLM(model=cfg.model, cache_dir=cfg.cache_dir, transcript_path=transcript_path)
    judge_llm = (NimLLM(model=cfg.judge_model, cache_dir=cfg.cache_dir,
                        transcript_path=transcript_path) if cfg.use_judge else None)
    items = frames.load(cfg.n_questions, cfg.seed)
    log.info(f"loaded {len(items)} FRAMES questions; policies={list(cfg.policies)}; "
             f"model={cfg.model}; budget={cfg.budget}; max_articles={cfg.max_articles}")

    # Pre-fetch the gold articles once (cached on disk), capped per question.
    # Optionally split each article into chunks read as separate steps, which raises
    # compaction pressure (more reads -> more compaction events).
    for it in items:
        arts = [wiki.fetch(u) for u in it.wiki_urls[:cfg.max_articles]]
        chunks = []
        for a in arts:
            if not a.strip():
                continue
            if cfg.chunk_chars > 0:
                chunks += [a[i:i + cfg.chunk_chars] for i in range(0, len(a), cfg.chunk_chars)]
            else:
                chunks.append(a)
        it.articles = chunks
    items = [it for it in items if it.articles]
    log.info(f"{len(items)} questions have fetchable articles")

    write_header = (not results_path.exists()) or results_path.stat().st_size == 0
    with results_path.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if write_header:
            w.writeheader()
        for pname in cfg.policies:
            pol = POLICIES[pname]
            corr = total = 0
            for it in items:
                if (pname, it.id) in done:
                    continue
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
                total += 1
            if total:
                log.info(f"[{pname}] {corr}/{total} correct (new this run)")
    log.info(f"sweep complete -> {results_path}")
    return results_path


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
    ap.add_argument("--chunk-chars", type=int, default=None, help="split articles into chunks of N chars")
    ap.add_argument("--preset", default=None, help="EXP003B for the high-pressure config")
    ap.add_argument("--resume", action="store_true", help="resume the latest run dir, skip done cells")
    a = ap.parse_args()
    setup("DEBUG" if a.v >= 2 else "INFO")
    cfg = EXP003B if a.preset == "EXP003B" else Config()
    if a.n:
        cfg.n_questions = a.n
    if a.chunk_chars is not None:
        cfg.chunk_chars = a.chunk_chars
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
    if a.resume:
        cfg.resume = True
    results_path = run(cfg)
    report(results_path)


if __name__ == "__main__":
    main()
