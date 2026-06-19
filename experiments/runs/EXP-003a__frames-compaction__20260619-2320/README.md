# EXP-003a — frames-compaction

**Hypothesis:** On FRAMES multi-hop QA, summary-based and reversible-hybrid compaction preserve more answer accuracy per token than truncation; the reversible-hybrid (summary plus retrievable raw) sits on or above the cost-quality frontier.

**Assumptions:**
- Oracle retrieval (gold Wikipedia articles) isolates compaction from search quality.
- Articles capped at 6000 chars and N per question still overflow the budget and force compaction.
- Normalized substring match against the gold answer is a cheap, objective accuracy proxy for dev.
- 8b is a dev model; final numbers and an LLM-judge come with the 70b solid run.

Run `20260619-2320` · git `6997e6a` · model `meta/llama-3.1-8b-instruct`

## Results

_Fill in after analysis: did the hypothesis hold? strongest threat?_
