// Build the Founsi-branded deck for AI Tinkerers (main deck + EXP-001 appendix).
// Reproducible: `node presentation/build_deck.js` -> founsi-context-engineering.pptx
// Brand: bg FAFAFE, ink 2E2C32, accent purple 9378FF (~5%), Syne display + Manrope body.
const pptxgen = require("pptxgenjs");
const sharp = require("sharp");
const fs = require("fs");
const path = require("path");

const BRAND = path.join(__dirname, "brand");
const FIG = path.join(__dirname, "figures");
const BG = "FAFAFE", INK = "2E2C32", PURPLE = "9378FF", PDARK = "7B5EF0",
      GREY = "655E74", MID = "7E7A8A", WHITE = "FFFFFF", ICE = "CADCFC";
const SYNE = "Syne", MAN = "Manrope";
const MX = 0.6;

async function png(file, w) {
  const buf = fs.readFileSync(path.join(BRAND, file));
  const out = await sharp(buf, { density: 300 }).resize({ width: w }).png().toBuffer();
  return "image/png;base64," + out.toString("base64");
}

(async () => {
  const markPurple = await png("founsi-mark.svg", 400);
  const lockupInv = await png("founsi-logo-horizontal-inverted.svg", 1600);

  const p = new pptxgen();
  p.layout = "LAYOUT_16x9";              // 10 x 5.625"
  p.author = "Kanishk Patel";
  p.title = "Context Engineering Inside the Harness";

  const footer = (s, n) => {
    s.addImage({ data: markPurple, x: MX, y: 5.16, w: 0.26, h: 0.26 * 110 / 146 });
    s.addText([{ text: "Founsi", options: { color: INK } }, { text: ".", options: { color: PURPLE } }],
      { x: MX + 0.32, y: 5.12, w: 1.4, h: 0.32, fontFace: SYNE, fontSize: 11, bold: true, margin: 0, valign: "middle" });
    s.addText(String(n), { x: 9.0, y: 5.12, w: 0.4, h: 0.32, fontFace: MAN, fontSize: 9, color: MID, align: "right", valign: "middle", margin: 0 });
  };
  const overline = (s, t) => s.addText(t.toUpperCase(),
    { x: MX, y: 0.4, w: 8.8, h: 0.3, fontFace: SYNE, fontSize: 11, bold: true, color: PURPLE, charSpacing: 3, margin: 0 });
  const titleTx = (s, t, size = 27) => s.addText(t,
    { x: MX, y: 0.7, w: 8.8, h: 0.95, fontFace: SYNE, fontSize: size, bold: true, color: INK, margin: 0, valign: "top" });
  const content = (ov, t, n, size) => {
    const s = p.addSlide(); s.background = { color: BG };
    overline(s, ov); titleTx(s, t, size); footer(s, n); return s;
  };
  const bullets = (s, items, o = {}) => {
    const opt = Object.assign({ x: MX, y: 1.75, w: 8.8, h: 3.1, fontFace: MAN, fontSize: 15, color: INK }, o);
    s.addText(items.map((it) => {
      const [txt, sub] = Array.isArray(it) ? it : [it, false];
      return { text: txt, options: { bullet: { indent: 16 }, breakLine: true, paraSpaceAfter: 9, color: sub ? GREY : opt.color, fontSize: sub ? opt.fontSize - 2 : opt.fontSize } };
    }), opt);
  };
  const fig = (s, file, o = {}) => s.addImage(Object.assign({ path: path.join(FIG, file), x: 4.55, y: 1.5, w: 5.0, h: 5.0 * 4.2 / 6.2 }, o));

  // ============ MAIN DECK ============
  // 1 — Title (dark)
  let s = p.addSlide(); s.background = { color: INK };
  s.addImage({ data: lockupInv, x: MX, y: 0.55, w: 2.5, h: 2.5 * 110 / 692 });
  s.addText("Context Engineering", { x: MX, y: 1.7, w: 9, h: 0.95, fontFace: SYNE, fontSize: 43, bold: true, color: WHITE, margin: 0 });
  s.addText("Inside the Harness", { x: MX, y: 2.62, w: 9, h: 0.95, fontFace: SYNE, fontSize: 43, bold: true, color: PURPLE, margin: 0 });
  s.addText("Keeping a long-running agent from falling apart.", { x: MX, y: 3.7, w: 9, h: 0.4, fontFace: MAN, fontSize: 16, color: ICE, margin: 0 });
  s.addText([{ text: "Kanishk Patel", options: { bold: true, color: WHITE } },
             { text: "   ·   Founsi AI · Learn Agentic AI   ·   AI Tinkerers Calgary · June 22, 2026", options: { color: MID } }],
    { x: MX, y: 4.75, w: 9, h: 0.4, fontFace: MAN, fontSize: 12, margin: 0 });

  // 2 — Cold open: the agent that dies
  s = content("The problem", "Brilliant at 5 steps. Dead at 50.", 2);
  bullets(s, [
    "Same model. Same 40-line loop. It drifts, repeats itself, forgets its goal —",
    ["then hits the hard context limit and the run just dies.", true],
    "Nothing changed in the model. Something filled up.",
  ], { y: 1.8, w: 5.0 });
  s.addShape(p.shapes.RECTANGLE, { x: 6.2, y: 1.9, w: 3.0, h: 0.5, fill: { color: "F7C1C1" } });
  s.addText("context_length_exceeded", { x: 6.2, y: 1.9, w: 3.0, h: 0.5, fontFace: "Courier New", fontSize: 12, bold: true, color: "A32D2D", align: "center", valign: "middle", margin: 0 });
  s.addText("step 51 →", { x: 6.2, y: 2.5, w: 3.0, h: 0.3, fontFace: MAN, fontSize: 11, italic: true, color: GREY, align: "center", margin: 0 });

  // 3 — The window is a budget
  s = content("The reframe", "The context window isn't storage. It's a budget.", 3, 26);
  bullets(s, [
    "The model is stateless — every turn you re-send the entire history.",
    "A 50-step run pays for its history ~50 times: cost climbs, latency climbs,",
    ["and recall drops — models read the middle of a long context worst.", true],
    "A bigger window raises the ceiling. It doesn't bend the curve.",
  ], { y: 1.8 });

  // 4 — The one sentence (statement)
  s = p.addSlide(); s.background = { color: BG };
  s.addText([{ text: "The model is a commodity you ", options: { color: INK } }, { text: "rent", options: { color: PDARK, italic: true } }, { text: ".", options: { color: INK } }],
    { x: 0.8, y: 1.7, w: 8.4, h: 0.9, fontFace: SYNE, fontSize: 34, bold: true, align: "center", margin: 0 });
  s.addText([{ text: "The harness is the part you ", options: { color: INK } }, { text: "build", options: { color: PURPLE, italic: true } }, { text: ".", options: { color: INK } }],
    { x: 0.8, y: 2.7, w: 8.4, h: 0.9, fontFace: SYNE, fontSize: 34, bold: true, align: "center", margin: 0 });
  footer(s, 4);

  // 5 — The list is the mind
  s = content("Mental model", "The list is the mind.", 5);
  bullets(s, [
    "The model remembers nothing between calls.",
    "Every turn, the harness rebuilds one list of messages — and that list IS the agent's entire mind for that turn.",
    ["If the agent forgot its goal, the goal wasn't in the list. There's no magic.", true],
    "messages() = pinned + body. The whole game is what goes in those two lists.",
  ]);

  // 6 — Five moves
  s = content("The map", "Five moves. One matters tonight.", 6);
  const moves = [["Pin", "goal + system prompt, never dropped"], ["Truncate", "cap oversized tool outputs"],
    ["Compact", "summarize the stale middle, drop raw turns"], ["Externalize", "findings live in a file, not the window"],
    ["Cap", "hard limits on steps / tokens / dollars"]];
  moves.forEach((m, i) => {
    const y = 1.8 + i * 0.62, hot = m[0] === "Compact";
    s.addShape(p.shapes.RECTANGLE, { x: MX, y, w: 0.12, h: 0.5, fill: { color: hot ? PURPLE : "D4C9FF" } });
    s.addText([{ text: m[0] + "   ", options: { bold: true, color: hot ? PURPLE : INK, fontSize: 16 } },
               { text: m[1], options: { color: GREY, fontSize: 13 } }],
      { x: MX + 0.25, y, w: 8.5, h: 0.5, fontFace: MAN, valign: "middle", margin: 0 });
  });

  // 7 — Compact deeply
  s = content("The heart", "Compact, deeply.", 7);
  bullets(s, [
    "Over budget? Summarize the stale middle into one dense note; drop the raw turns.",
    "Why the middle? It's the low-attention zone anyway (lost-in-the-middle).",
    ["The gotcha: never split a tool-call from its result — real APIs reject that transcript.", true],
    "Lossy on purpose — safe only because findings were externalized to disk.",
  ]);

  // 8 — Live demo
  s = p.addSlide(); s.background = { color: INK };
  s.addText("LIVE DEMO", { x: MX, y: 2.0, w: 9, h: 0.9, fontFace: SYNE, fontSize: 40, bold: true, color: WHITE, margin: 0 });
  s.addText("Watch the context bar grow, cross the threshold, ⚙ COMPACT, snap back — and keep going.",
    { x: MX, y: 3.0, w: 8.6, h: 0.6, fontFace: MAN, fontSize: 15, color: ICE, margin: 0 });
  s.addText("python run.py  ·  cat run/notes.md", { x: MX, y: 3.7, w: 9, h: 0.4, fontFace: "Courier New", fontSize: 14, color: PURPLE, margin: 0 });
  footer(s, 8);

  // 9 — The open question (+ figure)
  s = content("Zero to one", "Which way of forgetting loses least?", 9, 25);
  bullets(s, [
    "Compaction is lossy — so which policy preserves the most facts per token?",
    "Truncate · recency · importance · semantic.",
    ["I plant checkable facts and count how many survive each policy.", true],
    "Early result, right →",
  ], { y: 1.7, w: 3.9 });
  fig(s, "EXP-001_pareto_v1.png", { x: 4.55, y: 1.45, w: 5.0, h: 3.39 });

  // 10 — Swap the brain + clone
  s = content("Yours to build", "Swap the brain. Clone the harness.", 10, 25);
  bullets(s, [
    "Provider-agnostic via litellm — one flag swaps Claude / GPT / local Llama.",
    "Runs offline with no API key (FakeLLM).",
    "github.com/kanishkpatel1995/agent-harness",
    ["The model is rented. The harness is yours.", true],
  ]);

  // ============ APPENDIX ============
  // 11 — Appendix divider
  s = p.addSlide(); s.background = { color: INK };
  s.addText("APPENDIX", { x: MX, y: 1.9, w: 9, h: 0.6, fontFace: SYNE, fontSize: 13, bold: true, color: PURPLE, charSpacing: 4, margin: 0 });
  s.addText("The full trace", { x: MX, y: 2.4, w: 9, h: 0.9, fontFace: SYNE, fontSize: 38, bold: true, color: WHITE, margin: 0 });
  s.addText("Every experiment: hypothesis · assumptions · method · figures · results · threats.",
    { x: MX, y: 3.4, w: 8.8, h: 0.5, fontFace: MAN, fontSize: 14, color: ICE, margin: 0 });
  footer(s, 11);

  const ap = 12;  // appendix uses smaller fonts (density is fine here)
  const small = { fontSize: 13, y: 1.6 };

  // 12 — EXP-001 hypothesis + assumptions
  s = content("EXP-001 · compaction-bakeoff", "Hypothesis & assumptions", ap);
  s.addText("Hypothesis", { x: MX, y: 1.55, w: 8.8, h: 0.3, fontFace: MAN, fontSize: 13, bold: true, color: PURPLE, margin: 0 });
  s.addText("Under a fixed token budget, summary-based compaction (recency / importance / semantic) preserves more needle-facts per token than truncation, and there is a budget B* trading compaction fact-loss against lost-in-the-middle.",
    { x: MX, y: 1.85, w: 8.8, h: 0.8, fontFace: MAN, fontSize: 13, color: INK, margin: 0 });
  s.addText("Assumptions", { x: MX, y: 2.75, w: 8.8, h: 0.3, fontFace: MAN, fontSize: 13, bold: true, color: PURPLE, margin: 0 });
  bullets(s, [
    "Needle-fact recall is a valid proxy for task-relevant information retention.",
    "approx_tokens (~4 chars/token) is acceptable for budget gating.",
    "The summarizer model is held fixed across policies within a run.",
    "Coined needle tokens are recoverable only from context, not model priors.",
    "Synthetic transcripts approximate real agent compaction dynamics.",
  ], { y: 3.05, fontSize: 12.5 });

  // 13 — EXP-001 method
  s = content("EXP-001 · method", "Mode A — the controlled probe", ap, 25);
  bullets(s, [
    "Build a needle-bearing transcript (deterministic, seeded) up to run-length L.",
    "Compact it under budget B with each policy — real model writes the summaries.",
    "Probe: ask the model to recover the planted facts from the compacted window.",
    "Metrics — fidelity (literal survival, scores the policy) vs probe (model recall@length); cost in tokens billed.",
    "Free NVIDIA NIM (llama-3.1-8b dev); paced + backed-off + cached; every prompt saved to prompts.jsonl.",
  ], { fontSize: 13.5 });

  // 14 — Results: Pareto
  s = content("EXP-001 · results", "Quality vs cost by policy", ap, 25);
  fig(s, "EXP-001_pareto_v1.png", { x: 0.7, y: 1.5, w: 5.4, h: 3.66 });
  bullets(s, [
    "Truncate is the floor: cheapest, ~0.2 recall.",
    "Summary policies cluster higher (~0.4–0.5).",
    ["semantic edges it at B*=1000 (8b dev).", true],
    "Note: 8b under-reads — 70b run is next.",
  ], { x: 6.3, y: 1.7, w: 3.2, fontSize: 13 });

  // 15 — Results: recall by policy
  s = content("EXP-001 · results", "Needle recall by policy & budget", ap, 25);
  fig(s, "EXP-001_recall_by_policy_v1.png", { x: 0.7, y: 1.5, w: 5.4, h: 3.66 });
  bullets(s, [
    "Recall reported as a fraction (poolable across needle counts).",
    "Error bars = sd across seeds (now honest — seeds vary layout).",
    ["importance is tail-bound: can't reach small budgets with keep=2.", true],
  ], { x: 6.3, y: 1.7, w: 3.2, fontSize: 13 });

  // 16 — Results: baseline + overflow
  s = content("EXP-001 · results", "No-compaction baseline & the wall", ap, 24);
  fig(s, "EXP-001_baseline_recall_v1.png", { x: 0.7, y: 1.5, w: 5.4, h: 3.66 });
  bullets(s, [
    "Baseline grows the raw context and measures recall vs length.",
    "When raw tokens exceed the model's max window → context_overflow:",
    ["the agent dies. Compaction is the fix; we measure the deaths it prevents.", true],
  ], { x: 6.3, y: 1.7, w: 3.2, fontSize: 13 });

  // 17 — Threats
  s = content("EXP-001 · threats to validity", "What could make this wrong", ap, 25);
  bullets(s, [
    "Synthetic data + simulated agent — not a live decision-making run (Mode B is next).",
    "Needle recall is a proxy for diffuse understanding; score normalization is a choice.",
    "8b under-reads (weak instruction-following) — final numbers need 70b.",
    "Single task domain; importance/semantic are crude heuristics, not embeddings.",
  ], { fontSize: 13.5 });

  // 18 — Roadmap
  s = content("Where this goes", "Roadmap", ap, 27);
  bullets(s, [
    "EXP-002 — the 70b run: real numbers, the 128k ceiling, find B*.",
    "EXP-003 — lost-in-the-middle: recall by needle depth (data already logged).",
    "Real eval datasets (RULER / LongBench / BABILong) via HF datasets.",
    "LangChain summary-memory as a baseline arm to beat.",
    "Mode B — the live agent loop for ecological validity. Then the paper.",
  ], { fontSize: 13.5 });

  // 19 — References
  s = content("References", "The literature this stands on", ap, 26);
  bullets(s, [
    "Lost in the Middle — Liu et al., arXiv:2307.03172.",
    "RULER — Hsieh et al., 2404.06654 · HELMET — Yen et al., 2410.02694.",
    "MemGPT — Packer et al., 2310.08560 · LLMLingua — Jiang et al., 2310.05736.",
    "Judging LLM-as-a-Judge — Zheng et al., 2306.05685.",
    "Effective context engineering for AI agents — Anthropic, 2025.",
  ], { fontSize: 13, color: GREY });

  await p.writeFile({ fileName: path.join(__dirname, "founsi-context-engineering.pptx") });
  console.log("wrote presentation/founsi-context-engineering.pptx");
})();
