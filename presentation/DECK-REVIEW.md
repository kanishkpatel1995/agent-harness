# Deck review — `founsi-context-engineering.pptx` (41 slides)

A critical pass across aesthetics, layout, story/flow, technical content, and the
"journey." Reviewed against your own briefs in `deck-structure.md` and
`docs/research-track/talk-june22.md`. Ordered by priority.

---

## Top-line verdict

The raw material is excellent: real experiments (EXP-001→004), a genuinely
paper-grade result (one policy in the top group of every task×model cell), and a
clean, consistent Founsi brand system. The problems are **scope, story order,
one systemic layout bug, and one factual overclaim** — all fixable polish, not
fundamentals.

Two decisions dominate everything else:

1. **Decide what this deck *is*.** Your briefs describe a **≤10-minute,
   depth-on-one-mechanism** talk with ~10 main slides + a carried appendix. What
   got built is a **~41-slide research seminar** (problem → all 7 policies → "our
   method" → why → how-we-test → full results → claims → lit map → references).
   That's a 25–40 min talk. For the AI Tinkerers slot it's 2–3× too long, and the
   front third surveys all seven policies — exactly the breadth your own talk
   script says to avoid ("breadth is the enemy; let the other four moves be
   scenery"). Right now it's neither the tight talk nor cleanly a seminar.
2. **Fix the systemic footer collision** (below). It's the single thing that makes
   an otherwise-polished deck look unfinished.

---

## P0 — Fix before anything else

### 1. Bottom text collides with the footer logo on many slides
The recurring "summary line at the bottom of the slide" runs straight through the
**Founsi.** footer logo. Confirmed on slides **3, 10, 11, 12, 15, 24** (and likely
others with a bottom caption/footnote). On slide 3 a body bullet also overlaps the
footer *and* is cut off at the slide edge.

- **Root cause:** one shared layout puts a bottom caption at ~y6.95–7.1, the same
  band as the footer logo. No reserved footer safe-zone.
- **Fix:** reserve a footer zone — content bottom ≤ ~6.6", footer at ~7.0". Move
  every bottom caption up, or convert it to a normal last bullet. This is one
  template fix that clears all of them at once.

### 2. The table's title overclaims what the table shows (credibility risk)
Slide 24 title: **"One policy wins every cell."** The numbers on that same slide
say otherwise:

| arm | FR-8B | FR-70B | LC-8B | LC-70B |
|---|---|---|---|---|
| reversible_hybrid | 0.47 | **0.67** | 0.54 | 0.53 |
| externalize | 0.40 | 0.63 | **0.55** | **0.55** |
| importance | 0.50 | 0.60 | 0.26 | 0.23 |
| semantic | **0.57** | 0.53 | 0.27 | 0.17 |
| truncate | 0.37 | 0.27 | 0.12 | 0.09 |

reversible_hybrid wins outright in **1 of 4** cells (FR-70B). In FR-8B semantic
(0.57) beats it; in both LoCoMo cells externalize (0.55) beats it. The honest —
and still strong — claim is **"top group in every cell, the only arm that is,"**
which is exactly what your own footnote and slide 14 ("never the single best, but
never in the loser group") say. So the deck contradicts itself, and a sharp
audience member will see the contradiction on the slide. **Retitle to "Top group
in every cell"** (or "Never the best, never the worst — everywhere"). This is the
most important fix in the deck.

---

## P1 — Story, flow, and the journey

### 3. Open with the corpse, not the dictionary
Your single best hook — **"Brilliant at 5 steps. Dead at 50."** — is slide **4**,
sitting behind a vocabulary slide ("Three words, one thesis"). Your own talk
script is right: *"Don't open with theory. Open with a corpse."* Move the death to
**slide 2** and make it visceral — a real drifting/failing terminal ending in red
`context_length_exceeded` — not four bullets + a small chip. Let it land, then
explain. The "three words" slide can be cut or folded into the reframe.

### 4. The mechanism is told, not shown — on the one slide that must show it
Slide 7 ("Compaction: summarize the middle, drop the raw turns") is the heart of a
depth talk, and it's **four prose bullets with no code and no diagram.** The script
explicitly wanted the actual `maybe_compact` + `_safe_split_index` code, and a
before/after. You clearly *can* do this — slide 13 (reversible-hybrid) and the
before/after stacks are your best visuals. Bring that quality here: show the code,
show the message-list shrinking, name the tool-call gotcha visually.

### 5. The live demo — your highest-impact 90 seconds — is missing from the flow
The script's "money moment" (run it, watch the context bar compact and snap back,
`cat run/notes.md`) doesn't appear as a slide in the main sequence. Either it got
dropped when the deck pivoted to results, or it's purely-live with no anchor/back-
up slide. For a builders' room this is the moment they remember. Restore a demo
anchor slide (terminal mockup) + the GIF fallback the script calls for.

### 6. Collapse the seven-policy tour
Slides 8–13 walk all seven policies, including **three near-identical "flow"
diagram slides** (10 truncate/recency, 11 importance/semantic, 12 externalize/
subagent). For the talk, compress this to **one** "here's the menu, here's the one
that matters" slide and go deep on compaction. Keep the per-policy flows in the
appendix. (For a seminar version, they're fine where they are — but then it's a
seminar, see decision #1.)

### 7. Resolve the identity split: open question vs. solved result
The title subtitle poses an **open question** ("Which way of forgetting keeps a
long-running agent alive?") and the talk script says *"I don't have the answer yet
— I'm showing you the question while it's still open."* But the deck now **answers
it** ("reversible_hybrid… top group everywhere," "Six claims, now backed by
evidence"). Both are good talks — but pick one. Given you now *have* results, the
stronger arc for this room is: *"I asked which way of forgetting loses least, I
built the bake-off, and the answer surprised me."* Then update the subtitle and
retire the "open question / no answer yet" framing in the script — it's stale.

### 8. Trim redundancy
- The EXP "compaction holds as context grows" chart appears on **slide 6 and again
  on slide 19** — same figure, twice. Differentiate or cut one.
- The landscape ("everyone compacts" slide 8) and "we're not alone" (slide 27)
  cover overlapping ground. One in the main deck, one in appendix.

---

## P2 — Aesthetics and layout polish

### 9. Figures aren't brand-styled and break the deck's own color language
The result charts (slides 6, 19) are raw matplotlib — Times New Roman, default
pink/blue/green — while your `deck-structure.md` promises `chart_style.py` with
fixed policy colors (truncate=grey, recency=purple, importance=purple-dark,
semantic=ink, baseline=red). The on-slide legend colors therefore **don't match**
the policy colors you use elsewhere. Re-render every figure through `chart_style.py`
and lock one color per policy across the whole deck. This is the biggest single
aesthetic upgrade after the footer fix.

### 10. Vertical balance — content floats low, big dead gaps up top
Many slides (3, 7, 14, 15, 26) have a large empty band between the title and the
content, which sits low and bottom-heavy (contributing to the footer collisions).
Anchor content to a consistent higher Y; tighten the title→content gap.

### 11. Two-line title wraps eat space and shove content down
Slides 6, 7, 9, 11 wrap the title to two lines, pushing everything down. Either
shorten the titles or drop the title size a couple of points / widen the box.

### 12. Small stuff
- Slide 9 table: `reversible_hybrid` wraps mid-word ("reversible_hybri/d"). Widen
  the first column.
- The cutesy `$ / $$ / $$$` cost column (slide 9) is weaker than the **real**
  tokens/q numbers you already have on slide 25 — consider using real relative
  numbers earlier.
- Call out the killer stat bigger: raw context collapses **0.62 → 0.12** with
  length. That one number sells the whole thesis.

---

## What's genuinely working (keep it)

- The **brand system** — type hierarchy, the purple accent discipline, Syne
  overlines, dark section dividers (slide 30), the title slide — is clean and
  consistent. Don't touch it.
- The **research is real and the results are strong.** The 4-cell table (slide 24,
  retitled) is a paper-grade headline result and should be a *peak* of the talk,
  not buried in the back half.
- Good rigor signals are present (needle-fact metric, FRAMES + LoCoMo, 8B/70B
  axis, cost-normalized, reproducible run folders). Surface them briefly as
  credibility.
- The reversible-hybrid diagram (slide 13) and the before/after framing are your
  best visual work — propagate that style.

---

## Suggested 10-slide spine (for the ≤10-min AI Tinkerers cut)

1. **Title** — pick: open-question *or* result-tease subtitle (not both).
2. **The corpse** — agent dies at 50. Visceral. The hook.
3. **Why it dies** — window is a budget; lost-in-the-middle (one chart, the
   0.62→0.12 stat).
4. **Reframe** — model rented / harness built (the one sentence).
5. **The list IS the mind** — the mental model.
6. **Five moves, one matters** — menu in one slide; spotlight compaction.
7. **Compact, deeply** — the code + before/after + the tool-call gotcha (shown).
8. **💻 Live demo** — the bar compacts and snaps back. The money moment.
9. **The twist** — "so which way of forgetting loses least? I measured it." → the
   4-cell result as the payoff.
10. **Close** — reversible-hybrid, the one sentence, clone QR.

Everything else (7-policy tour, why-we-bet, how-we-test, lit map, infra, full
results) → appendix, exactly as `deck-structure.md` originally intended.

---

## Priority checklist

- [ ] **P0** Fix footer-collision template (slides 3, 10, 11, 12, 15, 24, +).
- [ ] **P0** Retitle slide 24 to the accurate "top group in every cell."
- [ ] **P1** Re-order: open with the death; restore the live-demo slide.
- [ ] **P1** Put code + before/after on the compaction slide.
- [ ] **P1** Collapse the 7-policy tour to one slide (talk cut).
- [ ] **P1** Resolve open-question vs. solved-result identity + fix the stale script.
- [ ] **P1** Cut the duplicate EXP chart (slide 6 vs 19); merge 8 vs 27.
- [ ] **P2** Re-render figures via `chart_style.py`; lock policy colors.
- [ ] **P2** Vertical-balance pass; fix two-line titles; widen slide-9 table column.
</content>
