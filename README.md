# agent-harness

A minimal, readable agent harness built to teach one thing: **context
engineering** — how to keep a long-running agent from falling apart as its
context window fills up.

It's a deep-research agent (search → read → take notes → synthesize), but the
agent task is just an excuse. The point is the harness around the model: the
loop, the context manager, the budget, the external memory, and the trace that
makes all of it visible.

> Talk: *"Context Engineering Inside the Harness — Keeping a Long-Running Agent
> From Falling Apart."* AI Tinkerers Calgary, June 23 2026.

---

## Quickstart (30 seconds, no API key)

```bash
git clone https://github.com/kanishkpatel1995/agent-harness
cd agent-harness
python run.py "context engineering for long-running agents"
```

That runs the **FakeLLM** — a deterministic, offline stand-in for a real model.
No key, no network. You'll watch the context window grow step by step, cross its
threshold, and snap back down when compaction fires, while the agent keeps
working. Then open `run/notes.md` to see the agent's externalized memory.

### Run it with a real model

```bash
pip install -r requirements.txt
cp .env.example .env          # add your key
python run.py --real --model gpt-4o-mini "your topic here"
```

Any litellm-supported model works — swap the `--model`:

| Provider | `--model` value |
|----------|-----------------|
| OpenAI   | `gpt-4o-mini`, `gpt-4o` |
| Anthropic| `claude-3-5-sonnet-20241022` |
| Google   | `gemini/gemini-1.5-pro` |
| Local (Ollama) | `ollama/llama3.1` |

For real web search/fetch instead of offline fixtures: `HARNESS_OFFLINE=0`.

---

## The whole idea in one picture

```
            ┌─────────────────────────────────────────────┐
            │                  THE LOOP                     │   loop.py  (~40 lines)
            │   ask model → run tools → manage context →    │
            │                  repeat                       │
            └───────┬───────────────┬───────────────┬──────┘
                    │               │               │
            ┌───────▼──────┐ ┌──────▼──────┐ ┌──────▼───────┐
            │   LLM client │ │   Tools     │ │ ContextMgr   │
            │ (any model   │ │ search/fetch│ │ pin · count  │
            │  via litellm)│ │ note/read   │ │ truncate ·   │
            │  llm.py      │ │ tools.py    │ │ COMPACT      │
            └──────────────┘ └──────┬──────┘ │ context.py   │
                                    │        └──────────────┘
                             ┌──────▼──────┐ ┌──────────────┐
                             │  Scratchpad │ │   Budget     │
                             │ memory on   │ │ steps/tokens │
                             │ disk        │ │ /$ kill sw.  │
                             │ memory.py   │ │ budget.py    │
                             └─────────────┘ └──────────────┘
                                    Trace (trace.py) wraps it all and
                                    prints the context window every step.
```

**The loop is trivial. The other files are the talk.**

---

## Read the code in this order

1. **`harness/loop.py`** — the entire agent loop. Start here. It's small on
   purpose.
2. **`harness/context.py`** — the ContextManager. Pinning, token counting,
   truncation, and compaction. This is the heart.
3. **`harness/memory.py`** — the Scratchpad. Memory that lives outside the window.
4. **`harness/budget.py`** — steps/tokens/dollars caps. The kill switch.
5. **`harness/tools.py`** + **`tools/web.py`** — what the agent can do.
6. **`harness/trace.py`** — how the demo becomes visible.
7. **`harness/llm.py`** / **`harness/fake_llm.py`** — the provider-agnostic
   client and its deterministic offline twin.

---

## The five context-engineering moves (and where they live)

| Move | What it does | File |
|------|--------------|------|
| **Pin** | Goal + system prompt are never dropped | `context.py` |
| **Truncate** | Oversized tool outputs are capped before entering the window | `context.py` |
| **Compact** | The stale middle is summarized and the raw turns dropped | `context.py` |
| **Externalize** | Findings live in a file, not the window | `memory.py` |
| **Cap** | Steps, tokens, and dollars are hard-limited | `budget.py` |

---

## Run the tests

```bash
pip install pytest
python -m pytest
```

All tests run offline with the FakeLLM. They cover pinning, truncation,
compaction (including the tool-call boundary edge case), the budget kill switch,
and a full end-to-end run.

---

## Layout

```
agent-harness/
├── run.py                  CLI entrypoint
├── harness/
│   ├── loop.py             the agent loop (read first)
│   ├── context.py          ContextManager — pinning, compaction (the heart)
│   ├── memory.py           Scratchpad — external memory
│   ├── budget.py           steps/tokens/$ caps
│   ├── tools.py            tool registry + schemas
│   ├── trace.py            per-step context visualization
│   ├── llm.py              provider-agnostic client (litellm)
│   └── fake_llm.py         deterministic offline model
├── tools/
│   ├── web.py              search + fetch (offline fixtures or real)
│   └── fixtures/           cached pages for the offline demo
├── examples/run_offline_demo.py
├── docs/
│   ├── architecture.md     deeper walkthrough
│   ├── demo-script.md      what to type and say on stage
│   └── references.md       where to go to learn more
└── tests/
```

---

## Not in scope (on purpose)

This is a teaching harness, not a framework. No retries-with-backoff, no
parallel tool calls, no vector store, no eval suite. Those are good next steps —
see `docs/architecture.md` for where each would slot in. The goal here is that
you can read the whole thing in 20 minutes and understand exactly how a
long-running agent keeps its head straight.

MIT licensed. Built for Learn Agentic AI — https://learnagentic.substack.com
