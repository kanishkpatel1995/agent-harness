# Talk — June 22 · ≤10 minutes

**Title:** Context Engineering Inside the Harness — Keeping a Long-Running Agent
From Falling Apart
**Speaker:** Kanishk Patel · Founsi AI · Learn Agentic AI
**Room:** AI Tinkerers — builders, technical, no-pitch. They want messy, real,
reproducible.

## The design brief (your words)

> *"Good storytelling. Take them from zero to one. Go in depth, depth, and
> depth."*

So this is **not** the survey-of-five-moves deck. It's a **depth-first story**:
one problem, one insight, one mechanism shown *deeply* and *live*, ending by
opening the research door. Breadth is the enemy here. We go deep on **compaction**
— the heart — and let the other four moves be scenery.

The spine: **Problem → Reframe → Mechanism (deep) → See it live → The open
question.** That last beat is what makes it "zero to one" — you don't just teach
a solved thing, you hand them the edge of the unknown.

---

## The one sentence they leave with

> **The model is a commodity you rent. The harness — what it sees, what it
> remembers, when it stops — is the part you build.**

Say it twice: once at the reframe (~slide 4), once to close. Everything else
serves it.

---

## Timing budget (target 9:30, hard cap 10:00)

| # | Slide | ⏱ | Running |
|---|---|---|---|
| 1 | Title | 0:15 | 0:15 |
| 2 | Cold open — the agent that dies | 1:00 | 1:15 |
| 3 | Why it dies — the window is a budget | 0:50 | 2:05 |
| 4 | The reframe + the one sentence | 0:30 | 2:35 |
| 5 | Mental model — the list IS the mind | 0:45 | 3:20 |
| 6 | The map — five moves, one matters tonight | 0:35 | 3:55 |
| 7 | Compact, deeply (the heart + the gotcha) | 1:25 | 5:20 |
| 8 | 💻 LIVE DEMO | 2:30 | 7:50 |
| 9 | Zero-to-one — the open question I'm chasing | 0:55 | 8:45 |
| 10 | Swap the brain | 0:20 | 9:05 |
| 11 | Close + clone | 0:25 | 9:30 |

Demo is the shock absorber: if you're behind, cut it to 2:00; if ahead, let the
compaction moment breathe. Never let the *talking* slides run long to compensate.

---

## Slide-by-slide

### 1 — Title · 0:15
Syne title, name, "Founsi AI · Learn Agentic AI", date. Subtitle: *Keeping a
long-running agent from falling apart.*
🎙 "I build a daily AI newsletter and an AI product. Tonight: the unglamorous code
that keeps an agent working for 50 steps instead of 5."

### 2 — Cold open: the agent that dies · 1:00
**Don't open with theory. Open with a corpse.** A short clip or a frozen terminal
of an agent that's drifting — repeating a tool call, re-asking what it already
knew, then a red `context_length_exceeded`.
🎙 "Here's an agent. Five steps in, it's brilliant. Fifty steps in, it's
repeating itself, it's forgotten its goal, and then — it just dies. Same model.
Same code. What changed? Nothing changed *in the model*. Something filled up."
**Beat. Let the death land.** This is the hook; everything pays it off.

### 3 — Why it dies: the window is a budget · 0:50
One chart: steps → up, three lines climbing (cost, latency) and one falling
(quality). Label the quality dip "lost in the middle."
🎙 "We picture the context window like a backpack you fill. Wrong. The model is
stateless — every turn you re-send the *entire* history. So a 50-step run pays for
its history fifty times. Cost climbs, latency climbs, and attention spreads thin —
models read the middle of a long context worst. It's not a backpack. It's a
budget you blow."

### 4 — The reframe + the one sentence · 0:30
Big text, mostly empty slide.
🎙 "So the fix isn't a bigger window — that just raises the ceiling, it doesn't
bend the curve. The fix is to *engineer what the model sees every turn.* That
engineering is the harness. **The model is a commodity you rent. The harness is
the part you build.**"

### 5 — Mental model: the list IS the mind · 0:45
A diagram: stateless model in the middle; every turn the harness hands it a
freshly-built `messages` list.
🎙 "Here's the whole mental model. The model remembers nothing. Every turn, the
harness rebuilds one list of messages and hands it over — and *that list is the
agent's entire mind* for that turn. If the agent forgot its goal, the goal wasn't
in the list. There's no magic. There's just: what do we put in the list?"

### 6 — The map: five moves, one matters tonight · 0:35
The five moves as a quiet list — pin, truncate, compact, externalize, cap — with
**compact** highlighted, the rest dimmed.
🎙 "There are five levers for building that list well. Pin the goal so it's never
lost. Truncate giant tool outputs. Externalize memory to disk. Cap the spend. I
could give a talk on each. Tonight I go deep on the one that does the real work —
**compaction** — because it's where agents live or die."

### 7 — Compact, deeply · 1:25
Show the actual `maybe_compact` + `_safe_split_index` code, highlighted.
🎙 "When the window crosses a threshold, compaction summarizes the *stale middle*
of the conversation into one dense note and throws the raw turns away. Why the
middle? Remember slide 3 — the middle is the low-attention zone anyway. We're not
losing good information; we're removing what the model had mostly stopped reading,
and dropping a tight summary into a spot it reads well."
**The gotcha (20s, this earns credibility):**
🎙 "One real trap. A tool *result* only makes sense right after the assistant
message that *called* it. Cut between them and you've made a transcript that real
APIs reject. This little function nudges the split so that never happens. Ten
fiddly lines — and the difference between a demo and a crash."
🎙 "And compaction *destroys* information — on purpose. That's only safe because
the important findings were already written to disk. The summary is a pointer; the
file is the truth. Watch."

### 8 — 💻 LIVE DEMO · 2:30
Slides recede. Terminal takes over. (Full script:
[`../demo-script.md`](../demo-script.md).)
1. `python run.py "context engineering for long-running agents"` — narrate the
   bar: "purple is pinned and never moves; cyan is working history, climbing…"
2. **The money moment:** `⚙ COMPACTED` fires, bar snaps back, agent keeps going.
   🎙 "There. It hit the threshold, summarized, snapped back down — and kept
   working. *That* single event is 5 steps versus 50."
3. `cat run/notes.md` — "compaction threw away the raw pages, but nothing's lost:
   the findings are here, on disk, outside the window. That's why throwing things
   away is safe."
**Offline. Record a GIF backup (Unit countdown, Jun 21) in case of stage gremlins.**

### 9 — Zero-to-one: the open question · 0:55
**This is the "to one" beat — hand them the edge of the unknown.** A slide with
the four policies and a blank Pareto plot axis (quality vs. cost).
🎙 "Here's where it stops being a tutorial and starts being research. Compaction
is lossy — so *which* way of forgetting loses the least? Just truncate? Summarize
by recency, like I just showed? Rank by importance? Cluster by topic? Nobody in my
repo measured it — so I'm measuring it. I plant checkable facts in the sources and
count how many survive each strategy, per token spent. I don't have the answer
yet. That's the point — I'm showing you the question while it's still open."

### 10 — Swap the brain · 0:20
One flag, four model names (Claude / GPT / Gemini / local Llama).
🎙 "And all of this is provider-agnostic — one flag swaps Claude for GPT for a
local Llama. The brain is rented. The harness is yours."

### 11 — Close + clone · 0:25
QR to the repo. The one sentence, big.
🎙 "Clone it tonight — it runs with no API key. **The model is a commodity you
rent. The harness is the part you build.** I'm Kanishk, I write this up daily at
Learn Agentic AI, find me after. Thanks."

---

## Founsi placement (the no-pitch room)

Keep it to *one breath* and frame Founsi as **what you build**, not what they
should buy. Best slot: a half-sentence on slide 1 ("I build an AI product")
and/or slide 11. Do **not** add a product slide to a 10-minute depth talk — it
breaks the story and the room will feel the pitch. The talk earns any plug by
being useful first.

---

## Rehearsal checklist (Jun 21)

- [ ] Full run with a timer. Target **9:30**. If over 10:00, cut from slides 5–7,
      never from the demo or the cold open.
- [ ] Demo run clean **3×** in a row. `python -m pytest -q` green beforehand.
- [ ] GIF backup of the demo recorded and embedded as slide 8 fallback.
- [ ] The one sentence said out loud until it's muscle memory.
- [ ] Cold open (slide 2) practiced most — if the hook lands, the rest carries.
- [ ] Q&A prep skimmed (see the main presentation plan's Q&A section).

## Why this beats the survey version

A 10-minute talk that touches all five moves equally gives the room *five shallow
things they'll forget*. This version gives them **one deep thing they'll
remember** (compaction, watched live) plus **one open question they might go solve
themselves** (the bake-off). Depth + an open door beats a checklist every time —
especially in a builders' room that came to see something real.
