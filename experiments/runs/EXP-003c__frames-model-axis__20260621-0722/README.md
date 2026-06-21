# EXP-003c — frames-model-axis

**Hypothesis:** The EXP-003b policy ranking is model-dependent: on a stronger instruct model and a reasoning model, structure-preserving compaction (semantic, importance) still leads on FRAMES accuracy, but the gaps between arms narrow as the model gets better at reconstructing dropped context, and the reversible-hybrid stays Pareto-efficient across all three model tiers.

**Assumptions:**
- Oracle retrieval (gold Wikipedia articles) isolates compaction from search quality.
- The same thirty FRAMES questions and cached articles are reused across models, so only the agent model changes.
- A fixed 70b judge grades every arm and every model, so the metric is held constant across the model axis.
- The reasoning model's chain-of-thought is parsed down to its final answer before judging.

Run `20260621-0722` · git `c8efad1` · model `nvidia/nemotron-3-nano-30b-a3b`

## Results

_Fill in after analysis: did the hypothesis hold? strongest threat?_
