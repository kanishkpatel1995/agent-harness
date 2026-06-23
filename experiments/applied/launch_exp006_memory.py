#!/usr/bin/env python3
"""EXP-006 — the memory-system bake-off: which retrieval backend wins on FRAMES?

Holds the agent, the questions, the judge, and the policy (externalize) constant and
swaps ONLY the store backend behind the externalize arm:

  nim    -> EmbedStore: NVIDIA nv-embedqa-e5-v5 (1024-d, retrieval-tuned, asymmetric
            query/passage embeddings, API + disk cache)
  chroma -> ChromaBackend: Chroma + all-MiniLM-L6-v2 (384-d, general-purpose, local
            onnxruntime, cosine HNSW, no API key)

Writes two self-contained run dirs (one per backend) and prints the head-to-head.
This is the first real open-source-memory-system arm; LangChain/Mem0 follow (on NIM).

    python experiments/applied/launch_exp006_memory.py
"""

from __future__ import annotations

import csv
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.applied.runner import Config, run  # noqa: E402
from experiments.bench.logsetup import setup, get  # noqa: E402

log = get("exp006")

BACKENDS = [("nim", "frames-memory-nim"), ("chroma", "frames-memory-chroma"),
            ("mem0", "frames-memory-mem0")]

LABELS = {"nim": "nv-embedqa-e5-v5 (API, 1024-d)",
          "chroma": "MiniLM (local ONNX, 384-d)",
          "mem0": "Mem0 deduped facts (nv-embedqa)"}


def _cfg(store: str, slug: str) -> Config:
    return Config(
        exp_id="EXP-006",
        slug=slug,
        hypothesis=(
            "On FRAMES, the memory system matters under a fixed externalize policy: a retrieval-"
            "tuned embedder (NIM nv-embedqa-e5-v5) beats a general local encoder (Chroma/MiniLM), "
            "and Mem0's extract-then-dedupe-facts strategy trades raw recall for a smaller, cleaner "
            "memory at a higher per-add LLM cost. The agent and judge are held constant."
        ),
        assumptions=(
            "Oracle articles + the externalize policy isolate the memory backend as the variable.",
            "nim and mem0 share the nv-embedqa embedder, so mem0's delta is its extract-then-dedupe, not the embedder.",
            "Chroma uses cosine space to match the NIM store's cosine ranking.",
            "The 70b judge and the 8b agent are identical across all backends.",
        ),
        model="meta/llama-3.1-8b-instruct",
        use_judge=True,
        policies=("externalize",),
        store=store,
        n_questions=20,
        max_articles=6,
        budget=1500,
        chunk_chars=1500,
        keep_recent=4,
        seed=7,
    )


def _summary(results_path):
    rows = list(csv.DictReader(open(results_path)))
    if not rows:
        return 0.0, 0, 0, 0
    acc = sum(int(r["correct"]) for r in rows) / len(rows)
    tok = st.mean(int(r["tokens_total"]) for r in rows)
    rch = st.mean(int(r["retrieved_chars"]) for r in rows)
    return acc, tok, rch, len(rows)


if __name__ == "__main__":
    setup("INFO")
    out = {}
    for store, slug in BACKENDS:
        log.info(f"=== EXP-006 backend: {store} ===")
        out[store] = _summary(run(_cfg(store, slug)))
    print("\n=== EXP-006: FRAMES externalize — memory-system head-to-head ===")
    print(f"{'backend':<8}{'accuracy':>10}{'mean_tokens':>13}{'retr_chars':>12}{'n':>5}   memory system")
    for store, _ in BACKENDS:
        acc, tok, rch, n = out[store]
        print(f"{store:<8}{acc:>10.2f}{tok:>13.0f}{rch:>12.0f}{n:>5}   {LABELS[store]}")
