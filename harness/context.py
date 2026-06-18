"""The ContextManager: the part the talk is actually about.

The model is stateless. Every single turn, the harness hands it a fresh list
of messages and that list *is* the agent's entire mind for that turn. If the
list is wrong, the agent is wrong. If the list grows without bound, the run
dies (cost, latency, then a hard context-limit error).

So the job of this class is to decide, on every turn, what the model gets to
see. It does four things:

  1. PIN the things that must never be dropped (system prompt + the goal).
  2. COUNT tokens so we know how full the window is.
  3. TRUNCATE individual tool outputs that are too big to be worth their space.
  4. COMPACT: when the window crosses a threshold, summarize the old middle of
     the conversation into one short note and throw the raw turns away.

Everything here is plain dicts in OpenAI message format so it works across
providers via litellm.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

# Rough fallback token counter (~4 chars/token) used when no real tokenizer is
# available. The ContextManager prefers the LLM client's count_tokens().
def approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _message_tokens(msg: dict) -> int:
    total = approx_tokens(msg.get("content") or "")
    for tc in msg.get("tool_calls", []) or []:
        total += approx_tokens(str(tc))
    return total


@dataclass
class ContextManager:
    system_prompt: str
    goal: str
    max_context_tokens: int = 8000
    # Compact once we cross this fraction of the budget.
    compact_at: float = 0.75
    # Keep this many of the most recent messages verbatim during compaction.
    keep_recent: int = 6
    # Truncate any single tool result longer than this many chars.
    max_tool_chars: int = 2000

    _pinned: list = field(default_factory=list)
    _body: list = field(default_factory=list)
    _token_counter: Callable[[list], int] | None = None

    def __post_init__(self):
        # The two pinned messages. These are never summarized or dropped.
        self._pinned = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"YOUR GOAL (never lose sight of this):\n{self.goal}"},
        ]

    # --- the list the model sees -------------------------------------------
    def messages(self) -> list:
        return self._pinned + self._body

    # --- appends ------------------------------------------------------------
    def add_assistant(self, content, tool_calls=None):
        msg = {"role": "assistant", "content": content or ""}
        if tool_calls:
            msg["tool_calls"] = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {"name": tc["name"], "arguments": _dumps(tc["arguments"])},
                }
                for tc in tool_calls
            ]
        self._body.append(msg)

    def add_tool_result(self, tool_call_id: str, content: str):
        content = _truncate(content, self.max_tool_chars)
        self._body.append({"role": "tool", "tool_call_id": tool_call_id, "content": content})

    def add_user(self, content: str):
        self._body.append({"role": "user", "content": content})

    # --- token accounting ---------------------------------------------------
    def set_token_counter(self, fn: Callable[[list], int]):
        self._token_counter = fn

    def token_count(self) -> int:
        msgs = self.messages()
        if self._token_counter:
            try:
                return self._token_counter(msgs)
            except Exception:
                pass
        return sum(_message_tokens(m) for m in msgs)

    def composition(self) -> dict:
        """Token breakdown by segment, for the trace/visualization."""
        pinned = sum(_message_tokens(m) for m in self._pinned)
        body = sum(_message_tokens(m) for m in self._body)
        return {
            "pinned": pinned,
            "body": body,
            "total": pinned + body,
            "budget": self.max_context_tokens,
            "messages": len(self._body),
        }

    # --- the important part: compaction ------------------------------------
    def maybe_compact(self, llm) -> str | None:
        """If the window is too full, summarize the old middle and drop it.

        Returns the summary text if compaction happened, else None.
        """
        threshold = int(self.max_context_tokens * self.compact_at)
        if self.token_count() <= threshold:
            return None
        if len(self._body) <= self.keep_recent + 1:
            return None  # nothing safe to compact yet

        split = self._safe_split_index(len(self._body) - self.keep_recent)
        if split <= 0:
            return None

        old, recent = self._body[:split], self._body[split:]
        summary = self._summarize(llm, old)

        self._body = [
            {
                "role": "system",
                "content": (
                    "[COMPACTED MEMORY] Earlier steps were summarized to save "
                    "context. Details live in the scratchpad (use read_notes). "
                    "Summary:\n" + summary
                ),
            }
        ] + recent
        return summary

    def _safe_split_index(self, proposed: int) -> int:
        """Don't split an assistant tool-call away from its tool results.

        A 'tool' message only makes sense right after the assistant message
        that requested it, so we never let the kept tail start on a 'tool'.
        """
        idx = max(0, min(proposed, len(self._body)))
        while idx < len(self._body) and self._body[idx].get("role") == "tool":
            idx += 1
        return idx

    def _summarize(self, llm, messages: list) -> str:
        transcript = _render_for_summary(messages)
        prompt = [
            {
                "role": "system",
                "content": (
                    "SUMMARIZE_REQUEST. You compress an agent's working transcript. "
                    "Produce a dense bullet summary of what was learned, decided, and "
                    "still open. Keep concrete facts, URLs, and numbers. Drop chatter. "
                    "Max ~180 words."
                ),
            },
            {"role": "user", "content": transcript},
        ]
        try:
            resp = llm.complete(prompt, tools=None)
            return (resp.content or "").strip() or _fallback_summary(messages)
        except Exception:
            return _fallback_summary(messages)

    def last_assistant_text(self) -> str:
        for m in reversed(self._body):
            if m.get("role") == "assistant" and m.get("content"):
                return m["content"]
        return ""


# --- helpers ---------------------------------------------------------------
def _dumps(obj) -> str:
    import json

    return json.dumps(obj, ensure_ascii=False)


def _truncate(text: str, limit: int) -> str:
    if text is None:
        return ""
    if len(text) <= limit:
        return text
    head = text[: limit - 200]
    return f"{head}\n...[truncated {len(text) - limit + 200} chars — full version saved to scratchpad]"


def _render_for_summary(messages: list) -> str:
    lines = []
    for m in messages:
        role = m.get("role")
        if role == "assistant" and m.get("tool_calls"):
            names = ", ".join(tc["function"]["name"] for tc in m["tool_calls"])
            lines.append(f"[assistant called: {names}]")
            if m.get("content"):
                lines.append(f"assistant: {m['content']}")
        elif role == "tool":
            lines.append(f"[tool result]: {m.get('content', '')}")
        elif m.get("content"):
            lines.append(f"{role}: {m['content']}")
    return "\n".join(lines)


def _fallback_summary(messages: list) -> str:
    tool_results = [m.get("content", "") for m in messages if m.get("role") == "tool"]
    joined = " ".join(tool_results)[:600]
    return f"({len(messages)} earlier messages compacted) Key tool output: {joined}"
