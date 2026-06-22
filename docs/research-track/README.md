# Research Track — from 101 to a small paper

This folder is a **course**. It takes one person (you, Kanishk — but written so it
works for anyone) from "what is a context window" to "I ran an experiment,
measured it, and wrote it up." The vehicle is this repo's compaction code; the
destination is a small, defensible empirical result.

It exists for three reasons at once, and you should keep them separate in your
head:

| Deliverable | What it is | File | Deadline |
|---|---|---|---|
| **The talk** | A ≤10-min storytelling showcase: zero-to-one, depth-first | [`talk-june22.md`](talk-june22.md) | **June 22** |
| **The curriculum** | The 101→research learning arc (readings, code, tasks, gates) | [`curriculum.md`](curriculum.md) | ongoing |
| **The paper** | The compaction bake-off — design, method, what to build | [`paper.md`](paper.md) | the destination |
| **The literature** | Verified, annotated survey + the gap our work fills | [`literature.md`](literature.md) | the grounding |

The talk is a *slice* of the curriculum (Units 0–3 + a teaser of the paper). The
paper is what the *whole* curriculum builds toward. The curriculum is the rails.
The literature ([`literature.md`](literature.md)) is what keeps it honest — 49
sources, every arXiv ID verified against its primary page, organized so each
curriculum unit knows exactly what to read.

---

## The North Star (memorize this)

> **The model is stateless. The harness rebuilds the context window every turn.
> That list is the whole game.**

Everything in this track is a consequence of that one sentence. The five moves
(pin, truncate, compact, externalize, cap) are just *tactics* for deciding what
goes in the list. The research question — "which compaction strategy loses the
least per token?" — is just that sentence, made measurable.

---

## The research question we're chasing

When a long-running agent must compact its context, **which compaction *policy*
best preserves end-task quality per token spent?**

The repo ships exactly one policy today: *recency summary* — summarize the stale
middle, keep the last N turns verbatim ([`context.py:113`](../../harness/context.py:113)).
Is that the right call? Nobody in this repo has measured it. That gap is your
paper. We compare it against three rivals:

1. **Truncate** — just drop the oldest turns, no summary. The dumb baseline.
2. **Recency summary** — what the repo does now.
3. **Importance-ranked** — keep/summarize selectively by how "factual" a turn is.
4. **Semantic** — cluster the evicted middle by topic, summarize per cluster.

And we measure them with an objective, offline, reproducible trick: **planted
needle-facts**. See [`paper.md`](paper.md). That design is the intellectual core
of the whole track — if you only read one file deeply, read that one.

---

## How to use these rails (the method, not just the content)

This is how a researcher actually learns, compressed into a loop you repeat
every unit:

1. **Read** the assigned source — but with a question in hand, not passively.
2. **Study the code** it maps to in *this* repo. Theory you can't point at in
   running code is theory you don't own yet.
3. **Build** the small task. Writing the code is where the understanding lands.
4. **Pass the gate** — a one-sentence test of "do I actually get this?" If you
   can't answer it cold, loop back. Don't advance on a soft pass.
5. **Write one paragraph** in a running lab notebook (`run/lab-notebook.md`,
   create it) on what surprised you. The surprises are where the paper hides.

> A professor's nag, said once: **do not skip the gates, and do not skip the
> notebook.** The gap between "I read about compaction" and "I can defend a
> measured claim about compaction in Q&A" is built entirely in steps 3–5.

---

## The arc at a glance (10 units)

```
FOUNDATIONS (this is the talk)        DEEPENING                 RESEARCH
─────────────────────────────   ──────────────────────   ─────────────────────────
0  Mental model + run the demo   3  Compaction internals  6  Make policy pluggable
1  Tokens = a budget            4  Lost-in-the-middle     7  Build the experiment
2  The five moves               5  Evals & needle-facts   8  Analyze + write paper
                                                          9  Frontier & extensions
```

Pace assumption: **~5 focused hours/day.** Units 0–3 are roughly a day each;
the research units (6–8) are the heavy ones — budget 2–3 days apiece. Full
unit-by-unit timing is in [`curriculum.md`](curriculum.md).

### The 4-day countdown to June 22

| Day | Focus | Output |
|---|---|---|
| **Jun 18** (today) | Units 0–1. Run the demo 10×. Read the loop and `context.py` until they're boring. | You can narrate the turn lifecycle cold. |
| **Jun 19** | Unit 2 + Unit 3 (compaction internals — the talk's deep part). | You can explain `_safe_split_index` to a skeptic. |
| **Jun 20** | Build the talk from [`talk-june22.md`](talk-june22.md). Draft the deck. | Slides exist; demo runs clean. |
| **Jun 21** | Rehearse with a timer (target 9:30). Record the demo GIF as wifi insurance. | A 10-min run you've done twice. |
| **Jun 22** | Present. Then Unit 4 starts the real research arc. | Talk delivered; paper begun. |

> ⚠️ **Date check:** your detailed plan says June **23**; you said June **22**.
> Confirm with the organizers before you lock the countdown above.

---

## What "done" looks like

- **Talk:** delivered in ≤10 min, one live compaction watched by the room, one
  sentence they remember.
- **Curriculum:** all 10 gates passed, lab notebook full.
- **Paper:** a quality-vs-cost Pareto plot across 4 compaction policies at
  increasing run-lengths, a 4–6 page write-up (workshop / blog-paper format), and
  the experiment code merged into the repo so anyone can reproduce it.

That last clause — *anyone can reproduce it* — is the whole ethos of this repo
and the room you're presenting to. The paper isn't done until `python -m
experiments.bench` reproduces your figure on someone else's laptop.
