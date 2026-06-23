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
    # Non-empty => run the AGENT against this OpenAI-compatible endpoint (e.g. LM Studio
    # at http://localhost:1234/v1). The judge stays on NIM so the metric is held constant.
    api_base: str = ""
    # Override the agent watchdog (seconds). Reasoning models emit long summaries that can
    # legitimately exceed the default 75s; raising this stops the watchdog killing them.
    agent_timeout: int = 0
    # Append "detailed thinking off" to the agent's compaction summaries (reasoning models
    # only) so summaries stay concise and fast; the answer keeps full reasoning.
    think_off_summarize: bool = False
    # Run compaction summaries on this (fast) model instead of the agent model. The agent
    # still answers. Used for the reasoning tier (verbose CoT makes self-summarizing slow).
    summarizer: str = ""
    # Retrieval backend for the externalize/hybrid (retrieving) policies:
    #   "nim"    -> EmbedStore: NVIDIA nv-embedqa-e5-v5 (1024-d, asymmetric query/passage, API)
    #   "chroma" -> ChromaBackend: Chroma + all-MiniLM-L6-v2 (384-d, local onnxruntime, no key)
    # The agent and judge are unchanged; only the memory backend differs (EXP-006).
    store: str = "nim"


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


# EXP-003c: the model axis. Same high-pressure regime as EXP-003b, but we vary the
# agent model instead of the policy set. We keep only the five arms that separated in
# EXP-003b (dropping recency and subagent, both Pareto-dominated there) and re-run them
# on a strong instruct model and a reasoning model, to see whether the 8b ranking holds
# as capability grows. The 8b numbers come from the EXP-003b run (same five arms).
EXP003C = Config(
    exp_id="EXP-003c",
    slug="frames-model-axis",
    hypothesis=(
        "The EXP-003b policy ranking is model-dependent: on a stronger instruct model "
        "and a reasoning model, structure-preserving compaction (semantic, importance) "
        "still leads on FRAMES accuracy, but the gaps between arms narrow as the model "
        "gets better at reconstructing dropped context, and the reversible-hybrid stays "
        "Pareto-efficient across all three model tiers."
    ),
    assumptions=(
        "Oracle retrieval (gold Wikipedia articles) isolates compaction from search quality.",
        "The same thirty FRAMES questions and cached articles are reused across models, so only the agent model changes.",
        "A fixed 70b judge grades every arm and every model, so the metric is held constant across the model axis.",
        "The reasoning model's chain-of-thought is parsed down to its final answer before judging.",
    ),
    model="meta/llama-3.3-70b-instruct",
    use_judge=True,
    policies=("truncate", "externalize", "importance", "semantic", "reversible_hybrid"),
    n_questions=30,
    max_articles=6,
    budget=1500,
    chunk_chars=1500,
    keep_recent=4,
    seed=0,
)


PRESETS = {"EXP003B": EXP003B, "EXP003C": EXP003C}


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

    if cfg.api_base:
        # Local agent: no rate-limit pacing, longer watchdog (local gen + first-load is
        # slower per call than NIM, but there is no shared quota to protect).
        llm = NimLLM(model=cfg.model, cache_dir=cfg.cache_dir, transcript_path=transcript_path,
                     api_base=cfg.api_base, min_interval=0.0, soft_timeout=150, hard_timeout=180)
        log.info(f"AGENT on local endpoint {cfg.api_base} (model={cfg.model}); judge stays on NIM")
    else:
        to = ({"soft_timeout": cfg.agent_timeout, "hard_timeout": cfg.agent_timeout + 20}
              if cfg.agent_timeout else {})
        if cfg.think_off_summarize:
            to["think_off_stages"] = {"summarize"}
        llm = NimLLM(model=cfg.model, cache_dir=cfg.cache_dir, transcript_path=transcript_path, **to)
        if cfg.agent_timeout:
            log.info(f"agent watchdog raised to {cfg.agent_timeout}s (reasoning summaries run long)")
        if cfg.think_off_summarize:
            log.info("summaries use 'detailed thinking off' (concise, fast); answer keeps reasoning")
    judge_llm = (NimLLM(model=cfg.judge_model, cache_dir=cfg.cache_dir,
                        transcript_path=transcript_path) if cfg.use_judge else None)
    # Optional separate (fast) summarizer for compaction; the agent still answers. Used for
    # the reasoning tier, whose verbose chain-of-thought makes self-summarizing prohibitive.
    summarizer_llm = (NimLLM(model=cfg.summarizer, cache_dir=cfg.cache_dir,
                             transcript_path=transcript_path) if cfg.summarizer else None)
    if summarizer_llm is not None:
        log.info(f"compaction summaries run on {cfg.summarizer}; agent {cfg.model} answers")
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

    # Retrieval backend factory for the retrieving policies (EXP-006: NIM vs Chroma).
    def make_store():
        if cfg.store == "chroma":
            from experiments.applied.chroma_backend import ChromaBackend
            return ChromaBackend()
        return EmbedStore()
    if any(POLICIES[p].retrieves for p in cfg.policies):
        log.info(f"retrieval backend: {cfg.store}")

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
                store = make_store() if pol.retrieves else None
                try:
                    row = answer_question(it, it.articles, llm, pol, store,
                                          budget=cfg.budget, keep_recent=cfg.keep_recent,
                                          judge_llm=judge_llm, summarizer_llm=summarizer_llm)
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
    print("\n=== FRAMES accuracy vs cost by policy ===")
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
    ap.add_argument("--preset", default=None,
                    help="EXP003B (high-pressure 7-arm) or EXP003C (model axis, 5-arm)")
    ap.add_argument("--resume", action="store_true", help="resume the latest run dir, skip done cells")
    ap.add_argument("--api-base", default=None,
                    help="run the agent against this OpenAI-compatible endpoint (e.g. LM Studio)")
    ap.add_argument("--agent-timeout", type=int, default=None,
                    help="raise the agent watchdog (s) for verbose reasoning models")
    ap.add_argument("--think-off-summarize", action="store_true",
                    help="reasoning models: keep compaction summaries concise (thinking off)")
    ap.add_argument("--summarizer", default=None,
                    help="run compaction summaries on this fast model; agent still answers")
    ap.add_argument("--store", default=None, choices=["nim", "chroma"],
                    help="retrieval backend for retrieving policies: nim (nv-embedqa) or chroma (MiniLM)")
    a = ap.parse_args()
    setup("DEBUG" if a.v >= 2 else "INFO")
    cfg = PRESETS[a.preset] if a.preset in PRESETS else Config()
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
    if a.api_base:
        cfg.api_base = a.api_base
    if a.agent_timeout:
        cfg.agent_timeout = a.agent_timeout
    if a.think_off_summarize:
        cfg.think_off_summarize = True
    if a.summarizer:
        cfg.summarizer = a.summarizer
    if a.store:
        cfg.store = a.store
    results_path = run(cfg)
    report(results_path)


if __name__ == "__main__":
    main()
