# Budgets, caps, and kill switches for agents

An agent loop is, by design, a thing that decides how many times to run itself.
That is exactly the property that lets it run away from you. Three dimensions go
runaway, and you should cap all three explicitly.

## The three runaway dimensions

1. **Steps.** The agent loops forever, often oscillating between two tool calls,
   or re-reading the same source. Cap the number of iterations. When you hit the
   cap, stop and return the best answer so far rather than crashing.
2. **Tokens.** Even within a step limit, a few huge tool outputs (a 200KB page,
   a giant file) can blow your token budget. Cap total tokens and truncate
   individual tool results before they enter the context.
3. **Dollars.** Steps and tokens are proxies; cost is the thing you actually
   care about. Track estimated USD per call using per-model pricing and stop the
   moment you cross a hard cap.

## Designing the kill switch

A good budget is a single object the loop checks before every model call and
updates after every response. The important design choices:

- **Fail soft, not hard.** When a cap trips, don't raise an unhandled exception
  into the user's process. Catch it in the loop, return whatever the agent has
  produced, and surface why it stopped.
- **Make limits visible.** Print the running totals every step (steps used,
  tokens spent, dollars spent) so you — and your audience — can watch the
  agent's resource consumption in real time.
- **Set caps per environment.** A generous cap in development; a tight cap in
  any automated or production path. Never ship an uncapped agent to prod.

## Truncation as a budget tool

Truncating oversized tool results is part of budgeting, not just formatting. A
single unbounded fetch can dominate the window. Cap each tool result at a
sensible length, keep the head, and write the full version to the scratchpad so
nothing is lost. The agent reads the summary by default and the full text only
if it asks.

## The mindset

Caps are not a safety afterthought; they are part of the agent's definition. "An
agent that researches a topic" is underspecified. "An agent that researches a
topic in at most 20 steps, 50K tokens, and 50 cents" is something you can
actually run unattended.
