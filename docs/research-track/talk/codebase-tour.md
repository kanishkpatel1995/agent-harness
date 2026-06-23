# Codebase Tour: the AI Tinkerers talk (live in the editor)

*Speaker script for a ~22 minute, codebase-forward talk. You drive the editor (Cursor) live;
the deck (`presentation/founsi-talk.pptx`) is a backdrop on a second screen. Every stop names the
exact file and line range to open, what to say, and the decision or trade-off to land. Timings are
cumulative. Constraints: plain spoken prose, no em-dashes. The headline of the talk is the
memory-systems bake-off (segment 7): how the systems the audience already uses actually perform.*

Open files in tabs before you start, in this order: `harness/loop.py`, `harness/context.py`,
`experiments/bench/window.py`, `harness/policies/base.py`, `harness/policies/truncate.py`,
`harness/policies/hybrid.py`, `experiments/applied/mem0_backend.py`, `experiments/nim.py`, and a
terminal. Zoom the editor font to ~18pt. Have `python run.py` and `python -m harness.compare` in
shell history.

---

## 0. Hook (slide) — 0:00 to 1:30

Slide: the title. Say:

> "I built an agent that runs for fifty steps without falling over, and a benchmark to prove which
> way of forgetting keeps it alive. One idea: the model is a commodity you rent. The harness, the
> code around the model, is the part you actually build, and the single most important thing it
> does is decide what to forget. Tonight I will show you the code, and then I will show you how the
> memory systems you already use, LangChain, Chroma, Mem0, actually perform when you measure them."

Land: this is a *how it works* talk with a *measured* payoff. Not a results-only talk, not a
framework demo.

## 1. Architecture in one diagram (slide) — 1:30 to 2:45

Slide: the loop diagram plus the data path (ContextManager, policies, store, judge, run-dirs). Say:

> "Three moving parts. An agent loop that never changes. A ContextManager that decides what the
> model sees each turn. And a set of compaction policies, swappable, that decide what to drop when
> the window fills. Everything else, the store, the judge, the run directories, exists to measure
> which policy is best."

Transition: "Let me show you how small the loop actually is."

## 2. The loop, live — `harness/loop.py` — 2:45 to 4:30

Open `harness/loop.py`, scroll to `run_agent`. Point at the `for step` loop.

> "This is the whole agent loop. Eighty lines. Check the budget, call the model, run the tools,
> repeat. The agent is trivial."

Now point at `context.maybe_compact(llm)`.

> "This one line is the entire talk. After every step we ask the context manager: are we over
> budget, and if so, forget something. That decision is where agents live or die."

Land: the loop is commodity; the value is in `maybe_compact`.

## 3. The heart, live — `harness/context.py` — 4:30 to 7:00

Open `harness/context.py`. Start at the two knobs: `compact_at = 0.75`, `keep_recent`.

> "The reframe that makes this work: the context window is a budget, not a backpack. We do not wait
> for the hard limit. We compact at seventy-five percent and keep the working set roughly constant
> no matter how long the run goes."

Point at the pinned messages.

> "Two messages are pinned, the goal and the system prompt. Never summarized, never dropped.
> Everything else is fair game."

Walk `maybe_compact`: the threshold check and the call to the split.

> "Over threshold? Find a safe split point, summarize the old middle, drop the raw turns, keep the
> recent ones. Lossy on purpose. Let me show you that it is safe."

## 4. Demo one, live — the terminal — 7:00 to 8:15

Terminal. Offline, no key:

```
python run.py "Compare three small cities for a team offsite"
```

> "Watch the step count climb. The window grows, crosses the threshold, COMPACT fires, the window
> snaps back, and the agent keeps going past where it would have died."

Then:

```
cat run/notes.md
```

> "Here is why lossy compaction is safe. Before we dropped the raw turns, the findings were written
> to disk. The window forgot; the agent did not."

## 5. The trade-off that bites everyone — `experiments/bench/window.py` — 8:15 to 9:30

Open `window.py`, `_safe_split`. Five lines.

> "Here is the gotcha that costs people hours. You can never split a tool-call from its result. Cut
> the transcript between 'the model called search' and 'search returned this', and a real API
> rejects the whole conversation. These five lines walk the boundary so the kept tail never starts
> on an orphan tool result. Correctness over convenience."

## 6. The seam, plus demo two — `harness/policies/` + `harness.compare` — 9:30 to 11:30

Open `harness/policies/base.py`. Point at the `Policy` Protocol.

> "Every way of forgetting is one tiny class with one method: compact, old turns in, replacement
> block out, plus a flag for whether it retrieves. That is the seam the whole benchmark plugs into."

Open `truncate.py` (two lines) and `hybrid.py` side by side.

> "Truncate: drop the oldest, no model call, the cost floor. Hybrid, my bet: keep a summary in the
> window AND push the raw to a store, so the gist is cheap and the detail stays retrievable. Nobody
> had measured whether carrying both pays off."

Terminal, offline:

```
python -m harness.compare "quantum networking startups"
```

> "One planted fact, a codename and a ship date, run through all seven policies. Truncate drops it,
> summaries blur it, the sub-agent fan-out is the most expensive and still loses it, and the two
> that keep it are the ones that kept the raw retrievable. Swap a string, get a different agent.
> That swappability is the entire reason the next part is possible."

## 7. Headline: you are not alone, and I measured them — 11:30 to 14:30

Open `harness/policies/adapters/` (list it), then `experiments/applied/mem0_backend.py`.

> "The famous memory systems are the same five-line shape. LangChain's summary buffer is my recency
> policy. Chroma is my externalize store with a different embedder. Mem0 is externalize with an LLM
> that extracts and dedupes facts first. So I wrapped each one behind the same seam and ran them on
> the same questions, the same judge, the same model. Here is what fell out."

Slides (the EXP-006 / EXP-007 head-to-heads). Land three numbers, slowly:

> "One. My fifteen-line recency policy beat LangChain's shipped ConversationSummaryBufferMemory,
> zero point four five to zero point three five, at lower token cost. The framework default bought
> a dependency, not accuracy.
>
> Two. The memory backend itself moves the needle. The same externalize policy with a
> retrieval-tuned embedder scored zero point five zero; with a general local embedder, zero point
> three five. The embedding model alone is fifteen points.
>
> Three. Mem0, which distills raw text into deduped facts, scored below storing the raw chunks, and
> it cost an LLM call on every single write. Compression lost the needle, which is the whole thesis
> of this talk showing up in a third-party system."

Land: the systems you reach for by default are choices on one map, and the defaults are often not
the right choice. Measure, do not assume.

## 8. War stories (slides) — 14:30 to 18:00

The bugs that taught the lessons. One slide each. This is the part the audience remembers.

**8a. The metric that almost fooled me.** Substring scoring made my best policy look worst at 0.21;
an LLM judge that credits paraphrase flipped it to 0.62. Your eval can invert your conclusion.

**8b. The agent that froze at zero percent CPU.** Runs hung forever, no error, past the library
timeout. Fix: every model call on a worker thread with a hard wall-clock deadline. Do not trust a
library's timeout. (Flash `experiments/nim.py`, `_completion_with_deadline`.)

**8c. The confound I caught.** My 70B hybrid "win" at 0.67 dropped to 0.53 once I held the
summarizer constant. The win was partly the summarizer. I report the worse, honest number.

**8d. Making the OSS adapters actually run (the fresh one).** nv-embedqa needs an input_type the
stock client never sends. Torch was too old for the GPU embedders, so Chroma runs on a bundled ONNX
model instead. Mem0's vector store would not even import on Python 3.9. Half of "use the famous
system" is making the famous system run at all.

Land: building a benchmark is mostly catching the ways you are fooling yourself.

## 9. The payoff in three lines (slides) — 18:00 to 20:30

> "Seven policies, two task types, three model sizes, and four real memory systems. Three things.
> One: the best policy depends on the task. Summarize for factual questions, keep the raw for
> conversational memory. The ranking literally inverts. Two: the policy that ships in most agents,
> summarize the stale middle, is dominated by plain truncation under pressure, same accuracy, seven
> times the cost, and it loses to a fifteen-line version of itself. Three: the one policy never in
> the loser group keeps both a summary and the raw. Keep the raw retrievable."

Show the cross-domain transfer figure with error bars.

## 10. Reproducible, and close — 20:30 to 22:00

> "Every experiment is a folder: the config, every prompt and response, the results, the figure.
> The bar I held is that a stranger clones the repo and regenerates any number, including the
> memory-systems comparison you just saw. Clone it, break it, tell me I am wrong."

Slide: the repo QR. End.

---

## Timing summary

| segment | end | mode |
|---|---|---|
| hook + architecture | 2:45 | slides |
| loop | 4:30 | editor |
| context manager | 7:00 | editor |
| demo one (run.py) | 8:15 | terminal |
| safe-split | 9:30 | editor |
| policies seam + compare | 11:30 | editor + terminal |
| memory systems (headline) | 14:30 | editor + slides |
| war stories | 18:00 | slides |
| payoff | 20:30 | slides |
| reproducible + close | 22:00 | slide |

About eleven minutes in the editor and terminal, the rest on slides. If you run long, cut war story
8c. If short, open one more policy (`importance.py`) or a second adapter (`chroma_backend.py`).

## Pre-flight checklist

- `python run.py` works offline (no key) and shows a COMPACT event. Test it the morning of.
- `python -m harness.compare "..."` runs offline and prints the seven-policy table. Test it too.
- Editor font ~18pt, line numbers on, the eight files open in tabs in tour order.
- Deck open on the second display; advance only on the slide segments (1, 7, 8, 9, 10).
- Have `cat run/notes.md` ready in shell history.
- Memory-systems numbers on the slides: recency 0.45 vs langchain 0.35; nim 0.50 vs chroma 0.35;
  mem0 trails both at a higher per-add cost. (Confirm the final Mem0 n=20 figure before the talk.)
