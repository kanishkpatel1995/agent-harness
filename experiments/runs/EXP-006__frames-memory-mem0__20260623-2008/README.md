# EXP-006 — frames-memory (the memory-system bake-off)

The consolidated result for the three EXP-006 backend runs (nim / chroma / mem0). Each backend
has its own run dir + manifest; this README holds the head-to-head.

**Hypothesis:** under a fixed externalize policy, the memory system matters — a retrieval-tuned
embedder beats a general local one, and Mem0's extract-then-dedupe trades recall for a cleaner
memory at a higher per-add cost. The agent and judge are held constant; only the store changes.

**Result (n=20, 8B agent, 70B judge, seed 7, identical questions across all three):**

| backend | memory system | accuracy | mean tokens (chat) |
|---|---|---|---|
| nim | nv-embedqa-e5-v5 (1024-d, retrieval-tuned, asymmetric query/passage, API) | **0.50** | ~1,900 |
| mem0 | extract-then-dedupe facts (LLM) + nv-embedqa embedder | **0.40** | ~1,925 |
| chroma | all-MiniLM-L6-v2 (384-d, general-purpose, local ONNX) | **0.35** | ~1,690 |

**Three readings.**
1. **The embedding model alone moves accuracy.** Same policy, swap only the embedder: nv-embedqa
   0.50 vs MiniLM 0.35, a 0.15 gap. Retrieval-tuned, asymmetric, higher-dimensional embeddings
   recover more answer-bearing chunks.
2. **Mem0's distillation hurt here.** Mem0 uses the *same* nv-embedqa embedder as `nim`, so its
   drop to 0.40 is entirely its extract-then-dedupe layer: turning raw chunks into deduped facts
   lost detail that multi-hop factual questions needed.
3. **But a good embedder beats a weak one even with distillation.** Mem0 (0.40) still beat chroma
   (0.35): nv-embedqa + facts > MiniLM + raw chunks. Mem0's cost, however, is an LLM extraction
   call on *every* add — invisible in the chat-token column above, and the reason it ran ~3 min per
   question (the most expensive arm by far).

**Strongest threat to validity.** n=20 at one seed; the 95% bootstrap CI on these proportions is
~±0.21, so the gaps are directional. The robust claims are qualitative: the embedder matters, and
Mem0's fact-distillation did not help on this factual task.

**Reproduce:** `python experiments/applied/launch_exp006_memory.py` (all three), or one backend with
`python -m experiments.applied --policies externalize --store nim|chroma|mem0 --judge --n 20 --budget 1500 --chunk-chars 1500`.
