"""Two DIFFERENT recalls, kept separate on purpose.

  fidelity : did the planted token literally survive in the window text?
             -> scores the COMPACTION POLICY (no model judgement involved).
  probe    : can the model recover the fact when asked to read the window back?
             -> scores POLICY + the model's recall-at-this-length.

Separating them is what lets us attribute an effect to compaction vs to the
model's length-dependent recall — the distinction that makes the claim defensible.
"""

from __future__ import annotations

from experiments.needles import score
from .logsetup import get

log = get("metrics")


def fidelity(window_text, needles):
    found = score(window_text, needles)
    log.debug(f"fidelity: {len(found)}/{len(needles)} tokens literally in window {sorted(found)}")
    return found


def probe(llm, window_text, needles):
    msgs = [
        {"role": "system", "content": "List every specific number, named term, and date "
                                       "that appears in the context. Output them plainly."},
        {"role": "user", "content": window_text[:12000]},
    ]
    r = llm.complete(msgs, stage="probe")
    found = score(r.content, needles)
    log.debug(f"probe: model recovered {len(found)}/{len(needles)} {sorted(found)} (cached={r.cached})")
    return found, r.usage
