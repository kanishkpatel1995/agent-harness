"""End-to-end test: the whole harness runs offline with FakeLLM."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["HARNESS_OFFLINE"] = "1"
os.environ["HARNESS_QUIET"] = "1"

from harness import FakeLLM, build_agent


def test_full_run_finishes_with_report(tmp_path):
    run = build_agent(
        "context engineering for long-running agents",
        FakeLLM(),
        notes_path=tmp_path / "notes.md",
        max_context_tokens=2500,
        quiet=True,
    )
    answer = run()
    assert "Research report" in answer
    assert run.scratchpad.count() > 0  # notes were externalized
    # ran within budget
    assert run.budget.steps <= run.budget.max_steps


def test_compaction_fires_on_long_run(tmp_path):
    run = build_agent(
        "compaction strategies",
        FakeLLM(max_fetches=6),
        notes_path=tmp_path / "notes.md",
        max_context_tokens=2000,  # small window forces compaction
        quiet=True,
    )
    run()
    # after the run, the window should be far below the cumulative raw size
    comp = run.context.composition()
    assert comp["total"] <= run.context.max_context_tokens * 1.2
