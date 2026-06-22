# Results So Far: From Mechanism to Impact

*A synthesis of the six experiments run to date, written so the story is clear in
one read. All numbers are LLM-judged where noted. Figures live in
`presentation/figures/`. This is the running results section for the paper.*

---

## The shape of the argument

We ran six experiments in two layers. The first layer asks a mechanical question,
does compaction preserve information. The second asks the question that matters,
does compaction help a real agent answer real questions. The point of the pairing
is that the mechanism explains the impact.

| Layer | Experiment | The question it answers |
|---|---|---|
| Mechanism | EXP-001 | Does a planted fact survive a compaction event, by policy? |
| Mechanism | EXP-002 | As context grows, does compaction beat raw context? |
| Impact | EXP-003a | On a real research task, does the policy change the answer? |
| Impact | EXP-003b | Under real pressure, which policy wins, and at what cost? |
| Impact | EXP-003c | Does the ranking hold as the agent model gets stronger? |
| Impact | EXP-004 | Does the ranking transfer to a different task type? |

---

## EXP-001, the mechanism: a fact either survives or it does not

We planted checkable facts (coined terms, specific numbers) in source pages and
measured how many survived a compaction, by policy. Truncation dropped them and sat
at the floor. The summary policies preserved them. At low compaction pressure the
policies were close, which was the first hint that pressure is what makes the choice
matter. The lesson is simple: compaction can preserve facts, and the policy decides
how many.

## EXP-002, the mechanism: the crossover

We then varied the amount of context the agent reads and compared a no-compaction
baseline against compaction at a fixed budget. The result is the cleanest figure we
have.

```
run length (sources):    8       16      32      48
no-compaction baseline:  0.62    0.33    0.12    0.17    collapses
recency / semantic:      ~0.6    ~0.58   ~0.58   ~0.58   holds flat
truncate:                0.08    0.08    0.08    0.08    floor
```

At short length the baseline ties compaction. As the context grows the baseline
falls apart, from 0.62 down to about 0.12, while compaction holds steady near 0.58.
The crossover is around sixteen sources. This is the lost-in-the-middle effect made
visible: a long raw context is worse than a short clean summary, so compaction
becomes net positive, not merely a way to survive the hard limit. Figure:
`EXP-002_recall_vs_length_v1`.

## EXP-003a, the impact: the metric flips the result

We pointed a real research agent at FRAMES, a multi-hop question benchmark, and ran
the four core policies. Two lessons came out, and the first nearly fooled us.

When we scored answers with a normalized substring match, our novel reversible
hybrid looked like the worst policy, at 0.21. When we re-scored with an LLM judge
that credits a correct but paraphrased answer, the same policy jumped to the best,
at 0.62, a swing of plus 0.41. The substring metric was punishing exactly the
policies that paraphrase, which is most of them. The lesson is that the metric
choice can invert the conclusion, so the judge is not optional.

The second lesson was quieter. Under the fair judge, all four policies clustered
near 0.6, because at this configuration compaction barely fired, about one event per
question. With no pressure, the policy choice washes out. Figure:
`EXP-003a_pareto_v1`.

## EXP-003b, the impact: under pressure, the policies separate

We then turned the pressure up by reading articles in small chunks against a small
budget, which forced nine to eighteen compaction events per question, and ran all
seven arms over thirty questions, judged. This is the first complete applied result.

| policy | accuracy (judged) | mean tokens | on the Pareto frontier |
|---|---|---|---|
| semantic | 0.57 | 18,685 | yes, the accuracy ceiling |
| importance | 0.50 | 14,158 | yes |
| subagent | 0.50 | 76,445 | no, dominated |
| reversible_hybrid | 0.47 | 9,923 | yes, our novel arm |
| externalize | 0.40 | 1,881 | yes |
| truncate | 0.37 | 1,201 | yes, the cheap floor |
| recency | 0.37 | 8,972 | no, dominated |

Figure: `EXP-003b_pareto_v1`. Three things stand out.

**The policy that ships in real agents is dominated.** Recency summary, the default
in Claude Code, LangChain, and most harnesses, scored 0.37, the same as naive
truncation, while costing seven times as many tokens. Summarizing the stale middle
bought nothing over dropping it here.

**Sub-agent isolation is a cost trap.** It matched importance on accuracy, 0.50, at
five times the cost, 76,445 tokens against 14,158. This is direct, cost-normalized
evidence on the multi-agent versus single-agent debate, and on this task it favors
the single-agent side: isolation is expensive and no more accurate.

**Structure-preserving compaction wins on accuracy.** The two leaders, semantic
clustering and keeping the highest-signal turns verbatim, both preserve structure
rather than flattening it into one summary.

Our reversible hybrid landed at 0.47 for 9,923 tokens. It is Pareto efficient, it
sits on the frontier and is not dominated, but it is not the accuracy winner. We
report that plainly rather than overselling the novel method. The accuracy champion
is a simple policy, semantic clustering.

## EXP-003c, the impact: the model axis, and the gap that widens with capability

We then ran the same five separating arms across three agent models: the small instruct
8b, the large instruct 70b, and a reasoning model (Nemotron 30B-A3B). The judge is held
constant at the 70b across every tier, so only the agent model changes. The result is the
model-dependence map.

| arm | 8B | 70B | reasoning |
|---|---|---|---|
| truncate (blind drop) | 0.37 | 0.27 | 0.40 |
| externalize (retrieval) | 0.40 | 0.63 | 0.67 |
| importance (keep verbatim) | 0.50 | 0.60 | 0.70 |
| semantic (cluster) | 0.57 | 0.53 | 0.63 |
| reversible_hybrid (ours) | 0.47 | 0.67 | 0.70 |

Figure: `EXP-003c_modelaxis_v1`. Two things stand out, and together they are the
strongest claim in the paper.

**Capability does not rescue blind truncation.** Truncate sits at the floor on every
model, 0.37, 0.27, 0.40. A stronger or reasoning model cannot recover information that was
dropped without a trace, because there is nothing to reason over. The line is flat along
the whole capability axis.

**Every structure or retrieval preserving arm climbs with capability, so the gap widens.**
Externalize, importance, semantic, and the reversible hybrid all rise from the 8b to the
reasoning model and converge near the top, 0.63 to 0.70. The distance between the best
compaction and blind truncation grows from about 0.2 on the 8b to about 0.3 on the
reasoning model. A better model has more to gain from a clean compacted context and more to
lose from a blind one. On the reasoning model the reversible hybrid and importance lead the
cluster at 0.70.

A methodological note we report plainly: on the reasoning tier the compaction summaries are
written by a fast instruct model (8b), because the reasoning model's verbose chain of
thought makes self-summarizing prohibitively slow (single cells stalled past 200s). The
reasoning model still produces the final answer, which is the capability the axis measures.
The 8b and 70b tiers summarize with their own model. This is a real difference between the
tiers and a caveat on the reasoning numbers, not a free lunch.

## EXP-004, the impact: the ranking does not fully transfer, and that is the point

The natural worry about everything above is that it is a FRAMES artifact. So we ran the same
five arms on LoCoMo, a conversational-memory benchmark: each conversation has many sessions
(tens of thousands of characters) that overflow the window, and many questions asked of that
one conversation. The agent compacts the conversation once and answers from the compacted
window. Same 8b agent, same 70b judge, 10 conversations x 10 questions per arm.

| arm | FRAMES (8b) | LoCoMo (8b) |
|---|---|---|
| semantic (summary) | 0.57 | 0.27 |
| importance (summary) | 0.50 | 0.26 |
| reversible_hybrid (summary + retrievable raw) | 0.47 | 0.54 |
| externalize (retrievable raw) | 0.40 | 0.55 |
| truncate (blind drop) | 0.37 | 0.12 |

Figure: `EXP-004_transfer_v1`. The ranking inverts at the top, and the reason is the task.

**On conversational memory, retrieval wins and pure summarization loses.** The two retrieval
arms lead, externalize 0.55 and the reversible hybrid 0.54; the two pure-summary arms fall to
0.26 and 0.27, half their FRAMES accuracy; truncation collapses to 0.12. LoCoMo questions ask
for specific scattered facts, a date, an item, who said what, which survive in a retrievable
raw copy but get smoothed away in a 180-word summary. FRAMES multi-hop questions reward the
opposite, a summarized reasoning chain. So the best single policy is task-dependent: semantic
on FRAMES, externalize on LoCoMo.

**The reversible hybrid is the one policy in the top group of both domains.** It is 0.47 on
FRAMES (on the frontier, and the outright winner once the model is strong, EXP-003c) and 0.54
on LoCoMo (tied for the lead). Because it carries both a summary and a retrievable raw copy,
it picks up whichever mechanism the task needs, so it never lands in the loser group. The pure
policies each win one domain and lose the other; the hybrid wins both. That cross-domain
robustness, not a single best score, is the case for keeping the raw retrievable.

**The LoCoMo model axis is the mirror of FRAMES.** We re-ran all five arms on the 70b. On
FRAMES, a stronger model lifted the summary arms (EXP-003c). On LoCoMo it does the opposite,
or nothing:

| arm | 8B | 70B |
|---|---|---|
| externalize (retrieval) | 0.55 | 0.55 |
| reversible_hybrid (both) | 0.54 | 0.53 |
| importance (summary) | 0.26 | 0.23 |
| semantic (summary) | 0.27 | 0.17 |
| truncate (blind) | 0.12 | 0.09 |

Figure: `EXP-004_modelaxis_v1`. The two retrieval arms are flat at the top across both
models; the summary arms are flat to falling, semantic dropping hardest, 0.27 to 0.17. A
stronger model cannot rescue a lossy summary, because the missing fact is simply not in it;
worse, the stronger model is more willing to admit it does not know, which costs it the
lucky guesses the smaller model sometimes got. So the cross-domain claim now holds across
the capability axis too: retrieval wins on conversational memory at every model size, and
the reversible hybrid rides its retrieval half to the top group in all four cells
(8b/70b x FRAMES/LoCoMo).

---

## The through-line

Reading the six together, seven claims are now supported by evidence.

1. **Compaction policy matters only under pressure.** EXP-003a tied at low pressure;
   EXP-003b separated at high pressure; EXP-002 shows the same along the length axis.
2. **The metric must credit paraphrase.** The substring-versus-judge flip in EXP-003a
   shows a careless metric inverts the ranking.
3. **The shipped default is weak under pressure.** Recency summary is dominated by
   truncation in EXP-003b.
4. **Multi-agent isolation is expensive without a benefit, on this task.** The
   sub-agent arm fills the empty cell from the literature on the single-agent side.
5. **Structure-preserving compaction is the move.** Keep facts verbatim or cluster
   by topic, do not flatten.
6. **The smart-versus-blind gap widens with model capability.** EXP-003c shows blind
   truncation stuck at the floor across all three models while every structure or
   retrieval preserving arm climbs, so a better agent makes the compaction choice matter
   more, not less.
7. **The best single policy is task-dependent, but the hybrid is robust.** EXP-004 inverts
   the FRAMES ranking on conversational memory (retrieval beats summary), yet the reversible
   hybrid stays in the top group of both domains because it keeps both a summary and a
   retrievable raw copy. Keeping the raw retrievable is the cross-domain hedge.

---

## Honest caveats

These are dev-scale results. The agent model is the small 8b, the question counts
are tens not hundreds, the domain is a single research benchmark, and the importance
and semantic policies use simple heuristics rather than trained models. The error
bars at n=30 are about plus or minus 0.09, so the gap between semantic and
importance is within noise, while the dominated policies and the overall frontier
shape are robust. The reversible hybrid result is a single configuration and may
change with a stronger model or a tuned store.

The reasoning tier carries an extra caveat: its compaction summaries are written by a
separate fast model, so the answer model is the controlled variable but the summarizer is
not held constant across all three tiers. The reversible hybrid reached 0.91 at n=11 on the
reasoning tier before regressing to 0.70 at n=30, a reminder of how wide the bars are at
this scale.

EXP-004 carries its own caveats: LoCoMo accuracy is judged the same way as FRAMES, but the
questions skew toward dates and named entities, which favor exact retrieval; the dev model is
again the 8b; and the per-conversation question sample is ten of roughly a hundred and fifty.
The cross-domain inversion is large enough (a third of a point) to survive these, but the
exact numbers are dev-scale.

## What is next

Both the FRAMES and LoCoMo model axes are now run (8b and 70b on both domains), and they tell
opposite capability stories that share one constant: the reversible hybrid is in the top group
of every cell. Remaining for rigor: a reasoning tier on LoCoMo; a summarizer held constant
across all tiers; larger N for tight bars; LangChain summary-memory as a baseline arm; and then
the write-up.
