// Build the Founsi-branded deck for AI Tinkerers.
//   node presentation/build_deck.js  ->  founsi-context-engineering.pptx
// Narrative: what context engineering IS -> why it matters -> what exists (landscape)
// -> THEN what we're building (harness + research). Appendix: project walkthrough +
// every experiment. Brand: bg FAFAFE, ink 2E2C32, accent purple 9378FF (~5%).
const pptxgen = require("pptxgenjs");
const sharp = require("sharp");
const fs = require("fs");
const path = require("path");

const BRAND = path.join(__dirname, "brand");
const FIG = path.join(__dirname, "figures");
const QR = path.join(__dirname, "assets", "qr");
const BG = "FAFAFE", INK = "2E2C32", PURPLE = "9378FF", PDARK = "7B5EF0",
      GREY = "655E74", MID = "7E7A8A", WHITE = "FFFFFF", ICE = "CADCFC", WASH = "EFEBFF";
const SYNE = "Syne", MAN = "Manrope", MONO = "Courier New";
const MX = 0.6;

async function png(file, w) {
  const out = await sharp(fs.readFileSync(file), { density: 300 }).resize({ width: w }).png().toBuffer();
  return "image/png;base64," + out.toString("base64");
}
const exists = (f) => fs.existsSync(f);

(async () => {
  const markPurple = await png(path.join(BRAND, "founsi-mark.svg"), 400);
  const lockupInv = await png(path.join(BRAND, "founsi-logo-horizontal-inverted.svg"), 1600);

  const p = new pptxgen();
  p.layout = "LAYOUT_16x9";
  p.author = "Kanishk Patel";
  p.title = "Context Engineering Inside the Harness";

  const footer = (s, n, dark = false) => {
    s.addImage({ data: markPurple, x: MX, y: 5.18, w: 0.24, h: 0.24 * 110 / 146 });
    s.addText([{ text: "Founsi", options: { color: dark ? WHITE : INK } }, { text: ".", options: { color: PURPLE } }],
      { x: MX + 0.3, y: 5.13, w: 1.4, h: 0.32, fontFace: SYNE, fontSize: 11, bold: true, margin: 0, valign: "middle" });
    s.addText(String(n), { x: 9.0, y: 5.13, w: 0.4, h: 0.32, fontFace: MAN, fontSize: 9, color: MID, align: "right", valign: "middle", margin: 0 });
  };
  const overline = (s, t, color = PURPLE) => s.addText(t.toUpperCase(),
    { x: MX, y: 0.4, w: 8.8, h: 0.3, fontFace: SYNE, fontSize: 11, bold: true, color, charSpacing: 3, margin: 0 });
  const titleTx = (s, t, size = 27) => s.addText(t,
    { x: MX, y: 0.7, w: 8.8, h: 0.95, fontFace: SYNE, fontSize: size, bold: true, color: INK, margin: 0, valign: "top" });
  const content = (ov, t, n, size) => {
    const s = p.addSlide(); s.background = { color: BG };
    overline(s, ov); titleTx(s, t, size); footer(s, n); return s;
  };
  const bullets = (s, items, o = {}) => {
    const opt = Object.assign({ x: MX, y: 1.8, w: 8.8, h: 3.1, fontFace: MAN, fontSize: 15, color: INK }, o);
    s.addText(items.map((it) => {
      const [txt, sub] = Array.isArray(it) ? it : [it, false];
      return { text: txt, options: { bullet: { indent: 16 }, breakLine: true, paraSpaceAfter: 8, color: sub ? GREY : opt.color, fontSize: sub ? opt.fontSize - 2 : opt.fontSize } };
    }), opt);
  };
  const fig = (s, file, o = {}) => exists(path.join(FIG, file)) &&
    s.addImage(Object.assign({ path: path.join(FIG, file), x: 4.55, y: 1.5, w: 5.0, h: 5.0 * 4.2 / 6.2 }, o));
  // landscape / project rows: accent bar + bold label + description
  const rows = (s, items, y0 = 1.75, gap = 0.66) => items.forEach((m, i) => {
    const y = y0 + i * gap, hot = m[2];
    s.addShape(p.shapes.RECTANGLE, { x: MX, y, w: 0.1, h: 0.52, fill: { color: hot ? PURPLE : "D4C9FF" } });
    s.addText([{ text: m[0] + "  ", options: { bold: true, color: hot ? PURPLE : INK, fontSize: 15 } },
               { text: m[1], options: { color: GREY, fontSize: 12.5 } }],
      { x: MX + 0.24, y, w: 8.7, h: 0.52, fontFace: MAN, valign: "middle", margin: 0 });
  });
  const qrBlock = (s, file, label, x, y, size = 1.35) => {
    if (exists(path.join(QR, file))) s.addImage({ path: path.join(QR, file), x, y, w: size, h: size });
    s.addText(label, { x: x - 0.3, y: y + size + 0.05, w: size + 0.6, h: 0.3, fontFace: MAN, fontSize: 11, bold: true, color: INK, align: "center", margin: 0 });
  };

  // ============================ MAIN DECK ============================
  // 1 — Title (dark)
  let s = p.addSlide(); s.background = { color: INK };
  s.addImage({ data: lockupInv, x: MX, y: 0.5, w: 2.4, h: 2.4 * 110 / 692 });
  s.addText("AI TINKERERS · CALGARY · JUNE 23, 2026", { x: MX, y: 1.55, w: 9, h: 0.3, fontFace: SYNE, fontSize: 11, bold: true, color: PURPLE, charSpacing: 3, margin: 0 });
  s.addText("Context Engineering", { x: MX, y: 1.95, w: 9, h: 0.9, fontFace: SYNE, fontSize: 42, bold: true, color: WHITE, margin: 0 });
  s.addText("Inside the Harness", { x: MX, y: 2.85, w: 9, h: 0.9, fontFace: SYNE, fontSize: 42, bold: true, color: PURPLE, margin: 0 });
  s.addText("Keeping a long-running agent from falling apart.", { x: MX, y: 3.85, w: 9, h: 0.4, fontFace: MAN, fontSize: 16, color: ICE, margin: 0 });
  s.addText([{ text: "Kanishk Patel", options: { bold: true, color: WHITE } }, { text: "   ·   Founsi AI   ·   Learn Agentic AI", options: { color: MID } }],
    { x: MX, y: 4.7, w: 9, h: 0.4, fontFace: MAN, fontSize: 12, margin: 0 });

  // 2 — What it is
  s = content("What it is", "Context engineering, defined.", 2, 26);
  s.addText([{ text: "Deciding what the model sees on every turn.", options: { bold: true, color: INK } }],
    { x: MX, y: 1.65, w: 8.8, h: 0.5, fontFace: MAN, fontSize: 19, margin: 0 });
  bullets(s, [
    "The model is stateless. Each turn, the harness hands it one list of messages — and that list IS the agent's entire mind for that turn.",
    ["Prompt engineering writes the instruction. Context engineering manages the whole working set: what to keep, summarize, externalize, and drop.", true],
    "It's the difference between an agent that runs for 5 steps and one that runs for 50.",
  ], { y: 2.35 });

  // 3 — Why it matters
  s = content("Why it matters", "Brilliant at 5 steps. Dead at 50.", 3, 26);
  bullets(s, [
    "Cost scales — you re-send the whole history every single turn.",
    "Latency scales — time-to-first-token grows with prompt length.",
    "Attention dilutes — the model gets lost in the middle.",
    ["Then it dies — drifts, repeats, forgets the goal, hits the hard limit.", true],
  ], { y: 1.85, w: 5.1 });
  s.addShape(p.shapes.RECTANGLE, { x: 6.3, y: 2.2, w: 3.0, h: 0.55, fill: { color: "F7C1C1" } });
  s.addText("context_length_exceeded", { x: 6.3, y: 2.2, w: 3.0, h: 0.55, fontFace: MONO, fontSize: 12, bold: true, color: "A32D2D", align: "center", valign: "middle", margin: 0 });
  s.addText("step 51 →", { x: 6.3, y: 2.85, w: 3.0, h: 0.3, fontFace: MAN, fontSize: 11, italic: true, color: GREY, align: "center", margin: 0 });

  // 4 — The reframe
  s = p.addSlide(); s.background = { color: BG };
  overline(s, "The reframe");
  s.addText([{ text: "The context window is a ", options: { color: INK } }, { text: "budget", options: { color: PURPLE, italic: true } }, { text: ",", options: { color: INK } }],
    { x: 0.8, y: 1.85, w: 8.4, h: 0.85, fontFace: SYNE, fontSize: 33, bold: true, align: "center", margin: 0 });
  s.addText([{ text: "not a ", options: { color: INK } }, { text: "backpack", options: { color: GREY, italic: true } }, { text: ".", options: { color: INK } }],
    { x: 0.8, y: 2.7, w: 8.4, h: 0.85, fontFace: SYNE, fontSize: 33, bold: true, align: "center", margin: 0 });
  s.addText("A bigger window raises the ceiling, not the curve. Engineer the working set and keep it roughly constant — no matter how long the run.",
    { x: 1.4, y: 3.75, w: 7.2, h: 0.7, fontFace: MAN, fontSize: 14, color: GREY, align: "center", margin: 0 });
  footer(s, 4);

  // 5 — The landscape
  s = content("What exists · the landscape", "Everyone is fighting the window.", 5, 25);
  rows(s, [
    ["Anthropic", "names the moves — compaction, structured note-taking, “context rot.”"],
    ["Cognition (Devin)", "“context engineering is the #1 job”; don't fragment it across agents."],
    ["LangChain · LlamaIndex", "memory abstractions — summary buffers, vector memory."],
    ["MemGPT · Letta", "treat the window like RAM; page facts to an external store."],
    ["RAG (Lewis, 2020)", "retrieve from a store instead of stuffing the prompt."],
  ]);

  // 6 — The gap
  s = content("The gap", "Everyone compacts. Nobody measured which way is best.", 6, 23);
  bullets(s, [
    "Prior work compresses a static prompt or RAG passages — to cut latency.",
    "The policy that ships in real agents — “summarize the stale middle” — is applied to an evolving transcript, and is essentially unmeasured against its alternatives.",
    ["Which way of forgetting preserves the most facts per token? That's the open question.", true],
    "So I built a harness to measure it.",
  ]);

  // 7 — The harness
  s = content("What I'm building", "The loop is trivial. The harness is the point.", 7, 25);
  rows(s, [
    ["Pin", "goal + system prompt — never dropped", false],
    ["Truncate", "cap oversized tool outputs before they enter", false],
    ["Compact", "summarize the stale middle, drop the raw turns", true],
    ["Externalize", "findings live in a file, not the window", false],
    ["Cap", "hard limits on steps / tokens / dollars", false],
  ]);
  s.addText("The model is a commodity you rent. These five moves are the part you build.",
    { x: MX, y: 5.0, w: 8.8, h: 0.3, fontFace: MAN, fontSize: 12, italic: true, color: GREY, margin: 0 });

  // 8 — Compact deeply
  s = content("The heart", "Compact: summarize the middle, drop the raw turns.", 8, 24);
  bullets(s, [
    "Over budget? Replace the stale middle with one dense summary; throw the raw turns away.",
    "Why the middle? It's the low-attention zone anyway — lost in the middle.",
    ["The gotcha: never split a tool-call from its result — real APIs reject that transcript.", true],
    "Lossy on purpose — safe only because findings were externalized to disk.",
  ]);

  // 9 — Live demo
  s = p.addSlide(); s.background = { color: INK };
  s.addText("LIVE DEMO", { x: MX, y: 1.95, w: 9, h: 0.9, fontFace: SYNE, fontSize: 40, bold: true, color: WHITE, margin: 0 });
  s.addText("Watch the context bar grow, cross the threshold, COMPACT, snap back — and keep going.",
    { x: MX, y: 2.95, w: 8.6, h: 0.6, fontFace: MAN, fontSize: 15, color: ICE, margin: 0 });
  s.addText("python run.py     ·     cat run/notes.md", { x: MX, y: 3.65, w: 9, h: 0.4, fontFace: MONO, fontSize: 14, color: PURPLE, margin: 0 });
  footer(s, 9, true);

  // 10 — The research question
  s = content("Zero to one", "The compaction bake-off.", 10, 26);
  bullets(s, [
    "Four ways of forgetting: truncate · recency · importance · semantic.",
    "Plant checkable “needle” facts in the sources; count how many survive each policy.",
    ["Metric: needle recall per token — objective, no LLM-judge.", true],
    "Free NVIDIA models, every prompt + result saved. Reproducible.",
  ], { y: 1.8, w: 4.0 });
  fig(s, "EXP-001_pareto_v1.png", { x: 4.7, y: 1.5, w: 4.9, h: 3.32 });

  // 11 — Early result
  s = content("Early result", "Truncation is the floor. Summaries win — at a cost.", 11, 24);
  fig(s, "EXP-001_recall_by_policy_v1.png", { x: 0.7, y: 1.5, w: 5.3, h: 3.59 });
  bullets(s, [
    "Truncate: cheapest, loses most.",
    "Summary policies preserve ~2-3x more facts.",
    ["semantic edges it at B*=1000 (8b dev).", true],
    "70b confirmation is running next.",
  ], { x: 6.2, y: 1.7, w: 3.3, fontSize: 13 });

  // 12 — Close
  s = p.addSlide(); s.background = { color: INK };
  s.addText([{ text: "The model is a commodity you ", options: { color: WHITE } }, { text: "rent", options: { color: ICE, italic: true } }, { text: ".", options: { color: WHITE } }],
    { x: 0.8, y: 1.7, w: 8.4, h: 0.8, fontFace: SYNE, fontSize: 30, bold: true, align: "center", margin: 0 });
  s.addText([{ text: "The harness is the part you ", options: { color: WHITE } }, { text: "build", options: { color: PURPLE, italic: true } }, { text: ".", options: { color: WHITE } }],
    { x: 0.8, y: 2.55, w: 8.4, h: 0.8, fontFace: SYNE, fontSize: 30, bold: true, align: "center", margin: 0 });
  qrBlock(s, "qr_repo.png", "Clone the repo", 4.35, 3.55, 1.1);
  s.addText("github.com/kanishkpatel1995/agent-harness", { x: 2.8, y: 4.78, w: 4.4, h: 0.3, fontFace: MONO, fontSize: 10, color: ICE, align: "center", margin: 0 });
  footer(s, 12, true);

  // ============================ APPENDIX ============================
  // 13 — divider
  s = p.addSlide(); s.background = { color: INK };
  s.addText("APPENDIX", { x: MX, y: 1.9, w: 9, h: 0.5, fontFace: SYNE, fontSize: 13, bold: true, color: PURPLE, charSpacing: 4, margin: 0 });
  s.addText("The whole project, and every experiment", { x: MX, y: 2.35, w: 9, h: 0.9, fontFace: SYNE, fontSize: 34, bold: true, color: WHITE, margin: 0 });
  s.addText("What's in the repo · the protocol · EXP-001 results · EXP-002 plan · roadmap.",
    { x: MX, y: 3.4, w: 8.8, h: 0.5, fontFace: MAN, fontSize: 14, color: ICE, margin: 0 });
  footer(s, 13, true);

  // 14 — Project map (file/folder tree)
  s = content("How to read this repo", "What's in the project", 14, 25);
  const tree = [
    "agent-harness/",
    "├─ harness/        the teaching harness: the loop + ContextManager",
    "├─ experiments/    the research: compaction bake-off (bench/ pkg)",
    "│   ├─ bench/       config · policies · window · runner · analyze",
    "│   └─ runs/        one folder per run: manifest + prompts + results",
    "├─ docs/research-track/   curriculum · paper · literature · protocol",
    "├─ presentation/   this deck + Founsi brand + figures",
    "└─ tests/          11 offline tests (no API key needed)",
  ];
  s.addShape(p.shapes.RECTANGLE, { x: MX, y: 1.65, w: 8.8, h: 2.7, fill: { color: "F4F2F8" }, line: { color: "D4C9FF", width: 1 } });
  s.addText(tree.map((t) => ({ text: t, options: { breakLine: true } })),
    { x: MX + 0.2, y: 1.8, w: 8.5, h: 2.4, fontFace: MONO, fontSize: 12.5, color: INK, margin: 0, lineSpacingMultiple: 1.18 });
  s.addText("Start at harness/loop.py (the agent loop), then harness/context.py (the heart).",
    { x: MX, y: 4.5, w: 8.8, h: 0.4, fontFace: MAN, fontSize: 12, italic: true, color: GREY, margin: 0 });

  // 15 — How an experiment is recorded (the protocol)
  s = content("How we keep it honest", "Every experiment is a traceable run", 15, 24);
  bullets(s, [
    "Hypothesis + assumptions first — stated before any code is written.",
    "Each run writes experiments/runs/EXP-NNN__slug__<UTC>/ with:",
    ["manifest.yaml (config + git sha + deps) · prompts.jsonl (every LLM call) · results.csv · figures/ · README.", true],
    "Figures in publication style (figstyle.py); rate-limited + cached so reruns are free.",
    "The bar: a stranger can clone the repo and reproduce the figure.",
  ], { fontSize: 14 });

  // 16 — EXP-001 hypothesis + assumptions
  s = content("EXP-001 · compaction-bakeoff", "Hypothesis & assumptions", 16, 25);
  s.addText("Hypothesis", { x: MX, y: 1.5, w: 8.8, h: 0.3, fontFace: MAN, fontSize: 13, bold: true, color: PURPLE, margin: 0 });
  s.addText("Under a fixed token budget, summary-based compaction (recency / importance / semantic) preserves more needle-facts per token than truncation, and a budget B* trades fact-loss against lost-in-the-middle.",
    { x: MX, y: 1.8, w: 8.8, h: 0.75, fontFace: MAN, fontSize: 13, color: INK, margin: 0 });
  s.addText("Assumptions", { x: MX, y: 2.7, w: 8.8, h: 0.3, fontFace: MAN, fontSize: 13, bold: true, color: PURPLE, margin: 0 });
  bullets(s, [
    "Needle-fact recall is a valid proxy for task-relevant information retention.",
    "approx_tokens (~4 chars/token) is acceptable for budget gating.",
    "The summarizer model is held fixed across policies within a run.",
    "Coined needle tokens are recoverable only from context, not model priors.",
    "Synthetic transcripts approximate real agent compaction dynamics.",
  ], { y: 3.0, fontSize: 12 });

  // 17 — EXP-001 method
  s = content("EXP-001 · method", "Mode A — the controlled probe", 17, 25);
  bullets(s, [
    "Build a needle-bearing transcript (deterministic, seeded) up to run-length L.",
    "Compact it under budget B with each policy — the real model writes the summaries.",
    "Probe: ask the model to recover the planted facts from the compacted window.",
    "Two metrics — fidelity (literal survival, scores the policy) vs probe (model recall@length).",
    "8b dev model on free NVIDIA NIM; paced + backed-off + cached; every prompt saved.",
  ], { fontSize: 13.5 });

  // 18-20 — results figures
  s = content("EXP-001 · results", "Quality vs cost by policy", 18, 25);
  fig(s, "EXP-001_pareto_v1.png", { x: 0.7, y: 1.5, w: 5.3, h: 3.59 });
  bullets(s, [["Upper-left wins: more recall per token.", true], "Truncate is the floor.", "Summary policies cluster higher.", "semantic best at B*=1000 (8b)."], { x: 6.2, y: 1.7, w: 3.3, fontSize: 13 });

  s = content("EXP-001 · results", "Needle recall by policy & budget", 19, 24);
  fig(s, "EXP-001_recall_by_policy_v1.png", { x: 0.7, y: 1.5, w: 5.3, h: 3.59 });
  bullets(s, ["Recall as a fraction (poolable across needle counts).", ["Error bars = sd across seeds (honest now).", true], "importance is tail-bound at small budgets."], { x: 6.2, y: 1.7, w: 3.3, fontSize: 13 });

  s = content("EXP-001 · results", "No-compaction baseline & the wall", 20, 23);
  fig(s, "EXP-001_baseline_recall_v1.png", { x: 0.7, y: 1.5, w: 5.3, h: 3.59 });
  bullets(s, ["Baseline grows raw context, measures recall vs length.", ["Exceed the model's max window -> context_overflow: the agent dies.", true], "Compaction is the fix; we measure the deaths it prevents."], { x: 6.2, y: 1.7, w: 3.3, fontSize: 13 });

  // 21 — threats
  s = content("EXP-001 · threats to validity", "What could make this wrong", 21, 25);
  bullets(s, [
    "Synthetic data + simulated agent — not a live decision-making run (Mode B is next).",
    "Needle recall is a proxy for diffuse understanding; score normalization is a choice.",
    "8b under-reads (weak instruction-following) — final numbers need 70b.",
    "Single task domain; importance/semantic are crude heuristics, not embeddings.",
  ], { fontSize: 13.5 });

  // 22 — EXP-002 results
  s = content("EXP-002 · length-degradation", "Does compaction beat raw context? Yes.", 22, 25);
  fig(s, "EXP-002_recall_vs_length_v1.png", { x: 0.7, y: 1.5, w: 5.3, h: 3.64 });
  bullets(s, [
    "No-compaction baseline collapses with length: 0.62 down to 0.12 by 32 sources.",
    "Summary compaction (recency, semantic) holds flat near 0.58.",
    ["Crossover around 16 sources: compaction goes from tied to decisively better.", true],
    "Truncate is the floor (0.08). 8b dev; the effect is the lost-in-the-middle escape.",
  ], { x: 6.2, y: 1.7, w: 3.3, fontSize: 12.5 });

  // 23 — EXP-003a applied (the metric lesson)
  s = content("EXP-003a · applied FRAMES", "On a real task, the metric flips the result", 23, 23);
  fig(s, "EXP-003a_pareto_v1.png", { x: 0.7, y: 1.5, w: 5.3, h: 3.59 });
  bullets(s, [
    "A real research agent answers FRAMES multi-hop questions under each policy.",
    "Substring scoring made the reversible-hybrid look worst, at 0.21.",
    ["The LLM judge, which credits paraphrase, flipped it to best, at 0.62.", true],
    "At low pressure all four cluster near 0.6: compaction barely fires (~1 event).",
  ], { x: 6.2, y: 1.7, w: 3.3, fontSize: 12.5 });

  // 24 — EXP-003b the bake-off
  s = content("EXP-003b · the compaction bake-off", "Under pressure, the policies separate", 24, 24);
  fig(s, "EXP-003b_pareto_v1.png", { x: 0.7, y: 1.5, w: 5.3, h: 3.6 });
  bullets(s, [
    "7 arms, 30 questions, high pressure (9 to 18 compactions each), judged.",
    "recency, the shipped default, is dominated by truncation: same accuracy, 7x cost.",
    "sub-agent isolation scores 0.50 at 5x the cost. Isolation is expensive here.",
    ["semantic 0.57 and importance 0.50 lead; reversible-hybrid is on the frontier at 0.47.", true],
  ], { x: 6.2, y: 1.7, w: 3.3, fontSize: 12 });

  // 25 — roadmap
  s = content("Where this goes", "Roadmap", 25, 25);
  bullets(s, [
    "EXP-003c: the 70b model and the reasoning model (the model-dependence map).",
    "EXP-004: LoCoMo conversational memory, the second domain.",
    "Larger N and tighter error bars on the arms that separate.",
    "LangChain summary-memory as a baseline arm; then the paper.",
  ], { fontSize: 13.5 });

  // 26 — references
  s = content("References", "The literature this stands on", 26, 26);
  bullets(s, [
    "Lost in the Middle, Liu et al., arXiv:2307.03172.",
    "RULER 2404.06654 · HELMET 2410.02694 · NoLiMa 2502.05167.",
    "MemGPT 2310.08560 · Mem0 2504.19413 · ACON 2510.00615.",
    "Judging LLM-as-a-Judge, Zheng et al., 2306.05685.",
    "FRAMES 2409.12941 · LoCoMo 2402.17753.",
  ], { fontSize: 13, color: GREY });

  // 27 — Find me (QR codes)
  s = p.addSlide(); s.background = { color: INK };
  s.addText("FIND ME", { x: MX, y: 0.6, w: 9, h: 0.4, fontFace: SYNE, fontSize: 12, bold: true, color: PURPLE, charSpacing: 4, margin: 0 });
  s.addText("Clone it. Read the write-ups. Say hi.", { x: MX, y: 1.0, w: 9, h: 0.7, fontFace: SYNE, fontSize: 30, bold: true, color: WHITE, margin: 0 });
  qrBlock(s, "qr_repo.png", "Repo", 0.95, 2.3, 1.25);
  qrBlock(s, "qr_newsletter.png", "Learn Agentic AI", 3.25, 2.3, 1.25);
  qrBlock(s, "qr_x.png", "X · @above_almighty", 5.55, 2.3, 1.25);
  qrBlock(s, "qr_linkedin.png", "LinkedIn", 7.85, 2.3, 1.25);
  footer(s, 27, true);

  await p.writeFile({ fileName: path.join(__dirname, "founsi-context-engineering.pptx") });
  console.log("wrote presentation/founsi-context-engineering.pptx (27 slides)");
})();
