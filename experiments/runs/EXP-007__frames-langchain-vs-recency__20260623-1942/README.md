# EXP-007 — frames-langchain-vs-recency

**Hypothesis:** LangChain's ConversationSummaryBufferMemory (the framework's shipped default) does not beat our 15-line `recency` on FRAMES: both are rolling-summary compaction, so they land in the same accuracy band; the framework adds a dependency, not accuracy.

**Assumptions:**
- Both arms summarize on the same 8B model (LangChain via an OpenAI-compatible NIM endpoint).
- Oracle articles + budget 1500 + chunked reads force many compaction events per question.
- The 70b judge grades both arms identically.
- LangChain summarization tokens are captured via get_openai_callback for a fair cost axis.

Run `20260623-1942` · git `a790e3a` · model `meta/llama-3.1-8b-instruct` · judge `meta/llama-3.3-70b-instruct`

## Results (n=20, 8B, judged, high pressure, seed=7)

| policy | accuracy | mean tokens | n |
|---|---|---|---|
| recency (our 15-line) | 0.45 (9/20) | 11,031 | 20 |
| langchain_summary | 0.35 (7/20) | 13,412 | 20 |

**Did the hypothesis hold?** Yes, and then some. Our 15-line `recency` matched and beat LangChain's ConversationSummaryBufferMemory: higher accuracy (0.45 vs 0.35) at lower token cost (11.0k vs 13.4k mean). The framework's shipped default bought a dependency, not accuracy, on this task. Both are rolling-summary compaction on the same 8B model (LangChain reaches it via ChatOpenAI -> NIM), so the comparison is apples to apples; LangChain's summarization tokens are metered via `get_openai_callback`, so the cost axis is fair.

**Strongest threat to validity.** n=20 at one seed: the 95% bootstrap CI on these proportions is ~±0.21, so the +0.10 gap is directional, not significant. The defensible claim is "the framework default does not beat the hand-rolled policy, and costs more tokens", not "recency is significantly better".

**Reproduce:** `python experiments/applied/launch_exp007_langchain.py`
