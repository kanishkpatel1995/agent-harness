"""LoCoMo loader for EXP-004 (the second domain: conversational memory).

Each of the 10 conversations has many sessions (the "sources" the agent reads,
which overflow the window and force compaction) and ~200 checkable QA pairs. The
agent reads the sessions under a compaction policy, then answers the questions.
This is the sequential, continuity-heavy task that contrasts with FRAMES.

Pre-cached file: experiments/applied/.data/locomo10.json (downloaded from
github.com/snap-research/locomo).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DATA = Path("experiments/applied/.data/locomo10.json")


@dataclass
class Conversation:
    id: str
    sessions: list   # list[str], one rendered transcript per session
    qa: list          # list[{question, answer, category}]


def _session_keys(conv):
    keys = [k for k in conv if k.startswith("session") and not k.endswith("date_time")]
    return sorted(keys, key=lambda k: int("".join(ch for ch in k if ch.isdigit()) or 0))


def load():
    raw = json.loads(DATA.read_text())
    out = []
    for c in raw:
        conv = c.get("conversation", {})
        sessions = []
        for sk in _session_keys(conv):
            turns = conv[sk]
            if not isinstance(turns, list):
                continue
            text = "\n".join(
                f"{t.get('speaker', '?')}: {t.get('text', '')}"
                for t in turns if isinstance(t, dict) and t.get("text")
            )
            if text.strip():
                sessions.append(text)
        qa = [
            {"question": q.get("question"), "answer": str(q.get("answer")),
             "category": str(q.get("category"))}
            for q in c.get("qa", [])
            if q.get("question") and q.get("answer") is not None
        ]
        out.append(Conversation(id=str(c.get("sample_id", "")), sessions=sessions, qa=qa))
    return out
