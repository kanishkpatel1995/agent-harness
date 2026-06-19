# Experiment protocol & engineering standards

**This is the contract.** Every experiment in this repo — and every line of code
and every figure that supports it — follows the rules below. The goal is a
repository a stranger can clone and fully reproduce, and a paper whose every claim
traces back to a recorded run. AGENTS.md and CLAUDE.md both defer to this file.

> One sentence: **nothing is real unless it is recorded, reproducible, and traceable.**

---

## 1. The experiment lifecycle (no skipping steps)

Every experiment moves through these stages, in order, and each stage leaves an
artifact on disk:

1. **Hypothesis** — a single falsifiable sentence. "Compaction policy P preserves
   more needle-facts per token than truncation at budgets below B."
2. **Assumptions** — list them explicitly (what must hold for the result to mean
   what we say). E.g. "needle recall is a valid proxy for task quality";
   "approx_tokens ≈ real tokens"; "the summarizer model is held fixed."
3. **Design** — independent variables, controls, dependent variables (metrics),
   sample size (seeds), and the figures you will produce (planned *before* the run).
4. **Code** — modular, classed, logged, seeded (see §4).
5. **Run** — executed from the terminal, narrating each step (see §5), writing a
   run directory (§2).
6. **Results** — raw data + the planned figures (§6), saved under the run dir.
7. **Analysis** — interpret against the hypothesis; state whether it held, and the
   strongest threat to validity.
8. **Record** — a slide block in the deck appendix: hypothesis · assumptions ·
   solution · code structure · figures · results (§7).

**Before planning experiment N, read the manifest + README of experiment N−1.**
Each experiment builds on the last; the `manifest.yaml` "follows_from" field makes
the chain explicit.

---

## 2. Nomenclature — so everything is traceable

### Experiment IDs
`EXP-NNN` — zero-padded, monotonic, never reused. Registered in
[`experiments/REGISTRY.md`](../../experiments/REGISTRY.md) (id · slug · hypothesis ·
date · status).

### Run directories
Every execution writes a self-contained run directory:

```
experiments/runs/EXP-NNN__<slug>__<YYYYMMDD-HHMM>/
├── manifest.yaml      # hypothesis, assumptions, config snapshot, model, git sha, deps
├── prompts.jsonl      # EVERY llm call: {stage, messages, response, usage, cached, ts}
├── results.csv        # the raw measurements (one row per cell)
├── figures/           # publication PDFs, named EXP-NNN_<figure>_v<N>.pdf
├── run.log            # the full terminal log (same as stdout)
└── README.md          # human summary: what/why/result, written after analysis
```

- `<slug>` is kebab-case and stable for the experiment (e.g. `compaction-bakeoff`).
- Timestamps are UTC, `YYYYMMDD-HHMM`.
- **Names encode meaning.** No `final2.csv`, no `test.png`, no `output/`.

### Data & figure files
- Data: snake_case, descriptive, with units where ambiguous (`probe_recall_by_budget.csv`).
- Figures: `EXP-NNN_<figure-name>_v<N>.pdf` — versioned, never overwritten silently.

---

## 3. Save everything — prompts, responses, outputs

**Every LLM interaction at every stage is persisted.** Non-negotiable: a paper
whose prompts you cannot show is not reproducible.

- The model client logs each call to the run's `prompts.jsonl`: the exact
  `messages` sent, the raw response text, token `usage`, whether it was a cache
  hit, the `stage` label (e.g. `summarize`, `probe`), and a timestamp.
- Set the transcript path per run; see `NimLLM(transcript_path=...)` in
  [`experiments/nim.py`](../../experiments/nim.py).
- The on-disk response cache (`experiments/.cache/`) makes re-runs free and frozen,
  but it is **not** the record — `prompts.jsonl` is the human-readable, per-run trace.
- Tool inputs/outputs, intermediate notes, and any generated text are saved too.

---

## 4. Figures — publication standard (strict)

All **data/research figures** (paper + appendix) follow this house style, captured
in [`experiments/figstyle.py`](../../experiments/figstyle.py). Treat the brief as a
spec:

> **Role:** Senior Academic Data Scientist specializing in publication-ready
> figures. **Task:** clean, deterministic matplotlib.
>
> **Styling:** (1) color-blind-friendly sequential palette; (2) Times New Roman for
> all text; (3) no vertical gridlines, light horizontal gridlines at major ticks
> only; (4) legend upper-right, transparent background; (5) all axes labelled with
> units in parentheses, e.g. `Temperature (Celsius)`.
>
> **Code constraints:** (1) raw executable code only; (2) set a random seed for
> reproducibility; (3) save as high-resolution **PDF**.

Use `figstyle.apply()` then `figstyle.save(fig, run_dir/"figures"/"EXP-NNN_name_v1.pdf")`.

**Brand vs publication — no contradiction.** The Founsi brand
([`presentation/brand/`](../../presentation/brand/)) styles the *deck chrome* — title
slides, section dividers, layout, the logo. The *data figures embedded in the deck*
stay in publication style (Times New Roman, color-blind, PDF). Clean academic
figures inside a branded deck is the correct, reviewer-proof combination.

---

## 5. Code standards (adopt mainstream OSS practice)

- **Modular & classed.** New behaviour goes in a small, single-purpose
  class/module — not a 300-line function. Before writing new code, **read the
  existing code** and reuse/extend it; match its idioms.
- **Comments explain *why*,** not what. Module docstrings state the purpose.
- **Type hints** on public functions. **snake_case** functions, **PascalCase**
  classes, **UPPER_SNAKE** constants. PEP 8.
- **Extensive, levelled debug logs** via the `logging` module (`bench.*` loggers).
  One line per meaningful step. `-v` = INFO, `-vv` = DEBUG. Never `print()` for
  diagnostics in library code.
- **Determinism.** Every stochastic step takes an explicit seed. No bare
  `random`/`np.random` without a seeded generator. Record the seed in the manifest.
- **Fail soft, never silent.** Guard loops (see the compaction progress-guard
  lesson), catch per-cell so one failure doesn't kill a sweep, and **log what was
  skipped or capped** — silent truncation reads as success.
- **Tests** for the fiddly invariants (e.g. the tool-call/result split). `pytest`
  green before a change is done.
- **No heavy deps without reason.** The core stays hand-rolled and readable.

---

## 6. Reproducibility (a stranger can rebuild it)

- `manifest.yaml` pins: model id, all config, seeds, git commit sha, Python
  version, and resolved dependency versions.
- One command reruns an experiment end-to-end; the response cache makes it free.
- `requirements.txt` (or a lock) is current. Offline paths (FakeLLM, fixtures)
  require no key or network.
- Results, figures, and the prompts trace are all in the run dir — the unit you'd
  attach to a paper's supplementary material.
- **The bar:** the paper isn't done until `python -m experiments.bench ...`
  reproduces the figure on someone else's laptop.

---

## 7. Recording in the deck (the appendix is the lab notebook)

Every experiment gets an appendix block in the deck
([`presentation/deck-structure.md`](../../presentation/deck-structure.md)) with, in order:
**Hypothesis · Assumptions · Design · Solution (code structure) · Figures ·
Results · Threats.** Appendix slides may use **small fonts** to fit more — density
is fine there; the appendix is the record, not the performance. Each block names
the run dir it came from, so a reader can open the exact artifacts.

---

## 8. Git hygiene

- **Never commit:** `.env`/secrets, the response cache, raw run data, large
  binaries, `.pptx`/large PDFs, `__pycache__`. See `.gitignore`.
- **Do commit:** all code, the protocol, the deck *plan* (markdown), small brand
  SVGs, the experiment `REGISTRY.md`, and per-run `manifest.yaml` + `README.md`
  (the lightweight trace) — but not the heavy data they point to.
- Conventional, descriptive commit messages. Branch off `main`; never force-push
  shared branches.

---

*This protocol is itself versioned. When practice improves, update this file first,
then the code — and note the change in the next commit.*
