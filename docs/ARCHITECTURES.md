# Architectures for keeping a long-running agent alive

This is the spine of the talk and the map of the codebase. It answers the
questions a builder actually cares about: **what are the architectural options
for a long-running agent, what decision did each one make, what does it trade
away — and how do the well-known open-source memory systems (LangChain/LangGraph,
MemGPT/Letta, Mem0) actually implement these same ideas?**

The thesis in one line: *every long-running-agent memory system is one of a few
moves on the context window — truncate, compact, externalize, or isolate — plus a
choice of where the dropped bytes go.* Once you see that, MemGPT, Mem0, LangChain,
Anthropic's multi-agent research system, even Sakana's brand-new Fugu, and our
seven policies stop looking different and start looking like points on one map.

---

## 0. The problem the architecture exists to solve

A model is stateless. Every turn, the harness re-sends a list of messages, and
that list is the agent's entire mind for the turn. The list grows every step
(tool calls, results, reasoning). Three things then break, measurably:

- **Cost** scales with the re-sent history (you pay for it every turn).
- **Latency** scales with prompt length.
- **Recall** *falls* — long contexts are read worst in the middle
  ("lost in the middle"), so more context can mean *worse* answers.

So the architecture's job is to keep a small, high-value **working set** in the
window while the run grows without bound. Every system below is a different
answer to "what goes in the working set, and where does the rest go?"

---

## 1. The architectures (the whole design space)

```
                         the window is over budget. now what?

  (1) TRUNCATE / TRIM            (2) COMPACT / SUMMARIZE
  ┌───────────────┐             ┌───────────────┐        ┌───────────────┐
  │ sys + goal    │             │ sys + goal    │        │ sys + goal    │
  │ turn  …       │  ──drop──▶   │ turn A        │ ─sum─▶ │ summary(A..C) │
  │ turn  …       │             │ turn B        │        │ recent turn   │
  │ recent        │             │ turn C        │        └───────────────┘
  └───────────────┘             │ recent        │
   keep last N, lose the rest   └───────────────┘   one LLM call; gist kept,
   no LLM call. cheapest, dumbest    detail blurred, raw gone

  (3) EXTERNALIZE / RETRIEVE                 (4) HYBRID (keep both)
  ┌───────────────┐    ┌──────────────┐     ┌───────────────┐   ┌──────────────┐
  │ sys + goal    │    │  store        │    │ sys + goal    │   │  store        │
  │ [ptr #3] ─────┼───▶│  raw turns    │    │ summary(A..C) │──▶│  raw turns    │
  │ [ptr #4]      │    │  (vector DB)  │    │ recent turn   │   │ (vector DB)  │
  │ recent        │◀───│  k-NN at      │    └───────┬───────┘   └──────┬───────┘
  └───────────────┘    │  answer time  │            └── retrieve at answer ◀┘
   window holds pointers└──────────────┘     gist in-window AND raw retrievable
   raw lives on disk, pulled back on demand   lossy summary + reversible raw
```

There is also a fifth move that doesn't compress the window at all — it spawns
*more* windows:

```
  (5) ISOLATE / SUB-AGENT
  ┌───────────────┐        ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │ lead / window │ ─spawn▶│ sub-agent A  │  │ sub-agent B  │  │ sub-agent C  │
  │ keeps only    │        │ fresh window │  │ fresh window │  │ fresh window │
  │ the summaries │◀findings│ reads, sums │  │ reads, sums  │  │ reads, sums  │
  └───────────────┘        └──────────────┘  └──────────────┘  └──────────────┘
   instead of shrinking one window, fan out to many fresh ones; keep only what
   each returns. Parallel, powerful — and the priciest move (one run per chunk).
```

**The one design decision that organizes everything:** when a byte leaves the
window, is it *gone* (truncate), *compressed* (compact), or *moved somewhere
retrievable* (externalize)? Hybrid refuses to choose and does the last two at
once. That single question predicts the cost, the failure mode, and which tasks
each architecture wins.

| Architecture | What leaves the window | Extra cost | Fails when… |
|---|---|---|---|
| **Truncate** | dropped forever | none | an old fact is needed again |
| **Compact** | compressed to a summary | 1 LLM call / compaction | the summary smoothed away the exact fact |
| **Externalize** | moved to a store | embedding + retrieval | retrieval misses, or there's no compressed reasoning chain |
| **Isolate** (sub-agent) | handed to a fresh window; only its summary returns | one sub-agent run per chunk (priciest) | the task is one focused question, not parallel breadth |
| **Hybrid** | summarized *and* stored | both | rarely — it hedges (and it's the priciest of the "cheap" tier) |

---

## 2. The abstraction: one interface, every architecture

The central engineering decision in this repo: **make all four architectures the
same shape**, so they're swappable and measurable. Every policy implements one
method (`harness/policies/`, formerly `experiments/applied/policies.py`):

```python
class Policy:
    name: str
    retrieves: bool                       # does the agent pull from the store at answer time?
    def compact(self, old, llm, store) -> tuple[list[Message], Usage]:
        """Given the over-budget 'old' turns, return the block(s) that replace
        them in the window (and any token usage). May write to `store`."""
```

That is the entire contract. The consequences:

- **Truncate** returns a one-line marker, touches neither `llm` nor `store`.
- **Recency** calls `llm` to summarize, returns one summary block.
- **Externalize** writes raw to `store`, returns a pointer marker, sets `retrieves=True`.
- **Reversible-hybrid** is *literally* Externalize + Recency composed: push raw to
  `store`, summarize, return the summary, set `retrieves=True`. ~10 lines.

Why this matters for the talk: the trade-off table above is not a claim on a
slide — it *falls out of the code*. You can open the files and see all five
architectures expressed in the same five-line shape, and the winner is two of
them glued together.

**Decisions, and why:**

- **Training-free, model-agnostic heuristics**, not learned rankers. So every arm
  runs on any model via litellm with no fine-tuning — you can clone and run it
  tonight. (Trade-off: a trained importance ranker would likely beat the heuristic.)
- **A `store` seam, not a hard-coded vector DB.** The store is an interface, so
  the externalize/hybrid arms — and the OSS systems below — drop in behind it.
- **Oracle sources** in the bench (gold articles) so we measure *compaction*, not
  retrieval quality. Search quality is a separate variable we deliberately hold fixed.
- **Simulate, then verify.** Layer 1 plants checkable facts in a synthetic
  transcript to measure mechanism cleanly; Layer 2 runs the real agent on FRAMES/
  LoCoMo for external validity.
- **Fail-soft budget.** Steps/tokens/$ caps stop the run and return the best
  answer so far rather than crashing — an architecture choice, not an afterthought.

---

## 3. How the open-source memory systems are built — and where they sit on the map

This is the part the audience came for. Each well-known system is one (or a
composition) of the four architectures, with its own opinion about *who* does the
forgetting and *how durable* the kept bytes are.

### LangChain / LangGraph — the framework default

- **Old:** `ConversationSummaryBufferMemory` = a buffer of recent turns **plus** a
  rolling summary of everything older, flushed by **token length**. That is
  exactly our **recency** arm. (Deprecated since LangChain 0.3.1; removed in 1.0.)
- **New (LangGraph):** short-term memory is the graph **state**, persisted in
  thread checkpoints; you manage it with `trim_messages` (keep the last N tokens —
  our **truncate**), message deletion, or a **summarization node** (our
  **compact**). Long-term memory goes to a LangGraph **store** (our **externalize**).
- **Architecture decision:** memory is application-layer plumbing the framework
  manages around the model. Cheap, ubiquitous — and, per our bench, the
  summary-buffer default is *Pareto-dominated by plain truncation under pressure*,
  which is the surprising headline.
- *Refs:* [migration guide](https://python.langchain.com/docs/versions/migrating_memory/conversation_summary_memory/) ·
  [LangGraph short-term memory](https://docs.langchain.com/oss/python/langchain/short-term-memory).

### MemGPT / Letta — "context as an operating system"

- **Architecture:** an OS-inspired hierarchy the *agent itself* manages via tool
  calls. Three tiers:
  - **Core memory** — labeled memory **blocks** pinned in-context, edited by the
    agent with `core_memory_append` / `core_memory_replace`. (≈ our **pin**, but
    self-editing.)
  - **Recall memory** — the full interaction history, searchable. (≈ a logged,
    retrievable transcript.)
  - **Archival memory** — explicit knowledge in an external DB. (≈ our **externalize**.)
- **The inversion:** traditional apps fetch context and stuff the prompt; Letta
  flips it — *the agent decides* what stays in core, what spills to recall, what
  gets archived. The agent is the curator.
- **Trade-off:** maximal flexibility and persistence, but the agent spends tokens
  and turns *managing its own memory* (extra tool calls), and behavior depends on
  the model being disciplined about calling them. Our harness makes the policy
  deterministic instead of agent-driven — easier to measure, less adaptive.
- *Refs:* [Letta — agent memory](https://www.letta.com/blog/agent-memory/) ·
  [MemGPT/Letta with virtual context](https://www.leoniemonigatti.com/blog/memgpt.html).

### Mem0 — extract-and-consolidate

- **Architecture:** a memory-centric pipeline in two phases, run on each
  user/assistant message pair:
  1. **Extraction** — an LLM pulls out salient *facts* (not raw text).
  2. **Update** — each fact is compared to existing memories by vector similarity,
     and an LLM decides **ADD / UPDATE / DELETE / NOOP** — deduping and resolving
     contradictions.
  - Default backend is a **vector store** (Qdrant/Chroma/Pinecone/FAISS); the
    **Mem0g** variant stores a **graph** (entities = nodes, relations = edges) for
    multi-hop queries.
- **Where it sits:** an **externalize** architecture, but it stores *distilled
  facts*, not raw turns — so it pays an LLM extraction cost up front in exchange
  for a compact, deduped, durable memory.
- **Trade-off:** great for evolving personal facts ("Maria adopted a greyhound");
  the extraction LLM adds cost and can drop nuance a raw copy would keep.
- *Refs:* [Mem0 paper (2504.19413)](https://arxiv.org/pdf/2504.19413) ·
  [vector vs graph memory](https://docs.mem0.ai/cookbooks/essentials/choosing-memory-architecture-vector-vs-graph).

### Isolation — Anthropic's multi-agent research, and Sakana's Fugu

- **Anthropic's multi-agent research system** is the canonical **isolate**
  architecture. An orchestrator-worker pattern: a lead agent analyzes the query,
  plans, and spawns **subagents** — each with its **own fresh context window**, a
  self-contained task, and no knowledge of the others. They explore in parallel
  and return only their **compressed findings** to the lead. Opus orchestrator +
  Sonnet subagents beat a single Opus 4 by **~90%**, which they attribute directly
  to spreading reasoning across multiple independent windows. So "subagent" isn't
  a routing trick — it's a *context* architecture: don't shrink one window, spin
  up many and keep only the summaries.
- **Our `subagent` arm models exactly this** (one fresh-window summary per evicted
  source). The honest result on our bench: on a single, focused FRAMES question it
  is **Pareto-dominated** — ~5x the token cost of `importance` for no accuracy
  gain. That isn't a contradiction of Anthropic; it's the nuance: **isolation pays
  off when the work is broad and parallelizable** (open-ended research across many
  independent directions) and is **a cost trap when the task is one narrow
  question**. Same architecture, opposite verdict — *task shape* decides. (That
  contrast is one of the most interesting things to say out loud.)
- **Sakana Fugu** (GA **June 22, 2026**) is the bleeding edge of the
  isolate/orchestrate family — a multi-agent system *sold as a model*. A trained
  7B "conductor" routes a task across a **swappable pool of frontier models**
  (GPT-5.5, Claude Opus, Gemini 3.1 Pro) behind one OpenAI-compatible API. The
  precise distinction for a technical room: Anthropic and our `subagent` isolate
  across **context windows** (a forgetting strategy); **Fugu orchestrates across
  models** (routing + combination). Both are "multi-agent," different axis — so we
  **cite Fugu as the frontier of this architecture, not as a compaction arm we
  bench.** (It's also a perfect "this shipped the day before the talk" hook.)
- *Refs:* [Anthropic multi-agent research](https://www.anthropic.com/engineering/multi-agent-research-system) ·
  [Sakana Fugu](https://sakana.ai/fugu/) ·
  [Fugu launch (MarkTechPost)](https://www.marktechpost.com/2026/06/22/sakana-ai-launches-sakana-fugu-an-orchestration-model-that-routes-tasks-across-a-swappable-pool-of-frontier-llms/).

### The store backends — Chroma / FAISS / sqlite-vec + sentence-transformers

- These are the **substrate** under "externalize" everywhere above. A vector
  store holds embeddings and does approximate k-NN; an open-source embedder
  (`sentence-transformers`, e.g. all-MiniLM) turns text into vectors **offline,
  no API key**. Our `store` seam targets this so the externalize/hybrid arms — and
  the Mem0/Letta adapters — run locally.

### The map, on one line each

| System | Architecture(s) | Who forgets | What's kept |
|---|---|---|---|
| **trim_messages** (LangGraph) | truncate | framework | last N tokens |
| **ConversationSummaryBufferMemory** | compact (recency) | framework | summary + recent |
| **Mem0** | externalize | an extractor LLM | deduped facts (vector/graph) |
| **MemGPT / Letta** | pin + externalize, self-managed | the agent | core blocks + archival DB |
| **Anthropic multi-agent research** | isolate (sub-agents) | the orchestrator | each sub-agent's compressed findings |
| **Sakana Fugu** | isolate + model-routing | a trained 7B conductor | findings combined across frontier models |
| **our reversible-hybrid** | compact + externalize | the harness (measured) | summary in-window **and** raw retrievable |

---

## 4. Why wrap them behind our `Policy` interface

Because then they're not rivals to read about — they're **arms you can bench
head-to-head.** Each adapter (`harness/memory/adapters/`) implements the same
`compact(old, llm, store)` (or wraps the system's own store), so the runner swaps
it in by name like any other policy:

- `langchain_summary` — wraps `ConversationSummaryBufferMemory` (or the LangGraph
  summarization node) → a faithful "framework default" baseline.
- `mem0` — routes the old turns through Mem0's extract→update, retrieves at answer.
- `letta` — uses Letta's archival memory as the store (and optionally core blocks).
- `chroma_store` — a `store` backend (Chroma + sentence-transformers) the
  externalize/hybrid arms run on, fully offline.

The payoff line for the talk: *"Here's how the famous memory systems are built —
and here's what happens when you make them all the same shape and measure them.
The 15-line hand-rolled arms hold their own; the framework's shipped default
loses to truncation; and the architecture that wins is the one that refuses to
pick — it keeps both the summary and the raw."*

---

## 5. Where to read it in the repo

```
harness/
  loop.py                 the ~40-line agent loop (the one maybe_compact call)
  context.py              the ContextManager: pin · truncate · compact
  compare.py              `python -m harness.compare "question"` — the side-by-side demo
  policies/               ← the five architectures, one file each (the tour)
    base.py                 the Policy protocol + summarize() primitive
    store.py                the store seam (offline default; Chroma adapter swaps in)
    truncate.py recency.py importance.py semantic.py externalize.py subagent.py hybrid.py
    adapters/               langchain_summary · mem0 · letta · chroma_store (import-guarded)
experiments/              the bench that produced the numbers (bench/ + applied/ + runs/)
docs/ARCHITECTURES.md     this file · docs/POLICIES.md the per-policy tour
```

Start at `loop.py`, then this document, then open the policy files in
`harness/policies/` side by side (or just run `python -m harness.compare`). That's the talk.
