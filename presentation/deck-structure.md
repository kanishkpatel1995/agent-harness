# Deck structure — AI Tinkerers, June 22

**Title:** Context Engineering Inside the Harness — Keeping a Long-Running Agent
From Falling Apart
**Format:** 16:9 PPTX, Founsi brand. **Present ~10 slides. Carry a ~30-slide
appendix.**

## The philosophy: thin front, deep appendix

We present a **tight, story-first deck** (≤10 min) and back it with a **large
appendix that is the full trace of the project** — every graph, every design
decision, every result, every citation. We almost never *show* the appendix
live; it exists so that (a) any Q&A can be answered by jumping to a slide, (b) the
deck doubles as the canonical record of what we did, and (c) the work is
reproducible by a reader flipping through it later.

Rule of thumb: **if it's a claim on a main slide, its evidence is a slide in the
appendix.** Main slides link to their appendix slide ("→ A7").

## Brand application (every slide)

Pulled from [`brand/founsi-brand-guide.md`](brand/founsi-brand-guide.md):
- **Background** `#FAFAFE` (never pure white). **Ink** `#2E2C32`. **Accent**
  purple `#9378FF` (~5% of the slide, accent only). Links/labels `#7B5EF0`.
- **Fonts:** Syne (titles/overlines, 700/800, tight tracking) · Manrope (body,
  400/600/700) · Courier New (code, ≥18pt for back-row legibility).
- **Overlines:** Syne 700, 12pt, 3px tracking, `#9378FF` — for section labels.
- **Logo:** [`brand/founsi-logo-horizontal-primary.svg`](brand/) bottom-left on
  content slides; [`brand/founsi-mark.svg`](brand/) as a small corner mark on the
  appendix. Inverted variants on dark slides. The purple period is never recolored.
- **Graphs:** all rendered via [`brand/chart_style.py`](brand/chart_style.py) —
  off-white surface, purple-tinted grid, ink text, fixed policy colours
  (truncate=grey, recency=purple, importance=purple-dark, semantic=ink,
  baseline=red). One figure per slide, ≥18pt labels.

---

## MAIN DECK (presented) — ~10 slides

Story spine (full speaker notes in [`../docs/research-track/talk-june22.md`](../docs/research-track/talk-june22.md)):
**Problem → Reframe → Mechanism (deep) → See it live → The open question.**

| # | Slide | One line | Appendix |
|---|---|---|---|
| 1 | **Title** | Founsi brand, name, date, subtitle | — |
| 2 | **The agent that dies** | cold open: brilliant at 5 steps, dead at 50 | → A2 |
| 3 | **The window is a budget** | re-send every turn → cost↑ latency↑ recall↓ | → A3, A4 |
| 4 | **The reframe** | engineer what the model sees. *"Model rented, harness built."* | — |
| 5 | **The list is the mind** | stateless model; harness rebuilds the window | → A5 |
| 6 | **Five moves, one matters tonight** | pin/truncate/**compact**/externalize/cap | → A6 |
| 7 | **Compact, deeply** | summarize the stale middle; the tool-call gotcha | → A7, A8 |
| 8 | **💻 LIVE DEMO** | watch the bar grow, COMPACT, snap back, keep going | → A11 |
| 9 | **The open question** | which way of forgetting loses least? I'm measuring it | → A12–A20 |
| 10 | **Swap the brain + clone it** | any model, one flag; QR to repo. The one sentence. | → A28 |

---

## APPENDIX (carried, not presented) — the full trace

Each appendix slide names the **artifact it traces**, so the deck is a literal
index of the work. Group dividers use a Syne overline.

### § A — Problem & framing
- **A1 — Project map / North Star.** The one sentence; the three deliverables
  (talk / curriculum / paper). *Source: [`docs/research-track/README.md`](../docs/research-track/README.md).*
- **A2 — The failure mode.** Drift, repetition, goal loss, hard limit. *Why agents die at 50 steps.*
- **A3 — Token economics.** Window-vs-billed divergence graph. *Source: [`experiments/token_growth.py`](../experiments/token_growth.py).*
- **A4 — Lost in the middle.** The U-shaped recall curve; why bigger ≠ better. *Cites Liu 2307.03172, RULER 2404.06654, NoLiMa 2502.05167.*

### § B — The harness
- **A5 — The turn lifecycle.** The ~40-line loop, the 5 steps. *Source: [`harness/loop.py`](../harness/loop.py).*
- **A6 — The five moves.** pin · truncate · compact · externalize · cap, mapped to files.
- **A7 — Compaction internals.** `maybe_compact`, the threshold, keep_recent. *Source: [`harness/context.py`](../harness/context.py).*
- **A8 — The tool-call/result gotcha.** `_safe_split_index`; why APIs reject orphaned tool results.
- **A9 — Externalize = safe compaction.** The scratchpad; lossy-but-safe. *Source: [`harness/memory.py`](../harness/memory.py).*
- **A10 — Compaction on vs off.** The bounded sawtooth vs the unbounded climb. *Source: [`experiments/scenarios.py`](../experiments/scenarios.py).*
- **A11 — Live-demo backup.** The recorded GIF + `cat run/notes.md`, for wifi insurance.

### § C — The research
- **A12 — The question & the gap.** Compaction policies, unmeasured. *Source: [`docs/research-track/paper.md`](../docs/research-track/paper.md) §1–2b.*
- **A13 — Literature map.** The 3 families (token / latent / KV) + the externalize line; where we sit. *Source: [`docs/research-track/literature.md`](../docs/research-track/literature.md).*
- **A14 — The four policies.** truncate / recency / importance / semantic. *Source: [`experiments/policies.py`](../experiments/policies.py).*
- **A15 — The needle-fact metric.** Planted coined facts; fidelity vs probe. *Source: [`experiments/needles.py`](../experiments/needles.py), [`experiments/bench/metrics.py`](../experiments/bench/metrics.py).*
- **A16 — Mode A: the controlled probe.** Why simulated transcript + real model. *Source: [`experiments/bench/window.py`](../experiments/bench/window.py).*
- **A17 — Realism: budget is an axis.** B sweep; the B\* optimum sketch.
- **A18 — Realism: the no-compaction baseline.** Recall-vs-length curve.
- **A19 — Realism: the max-window wall.** `context_overflow` = the agent dies; compaction as the fix.
- **A20 — The B\* idea.** Compaction can *beat* raw context by escaping lost-in-the-middle.

### § D — Infrastructure
- **A21 — Provider-agnostic models.** litellm; 8b dev / 70b final on free NVIDIA NIM.
- **A22 — Rate-limit engineering.** 40 req/min → pace + backoff + cache. *Source: [`experiments/nim.py`](../experiments/nim.py).*
- **A23 — The bench package.** config / logging / datasets / metrics / policies / window / runner / analyze. *Source: [`experiments/bench/`](../experiments/bench/).*
- **A24 — Observability.** The `-vv` step-by-step log trace.

### § E — Results & analysis  *(filled from the live sweeps)*
- **A25 — Dev sweep (8b).** Per-policy × budget table, real ± sd error bars.
- **A26 — Quality-vs-cost Pareto.** One point per policy per budget. *brand-styled.*
- **A27 — Baseline recall-vs-length + overflow.** Where the wall hits.

### § F — Closing
- **A28 — Reproduce it.** `git clone && python run.py` (no key) and `python -m experiments.bench -vv`.
- **A29 — Threats to validity.** Synthetic data, FakeLLM determinism, normalization, judge variance, single domain.
- **A30 — Roadmap.** HF datasets (RULER/LongBench), LangChain baseline arm, position analysis, Mode B, the paper.
- **A31 — References.** The full verified bibliography. *Source: [`docs/research-track/literature.md`](../docs/research-track/literature.md).*

---

## Build order

1. ✅ Brand assets staged + logo set generated ([`brand/`](brand/)).
2. ✅ Brand chart style ([`brand/chart_style.py`](brand/chart_style.py)).
3. ✅ This structure.
4. ☐ Render the appendix figures (A3, A10, A25–A27) from results via chart_style.
5. ☐ Build the `.pptx` (main + appendix) with the pptx skill, Founsi brand.
6. ☐ Rehearse the ~10 main slides to ≤10 min; appendix stays in reserve.
