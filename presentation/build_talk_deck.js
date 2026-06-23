// Build the LEAN talk-deck backdrop for AI Tinkerers (codebase-forward, live editor).
//   node presentation/build_talk_deck.js  ->  founsi-talk.pptx
// This is the ~17-slide backdrop for the ~22 min live talk. The EDITOR and the DEMOS are the
// star; this deck carries the non-code segments: hook, architecture, the one constraint, the
// memory-systems bake-off (the headline), the war stories, a demo card, and the payoff. The full
// 41-slide founsi-context-engineering.pptx remains the comprehensive leave-behind/appendix.
// Tour script: docs/research-track/talk/codebase-tour.md. Brand: bg FAFAFE, ink 2E2C32, purple.
const pptxgen = require("pptxgenjs");
const sharp = require("sharp");
const fs = require("fs");
const path = require("path");

const BRAND = path.join(__dirname, "brand");
const FIG = path.join(__dirname, "figures");
const QR = path.join(__dirname, "assets", "qr");
const BG = "FAFAFE", INK = "2E2C32", PURPLE = "9378FF", PDARK = "7B5EF0",
      GREY = "655E74", MID = "7E7A8A", WHITE = "FFFFFF", ICE = "CADCFC", WASH = "EFEBFF",
      PANEL = "F4F2F8", LILAC = "D4C9FF", RED = "A32D2D", GREEN = "2E8B57";
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
  p.title = "Context Engineering Inside the Harness (talk)";
  const RR = p.shapes.ROUNDED_RECTANGLE, RECT = p.shapes.RECTANGLE, LINE = p.shapes.LINE;

  const footer = (s, n, dark = false) => {
    s.addImage({ data: markPurple, x: MX, y: 5.18, w: 0.24, h: 0.24 * 110 / 146 });
    s.addText([{ text: "Founsi", options: { color: dark ? WHITE : INK } }, { text: ".", options: { color: PURPLE } }],
      { x: MX + 0.3, y: 5.13, w: 1.4, h: 0.32, fontFace: SYNE, fontSize: 11, bold: true, margin: 0, valign: "middle" });
    s.addText(String(n), { x: 9.0, y: 5.13, w: 0.4, h: 0.32, fontFace: MAN, fontSize: 9, color: MID, align: "right", valign: "middle", margin: 0 });
  };
  const overline = (s, t, color = PURPLE) => s.addText(t.toUpperCase(),
    { x: MX, y: 0.4, w: 8.8, h: 0.3, fontFace: SYNE, fontSize: 11, bold: true, color, charSpacing: 3, margin: 0 });
  const titleTx = (s, t, size = 28) => s.addText(t,
    { x: MX, y: 0.7, w: 8.8, h: 0.9, fontFace: SYNE, fontSize: size, bold: true, color: INK, margin: 0, valign: "top" });
  const content = (ov, t, n, size) => {
    const s = p.addSlide(); s.background = { color: BG };
    overline(s, ov); titleTx(s, t, size); footer(s, n); return s;
  };
  const bullets = (s, items, o = {}) => {
    const opt = Object.assign({ x: MX, y: 1.9, w: 8.8, h: 3.0, fontFace: MAN, fontSize: 15, color: INK }, o);
    s.addText(items.map((it) => {
      const [txt, sub] = Array.isArray(it) ? it : [it, false];
      return { text: txt, options: { bullet: { indent: 16 }, breakLine: true, paraSpaceAfter: 9, color: sub ? GREY : opt.color, fontSize: sub ? opt.fontSize - 2 : opt.fontSize } };
    }), opt);
  };
  const fig = (s, file, o = {}) => exists(path.join(FIG, file)) &&
    s.addImage(Object.assign({ path: path.join(FIG, file), x: 4.55, y: 1.5, w: 5.0, h: 5.0 * 4.2 / 6.2 }, o));
  const dbox = (s, x, y, w, h, title, sub, o = {}) => {
    const txt = [{ text: title, options: { bold: true, fontSize: o.fs || 12.5, color: o.color || INK, breakLine: true } }];
    if (sub) txt.push({ text: sub, options: { fontSize: (o.fs || 12.5) - 3, color: GREY } });
    s.addText(txt, { x, y, w, h, shape: RR, fill: { color: o.fill || PANEL }, line: { color: o.line || LILAC, width: o.lw || 1.25 },
      rectRadius: 0.07, fontFace: MAN, align: "center", valign: "middle", margin: 4 });
  };
  const arr = (s, x, y, w, h, o = {}) => s.addShape(LINE,
    { x, y, w, h, line: { color: o.color || MID, width: o.width || 1.75, endArrowType: "triangle", dashType: o.dash || "solid" } });
  const code = (s, lines, x, y, w, o = {}) => {
    s.addShape(RR, { x: x - 0.1, y: y - 0.1, w: w + 0.2, h: (o.h || 0.32 * lines.length) + 0.2, fill: { color: INK }, line: { color: PDARK, width: 1 }, rectRadius: 0.05 });
    s.addText(lines.map((t) => ({ text: t, options: { breakLine: true } })),
      { x, y, w, h: o.h || 0.32 * lines.length, fontFace: MONO, fontSize: o.fs || 12, color: ICE, margin: 0, lineSpacingMultiple: 1.15 });
  };
  const qrBlock = (s, file, label, x, y, size = 1.35) => {
    if (exists(path.join(QR, file))) s.addImage({ path: path.join(QR, file), x, y, w: size, h: size });
    s.addText(label, { x: x - 0.3, y: y + size + 0.05, w: size + 0.6, h: 0.3, fontFace: MAN, fontSize: 11, bold: true, color: INK, align: "center", margin: 0 });
  };
  // a war-story slide: big punch number/quote + the lesson
  const warStory = (n, kicker, punch, story, lesson) => {
    const s = p.addSlide(); s.background = { color: BG };
    overline(s, "War story");
    s.addText(kicker, { x: MX, y: 0.72, w: 8.8, h: 0.5, fontFace: SYNE, fontSize: 24, bold: true, color: INK, margin: 0 });
    s.addText(punch, { x: MX, y: 1.6, w: 8.8, h: 1.0, fontFace: SYNE, fontSize: 40, bold: true, color: PURPLE, margin: 0, valign: "middle" });
    s.addText(story, { x: MX, y: 2.85, w: 8.8, h: 1.2, fontFace: MAN, fontSize: 16, color: INK, margin: 0 });
    s.addShape(RECT, { x: MX, y: 4.25, w: 0.1, h: 0.5, fill: { color: PURPLE } });
    s.addText([{ text: "Lesson  ", options: { bold: true, color: PDARK } }, { text: lesson, options: { color: GREY } }],
      { x: MX + 0.24, y: 4.25, w: 8.6, h: 0.5, fontFace: MAN, fontSize: 14, valign: "middle", margin: 0 });
    footer(s, n);
  };
  // a head-to-head row: label A (winner) vs label B, with the verdict
  const versus = (s, y, a, an, b, bn, verdict) => {
    s.addShape(RR, { x: 0.7, y, w: 8.6, h: 0.92, fill: { color: PANEL }, line: { color: LILAC, width: 1 }, rectRadius: 0.06 });
    s.addText([{ text: a + "  ", options: { bold: true, color: INK, fontSize: 15 } }, { text: an, options: { bold: true, color: GREEN, fontSize: 17 } }],
      { x: 0.9, y: y + 0.06, w: 4.0, h: 0.8, fontFace: MAN, valign: "middle", margin: 0 });
    s.addText("vs", { x: 4.6, y, w: 0.5, h: 0.92, fontFace: SYNE, fontSize: 12, italic: true, color: MID, align: "center", valign: "middle", margin: 0 });
    s.addText([{ text: b + "  ", options: { color: GREY, fontSize: 14 } }, { text: bn, options: { bold: true, color: RED, fontSize: 16 } }],
      { x: 5.1, y: y + 0.06, w: 4.0, h: 0.8, fontFace: MAN, valign: "middle", margin: 0 });
    s.addText(verdict, { x: 0.9, y: y + 0.5, w: 8.2, h: 0.36, fontFace: MAN, fontSize: 11.5, italic: true, color: PDARK, margin: 0 });
  };

  // 1 — Title
  let s = p.addSlide(); s.background = { color: INK };
  s.addImage({ data: lockupInv, x: MX, y: 0.5, w: 2.4, h: 2.4 * 110 / 692 });
  s.addText("AI TINKERERS · CALGARY · JUNE 23, 2026", { x: MX, y: 1.55, w: 9, h: 0.3, fontFace: SYNE, fontSize: 11, bold: true, color: PURPLE, charSpacing: 3, margin: 0 });
  s.addText("Context Engineering", { x: MX, y: 1.95, w: 9, h: 0.9, fontFace: SYNE, fontSize: 42, bold: true, color: WHITE, margin: 0 });
  s.addText("Inside the Harness", { x: MX, y: 2.85, w: 9, h: 0.9, fontFace: SYNE, fontSize: 42, bold: true, color: PURPLE, margin: 0 });
  s.addText("Which way of forgetting keeps a long-running agent alive? A live tour.", { x: MX, y: 3.85, w: 9, h: 0.4, fontFace: MAN, fontSize: 16, color: ICE, margin: 0 });
  s.addText([{ text: "Kanishk Patel", options: { bold: true, color: WHITE } }, { text: "   ·   Founsi AI   ·   Learn Agentic AI", options: { color: MID } }],
    { x: MX, y: 4.7, w: 9, h: 0.4, fontFace: MAN, fontSize: 12, margin: 0 });

  // 2 — The thesis
  s = p.addSlide(); s.background = { color: BG };
  overline(s, "The whole idea");
  s.addText([{ text: "The model is ", options: { color: INK } }, { text: "rented", options: { color: GREY, italic: true } }, { text: ".", options: { color: INK } }],
    { x: 0.8, y: 1.6, w: 8.4, h: 0.85, fontFace: SYNE, fontSize: 34, bold: true, align: "center", margin: 0 });
  s.addText([{ text: "The ", options: { color: INK } }, { text: "harness", options: { color: PURPLE, italic: true } }, { text: " is the part you build.", options: { color: INK } }],
    { x: 0.8, y: 2.45, w: 8.4, h: 0.85, fontFace: SYNE, fontSize: 34, bold: true, align: "center", margin: 0 });
  s.addText("And the single most important thing it does is decide what to forget. Get that wrong and the agent drifts, repeats, and dies. Tonight: the code that gets it right, and how the memory systems you already use actually perform.",
    { x: 1.2, y: 3.55, w: 7.6, h: 0.9, fontFace: MAN, fontSize: 14, color: GREY, align: "center", margin: 0 });
  footer(s, 2);

  // 3 — Architecture
  s = content("The architecture", "Three moving parts.", 3, 27);
  dbox(s, 0.7, 1.65, 8.7, 0.72, "Agent loop", "perceive → think → act → repeat   (harness/loop.py, ~80 lines)", { fs: 13, fill: PANEL });
  arr(s, 5.05, 2.37, 0, 0.33, { color: PURPLE });
  dbox(s, 0.7, 2.75, 3.7, 0.95, "ContextManager", "maybe_compact(): over budget? forget the middle", { fs: 13, fill: WASH, line: PURPLE, color: PDARK });
  arr(s, 4.4, 3.22, 0.45, 0);
  dbox(s, 4.85, 2.75, 2.3, 0.95, "Compaction policy", "1 of 7, swappable", { fs: 12.5 });
  arr(s, 7.15, 3.22, 0.4, 0);
  dbox(s, 7.55, 2.75, 1.85, 0.95, "Store", "raw, retrievable", { fs: 12.5 });
  arr(s, 2.55, 3.7, 0, 0.35, { color: PURPLE });
  dbox(s, 0.7, 4.05, 8.7, 0.72, "Every run → a folder", "manifest · every prompt · results · figures   (judge-scored, reproducible)", { fs: 13, fill: PANEL });
  footer(s, 3);

  // 4 — The constraint (backdrop for window.py _safe_split)
  s = content("The constraint that bites everyone", "Never split a tool-call from its result.", 4, 25);
  code(s, [
    "def _safe_split(body, proposed):",
    "    # the kept tail can't start on a 'tool' message",
    "    idx = proposed",
    "    while body[idx].role == 'tool':",
    "        idx += 1",
    "    return idx",
  ], 1.0, 2.0, 5.6, { fs: 12.5 });
  bullets(s, [
    "Cut the transcript between a call and its result, and a real API rejects the whole thing.",
    ["5 lines. The difference between an agent that runs and a 400 error.", true],
    "Trade-off: you can't always cut exactly at the budget line.",
  ], { x: 6.9, y: 2.0, w: 2.7, fontSize: 13 });

  // 5 — Demo card (run.py + compare)
  s = p.addSlide(); s.background = { color: INK };
  s.addText("LIVE", { x: MX, y: 1.35, w: 9, h: 0.4, fontFace: SYNE, fontSize: 13, bold: true, color: PURPLE, charSpacing: 4, margin: 0 });
  s.addText("Watch it grow, COMPACT, snap back, keep going.", { x: MX, y: 1.8, w: 9, h: 1.3, fontFace: SYNE, fontSize: 32, bold: true, color: WHITE, margin: 0 });
  s.addText("python run.py     ·     cat run/notes.md", { x: MX, y: 3.25, w: 9, h: 0.4, fontFace: MONO, fontSize: 15, color: PURPLE, margin: 0 });
  s.addText("python -m harness.compare \"...\"     # 7 policies, one needle, who keeps it", { x: MX, y: 3.75, w: 9, h: 0.4, fontFace: MONO, fontSize: 14, color: ICE, margin: 0 });
  s.addText("Offline. No key. The window forgets; the scratchpad does not.", { x: MX, y: 4.3, w: 9, h: 0.4, fontFace: MAN, fontSize: 14, color: MID, margin: 0 });
  footer(s, 5, true);

  // 6 — Headline: you are not alone (the map)
  s = content("You are not alone", "The famous memory systems are the same seam.", 6, 25);
  bullets(s, [
    ["LangChain  summary-buffer", true], "→ compact. A rolling summary. Literally my 15-line recency.",
    ["Chroma", true], "→ externalize. A vector store behind the same add / retrieve.",
    ["Mem0", true], "→ externalize, but an LLM extracts and dedupes facts first.",
    ["MemGPT / Letta", true], "→ pin + externalize. Agent-managed core blocks + an archival DB.",
    ["Anthropic multi-agent", true], "→ isolate. Sub-agents, each a fresh window.",
  ], { y: 1.7, fontSize: 14 });
  s.addText("All points on one map. So I wrapped each behind the same interface and benched it.",
    { x: MX, y: 4.85, w: 8.8, h: 0.35, fontFace: MAN, fontSize: 12.5, italic: true, color: PDARK, margin: 0 });

  // 7 — Headline: I measured them (the numbers)
  s = content("And I measured them", "The defaults are not the right choice.", 7, 24);
  versus(s, 1.65, "our 15-line recency", "0.45", "LangChain summary-buffer", "0.35",
    "The framework default bought a dependency, not accuracy — and cost more tokens.");
  versus(s, 2.75, "nv-embedqa store", "0.50", "MiniLM (general, local)", "0.35",
    "Same policy, swap only the embedder: the embedding model alone is +0.15.");
  s.addShape(RR, { x: 0.7, y: 3.85, w: 8.6, h: 0.92, fill: { color: PANEL }, line: { color: LILAC, width: 1 }, rectRadius: 0.06 });
  s.addText([{ text: "Mem0  ", options: { bold: true, color: INK, fontSize: 15 } },
             { text: "distills raw text → deduped facts", options: { color: GREY, fontSize: 14 } }],
    { x: 0.9, y: 3.91, w: 8.2, h: 0.5, fontFace: MAN, valign: "middle", margin: 0 });
  s.addText("Trailed storing the raw chunks, and cost an LLM call on every write. Compression lost the needle.",
    { x: 0.9, y: 4.35, w: 8.2, h: 0.36, fontFace: MAN, fontSize: 11.5, italic: true, color: PDARK, margin: 0 });

  // 8-12 — War stories
  warStory(8, "The metric that almost fooled me",
    "0.21  →  0.62", "Substring scoring made my best policy look like the worst. An LLM judge that credits paraphrase flipped it to best.",
    "Your eval can quietly invert your conclusion.");
  warStory(9, "The agent that froze at 0% CPU",
    "no error. just gone.", "Runs hung forever, Python idle, past the library timeout. Fix: a hard wall-clock watchdog on a worker thread (nim.py).",
    "Do not trust a library's timeout.");
  warStory(10, "The reasoning model that wouldn't shut up",
    "2k–20k token 'summaries'", "Asked to compress, it rambled; turning thinking off corrupted it. Fix: a split summarizer (fast model compacts, reasoning model answers).",
    "Reasoning models are bad compactors.");
  warStory(11, "The confound I caught the day before",
    "0.67  →  0.53", "My 70B headline win shrank once I held the summarizer constant. The win was partly the summarizer, not the answer model.",
    "Isolate your variable, even when it costs the headline.");
  warStory(12, "Making the famous systems actually run",
    "py3.9. torch. input_type.", "nv-embedqa needs an input_type the stock client never sends. Torch too old for the GPU embedders. Mem0's vector store would not import on Python 3.9.",
    "Half of 'use the famous system' is making it run at all.");

  // 13 — Payoff: the inversion
  s = content("And so what?", "The best way to forget depends on the task.", 13, 24);
  fig(s, "EXP-004_transfer_v1.png", { x: 0.7, y: 1.5, w: 5.3, h: 3.6 });
  bullets(s, [
    "Same 7 policies, two task types, three model sizes.",
    "The ranking INVERTS: summarize for factual, keep-the-raw for memory.",
    ["The one policy never in the loser group keeps BOTH a summary and the raw.", true],
    "Error bars are bootstrap 95% CIs (FRAMES is still noisy at n=30).",
  ], { x: 6.2, y: 1.65, w: 3.3, fontSize: 12.5 });

  // 14 — Payoff: the default is weak
  s = content("And so what?", "The policy that ships in most agents is weak.", 14, 24);
  s.addShape(RECT, { x: 0.7, y: 1.8, w: 8.6, h: 0.95, fill: { color: PANEL }, line: { color: LILAC, width: 1 } });
  s.addText([{ text: "recency summary  ", options: { bold: true, color: INK, fontSize: 18 } },
             { text: "= truncation's accuracy,  ", options: { color: GREY, fontSize: 16 } },
             { text: "7× the cost.", options: { bold: true, color: RED, fontSize: 18 } }],
    { x: 0.9, y: 1.8, w: 8.2, h: 0.95, fontFace: MAN, valign: "middle", margin: 0 });
  bullets(s, [
    "Summarizing the stale middle bought nothing over just dropping it, under pressure.",
    "Sub-agent isolation: same accuracy as keeping turns, 5× the cost. A trap on this task.",
    ["Both are cost-normalized negatives that anyone running agents can use today.", true],
  ], { y: 3.05, fontSize: 14 });

  // 15 — The principle
  s = p.addSlide(); s.background = { color: INK };
  s.addText([{ text: "Keep the raw ", options: { color: WHITE } }, { text: "retrievable", options: { color: PURPLE, italic: true } }, { text: ".", options: { color: WHITE } }],
    { x: 0.8, y: 2.1, w: 8.4, h: 1.0, fontFace: SYNE, fontSize: 38, bold: true, align: "center", margin: 0 });
  s.addText("One principle survives task type, model size, and the OSS systems: forget cheaply in-window, but keep the detail recoverable.",
    { x: 1.3, y: 3.2, w: 7.4, h: 0.8, fontFace: MAN, fontSize: 15, color: ICE, align: "center", margin: 0 });
  footer(s, 15, true);

  // 16 — Reproducible
  s = content("How to check me", "Every number is a folder you can open.", 16, 25);
  bullets(s, [
    "Each run: experiments/runs/EXP-NNN__slug__UTC/ — config + git sha, every prompt and response, results.csv, the figure.",
    "Bootstrap CIs + McNemar tests (experiments/stats.py); seeded; rate-limited + cached so re-runs are free.",
    ["The bar: a stranger clones the repo and regenerates any figure. The whole study cost $0 (free NIM API).", true],
    "DECISIONS.md logs every call we made and every one we changed.",
  ], { fontSize: 13.5 });

  // 17 — Find me
  s = p.addSlide(); s.background = { color: INK };
  s.addText("FIND ME", { x: MX, y: 0.6, w: 9, h: 0.4, fontFace: SYNE, fontSize: 12, bold: true, color: PURPLE, charSpacing: 4, margin: 0 });
  s.addText("Clone it. Break it. Tell me I'm wrong.", { x: MX, y: 1.0, w: 9, h: 0.7, fontFace: SYNE, fontSize: 30, bold: true, color: WHITE, margin: 0 });
  qrBlock(s, "qr_repo.png", "Repo", 0.95, 2.3, 1.25);
  qrBlock(s, "qr_newsletter.png", "Learn Agentic AI", 3.25, 2.3, 1.25);
  qrBlock(s, "qr_x.png", "X · @above_almighty", 5.55, 2.3, 1.25);
  qrBlock(s, "qr_linkedin.png", "LinkedIn", 7.85, 2.3, 1.25);
  s.addText("github.com/kanishkpatel1995/agent-harness", { x: MX, y: 4.55, w: 9, h: 0.3, fontFace: MONO, fontSize: 11, color: ICE, align: "center", margin: 0 });
  footer(s, 17, true);

  await p.writeFile({ fileName: path.join(__dirname, "founsi-talk.pptx") });
  console.log("wrote presentation/founsi-talk.pptx (17 slides)");
})();
