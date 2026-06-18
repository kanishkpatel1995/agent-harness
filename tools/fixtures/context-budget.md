# Context windows are a budget, not a backpack

The most common mental model for the context window is wrong. People imagine it
as a backpack: keep stuffing things in and the agent gets smarter. In practice
it behaves like a budget. Every token you spend on history is a token you can't
spend on reasoning, and past a certain fill level the quality of the model's
output drops even though it technically still fits.

## Why "just use a bigger window" doesn't save you

Larger windows raise the ceiling; they do not change the shape of the curve.
Three things degrade as the window fills, regardless of the maximum:

1. **Cost scales with input tokens.** A long-running agent re-sends most of its
   history on every single turn. A 30-step run that lets history grow linearly
   pays for that history 30 times. This is the line item that surprises people.
2. **Latency scales with input tokens.** Time-to-first-token grows with prompt
   length. An agent that felt snappy at step 3 feels sluggish at step 25.
3. **Attention dilutes.** Models reliably retrieve information at the start and
   end of a long context and lose the middle — the "lost in the middle" effect.
   The instruction you care about competes with thousands of tokens of stale
   tool output.

## The failure mode

The classic long-run failure is not a crash. It's a slow drift: the agent keeps
going, but the signal-to-noise ratio of its context falls until it starts
repeating tool calls, forgetting its own earlier conclusions, or ignoring the
goal. By the time it hits the hard context limit and errors out, it has usually
been producing low-quality work for several steps already.

## The reframe

Treat the window as a fixed budget you actively manage every turn:

- **Pin** the few things that must always be visible (system prompt, the goal).
- **Spend** the rest on the most recent, most relevant turns.
- **Evict** the stale middle by summarizing it and dropping the raw text.
- **Externalize** anything you might need later to durable storage, so eviction
  is never lossy in a way that matters.

The number that matters is not the model's maximum context. It's the *working
set* you choose to keep — the deliberately small slice of state that is enough
to take the next correct action. Good harnesses keep that working set roughly
constant no matter how long the run goes.
