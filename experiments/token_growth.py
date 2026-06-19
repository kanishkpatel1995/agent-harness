"""Unit 1 experiment — the window is a budget, not a backpack.

Runs one offline agent and records, per step, two numbers that tell the whole
economic story of a long-running agent:

  - window_tokens   : how big the context window is RIGHT NOW (what compaction
                      controls). Should stay roughly flat — a sawtooth.
  - billed_tokens   : cumulative prompt+completion tokens you have PAID FOR so
                      far. Should climb roughly linearly, because a stateless
                      model means you re-send the window every single turn.

The gap between a flat line and a climbing line is the entire argument for
context engineering. Run it:

    python experiments/token_growth.py

It writes experiments/token_growth.csv and prints an ASCII chart. No API key,
no network (FakeLLM).
"""

from __future__ import annotations

import csv
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
from harness.trace import Trace
from harness.agent import SYSTEM_PROMPT


class RecordingTrace(Trace):
    """A Trace that also records per-step numbers. Subclassing (not editing the
    repo) keeps the experiment self-contained — and proves the point from Unit 0
    that the harness is just composable pieces."""

    def __init__(self):
        super().__init__(quiet=True)  # stay silent; we print our own chart
        self.rows = []

    def step_start(self, step, context, budget):
        comp = context.composition()
        self.rows.append(
            {
                "step": step,
                "window_tokens": comp["total"],
                "pinned_tokens": comp["pinned"],
                "body_tokens": comp["body"],
                "messages": comp["messages"],
                # billed-so-far ENTERING this step (record_usage for this step
                # hasn't run yet) — monotonic, which is all we need.
                "billed_tokens": budget.total_tokens,
                "compacted": False,
            }
        )

    def compaction(self, summary, context):
        if self.rows:
            self.rows[-1]["compacted"] = True


def build_recorded_agent(goal: str, max_context_tokens: int = 1200):
    """Same assembly as harness.build_agent, but with our RecordingTrace.
    Reading this is itself Unit 0: the harness is five pieces wired together."""
    scratchpad = Scratchpad("run/notes.md")
    tools = ToolRegistry(scratchpad)
    context = ContextManager(
        system_prompt=SYSTEM_PROMPT, goal=goal, max_context_tokens=max_context_tokens
    )
    llm = FakeLLM()
    context.set_token_counter(llm.count_tokens)
    context.add_user(f"Research this and write a report: {goal}")
    budget = Budget(max_steps=40, max_usd=1.00, max_tokens=200_000)
    trace = RecordingTrace()

    def run():
        return run_agent_safe(llm, context, tools, budget, trace, max_steps=40)

    run.trace = trace
    run.budget = budget
    return run


def ascii_chart(rows):
    """Two side-by-side bars per step: window (flat-ish) vs billed (climbing)."""
    max_window = max(r["window_tokens"] for r in rows) or 1
    max_billed = max(r["billed_tokens"] for r in rows) or 1
    W = 28
    print()
    print(f"{'step':>4} {'window (live)':<32} {'billed (cumulative)':<40}")
    print("-" * 84)
    for r in rows:
        wbar = "█" * max(1, int(W * r["window_tokens"] / max_window))
        bbar = "█" * max(1, int(W * r["billed_tokens"] / max_billed))
        flag = "  ⚙ COMPACTED" if r["compacted"] else ""
        print(
            f"{r['step']:>4} "
            f"{wbar:<28}{r['window_tokens']:>5} | "
            f"{bbar:<28}{r['billed_tokens']:>7}{flag}"
        )


def main():
    os.environ.setdefault("HARNESS_OFFLINE", "1")
    goal = " ".join(sys.argv[1:]) or "context engineering for long-running agents"
    # Small window so compaction fires several times — the sawtooth is clearer.
    run = build_recorded_agent(goal, max_context_tokens=1200)
    run()
    rows = run.trace.rows

    out = Path(__file__).parent / "token_growth.csv"
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    ascii_chart(rows)
    final_window = rows[-1]["window_tokens"]
    final_billed = run.budget.total_tokens
    print("-" * 84)
    print(f"\nSteps run:            {len(rows)}")
    print(f"Final window size:    {final_window:,} tokens   (compaction kept it bounded)")
    print(f"Total tokens BILLED:  {final_billed:,} tokens   (~{final_billed / max(1, final_window):.1f}x the window)")
    print(f"\nThe lesson: the window stayed ~flat while you paid for it over and over.")
    print(f"CSV: {out}")


if __name__ == "__main__":
    main()
