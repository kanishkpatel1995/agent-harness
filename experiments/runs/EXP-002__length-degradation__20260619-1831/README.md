# EXP-002 — length-degradation

**Hypothesis:** As raw context length grows, the no-compaction baseline's needle recall degrades (lost-in-the-middle); fixed-budget compaction (recency/semantic) holds recall higher at long lengths, and the crossover marks where compaction becomes net-positive.

**Assumptions:**
- Needle-fact recall is a valid proxy for task-relevant information retention.
- approx_tokens (~4 chars/token) is acceptable for budget gating.
- model_max (24k) is large enough that the baseline degrades rather than overflows.
- The 8b model exhibits lost-in-the-middle within the tested 3k-21k range.
- Filler pages act as genuine distractors around the planted needles.

Run `20260619-1831` · git `10e2c1e` · model `meta/llama-3.1-8b-instruct`

## Results

_Fill in after analysis: did the hypothesis hold? strongest threat?_
