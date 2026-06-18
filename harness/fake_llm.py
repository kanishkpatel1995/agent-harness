"""A deterministic, offline 'model'.

This is not an LLM. It's a scripted stand-in with the exact same interface as
LLMClient, so the whole harness — loop, tools, context, compaction, budget,
trace — runs end to end with no API key and no network.

Why it exists:
  - Reliable live demos (conference wifi is a hostile environment).
  - Fast, free tests in CI.
  - You can read it to see precisely what sequence of tool calls the harness
    is exercising, with no model nondeterminism in the way.

It plays a fixed research script (plan -> search -> fetch/note loop -> read ->
finish) and reacts to the real fixture URLs returned by web_search. It also
answers the ContextManager's summarize requests so compaction works offline.
"""

from __future__ import annotations

import re

from .context import approx_tokens


class FakeLLM:
    model = "fake"

    def __init__(self, max_fetches: int = 5):
        self.max_fetches = max_fetches
        self.searches = 0
        self.fetches = 0
        self.notes = 0
        self.plan_done = False
        self.read_done = False
        self._last_action = None

    # --- interface parity with LLMClient -----------------------------------
    def count_tokens(self, messages: list) -> int:
        return sum(approx_tokens(str(m)) for m in messages)

    def complete(self, messages: list, tools: list | None = None):
        from .llm import LLMResponse

        # Compaction asks us to summarize. Detect and answer it directly.
        if messages and "SUMMARIZE_REQUEST" in (messages[0].get("content") or ""):
            transcript = messages[-1].get("content", "")
            content = self._summarize(transcript)
            return LLMResponse(content=content, tool_calls=[], usage=self._usage(messages, content))

        goal = self._goal(messages)
        name, args, content = self._next_action(goal, messages)

        if name is None:  # finish path returns content as a plain message
            return LLMResponse(content=content, tool_calls=[], usage=self._usage(messages, content))

        call = {"id": f"call_{name}_{self._counter()}", "name": name, "arguments": args}
        return LLMResponse(content=content, tool_calls=[call], usage=self._usage(messages, str(args)))

    # --- the script ---------------------------------------------------------
    def _next_action(self, goal, messages):
        if not self.plan_done:
            self.plan_done = True
            self._last_action = "save_note"
            return ("save_note", {"text": f"Plan: research '{goal}'. Search, read top sources, "
                                          "save findings, then synthesize.", "tag": "plan"}, None)

        if self.searches == 0:
            self.searches += 1
            self._last_action = "web_search"
            return ("web_search", {"query": goal, "k": 5}, "Searching for sources.")

        # Interleave fetch -> note so every page read becomes durable memory.
        if self._last_action in ("web_search", "save_note") and self.fetches < self.max_fetches:
            url = self._next_url(messages)
            if url:
                self.fetches += 1
                self._last_action = "fetch_url"
                return ("fetch_url", {"url": url}, f"Reading source {self.fetches}.")

        if self._last_action == "fetch_url":
            self.notes += 1
            self._last_action = "save_note"
            return ("save_note",
                    {"text": f"Finding {self.notes}: source {self.notes} supports the working "
                             f"thesis on '{goal}'; noting key claim and its URL for the report.",
                     "tag": "finding"}, None)

        if not self.read_done:
            self.read_done = True
            self._last_action = "read_notes"
            return ("read_notes", {}, "Reviewing everything saved before writing.")

        # Done: emit the final report via the finish tool.
        self._last_action = "finish"
        report = self._report(goal)
        return ("finish", {"report": report}, None)

    # --- url extraction -----------------------------------------------------
    def _next_url(self, messages):
        urls = []
        for m in messages:
            if m.get("role") == "tool":
                urls += re.findall(r"https?://\S+", m.get("content") or "")
        # de-dup, preserve order
        seen, ordered = set(), []
        for u in urls:
            u = u.rstrip(".,)")
            if u not in seen:
                seen.add(u)
                ordered.append(u)
        idx = self.fetches
        return ordered[idx] if idx < len(ordered) else (ordered[0] if ordered else None)

    # --- content generators -------------------------------------------------
    def _summarize(self, transcript: str) -> str:
        n = transcript.count("tool result")
        return (
            "- Goal restated and plan recorded.\n"
            f"- Searched and read {self.fetches} sources; {self.notes} findings saved to scratchpad.\n"
            "- Working thesis is holding; concrete claims + URLs are in notes (read_notes).\n"
            f"- {n} raw tool outputs compacted away to save context; nothing lost (it's on disk)."
        )

    def _report(self, goal: str) -> str:
        return (
            f"# Research report: {goal}\n\n"
            f"## Summary\nBased on {self.fetches} sources (see scratchpad), here is the synthesis.\n\n"
            "## Key findings\n"
            "1. The dominant factor is approach, not tooling.\n"
            "2. Trade-offs around cost, latency, and reliability recur across sources.\n"
            "3. A few claims remain contested and warrant follow-up.\n\n"
            "## Method note\nThis run kept a small context window via compaction and an "
            "external scratchpad, so research length was not bounded by the model's window."
        )

    # --- bookkeeping --------------------------------------------------------
    def _goal(self, messages):
        for m in messages:
            c = m.get("content") or ""
            if c.startswith("YOUR GOAL"):
                return c.split("\n", 1)[-1].strip()
        return "the topic"

    def _counter(self):
        return self.searches + self.fetches + self.notes

    def _usage(self, messages, output):
        return {
            "prompt_tokens": sum(approx_tokens(str(m)) for m in messages),
            "completion_tokens": approx_tokens(str(output)),
        }
