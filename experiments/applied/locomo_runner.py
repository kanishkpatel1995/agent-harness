"""EXP-004 runner: the compaction bake-off on LoCoMo (the second domain).

Where FRAMES is multi-hop factual QA over Wikipedia (one article-set per question),
LoCoMo is conversational memory: each conversation has many sessions that overflow the
window, and many questions asked of that one conversation. So the agent reads the sessions
ONCE under a policy (compact-once) and answers many questions from the same compacted
window (ask-many) — the realistic long-chat-many-questions flow. The compaction itself is
shared with the FRAMES agent (agent.read_and_compact), so the only thing that changes is
the domain. This tests whether the FRAMES policy ranking transfers across task types.

    python -m experiments.applied.locomo_runner -v
    python -m experiments.applied.locomo_runner --n-conv 10 --q-per-conv 10 --judge -vv
"""

from __future__ import annotations

import argparse
import collections
import csv
import random
import statistics as st
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from experiments.nim import NimLLM
from experiments.bench.run_context import RunContext
from experiments.bench.logsetup import setup, get
from experiments.applied import locomo
from experiments.applied.embed import EmbedStore
from experiments.applied.policies import POLICIES
from experiments.applied.agent import read_and_compact, answer_from_window
from experiments.bench.window import _toks

log = get("locomo")

FIELDS = ["policy", "conv", "qid", "category", "correct", "n_compactions",
          "comp_tokens", "ans_tokens", "final_window_tokens", "retrieved_chars"]
RUNS_DIR = Path("experiments/runs")


@dataclass
class Config:
    exp_id: str = "EXP-004"
    slug: str = "locomo-transfer"
    hypothesis: str = (
        "The FRAMES compaction ranking transfers to conversational memory: under high "
        "compaction pressure, structure and retrieval preserving policies (importance, "
        "semantic, reversible-hybrid, externalize) preserve more LoCoMo QA accuracy than "
        "truncation, because conversational questions hinge on specific facts scattered "
        "across early sessions that blind truncation drops."
    )
    assumptions: tuple = (
        "The agent reads all sessions of a conversation (oracle), so there is no retrieval-quality confound.",
        "Each conversation's sessions (tens of thousands of chars) overflow the 1500-token budget and force many compactions.",
        "The conversation is compacted once per policy; the same window answers every sampled question (amortized compaction).",
        "The 70b LLM judge credits paraphrase and date-format differences in short conversational answers.",
        "8b is a dev model; the solid run repeats on the 70b.",
    )
    model: str = "meta/llama-3.1-8b-instruct"
    use_judge: bool = False
    judge_model: str = "meta/llama-3.3-70b-instruct"
    policies: tuple = ("truncate", "externalize", "importance", "semantic", "reversible_hybrid")
    n_conversations: int = 10
    q_per_conv: int = 10
    budget: int = 1500
    keep_recent: int = 4
    seed: int = 0
    cache_dir: str = "experiments/.cache"
    resume: bool = False
    story: bool = False   # narrate each cell: question, retrieved chunks, answer, gold, verdict
    question_ids: tuple = ()   # if set, answer exactly these qa indices (overrides --q-per-conv sampling)


def _latest_run_dir(exp_id):
    dirs = sorted(RUNS_DIR.glob(f"{exp_id}__*"))
    return dirs[-1] if dirs else None


def _done_cells(results_path):
    if not Path(results_path).exists():
        return set()
    with open(results_path) as f:
        return {(r["policy"], r["conv"], r["qid"]) for r in csv.DictReader(f)}


def _sample_questions(conv, k, seed):
    """A fixed sample of this conversation's QA, stable across policies (seeded by conv id)."""
    idx = list(range(len(conv.qa)))
    random.Random(f"{seed}-{conv.id}").shuffle(idx)
    return [(i, conv.qa[i]) for i in idx[:k]]


def run(cfg):
    done = set()
    if getattr(cfg, "resume", False) and _latest_run_dir(cfg.exp_id) is not None:
        rundir = _latest_run_dir(cfg.exp_id)
        results_path, transcript_path = rundir / "results.csv", rundir / "prompts.jsonl"
        done = _done_cells(results_path)
        log.info(f"RESUMING {rundir.name}: {len(done)} cells already done, skipping those")
    else:
        ctx = RunContext(cfg)
        results_path, transcript_path = ctx.results_path, ctx.transcript_path

    llm = NimLLM(model=cfg.model, cache_dir=cfg.cache_dir, transcript_path=transcript_path)
    judge_llm = (NimLLM(model=cfg.judge_model, cache_dir=cfg.cache_dir,
                        transcript_path=transcript_path) if cfg.use_judge else None)

    convs = locomo.load()[:cfg.n_conversations]
    log.info(f"loaded {len(convs)} LoCoMo conversations; policies={list(cfg.policies)}; "
             f"model={cfg.model}; budget={cfg.budget}; q_per_conv={cfg.q_per_conv}")

    write_header = (not results_path.exists()) or results_path.stat().st_size == 0
    with results_path.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if write_header:
            w.writeheader()
        for pname in cfg.policies:
            pol = POLICIES[pname]
            corr = total = 0
            for conv in convs:
                qs = _sample_questions(conv, cfg.q_per_conv, cfg.seed)
                if cfg.question_ids:   # feature specific question(s) on stage
                    qs = [(i, conv.qa[i]) for i in cfg.question_ids if 0 <= i < len(conv.qa)]
                if all((pname, conv.id, str(qi)) in done for qi, _ in qs):
                    continue
                # Compact this conversation ONCE; the same window answers every question.
                store = EmbedStore() if pol.retrieves else None
                try:
                    body, n_comp, ctin, ctout = read_and_compact(
                        conv.sessions, llm, pol, store, budget=cfg.budget,
                        keep_recent=cfg.keep_recent, story=cfg.story)
                except Exception as e:  # a bad conversation must not kill the sweep
                    log.error(f"{pname} conv{conv.id} COMPACT FAILED: {type(e).__name__}: {e}")
                    continue
                comp_tokens = ctin + ctout
                fwin = _toks(body)
                for qi, qa in qs:
                    if (pname, conv.id, str(qi)) in done:
                        continue
                    try:
                        ok, final, rchars, atin, atout = answer_from_window(
                            body, store, qa["question"], qa["answer"], llm, pol,
                            judge_llm=judge_llm, story=cfg.story)
                    except Exception as e:
                        log.error(f"{pname} conv{conv.id} q{qi} FAILED: {type(e).__name__}: {e}")
                        continue
                    w.writerow({"policy": pname, "conv": conv.id, "qid": qi,
                                "category": qa.get("category", ""), "correct": int(ok),
                                "n_compactions": n_comp, "comp_tokens": comp_tokens,
                                "ans_tokens": atin + atout, "final_window_tokens": fwin,
                                "retrieved_chars": rchars})
                    f.flush()
                    corr += int(ok)
                    total += 1
                log.info(f"[{pname}] conv{conv.id}: compacted {n_comp}x ({comp_tokens} tok), "
                         f"window {fwin} tok")
            if total:
                log.info(f"[{pname}] {corr}/{total} correct (new this run)")
    log.info(f"sweep complete -> {results_path}")
    return results_path


def report(results_path):
    rows = list(csv.DictReader(open(results_path)))
    g = collections.defaultdict(list)
    convtok = collections.defaultdict(dict)  # policy -> conv -> comp_tokens (paid once)
    anstok = collections.defaultdict(list)
    for r in rows:
        g[r["policy"]].append(int(r["correct"]))
        convtok[r["policy"]][r["conv"]] = int(r["comp_tokens"])
        anstok[r["policy"]].append(int(r["ans_tokens"]))
    print("\n=== EXP-004: LoCoMo accuracy vs cost by policy ===")
    print(f"{'policy':<18}{'accuracy':>10}{'mean_ans_tok':>14}{'compact_tok':>13}{'n':>6}")
    for p in ("truncate", "externalize", "importance", "semantic", "reversible_hybrid"):
        if p in g:
            acc = sum(g[p]) / len(g[p])
            mean_ans = st.mean(anstok[p])
            comp = st.mean(convtok[p].values())  # mean compaction cost per conversation
            print(f"{p:<18}{acc:>10.2f}{mean_ans:>14.0f}{comp:>13.0f}{len(g[p]):>6}")


def main():
    ap = argparse.ArgumentParser(description="EXP-004: LoCoMo compaction bake-off")
    ap.add_argument("-v", action="count", default=0)
    ap.add_argument("--n-conv", type=int, default=None, help="number of conversations")
    ap.add_argument("--q-per-conv", type=int, default=None, help="questions sampled per conversation")
    ap.add_argument("--model", default=None)
    ap.add_argument("--policies", default=None, help="comma list")
    ap.add_argument("--budget", type=int, default=None)
    ap.add_argument("--judge", action="store_true", help="grade with the LLM judge, not substring")
    ap.add_argument("--resume", action="store_true", help="resume the latest run dir, skip done cells")
    ap.add_argument("--story", action="store_true",
                    help="narrate each cell: question, retrieved chunks, answer, gold, judge verdict")
    ap.add_argument("--question", default=None,
                    help="feature specific question id(s), comma-separated (overrides --q-per-conv sampling)")
    a = ap.parse_args()
    setup("DEBUG" if a.v >= 2 else "INFO")
    cfg = Config()
    if a.story:
        cfg.story = True
        import logging
        # --story is its own clean narration; mute the per-call / per-chunk DEBUG spam.
        for noisy in ("bench.embed", "bench.model"):
            logging.getLogger(noisy).setLevel(logging.WARNING)
    if a.n_conv:
        cfg.n_conversations = a.n_conv
    if a.q_per_conv:
        cfg.q_per_conv = a.q_per_conv
    if a.model:
        cfg.model = a.model
    if a.policies:
        cfg.policies = tuple(a.policies.split(","))
    if a.budget:
        cfg.budget = a.budget
    if a.judge:
        cfg.use_judge = True
    if a.resume:
        cfg.resume = True
    if a.question:
        cfg.question_ids = tuple(int(x) for x in a.question.split(","))
    results_path = run(cfg)
    report(results_path)


if __name__ == "__main__":
    main()
