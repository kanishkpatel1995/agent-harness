"""FRAMES loader (google/frames-benchmark): multi-hop questions with gold answers
and 2-15 gold Wikipedia URLs each. We use the gold URLs as oracle retrieval."""

from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class Item:
    id: str
    question: str
    answer: str
    wiki_urls: list = field(default_factory=list)


def load(n=100, seed=0):
    from datasets import load_dataset

    ds = load_dataset("google/frames-benchmark", split="test")
    items = []
    for i, r in enumerate(ds):
        urls = [r[k] for k in r if k.lower().startswith("wikipedia_link")]
        urls = [u for u in urls if isinstance(u, str) and u.startswith("http")]
        if not urls or not r.get("Prompt") or not r.get("Answer"):
            continue
        items.append(Item(id=str(i), question=r["Prompt"], answer=str(r["Answer"]), wiki_urls=urls))
    rng = random.Random(seed)
    rng.shuffle(items)
    return items[:n]
