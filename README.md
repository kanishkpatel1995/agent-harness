# agent-harness

A minimal, readable agent harness built to teach one thing: **context
engineering** — how to keep a long-running agent from falling apart as its
context window fills up.

It's a deep-research agent (search → read → take notes → synthesize), but the
agent task is just an excuse. The point is the harness around the model: the
loop, the context manager, the budget, the external memory, and the trace that
makes all of it visible.

> Talk: *"Context Engineering Inside the Harness — Keeping a Long-Running Agent
> From Falling Apart."* AI Tinkerers Calgary, June 23 2026.

---

## Quickstart — run the policy comparison

Everything below runs **offline, with no API key**. Total time: ~2 minutes.

**Prerequisites:** **Python 3.10 or newer** and `git`. Check your version:

```bash
python3 --version        # must be 3.10+  (on Windows: py --version)
```

### 1. Clone the repo

```bash
git clone https://github.com/kanishkpatel1995/agent-harness
cd agent-harness
```

### 2. Create and activate a virtual environment

A virtual environment keeps these packages isolated from your system Python.

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

Your prompt should now start with `(.venv)`. (Run `deactivate` when you're done.)

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

> The offline comparison itself needs **no** dependencies — pure standard library.
> This step adds `pytest` (for the tests) and `litellm` (for running a real model
> later). To bench the open-source memory systems too, also run
> `python -m pip install -r requirements-adapters.txt`.

### 4. Run the comparison (the headline demo)

```bash
python -m harness.compare "quantum networking startups"
```

This runs **one question through all seven compaction policies** and prints a
side-by-side table — how many LLM calls each costs, the resulting window size,
whether it retrieves, and **whether a planted fact survives**:

```
  policy             architecture  llm  ctx tok  retr  fact?
  ------------------------------------------------------------
  truncate           truncate        0       47     -   ✗ lost
  recency            compact         1       70     -   ✗ lost
  importance         compact         1      138     -   ✓ kept
  semantic           compact         2       98     -   ✗ lost
  externalize        externalize     0       56   yes   ✓ kept
  subagent           isolate         6      225     -   ✗ lost
  reversible_hybrid  hybrid          1       74   yes   ✓ kept
```

See it explained two more ways:

```bash
python -m harness.compare "quantum networking startups" --verbose   # show what each policy KEPT in the window
python -m harness.compare "quantum networking startups" --story     # step-by-step: what each policy DECIDES, keeps, retrieves, and costs
```

`--story` walks one policy at a time — what it decides, what's left in the
window, what it retrieves at answer time, the cost, and whether the fact
survived — which is the clearest way to understand what each one is doing.

### 5. (Optional) Run the tests and watch one agent compact

```bash
python -m pytest -q                  # 11 offline tests
python run.py "context engineering for long-running agents"   # watch compaction live
cat run/notes.md                     # the agent's externalized memory
```

---

## Run it with a real model

```bash
cp .env.example .env          # add your API key
python run.py --real --model gpt-4o-mini "your topic here"
```

Any litellm-supported model works — swap the `--model`:

| Provider | `--model` value |
|----------|-----------------|
| OpenAI   | `gpt-4o-mini`, `gpt-4o` |
| Anthropic| `claude-3-5-sonnet-20241022` |
| Google   | `gemini/gemini-1.5-pro` |
| Local (Ollama) | `ollama/llama3.1` |

For real web search/fetch instead of offline fixtures: `HARNESS_OFFLINE=0`.

---

## Run the policies on a real dataset (FRAMES & LoCoMo)

The offline `compare` above shows the *mechanism* on a planted fact. To watch the
policies run on **real benchmark questions** with a real model and an LLM judge,
use the applied bench. These need a key in `.env` (the runs in `experiments/runs/`
used the free NVIDIA NIM tier — set `NVIDIA_FREE_API_KEY`) and are **much slower**
than the offline demos — real model calls, seconds-to-minutes per question.

Add **`--story`** to any command below for a narrated play-by-play (recommended): per
question it shows the dataset, the compaction, the chunks retrieved, the **exact input**
the model sees, the **raw output** it returns, the judge's grade, and what gets saved.
(`-vv` instead gives the raw firehose: every model call and chunk store, no narration.)

**FRAMES — multi-hop factual QA** (one question, the key policies, LLM-judged):

```bash
python -m experiments.applied --n 1 \
  --policies truncate,recency,externalize,reversible_hybrid \
  --budget 1500 --chunk-chars 1500 --judge --story
```

**LoCoMo — conversational memory:**

```bash
python -m experiments.applied.locomo_runner --n-conv 1 --q-per-conv 3 \
  --policies truncate,externalize,reversible_hybrid \
  --budget 1500 --judge --story
```

### See exactly what happens — `--story`

`--story` narrates each *(policy, question)* cell so you can follow the data end to end.
One real cell from the LoCoMo command above (the `externalize` policy):

```
┌─ policy: externalize ──────────────────────────────────────────
│ DATASET  the agent reads 19 sources (chat sessions / articles)
│   peek › Caroline: Hey Mel! Good to see you! How have you been? ...
│ COMPACT  window crossed the 1500-tok budget 17× → externalize moved the raw
│          turns to a store (90 chunks, searchable)
│   the window the model will actually see: 1504 tokens
└────────────────────────────────────────────────────

  ❓ QUESTION (from the dataset)
     Did Melanie make the black and white bowl in the photo?
     ↳ gold answer the dataset expects: "Yes"
  🔎 RETRIEVED 3 chunks from the store (this is what 'memory' pulls back):
     › ...Yeah, I made this bowl in my class. It took some work, but I'm proud ...
     › Caroline: Hey Melanie! Long time no talk! A lot's been going on ...
  📨 INPUT to llama-3.1-8b-instruct (2199 tokens go in):
     system  │ You are answering a research question using ONLY the provided ...
     context │ [the 1504-tok compacted window + 3 retrieved chunks]
     question│ Did Melanie make the black and white bowl in the photo?
  📥 OUTPUT (what llama-3.1-8b-instruct actually said, raw):
     No, Melanie did not make the black and white bowl in the photo. Caroline ...
  ⚖️  GRADE (70B judge): "No, Melanie did not make ..." vs gold "Yes"  →  ✗ WRONG
  💾 SAVED → results.csv:  correct=0 · retrieved_chars=3426 · tokens=2396
```

Read top to bottom, that *is* the experiment: **what's in the dataset → what the policy
did to the window → what it retrieved → what the model saw → what it said → how it was
graded → what was recorded.** You can even see *why* it was wrong here — retrieval pulled
chunks about a bowl, but not the one that settles the question. Every value is also saved
verbatim to the run's `prompts.jsonl` (every prompt + response) and `results.csv` (one
row per cell), so nothing on screen is lost.

**The memory-system bake-off** (swap only the store — hand-rolled NIM vs Mem0 vs
Chroma; needs `pip install -r requirements-adapters.txt`):

```bash
python -m experiments.applied --policies externalize --store nim \
  --judge --n 20 --budget 1500 --chunk-chars 1500       # then --store chroma, --store mem0
# or all three at once:
python experiments/applied/launch_exp006_memory.py
```

Each run writes a folder under `experiments/runs/EXP-NNN__…/` with a `manifest.yaml`
and a `README.md` holding the result and the strongest threat to validity.

---

## The whole idea in one picture

```
            ┌─────────────────────────────────────────────┐
            │                  THE LOOP                     │   loop.py  (~40 lines)
            │   ask model → run tools → manage context →    │
            │                  repeat                       │
            └───────┬───────────────┬───────────────┬──────┘
                    │               │               │
            ┌───────▼──────┐ ┌──────▼──────┐ ┌──────▼───────┐
            │   LLM client │ │   Tools     │ │ ContextMgr   │
            │ (any model   │ │ search/fetch│ │ pin · count  │
            │  via litellm)│ │ note/read   │ │ truncate ·   │
            │  llm.py      │ │ tools.py    │ │ COMPACT      │
            └──────────────┘ └──────┬──────┘ │ context.py   │
                                    │        └──────────────┘
                             ┌──────▼──────┐ ┌──────────────┐
                             │  Scratchpad │ │   Budget     │
                             │ memory on   │ │ steps/tokens │
                             │ disk        │ │ /$ kill sw.  │
                             │ memory.py   │ │ budget.py    │
                             └─────────────┘ └──────────────┘
                                    Trace (trace.py) wraps it all and
                                    prints the context window every step.
```

**The loop is trivial. The other files are the talk.**

---

## Read the code in this order

1. **`harness/loop.py`** — the entire agent loop. Start here. It's small on
   purpose.
2. **`harness/context.py`** — the ContextManager. Pinning, token counting,
   truncation, and compaction. This is the heart.
3. **`harness/policies/`** — the seven ways to forget, one file each, behind one
   `Policy` contract (`base.py`). Open them side by side; the trade-offs fall out
   of the diffs. `adapters/` wraps LangChain / Mem0 / Letta / Chroma behind the
   same interface.
4. **`harness/memory.py`** — the Scratchpad. Memory that lives outside the window.
5. **`harness/budget.py`** — steps/tokens/dollars caps. The kill switch.
6. **`harness/tools.py`** + **`tools/web.py`** — what the agent can do.
7. **`harness/trace.py`** — how the demo becomes visible.
8. **`harness/llm.py`** / **`harness/fake_llm.py`** — the provider-agnostic
   client and its deterministic offline twin.

See the policies forget differently in one command (offline, no key):

```bash
python -m harness.compare "quantum networking startups"   # --verbose to show what each kept
```

For a deeper module-by-module walkthrough, see [`docs/architecture.md`](docs/architecture.md);
for the guided first session, [`docs/WALKTHROUGH.md`](docs/WALKTHROUGH.md).

---

## The five context-engineering moves (and where they live)

| Move | What it does | File |
|------|--------------|------|
| **Pin** | Goal + system prompt are never dropped | `context.py` |
| **Truncate** | Oversized tool outputs are capped before entering the window | `context.py` |
| **Compact** | The stale middle is summarized and the raw turns dropped | `context.py` + `policies/` |
| **Externalize** | Findings live in a file or store, not the window | `memory.py` + `policies/store.py` |
| **Cap** | Steps, tokens, and dollars are hard-limited | `budget.py` |

*Compaction is not one move but a design space.* The seven policies in
[`harness/policies/`](harness/policies/) (truncate, recency, importance, semantic,
externalize, sub-agent, reversible hybrid) are seven answers to "what replaces the
old turns?", behind one interface. The map, the trade-off table, and where the OSS
memory systems land are in [`docs/POLICIES.md`](docs/POLICIES.md) and
[`docs/ARCHITECTURES.md`](docs/ARCHITECTURES.md).

---

## The research track: which way of forgetting is best?

The harness above teaches the moves. The `experiments/` tree measures them. It runs a
reproducible **compaction bake-off**: seven policies (truncate, recency, importance, semantic,
externalize, sub-agent, and a reversible hybrid that keeps both a summary and a retrievable raw
copy), scored by answer accuracy per token on two task types (FRAMES multi-hop QA and LoCoMo
conversational memory) across three model sizes, with a fixed LLM judge.

```bash
python -m experiments.applied -v        # the applied FRAMES/LoCoMo bake-off
python experiments/stats.py <results.csv> armA:armB    # bootstrap CIs + McNemar tests
```

Every run writes a self-contained folder (`experiments/runs/EXP-NNN__slug__UTC/`) with the
config, every prompt and response, the results, and the figure, so any number is reproducible.

- [`experiments/REGISTRY.md`](experiments/REGISTRY.md) — one row per experiment.
- [`docs/research-track/`](docs/research-track/) — the protocol, the paper draft, the literature.
- [`docs/research-track/paper/results-so-far.md`](docs/research-track/paper/results-so-far.md) — the running results synthesis.
- [`DECISIONS.md`](DECISIONS.md) — every design call we made, and every one we changed.

Headline so far: the best policy depends on the task (summarize for factual, keep the raw for
memory), the shipped default (recency summary) is dominated by plain truncation under pressure,
and the reversible hybrid is the one policy never in the loser group.

---

## Run the tests

```bash
pip install pytest
python -m pytest
```

All tests run offline with the FakeLLM. They cover pinning, truncation,
compaction (including the tool-call boundary edge case), the budget kill switch,
and a full end-to-end run.

---

## Layout

```
agent-harness/
├── run.py                  CLI entrypoint (the offline demo)
├── harness/                THE TEACHING HARNESS (read this first)
│   ├── loop.py             the agent loop (read first)
│   ├── context.py          ContextManager — pinning, compaction (the heart)
│   ├── policies/           the 7 forgetting policies, one file each, + base.py
│   │   ├── base.py         the Policy contract every arm implements
│   │   ├── store.py        the offline retrieval store (externalize/hybrid)
│   │   └── adapters/       LangChain / Mem0 / Letta / Chroma behind that interface
│   ├── compare.py          `python -m harness.compare` — 7 policies side by side
│   ├── agent.py            assembles the deep-research agent from the parts
│   ├── memory.py           Scratchpad — external memory
│   ├── budget.py           steps/tokens/$ caps
│   ├── tools.py            tool registry + schemas
│   ├── trace.py            per-step context visualization
│   ├── llm.py              provider-agnostic client (litellm)
│   └── fake_llm.py         deterministic offline model
├── experiments/            THE RESEARCH: the compaction bake-off
│   ├── applied/            FRAMES + LoCoMo runners, the 7 policies, judge, embed store
│   ├── bench/              the controlled mechanism probe (window, run-context)
│   ├── nim.py              cached, watchdog-guarded model client (free NIM API)
│   ├── stats.py            bootstrap CIs + McNemar tests
│   ├── make_figures_*.py   publication figures (figstyle.py)
│   └── runs/               one folder per run: manifest + prompts + results + figures
├── presentation/           the talk: build_deck.js, build_talk_deck.js, brand, figures
├── docs/
│   ├── WALKTHROUGH.md      guided offline first session (test → run → compare → bench)
│   ├── POLICIES.md         the 7 policies: decision · trade-off · result
│   ├── ARCHITECTURES.md    the architecture map + where the OSS systems land
│   ├── architecture.md     deeper module walkthrough
│   ├── demo-script.md      what to type and say on stage
│   ├── references.md       where to go to learn more
│   └── research-track/     protocol · curriculum · paper draft · literature
├── requirements-adapters.txt   optional deps for the OSS adapters
├── DECISIONS.md            every design call, and every one we changed
└── tests/
```

---

## Not in scope, on purpose

The **harness** is a teaching artifact: no retries-with-backoff, no parallel tool calls. You can
read the whole thing in 20 minutes and understand exactly how a long-running agent keeps its head
straight. Its core stays dependency-free: the retrieval store in `policies/store.py` is a tiny
offline keyword matcher, and the real vector stores and OSS memory systems (Chroma, Mem0, Letta,
LangChain) are **import-guarded adapters** you opt into with `requirements-adapters.txt`. The
**research track** (`experiments/`) is the full eval/bake-off that scores these policies on real
tasks. See `docs/architecture.md` for how the pieces fit.

MIT licensed. Built for Learn Agentic AI — https://learnagentic.substack.com
