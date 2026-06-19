# Experiment registry

One row per experiment. IDs are **monotonic and never reused**. Each experiment's
runs live in `experiments/runs/EXP-NNN__<slug>__<UTC>/`. See
[`../docs/research-track/experiment-protocol.md`](../docs/research-track/experiment-protocol.md)
for the lifecycle and rules.

| ID | Slug | Hypothesis (short) | Status | Latest result |
|----|------|--------------------|--------|---------------|
| EXP-001 | compaction-bakeoff | Summary policies (recency/importance/semantic) preserve more needle-facts per token than truncation; a budget B\* exists trading fact-loss vs lost-in-the-middle | in&nbsp;progress | truncate worst (~0.2 rate); summary policies ~0.5; semantic B\*=1000 (8b dev) |

## How to add an experiment

1. Pick the next `EXP-NNN`. Add a row here with a one-line hypothesis.
2. Set `exp_id` / `slug` / `hypothesis` / `assumptions` in the run config.
3. Run it — a run dir with `manifest.yaml`, `prompts.jsonl`, `results.csv`,
   `figures/`, `README.md` is created automatically.
4. Fill the run's `README.md` with the result + the strongest threat to validity.
5. Add an appendix block to [`../presentation/deck-structure.md`](../presentation/deck-structure.md).
6. **Before designing EXP-(N+1), read EXP-N's README + manifest.**
