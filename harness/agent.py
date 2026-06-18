"""DeepResearchAgent: wires the pieces together.

This file is just assembly. The interesting code is in the modules it imports.
Read order for the talk: loop.py -> context.py -> memory.py -> budget.py.
"""

from __future__ import annotations

from pathlib import Path

from .budget import Budget
from .context import ContextManager
from .loop import run_agent_safe
from .memory import Scratchpad
from .tools import ToolRegistry
from .trace import Trace

SYSTEM_PROMPT = """\
You are a careful research agent. You work in steps, using tools.

Operating rules:
- Search first, then read the most promising sources with fetch_url.
- After reading anything useful, immediately save_note it. The scratchpad is
  your long-term memory; the conversation will be compacted and you must not
  rely on remembering raw page text.
- Before writing the final report, call read_notes to gather your findings.
- When done, call finish with a complete markdown report.
- Be concrete. Prefer specific claims, numbers, and source URLs.
"""


def build_agent(
    goal: str,
    llm,
    *,
    notes_path: str | Path = "run/notes.md",
    max_context_tokens: int = 3000,
    max_steps: int = 30,
    max_usd: float = 1.00,
    max_tokens: int = 200_000,
    quiet: bool | None = None,
):
    """Construct every component and return a zero-arg callable that runs it."""
    scratchpad = Scratchpad(notes_path)
    tools = ToolRegistry(scratchpad)
    context = ContextManager(
        system_prompt=SYSTEM_PROMPT,
        goal=goal,
        max_context_tokens=max_context_tokens,
    )
    context.set_token_counter(llm.count_tokens)
    context.add_user(f"Research this and write a report: {goal}")

    budget = Budget(max_steps=max_steps, max_usd=max_usd, max_tokens=max_tokens)
    trace = Trace(quiet=quiet)

    def run() -> str:
        return run_agent_safe(llm, context, tools, budget, trace, max_steps=max_steps)

    run.context = context
    run.budget = budget
    run.scratchpad = scratchpad
    return run
