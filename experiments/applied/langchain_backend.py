"""LangChain ConversationSummaryBufferMemory as a benchable FRAMES compact arm — on NIM.

Wraps the harness `LangChainSummary` with a NIM-backed `ChatOpenAI` (NIM is
OpenAI-compatible, so the framework's shipped default runs on the free tier with no
OpenAI spend). The head-to-head this enables: does LangChain's summary-buffer beat our
15-line `recency`? Same FRAMES questions, same 8B summarizer model, same 70B judge.

Two integration details, both real lessons:
  - `tiktoken_model_name` pins token counting to a known encoding. LangChain counts
    buffer tokens with tiktoken, which doesn't recognise "meta/llama-3.1-8b-instruct"
    and raises; pinning it to gpt-3.5-turbo fixes counting while calls still go to NIM.
  - the buffer is STATEFUL across compaction events within a question, so `reset()`
    rebuilds it per question; the runner calls reset() between questions.

Summarization token usage is captured via `get_openai_callback`, so the cost axis is
comparable to `recency` (whose summarizer tokens we meter directly).
"""

from __future__ import annotations

from experiments.nim import _load_env_key
from experiments.bench.logsetup import get

log = get("langchain")
NIM_BASE = "https://integrate.api.nvidia.com/v1"
ZERO = {"prompt_tokens": 0, "completion_tokens": 0}


class LangChainSummaryPolicy:
    name = "langchain_summary"
    architecture = "compact"
    retrieves = False

    def __init__(self, model: str = "meta/llama-3.1-8b-instruct", max_token_limit: int = 256):
        from langchain_openai import ChatOpenAI
        self._lc = ChatOpenAI(base_url=NIM_BASE, api_key=_load_env_key(), model=model,
                              temperature=0, max_tokens=256, tiktoken_model_name="gpt-3.5-turbo")
        self._max = max_token_limit
        self.reset()
        log.info(f"LangChain summary-buffer on NIM ({model}); max_token_limit={max_token_limit}")

    def reset(self):
        # fresh memory per question: the buffer must not bleed context across questions.
        from harness.policies.adapters.langchain_summary import LangChainSummary
        self._pol = LangChainSummary(lc_llm=self._lc, max_token_limit=self._max)

    def compact(self, old, llm, store):
        try:
            from langchain_community.callbacks import get_openai_callback
            with get_openai_callback() as cb:
                block, _ = self._pol.compact(old, llm, store)
            return block, {"prompt_tokens": cb.prompt_tokens, "completion_tokens": cb.completion_tokens}
        except Exception:
            block, _ = self._pol.compact(old, llm, store)
            return block, dict(ZERO)
