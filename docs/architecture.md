# Architecture

A deeper walkthrough than the README. Read this after you've run the demo once.

## The one-sentence version

A stateless model is called in a loop; on every turn the harness rebuilds the
exact list of messages the model sees, and the engineering is all in *what goes
in that list*.

## The turn lifecycle

Each iteration of `run_agent` (in `loop.py`) does this:

1. **Check the budget.** `budget.check_step()` increments the step counter and
   raises `BudgetExceeded` if we're over the step cap.
2. **Build the window and call the model.** `context.messages()` returns
   `pinned + body`. The model sees this and only this. `llm.complete()` returns
   either text (it's done) or tool calls (it wants to act).
3. **Record usage.** `budget.record_usage()` adds prompt/completion tokens and
   estimated dollars, and raises if either cap is crossed.
4. **Act.** For each tool call, `tools.dispatch()` runs the function and the
   result is appended to the body via `context.add_tool_result()` (which
   truncates oversized results).
5. **Compact if needed.** `context.maybe_compact()` checks the token count and,
   if over threshold, summarizes the old middle and drops the raw turns.

That's the whole system. Everything below is detail on step 2, 4, and 5.

## The context window, segment by segment

`ContextManager` keeps two lists:

- `_pinned` — the system prompt and the goal. Never summarized, never dropped.
  This guarantees the agent never "forgets why it's here," no matter how long
  the run.
- `_body` — everything else: assistant turns, tool calls, tool results, and (after
  compaction) summary markers.

`messages()` is just `_pinned + _body`. `composition()` reports the token split
so `trace.py` can draw the bar.

## Compaction, carefully

`maybe_compact()`:

1. If `token_count() <= max_context_tokens * compact_at`, do nothing.
2. Otherwise pick a split point that keeps the last `keep_recent` messages
   verbatim.
3. `_safe_split_index()` nudges the split so the kept tail never *starts* on a
   `tool` message — a tool result is only valid immediately after the assistant
   message that requested it. Splitting there produces a transcript real APIs
   reject. This is the single fiddliest bit of the whole repo.
4. Summarize the evicted middle (via the model, with a fallback) and replace it
   with one `[COMPACTED MEMORY]` system message that also reminds the agent its
   details are in the scratchpad.

Compaction is **lossy by design** — which is only safe because of the scratchpad.

## Why the scratchpad makes compaction safe

`memory.py` writes findings to `run/notes.md`. The agent is told (in the system
prompt) to `save_note` anything worth keeping and to `read_notes` before writing
the report. So when compaction throws away raw page text, nothing important is
gone — the durable version is on disk. The window holds a *working set*; the file
holds the *archive*.

## The budget as a single source of truth

`budget.py` tracks three runaway dimensions — steps, tokens, dollars — in one
object the loop consults every turn. It fails soft: `run_agent_safe()` catches
`BudgetExceeded` and returns the best answer so far instead of crashing.

## Provider-agnosticism

`llm.py` wraps `litellm.completion()`, so messages stay in OpenAI format and any
provider works via `HARNESS_MODEL`. `fake_llm.py` mirrors the same interface with
a scripted, deterministic flow so everything runs offline. The rest of the
harness never knows or cares which one it's talking to.

## Where you'd extend it

| Want | Where it slots in |
|------|-------------------|
| Retries / backoff on tool failure | wrap `tools.dispatch()` in `loop.py` |
| Parallel tool calls | the `for call in response.tool_calls` block in `loop.py` |
| Vector-store memory | swap `Scratchpad` in `memory.py` for an embedding store |
| Semantic compaction / importance ranking | `ContextManager._summarize` + split logic |
| Sub-agents (isolated context) | spawn a second `build_agent` for a sub-goal |
| Real eval suite | add `tests/` cases with recorded transcripts |

Each is a deliberate "next exercise," not a missing feature.
