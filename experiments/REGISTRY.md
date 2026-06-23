# Experiment registry

One row per experiment. IDs are **monotonic and never reused**. Each experiment's
runs live in `experiments/runs/EXP-NNN__<slug>__<UTC>/`. See
[`../docs/research-track/experiment-protocol.md`](../docs/research-track/experiment-protocol.md)
for the lifecycle and rules.

| ID | Slug | Hypothesis (short) | Status | Latest result |
|----|------|--------------------|--------|---------------|
| EXP-001 | compaction-bakeoff | Summary policies (recency/importance/semantic) preserve more needle-facts per token than truncation; a budget B\* exists trading fact-loss vs lost-in-the-middle | done | truncate worst (~0.2 rate); summary policies ~0.5; semantic B\*=1000 (8b dev) |
| EXP-002 | length-degradation | As raw context grows the no-compaction baseline degrades (lost-in-the-middle); a fixed-budget summary holds recall higher past a crossover | done | crossover confirmed: past the mid-range a short clean summary beats the long raw context on needle recall, so compacting early is net-positive |
| EXP-003a | frames-compaction | On FRAMES multi-hop QA, summary and reversible-hybrid compaction preserve more answer accuracy per token than truncation | done | low-pressure tie: a loose budget barely fires compaction, so the policies do not separate (substring). Motivated the high-pressure EXP-003b |
| EXP-003b | frames-pressure | Under high compaction pressure the policies separate on FRAMES accuracy and the reversible-hybrid sits on the cost-quality frontier | done | semantic 0.57 / importance 0.50 lead; recency (the shipped default) Pareto-dominated by truncate (7x cost, =acc); subagent 5x cost, =acc; reversible_hybrid Pareto-efficient (0.47), not the winner. n=30, 8b, judged |
| EXP-003c | frames-model-axis | The FRAMES ranking is model-dependent; gaps narrow as the model gets better at reconstructing dropped context, reversible-hybrid stays Pareto-efficient | done | capability does not rescue summarization: ranking holds across 8b/70b/reasoning. With the summarizer held constant on the 70b, semantic 0.67 leads, reversible_hybrid 0.53 (the original 0.67 hybrid lead was partly a summarizer artifact) |
| EXP-004 | locomo-transfer | The FRAMES ranking transfers to conversational memory (LoCoMo): structure and retrieval preserving policies beat truncation | done | ranking INVERTS cross-domain: on LoCoMo retrieval wins where FRAMES favored summary (externalize/semantic top, +0.27..+0.38, p<0.0001, n=100). reversible_hybrid is in the top group of all four FRAMES/LoCoMo x 8B/70B cells |
| EXP-005 | frames-truncate-baseline | Truncation sets the FRAMES accuracy floor under high compaction pressure: the cheapest policy, the baseline every arm must beat | done | truncate 0.37 (11/30, 8B, judged, seed 7) — reproduces the EXP-003b floor on independent questions |
| EXP-006 | frames-memory | The retrieval-tuned NIM embedder (nv-embedqa-e5-v5) beats a general local encoder (Chroma/MiniLM) as the externalize backend on FRAMES; the gap quantifies how much the embedding model matters | running | externalize, NIM nv-embedqa-e5-v5 (1024-d API) vs Chroma all-MiniLM-L6-v2 (384-d local ONNX), n=20, judged. First real OSS-memory-system arm |

## How to add an experiment

1. Pick the next `EXP-NNN`. Add a row here with a one-line hypothesis.
2. Set `exp_id` / `slug` / `hypothesis` / `assumptions` in the run config.
3. Run it — a run dir with `manifest.yaml`, `prompts.jsonl`, `results.csv`,
   `figures/`, `README.md` is created automatically.
4. Fill the run's `README.md` with the result + the strongest threat to validity.
5. Add an appendix block to [`../presentation/deck-structure.md`](../presentation/deck-structure.md).
6. **Before designing EXP-(N+1), read EXP-N's README + manifest.**
