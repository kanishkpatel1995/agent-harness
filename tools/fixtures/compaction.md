# Compaction strategies for long-running agents

Compaction is the act of shrinking the conversation history once it grows past a
threshold, so the working set stays roughly constant. There are three common
strategies; most production harnesses combine them.

## 1. Sliding window (drop the oldest)

Keep the last N messages, discard the rest. Cheap and predictable.

- **Pros:** trivial, zero extra model calls, deterministic.
- **Cons:** purely recency-based. The agent forgets early decisions and goals
  unless those are pinned separately. Works poorly for tasks where early
  context matters throughout.

The fix is to always pin the system prompt and the goal outside the sliding
window so they are never dropped.

## 2. Summarize-and-drop (recursive summarization)

When the window crosses a threshold, take the old middle of the conversation,
ask the model to compress it into a dense summary, and replace those raw turns
with the summary.

- **Pros:** retains the *gist* of long histories at a fraction of the tokens.
  Scales to very long runs.
- **Cons:** lossy by construction. Summaries can drop the one detail you needed,
  and summarizing costs an extra model call. Errors compound if you summarize
  summaries repeatedly.

Two practical rules: (a) never summarize across a tool-call boundary — keep an
assistant tool call and its result together, or you produce an invalid
transcript; (b) instruct the summarizer to preserve concrete facts, numbers, and
URLs, and to drop conversational filler.

## 3. Hierarchical / external memory

Don't rely on the summary at all for facts. Have the agent write findings to an
external store (a file, a vector DB, a KV store) and keep only pointers in the
window. Compaction becomes safe because the raw detail still exists on disk; the
summary just needs to remind the agent that it's there.

- **Pros:** effectively unbounded memory; compaction is no longer lossy in a way
  that matters.
- **Cons:** the agent has to be disciplined about writing notes, and you need a
  retrieval path back to them.

## What breaks, and when

- Summarize-and-drop breaks when a late step needs an exact early detail that the
  summary smoothed over. Mitigate with external memory.
- Sliding window breaks the moment the task requires anything older than N turns.
  Mitigate with pinning.
- External memory breaks when the agent forgets to write notes, or writes them so
  vaguely they're useless. Mitigate with a system-prompt rule and a tool that
  makes note-taking the path of least resistance.

The strong default: pin goal + system, slide the recent window, summarize the
evicted middle, and back it all with an external scratchpad.
