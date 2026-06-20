# Results So Far: From Mechanism to Impact

*A synthesis of the four experiments run to date, written so the story is clear in
one read. All numbers are LLM-judged where noted. Figures live in
`presentation/figures/`. This is the running results section for the paper.*

---

## The shape of the argument

We ran four experiments in two layers. The first layer asks a mechanical question,
does compaction preserve information. The second asks the question that matters,
does compaction help a real agent answer real questions. The point of the pairing
is that the mechanism explains the impact.

| Layer | Experiment | The question it answers |
|---|---|---|
| Mechanism | EXP-001 | Does a planted fact survive a compaction event, by policy? |
| Mechanism | EXP-002 | As context grows, does compaction beat raw context? |
| Impact | EXP-003a | On a real research task, does the policy change the answer? |
| Impact | EXP-003b | Under real pressure, which policy wins, and at what cost? |

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

---

## The through-line

Reading the four together, five claims are now supported by evidence.

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

---

## Honest caveats

These are dev-scale results. The agent model is the small 8b, the question counts
are tens not hundreds, the domain is a single research benchmark, and the importance
and semantic policies use simple heuristics rather than trained models. The error
bars at n=30 are about plus or minus 0.09, so the gap between semantic and
importance is within noise, while the dominated policies and the overall frontier
shape are robust. The reversible hybrid result is a single configuration and may
change with a stronger model or a tuned store.

## What is next

EXP-003c runs the same bake-off on the 70b model and a reasoning model, which gives
the model-dependence map and may reorder the top cluster. EXP-004 adds LoCoMo,
conversational memory, the second domain, to test whether the winning policy
transfers across task types. After that, larger N for tight error bars, and the
write-up.
