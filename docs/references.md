# References & further reading

Curated, opinionated. These are the sources behind the talk and the best places
to go deeper. Grouped by what they're good for.

## Start here — context engineering

- **Effective context engineering for AI agents** — Anthropic Engineering, Sep 29
  2025. The single most on-point read for this talk. Names the exact moves this
  harness implements: compaction, structured note-taking, and the "context rot"
  problem. https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- **Don't Build Multi-Agents** — Walden Yan / Cognition (the Devin team). Argues
  context engineering is the #1 job of an agent engineer, and why naive
  multi-agent setups fragment context. https://cognition.ai/blog/dont-build-multi-agents
- **Building effective agents** — Anthropic, Dec 2024. The canonical "keep it
  simple" guide to agent patterns; the loop in this repo is the "agent" pattern
  it describes. https://www.anthropic.com/research/building-effective-agents
- **Scaling managed agents: decoupling the brain from the hands** — Anthropic
  Engineering. On separating model (brain) from harness (hands).
  https://www.anthropic.com/engineering/managed-agents

## Why long context degrades (the problem)

- **Lost in the Middle: How Language Models Use Long Contexts** — Liu et al.,
  2023. The empirical basis for "bigger window ≠ better." arXiv:2307.03172 —
  https://arxiv.org/abs/2307.03172
- **MemGPT: Towards LLMs as Operating Systems** — Packer et al., 2023. Treats the
  context window like RAM with paging to external memory — the intellectual
  ancestor of the scratchpad pattern. arXiv:2310.08560 —
  https://arxiv.org/abs/2310.08560

## The agent loop & tool use (the foundations)

- **ReAct: Synergizing Reasoning and Acting in Language Models** — Yao et al.,
  2022. The reason-then-act loop every tool-using agent descends from.
  arXiv:2210.03629 — https://arxiv.org/abs/2210.03629
- **Reflexion: Language Agents with Verbal Reinforcement Learning** — Shinn et
  al., 2023. Self-critique loops. arXiv:2303.11366 —
  https://arxiv.org/abs/2303.11366

## Provider-agnostic models & protocols (what the harness uses)

- **litellm** — one interface to 100+ LLM providers. The library behind
  `harness/llm.py`. https://github.com/BerriAI/litellm · docs:
  https://docs.litellm.ai
- **Model Context Protocol (MCP)** — the open standard for giving agents tools.
  Natural next step beyond this repo's hand-rolled tool registry.
  https://modelcontextprotocol.io · servers:
  https://github.com/modelcontextprotocol/servers
- **Ollama** — run models locally (`ollama/llama3.1` works as `--model`).
  https://ollama.com

## Frameworks (when you outgrow a hand-rolled harness)

- **Pydantic AI** — type-safe agents, closest in spirit to this repo.
  https://github.com/pydantic/pydantic-ai
- **LangGraph** — graph-structured agent control flow (heavier).
  https://github.com/langchain-ai/langgraph
- **OpenAI Agents SDK** — https://github.com/openai/openai-agents-python

## People worth following

- **Simon Willison** — https://simonwillison.net (consistently the clearest
  writing on what's actually happening in LLM tooling)
- **Eugene Yan** — https://eugeneyan.com
- **Lilian Weng — "LLM Powered Autonomous Agents"** — the survey that mapped the
  whole space. https://lilianweng.github.io/posts/2023-06-23-agent/

## This project

- **Learn Agentic AI** (newsletter) — https://learnagentic.substack.com
- The talk's whole argument is implemented in this repo:
  https://github.com/patelkanishk1995/agent-harness — read `harness/loop.py`,
  then `harness/context.py`.

---

*Sources for the two lead links were verified June 2026. arXiv IDs are stable.
The rest are living resources — expect them to keep improving.*
