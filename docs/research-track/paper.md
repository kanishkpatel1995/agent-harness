# The paper — Compaction Bake-Off

> Working title: **"What to Forget: An Empirical Comparison of Context
> Compaction Policies for Long-Running Agents."**

This is the research the whole curriculum builds toward. It is deliberately
*small and finishable* — a workshop paper / long blog-paper, not a thesis. The
goal is a single, defensible, reproducible claim. Read this before Unit 5; it's
what gives every earlier unit its direction.

---

## 1. The question

A long-running agent must periodically throw away context to stay under budget.
This repo throws away the **stale middle** and replaces it with an LLM summary —
*recency summary*. But that is one choice among several, made by assertion, never
measured. So:

> **Among compaction policies that all keep the agent under the same token
> budget, which preserves the most end-task quality per token spent — and does
> the answer change as the run gets longer?**

"Per token spent" matters: a policy that preserves everything by calling the
model ten times to summarize isn't free. We want the **quality-vs-cost frontier**,
not a single winner.

---

## 2. Why it's worth doing

- **It's unmeasured in the wild.** Frameworks ship a compaction default and move
  on. A clean comparison with an objective metric is genuinely useful and
  genuinely missing.
- **It's tractable for one person in weeks**, because the harness already
  isolates compaction behind `maybe_compact`.
- **It's reproducible by design** — the FakeLLM makes agent behavior
  deterministic, so results aren't washed out by model noise.
- **The likely result is interesting either way:** either a fancy policy beats
  recency (actionable), or it doesn't and externalization dominates (a clean,
  honest null that *also* validates the repo's design).

---

## 2b. Related work (the grounding — full survey in `literature.md`)

The positioning, in one paragraph (citations and the verified bibliography are in
[`literature.md`](literature.md) §7):

> Long-context degradation is well established — *Lost in the Middle*
> (arXiv:2307.03172), and the post-NIAH benchmarks RULER (2404.06654), HELMET
> (2410.02694) and NoLiMa (2502.05167) showing models use far less of their
> window than advertised. Two fixes exist: **externalize** (MemGPT 2310.08560;
> Generative Agents 2304.03442; Mem0 2504.19413) and **compress**. But prior
> compression targets a *static prompt* or *RAG passages*, optimizes *inference
> efficiency*, and works at the *token / activation / KV* level, often with
> finetuning (LLMLingua 2310.05736; Gist 2304.08467; H₂O 2306.14048; StreamingLLM
> 2309.17453). The closest analogue to our LLM-summary compaction is RECOMP's
> abstractive compressor (2310.04408) — but on retrieved passages for one query,
> not an evolving agent transcript.

**Our niche:** message/turn-level, training-free, model-agnostic compaction of an
*evolving multi-turn transcript*, measured by fact-recall per token, with an
external scratchpad as control. That regime — the one real agent harnesses
actually run in — is essentially unmeasured. That is the gap.

## 3. The policies (the arms)

All four operate on the same input — the evicted "old" messages — and must
preserve the tool-call/result invariant (Unit 3).

| Policy | What it keeps | Cost profile | Hypothesized strength |
|---|---|---|---|
| **Truncate** | Nothing (one marker line) | Cheapest (no model call) | Floor / baseline |
| **Recency summary** | One LLM summary of the middle | 1 model call per compaction | Strong, cheap default |
| **Importance-ranked** | Top-scoring raw turns + summary of rest | 1 model call + scoring | Wins when specific facts matter |
| **Semantic** | Per-topic-cluster summaries | ≥1 model call per compaction | Wins at high run-length / many topics |

Optional 5th arm for the talk's "why": **No compaction** — let it grow to the
hard limit and die. Demonstrates the failure mode the others prevent.

---

## 4. The metric — needle-fact recall (the core idea)

This is the part that makes it a paper instead of a vibe.

**Setup.** Inject K labeled needle-facts into the fixtures — each a distinct,
mechanically-checkable token: a coined term, a specific number, a dated claim
(e.g. *"The Zarnak coefficient was measured at 0.47 in 2019."*). Distribute them
across pages so the agent encounters them at different points in the run.

**Measure, after each run:**
- **`recall_report`** — fraction of encountered needles present in the final
  report. *The end-task metric.*
- **`recall_scratchpad`** — fraction saved to disk. *Isolates the externalize
  move from compaction.*
- **`recall_window`** — fraction surviving in the post-compaction window.
  *Directly scores the compaction policy's fidelity.*

**Cost, per run:**
- `total_tokens_billed` (cumulative prompt+completion — the re-send cost),
  `est_usd`, `steps`, `n_compactions`.

**Why this is strong evidence.** A planted fact either appears in the output or
it doesn't — no judge, no rubric, no model nondeterminism (under FakeLLM). It's
the agent-loop analogue of needle-in-a-haystack, but measuring *survival through
compaction* rather than retrieval from a single prompt.

**Optional softer metric.** LLM-as-judge on the report for coverage/coherence,
reported separately and flagged as higher-variance. Never let it carry the
headline claim alone.

---

## 5. Experimental design

The result is a function: `policy × run_length × seed → metrics`.

- **Independent variable: `run_length`** = number of sources the agent reads
  (drives `n_compactions`). Sweep e.g. {4, 8, 16, 32}. This is *the* axis —
  policies should be indistinguishable when nothing gets compacted and diverge as
  compaction events pile up.
- **Control:** identical token budget (`max_context_tokens`), `keep_recent`,
  goal, and needle set across all policies. Only the policy changes.
- **Repeats:** ≥5 seeds per cell (vary needle placement / source order) for error
  bars. With FakeLLM the agent path is deterministic, so the variance you measure
  is from needle placement and the (real-model) summary step, not loop chaos.

**The headline figure:** a **Pareto plot** — x = `total_tokens_billed`, y =
`recall_report` — one line per policy, points at increasing run-lengths. The
story is which policy sits on the upper-left frontier, and where the lines cross.

---

## 6. The methodology decision you must make (and defend)

Under the **pure** FakeLLM, the compaction summary is canned text — so you cannot
study summary *quality* fully offline. Two honest options:

- **(A) Hybrid.** FakeLLM drives the deterministic tool-call loop, but the
  *summarization step* (`_summarize`) calls a cheap real model
  (`gpt-4o-mini`/`haiku`). Agent behavior stays deterministic; compaction quality
  is real. **Recommended** — it's the cleanest separation of concerns.
- **(B) Offline-only.** Restrict the offline study to `recall_*` + cost (which
  *are* well-defined even with canned summaries, since recall is about whether
  needle text survives), and validate report-quality on real models in a smaller
  separate run.

Pick one, write a paragraph on why. Making — and defending — this call is exactly
the kind of methodological judgment that separates a measured result from a
plausible-sounding one.

---

## 7. Hypotheses (commit before you run — intellectual honesty)

1. **H1.** At low run-length (≤1 compaction), all policies are within noise on
   `recall_report`.
2. **H2.** As run-length grows, `recall_window` ordering is Importance ≥ Semantic
   > Recency > Truncate.
3. **H3.** `recall_scratchpad` is ~policy-independent and high — i.e.
   **externalization dominates**, and the compaction policy only matters for
   facts the agent *didn't* externalize.
4. **H4.** On a cost-adjusted basis, Recency summary is hard to beat until
   run-length exceeds some K — the "fancy policy tax" doesn't pay off until there
   are enough compaction events to amortize it.

If H3 holds strongly, your headline becomes *"compaction policy is second-order;
externalize is the move that matters"* — a better, more surprising talk than any
single-policy win.

---

## 8. Threats to validity (write this section honestly)

- **FakeLLM determinism** buys reproducibility at the cost of realism — the agent
  never makes the messy mistakes a real model does. State it; offer the real-model
  spot-check as mitigation.
- **Single task domain** (deep research over web fixtures). Don't over-claim to
  all agents.
- **Needle-facts may be easier to preserve than diffuse understanding** — recall
  of discrete facts is a *proxy* for quality, not quality itself. The LLM-judge
  metric partially covers this; name the gap.
- **Price table is approximate** (`budget.py` `_PRICES`); use litellm's real costs
  for the final numbers.
- **Summary quality depends on the summarizer model** — report which model and
  note results may shift with a stronger/weaker one.

A reviewer who sees you list these *before* they ask trusts the result more.

---

## 9. Deliverable & format

- **`paper/compaction-bakeoff.md`** — 4–6 pages: Question · Method (policies +
  needle metric) · Setup · Results (the Pareto figure) · Threats · Reproduction.
- **`experiments/bench`** (the bake-off runner) + **`experiments/make_figures*.py`**
  + committed `results.csv` — so the claim is reproducible with one command.
- **A blog-paper version** for Learn Agentic AI, same content, narrative voice.
- **Stretch:** submit to a workshop or post to arXiv-adjacent venue once the
  result holds across a couple of task domains.

The bar, repeated from the README: **the paper is not done until someone else can
run `python -m experiments.bench` and get your figure.**

---

## 10. How this feeds the June 22 talk

You won't have the full result by the 22nd, and that's fine. The talk shows the
*machinery* (live compaction) and ends by **posing** this question as "the thing
I'm now measuring" — see [`talk-june22.md`](talk-june22.md) slide 9. Presenting
the question, the metric, and the hypothesis *before* the answer is itself good
science communication, and it gives you a reason to come back and present the
result later.
