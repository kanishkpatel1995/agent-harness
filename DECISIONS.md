# Decisions and trade-offs

The interesting part of this project is not the code, it is the decisions, and the times a
decision was wrong and had to change. This file is the running log: each entry is the context,
the call we made, and what it cost. Plain language, no em-dashes. It is also the spine of the
talk (see `docs/research-track/talk/codebase-tour.md`).

---

### 1. The window is a budget, not a backpack
**Context.** A stateless model gets one message list per turn, and it only grows.
**Decision.** Do not wait for the hard limit. Compact at 75% of budget (`context.py`,
`compact_at = 0.75`) and keep the working set roughly constant for the whole run.
**Trade-off.** You throw information away earlier than you strictly must. That is the point, and
EXP-002 shows it is net positive: a short clean summary beats a long raw context past the
crossover, so compacting early helps accuracy, not just survival.

### 2. Pin the goal, forget the middle
**Decision.** Two messages, the goal and the system prompt, are pinned and never summarized or
dropped (`context.py`). Compaction targets the stale middle, the low-attention zone (lost in the
middle), and keeps the most recent turns verbatim.
**Trade-off.** Mid-conversation detail is the first to go. Acceptable because the agent rarely
needs the exact wording of step 12 at step 40, and what it does need was externalized.

### 3. Never split a tool-call from its result
**Context.** Compaction cuts the transcript at a chosen index.
**Decision.** `_safe_split` (`experiments/bench/window.py`) walks the boundary so the kept tail
never starts on an orphan `tool` message.
**Trade-off.** The split point is constrained, you cannot always cut exactly at the budget line.
Non-negotiable: a real tool-calling API rejects a transcript where a result has no preceding
call. This five-line function is the difference between an agent that runs and a 400 error.

### 4. A policy is a tiny swappable class
**Decision.** Every compaction policy is one class with one method,
`compact(old, llm, store) -> (block, usage)`, plus a `retrieves` flag
(`experiments/applied/policies.py`). Seven of them live in one `POLICIES` registry.
**Trade-off.** A fixed interface limits how clever any single policy can be. Worth it: the agent
does not know which policy it runs, so all seven are measurable head-to-head. The benchmark only
exists because of this.

### 5. Externalize before you forget
**Context.** Compaction is lossy on purpose.
**Decision.** Findings are written to an external store or scratchpad before the raw turns are
dropped (the `externalize` and `reversible_hybrid` policies; the demo's `run/notes.md`).
**Trade-off.** Extra moving part (a store, retrieval at answer time). It is what makes lossy
compaction safe: the window forgets, the agent does not.

### 6. The metric must credit paraphrase
**Context.** First scoring pass used a normalized substring match.
**Decision.** Switch to an LLM judge that credits a correct but reworded answer
(`experiments/applied/judge.py`), held constant across every arm and model.
**Trade-off.** Judges carry their own biases and cost a model call per cell. But substring made
the best policy look worst (0.21) and the judge flipped it to best (0.62). A careless metric
inverts the ranking, so the judge is not optional.

### 7. A hard wall-clock watchdog, because the timeout lied
**Context.** Runs hung forever. Python at 0% CPU, no error, past the library timeout.
**Decision.** Run every model call on a worker thread bounded by `future.result(timeout=...)`
(`experiments/nim.py`, `_completion_with_deadline`). A wedged socket now raises instead of
freezing the study.
**Trade-off.** An orphaned thread can leak until its connection drops. Acceptable for a bounded
run, and far better than a silent multi-hour freeze. Lesson: do not trust a library's timeout.

### 8. Reasoning models are bad compactors
**Context.** Tried a reasoning model as the summarizer for the reasoning tier.
**Decision.** Use a split summarizer: a fast instruct model writes the compaction summaries, the
reasoning model only produces the final answer (`agent.py` `summarizer_llm`, runner
`--summarizer`).
**Trade-off.** The summarizer is then a different model from the answerer on that tier. We tried
the alternatives first: self-summarizing was prohibitively slow (single cells stalled past 200
seconds, summaries of 2k to 20k tokens), and turning thinking off corrupted the summaries.

### 9. Hold the summarizer constant, even when it hurts
**Context.** The 70B headline was that the reversible hybrid won at 0.67.
**Decision.** Re-run the 70B tier with the same fast 8B summarizer the other tiers use, so the
answer model is the only variable.
**Trade-off.** The hybrid's 70B number drops to 0.53 and semantic takes the lead. The original
win was partly the summarizer, not the answer model. We report the worse, honest number. Lesson:
isolate your variable.

### 10. Compact once, answer many
**Context.** Conversational memory (LoCoMo) asks many questions of one long conversation.
**Decision.** Factor the agent into `read_and_compact` (compact the conversation once) and
`answer_from_window` (answer each question from the compacted window), in
`experiments/applied/agent.py`, shared with the FRAMES path.
**Trade-off.** A small refactor of the single-question path. It models the realistic case and
keeps both domains on one compaction implementation.

### 11. Reproducible by construction
**Decision.** Every run writes `experiments/runs/EXP-NNN__slug__UTC/` with a manifest (config,
git sha, deps), every prompt and response, the results CSV, and the figures
(`experiments/bench/run_context.py`). The bar: a stranger clones the repo and regenerates any
figure.
**Trade-off.** More files, slightly more ceremony per run. It is the reason every number in the
paper is checkable.

### 12. A whole study on zero dollars
**Decision.** Run on the free NVIDIA NIM API with a paced, backed-off, cached client
(`experiments/nim.py`); the response cache makes re-runs free, and runs are detached, caffeinated,
and auto-resuming so a multi-hour sweep survives a sleep or a crash.
**Trade-off.** Rate limits and dev-scale models, not frontier ones. Resourceful infra beats a
budget for getting the signal; the frontier-model tier is the planned upgrade.

### 13. Report the negatives
**Decision.** State the results that do not flatter the project: the shipped default (recency
summary) is Pareto-dominated by truncation; sub-agent isolation is a 5x cost trap; the novel
hybrid is not the single best policy in every cell.
**Trade-off.** A less triumphant story. A more trustworthy one, and the negatives (the default is
weak, multi-agent is expensive here) are the most useful findings for anyone running agents.
