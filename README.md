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

For a deeper module-by-module walkthrough, see [`docs/architecture.md`](docs/architecture.md).

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

## The research track: which way of forgetting is best?

The harness above teaches the moves. The `experiments/` tree measures them. It runs a
reproducible **compaction bake-off**: seven policies (truncate, recency, importance, semantic,
externalize, sub-agent, and a reversible hybrid that keeps both a summary and a retrievable raw
copy), scored by answer accuracy per token on two task types (FRAMES multi-hop QA and LoCoMo
conversational memory) across three model sizes, with a fixed LLM judge.

```bash
python -m experiments.applied -v        # the applied FRAMES/LoCoMo bake-off
python experiments/stats.py <results.csv> armA:armB    # bootstrap CIs + McNemar tests
```

Every run writes a self-contained folder (`experiments/runs/EXP-NNN__slug__UTC/`) with the
config, every prompt and response, the results, and the figure, so any number is reproducible.

- [`experiments/REGISTRY.md`](experiments/REGISTRY.md) — one row per experiment.
- [`docs/research-track/`](docs/research-track/) — the protocol, the paper draft, the literature.
- [`docs/research-track/paper/results-so-far.md`](docs/research-track/paper/results-so-far.md) — the running results synthesis.
- [`DECISIONS.md`](DECISIONS.md) — every design call we made, and every one we changed.

Headline so far: the best policy depends on the task (summarize for factual, keep the raw for
memory), the shipped default (recency summary) is dominated by plain truncation under pressure,
and the reversible hybrid is the one policy never in the loser group.

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
├── run.py                  CLI entrypoint (the offline demo)
├── harness/                THE TEACHING HARNESS (read this first)
│   ├── loop.py             the agent loop (read first)
│   ├── context.py          ContextManager — pinning, compaction (the heart)
│   ├── agent.py            assembles the deep-research agent from the parts
│   ├── memory.py           Scratchpad — external memory
│   ├── budget.py           steps/tokens/$ caps
│   ├── tools.py            tool registry + schemas
│   ├── trace.py            per-step context visualization
│   ├── llm.py              provider-agnostic client (litellm)
│   └── fake_llm.py         deterministic offline model
├── experiments/            THE RESEARCH: the compaction bake-off
│   ├── applied/            FRAMES + LoCoMo runners, the 7 policies, judge, embed store
│   ├── bench/              the controlled mechanism probe (window, run-context)
│   ├── nim.py              cached, watchdog-guarded model client (free NIM API)
│   ├── stats.py            bootstrap CIs + McNemar tests
│   ├── make_figures_*.py   publication figures (figstyle.py)
│   └── runs/               one folder per run: manifest + prompts + results + figures
├── presentation/           the talk: build_deck.js, build_talk_deck.js, brand, figures
├── docs/
│   ├── architecture.md     deeper module walkthrough
│   ├── demo-script.md      what to type and say on stage
│   ├── references.md       where to go to learn more
│   └── research-track/     protocol · curriculum · paper draft · literature
├── DECISIONS.md            every design call, and every one we changed
└── tests/
```

---

## Not in scope, on purpose

The **harness** is a teaching artifact: no retries-with-backoff, no parallel tool calls. You can
read the whole thing in 20 minutes and understand exactly how a long-running agent keeps its head
straight. The **research track** (`experiments/`) is where the heavier machinery lives, a vector
store and a full eval/bake-off, kept deliberately separate so the teaching core stays minimal.
See `docs/architecture.md` for how the pieces fit.

MIT licensed. Built for Learn Agentic AI — https://learnagentic.substack.com
