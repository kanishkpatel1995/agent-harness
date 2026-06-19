"""Planted 'needle' facts: the objective, mechanical recall metric.

Each needle is a checkable fact whose answer is a unique token (a coined term or
a specific number) we can grep for in any text. We INJECT the needle sentence
into a source page; we SCORE by testing whether the needle's answer survived into
a given text (the compacted window, the scratchpad, or the model's probe answer).
No LLM judge, no ambiguity: a coined token either survived or it didn't.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Needle:
    id: str
    sentence: str  # what gets embedded in a page
    answer: str    # the unique token we grep for when scoring


# A fixed bank. Coined names / specific numbers, so they can't be in training
# data and can't be guessed — a hit means the fact genuinely survived.
NEEDLES = [
    Needle("zarnak",     "The Zarnak coefficient was measured at 0.47 in 2019.",  "0.47"),
    Needle("bellwether", "Project Bellwether cut p99 latency by 38 percent.",     "38 percent"),
    Needle("kessler",    "The Kessler threshold for the array is 6,200 units.",   "6,200"),
    Needle("vantage",    "Vantage-9 shipped on March 14, 2021.",                  "March 14, 2021"),
    Needle("orrery",     "The Orrery index peaked at 1,815 before falling.",      "1,815"),
    Needle("plimsoll",   "Plimsoll capacity is rated for 27 metric tonnes.",      "27 metric tonnes"),
    Needle("doppler",    "Doppler-7 uses a 13-stage pipeline.",                   "13-stage"),
    Needle("quillon",    "The Quillon constant equals 88.6 millijoules.",         "88.6"),
]


def _norm(s: str) -> str:
    """Forgive trivial formatting drift: %<->percent, 6,200<->6200, spacing."""
    s = (s or "").lower().replace("%", " percent")
    s = re.sub(r",", "", s)
    return re.sub(r"\s+", " ", s).strip()


def inject(page_text: str, needles, position: float = 0.5) -> str:
    """Insert each needle sentence into the page at a relative position."""
    lines = page_text.split("\n")
    for i, n in enumerate(needles):
        at = max(0, min(len(lines), int(len(lines) * position) + i))
        lines.insert(at, n.sentence)
    return "\n".join(lines)


def score(text: str, needles) -> set:
    """Which needle answers survived into `text` (normalized, case-insensitive)."""
    hay = _norm(text)
    return {n.id for n in needles if _norm(n.answer) in hay}
