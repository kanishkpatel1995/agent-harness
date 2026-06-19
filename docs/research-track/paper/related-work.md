# Related Work: How Long-Running Agents Manage Their Memory

*A narrative review for the compaction bake-off. Written to be read start to
finish, by a curious beginner as much as by a reviewer. Every number is sourced;
the full reference list is at the end. Companion to the verified bibliography in
[`../literature.md`](../literature.md).*

---

## 1. A small story about a window that fills up

Picture an agent that does research for you. It reads a question, runs a search,
opens a page, takes a note, opens another page, and keeps going until it can write
an answer. For the first five steps it looks brilliant. By the fiftieth step it
has started to repeat itself, it contradicts a decision it made earlier, and then
it stops with an error that says the context is too long.

Nothing about the model changed between step five and step fifty. What changed is
that the agent kept everything it had ever seen inside one growing list of
messages, and that list is the only memory a language model has. The model itself
is stateless. On every turn the surrounding program, which we will call the
harness, hands the model a fresh copy of that list, and the list is the agent's
entire mind for that single turn. When the list grows without bound, three things
happen at once. The cost rises, because the whole history is re-sent on every turn
and billed every time. The latency rises, because a longer prompt takes longer to
read. And the quality falls, because the model attends less well to a long input
than to a short one.

The instinct is to ask for a bigger window. That instinct is wrong, and the next
section explains why. The better question, and the question this whole field is
really about, is which slice of the past the agent should carry forward on each
turn so that it can take the next correct action without drowning in its own
history. People now call this discipline context engineering, and the single move
at its center is compaction: when the window gets too full, summarize the stale
middle of the conversation and throw the raw turns away.

This review walks through what the research community has learned about that move
and the alternatives to it. It builds toward one observation that, as far as we
can tell, no one has measured cleanly, and that observation is the reason for our
experiment.

---

## 2. Why a bigger window is not the fix

The first thing to understand is that long context is not free, and it is not even
neutral. A longer input measurably hurts accuracy, in patterns that are now well
documented.

The foundational result is **Lost in the Middle** (Liu et al., 2023). It showed
that a model retrieves a fact reliably when the fact sits near the start or the
end of a long input, and unreliably when the fact sits in the middle. Recall as a
function of position is a U shape. The practical lesson is that the middle of a
long transcript is not just expensive to keep, it is also the part the model can
least use.

The follow-up benchmarks made the picture sharper and, frankly, more alarming.
**RULER** (Hsieh et al., 2024) tested seventeen models and found that the context
length a model claims and the context length it can actually use are very
different numbers. The gap ranges from roughly one times to more than thirty times
depending on the model. **NoLiMa** (Modarressi et al., 2025) removed the easy
lexical overlap that lets a model cheat by keyword matching, and ten of twelve
models then fell below half of their short-context score by thirty-two thousand
tokens. **HELMET** (Yen et al., 2024) added the inconvenient finding that the
simple needle-in-a-haystack test does not predict downstream performance, and that
no single model wins across task categories. The Chroma group's **Context Rot**
report, which is an industry technical note rather than a peer-reviewed paper,
reached the same conclusion across eighteen frontier models: performance decays as
input grows, even on simple tasks, well before any hard limit.

A short table makes the spread concrete. The number that matters is the effective
length, meaning the longest context at which the model still performs well, which
is almost always far below the advertised window.

| Model | Advertised window | Effective length (NoLiMa) | What this tells us |
|---|---|---|---|
| GPT-4.1 | very large | about 16K | holds up best of the set |
| GPT-4o | very large | about 8K | degrades by mid-context |
| Claude 3.5 Sonnet | 200K | about 4K | strong model, short effective length |
| Llama 3.3 70B | 128K | about 2K | a sixty-fold gap to its advertised window |
| Gemini 1.5 Pro | 1M+ | about 2K | the advertised number is not the usable one |

*Source: NoLiMa, arXiv:2502.05167. Effective length is the longest context that
keeps at least 85 percent of the short-context score.*

The takeaway for a builder is blunt. Buying a larger window raises the ceiling but
does not bend the curve. The quantity that actually governs cost, speed, and
quality is the working set, meaning the tokens that are live in the window right
now, and the engineering job is to keep that working set small and relevant no
matter how long the run becomes.

---

## 3. Two ways to cope: put it somewhere else, or shrink it

Faced with a window that fills up, the field has split into two families of
solutions, and almost every real system is some blend of the two.

The first family is **externalization**. Instead of keeping information in the
window, the agent writes it to a place outside the window, a file or a database or
a vector store, and reads it back on demand. The window then holds a small working
set, and the durable record lives on disk. The intellectual ancestor of this idea
is **MemGPT** (Packer et al., 2023), which treats the context window like the RAM
of a computer and pages information to and from an external store, with the model
itself deciding what to load. Retrieval-augmented generation (Lewis et al., 2020)
is the same idea seen from a different angle: do not memorize the corpus, retrieve
the relevant piece when you need it.

The second family is **compression**, also called compaction. Here the agent
shrinks what stays in the window. The crudest version is truncation, which simply
drops the oldest turns. The version that ships in real agent harnesses is
recency-summary, which replaces the stale middle of the conversation with a short
summary and keeps the most recent turns verbatim.

A useful distinction cuts across both families, and the Redis engineering team
states it cleanly: compression can be **reversible** or **lossy**. Reversible
compaction drops text that still lives somewhere else and can be fetched back by a
later tool call. Lossy compaction destroys whatever does not make it into the
summary. Hold on to this distinction, because the novel method we propose lives
exactly on the line between the two.

---

## 4. The compression family, organized

Compression has a long and somewhat scattered literature, because researchers have
attacked it at four different levels of the stack. It helps to see them side by
side, since a practitioner choosing a method is really choosing a level.

| Level | Representative work | What it does | Reversible? | Needs training? |
|---|---|---|---|---|
| Token-level pruning | LLMLingua, LongLLMLingua, Selective Context | drop low-information tokens from the text | no | no |
| Learned latent | Gist Tokens, ICAE, AutoCompressors | encode the prompt into a few learned vectors | no | yes |
| KV-cache / attention | StreamingLLM, H2O, Landmark Attention | keep or evict entries in the attention cache | varies | no |
| Message / turn level | recency-summary, recursive summary, ACON | summarize whole turns of an agent transcript | no, unless paired with a store | usually no |

Two observations matter for us. First, the great majority of this work optimizes
for inference efficiency, meaning speed and dollars on a single static prompt or a
batch of retrieved passages, and not for the success of a multi-step agent.
Second, the message level, which is exactly where agent harnesses operate, is the
least studied of the four. The recency-summary policy that runs inside Claude
Code, inside LangChain, and inside our own teaching harness has almost never been
measured against its alternatives on a real task. That absence is the seed of our
contribution.

A few token-level results are worth keeping in mind as anchors. LLMLingua (Jiang
et al., 2023) reports up to twenty times compression with small loss on a static
prompt. LongLLMLingua adds question-aware reordering to fight lost-in-the-middle
and reports a twenty-one percent accuracy gain on Natural Questions at four times
fewer tokens. These are strong numbers, but note the caveat that appears again and
again: token-dropping works well on prose and poorly on structured tool output,
where deleting a few tokens can break the structure the next tool call depends on.

---

## 5. Memory-augmented agents, and the results they report

The memory papers are the closest thing the field has to a measured comparison,
because each one reports an end-task number against a baseline. They are also our
most direct baselines, so their results deserve a table of their own.

| System | Benchmark | Headline result | The lesson it teaches |
|---|---|---|---|
| MemGPT (2023) | multi-session recall | paged memory 92.5 percent vs naive summary 32.1 percent | naive summarization destroys task success |
| Mem0 (2025) | LoCoMo conversations | 66.9 vs full-context 72.9, at about 90 percent fewer tokens | good compaction nearly matches full context, far cheaper |
| A-MEM (2025) | LoCoMo multi-hop | roughly double the F1 of MemGPT, at a fraction of the tokens | linked, structured notes beat flat summaries |
| SCM (2023) | long dialogue QA | 77 percent accuracy by storing both raw text and a summary | the reversible hybrid works, but is untested as one agent policy |

Read together, these results tell a coherent and slightly surprising story. Good
compaction repeatedly reaches close to full-context accuracy while spending a
fraction of the tokens, which is the quality-versus-cost win that motivates the
whole enterprise. At the same time, bad or naive compaction is genuinely
destructive: the ninety-two versus thirty-two split for MemGPT is the single most
important cautionary number in this literature. The difference between those two
worlds is the policy, which is precisely the variable our work isolates.

One paper in this group deserves a second look, because it foreshadows our novel
method. **SCM**, the Self-Controlled Memory framework (Wang et al., 2023), stores
each memory item as both its raw content and a summary, and decides per query
whether to inject the full text or only the summary. That is reversible compaction
in spirit. What no one has done, and what we will do, is lift that idea into a
single in-agent compaction policy and measure it head to head against a
summary-only policy on the same task.

---

## 6. How real research agents actually do it

Step out of the papers and into the products, and a striking thing appears. There
are now more than a dozen serious deep research agents, every one of them solves
the same problem of a run that reads more than fits in a window, and every one of
them commits to a different technique. None of them publishes a comparison that
would tell you whether their choice is the right one. They fall into three camps.

The first camp uses **multi-agent isolation**, which means the system compresses by
giving each subtopic its own fresh window. Anthropic's research system is the
clearest example. Its own engineering write-up says, in plain words, that
subagents facilitate compression by operating in parallel with their own context
windows and condensing the most important tokens for the lead agent. The same
write-up reports that this design beats a single agent by ninety percent on their
internal evaluation, but also that it uses about fifteen times more tokens than a
chat, and that token usage alone explains eighty percent of the variance in their
benchmark. LangChain's Open Deep Research, the deepagents library, and Stanford's
STORM all sit in this camp.

The second camp leans on **long context with a retrieval fallback**. Google's
Gemini Deep Research keeps everything in a very large window and falls back to
retrieval only when the window fills. OpenAI's Deep Research is a single
reinforcement-learned agent that reasons in context. GPT Researcher writes scraped
text to a vector store and retrieves it. Perplexity iterates search and read and
reason.

The third camp uses a **file system or a distilled state**. Manus, whose
engineering blog is the most candid first-person account of context engineering in
production, treats the file system as unlimited external memory and rewrites a
running todo list to keep the plan in the model's recent attention. The minimalist
open repositories, such as Jina's and dzhng's, skip almost everything and simply
carry a compact list of learnings forward, never the raw transcript.

| Agent | Primary technique | Open or closed |
|---|---|---|
| Anthropic Research | multi-agent isolation, subagents return short summaries | closed |
| LangChain Open Deep Research | multi-agent isolation, finding pruning, no RAG | open |
| deepagents | planning, subagents, virtual file system, summarization | open |
| GPT Researcher | vector store plus per-source summarization | open |
| Stanford STORM | multi-perspective questions, outline-first, mind map | open |
| Gemini Deep Research | very long context plus retrieval fallback | closed |
| OpenAI Deep Research | single reinforcement-learned agent, in-context reasoning | closed |
| Manus | file system as memory plus todo recitation | closed |
| Jina, dzhng | carry-forward distilled state, token budget loop | open |

The pattern is the headline. Each system makes a context decision and ships it.
Not one of them measures whether a different decision would have done better on the
same task with the same budget. That is a product reality, not a criticism. It is
also a gap a research project can fill.

---

## 7. The argument no one has settled

Underneath the landscape sits a genuine and public disagreement, and it is worth
stating clearly because our experiment is designed to resolve a piece of it.

On one side, Anthropic argues that subagents are a form of compression and that
parallel exploration with isolated windows is the right way to scale a research
agent. On the other side, Cognition, the team behind Devin, published a piece
titled "Don't Build Multi-Agents" arguing the opposite. Their concern is that when
you split work across parallel agents and then compress each agent's output up to a
coordinator, you drop the implicit decisions that each agent made, and the agents
then build on conflicting assumptions. Their recommended alternative is to keep one
continuous thread and to compact it with a dedicated, fine-tuned compaction model.

The most honest voice in this debate is Anthropic itself, which in a later post on
long-running agents writes that it is still unclear whether a single
general-purpose agent or a multi-agent architecture performs best, and that
compaction on its own is not sufficient.

Now here is the part that turns an argument into a research opportunity. Several
careful studies have compared multi-agent systems against single-agent systems
under controlled conditions. Kim et al. (2025) ran two hundred and sixty
configurations. Tran and Kiela (2026) held the token budget equal. LangChain ran a
controlled benchmark. In every one of these studies, the single-agent baseline is
a plain agent with no context engineering, meaning it simply receives a polluted
window. No study compares multi-agent isolation against a single agent that has
been properly engineered with compaction, on the same task and model, with cost
held equal. That specific cell of the comparison table, the one on which the entire
Anthropic-versus-Cognition disagreement actually rests, is empty. We can fill it.

---

## 8. The finding that reframes the whole question

If the review stopped at the previous section, you would expect the experiment to
produce a single ranking of policies. The most important thing we learned while
preparing this work is that a single ranking would be a mistake, because the best
policy depends on the model.

The evidence here is strong and converges from several directions. We already saw
in section two that the effective context length varies by more than thirty times
across model families at the same advertised window. The value of compaction
varies the same way. The ACON paper (2025) applies the same compression method
across model sizes and finds that small models gain as much as forty-six percent
from compression, because they degrade with length faster and benefit most from
having distraction removed, while large models stay roughly flat. A separate
characterization study states it directly: a seventy-billion-parameter model is
much less sensitive to compression than an eight-billion-parameter model.

The sharpest result is about transfer. A cross-backbone evaluation of memory
methods found that the relative ranking of methods changed for about seventy
percent of the models tested, and concluded that the best method depends on the
backbone model chosen. Prompt compression shows the same effect from the other
side: LongLLMLingua finds that a stronger target model tolerates a more aggressive
compression ratio, while a weaker model breaks earlier.

Reasoning models add a third dimension. A model like DeepSeek-R1 holds long context
better than its non-reasoning peers on RULER, yet a study of memory drift finds
that even a reasoning model like o1 remains vulnerable to forgetting early
information in a long, noisy context. Reasoning models also fill the window faster,
because their chains of thought are long, so they reach the point where compaction
is needed sooner. This means compaction is more valuable for a reasoning agent and
also more dangerous, because truncating a transcript can sever a chain of reasoning
midway.

| Axis | What changes with the model | Strongest evidence |
|---|---|---|
| Family | effective length ranges from 1x to over 30x the gap to advertised | RULER, NoLiMa |
| Size | small models gain up to 46 percent from compaction, large models flat | ACON, 2407.08892 |
| Method transfer | best method changes for about 70 percent of backbones | cross-backbone memory eval |
| Reasoning | reasoning models hit the wall sooner and risk losing chain-of-thought | RULER, memory-drift 2510.03611 |

We treat this as the central design lesson rather than a footnote. It means that
the question "which compaction policy is best" is malformed. The well-formed
question is "which compaction policy is best for which model," and the answer is a
decision map rather than a single winner. That reframing is both more useful to an
engineer, who runs a specific model, and more interesting to a researcher, because
the claim that a context strategy does not transfer across model classes is
contrarian and, if it holds, genuinely worth publishing.

---

## 9. The gap, stated plainly

We can now say exactly what is missing, and therefore what we will provide.

Prior compression work optimizes a static prompt for latency, at the token or
cache level, often with training. Memory agents prove that externalization helps
but treat in-window compaction as a side detail. The shipped research agents each
choose one strategy and never compare. The multi-agent-versus-compaction debate is
argued from architecture intuition, and its controlled comparison has never been
run. And underneath all of it, the best policy depends on the model, yet no study
sweeps the model as a variable.

What does not exist anywhere in this literature is a single, open, reproducible
harness that takes the same agent, the same task, and the same token budget, swaps
the context policy across all the camps described above, sweeps the model across
sizes and families and reasoning styles, and reports end-task success against cost.
That object is what we are building. The next document, the methodology, specifies
it in full.

---

## 10. Where our work sits, and what we add

It is worth being honest about what we are not doing. We are not building a
research agent that outperforms LangChain's or OpenAI's. They have more engineering
and stronger models, and a claim that we beat them would not survive scrutiny.

What we add is the measurement layer that the field is missing, plus one new
method. Concretely, our contribution has four parts.

First, a controlled bake-off that brings every camp under one roof as a swappable
policy: truncation, recency-summary, importance ranking, semantic clustering,
externalization, retrieval, sub-agent isolation, and a new reversible hybrid.

Second, a metric that engineers care about, namely answer accuracy per token on a
real research task, reported as a quality-versus-cost frontier rather than a single
score.

Third, the model treated as a swept axis, which converts a possibly mushy ranking
into a decision map and lets us test directly whether the best policy transfers
across models.

Fourth, a new policy, the reversible hybrid, which summarizes the stale middle into
the window and at the same time indexes the exact raw span to a store so the agent
can fetch it back if a later step needs it. The pieces exist separately in SCM and
in the memory systems, but no one has isolated this as a single in-agent policy and
measured it head to head against a summary-only policy. If reversible compaction
recovers the accuracy that lossy compaction loses, while keeping most of the token
savings, that is a clean and useful result.

Our earlier needle-recall experiments, which measured whether a planted fact
survives a single compaction event, are not replaced by any of this. They become
the mechanism layer that explains the impact layer. The needle work tells us why a
policy preserves information; the bake-off tells us whether that preservation
translates into answering more questions correctly per dollar. The two together are
the spine of the paper.

---

## References

Grouped by role. Identifiers verified against primary pages in June 2026. The
working bibliography with one-line annotations is in [`../literature.md`](../literature.md).

**Long context degrades**
- Lost in the Middle, Liu et al., 2023. arXiv:2307.03172
- RULER, Hsieh et al., 2024. arXiv:2404.06654
- NoLiMa, Modarressi et al., 2025. arXiv:2502.05167
- HELMET, Yen et al., 2024. arXiv:2410.02694
- Context Rot, Chroma, 2025 (industry report). research.trychroma.com/context-rot

**Compression methods**
- LLMLingua, Jiang et al., 2023. arXiv:2310.05736
- LongLLMLingua, Jiang et al., 2023. arXiv:2310.06839
- Selective Context, Li et al., 2023. arXiv:2310.06201
- Gist Tokens, Mu et al., 2023. arXiv:2304.08467
- StreamingLLM, Xiao et al., 2024. arXiv:2309.17453
- H2O, Zhang et al., 2023. arXiv:2306.14048
- ACON, 2025. arXiv:2510.00615
- Context-Folding, 2025. arXiv:2510.11967
- Recursive Summarization, Wang et al., 2023. arXiv:2308.15022

**Memory-augmented agents**
- MemGPT, Packer et al., 2023. arXiv:2310.08560
- Mem0, Chhikara et al., 2025. arXiv:2504.19413
- A-MEM, Xu et al., 2025. arXiv:2502.12110
- SCM (Self-Controlled Memory), Wang et al., 2023. arXiv:2304.13343
- MemoryBank, Zhong et al., 2023. arXiv:2305.10250
- Retrieval-Augmented Generation, Lewis et al., 2020. arXiv:2005.11401
- MEM1, 2025. arXiv:2506.15841

**Research agents and the architecture debate**
- Anthropic, How we built our multi-agent research system. anthropic.com/engineering/built-multi-agent-research-system
- Cognition, Don't Build Multi-Agents. cognition.ai/blog/dont-build-multi-agents
- Anthropic, Effective context engineering for AI agents. anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Anthropic, Effective harnesses for long-running agents. anthropic.com/engineering/effective-harnesses-for-long-running-agents
- LangChain, Open Deep Research. langchain.com/blog/open-deep-research
- deepagents. github.com/langchain-ai/deepagents
- GPT Researcher. github.com/assafelovic/gpt-researcher
- Stanford STORM, 2024. arXiv:2402.14207
- Manus, Context Engineering for AI Agents. manus.im/blog
- Kim et al., Science of Scaling Agent Systems, 2025. arXiv:2512.08296
- Tran and Kiela, Single-Agent under Equal Token Budgets, 2026. arXiv:2604.02460

**Model and reasoning dependence**
- Characterizing Prompt Compression Methods, 2024. arXiv:2407.08892
- Memory drift in reasoning models, 2025. arXiv:2510.03611
- TokenSkip (reasoning compression), 2025. arXiv:2502.12067
- Chain of Draft, 2025. arXiv:2502.18600

**Evaluation datasets**
- FRAMES, Google, 2024. arXiv:2409.12941
- LoCoMo, Maharana et al., 2024. arXiv:2402.17753
- tau2-bench, Sierra, 2024. arXiv:2406.12045
- Judging LLM-as-a-Judge, Zheng et al., 2023. arXiv:2306.05685

**Practitioner framing**
- A Survey of Context Engineering for LLMs, Mei et al., 2025. arXiv:2507.13334
- Redis, Context Compaction guide. redis.io/blog/context-compaction
