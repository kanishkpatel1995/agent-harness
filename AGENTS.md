# AGENTS.md

Briefing for any AI agent (or human) working in this repo.

## What this project is

A minimal, readable **agent harness** that teaches context engineering for
long-running agents. The demo task is deep research (search → read → note →
synthesize), but the lesson is the harness, not the task. It's the companion
code for an AI Tinkerers talk and for the Learn Agentic AI newsletter.

Optimize every change for **readability and teaching value**, not for
production completeness. If a change makes the code more capable but harder to
read in one sitting, it's probably the wrong change for this repo.

## Tech stack

- Python 3.10+
- `litellm` for provider-agnostic model calls (lazy-imported)
- `pytest` for tests
- No framework (no LangChain/LlamaIndex) — that's deliberate

## How to run / test

```bash
python run.py "some topic"            # offline FakeLLM demo, no key needed
python run.py --real --model gpt-4o-mini "some topic"   # real model
python -m pytest                      # all tests, offline
python examples/run_offline_demo.py   # the stage demo
```

## Conventions

- Messages are plain dicts in OpenAI format so litellm normalizes across
  providers. Don't introduce provider-specific message shapes.
- The FakeLLM must stay in lockstep with `LLMClient`'s interface
  (`complete()` returning `LLMResponse`, `count_tokens()`). If you change one,
  change both.
- Anything offline must stay offline: tests and the FakeLLM demo never touch the
  network and never require an API key.
- Module docstrings explain *why*, not just *what* — keep that style.

## Do / Don't

- **Do** keep `loop.py` small. It's the centerpiece of the talk. New behavior
  usually belongs in `context.py`, `budget.py`, or a tool — not the loop.
- **Do** preserve the tool-call ↔ tool-result pairing when touching compaction
  (`_safe_split_index`). Breaking it produces invalid transcripts on real APIs.
- **Do** run `python -m pytest` before considering a change done.
- **Don't** add heavy dependencies or a framework.
- **Don't** make the offline path require keys or network.
- **Don't** delete the explanatory docstrings to "clean up" — they are the
  product.

## Where things live

- `harness/loop.py` — the loop (read first)
- `harness/context.py` — ContextManager: pin, count, truncate, compact (the heart)
- `harness/memory.py` — Scratchpad: external memory
- `harness/budget.py` — steps/tokens/$ caps
- `harness/tools.py` + `tools/web.py` — tools and web access
- `harness/trace.py` — per-step context visualization
- `harness/llm.py` / `harness/fake_llm.py` — real and offline models
- `docs/` — architecture, demo script, references
- `tests/` — all offline
