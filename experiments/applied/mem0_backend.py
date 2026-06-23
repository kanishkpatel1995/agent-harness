"""Mem0 as a FRAMES retrieval backend — extract-then-dedupe facts, on NIM.

Same EmbedStore interface (add / retrieve->str). Mem0's value-add vs our plain
`externalize` store is the strategy: an LLM extracts salient facts from each chunk and
dedupes them against what's stored (ADD / UPDATE / DELETE / NOOP), so the memory holds
deduped facts, not raw text. We hold the EMBEDDER constant with our NIM store
(nv-embedqa-e5-v5) via a custom mem0 embedder, so the only variable vs the `nim` store
is Mem0's extract-then-update layer, not the embedding model.

  LLM       : NIM (OpenAI-compatible) via OPENAI_BASE_URL / OPENAI_API_KEY
  embedder  : custom nv-embedqa (passage on add, query on search) — same as our store
  vector db : local chroma, fresh path per instance (no server, no cross-question bleed)

Note: mem0's qdrant module uses PEP-604 (`X | None`) annotations that fail to import on
Python 3.9; chroma imports cleanly, so we use it as the vector store here.
"""

from __future__ import annotations

import os
import tempfile

from experiments.nim import _load_env_key
from experiments.applied.embed import _embed   # nv-embedqa with input_type
from experiments.bench.logsetup import get
from mem0.embeddings.base import EmbeddingBase

log = get("mem0")
NIM_BASE = "https://integrate.api.nvidia.com/v1"


class NvEmbedqaEmbedder(EmbeddingBase):
    """mem0 embedder backed by our nv-embedqa; maps memory_action -> input_type."""

    def __init__(self, config=None):
        self.config = config

    def embed(self, text, memory_action=None):
        itype = "query" if memory_action == "search" else "passage"
        return _embed([text], itype)[0]

    def embed_batch(self, texts, memory_action="add"):
        itype = "query" if memory_action == "search" else "passage"
        return _embed(list(texts), itype)


class Mem0Backend:
    """EmbedStore-compatible store backed by Mem0 (extract-then-dedupe), on NIM."""

    def __init__(self, model: str = "meta/llama-3.1-8b-instruct"):
        os.environ["OPENAI_API_KEY"] = _load_env_key()
        os.environ["OPENAI_BASE_URL"] = NIM_BASE
        from mem0 import Memory
        path = tempfile.mkdtemp(prefix="mem0_chroma_")
        config = {
            "llm": {"provider": "openai",
                    "config": {"model": model, "temperature": 0, "max_tokens": 512}},
            "embedder": {"provider": "openai",
                         "config": {"model": "text-embedding-3-small"}},  # placeholder, overridden below
            "vector_store": {"provider": "chroma",
                             "config": {"collection_name": "frames", "path": path}},
        }
        self.mem = Memory.from_config(config)
        self.mem.embedding_model = NvEmbedqaEmbedder()   # hold the embedder constant with our NIM store
        self.user_id = "frames"
        self.backend = "mem0/nv-embedqa-e5-v5+chroma (extract-then-dedupe)"
        log.info(self.backend)

    def add(self, text):
        self.mem.add(text, user_id=self.user_id)

    def retrieve(self, query, k=3):
        # mem0 2.x: entity scoping moved from a top-level user_id to filters={...}.
        res = self.mem.search(query, filters={"user_id": self.user_id}, limit=k)
        items = res.get("results", res) if isinstance(res, dict) else res
        return "\n\n".join((r.get("memory", "") if isinstance(r, dict) else str(r)) for r in items)
