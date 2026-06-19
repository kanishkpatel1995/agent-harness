"""Datasets = a stream of text chunks + the facts we expect to survive.

  synthetic : our planted-needle pages — full control, offline, reproducible.
  hf:<name> : real long-context benchmarks (RULER / LongBench / BABILong) via the
              Hugging Face `datasets` library. A SEAM for external validity, not
              wired yet — see load().

Every Sample also records each needle's DEPTH in its page (0=front .. 1=end), so
we can later analyze recall vs position — the lost-in-the-middle axis.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from experiments.needles import NEEDLES  # reuse the planted-fact bank
from .logsetup import get

log = get("dataset")


@dataclass
class Sample:
    chunks: list      # list[str] — the "pages" that stream into the window
    needles: list     # list[Needle] — the facts we planted
    positions: dict   # needle_id -> depth in [0, 1]


def synthetic(run_length: int, n_needles: int, seed: int) -> Sample:
    rng = random.Random(seed)
    needles = NEEDLES[: min(n_needles, len(NEEDLES), run_length)]
    order = list(range(run_length))
    rng.shuffle(order)
    needle_on = {order[i]: needles[i] for i in range(len(needles))}

    chunks, positions = [], {}
    for i in range(run_length):
        n_filler = rng.randint(30, 50)              # vary size -> vary compaction timing
        lines = [f"# Source {i + 1}"] + [
            f"Background detail line {j} for source {i + 1}." for j in range(n_filler)
        ]
        if i in needle_on:
            depth = rng.random()                    # 0=front .. 1=end (the position axis)
            at = max(1, min(len(lines), int(len(lines) * depth)))
            lines.insert(at, needle_on[i].sentence)
            positions[needle_on[i].id] = round(depth, 3)
            log.debug(f"seed{seed} L{run_length}: needle '{needle_on[i].id}' -> source {i + 1} @ depth {depth:.2f}")
        chunks.append("\n".join(lines))
    log.debug(f"seed{seed} L{run_length}: built {len(chunks)} chunks, {len(needles)} needles")
    return Sample(chunks=chunks, needles=needles, positions=positions)


def load(spec: str, run_length: int, n_needles: int, seed: int) -> Sample:
    if spec == "synthetic":
        return synthetic(run_length, n_needles, seed)
    if spec.startswith("hf:"):
        raise NotImplementedError(
            f"HF dataset adapter not wired yet ({spec}). Planned: load RULER / "
            "LongBench / BABILong via the `datasets` library and map each into a "
            "Sample(chunks, needles, positions). This is the external-validity seam."
        )
    raise ValueError(f"unknown dataset spec: {spec!r}")
