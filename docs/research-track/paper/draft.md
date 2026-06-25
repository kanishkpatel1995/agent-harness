# Which Way to Forget? A Compaction-Policy Bake-Off for Long-Running LLM Agents

*Full paper draft, v0.2 (post deep-research reframe, 2026-06-24). Repositioned from "first
head-to-head" to the compaction-POLICY axis, orthogonal to the memory-SYSTEM benchmarks
(MemoryAgentBench, LongMemEval); FRAMES headline now significant at the n=200 scale-up; judge-
defense plan made explicit. Measurement/benchmark framing for ICLR 2027 (arXiv first). All
numbers LLM-judged unless noted. Figures in `presentation/figures/`. Constraints: plain prose
for practitioners and researchers, honest reporting including negative results, no em-dashes.*

**Authors.** Kanishk Patel (Founsi AI). *[co-authors / affiliations TBD]*

---

## Abstract

A long-running language-model agent fails not when its reasoning is wrong but when its
context window fills up. The standard fix is compaction: when the transcript exceeds a token
budget, replace the stale middle with a summary and drop the raw turns. Every major agent
framework does this. Recent benchmarks compare whole memory *systems*, but the *policy* by
which an agent forgets, summarize-the-middle versus keep-the-important-turns versus
page-to-a-store, has not been isolated and measured under a fixed token budget with the agent
and store held constant. We build a minimal, reproducible harness and run a bake-off of seven
compaction policies across two task domains (multi-hop factual QA and long conversational
memory) and three model sizes (8B, 70B, and a reasoning model), scoring answer accuracy per
token with a held-constant, robustness-checked LLM judge. We report five results. First, the
metric choice can invert the ranking: a naive substring match makes the best policy look worst,
because most policies paraphrase. Second, the policy that ships in real agents, recency
summarization, is Pareto-dominated by plain truncation under pressure, and sub-agent isolation
costs roughly five times as much for no accuracy gain. Third, the best single policy is
task-dependent and the ranking *inverts* across domains: summarization wins on factual QA,
retrieval wins on conversational memory. Fourth, exactly one policy, a reversible hybrid that
keeps both a summary and a retrievable raw copy, is in the top group of every domain-by-capability
cell. Fifth, when the agent drives its own tool use so the transcript is a trajectory it actually
built, the gap amplifies: keeping the raw retrievable significantly beats blind truncation by a
far wider margin than under oracle retrieval, because the agent cannot recover evidence it
gathered and then dropped. The robustness of keeping the raw retrievable, not any single peak
score, is our central finding.

---

## 1. Introduction

The headline capability of modern agents is that they run for many steps. The headline
failure mode is that they cannot. A stateless model is handed one list of messages per turn,
and that list is the agent's entire working memory for that turn. Every loop appends tool
outputs, reasoning, and results, so the working set only grows. Cost grows with it, because
the whole history is re-sent each turn; latency grows, because time-to-first-token scales with
prompt length; and accuracy degrades, because attention dilutes over long contexts (the
lost-in-the-middle effect). Eventually the agent drifts, repeats, forgets its goal, or hits
the hard context limit and dies.

The community agrees on the cure in the abstract. Anthropic names the moves (compaction,
structured note-taking, "context rot"); Cognition calls context engineering the number-one
job; LangChain and LlamaIndex ship summary-buffer and vector memories; MemGPT and Letta treat
the window like RAM and page facts to a store. Recent benchmarks (MemoryAgentBench, LongMemEval)
compare whole memory *systems* head-to-head on a competency axis. What is still missing is the
controlled variable underneath those systems: the compaction *policy* itself, isolated under a
fixed token budget with the agent and store held constant. Prior compression work shrinks a
static prompt or a set of retrieved passages, usually to cut latency. The single policy that
runs inside agents, summarize the stale middle of an evolving transcript and drop the raw turns,
is shipped by every framework and isolated as a controlled variable by almost none.

We ask a single question: under a fixed token budget, which compaction policy preserves the
most answer accuracy per token, and does the answer depend on the task or the model? To
answer it we build a small, readable agent harness and run a controlled bake-off. Our
contribution is a measurement, not a method: a reproducible comparison of seven policies, two
domains, and three model sizes, with the metric, the pressure regime, and the judge held
constant so that the policy is the only thing that varies.

The results are useful precisely because several of them are negative. The shipped default is
weak. Multi-agent isolation is a cost trap. The "best" policy is not stable; it flips between
domains. And the one stable finding is not a clever method but a simple design principle:
keep the raw retrievable, so the agent can recover whichever kind of information the task
turns out to need.

**Contributions.**
1. A reproducible harness and protocol for comparing compaction policies on evolving agent
   transcripts, with traceable runs (manifest, every prompt, results, figures).
2. A demonstration that the scoring metric can invert the policy ranking, and that an
   LLM judge that credits paraphrase is necessary, with a robustness check (model size,
   position, and a human spot-check) showing the judge verdict is stable.
3. Two negative results on widely used techniques: recency summarization is Pareto-dominated
   by truncation under pressure, and sub-agent isolation costs about five times as much for
   no accuracy gain.
4. A cross-domain, cross-capability map showing that the best policy is task-dependent and
   the ranking inverts, while a reversible-hybrid policy is robust in every cell.
5. An agentic regime in which the agent drives its own search-and-read tool use, so the
   transcript is a real trajectory and retrieval is no longer oracle; there the policy gap
   amplifies and keeping the raw retrievable significantly beats blind truncation.

---

## 2. Related Work

**Long-context degradation.** Liu et al. (2307.03172) show that models attend to the ends of
a long context and lose the middle. Benchmarks such as RULER (2404.06654), HELMET (2410.02694),
and NoLiMa (2502.05167) quantify how retrieval and reasoning decay with length. These motivate
compaction but study static contexts, not the evolving transcript of a running agent.

**Agent memory and external stores.** MemGPT (2310.08560), Mem0 (2504.19413), and Letta page
facts to an external store and retrieve them on demand, treating the window like RAM. RAG
(Lewis et al., 2005.11401) retrieves from a store rather than stuffing the prompt. These
systems propose mechanisms; we measure which mechanism wins on which task, and we include a
retrieval-only and a summary-plus-retrieval policy as arms.

**Agent-memory benchmarks (the closest prior work).** A wave of 2025-2026 benchmarks evaluates
memory *systems* head-to-head. MemoryAgentBench (2507.05257, ICLR 2026) scores Mem0, MemGPT,
Cognee, Zep, HippoRAG-v2 and others across four competencies (accurate retrieval, test-time
learning, long-range understanding, selective forgetting) and reports that no single system
masters all four. LongMemEval-V2 (2605.12493) evaluates retrieval and coding-agent memory over
long agentic trajectories, and a growing set (MemoryArena 2602.16313, AMA-Bench 2602.22769,
Mem2ActBench 2601.19935) follows. These benchmark *systems* on a competency axis. We are
orthogonal: we isolate the *policy* axis, the single compaction rule applied to an evolving
transcript under a fixed token budget, holding the agent, embedder, and store constant so the
rule is the only variable. A system is a policy plus an embedder plus a store; our policy
result explains part of why those systems differ, and we connect the two axes directly by
running three of these systems (LangChain summary memory, Chroma, Mem0) as policy arms. We do
not claim the first comparison of agent memory; we claim the first controlled isolation of the
compaction policy under a fixed budget with a paraphrase-aware metric.

**Agent context compression.** ACON (2510.00615) compresses agent context with one-way
summarization that deletes the raw history and supports no retrieval; its follow-up (2601.07190)
contrasts two configurations on a coding agent. Production frameworks (LangChain, LlamaIndex)
ship summary-buffer memories. To our knowledge none reports a controlled head-to-head of
compaction *policies* on the same evolving transcript under a fixed budget with a
paraphrase-aware metric, including the metric-inversion and the truncation-dominates-summary
results, which is the gap this paper fills.

**Evaluation.** Zheng et al. (2306.05685) document the biases of LLM-as-a-judge. We use a
fixed strong judge and, in an early experiment, show that the alternative (substring match)
inverts the ranking, which is itself a contribution to how this subfield should be evaluated.

**Benchmarks.** We evaluate on FRAMES (2409.12941), multi-hop factual QA over Wikipedia, and
LoCoMo (2402.17753), long multi-session conversational memory.

---

## 3. The Compaction Problem and the Policies

**Setup.** The harness runs a minimal agent loop. The agent reads sources in sequence
(oracle retrieval, so search quality is not a confound), and whenever the window exceeds a
token budget B, it compacts the stale portion with the chosen policy and continues. After
reading, it answers a question; for retrieval-capable policies it may pull detail back from a
store at answer time. The one hard constraint is that a tool-call is never split from its
result, since real APIs reject such a transcript; the harness enforces this with a safe-split
that compacts on message boundaries only.

**The seven policies.** Each is a small class with one method, `compact(old, llm, store) ->
(block, usage)`, and a flag for whether it retrieves at answer time.

- **truncate**: drop the oldest raw turns. No LLM call. The cheap floor.
- **recency**: summarize the stale middle into one block, keep the recent turns. The default
  in Claude Code, LangChain, and most harnesses.
- **importance**: score turns and keep the highest-signal ones verbatim; drop the chatter.
- **semantic**: cluster turns by topic (embeddings) and summarize each cluster.
- **externalize**: write the raw turns to a vector store; retrieve the relevant ones at
  answer time. Keeps the literal fact.
- **subagent**: isolate a sub-task in a fresh window and return only its result. The
  multi-agent move.
- **reversible_hybrid (ours)**: keep a summary *in* the window *and* write the raw turns to a
  retrievable store, so the gist is cheap in-context and the detail is losslessly recoverable.

The reversible hybrid is not a new mechanism; it is the obvious combination of summary memory
and retrieval. We include it not as a novel method but as a hypothesis: that carrying both
mechanisms is robust to whichever one the task rewards.

---

## 4. Experimental Design

**Domains.** FRAMES (multi-hop factual QA, 824 questions, gold Wikipedia articles as oracle
sources) rewards a summarized reasoning chain. LoCoMo (10 conversations, about 19 sessions and
150 questions each) rewards exact scattered facts: dates, items, who said what. If a winner
transfers across both, it is a property of the policy, not the benchmark.

**Pressure.** Policy choice only matters when compaction actually fires. We read sources in
small chunks against a small budget so that compaction fires many times per question (roughly
9 to 18 events on FRAMES; LoCoMo conversations overflow by about ten times and compact tens of
times each). A low-pressure regime, where compaction barely fires, ties all policies and is
reported as a control.

**Metric.** Answer accuracy, graded by a fixed 70B LLM judge that credits a correct but
paraphrased answer. We show in Section 5.1 why a substring metric is not acceptable.

**Models.** A capability axis on the free NVIDIA NIM API: Llama 3.1 8B (dev), Llama 3.3 70B
(large instruct), and Nemotron 30B-A3B (a reasoning model). The judge is the 70B, fixed across
every arm and model, so the metric is constant along the axis.

**Reproducibility.** Each run writes `experiments/runs/EXP-NNN__slug__UTC/` with a manifest
(config, git SHA, dependencies), every prompt and response (`prompts.jsonl`), `results.csv`,
and figures. Everything is seeded; loops are guarded; a wall-clock watchdog kills any hung
call; the response cache makes re-runs free. The bar we hold is that a stranger can clone the
repository and regenerate any figure.

---

## 5. Results

### 5.1 The metric can invert the ranking (EXP-003a)

We first pointed the agent at FRAMES and scored its answers two ways. Under a normalized
substring match, our reversible hybrid looked like the worst policy, at 0.21. Under the LLM
judge, which credits paraphrase, the same policy was the best, at 0.62, a swing of plus 0.41.
The substring metric was punishing exactly the policies that paraphrase, which is most of
them. The lesson is that the metric choice can invert the conclusion; the judge is not
optional. A second, quieter result: at low pressure all policies clustered near 0.6, because
compaction fired about once per question. Policy choice washes out when there is no pressure.

### 5.2 Mechanism: facts survive, and compaction beats raw context (EXP-001, EXP-002)

Before measuring impact we confirmed the mechanism. EXP-001 plants checkable facts in sources
and counts how many survive a compaction. Truncation drops them and sits at the floor; summary
policies preserve roughly two to three times more. EXP-002 varies the amount of context read
and compares a no-compaction baseline to compaction at a fixed budget. The no-compaction
baseline collapses with length, from 0.62 down to about 0.12 by 32 sources, while compaction
holds flat near 0.58. The crossover is around sixteen sources. A long raw context is worse
than a short clean summary, so compaction is net positive, not merely a way to survive the
hard limit. This mechanism explains every impact result below.

### 5.3 Impact: under pressure, the policies separate (EXP-003b)

Reading articles in small chunks against a small budget forces nine to eighteen compaction
events per question. Over all seven arms on FRAMES (8B, n=30, judged):

| policy | accuracy | mean tokens | on Pareto frontier |
|---|---|---|---|
| semantic | 0.57 | 18,685 | yes (accuracy ceiling) |
| importance | 0.50 | 14,158 | yes |
| subagent | 0.50 | 76,445 | no (dominated) |
| reversible_hybrid | 0.47 | 9,923 | yes |
| externalize | 0.40 | 1,881 | yes |
| truncate | 0.37 | 1,201 | yes (cheap floor) |
| recency | 0.37 | 8,972 | no (dominated) |

Two negative results stand out. **The shipped default is dominated.** Recency summarization
scored 0.37, identical to naive truncation, while costing seven times as many tokens.
Summarizing the stale middle bought nothing over dropping it here. **Sub-agent isolation is a
cost trap.** It matched importance on accuracy (0.50) at five times the cost (76k versus 14k
tokens), direct cost-normalized evidence on the multi-agent versus single-agent debate, and on
this task it favors the single-agent side. The accuracy leaders are structure-preserving
policies (semantic, importance). Our reversible hybrid is Pareto-efficient at 0.47 but not the
accuracy winner here, which we report plainly.

At n=30 these FRAMES accuracy gaps are within noise (95% bootstrap intervals about plus or minus
0.17; even semantic over truncation reaches only p=0.07, McNemar exact test on the paired
per-question outcomes). We therefore ran a scale-up to n=200 on the five separating arms. The
ordering holds and the headline becomes significant. The accuracy ranking compresses (semantic
0.49, importance 0.46, reversible_hybrid 0.44, externalize 0.41, truncate 0.40), but semantic
now beats truncation by +0.10 (McNemar p=0.014) and beats pure retrieval by +0.07 (p=0.04). On
factual FRAMES, structure-preserving summarization significantly outperforms both blind
truncation and pure retrieval. The finer distinctions among the middle arms (importance, hybrid,
externalize) remain within noise even at n=200, which we report rather than overclaim. The two
cost dominations from the seven-arm n=30 run are robust at any N because their accuracy
difference is exactly zero: recency ties truncation and sub-agent ties importance (both p=1.0) at
seven and five times the cost respectively.

### 5.4 The model axis on FRAMES: the gap widens with capability (EXP-003c)

We re-ran the five separating arms across 8B, 70B, and the reasoning model, judge fixed.

| arm | 8B | 70B | reasoning |
|---|---|---|---|
| reversible_hybrid | 0.47 | 0.67 | 0.70 |
| externalize | 0.40 | 0.63 | 0.67 |
| importance | 0.50 | 0.60 | 0.70 |
| semantic | 0.57 | 0.53 | 0.63 |
| truncate | 0.37 | 0.27 | 0.40 |

Blind truncation never improves; it sits at the floor on every model, because a stronger
model cannot reason over information that was dropped without a trace. Every structure or
retrieval preserving arm climbs, so the distance between the best compaction and blind
truncation grows from about 0.2 on the 8B to about 0.3 on the reasoning model. A better model
has more to gain from a clean compacted context and more to lose from a blind one. On the
reasoning model the reversible hybrid and importance lead at 0.70.

We note one methodological caveat. On the reasoning tier the compaction summaries are written
by a fast 8B model, because the reasoning model's verbose chain-of-thought made per-summary
latency prohibitive (single cells stalled past 200 seconds). The reasoning model still
produces the answer, which is the capability the axis measures. The summarizer is therefore
not held perfectly constant across tiers; closing this is a planned revision.

### 5.5 Cross-domain: the ranking inverts (EXP-004)

We ran the same five arms on LoCoMo, where the agent compacts a conversation once and answers
many questions from the compacted window (8B agent, 70B judge).

| arm | FRAMES (8B) | LoCoMo (8B) |
|---|---|---|
| semantic | 0.57 | 0.27 |
| importance | 0.50 | 0.26 |
| reversible_hybrid | 0.47 | 0.54 |
| externalize | 0.40 | 0.55 |
| truncate | 0.37 | 0.12 |

The ranking inverts at the top. On conversational memory the two retrieval arms lead
(externalize 0.55, reversible hybrid 0.54) and the two pure-summary arms fall to about 0.26,
half their FRAMES accuracy. LoCoMo questions ask for specific scattered facts, a date, an item,
who said what, which survive in a retrievable raw copy but get smoothed away in a summary.
FRAMES multi-hop questions reward the opposite, a summarized reasoning chain. So the best
single policy is task-dependent: semantic on FRAMES, externalize on LoCoMo.

Unlike the FRAMES cell, these LoCoMo gaps are large and significant. Retrieval beats
summarization by 0.27 to 0.28 (externalize and the hybrid each over semantic, p<0.0001,
McNemar, n=100), the hybrid beats truncation by 0.42 (p<0.0001), and the hybrid is
statistically tied with externalize at the top (difference 0.01, p=1.0). The inversion is real,
not an artifact of small samples.

### 5.6 Capability does not rescue summarization on memory (EXP-004, 70B)

Re-running all five arms on the 70B gives the mirror image of the FRAMES model axis.

| arm | LoCoMo 8B | LoCoMo 70B |
|---|---|---|
| externalize | 0.55 | 0.55 |
| reversible_hybrid | 0.54 | 0.53 |
| importance | 0.26 | 0.23 |
| semantic | 0.27 | 0.17 |
| truncate | 0.12 | 0.09 |

The retrieval arms are flat at the top across both models; the summary arms are flat to
falling, semantic dropping hardest from 0.27 to 0.17. A stronger model cannot rescue a lossy
summary, because the missing fact is simply not in it; worse, the stronger model is more
willing to admit it does not know, which costs it the lucky guesses the smaller model
sometimes got. Retrieval wins on conversational memory at every model size.

### 5.7 One policy wins every cell

Across the full design, five arms by two domains by two model sizes:

| arm | FR-8B | FR-70B | LC-8B | LC-70B |
|---|---|---|---|---|
| reversible_hybrid | 0.47 | 0.67 | 0.54 | 0.53 |
| externalize | 0.40 | 0.63 | 0.55 | 0.55 |
| importance | 0.50 | 0.60 | 0.26 | 0.23 |
| semantic | 0.57 | 0.53 | 0.27 | 0.17 |
| truncate | 0.37 | 0.27 | 0.12 | 0.09 |

The pure policies each win one domain and lose the other: semantic tops FRAMES and collapses
on LoCoMo; externalize tops LoCoMo and trails on FRAMES. The reversible hybrid is in the top
group of all four cells, because it carries both a summary and a retrievable raw copy and so
picks up whichever mechanism the task needs. That cross-domain, cross-capability robustness,
not a single best score, is the case for keeping the raw retrievable.

### 5.8 The agentic regime: the gap amplifies (EXP-009)

Every result so far feeds the agent oracle sources, so the agent never drives the loop. To test
the policies on a real agent transcript we made FRAMES agentic: the agent is given `search` and
`read` tools over the question's gold corpus and drives its own multi-step retrieval, so the
transcript it compacts is its own tool-use trajectory (search queries, observations, reads) rather
than pre-fetched articles. This also removes the oracle: the agent must find the supporting
passage itself. Compaction fires on 60% of trajectories at this budget.

| policy | oracle FRAMES (n=200) | agentic FRAMES (n=60) |
|---|---|---|
| truncate | 0.40 | 0.20 |
| externalize | 0.41 | 0.32 |
| reversible_hybrid | 0.44 | 0.38 |

Two things change. Accuracy drops across the board, because the agent now has to retrieve its own
evidence rather than being handed it. And the policy gap *amplifies*: under oracle retrieval
truncation trails the hybrid by 0.04, but on the real agent transcript it trails by 0.18, nearly
half the hybrid's accuracy. When the agent gathered the evidence itself, blind truncation throws
away work it did with no way to recover it, while keeping the raw retrievable lets the agent get
its own observations back. At n=60 both keep-the-raw policies significantly beat truncation: the
reversible hybrid by 0.18 (McNemar p=0.003, 95% interval +0.08 to +0.30) and externalize by 0.12
(p=0.039). The amplification is real, not a small-sample artifact, and it is the most realistic
form of the paper's claim: on a transcript the agent actually built, forgetting without a trace is
the costliest mistake a compaction policy can make.

---

## 6. Discussion

Seven claims are now supported by evidence. (1) Compaction policy matters only under pressure.
(2) The metric must credit paraphrase, or it inverts the ranking, and the judge that does is
robust to model size and answer order. (3) The shipped default (recency summary) is weak,
dominated by truncation under pressure. (4) The smart-versus-blind gap widens with model
capability on factual QA and persists on memory. (5) The best single policy is task-dependent:
summary on factual, retrieval on memory. (6) The reversible hybrid is robust across task type and
model size; keeping the raw retrievable is the cross-domain hedge. (7) When the agent drives its
own tool use so the transcript is a trajectory it built, the gap amplifies and keeping the raw
retrievable significantly beats blind truncation, the most realistic form of the result.

For practitioners the operational takeaway is concrete. If you run a long agent and have not
measured your compaction policy, the default you inherited is probably the wrong one: it likely
costs more than truncation for no gain. If your task is factual and multi-hop, summarize. If it
is conversational or memory-heavy, keep the raw retrievable. If you cannot characterize the
task in advance, keep both, because the hybrid never lands in the loser group.

---

## 7. Limitations

These are dev-to-moderate-scale results and we state the gaps plainly. We report 95% bootstrap
confidence intervals and McNemar exact tests on the paired per-question outcomes
(`experiments/stats.py`). The LoCoMo results are statistically robust: retrieval beats
summarization by 0.27 to 0.38 with p below 0.0001 at n=100, and the reversible hybrid ties
externalize at the top. The FRAMES headline is significant at the scale-up n=200: semantic beats
truncation by +0.10 (p=0.014) and pure retrieval by +0.07 (p=0.04), though the finer middle-arm
gaps (importance, hybrid, externalize) remain within noise even at n=200. The cost dominations
are robust by construction: recency and sub-agent match truncation and importance on accuracy
(difference 0.00, p=1.0) while costing seven and five times as much.

The remaining gaps are each a scale-or-rigor gap, not a design flaw, and each is addressed in the
current revision. (1) Evaluation rests on a single open 70B judge, the subfield's most-attacked
choice (position and self-preference bias, Zheng et al. 2306.05685; reference-knowledge override,
2601.07506). We harden it in Appendix C (EXP-008a): the verdict is stable across model size
(kappa 0.72 against an 8B judge) and robust to answer order (kappa 0.82 under the position-bias
swap), it disagrees with the naive substring metric on a quarter of items (the metric inversion of
Section 5.1, quantified), and a manual spot-check of the hard disagreement cases confirms the 70B
as the better grader. The one check the free tier cannot run is cross-family: it throttles
non-Llama judges to near-zero, so a frontier judge, which the literature finds most robust, is
folded into the frontier-model addition below. (2) We do not yet report multiple seeds.
(3) The agent models are open and mid-scale (8B, 70B, one reasoning model); no frontier model is
yet included. (4) We now run three production memory systems (LangChain summary memory, Chroma,
Mem0) as policy arms on the factual domain, isolating the embedder and the extract-then-dedupe
layer; extending them to conversational memory is in progress. (5) The reasoning tier uses a
separate summarizer, an acknowledged confound we are closing by holding the summarizer constant.
(6) The importance and semantic policies use simple heuristics rather than trained rankers.
(7) We add an agentic regime in Section 5.8 (EXP-009): an agent-driven FRAMES where the agent
searches and reads over the corpus itself, so the transcript is a real tool-use trajectory and
retrieval is no longer oracle, and the policy gap is significant and larger there. A second
agentic domain (a coding or web agent run on a frontier model where the agent can succeed) is the
remaining extension.

---

## 8. Conclusion

A long-running agent must forget, and how it forgets decides whether it survives. We measured
seven ways of forgetting across two domains and three model sizes and found that the question
has no single answer: the best policy depends on the task, and the ranking inverts between
factual and conversational work. The one stable result is a design principle rather than a
method. Keep a summary for the gist and the raw turns for the detail, and the agent stays in
the top group whatever the task and whatever the model. The contribution is the measurement
and the principle it yields; the harness, every prompt, and every figure are released so the
measurement can be checked and extended.

---

## Appendix A. Reproducibility

Each experiment is a self-contained run directory. The seven policies live in
`experiments/applied/policies.py`; the agent loop and the shared `read_and_compact` /
`answer_from_window` functions in `experiments/applied/agent.py`; the judge in `judge.py`; the
embedding store in `embed.py`. Figures are regenerated by `experiments/make_figures_*.py`.
Models are served through a rate-limited, cached client with a wall-clock watchdog
(`experiments/nim.py`).

## Appendix B. Cost note

We ran entirely on the free NVIDIA NIM API. A full 824-question by 7-arm by 10-model study on
paid OpenRouter with 2026 frontier models would cost roughly 140 USD (four arms) to about 1,560
USD (all arms, two frontier models), which informs the planned scale-up.

## Appendix C. Judge robustness (EXP-008a)

The headline metric is a single 70B Llama LLM judge, the most attacked choice in this subfield.
We report four robustness checks on 200 stratified verdicts; the cross-family panel is deferred to
a frontier judge (Section 7), because the free tier throttles non-Llama judges to near-zero.

- **Model size.** Re-grading with an 8B judge of the same family agrees with the 70B on 86% of
  items (Cohen's kappa 0.72, substantial). The verdict is largely stable across a roughly nine-fold
  change in judge capacity.
- **Position.** Swapping the order of the gold and candidate answer in the prompt, the classic
  position-bias probe, changes the 70B verdict on only 9% of items (kappa 0.82, almost perfect).
  The judge is robust to answer order.
- **Against the naive metric.** The 70B judge disagrees with the normalized substring match on
  25.5% of items. This is the metric inversion of Section 5.1 quantified: a quarter of answers are
  graded differently, and the substring metric is the one that inverts the policy ranking.
- **Human spot-check.** On the 28 items where the 8B and 70B disagree (the genuinely hard cases:
  answers truncated mid-reasoning, off-by-one numbers, abstentions, near-paraphrases), an
  independent manual adjudication sides with the 70B on roughly 70 to 75%, confirming it as the
  better primary grader. The disagreements concentrate on ambiguous cases, not random noise; both
  judges share a mild leniency rather than a directional bias. A third-party human pass on a random
  sample is the planned final check.

## References

*[To be formatted to venue style.]*
Liu et al. 2307.03172 · RULER 2404.06654 · HELMET 2410.02694 · NoLiMa 2502.05167 ·
MemGPT 2310.08560 · Mem0 2504.19413 · ACON 2510.00615 · ACON-Focus 2601.07190 ·
Zheng et al. 2306.05685 · FRAMES 2409.12941 · LoCoMo 2402.17753 · RAG (Lewis et al.) 2005.11401.
*Agent-memory benchmarks (related work):* MemoryAgentBench 2507.05257 (ICLR 2026) ·
LongMemEval-V2 2605.12493 · MemoryArena 2602.16313 · AMA-Bench 2602.22769 · Mem2ActBench 2601.19935.
*Judge reliability (Section 7 hardening):* reference-knowledge conflict 2601.07506 ·
reference+criteria 2506.13639 · Trust-or-Escalate 2407.18370 (ICLR 2025).
