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
gathered and then dropped. To show the taxonomy is the right axis, we map twelve production
memory frameworks to it from their source code, and find that the most capable systems already
converge on this reversible policy. The robustness of keeping the raw retrievable, not any single
peak score, is our central finding.

---

## 1. Introduction

The headline capability of modern agents is that they run for many steps. The headline
failure mode is that they cannot. A stateless model is handed one list of messages per turn,
and that list is the agent's entire working memory for that turn. Every loop appends tool
outputs, reasoning, and results, so the working set only grows. Cost grows with it, because
the whole history is re-sent each turn; latency grows, because time-to-first-token scales with
prompt length; and accuracy degrades, because attention dilutes over long contexts (the
lost-in-the-middle effect) [@liu2023lost; @hsieh2024ruler; @hong2025context]. Eventually the
agent drifts, repeats, forgets its goal, or hits the hard context limit and dies.

The community agrees on the cure in the abstract. Anthropic names the moves, compaction,
structured note-taking, and "context rot" [@anthropic2026context; @rajasekaran2025effective];
Cognition argues that context engineering is the central job of building an agent
[@cognition2025don]; LangChain and LlamaIndex ship summary-buffer and vector memories
[@langchainndlangchaindoc; @llamaindexndllamaindexdoc]; MemGPT and Letta treat the window like
RAM and page facts to a store [@packer2023memgpt]. Recent benchmarks compare whole memory
*systems* head-to-head on a competency axis [@hu2025evaluating; @wu2024longmemeval]. What is
still missing is the controlled variable underneath those systems: the compaction *policy*
itself, isolated under a fixed token budget with the agent and store held constant. Prior
compression work shrinks a static prompt or a set of retrieved passages, usually to cut latency
[@jiang2023llmlingua; @mu2023learning]. The single policy that runs inside agents, summarize the
stale middle of an evolving transcript and drop the raw turns, is shipped by every framework
(Section 2) and isolated as a controlled variable by almost none.

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
6. A grounding of the policy taxonomy in twelve production memory frameworks, read from their
   source code, showing that each policy is a mechanism some framework ships, that the
   widely-deployed defaults are exactly the policies we find weak, and that the most capable
   systems (MemGPT, Letta, Cognee, AutoGPT) already converge on the reversible hybrid.

---

## 2. Related Work

Compaction sits at the intersection of several literatures: why long context hurts, how agents
store memory, what policy deployed frameworks actually use, how memory systems are benchmarked,
how prompts are compressed, and how all of this is scored. We cover each and state precisely
what we add.

**Long-context degradation motivates compaction.** Liu et al. [@liu2023lost] show that models
attend to the start and end of a long context and lose the middle. A line of benchmarks
quantifies how retrieval and reasoning decay with length: RULER [@hsieh2024ruler], HELMET
[@yen2024helmet], NoLiMa [@modarressi2025nolima], BABILong [@kuratov2024babilong], and LongBench
v2 [@bai2024longbench], with position bias traced to the attention mechanism itself
[@wu2025emergence]. The effect is not only retrieval failure: longer input degrades accuracy even
when the needle is retrieved perfectly [@du2025context], an effect practitioners call "context
rot" [@hong2025context]. These studies measure static contexts, not the evolving transcript of a
running agent, which is what a compaction policy acts on.

**Agent memory architectures and external stores.** A second line gives agents an explicit
memory. Retrieval-augmented generation pulls from a store instead of stuffing the prompt
[@lewis2020retrieval]. MemGPT casts the window as paged virtual memory, summarizing on overflow
and paging facts to an external store [@packer2023memgpt]; Generative Agents keep a memory stream
scored by recency, importance, and relevance, with periodic reflection [@park2023generative].
MemoryBank [@zhong2023memorybank], RecurrentGPT [@zhou2023recurrentgpt], SCM [@wang2023scm], and
A-MEM [@xu2025mem] add forgetting curves, recurrent summaries, controllers, and agentic
note-linking. A knowledge-graph branch (HippoRAG [@gutirrez2024hipporag; @gutirrez2025from], Zep
and Graphiti [@rasmussen2025zep], Mem0 [@chhikara2025mem]) extracts entities and relations rather
than storing raw turns. Each work proposes a mechanism; we measure which mechanism wins on which
task, and include retrieval-only, summary-only, and summary-plus-retrieval policies as arms.

**What policy do deployed frameworks actually use?** To check that our taxonomy is the right
axis and not an invented one, we read the source of twelve production memory frameworks and
mapped each to the policy it implements (Table 1; Figure 1). Every one of our policies is a shipped
mechanism, and the mapping is informative: the most widely deployed defaults are truncation and
recency summarization (LangChain's window and summary-buffer memories [@langchainndlangchaindoc],
OpenAI's `truncation_strategy` and compaction session [@openaindopenaiassistdoc], Anthropic's
tool-result clearing and auto-compaction [@anthropicndanthropiccladoc]), while the most capable
agent stacks (MemGPT [@packer2023memgpt], Letta, AutoGPT, Cognee [@markovic2025optimizing])
converge on a reversible hybrid that keeps an in-window summary and pages the raw turns to a
retrievable store. This grounding shows the policy axis is real and under-measured, and it means
our negative result on recency summarization (Section 5.3) lands on the single most common
default.

Table: What compaction policy production memory frameworks implement, by reading their source
(mapped to the taxonomy of Section 3). Defaults (top) are truncation and recency; the most
capable stacks (middle) converge on the reversible hybrid; the structured-memory family (bottom)
motivates our eighth category. "Retrieves" means it pages content back in at answer time.

| Framework | Native mechanism(s) | Our policy | Retrieves |
|---|---|---|---|
| LangChain / LangGraph [@langchainndlangchaindoc] | window / `trim_messages`, summary-buffer | truncate, recency | no |
| OpenAI Assistants / Agents [@openaindopenaiassistdoc] | `truncation_strategy`, compaction session | truncate, recency | no |
| LlamaIndex [@llamaindexndllamaindexdoc] | buffer, summary-buffer, vector, memory blocks | truncate, recency, externalize | yes |
| Anthropic Claude, Claude Code [@anthropicndanthropiccladoc] | clear-tool-uses, compaction, memory tool, subagents | truncate, recency, externalize, subagent | yes |
| MemGPT [@packer2023memgpt] | recursive summary + paging to recall/archival | reversible hybrid | yes |
| Letta [@packer2023memgpt] | sliding-window compactor + recall/archival stores | reversible hybrid | yes |
| AutoGPT / BabyAGI [@babyagindautogptandbadoc] | running summary + vector store; vector store | reversible hybrid; externalize | yes |
| Generative Agents [@park2023generative] | memory stream, recency+importance+relevance, reflection | externalize, importance | yes |
| Mem0 [@chhikara2025mem] | extract-then-dedupe facts to vector / graph store | structured (externalize) | yes |
| Zep / Graphiti [@rasmussen2025zep] | episode to temporal knowledge graph | structured (reversible) | yes |
| HippoRAG [@gutirrez2024hipporag] | OpenIE knowledge graph + Personalized PageRank | structured (externalize) | yes |
| Cognee [@markovic2025optimizing] | cognify to graph + per-chunk summaries + raw chunks | structured (reversible hybrid) | yes |

![The eight compaction policies as a map, annotated with the production frameworks that ship each (Table 1). Vertical axis: what survives in the window (raw turns, a free-text summary, or structured facts); horizontal axis: whether dropped content is recoverable from a store. The widely-deployed defaults sit in the lossy column (truncate, recency); the most capable production stacks live in the recoverable column, and converge on our reversible hybrid.](presentation/figures/policy_taxonomy_v1.pdf){width=92%}

**Agent-memory benchmarks (the closest prior work).** A wave of 2024-2026 benchmarks evaluates
memory *systems* head-to-head. MemoryAgentBench [@hu2025evaluating] scores Mem0, MemGPT, Cognee,
Zep, and HippoRAG across accurate retrieval, test-time learning, long-range understanding, and
selective forgetting, and reports that no single system masters all four. LongMemEval
[@wu2024longmemeval] and its successor LongMemEval-V2 [@wu2026longmemeval] evaluate long-term and
agentic memory over multi-session histories, and the stream continues [@tavakoli2025beyond]. We
evaluate on FRAMES [@krishna2025fact], multi-hop factual QA over Wikipedia, and LoCoMo
[@maharana2024evaluating], long multi-session conversational memory. These works benchmark
*systems* on a competency axis; we are orthogonal. A system is a policy plus an embedder plus a
store; we isolate the *policy*, holding the agent, embedder, and store constant so the rule is
the only variable, and connect the two axes by running three production systems (LangChain
summary memory, Chroma, Mem0) as policy arms (Section 5.9). We do not claim the first comparison
of agent memory; we claim the first controlled isolation of the compaction policy under a fixed
budget with a paraphrase-aware metric.

**Context and prompt compression.** A parallel literature compresses a mostly static prompt to
cut cost or latency: token pruning with LLMLingua and its variants [@jiang2023llmlingua;
@pan2024llmlingua; @jiang2023longllmlingua], soft-prompt and autoencoder methods (gisting
[@mu2023learning], AutoCompressors [@chevalier2023adapting], ICAE [@ge2023context],
[@li2023compressing]), and retrieved-passage compression (RECOMP [@xu2023recomp]). Closer to
agents, recursive summarization compresses long inputs and dialogues [@wu2021recursively;
@wang2023recursively], and ACON compresses agent context with one-way summarization that deletes
the raw history and supports no retrieval [@kang2025acon]. These compress a prompt or a passage
set; we compact an evolving multi-turn transcript and compare the policy choice itself, including
a reversible variant that keeps the raw recoverable, which one-way summarization cannot.

**LLM-as-judge evaluation.** We score answers with a fixed LLM judge, the standard for
paraphrase-tolerant grading [@zheng2023judging], and inherit its known failure modes: position
and verbosity bias [@wang2023large; @ye2024justice], self-preference [@panickssery2024llm], and,
most relevant here, reference-knowledge conflict, where a judge overrides the gold reference with
its own parametric knowledge [@lee2026judging]. We harden the judge against these (Appendix C)
following the inter-judge-agreement, jury, and escalation literature [@verga2024replacing;
@jung2024trust; @bavaresco2024llms], and we show (Section 5.1) that the alternative, a substring
metric, inverts the policy ranking, which we believe matters for how this subfield is scored.

---

## 3. The Compaction Problem and the Policies

**Setup.** The harness runs a minimal agent loop. The agent reads sources in sequence
(oracle retrieval, so search quality is not a confound), and whenever the window exceeds a
token budget B, it compacts the stale portion with the chosen policy and continues. After
reading, it answers a question; for retrieval-capable policies it may pull detail back from a
store at answer time. The one hard constraint is that a tool-call is never split from its
result, since real APIs reject such a transcript; the harness enforces this with a safe-split
that compacts on message boundaries only.

**The policies.** Each benchmarked policy is a small class with one method, `compact(old, llm,
store) -> (block, usage)`, and a flag for whether it retrieves at answer time. We run seven, each
shipped by some production system (Table 1):

- **truncate**: drop the oldest raw turns. No LLM call. The cheap floor. Shipped as LangChain's
  window memory and `trim_messages`, OpenAI's `last_messages`, and Anthropic's tool-result
  clearing.
- **recency**: summarize the stale middle into one block, keep the recent turns. The default in
  Claude Code auto-compaction, LangChain's summary-buffer, and OpenAI's compaction session.
- **importance**: score turns and keep the highest-signal ones verbatim; drop the chatter. The
  scoring half of Generative Agents' retrieval.
- **semantic**: cluster turns by topic (embeddings) and summarize each cluster.
- **externalize**: write the raw turns to a vector store; retrieve the relevant ones at answer
  time. Keeps the literal fact. The whole design of BabyAGI and HippoRAG, and Generative Agents'
  memory stream.
- **subagent**: isolate a sub-task in a fresh window and return only its result. The multi-agent
  move; Claude Code's sub-agents.
- **reversible_hybrid (ours)**: keep a summary *in* the window *and* write the raw turns to a
  retrievable store, so the gist is cheap in-context and the detail is losslessly recoverable. Not
  a new mechanism: it is what the most capable production stacks already converge on (MemGPT's
  summarize-then-page, Letta's compactor-plus-recall, AutoGPT's running-summary-plus-vector-store).

We also map, but do not benchmark, an eighth family:

- **structured / graph memory**: distill turns into typed facts or a knowledge graph and retrieve
  over that structure rather than over raw text (Mem0, Zep and Graphiti, HippoRAG, Cognee). It is a
  distinct policy: the in-store artifact is neither the raw turn (externalize) nor a free-text
  summary (recency) but an extracted, deduplicated structure. We exclude it from the controlled
  bake-off because it changes the store representation, not just the compaction rule, so it is a
  system difference rather than a policy difference under our fixed-store design. We treat it as
  future work and discuss it where it bears on the results (Section 5.9).

We include the reversible hybrid not as a novel method but as a hypothesis, that carrying both
summary and retrieval is robust to whichever one the task rewards, which Table 1 shows the field
has independently adopted.

---

## 4. Experimental Design

**Domains.** FRAMES (multi-hop factual QA, 824 questions, gold Wikipedia articles as oracle
sources) rewards a summarized reasoning chain. LoCoMo (10 conversations, about 19 sessions and
150 questions each) rewards exact scattered facts: dates, items, who said what. If a winner
transfers across both, it is a property of the policy, not the benchmark.

**Pressure.** Policy choice only matters when compaction actually fires. We read sources in
small chunks against a small budget so that compaction fires repeatedly per question (a median
of about five events on FRAMES and a mean of nine, up to the mid-60s on the heaviest questions;
LoCoMo conversations overflow by about ten times and compact tens of times each). A low-pressure
regime, where compaction barely fires, ties all policies and is reported as a control.

**Metric.** Answer accuracy, graded by a fixed 70B LLM judge that credits a correct but
paraphrased answer. We show in Section 5.1 why a substring metric is not acceptable.

**Models.** A capability axis on the free NVIDIA NIM API: Llama 3.1 8B (dev), Llama 3.3 70B
(large instruct), and Nemotron 30B-A3B (a reasoning model). The judge is the 70B, fixed across
every arm and model, so the metric is constant along the axis.

**Policy fidelity.** Our seven policies are minimal, readable reimplementations chosen so the
*rule* is the only variable, not faithful clones of any one framework. The two we benchmark
against their real counterparts, recency against LangChain's `ConversationSummaryBufferMemory`
(Section 5.9) and the three memory backends (Section 5.9), match the production behavior closely.
The others are deliberately simple: `importance` and `semantic` use heuristic scorers and
embedding clusters rather than the trained or LLM-driven rankers a system like Generative Agents
or Mem0 would use, so they are lower bounds on what a tuned version of that policy could achieve.
We read each framework's source (Table 1) to keep the reimplementations honest about which
mechanism they stand in for, and we flag the remaining gaps in Section 7.

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

![Needle recall versus context length (EXP-002). The no-compaction baseline degrades with length while a fixed-budget compaction holds flat; they cross near sixteen sources, so compacting early is net-positive.](presentation/figures/EXP-002_recall_vs_length_v1.pdf){width=78%}

### 5.3 Impact: under pressure, the policies separate (EXP-003b)

Reading articles in small chunks against a small budget forces repeated compaction, a median of
about five events per question and a mean of nine (up to the mid-60s on the heaviest questions).
Over all seven arms on FRAMES (8B, n=30, judged):

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

![Accuracy versus cost on FRAMES under pressure (EXP-003b, 8B, n=30). The structure- and retrieval-preserving policies sit on the cost-quality frontier; recency (the shipped default) and sub-agent are dominated, costing far more for no accuracy gain.](presentation/figures/EXP-003b_pareto_v1.pdf){width=80%}

### 5.4 The model axis on FRAMES: the gap widens with capability (EXP-003c)

We re-ran the five separating arms across 8B, 70B, and the reasoning model, judge fixed.

| arm | 8B | 70B | reasoning |
|---|---|---|---|
| semantic | 0.57 | 0.67 | 0.63 |
| externalize | 0.40 | 0.63 | 0.67 |
| importance | 0.50 | 0.60 | 0.70 |
| reversible_hybrid | 0.47 | 0.53 | 0.70 |
| truncate | 0.37 | 0.27 | 0.40 |

Blind truncation never improves; it sits at the floor on every model, because a stronger
model cannot reason over information that was dropped without a trace. Every structure or
retrieval preserving arm climbs, so the distance between the best compaction and blind
truncation grows from about 0.2 on the 8B to about 0.3 on the reasoning model. A better model
has more to gain from a clean compacted context and more to lose from a blind one. On the 70B
the structure-preserving summary leads (semantic 0.67) and on the reasoning model the
reversible hybrid and importance lead at 0.70.

We note one methodological caveat about the compaction summarizer. The 70B column holds the
summarizer constant at the 8B; an earlier 70B run that summarized its own transcript inflated
the reversible hybrid to 0.67, which the experiment registry flags as a summarizer artifact, so
we use the corrected, summarizer-held-constant run here. On the reasoning tier the summaries are
likewise written by the fast 8B model, because the reasoning model's verbose chain-of-thought
made per-summary latency prohibitive (single cells stalled past 200 seconds); the reasoning
model still produces the answer, which is the capability the axis measures. The summarizer held
constant across the 8B and 70B tiers is the 8B, so the policy is the only variable there; the
reasoning tier shares that 8B summarizer rather than its own, which we report rather than smooth
over.

![The smart-versus-blind gap widens with capability on FRAMES (EXP-003c). Every structure- or retrieval-preserving arm climbs from the 8B to the reasoning model while blind truncation stays at the floor, so the distance grows from about 0.2 to about 0.3.](presentation/figures/EXP-003c_modelaxis_v1.pdf){width=78%}

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

![The compaction-policy ranking inverts across domains (EXP-004). Summary policies (semantic, importance) lead on factual FRAMES and collapse on conversational LoCoMo, where the retrieval policies (externalize, reversible hybrid) lead instead.](presentation/figures/EXP-004_transfer_v1.pdf){width=80%}

### 5.7 One policy stays in the top group of every cell

Across the full design, five arms by two domains by two model sizes:

| arm | FR-8B | FR-70B | LC-8B | LC-70B |
|---|---|---|---|---|
| reversible_hybrid | 0.47 | 0.53 | 0.54 | 0.53 |
| externalize | 0.40 | 0.63 | 0.55 | 0.55 |
| importance | 0.50 | 0.60 | 0.26 | 0.23 |
| semantic | 0.57 | 0.67 | 0.27 | 0.17 |
| truncate | 0.37 | 0.27 | 0.12 | 0.09 |

The pure policies each win one domain and lose the other: semantic tops FRAMES and collapses
on LoCoMo; externalize tops LoCoMo and trails on FRAMES. The reversible hybrid is rarely the
single best point estimate in a cell, but it is never significantly below the best either: in
all four cells its accuracy is within noise of the cell leader. On FRAMES-70B semantic leads at
0.67 and the hybrid sits at 0.53, a gap that does not reach significance at n=30 (McNemar
p=0.13); on FRAMES-8B the gap to semantic is also not significant (p=0.51); and on both LoCoMo
cells the hybrid ties externalize at the top. It is the only arm that stays in the top
statistical group of every cell, because it carries both a summary and a retrievable raw copy
and so picks up whichever mechanism the task needs. That cross-domain, cross-capability
robustness, not a single best score, is the case for keeping the raw retrievable.

### 5.8 The agentic regime: the gap amplifies (EXP-009)

Every result so far feeds the agent oracle sources, so the agent never drives the loop. To test
the policies on a real agent transcript we made FRAMES agentic: the agent is given `search` and
`read` tools over the question's gold corpus and drives its own multi-step retrieval, so the
transcript it compacts is its own tool-use trajectory (search queries, observations, reads) rather
than pre-fetched articles. This also removes the oracle: the agent must find the supporting
passage itself. Compaction fires on 77% of trajectories at this budget (46 of 60 per arm).

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

![The agentic regime amplifies the policy gap (EXP-009). Under oracle retrieval the three policies sit within 0.04; on a real agent-driven transcript blind truncation falls to 0.20 while keeping the raw retrievable holds at 0.32 to 0.38, a gap of 0.18.](presentation/figures/EXP-009_agentic_amplification_v1.pdf){width=80%}

### 5.9 From policies to systems (EXP-006, EXP-007)

The policy is one variable inside a memory system; a system is a policy plus an embedder plus a
store. Two experiments connect the policy axis to the systems practitioners deploy by running
production memory systems as policy arms on FRAMES.

First, the embedder and the memory layer matter under a fixed externalize policy. Holding the
policy constant and swapping only the backend, NIM's retrieval-tuned nv-embedqa scores 0.50,
Mem0's extract-then-dedupe memory 0.40, and Chroma's general-purpose MiniLM 0.35 (n=20, judged,
same questions). The retrieval-tuned embedder alone buys +0.15 over the general one; Mem0's
distillation, which rewrites turns into deduplicated facts at an LLM call per add, costs 0.10 on
this factual task because it smooths away detail the question needs. This is the policy result
restated at the system level: the keep-the-literal-fact mechanism that wins on memory also
rewards a store that preserves it.

Second, a framework default is a dependency, not an accuracy win. LangChain's shipped
ConversationSummaryBufferMemory, the production form of recency summarization, does not beat our
fifteen-line recency on FRAMES: recency scores 0.45 against the framework's 0.35, at lower cost
(11.0k versus 13.4k tokens, n=20). Reaching for the framework's summary memory buys a heavier
dependency and, here, slightly worse accuracy, consistent with the shipped-default result of
Section 5.3.

Both are n=20 and therefore directional, not significant; we report them to tie the controlled
policy axis to off-the-shelf systems, and we mark the significance-grade sample size as future work.

![Under a fixed externalize policy, the memory backend is the lever (EXP-006). The same FRAMES questions through the same policy: a retrieval-tuned embedder (NIM nv-embedqa) leads, a general local one (Chroma MiniLM) trails, and Mem0's extract-then-dedupe distillation sits between, n=20 each with the wide intervals shown.](presentation/figures/EXP-006_memory_bakeoff_v1.pdf){width=72%}

---

## 6. Discussion

The evidence supports seven claims, which expand the abstract's five headline results with two
mechanistic findings (when the policy matters, and how the gap scales with model capability).
(1) Compaction policy matters only under pressure.
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
choice (position and self-preference bias [@zheng2023judging; @panickssery2024llm];
reference-knowledge override [@lee2026judging]). We harden it in Appendix C (EXP-008a): the
verdict is stable across model size
(kappa 0.72 against an 8B judge) and robust to answer order (kappa 0.82 under the position-bias
swap), it disagrees with the naive substring metric on a quarter of items (the metric inversion of
Section 5.1, quantified), and a manual spot-check of the hard disagreement cases confirms the 70B
as the better grader. The one check the free tier cannot run is cross-family: it throttles
non-Llama judges to near-zero, so a frontier judge, which the literature finds most robust, is
folded into the frontier-model addition below. (2) We do not yet report multiple seeds.
(3) The agent models are open and mid-scale (8B, 70B, one reasoning model); no frontier model is
yet included. (4) We connect the policy axis to deployed memory systems in Section 5.9 (EXP-006,
EXP-007): three production systems (LangChain summary memory, Chroma, Mem0) run as policy arms on
the factual domain, isolating the embedder and the extract-then-dedupe layer, but at n=20 these
are directional; significance-grade samples and a conversational-memory extension are in progress.
(5) The reasoning tier's compaction summaries are written by the 8B rather than the reasoning
model itself (Section 5.4); the 8B and 70B tiers already hold the summarizer constant, and
matching every tier's summarizer to its own model is a planned revision.
(6) The importance and semantic policies use simple heuristics rather than trained rankers.
(7) We add an agentic regime in Section 5.8 (EXP-009): an agent-driven FRAMES where the agent
searches and reads over the corpus itself, so the transcript is a real tool-use trajectory and
retrieval is no longer oracle, and the policy gap is significant and larger there. A second
agentic domain (a coding or web agent run on a frontier model where the agent can succeed) is the
remaining extension.

Four further gaps are scoping choices we state rather than fix here. (8) We benchmark seven
policies but exclude the structured/graph-memory family (Mem0, Zep, HippoRAG, Cognee; Section 3
and Table 1): it changes the store representation, not just the compaction rule, so benchmarking
it fairly needs a second store, which we defer. (9) All three domains are question answering
(factual FRAMES, conversational LoCoMo, agent-driven FRAMES); a coding or web agent that succeeds
end to end is the domain we most want next, and is the second agentic domain above. (10) We fix
one token budget and one high-pressure regime; we report the low-pressure control (all policies
tie) but do not sweep the budget to trace the full accuracy-cost frontier or locate an optimal
B\*, which would sharpen the pressure-dependence claim. (11) Our cost axis is tokens; we do not
yet report wall-clock latency or dollar cost, which is what a deployment actually trades and is a
cheap addition on the existing run timings. We mark (8) through (11) as scoped, not solved.

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
`answer_from_window` functions in `experiments/applied/agent.py`; the judge in
`experiments/applied/judge.py`; the embedding store in `experiments/applied/embed.py`. Figures
are regenerated by `experiments/make_figures_*.py`.
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

![Judge robustness (EXP-008a, n=200). Agreement with the fixed 70B judge stays high across a roughly nine-fold change in judge size (86%, kappa 0.72) and under the position-bias answer-order swap (91%, kappa 0.82); the naive substring metric agrees on only 74.5%, the metric inversion of Section 5.1 quantified.](presentation/figures/EXP-008_judge_robustness_v1.pdf){width=82%}

## References

::: {#refs}
:::
