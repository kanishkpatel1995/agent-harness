# Run it & understand it — a guided first session

Everything here runs **offline, no API key** (a deterministic FakeLLM stands in
for a real model). Do it in your terminal, or open the repo in **Claude Code** and
ask it the prompts at the bottom as you go.

```bash
cd ~/Desktop/agent-harness
python -m venv .venv && source .venv/bin/activate   # optional
pip install -r requirements.txt                     # core only; adapters are separate
```

## Step 1 — prove it works (10 seconds)
```bash
python -m pytest -q
```
11 tests, all offline. They cover pinning, truncation, compaction (incl. the
tool-call boundary), the budget kill-switch, and a full end-to-end run. Green =
the harness works on your machine.

## Step 2 — watch one agent run and compact (the mechanism)
```bash
python run.py "context engineering for long-running agents"
```
Watch the per-step trace: the context bar climbs, crosses the threshold, prints
`⚙ COMPACTED`, and snaps back down — while the agent keeps going. Then look at
what it externalized:
```bash
cat run/notes.md
```
**What to understand here:** compaction is lossy, but nothing important was lost
because the findings were written to disk. That's the whole safety argument.

## Step 3 — compare the seven policies side by side (the payoff)
```bash
python -m harness.compare "quantum networking startups"
python -m harness.compare "quantum networking startups" --verbose   # show what each kept
```
One planted fact, seven policies. Watch truncate drop it, summaries blur it, the
sub-agent fan-out cost the most and *still* lose it, and externalize + the hybrid
recover it. `--verbose` prints the actual window each policy produced — that's the
"how it's coded" made visible.

## Step 4 — the research results
The bench that produced the paper numbers lives in `experiments/`. The offline
mechanism layer:
```bash
python -m experiments.bench -vv        # full step-by-step logs
```
The applied FRAMES/LoCoMo arms call a real model (free NVIDIA NIM) — set that up
later. For now the computed results + figures are in:
```
experiments/runs/EXP-*/README.md       # hypothesis + result + threat per run
presentation/figures/                  # the plots
```

## The reading order (what to open, in order)
1. `harness/loop.py` — the ~40-line agent loop. The one `maybe_compact` call.
2. `harness/context.py` — the ContextManager: pin · truncate · compact (`_safe_split`).
3. `harness/policies/base.py` — the one interface every policy implements.
4. `harness/policies/{truncate,recency,importance,semantic,externalize,subagent,hybrid}.py`
   — open them side by side; the trade-offs fall out of the diffs.
5. `harness/policies/adapters/` — how LangChain / Mem0 / Letta / Chroma wrap behind
   that same interface.
6. `docs/ARCHITECTURES.md` — the map tying it all together (and the OSS systems).

## Good prompts to ask Claude Code
- "Walk me through `harness/loop.py` line by line — what is each step doing?"
- "In `context.py`, explain `maybe_compact` and why `_safe_split` exists. Show me what breaks without it."
- "Open the seven files in `harness/policies/` and explain how each `compact()` differs. Why is `hybrid` just two of the others composed?"
- "Run `python -m harness.compare` and explain why each policy keeps or loses the planted fact."
- "I want to add the LangChain summary-buffer as a real bench arm — how do `harness/policies/adapters/langchain_summary.py` and the bench fit together?"
- "Trace one FRAMES question through `experiments/applied/` — runner → policy → judge."

## Going further (needs setup)
- Real model: `python run.py --real --model gpt-4o-mini "..."` (put a key in `.env`).
- OSS adapters: `pip install -r requirements-adapters.txt`, then wire one arm into the bench.
