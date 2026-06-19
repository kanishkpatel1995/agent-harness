# Literature review — context engineering & compaction

A grounded survey for the compaction bake-off ([`paper.md`](paper.md)) and the
curriculum ([`curriculum.md`](curriculum.md)). It is organized as a *narrative*
first (where the field is, where the gap is) and an *annotated bibliography*
second.

> **Verification note.** Every arXiv ID, author list, year, and venue below was
> confirmed against the paper's actual abstract page (or the live blog URL) in
> June 2026 — not recalled from memory. Two sources are explicitly **not**
> peer-reviewed and flagged inline: the Chroma "Context Rot" report and the
> practitioner blog posts in §6. If you cite anything here, you can trust the
> identifier; still open the link before quoting a number.

---

## 0. The through-line (read this first)

The argument the whole field makes, in five steps:

1. **More context is not free, and not even neutral.** Long inputs degrade model
   accuracy in structured, measurable ways — the U-shaped "lost in the middle"
   curve (§1). A bigger window raises the ceiling; it does not bend the curve.
2. **The degradation is worse than the marketing.** Benchmarks designed *after*
   needle-in-a-haystack (RULER, HELMET, NoLiMa, §2) show models use only a
   fraction of their advertised window and that the simple needle test
   *overstates* real ability. So you must measure carefully, and a single needle
   number is not enough.
3. **So you manage the context.** Two families of fixes exist. **Externalize** —
   move information to a retrievable store outside the window (§3). **Compress /
   compact** — shrink what stays in the window (§4).
4. **Compression has been studied mostly at the wrong level for agents.** Almost
   all prior compression work targets a *single static prompt* or *retrieved RAG
   passages*, and optimizes *inference efficiency* (§4). Very little studies an
   *evolving multi-turn agent transcript*, and the *recency-summary* policy that
   ships in real agent harnesses is essentially unmeasured against alternatives.
5. **That is the gap (§7).** We compare compaction policies at the *message/turn*
   level, training-free and model-agnostic, measured by *fact-recall per token*,
   with an external scratchpad as the safety net — the regime real agents live in
   and the one the literature skips.

Everything below substantiates one of those five steps.

---

## 1. The problem — long-context degradation

The empirical foundation: model quality is a function of *where* and *how much*
context you use, not just *whether* the fact is present.

- **Lost in the Middle: How Language Models Use Long Contexts** — Liu et al.,
  2023 (publ. TACL 2024). arXiv:[2307.03172](https://arxiv.org/abs/2307.03172).
  Accuracy is highest when the relevant fact is at the *start* or *end* of the
  input and sags in the *middle* — a U-shaped curve. → The single load-bearing
  citation for "position governs recall," and the theoretical justification for
  keeping the pinned head + recent tail verbatim and compacting the middle.
- **RULER: What's the Real Context Size of Your Long-Context LMs?** — Hsieh et
  al., 2024 (COLM 2024). arXiv:[2404.06654](https://arxiv.org/abs/2404.06654).
  A configurable synthetic benchmark (multi-hop tracing, aggregation) on which
  ~all 17 models tested degrade *well before* their advertised window despite
  near-perfect vanilla needle scores. → "Effective context" ≪ nominal context;
  compaction is justified even when the raw budget looks sufficient.
- **NoLiMa: Long-Context Evaluation Beyond Literal Matching** — Modarressi et
  al., 2025 (ICML 2025). arXiv:[2502.05167](https://arxiv.org/abs/2502.05167).
  Remove lexical overlap between query and target and 10/12 models fall below
  half their short-context baseline by 32K. → Degradation is an
  attention/retrieval problem, not surface matching — a policy that preserves
  *semantically* relevant facts should beat keyword truncation.
- **Context Rot: How Increasing Input Tokens Impacts LLM Performance** — Hong,
  Troynikov & Huber, 2025. *Chroma technical report — NOT peer-reviewed.*
  [research.trychroma.com/context-rot](https://research.trychroma.com/context-rot).
  Across 18 frontier models, performance decays non-uniformly as input grows,
  even on simple tasks well below the limit. → The most direct practitioner
  motivation for "fact-recall **per token**" as a metric; cite as industry
  evidence, not as a peer-reviewed result.

---

## 2. Evaluation — how we know (and how needle tests mislead)

Our metric is a fact-recall probe, so we inherit this methodology — including its
documented failure modes.

- **Needle-in-a-Haystack (NIAH)** — Greg Kamradt, 2023. *GitHub artifact, not a
  paper.* [github.com/gkamradt/LLMTest_NeedleInAHaystack](https://github.com/gkamradt/LLMTest_NeedleInAHaystack).
  The canonical probe: place one fact at varying depth in long filler, test
  recall over (length × depth). → Direct ancestor of our metric; we measure
  *survival through compaction* rather than retrieval from a static prompt.
- **HELMET: How to Evaluate Long-Context LMs Effectively and Thoroughly** — Yen
  et al., 2024 (ICLR 2025). arXiv:[2410.02694](https://arxiv.org/abs/2410.02694).
  Across 59 models and 7 application categories: synthetic NIAH does *not*
  reliably predict downstream performance. → The methodological backbone for our
  eval design — don't let a single needle number carry the claim; ground it in an
  application task.
- **Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena** — Zheng et al.,
  2023 (NeurIPS 2023 D&B). arXiv:[2306.05685](https://arxiv.org/abs/2306.05685).
  Strong LLM judges agree with humans ~80%+ but carry position, verbosity, and
  self-enhancement biases. → If we add an LLM-judge quality metric, this is the
  citation for both its validity *and* the threats-to-validity section.
- **LongBench** — Bai et al., 2023 (ACL 2024).
  arXiv:[2308.14508](https://arxiv.org/abs/2308.14508); **LongBench v2** — Bai et
  al., 2024. arXiv:[2412.15204](https://arxiv.org/abs/2412.15204). Realistic
  multi-task long-context suites (v2: 503 hard items, 8K–2M words). → A source of
  realistic downstream tasks if we extend beyond synthetic needles.
- **∞Bench / InfiniteBench** — Zhang et al., 2024 (ACL 2024).
  arXiv:[2402.13718](https://arxiv.org/abs/2402.13718); **LV-Eval** — Yuan et
  al., 2024. arXiv:[2402.05136](https://arxiv.org/abs/2402.05136); **BABILong** —
  Kuratov et al., 2024 (NeurIPS 2024 D&B).
  arXiv:[2406.10149](https://arxiv.org/abs/2406.10149); **Michelangelo** —
  Vodrahalli et al., 2024 (Google DeepMind).
  arXiv:[2409.12640](https://arxiv.org/abs/2409.12640). The 100K–10M-token and
  latent-structure regimes; BABILong's *distributed multi-fact* setting is the
  closest analogue to where importance-ranked/semantic compaction should win. →
  Use to argue our run-length axis is the right stressor and to source harder
  tasks later.

---

## 3. The externalize move — memory-augmented agents

This family is why our compaction can be *lossy but safe*: if the durable facts
live in a retrievable store, evicting them from the window costs nothing.

- **MemGPT: Towards LLMs as Operating Systems** — Packer et al., 2023.
  arXiv:[2310.08560](https://arxiv.org/abs/2310.08560). OS-inspired hierarchical
  memory that *pages* between a fixed window ("main memory") and external storage
  ("disk"), with the LLM self-editing what stays resident. → The canonical
  "window as managed cache + external store"; the intellectual parent of the
  scratchpad. (Became the open-source Letta project.)
- **Generative Agents: Interactive Simulacra of Human Behavior** — Park et al.,
  2023. arXiv:[2304.03442](https://arxiv.org/abs/2304.03442). A natural-language
  "memory stream" retrieved by *recency + importance + relevance*, periodically
  distilled into "reflections." → Direct motivation for importance-ranked and
  semantic compaction; the scoring axes are a ready-made importance heuristic.
- **Retrieval-Augmented Generation for Knowledge-Intensive NLP** — Lewis et al.,
  2020 (NeurIPS 2020). arXiv:[2005.11401](https://arxiv.org/abs/2005.11401). The
  foundational case that an external retrievable store can substitute for
  in-parameter knowledge. → The theoretical basis for "evict freely if still
  retrievable."
- **Recursively Summarizing Enables Long-Term Dialogue Memory** — Wang (Qingyue)
  et al., 2023. arXiv:[2308.15022](https://arxiv.org/abs/2308.15022). A running
  summary updated by combining prior memory with each new chunk keeps long
  dialogues consistent without retraining. → The clearest published baseline for
  the **recency-summary** policy we benchmark.
- **MemoryBank** — Zhong et al., 2023.
  arXiv:[2305.10250](https://arxiv.org/abs/2305.10250) (Ebbinghaus-style
  forgetting curve); **Self-Controlled Memory (SCM)** — Wang (Bing) et al., 2023.
  arXiv:[2304.13343](https://arxiv.org/abs/2304.13343); **Think-in-Memory** — Liu
  et al., 2023. arXiv:[2311.08719](https://arxiv.org/abs/2311.08719) (store
  reasoned *thoughts*, not raw turns); **A-MEM** — Xu et al., 2025.
  arXiv:[2502.12110](https://arxiv.org/abs/2502.12110) (Zettelkasten-style linked
  notes). → A spectrum of *what* and *how* to externalize and decay — each is an
  importance/semantic policy in disguise.
- **Mem0: Production-Ready AI Agents with Scalable Long-Term Memory** — Chhikara
  et al., 2025. arXiv:[2504.19413](https://arxiv.org/abs/2504.19413). Extract +
  consolidate + retrieve salient facts; reports >90% lower token cost vs.
  full-context while improving long-conversation accuracy. → The closest existing
  evidence for our exact thesis (fact-recall per token), at the memory-store
  level rather than the compaction-policy level.
- **MemoryLLM: Towards Self-Updatable LLMs** — Wang (Yu) et al., 2024 (ICML
  2024). arXiv:[2402.04624](https://arxiv.org/abs/2402.04624). A *parametric*
  in-model memory pool. → The boundary case / contrast: argues why an
  *inspectable external* store is preferable when compaction must be auditable.
- **A Survey on the Memory Mechanism of LLM-based Agents** — Zhang et al., 2024
  (ACM TOIS). arXiv:[2404.13501](https://arxiv.org/abs/2404.13501). → The umbrella
  taxonomy that situates compaction within agent memory design; cite to position
  the four policies.

---

## 4. The compact move — compression & KV-cache

The biggest neighbor to our work — and the one with the cleanest gap. Prior
compression splits into three families; **none operates where we do.**

**(a) Token-level pruning** — drop low-information tokens from the text:
- **LLMLingua** — Jiang et al., 2023 (EMNLP 2023).
  arXiv:[2310.05736](https://arxiv.org/abs/2310.05736); **LongLLMLingua** — Jiang
  et al., 2023 (ACL 2024). arXiv:[2310.06839](https://arxiv.org/abs/2310.06839).
  Budget-controlled, query-aware token dropping (up to 20×). → Token-level, on a
  static prompt; we keep whole turns and summarize, on an evolving transcript.
- **Compressing Context to Enhance Inference Efficiency (Selective Context)** —
  Li et al., 2023 (EMNLP 2023).
  arXiv:[2310.06201](https://arxiv.org/abs/2310.06201). Prune units by
  self-information (~50% cost cut). → The within-text analogue of our
  *importance-ranked* policy.
- **RECOMP: Improving RAG with Compression and Selective Augmentation** — Xu et
  al., 2023. arXiv:[2310.04408](https://arxiv.org/abs/2310.04408). Extractive +
  abstractive compressors for retrieved passages; can emit empty when irrelevant.
  → Its *abstractive* compressor is the closest prior analogue to our LLM-summary
  compaction — but on RAG passages for one query, not an accumulating dialogue.

**(b) Learned latent / soft-prompt compression** — compress into vectors
(requires training):
- **Learning to Compress Prompts with Gist Tokens** — Mu et al., 2023 (NeurIPS
  2023). arXiv:[2304.08467](https://arxiv.org/abs/2304.08467); **In-context
  Autoencoder (ICAE)** — Ge et al., 2023.
  arXiv:[2307.06945](https://arxiv.org/abs/2307.06945); **AutoCompressors** —
  Chevalier et al., 2023 (EMNLP 2023).
  arXiv:[2305.14788](https://arxiv.org/abs/2305.14788). → All produce opaque,
  finetuned soft tokens; ours is training-free and stays in human-readable text.
- **Compressive Transformers** — Rae et al., 2019 (ICLR 2020).
  arXiv:[1911.05507](https://arxiv.org/abs/1911.05507); **Recurrent Memory
  Transformer** — Bulatov et al., 2022 (NeurIPS 2022).
  arXiv:[2207.06881](https://arxiv.org/abs/2207.06881); **Long Context
  Compression with Activation Beacon** — Zhang et al., 2024.
  arXiv:[2401.03462](https://arxiv.org/abs/2401.03462). → Architecture-level
  compression of activations/KV; orthogonal to (and stackable beneath) our
  text-level compaction.

**(c) KV-cache eviction & retrieval-preserving access** — operate in the
attention layer:
- **Efficient Streaming LMs with Attention Sinks (StreamingLLM)** — Xiao et al.,
  2024 (ICLR 2024). arXiv:[2309.17453](https://arxiv.org/abs/2309.17453). Keep
  initial "sink" tokens + a recent window. → A fixed sinks+recency rule in the
  cache; our recency-summary is the *message-level* cousin.
- **H₂O: Heavy-Hitter Oracle** — Zhang et al., 2023 (NeurIPS 2023).
  arXiv:[2306.14048](https://arxiv.org/abs/2306.14048). Evict KV by attention
  mass, keeping recent + "heavy hitter" tokens. → The attention-level analogue of
  *importance-ranked* compaction (ranks KV entries; we rank turns by content).
- **Landmark Attention** — Mohtashami & Jaggi, 2023 (NeurIPS 2023).
  arXiv:[2305.16300](https://arxiv.org/abs/2305.16300). Block "landmark" tokens
  enable random-access retrieval over long context. → *Retrieval-preserving* —
  keeps full context available; the opposite design choice from our lossy
  eviction, a useful contrast.

---

## 5. Foundations — agent loops & reasoning

What the harness *is*, and where the transcript that needs compacting comes from.

- **Chain-of-Thought Prompting** — Wei et al., 2022 (NeurIPS 2022).
  arXiv:[2201.11903](https://arxiv.org/abs/2201.11903). Intermediate reasoning
  steps improve performance. → The reasoning trace is exactly the context
  compaction prunes; preserving it is a quality risk to measure.
- **ReAct: Synergizing Reasoning and Acting** — Yao et al., 2022 (ICLR 2023).
  arXiv:[2210.03629](https://arxiv.org/abs/2210.03629). The interleaved
  thought→action→observation loop. → The canonical loop our harness implements;
  the transcript that grows unboundedly.
- **Reflexion** — Shinn et al., 2023 (NeurIPS 2023).
  arXiv:[2303.11366](https://arxiv.org/abs/2303.11366). Verbal self-reflection in
  an episodic buffer. → An early "what verbal feedback to retain vs. discard"
  decision — a compaction question.
- **Toolformer** — Schick et al., 2023.
  arXiv:[2302.04761](https://arxiv.org/abs/2302.04761); **Voyager** — Wang et
  al., 2023. arXiv:[2305.16291](https://arxiv.org/abs/2305.16291). Tool use, and
  a growing skill library as a bounded-working-context strategy over long
  horizons. → Tool outputs are a major context source; Voyager's skill library is
  externalization by another name.
- **Cognitive Architectures for Language Agents (CoALA)** — Sumers et al., 2023
  (v3 2024). arXiv:[2309.02427](https://arxiv.org/abs/2309.02427). A framework
  with working / long-term / procedural memory and a decision loop. → Gives the
  precise vocabulary for *what a compaction policy moves, keeps, or evicts*.

---

## 6. Framing — "context engineering" as a discipline

The vocabulary and the practitioner case. The blog posts are **not
peer-reviewed**; cite them for framing and provenance, not for evidence.

- **A Survey of Context Engineering for Large Language Models** — Mei et al.,
  2025. arXiv:[2507.13334](https://arxiv.org/abs/2507.13334). Formalizes the
  discipline (retrieval/generation, processing, management) over 1400+ papers. →
  The best *academic* anchor for the term and our framing.
- **Effective context engineering for AI agents** — Anthropic, Sep 29 2025
  (blog). Context as "a critical but finite resource." → The practitioner
  statement of our exact problem; names compaction and note-taking directly.
- **Building Effective Agents** — Anthropic, Dec 19 2024 (blog). Workflows vs.
  agents; simple composable patterns over frameworks. → Justifies the minimal
  hand-rolled loop we study.
- **Don't Build Multi-Agents** — Walden Yan / Cognition, Jun 12 2025 (blog).
  Context engineering as "the #1 job"; multi-agent fragments context. → The
  argument for single-thread continuity and why long-running compaction matters.
- **LLM Powered Autonomous Agents** — Lilian Weng, Jun 23 2023 (blog). Planning /
  memory / tool-use decomposition. → The reference mental model; short- vs.
  long-term memory is our window-vs-scratchpad split.
- **Context engineering** — Simon Willison, Jun 27 2025 (blog); **The New Skill
  in AI is Not Prompting, It's Context Engineering** — Philipp Schmid, Jun 30
  2025 (blog). → Provenance of the term and a crisp quotable definition.

---

## 7. The gap this work fills (the positioning argument)

State this plainly in the paper's introduction; it is what makes the bake-off a
contribution rather than a tutorial:

> Prior compression work (§4) overwhelmingly (a) targets a **single static
> prompt** or **retrieved RAG passages**, (b) optimizes **inference
> efficiency/latency**, and (c) operates at the **token, activation, or KV-cache
> level**, often requiring **finetuning**. Memory-augmented agents (§3) show that
> **externalization** works but treat in-window compaction as a side concern.
> Meanwhile, the policy that actually ships in agent harnesses — **summarize the
> stale middle, keep the recent tail** — is applied at the **message/turn level**
> on an **evolving multi-turn transcript**, training-free, and is **essentially
> unmeasured against its alternatives** under an end-task metric.

Our contribution is therefore narrow and concrete:

1. **A controlled comparison** of four message-level compaction policies
   (truncate / recency-summary / importance-ranked / semantic) holding the token
   budget fixed.
2. **An objective, reproducible metric** — needle-fact recall per token —
   designed around the §2 critique that single-needle scores mislead and the §2
   evidence that LLM-judges are biased.
3. **The externalized scratchpad as control**, operationalizing the §3 insight so
   we can separate "did the *policy* preserve it" from "did the *store* preserve
   it."
4. **A finding about run-length**: where (if anywhere) the fancy policies overtake
   the cheap recency-summary default, as compaction events accumulate.

The honest expected result (worth stating up front): **externalization likely
dominates compaction-policy choice** — which would make the headline *"compaction
policy is second-order; externalize is the move that matters,"* a cleaner and
more useful claim than any single-policy win, and one fully consistent with §3.

---

## 8. Reading map — which unit reads what

| Unit | Primary read(s) | Section |
|---|---|---|
| 0 Mental model | Building Effective Agents; ReAct (2210.03629) | §5, §6 |
| 1 Window = budget | Context Rot (Chroma); skim a tokenizer explainer | §1 |
| 2 Five moves | Effective context engineering (Anthropic); Survey (2507.13334) | §6 |
| 3 Compaction internals | MemGPT (2310.08560); RECOMP (2310.04408); CoALA (2309.02427) | §3, §4 |
| 4 Lost in the middle | Lost in the Middle (2307.03172); RULER (2404.06654); NoLiMa (2502.05167) | §1 |
| 5 Evals & needles | NIAH; HELMET (2410.02694); Judging LLM-as-a-Judge (2306.05685) | §2 |
| 6 Pluggable policies | LLMLingua (2310.05736); Selective Context (2310.06201); H₂O (2306.14048) | §4 |
| 7 Experiment | Recursively Summarizing (2308.15022); Mem0 (2504.19413) | §3 |
| 8 Write-up | the §7 positioning; LongBench/HELMET for task choices | §2, §7 |
| 9 Frontier | A-MEM (2502.12110); Don't Build Multi-Agents; Memory survey (2404.13501) | §3, §6 |

---

*49 sources, each verified against its primary page in June 2026. Two are flagged
non-peer-reviewed (Chroma Context Rot; the §6 blogs). When the field moves, re-run
the verification — the [`paper.md`](paper.md) related-work section depends on these
identifiers being correct.*
