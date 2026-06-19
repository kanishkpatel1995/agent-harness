# CLAUDE.md

Guidance for Claude Code (and any AI agent) working in this repo. The full
contributor briefing is [`AGENTS.md`](AGENTS.md); the experiment contract is
[`docs/research-track/experiment-protocol.md`](docs/research-track/experiment-protocol.md).
**Both apply in full.** This file is the quick checklist.

## What this repo is

A minimal, readable **agent harness** that teaches context engineering, plus an
active **research track** (`experiments/`) running a compaction bake-off toward a
publishable paper, and a **presentation** (`presentation/`) in Founsi brand. Optimize
for readability, teaching value, and reproducibility — not production completeness.

## Before you write code

1. **Read the existing code first.** Reuse and extend; match the surrounding
   idioms. New behaviour → a small, single-purpose class/module, not a giant function.
2. Keep `harness/loop.py` small (it's the centerpiece of the talk).
3. Preserve the tool-call ↔ tool-result pairing in compaction (`_safe_split`).

## When you run an experiment

Follow the lifecycle in the protocol — **hypothesis → assumptions → design → code
→ run → results → analysis → record**. Concretely:

- State the **hypothesis** (one falsifiable sentence) and **assumptions** up front.
- Write to a run dir: `experiments/runs/EXP-NNN__<slug>__<UTC>/` with
  `manifest.yaml`, `prompts.jsonl`, `results.csv`, `figures/`, `run.log`, `README.md`.
- **Save every LLM prompt + response** to `prompts.jsonl` (`NimLLM(transcript_path=...)`).
- Figures use [`experiments/figstyle.py`](experiments/figstyle.py) (Times New
  Roman, color-blind, no vertical grid, legend upper-right, axis units, seeded, PDF).
- **Log extensively** with the `logging` module so a terminal run narrates each
  step (`-v` INFO, `-vv` DEBUG). Never `print()` for diagnostics in library code.
- **Seed everything** stochastic; record the seed.
- **Guard loops** and fail soft per-cell; log anything skipped or capped.
- Add an appendix block to the deck for the result.

## Running things

```bash
python run.py "some topic"                 # offline FakeLLM demo, no key
python -m pytest                           # all tests, offline
python -m experiments.bench -vv            # the compaction bake-off, full logs
```

## Do / Don't

- **Do** run `python -m pytest` before considering a change done.
- **Do** read `EXP-(N-1)`'s manifest before planning the next experiment.
- **Don't** commit secrets, the response cache, raw run data, or large binaries
  (see `.gitignore`).
- **Don't** add heavy dependencies or a framework to the core harness.
- **Don't** let the offline path require a key or network.
