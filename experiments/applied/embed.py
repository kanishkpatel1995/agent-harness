"""Embedding store for the reversible-hybrid (and externalize) policies.

Direct call to the NVIDIA NIM embeddings endpoint (litellm mishandles
nv-embedqa's required input_type). In-memory cosine similarity, with a disk cache
keyed by text so re-runs are free. Chunks are kept small (nv-embedqa caps input
length).
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import requests

from experiments.nim import _load_env_key
from experiments.bench.logsetup import get

log = get("embed")
URL = "https://integrate.api.nvidia.com/v1/embeddings"
MODEL = "nvidia/nv-embedqa-e5-v5"
CHUNK = 1200  # chars per passage (well under the model's token cap)
CACHE = Path("experiments/applied/.embcache")
CACHE.mkdir(parents=True, exist_ok=True)


def _ckey(text, input_type):
    return hashlib.sha256(f"{input_type}|{text}".encode()).hexdigest()[:24]


def _embed(texts, input_type):
    out, todo, idx = [None] * len(texts), [], []
    for i, t in enumerate(texts):
        p = CACHE / f"{_ckey(t, input_type)}.json"
        if p.exists():
            out[i] = json.loads(p.read_text())
        else:
            todo.append(t); idx.append(i)
    for start in range(0, len(todo), 32):
        batch = todo[start:start + 32]
        key = _load_env_key()
        r = requests.post(
            URL, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"input": batch, "model": MODEL, "input_type": input_type,
                  "encoding_format": "float", "truncate": "END"}, timeout=60)
        r.raise_for_status()
        for j, d in enumerate(r.json()["data"]):
            v = d["embedding"]
            i = idx[start + j]
            out[i] = v
            (CACHE / f"{_ckey(texts[i], input_type)}.json").write_text(json.dumps(v))
    return out


def _chunks(text):
    return [text[i:i + CHUNK] for i in range(0, len(text), CHUNK) if text[i:i + CHUNK].strip()]


def _cos(a, b):
    s = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return s / (na * nb + 1e-9)


class EmbedStore:
    def __init__(self):
        self.texts = []
        self.vecs = []

    def add(self, text):
        chunks = _chunks(text)
        if not chunks:
            return
        for v, c in zip(_embed(chunks, "passage"), chunks):
            self.texts.append(c)
            self.vecs.append(v)
        log.debug(f"store add {len(chunks)} chunks (total {len(self.texts)})")

    def retrieve(self, query, k=3):
        if not self.texts:
            return ""
        qv = _embed([query], "query")[0]
        scored = sorted(((_cos(qv, v), t) for v, t in zip(self.vecs, self.texts)), key=lambda x: x[0], reverse=True)
        log.debug(f"store retrieve k={k} from {len(self.texts)} chunks")
        return "\n\n".join(t for _, t in scored[:k])
