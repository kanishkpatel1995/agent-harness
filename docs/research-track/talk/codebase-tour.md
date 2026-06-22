# Codebase Tour: the AI Tinkerers talk (live in the editor)

*Speaker script for a 20 to 25 minute, codebase-forward talk. You drive the editor (Cursor)
live; the deck is a backdrop. Every stop below names the exact file and line range to open,
what to say, and the decision or trade-off to land. Timings are cumulative. Constraints: plain
spoken prose, no em-dashes. Keep the deck on the architecture slide except where noted.*

Open files in tabs before you start, in this order: `harness/loop.py`, `harness/context.py`,
`experiments/bench/window.py`, `experiments/applied/policies.py`, `experiments/nim.py`, a
terminal. Zoom the editor font to ~18pt.

---

## 0. Hook (slide) — 0:00 to 1:30

Slide: the title. Say:

> "I built an agent that runs for fifty steps without falling over, and a benchmark to prove
> which way of forgetting keeps it alive. Here is the one idea: the model is a commodity you
> rent. The harness, the code around the model, is the part you actually build, and the single
> most important thing it does is decide what to forget. Let me show you the code."

Land: this is a *how it works* talk, not a results talk. Results come at the end as the payoff.

## 1. Architecture in one diagram (slide) — 1:30 to 3:00

Slide: the loop diagram (perceive, think, act) plus the data path (ContextManager, policies,
store, judge, run-dirs). Say:

> "Three moving parts. An agent loop that never changes. A ContextManager that decides what the
> model sees each turn. And a set of compaction policies, swappable, that decide what to drop
> when the window fills. Everything else, the store, the judge, the run directories, is in
> service of measuring which policy is best."

Transition: "Let me show you how small the loop actually is."

## 2. The loop, live — `harness/loop.py` lines 20 to 66 — 3:00 to 5:00

Open `harness/loop.py`, scroll to `run_agent` (line 20). Point at the `for step` loop (line 32).

> "This is the whole agent loop. Eighty lines. Check the budget, call the model, run the tools,
> repeat. That is it. The agent is trivial."

Now point at line 61, `compacted = context.maybe_compact(llm)`.

> "This one line is the entire talk. After every step, before the next, we ask the context
> manager: are we over budget, and if so, forget something. That decision is where agents live
> or die."

Land (decision): the loop is commodity; the value is in `maybe_compact`. Trade-off teaser: how
you forget is unmeasured in most frameworks, which is why I built the benchmark.

## 3. The heart, live — `harness/context.py` lines 40 to 135 — 5:00 to 8:00

Open `harness/context.py`. Start at the class (line 40) and the two knobs (lines 44 to 46):
`compact_at = 0.75`, `keep_recent`.

> "The reframe that makes this work: the context window is a budget, not a backpack. We do not
> wait for the hard limit. We compact at seventy-five percent and keep the working set roughly
> constant no matter how long the run goes."

Point at the pinned messages (line 56).

> "Two messages are pinned: the goal and the system prompt. They are never summarized, never
> dropped. Everything else is fair game."

Now the method `maybe_compact` (line 113). Walk the threshold check (line 118) and the call to
`_safe_split_index` (line 124).

> "Over threshold? Find a safe split point, summarize the old middle, drop the raw turns, keep
> the recent ones. Lossy on purpose. We will see in the demo why that is safe."

Land (decision): pin the goal, compact the stale middle (the low-attention zone), keep recent
verbatim. Transition: "But there is one rule you cannot break when you cut a transcript."

## 4. The trade-off that bites everyone — `experiments/bench/window.py` lines 28 to 34 — 8:00 to 9:30

Open `experiments/bench/window.py`, line 28, `_safe_split`. Five lines.

> "Here is the gotcha that costs people hours. You can never split a tool-call from its result.
> If you cut the transcript between 'the model called search' and 'search returned this', a real
> API rejects the whole conversation. This five-line function walks the boundary so the kept
> tail never starts on an orphan tool result."

Land (trade-off): correctness over convenience. You cannot compact mid-pair, so the split point
is constrained, and that constraint is non-negotiable with real tool-calling APIs.

## 5. The policies, live — `experiments/applied/policies.py` — 9:30 to 12:00

Open `experiments/applied/policies.py`. Point at the interface: every policy is a tiny class
with one method, `compact(self, old, llm, store)`, and a `retrieves` flag.

Show `Truncate` (line 24, the body is two lines):

> "The cheap floor. Drop the oldest raw turns. No model call. Loses the most."

Show `ReversibleHybrid` (line 54):

> "My bet. Keep a summary in the window AND write the raw turns to a store, so the gist is cheap
> in context and the detail stays losslessly retrievable. Nobody had measured whether carrying
> both actually pays off."

Show the `POLICIES` registry (line 132):

> "Seven ways to forget, one dictionary. Swap a string, get a different agent. That swappability
> is the whole reason the bake-off is possible."

Land (architecture decision): a policy is a small, single-responsibility class behind a fixed
interface, so the agent does not know or care which one it runs. That is what makes them
measurable head-to-head.

## 6. War stories (slides) — 12:00 to 17:00

Four decisions that broke and got fixed. One slide each. This is the part the audience remembers.

**6a. The metric that almost fooled me.**
> "First time I scored answers with a substring match, my best policy looked like the worst, at
> 0.21. Switched to an LLM judge that credits paraphrase, and the same policy jumped to 0.62. The
> metric inverted the ranking. Lesson: your eval can quietly flip your conclusion."

**6b. The agent that froze at zero percent CPU.**
Optionally flash `experiments/nim.py` line 30, `_completion_with_deadline`.
> "Runs would hang forever. Python sitting at zero percent CPU, no error. The library's timeout
> was silently not firing for this provider. The fix: run every model call on a worker thread
> with a hard wall-clock deadline, so a wedged socket raises instead of freezing the whole study.
> Lesson: do not trust a library's timeout."

**6c. The reasoning model that would not shut up.**
> "I tried a reasoning model as the summarizer. Asked to compress, it emitted two thousand to
> twenty thousand token 'summaries'. Turning thinking off corrupted them. The fix was a split:
> a fast model writes the summaries, the reasoning model only answers. Lesson: reasoning models
> are bad compactors."

**6d. The confound I caught yesterday.**
> "My 70B headline was that my hybrid won at 0.67. Then I held the summarizer constant and it
> dropped to 0.53. The win was partly the summarizer, not the answer model. I am telling you the
> worse number because that is the honest one. Lesson: isolate your variable, even when it costs
> you the headline."

Land: building a benchmark is mostly catching the ways you are fooling yourself.

## 7. Live demo (terminal) — 17:00 to 19:00

Terminal. Run the offline demo (no key, no network):

```
python run.py "Compare three small cities for a team offsite"
```

Narrate as it streams:
> "Watch the step count climb. The window grows, crosses the threshold, COMPACT fires, the
> window snaps back, and the agent keeps going past where it would have died."

Then show the externalized scratchpad:

```
cat run/notes.md
```

> "Here is why lossy compaction is safe. Before we dropped the raw turns, the findings were
> written to disk. The window forgot; the agent did not."

Backup if live fails: a recorded gif or the same on a screenshot slide.

## 8. The payoff (slides) — 19:00 to 22:00

Now, and only now, the results. Two or three slides, fast.

> "I ran seven policies across two task types and three model sizes. Three things. One: the best
> policy depends on the task. On factual multi-hop questions, summarize. On conversational
> memory, keep the raw retrievable. The ranking literally inverts. Two: the policy that ships in
> most agents, summarize the stale middle, is dominated by plain truncation under pressure: same
> accuracy, seven times the cost. Three: the one policy that is never the loser in any setting is
> the one that keeps both a summary and the raw. Keep the raw retrievable."

Show the cross-domain transfer figure with the error bars (the inversion is visible).

## 9. Reproducible, and close — 22:00 to 24:00

> "Every experiment is a folder: the config, every single prompt and response, the results, the
> figure. The bar I held is that a stranger can clone the repo and regenerate any figure. It is
> all there. Clone it, break it, tell me I am wrong."

Slide: the repo QR. End.

---

## Timing summary

| segment | end | mode |
|---|---|---|
| hook + architecture | 3:00 | slides |
| loop | 5:00 | editor |
| context manager | 8:00 | editor |
| safe-split | 9:30 | editor |
| policies | 12:00 | editor |
| war stories | 17:00 | slides (+ flash nim.py) |
| demo | 19:00 | terminal |
| payoff | 22:00 | slides |
| reproducible + close | 24:00 | slide |

About thirteen minutes in the editor and terminal, the rest on slides. If you run long, cut a
war story (keep 6a and 6d). If short, expand the context-manager walk or open one more policy
(Importance, line 67, the tail-bound one).

## Pre-flight checklist

- `python run.py` works offline (no key) and shows a COMPACT event. Test it the morning of.
- Editor font ~18pt, line numbers on, the six files open in tabs in tour order.
- Deck open on a second display or use presenter view; advance only on the slide segments.
- Have `cat run/notes.md` ready in shell history.
