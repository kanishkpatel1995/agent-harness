# EXP-005 — frames-truncate-baseline

**Hypothesis:** Truncation (keep the recent turns, drop the rest, no LLM call) sets the accuracy floor on FRAMES multi-hop QA under high compaction pressure: it is the cheapest policy and the baseline every summary/retrieval arm must beat.

**Assumptions:**
- Oracle retrieval (gold Wikipedia articles) isolates compaction from search quality.
- Chunked reads at budget 1500 force many compaction events per question.
- The 70b LLM judge credits paraphrased-correct answers; substring is biased toward verbatim.
- n=30 at one seed is a dev-scale point estimate; the 95% CI is wide (cf. experiments/stats.py).

Run `20260623-1904` · git `1ebe18c` · model `meta/llama-3.1-8b-instruct` · judge `meta/llama-3.3-70b-instruct`

## Results (n=30, 8B, judged, high pressure, seed=7)

| policy | accuracy | mean tokens | mean compactions | n |
|---|---|---|---|---|
| truncate | 0.37 (11/30) | 1,260 | 3.7 | 30 |

**Did the hypothesis hold?** Yes. Truncation lands at **0.367**, essentially identical to the 0.37 truncate floor measured in EXP-003b on a *different* question set (seed 0 vs seed 7). The floor reproduces across independent samples. It is the cheapest policy (no LLM call for compaction; the ~1.3k mean tokens are spent on the single answer plus the judge), and it is the number every summary and retrieval arm must beat.

**Strongest threat to validity.** n=30 at a single seed: the 95% bootstrap CI on a 0.37 proportion is roughly ±0.17 (cf. `experiments/stats.py`), so this is a dev-scale point estimate, not a publication number. Its value is as a *reproduced floor*, not a precise value; scaling n (the EXP-003b pressure run at n=200) tightens it.

**Reproduce:** `python experiments/applied/launch_exp005_truncate.py` (re-runs replay the response cache for free).
