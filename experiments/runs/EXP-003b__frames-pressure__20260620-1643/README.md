# EXP-003b — frames-pressure

**Hypothesis:** Under high compaction pressure (small budget, chunked reads forcing many compaction events per question), the policies separate on FRAMES answer accuracy, and the reversible-hybrid (summary plus retrievable raw) sits on or above the cost-quality frontier, unlike the low-pressure EXP-003a tie.

**Assumptions:**
- Oracle retrieval (gold Wikipedia articles) isolates compaction from search quality.
- Chunked reads at budget 1500 force roughly 10-20 compactions per question (cf. EXP-002 pressure).
- The 70b LLM judge credits paraphrased-correct answers (substring biased toward verbatim).
- 8b is a dev model; the model axis (70b, reasoning) comes in EXP-003c.

Run `20260620-1643` · git `2a7da5c` · model `meta/llama-3.1-8b-instruct`

## Results

_Fill in after analysis: did the hypothesis hold? strongest threat?_

## Results (n=30, 8b, judged, high pressure)

| policy | accuracy | mean tokens | Pareto |
|---|---|---|---|
| semantic | 0.57 | 18,685 | frontier (accuracy ceiling) |
| importance | 0.50 | 14,158 | frontier |
| subagent | 0.50 | 76,445 | DOMINATED (5x cost of importance) |
| reversible_hybrid | 0.47 | 9,923 | frontier (our novel arm; not the winner) |
| externalize | 0.40 | 1,881 | frontier |
| truncate | 0.37 | 1,201 | frontier (cheap floor) |
| recency | 0.37 | 8,972 | DOMINATED (7x cost of truncate, same accuracy) |

**Findings:** (1) recency-summary (the shipped default) is Pareto-dominated by truncation. (2) sub-agent isolation matches importance accuracy at 5x cost (evidence against isolation on this task). (3) structure-preserving policies (semantic, importance) win accuracy. (4) reversible-hybrid is Pareto-efficient but not the accuracy winner. Caveat: 8b dev, n=30, SE ~0.09; 70b + model axis (EXP-003c) next.
