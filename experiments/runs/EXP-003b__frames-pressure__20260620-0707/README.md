# EXP-003b — frames-pressure

**Hypothesis:** Under high compaction pressure (small budget, chunked reads forcing many compaction events per question), the policies separate on FRAMES answer accuracy, and the reversible-hybrid (summary plus retrievable raw) sits on or above the cost-quality frontier, unlike the low-pressure EXP-003a tie.

**Assumptions:**
- Oracle retrieval (gold Wikipedia articles) isolates compaction from search quality.
- Chunked reads at budget 1500 force roughly 10-20 compactions per question (cf. EXP-002 pressure).
- The 70b LLM judge credits paraphrased-correct answers (substring biased toward verbatim).
- 8b is a dev model; the model axis (70b, reasoning) comes in EXP-003c.

Run `20260620-0707` · git `88b7fc4` · model `meta/llama-3.1-8b-instruct`

## Results

_Fill in after analysis: did the hypothesis hold? strongest threat?_
