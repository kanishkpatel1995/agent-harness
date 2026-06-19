# Curriculum — 101 to research, in 10 units

Each unit has the same five parts, on purpose (it's the loop from the
[README](README.md#how-to-use-these-rails-the-method-not-just-the-content)):

- **Idea** — the concept, in plain words. This is the lecture.
- **Read** — one source, with the question to read it *for*.
- **Study** — the exact code in this repo it maps to.
- **Build** — the task. Code is where understanding lands.
- **Gate** — answer this cold, or loop back. No soft passes.

Times assume ~5 hrs/day. Foundations (0–3) ≈ a day each; research (6–8) ≈ 2–3
days each. Keep a running `run/lab-notebook.md` — one paragraph per unit on what
surprised you.

> **Citations.** Every "Read" below maps to a *verified* source in
> [`literature.md`](literature.md) (arXiv IDs confirmed against primary pages,
> not memory). The reading map at the end of that file lists the exact papers per
> unit. Read papers *with the unit's question in hand*, not cover to cover.

---

# FOUNDATIONS — *this is the talk*

## Unit 0 — The mental model ⏱ ~half day

**Idea.** The model is a pure function: messages in, one response out. It
remembers *nothing* between calls. So "the agent's memory" is a fiction the
harness maintains — every turn, the harness hands the model a freshly-built list
of messages, and *that list is the agent's entire mind for that turn.* There is
no hidden state. If the agent "forgot its goal," it's because the goal wasn't in
the list. This is the most important and least intuitive idea in the whole
track; everything else is mechanics.

**Read.** Anthropic, *Building Effective Agents* (the "agent" pattern section).
Read it for one question: *where is the agent's state actually stored?* (Answer:
nowhere durable — it's reconstructed each loop.)

**Study.** [`harness/loop.py`](../../harness/loop.py) — all of it, it's ~40 lines.
Trace one iteration: `context.messages()` builds the list →
`llm.complete()` → tool calls run → `context.maybe_compact()`. Then
[`harness/agent.py`](../../harness/agent.py) to see how the pieces are wired.

**Build.** Run `python run.py "context engineering for long-running agents"`
five times. Then add a single `print(len(context.messages()))` at the top of the
loop and watch the message count climb. Delete it after.

**Gate.** Without looking: *list the five things one iteration of `run_agent`
does, in order.* If you hesitate, re-read the loop.

---

## Unit 1 — The window is a budget, not a backpack ⏱ ~1 day

**Idea.** People picture the context window as storage you fill up. Wrong model.
Because the model is stateless, **you re-send the entire history on every single
turn.** So a 50-step run doesn't pay for the history once — it pays for it ~50
times. That's why three things blow up together as a run grows: **cost** (tokens
billed per turn × turns), **latency** (more tokens = slower prefill), and
**quality** (attention dilutes across a longer context — the "lost in the
middle" effect you'll study in Unit 4). A bigger window raises the ceiling; it
does not bend the curve. The number that matters is your **working set** — the
tokens actually live in the window — and the job is to keep that ~constant even
as the run gets arbitrarily long.

**Read.** Skim a tokenizer explainer (e.g. the OpenAI tokenizer page or
`tiktoken` README) for one question: *why is token count not the same as
character count, and why ~4 chars/token is only a rough guess?* Connect it to
`approx_tokens` in the repo.

**Study.** [`harness/context.py`](../../harness/context.py): `token_count()`,
`composition()`, and `approx_tokens()`. Then
[`harness/budget.py`](../../harness/budget.py): see how `record_usage` adds
`prompt_tokens` *every turn* — that accumulation **is** the re-send cost made
visible. Then [`harness/trace.py`](../../harness/trace.py) `_context_bar()` — the
purple/cyan bar you'll show on stage.

**Build.** Instrument a run to dump, per step, `(step, total_tokens_in_window,
cumulative_prompt_tokens_billed)` to a CSV. Plot the two columns. The gap between
them — window size vs. cumulative billed — is the entire economic argument of
your talk, in one chart.

**Gate.** *A run does 30 steps with a roughly-constant 2,000-token window. Order
of magnitude, how many prompt tokens did you pay for total, and why isn't it
2,000?* (≈60,000 — you re-sent the window ~30 times.)

---

## Unit 2 — The five moves ⏱ ~half day

**Idea.** Given "keep the working set small without lobotomizing the agent,"
there are exactly five levers, and this repo is organized around them:

| Move | One-line job | Lives in |
|---|---|---|
| **Pin** | Goal + system prompt can *never* be evicted | `context.py` `_pinned` |
| **Truncate** | Cap any single oversized tool output before it enters | `context.py` `_truncate` |
| **Compact** | Summarize the stale middle; drop the raw turns | `context.py` `maybe_compact` |
| **Externalize** | Findings live in a file, not the window | `memory.py` |
| **Cap** | Hard limit steps / tokens / dollars; fail soft | `budget.py` |

The art is that they interact: compaction is only *safe* because of
externalization; truncation and compaction both buy you headroom so the cap
fires later; pinning is what guarantees that no matter how aggressive the other
four get, the agent never forgets why it's running.

**Read.** Anthropic, *Effective context engineering for AI agents*. This is the
single most on-point source — it names these exact moves ("compaction",
"structured note-taking", "context rot"). Read it for: *which of the five moves
does Anthropic consider most underused?*

**Study.** Find each move's code, one grep at a time. For each, write the file
and line in your notebook. (`pin` → `__post_init__`; `truncate` → `_truncate`;
`compact` → `maybe_compact`; `externalize` → `Scratchpad.save_note`; `cap` →
`Budget.check_step` / `record_usage`.)

**Build.** Draw the architecture diagram from memory (the one in the repo
README), then check it. Redraw until you can produce it cold — you'll need it on
slide 5.

**Gate.** *Name all five moves and the file each lives in, without looking.*

---

# DEEPENING

## Unit 3 — Compaction internals (the heart) ⏱ ~1 day

**Idea.** Compaction is the move your paper is about, so you go deep here.
`maybe_compact` ([`context.py:113`](../../harness/context.py:113)): if the window
is over `compact_at` × budget, pick a split that keeps the last `keep_recent`
messages verbatim, summarize everything older into one `[COMPACTED MEMORY]`
system message, and drop the raw turns. Two subtleties that separate people who
*get it* from people who don't:

1. **The tool-call/result boundary (the one real gotcha).** A `tool` message is
   only valid immediately after the assistant message that requested it. If your
   split point lands such that the kept tail *starts* on a `tool` message, you've
   orphaned a result from its call, and real APIs (OpenAI, Anthropic) will reject
   the transcript. `_safe_split_index`
   ([`context.py:143`](../../harness/context.py:143)) nudges the split forward
   past any leading `tool` messages. This is the fiddliest 10 lines in the repo
   and worth 20 seconds on stage.
2. **Lossy-but-safe.** Compaction *destroys information* — that's the point. It's
   only acceptable because anything important was already written to the
   scratchpad (Unit 5 / the externalize move). The summary is a *pointer*
   ("details in the scratchpad, use read_notes"), not the source of truth.

**Read.** MemGPT (Packer et al., 2023), arXiv:2310.08560. Read the intro +
the "main context vs. external context" framing. It's the intellectual ancestor
of compaction-plus-scratchpad: treat the window like RAM and page to disk.

**Study.** Read `maybe_compact`, `_safe_split_index`, `_summarize`,
`_render_for_summary`, and `_fallback_summary` line by line. Then see how the
FakeLLM answers a `SUMMARIZE_REQUEST` in
[`fake_llm.py`](../../harness/fake_llm.py) `_summarize` — that's how compaction
works offline.

**Build.** Write a failing test that constructs a `_body` where the natural split
lands on a `tool` message, and assert `_safe_split_index` moves it. Then break
`_safe_split_index` (remove the `while` loop) and watch your test go red. Fix it.
You now *own* the gotcha.

**Gate.** *Why can't you split the context right before a `tool` message — what
exactly breaks, and where in the code is it prevented?*

---

## Unit 4 — Lost in the middle (why any of this is necessary) ⏱ ~1 day

**Idea.** Up to now you've taken "long context degrades quality" on faith. Time
to ground it. Liu et al. showed models retrieve facts well from the *start* and
*end* of a long context but poorly from the *middle* — a U-shaped accuracy curve.
Implication for agents: the stale middle of a long transcript isn't just
*expensive*, it's *low-value* — the model can barely attend to it anyway. That
reframes compaction: you're not reluctantly throwing away good information,
you're removing information the model had mostly stopped using, and replacing it
with a dense summary that lands in a high-attention position. This is the
*theoretical justification* for the entire harness, and it's the slide-3 "why" of
your talk.

**Read.** *Lost in the Middle* (Liu et al., 2023), arXiv:2307.03172 — for *where
recall is worst and how big the effect is.* Then skim RULER (2404.06654) and
NoLiMa (2502.05167) for the kicker: models use *far less* of their window than
advertised, and the effect is associative, not lexical. (Full notes:
[`literature.md`](literature.md) §1.)

**Study.** No new code — instead, connect the paper to `keep_recent` and the
pinned segment. Pinned content sits at the *front* (high recall); `keep_recent`
keeps the *tail* verbatim (high recall); the compacted summary replaces the
*middle* (the low-recall zone). The repo's design is "lost in the middle" applied
without ever naming it. Verify that reading of the code.

**Build.** Design (don't run yet) a mini experiment: if you planted the same fact
at position 0, the middle, and the end of a long window, which would the agent
recall? Write the hypothesis in your notebook. You'll actually run a version of
this in the paper.

**Gate.** *In one sentence, connect the U-shaped recall curve to why
`keep_recent` keeps the tail and pinning keeps the head.*

---

## Unit 5 — Evals & the needle-fact trick ⏱ ~1–2 days

**Idea.** You cannot improve what you cannot measure, and "the report seems
good" is not measurement. The hard part of evaluating a research agent is that
its output is open-ended prose. The trick that makes it *objective and offline*:
**plant needle-facts.** Seed the fixtures with N distinct, checkable facts
(specific numbers, coined names, dated claims). After a run, you can mechanically
ask: how many needles survived into (a) the final report, (b) the scratchpad,
(c) the post-compaction window? That's **recall@needle** — a hard number, no
LLM-judge required, deterministic with the FakeLLM. This single idea is what
turns "I have opinions about compaction" into "I have a measured result."
(Optional second metric: LLM-as-judge on the report for coverage/coherence — but
note its variance; that's a *threat to validity*, covered in the paper.)

**Read.** Greg Kamradt's NIAH (the original needle eval) for the paradigm; HELMET
(2410.02694) for *why a single needle number misleads*; and Judging LLM-as-a-Judge
(Zheng et al., 2306.05685) for the documented biases of judge scores. Read for:
*why is a planted, mechanically-checkable fact stronger evidence than a judge
score?* (Full notes: [`literature.md`](literature.md) §2.)

**Study.** [`tools/fixtures/index.json`](../../tools/fixtures/index.json) and one
fixture (e.g. `compaction.md`) — see exactly what the agent reads. This is where
needles will go. And `Scratchpad` in [`memory.py`](../../harness/memory.py) —
the externalized store you'll measure against.

**Build.** Write `experiments/needles.py`: a function that injects K labeled
needle-facts into a copy of the fixtures, and a scorer that, given a final
report + scratchpad, returns how many needles each contains. Test it on one
normal run. This is the measurement instrument for the whole paper.

**Gate.** *Describe the needle-fact metric in two sentences, and say why it's
reproducible where "judge the report" is not.*

---

# RESEARCH — *building toward the paper*

## Unit 6 — Make the compaction policy pluggable ⏱ ~2 days

**Idea.** Today there's one hard-coded policy inside `maybe_compact`. To compare
four, you need a clean seam: a `CompactionPolicy` interface that takes the
evicted messages and returns a replacement block, so the loop and the rest of
`ContextManager` don't change. This is ordinary software design (strategy
pattern), but doing it *without* breaking the tool-call/result invariant from
Unit 3 is the test of whether you really understood Unit 3.

**Read.** Re-read the Anthropic context-engineering post's compaction section
with new eyes — now you're implementing the alternatives it gestures at.

**Study.** `maybe_compact` again — identify the exact 4 lines that are
"policy" (choosing the split + producing the summary) vs. "mechanism" (swapping
`_body`). Only the policy part varies.

**Build.** Refactor so `maybe_compact` delegates to `self.policy.compact(old,
recent, llm)`. Implement four policies:
1. `TruncatePolicy` — drop `old`, no summary (a one-line marker).
2. `RecencySummaryPolicy` — today's behavior, moved behind the interface.
3. `ImportancePolicy` — score each `old` message (heuristic: presence of URLs /
   digits / note-saves), keep the top-scoring verbatim, summarize the rest.
4. `SemanticPolicy` — group `old` by crude topic (keyword clusters), summarize
   per group. (Embeddings optional; keep it offline-capable.)
Keep all existing tests green — that's your proof you didn't break the invariant.

**Gate.** *Run the full suite green with each of the four policies selected. If
any policy produces an invalid transcript on a real API, you missed Unit 3.*

---

## Unit 7 — Build the experiment ⏱ ~2–3 days

**Idea.** A result is `policy × run-length × seed → metrics`. Run-length (how
many sources the agent reads) is the independent variable that *forces* more
compaction events — that's where policies should diverge. You sweep it, repeat
across seeds for noise, and collect the metrics from Units 1 and 5.

**Read.** The "experimental setup" section of any short empirical ML paper, for
*shape*: what a clean results table looks like.

**Study.** `build_agent` in [`agent.py`](../../harness/agent.py) and the knobs in
`run.py` (`--context`, `--max-steps`) — these are your experiment's parameters.

**Build.** `experiments/bakeoff.py`: for each `(policy, run_length, seed)`, build
an agent with needles injected, run it, and record `{needle_recall_report,
needle_recall_scratchpad, total_tokens_billed, est_usd, steps, n_compactions}`.
Write results to `experiments/results.csv`. Then `experiments/plot.py` →
quality-vs-cost Pareto, one line per policy, points at increasing run-lengths.
**Methodology note you must resolve:** with the pure FakeLLM the *summary text*
is canned, so you can't study summary *quality* offline. Either (a) run the
compaction-summary step through a cheap real model while FakeLLM drives the
deterministic tool calls (a clean hybrid), or (b) restrict the offline study to
needle-recall + cost and validate quality on real models separately. Decide,
write down why. This decision is itself a paper-worthy paragraph.

**Gate.** *Produce the Pareto plot. Can you defend, from the data, whether the
repo's default (recency summary) was a good choice?*

---

## Unit 8 — Analyze and write the paper ⏱ ~2–3 days

**Idea.** A result isn't a paper until you've stated the claim, shown it's not an
artifact, and made it reproducible. The write-up is short (4–6 pages / a long
blog-paper): question, method, the needle-fact design, the Pareto figure,
threats to validity, and "run `python experiments/bakeoff.py` to reproduce."

**Read.** One well-regarded short workshop paper or empirical blog-post in the
agents space, purely for structure and tone.

**Study.** Your own `results.csv`. Find the *one* sentence the data supports
strongest — that's your headline claim. Everything else supports it.

**Build.** Write `paper/compaction-bakeoff.md` following the outline in
[`paper.md`](paper.md). Include the figure, the threats-to-validity section
(FakeLLM determinism, single task domain, judge variance, price-table
approximations), and the reproduction command.

**Gate.** *State your headline result in one sentence a skeptic can't trivially
dismiss, and name the strongest threat to it.*

---

## Unit 9 — Frontier & extensions ⏱ open-ended

**Idea.** Where this goes next, each a real research direction: importance scored
by a model instead of a heuristic; hierarchical / paged memory (full MemGPT);
sub-agents with isolated context as a compaction strategy (the Cognition vs.
Anthropic debate); learned compaction; semantic dedup before summarizing.

**Read.** Cognition, *Don't Build Multi-Agents* + the Anthropic managed-agents
post — the two sides of the "isolate context vs. share context" argument.

**Study.** The "where you'd extend it" table in
[`architecture.md`](../architecture.md) — each row is a follow-up paper.

**Build.** Pick one extension, write a one-page proposal: hypothesis, method,
metric, what to add to the repo. That's your *next* paper, seeded.

**Gate.** *Pitch your next experiment in 3 sentences: question, method, metric.*

---

## A note on honesty (read this when the experiment disappoints)

The most likely outcome of the bake-off is **not** "my clever policy wins." It's
something more boring and more true — e.g. *"recency summary is within noise of
the fancy policies until run-length exceeds K, and externalization dominates all
of them."* That is a **real result** and a better talk than a fake triumph. The
room you're presenting to respects a measured null result far more than an
unmeasured claim. Report what the data says, including when it says your
intuition was wrong. That instinct — more than any single technique here — is
what makes the difference between a builder who tinkers and a researcher.
