# Observability: making the context window visible

Agents feel like black magic because their most important state — the context
window — is invisible. You see the inputs and the final output, but not the
thing that actually drives behavior: what the model saw on each turn. Most
"the agent is acting weird" problems dissolve the moment you can see the window.

## What to trace, per step

- **Step number and the action taken.** Which tool, with which arguments.
- **Context composition.** How many tokens are in the pinned section vs. the
  growing body, and what fraction of the budget is used. A simple bar chart in
  the terminal communicates this instantly.
- **Tool results, abbreviated.** Enough to see what came back, not so much that
  the trace itself becomes unreadable.
- **Compaction events.** When summarization fires, how many tokens it reclaimed,
  and how many messages it collapsed.
- **Running budget.** Steps, tokens, and dollars spent so far.

## Why composition matters more than raw size

Knowing the window is "6,000 tokens" tells you little. Knowing it's "1,200
pinned, 4,800 body, and the body is mostly one giant tool result" tells you
exactly what to fix. Trace the breakdown, not just the total.

## Watching compaction work

The most reassuring thing you can show — to yourself or an audience — is the
context bar growing step over step, crossing the threshold, and then snapping
back down when compaction fires, while the agent keeps making progress. That
single visual is the difference between "trust me, it manages memory" and
"watch it manage memory."

## From trace to debugging

Once you log composition per step, common bugs become obvious:

- The bar climbs and never drops -> compaction isn't firing; check the
  threshold.
- The bar drops but the agent then repeats work -> summaries are too lossy or the
  agent isn't reading its notes.
- One step balloons the bar -> a tool result needs truncation.

Observability turns agent debugging from archaeology into reading a dashboard.
Build the trace first; it pays for itself on the first weird run.
