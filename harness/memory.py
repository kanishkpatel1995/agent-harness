"""Scratchpad: memory that lives OUTSIDE the context window.

The single most effective context-engineering move: stop trying to keep
everything in the window. Let the agent write findings to a file and read them
back on demand. The window stays small; the memory is unbounded; and compaction
is safe because nothing important only existed in the turns we threw away.

This is a deliberately dumb file-backed store. That's the point — you can open
notes.md during the demo and show the audience the agent's externalized brain.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path


class Scratchpad:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._notes: list[str] = []
        # Start fresh each run so the demo is reproducible.
        self.path.write_text("# Agent scratchpad\n\n", encoding="utf-8")

    def save_note(self, text: str, tag: str = "note") -> str:
        stamp = _dt.datetime.now().strftime("%H:%M:%S")
        entry = f"## [{tag}] {stamp}\n{text.strip()}\n"
        self._notes.append(entry)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(entry + "\n")
        return f"Saved note #{len(self._notes)} ({len(text)} chars) to scratchpad."

    def read_notes(self) -> str:
        if not self._notes:
            return "(scratchpad is empty)"
        return "\n".join(self._notes)

    def count(self) -> int:
        return len(self._notes)
