"""Tests for the ContextManager — the part the talk is about."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness.context import ContextManager


class StubLLM:
    model = "fake"

    def complete(self, messages, tools=None):
        from harness.llm import LLMResponse

        return LLMResponse(content="SUMMARY: compacted.", tool_calls=[], usage={})


def _fill(cm, n, size=400):
    for i in range(n):
        cm.add_assistant(None, tool_calls=[{"id": f"c{i}", "name": "fetch_url", "arguments": {"url": "u"}}])
        cm.add_tool_result(f"c{i}", "x" * size)


def test_pinned_always_present():
    cm = ContextManager("SYS", "GOAL", max_context_tokens=1000)
    assert cm.messages()[0]["role"] == "system"
    assert "GOAL" in cm.messages()[1]["content"]


def test_tool_results_are_truncated():
    cm = ContextManager("SYS", "GOAL", max_tool_chars=100)
    cm.add_assistant(None, tool_calls=[{"id": "c1", "name": "fetch_url", "arguments": {}}])
    cm.add_tool_result("c1", "y" * 5000)
    body = cm.messages()[-1]["content"]
    assert len(body) < 5000
    assert "truncated" in body


def test_compaction_shrinks_window_and_keeps_pins():
    cm = ContextManager("SYS", "GOAL", max_context_tokens=1200, compact_at=0.6, keep_recent=2)
    _fill(cm, 12)
    before = cm.token_count()
    summary = cm.maybe_compact(StubLLM())
    after = cm.token_count()
    assert summary is not None
    assert after < before
    # pins survive
    assert cm.messages()[0]["content"] == "SYS"
    assert "GOAL" in cm.messages()[1]["content"]
    # a compacted-memory marker is present
    assert any("COMPACTED MEMORY" in (m.get("content") or "") for m in cm.messages())


def test_no_compaction_when_small():
    cm = ContextManager("SYS", "GOAL", max_context_tokens=100000)
    _fill(cm, 3)
    assert cm.maybe_compact(StubLLM()) is None


def test_safe_split_never_starts_tail_on_tool():
    cm = ContextManager("SYS", "GOAL", max_context_tokens=600, compact_at=0.5, keep_recent=1)
    _fill(cm, 10)
    cm.maybe_compact(StubLLM())
    # first body message after pins must not be a dangling tool result
    first_body = cm.messages()[len(cm._pinned)]
    assert first_body["role"] != "tool"
