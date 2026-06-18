"""Provider-agnostic LLM client.

One interface, any model. litellm normalizes OpenAI / Anthropic / Gemini / local
(Ollama, LM Studio) behind a single completion() call, so the harness never
hard-codes a provider. Set HARNESS_MODEL to switch brains:

    HARNESS_MODEL=gpt-4o-mini
    HARNESS_MODEL=claude-3-5-sonnet-20241022
    HARNESS_MODEL=ollama/llama3.1     (local, free, offline)

litellm is imported lazily so the FakeLLM path runs with zero dependencies.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass


@dataclass
class LLMResponse:
    content: str | None
    tool_calls: list  # [{"id", "name", "arguments": dict}]
    usage: dict       # {"prompt_tokens", "completion_tokens"}


class LLMClient:
    def __init__(self, model: str | None = None, temperature: float = 0.2):
        self.model = model or os.environ.get("HARNESS_MODEL", "gpt-4o-mini")
        self.temperature = temperature

    def complete(self, messages: list, tools: list | None = None) -> LLMResponse:
        import litellm  # lazy: only needed when actually calling a real model

        kwargs = {"model": self.model, "messages": messages, "temperature": self.temperature}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        resp = litellm.completion(**kwargs)
        msg = resp.choices[0].message

        tool_calls = []
        for tc in (getattr(msg, "tool_calls", None) or []):
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            tool_calls.append({"id": tc.id, "name": tc.function.name, "arguments": args})

        usage = {
            "prompt_tokens": getattr(resp.usage, "prompt_tokens", 0),
            "completion_tokens": getattr(resp.usage, "completion_tokens", 0),
        }
        return LLMResponse(content=msg.content, tool_calls=tool_calls, usage=usage)

    def count_tokens(self, messages: list) -> int:
        try:
            import litellm

            return litellm.token_counter(model=self.model, messages=messages)
        except Exception:
            from .context import approx_tokens

            return sum(approx_tokens(str(m)) for m in messages)
