"""LettaArchival — wrap Letta (formerly MemGPT) archival memory as an EXTERNALIZE
arm (with an ISOLATE flavor).

Letta's architecture is OS-inspired: the agent self-manages tiers — *core* memory
blocks pinned in-context, *recall* (the searchable history), and *archival* memory
in an external DB — editing them via tool calls. Here we use archival memory as
the store: push evicted turns in, let retrieval pull them back. The distinctive
trade-off vs a plain vector store is that in real Letta the *agent* decides what
to archive and when to read it (it spends tokens curating its own memory).

    pip install letta-client      # plus a running Letta server (see docs.letta.com)

Note: the Letta client surface shifts across versions; adjust the calls below to
your installed version if needed.
"""

from __future__ import annotations

try:
    from letta_client import Letta
except Exception:  # pragma: no cover - optional dep
    Letta = None

from ..base import ZERO, text


class LettaArchival:
    name = "letta"
    architecture = "externalize"
    retrieves = True
    decision = "Push evicted turns into Letta's archival memory; the agent retrieves them via archival search at answer time."
    tradeoff = "Persistent, agent-managed, OS-style tiers (core/recall/archival) — but the agent spends tokens and turns curating its own memory."
    result = "The MemGPT architecture, benched. (Needs a running Letta server.)"

    def __init__(self, base_url: str = "http://localhost:8283", agent_id: str | None = None):
        if Letta is None:
            raise ImportError("pip install letta-client (and run a Letta server)")
        self.client = Letta(base_url=base_url)
        self.agent_id = agent_id

    def compact(self, old, llm, store):
        for m in old:
            t = text(m)
            if t.strip():
                # archival insert (API shape may vary by Letta version)
                self.client.agents.passages.create(agent_id=self.agent_id, text=t)
        return [{"role": "system",
                 "content": f"[{len(old)} turns archived in Letta; retrievable on demand]"}], dict(ZERO)

    def retrieve(self, query: str, k: int = 3) -> list[str]:
        hits = self.client.agents.passages.search(agent_id=self.agent_id, query=query, limit=k)
        return [getattr(h, "text", str(h)) for h in (hits or [])]
