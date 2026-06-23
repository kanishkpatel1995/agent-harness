# The seven policies — one interface, seven ways to forget

Every policy lives in its own file under [`harness/policies/`](../harness/policies/)
and implements the same contract:

```python
compact(old, llm, store) -> (replacement_block, usage)   # + .architecture, .retrieves
```

Open the seven files side by side — the trade-off table below *falls out of the
code*. See [`ARCHITECTURES.md`](ARCHITECTURES.md) for the architecture map and the
open-source memory systems (LangChain, MemGPT/Letta, Mem0, Sakana Fugu) placed on it.

## See it, don't read it

```bash
python -m harness.compare "quantum networking startups"
```

Runs one question through all seven policies offline (no API key) and prints a
side-by-side: LLM calls, resulting window size, whether it retrieves, and whether
a planted fact survives. The result that sells the whole talk:

```
  policy             architecture  llm  ctx tok  retr  fact?
  ------------------------------------------------------------
  truncate           truncate        0       47     -   ✗ lost
  recency            compact         1       70     -   ✗ lost
  importance         compact         1      138     -   ✓ kept
  semantic           compact         2       98     -   ✗ lost
  externalize        externalize     0       56   yes   ✓ kept
  subagent           isolate         6      225     -   ✗ lost     ← priciest, still loses
  reversible_hybrid  hybrid          1       74   yes   ✓ kept     ← cheap-ish, recovers
```

truncate drops the fact, summaries blur it, the sub-agent fan-out is the most
expensive and *still* loses it on a single focused question, and the hybrid is the
cheap one that recovers it. Add `--verbose` to see what each window kept.

## The seven, at a glance

| policy | architecture | the decision it makes | trade-off | result |
|---|---|---|---|---|
| **truncate** | truncate | keep recent, drop the rest; no LLM | cheapest, but old facts vanish | 0.37 · the floor (= LangGraph `trim_messages`) |
| **recency** | compact | one summary of all old turns | the shipped default; blurs the exact fact | 0.37 · dominated by truncate under pressure |
| **importance** | compact | keep top-signal turns verbatim, summarize rest | keeps exact facts; heuristic + more tokens | 0.50 · accuracy leader on factual |
| **semantic** | compact | cluster by topic, summarize each | preserves structure; one call per cluster | 0.57 · factual ceiling; loses scattered facts |
| **externalize** | externalize | push raw to store, retrieve at answer | keeps literal facts; needs retrieval to hit | 0.40 · winner on memory (LoCoMo) |
| **subagent** | isolate | each source → fresh window → keep its summary | Anthropic's pattern; priciest; cost trap on single tasks | 0.50 · Pareto-dominated here |
| **reversible_hybrid** | hybrid | summary in window **and** raw in store | hedges both ways; priciest of the cheap tier | top group in *every* cell — the only arm that is |

## How the OSS systems map onto these

- **LangGraph `trim_messages`** → `truncate`
- **LangChain `ConversationSummaryBufferMemory`** → `recency`
- **Mem0** (extract→update facts) → `externalize`, with an LLM extractor in front
- **MemGPT / Letta** (core blocks + archival DB) → pin + `externalize`, agent-managed
- **Anthropic multi-agent research** → `subagent` / `isolate`
- **Sakana Fugu** → the `isolate`/orchestrate frontier (routes across models — cited, not benched)

Wrapping these behind the same interface lives in
[`harness/policies/adapters/`](../harness/policies/adapters/) (import-guarded, so the
core stays dependency-free).
