"""The store seam — where 'externalized' bytes go and how they come back.

This is the substrate under the externalize / hybrid architectures (and under
Mem0 / Letta / a LangGraph store in `adapters/`). The default here is a tiny,
dependency-free, OFFLINE store: it keeps raw text and ranks by token overlap, so
the compare demo runs with no embeddings and no network.

Swap in a real vector store for production — `adapters/chroma_store.py` wraps
Chroma + sentence-transformers behind this exact interface:

    store.add(text)            # remember a chunk
    store.search(query, k)     # get the k most relevant chunks back
"""

from __future__ import annotations

import re


def _tokens(s: str) -> set:
    return set(re.findall(r"[a-z0-9][a-z0-9\-]+", s.lower()))


class Store:
    """In-memory, offline, keyword-overlap retrieval. The honest baseline."""

    def __init__(self):
        self._docs: list[str] = []

    def add(self, text: str):
        if text and text.strip():
            self._docs.append(text.strip())

    def search(self, query: str, k: int = 3) -> list[str]:
        q = _tokens(query)
        if not q or not self._docs:
            return []
        scored = sorted(
            self._docs,
            key=lambda d: len(q & _tokens(d)),
            reverse=True,
        )
        # only return docs with any overlap
        return [d for d in scored if q & _tokens(d)][:k]

    def __len__(self):
        return len(self._docs)
