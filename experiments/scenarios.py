"""Unit 1, expanded — run several scenarios and emit per-step series as JSON.

Scenarios that make the 'window is a budget' lesson visceral:

  - compaction ON vs OFF (same window): the single most important graph. OFF
    climbs forever (and on a real API eventually dies); ON is a bounded sawtooth.
  - three window budgets (1.2k / 2.5k / 5k): 'a bigger window raises the ceiling,
    it does not bend the curve' — billed still climbs linearly, just steeper.

Run:  python experiments/scenarios.py
It prints JSON (consumed to draw charts) and a one-line summary per scenario.
Offline, deterministic, no key.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harness.budget import Budget
from harness.context import ContextManager
from harness.fake_llm import FakeLLM
from harness.loop import run_agent_safe
from harness.memory import Scratchpad
from harness.tools import ToolRegistry
from harness.agent import SYSTEM_PROMPT
from experiments.token_growth import RecordingTrace


def run_scenario(goal, *, window, compact_at=0.75, max_fetches=8):
    scratch = Scratchpad("run/notes.md")
    tools = ToolRegistry(scratch)
    ctx = ContextManager(
        system_prompt=SYSTEM_PROMPT,
        goal=goal,
        max_context_tokens=window,
        compact_at=compact_at,
    )
    llm = FakeLLM(max_fetches=max_fetches)
    ctx.set_token_counter(llm.count_tokens)
    ctx.add_user(f"Research this and write a report: {goal}")
    # Generous caps so the budget kill-switch doesn't end the run early; here we
    # study context growth, not the cap (that's Unit 5/the budget move).
    budget = Budget(max_steps=120, max_usd=1000.0, max_tokens=10_000_000)
    trace = RecordingTrace()
    run_agent_safe(llm, ctx, tools, budget, trace, max_steps=120)
    return trace.rows, budget.total_tokens


def series(rows):
    return [
        {"step": r["step"], "w": r["window_tokens"], "b": r["billed_tokens"], "c": r["compacted"]}
        for r in rows
    ]


def main():
    os.environ.setdefault("HARNESS_OFFLINE", "1")
    goal = "context engineering for long-running agents"

    specs = {
        "compaction_on": dict(window=1500, compact_at=0.75, max_fetches=10),
        "compaction_off": dict(window=1500, compact_at=99.0, max_fetches=10),
        "win_1200": dict(window=1200, compact_at=0.75, max_fetches=10),
        "win_2500": dict(window=2500, compact_at=0.75, max_fetches=10),
        "win_5000": dict(window=5000, compact_at=0.75, max_fetches=10),
    }

    out = {}
    print("scenario          steps   final_window   total_billed")
    print("-" * 58)
    for name, spec in specs.items():
        rows, billed = run_scenario(goal, **spec)
        out[name] = series(rows)
        fw = rows[-1]["window_tokens"]
        print(f"{name:<16} {len(rows):>5} {fw:>13,} {billed:>14,}")

    Path(__file__).parent.joinpath("scenarios.json").write_text(json.dumps(out, indent=2))
    print("\n--- JSON (for charts) ---")
    print(json.dumps(out))


if __name__ == "__main__":
    main()
