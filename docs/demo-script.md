# Demo script — what to type and say

For the live portion. Total ~4 minutes. Everything is offline (FakeLLM), so it
works on conference wifi or no wifi.

## Before you go on

```bash
cd agent-harness
python -m pytest -q        # green, proves it works
clear
```

Have two things open: a terminal, and `harness/loop.py` in your editor.

## Beat 1 — "the loop is the boring part" (45s)

Show `harness/loop.py`. Scroll the ~40 lines of `run_agent`.

> "This is the entire agent loop. Ask the model, run the tools it asked for,
> manage the context, repeat. That's it. If the loop is this small, why do
> long-running agents fall apart? Because everything that matters is in the one
> line that says `context.maybe_compact`."

## Beat 2 — run it (90s)

```bash
python run.py "context engineering for long-running agents"
```

Talk over the output as the bar grows:

> "Watch the context bar. Purple is pinned — the goal and system prompt, never
> dropped. Cyan is the working history. It climbs as the agent reads sources…"

When `⚙ COMPACTED` appears:

> "…and there. It crossed 75% of the budget, summarized the old turns, and the
> window snapped back down — while the agent kept going. That single event is
> the difference between an agent that runs for 5 steps and one that runs for 50."

## Beat 3 — show the externalized memory (45s)

```bash
cat run/notes.md
```

> "Compaction threw away the raw pages — but nothing was lost, because the agent
> wrote its findings here, on disk, outside the context window. The window holds
> what it needs *now*; the file holds everything. That's why compaction is safe."

## Beat 4 — swap the brain (optional, 30s)

Show that it's provider-agnostic:

```bash
# python run.py --real --model claude-3-5-sonnet-20241022 "..."
# python run.py --real --model ollama/llama3.1 "..."
```

> "Same harness, any model — one flag. The harness doesn't care if the brain is
> Claude, GPT, or a local Llama. The brain is swappable; the context engineering
> is the part you own."

## If something breaks

- Nothing should need the network. If a command hangs, Ctrl-C and rerun — it's
  deterministic.
- Fallback: `python examples/run_offline_demo.py` does the same thing in one shot.
- Last resort: you already ran `pytest` green on stage; talk to the code in the
  editor instead.

## The line to land on

> "The model is a commodity you rent. The harness — what it sees, what it
> remembers, when it stops — is the part you build. That's where the engineering
> is."
