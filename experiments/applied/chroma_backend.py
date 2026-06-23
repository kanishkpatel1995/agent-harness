"""Chroma as a FRAMES retrieval backend — the open-source memory-system arm.

Same interface as `embed.EmbedStore` (`add(text)` / `retrieve(query, k) -> str`),
so the runner swaps it in for the externalize / hybrid policies with one line. It
wraps the harness `ChromaStore` (Chroma + all-MiniLM-L6-v2, cosine HNSW) and chunks
added text to the same 1200-char granularity EmbedStore uses, so the ONLY variable
versus the NIM store is the embedding model + index, not the chunking.

What this lets us measure (EXP-006): a general-purpose, local, 384-d encoder
(Chroma / MiniLM, offline via onnxruntime, no key) against a retrieval-tuned, 1024-d
API encoder with asymmetric query/passage embeddings (NIM nv-embedqa-e5-v5). Same
agent, same questions, same judge; only the memory backend changes.
"""

from __future__ import annotations

from harness.policies.adapters.chroma_store import ChromaStore
from experiments.bench.logsetup import get

log = get("chroma")
CHUNK = 1200  # match embed.EmbedStore so chunking is not a confound


def _chunks(text):
    return [text[i:i + CHUNK] for i in range(0, len(text), CHUNK) if text[i:i + CHUNK].strip()]


class ChromaBackend:
    """EmbedStore-compatible store backed by Chroma."""

    def __init__(self):
        self.store = ChromaStore(collection="frames")
        self.backend = self.store.backend
        log.info(f"Chroma retrieval backend: {self.backend} (cosine)")

    def add(self, text):
        chunks = _chunks(text)
        for c in chunks:
            self.store.add(c)
        log.debug(f"chroma add {len(chunks)} chunks (total {len(self.store)})")

    def retrieve(self, query, k=3):
        hits = self.store.search(query, k)
        log.debug(f"chroma retrieve k={k} from {len(self.store)} chunks")
        return "\n\n".join(hits)
