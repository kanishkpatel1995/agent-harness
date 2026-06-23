"""ChromaStore — the externalize backend, for real: Chroma + sentence-transformers.

A drop-in replacement for `harness.policies.store.Store` (same `add` / `search`).
The hand-rolled Store ranks by keyword overlap; this one embeds with an
open-source model and does real vector k-NN — fully offline once the model is
cached, no API key. The externalize / hybrid arms (and Mem0/Letta below) sit on
top of a store like this.

    pip install chromadb sentence-transformers
"""

from __future__ import annotations

try:
    import chromadb
except Exception:  # pragma: no cover - optional dep
    chromadb = None
try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dep
    SentenceTransformer = None


class ChromaStore:
    def __init__(self, model: str = "all-MiniLM-L6-v2", collection: str = "harness"):
        if chromadb is None or SentenceTransformer is None:
            raise ImportError("ChromaStore needs: pip install chromadb sentence-transformers")
        self._embed = SentenceTransformer(model)            # open-source, offline embedder
        self._client = chromadb.EphemeralClient()           # in-memory; use PersistentClient to keep
        self._col = self._client.get_or_create_collection(collection)
        self._n = 0

    def add(self, text: str):
        if not text or not text.strip():
            return
        vec = self._embed.encode(text).tolist()
        self._col.add(ids=[str(self._n)], documents=[text], embeddings=[vec])
        self._n += 1

    def search(self, query: str, k: int = 3) -> list[str]:
        if self._n == 0:
            return []
        vec = self._embed.encode(query).tolist()
        res = self._col.query(query_embeddings=[vec], n_results=min(k, self._n))
        return (res.get("documents") or [[]])[0]

    def __len__(self):
        return self._n
