"""Trace: make the invisible visible.

You can't debug what you can't see. The whole reason long-running agents feel
like black magic is that the context window is invisible. This prints it: on
every step you see how full the window is, what the agent decided, and when
compaction fires. On stage, this terminal output IS the demo.

Set HARNESS_QUIET=1 to silence it (e.g. in tests).
"""

from __future__ import annotations

import os
import textwrap


class Trace:
    def __init__(self, quiet: bool | None = None):
        self.quiet = quiet if quiet is not None else os.environ.get("HARNESS_QUIET") == "1"

    def _p(self, *a):
        if not self.quiet:
            print(*a)

    def step_start(self, step, context, budget):
        comp = context.composition()
        self._p("")
        self._p(f"{C.DIM}{'─' * 64}{C.END}")
        self._p(f"{C.BOLD}STEP {step}{C.END}   {C.DIM}{budget.summary()}{C.END}")
        self._p(self._context_bar(comp))

    def _context_bar(self, comp):
        total, budget = comp["total"], comp["budget"]
        width = 40
        filled = min(width, int(width * total / budget)) if budget else 0
        pinned_w = min(filled, int(width * comp["pinned"] / budget)) if budget else 0
        body_w = filled - pinned_w
        bar = (
            C.PURPLE + "█" * pinned_w + C.END
            + C.CYAN + "█" * body_w + C.END
            + C.DIM + "·" * (width - filled) + C.END
        )
        pct = int(100 * total / budget) if budget else 0
        return (
            f"  context [{bar}] {total:,}/{budget:,} tok ({pct}%)  "
            f"{C.DIM}{comp['messages']} msgs{C.END}"
        )

    def tool_call(self, call):
        args = ", ".join(f"{k}={_short(v)}" for k, v in call["arguments"].items())
        self._p(f"  {C.PURPLE}→ {call['name']}{C.END}({args})")

    def tool_result(self, name, result):
        preview = textwrap.shorten(result.replace("\n", " "), width=88, placeholder=" …")
        self._p(f"    {C.DIM}{preview}{C.END}")

    def compaction(self, summary, context):
        comp = context.composition()
        self._p(f"  {C.AMBER}⚙ COMPACTED{C.END} → window now {comp['total']:,} tok "
                f"({comp['messages']} msgs). Old turns summarized; details in scratchpad.")

    def final(self, answer, budget):
        self._p("")
        self._p(f"{C.GREEN}{'═' * 64}{C.END}")
        self._p(f"{C.GREEN}{C.BOLD}DONE{C.END}  {C.DIM}{budget.summary()}{C.END}")
        self._p(f"{C.GREEN}{'═' * 64}{C.END}")

    def note(self, text):
        self._p(f"  {C.AMBER}! {text}{C.END}")


def _short(v):
    s = str(v)
    return s if len(s) <= 40 else s[:37] + "…"


class C:
    # ANSI colors, roughly mapped to the Founsi palette for on-brand demos.
    PURPLE = "\033[38;5;141m"
    CYAN = "\033[38;5;80m"
    GREEN = "\033[38;5;71m"
    AMBER = "\033[38;5;179m"
    DIM = "\033[2m"
    BOLD = "\033[1m"
    END = "\033[0m"
