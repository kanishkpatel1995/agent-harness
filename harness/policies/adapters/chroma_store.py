"""ChromaStore — the externalize backend, for real: Chroma vector k-NN.

A drop-in replacement for `harness.policies.store.Store` (same `add` / `search`).
The hand-rolled Store ranks by keyword overlap; this one does real embedding-based
nearest-neighbour search over an HNSW index.

It picks an embedder automatically, so it works whether or not you have a GPU stack:
  1. `sentence-transformers` (all-MiniLM-L6-v2) if installed — we embed, Chroma indexes.
  2. otherwise Chroma's bundled ONNX all-MiniLM-L6-v2 (via onnxruntime) — the SAME
     model, no torch needed. Fully offline once the ~80MB model is cached; no API key.

The collection is created with cosine space, to match the rest of the harness's
stores (the hand Store and the NIM `EmbedStore` both rank by cosine).

    pip install chromadb                        # ONNX path, no torch
    pip install chromadb sentence-transformers  # explicit-vector path (needs torch>=2.1)
"""

from __future__ import annotations

try:
    import chromadb
    from chromadb.config import Settings
except Exception:  # pragma: no cover - optional dep
    chromadb = None
try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dep
    SentenceTransformer = None


class ChromaStore:
    def __init__(self, model: str = "all-MiniLM-L6-v2", collection: str = "harness"):
        if chromadb is None:
            raise ImportError("ChromaStore needs: pip install chromadb")
        # in-memory; swap to PersistentClient(path=...) to keep the index on disk.
        self._client = chromadb.EphemeralClient(settings=Settings(anonymized_telemetry=False))
        common = dict(name=collection, metadata={"hnsw:space": "cosine"})
        if SentenceTransformer is not None:
            # explicit-vector path: we compute the embedding, Chroma just stores + indexes it.
            self._embed = SentenceTransformer(model)
            self.backend = f"sentence-transformers/{model}"
            self._col = self._client.get_or_create_collection(**common)
        else:
            # ONNX fallback: Chroma embeds with its bundled all-MiniLM-L6-v2 (onnxruntime).
            from chromadb.utils import embedding_functions
            self._embed = None
            self.backend = "chroma-onnx/all-MiniLM-L6-v2"
            self._col = self._client.get_or_create_collection(
                embedding_function=embedding_functions.DefaultEmbeddingFunction(), **common)
        self._n = 0

    def add(self, text: str):
        if not text or not text.strip():
            return
        if self._embed is not None:
            self._col.add(ids=[str(self._n)], documents=[text],
                          embeddings=[self._embed.encode(text).tolist()])
        else:
            self._col.add(ids=[str(self._n)], documents=[text])  # Chroma embeds it
        self._n += 1

    def search(self, query: str, k: int = 3) -> list[str]:
        if self._n == 0:
            return []
        n = min(k, self._n)
        if self._embed is not None:
            res = self._col.query(query_embeddings=[self._embed.encode(query).tolist()], n_results=n)
        else:
            res = self._col.query(query_texts=[query], n_results=n)
        return (res.get("documents") or [[]])[0]

    def __len__(self):
        return self._n
