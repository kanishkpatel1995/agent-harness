#!/usr/bin/env python3
"""The stage demo, as a script. No API key, no network.

    python examples/run_offline_demo.py

Watch the context bar grow, cross the threshold, and snap back when compaction
fires — while the agent keeps making progress. Then open run/notes.md to see the
agent's externalized memory.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("HARNESS_OFFLINE", "1")

from harness import FakeLLM, build_agent

GOAL = "context engineering for long-running LLM agents"


def main():
    print(f"GOAL: {GOAL}\n(FakeLLM — deterministic, offline)\n")
    run = build_agent(GOAL, FakeLLM(max_fetches=5), max_context_tokens=2200)
    answer = run()
    print("\n\n===== FINAL REPORT =====\n")
    print(answer)
    print(f"\nNotes externalized to: {run.scratchpad.path} ({run.scratchpad.count()} notes)")
    print(run.budget.summary())


if __name__ == "__main__":
    main()
