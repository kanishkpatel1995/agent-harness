// Build the Founsi-branded deck for AI Tinkerers.
//   node presentation/build_deck.js  ->  founsi-context-engineering.pptx
// Full talk: title unpacked -> how long-running agents work -> the techniques (with
// flowchart diagrams) -> our technique & why it wins -> setup (datasets, metrics, models)
// -> results (mechanism, impact, model axis, cross-domain) -> what others see -> future
// work. Then a detailed appendix: protocol, every experiment, full matrices, implementation,
// model catalog, references. Brand: bg FAFAFE, ink 2E2C32, accent purple 9378FF.
const pptxgen = require("pptxgenjs");
const sharp = require("sharp");
const fs = require("fs");
const path = require("path");

const BRAND = path.join(__dirname, "brand");
const FIG = path.join(__dirname, "figures");
const QR = path.join(__dirname, "assets", "qr");
const BG = "FAFAFE", INK = "2E2C32", PURPLE = "9378FF", PDARK = "7B5EF0",
      GREY = "655E74", MID = "7E7A8A", WHITE = "FFFFFF", ICE = "CADCFC", WASH = "EFEBFF",
      MINT = "1B9E77", ORANGE = "D95F02", FLOOR = "B9B4C6", PANEL = "F4F2F8", LILAC = "D4C9FF";
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
  const RR = p.shapes.ROUNDED_RECTANGLE, RECT = p.shapes.RECTANGLE, LINE = p.shapes.LINE;

  // ---- chrome ----
  const footer = (s, n, dark = false) => {
    s.addImage({ data: markPurple, x: MX, y: 5.18, w: 0.24, h: 0.24 * 110 / 146 });
    s.addText([{ text: "Founsi", options: { color: dark ? WHITE : INK } }, { text: ".", options: { color: PURPLE } }],
      { x: MX + 0.3, y: 5.13, w: 1.4, h: 0.32, fontFace: SYNE, fontSize: 11, bold: true, margin: 0, valign: "middle" });
    s.addText(String(n), { x: 9.0, y: 5.13, w: 0.4, h: 0.32, fontFace: MAN, fontSize: 9, color: MID, align: "right", valign: "middle", margin: 0 });
  };
  const overline = (s, t, color = PURPLE) => s.addText(t.toUpperCase(),
    { x: MX, y: 0.4, w: 8.8, h: 0.3, fontFace: SYNE, fontSize: 11, bold: true, color, charSpacing: 3, margin: 0 });
  const titleTx = (s, t, size = 27) => s.addText(t,
    { x: MX, y: 0.7, w: 8.8, h: 0.85, fontFace: SYNE, fontSize: size, bold: true, color: INK, margin: 0, valign: "top" });
  const content = (ov, t, n, size) => {
    const s = p.addSlide(); s.background = { color: BG };
    overline(s, ov); titleTx(s, t, size); footer(s, n); return s;
  };
  const dark = (n) => { const s = p.addSlide(); s.background = { color: INK }; footer(s, n, true); return s; };
  const bullets = (s, items, o = {}) => {
    const opt = Object.assign({ x: MX, y: 1.8, w: 8.8, h: 3.1, fontFace: MAN, fontSize: 15, color: INK }, o);
    s.addText(items.map((it) => {
      const [txt, sub] = Array.isArray(it) ? it : [it, false];
      return { text: txt, options: { bullet: { indent: 16 }, breakLine: true, paraSpaceAfter: 8, color: sub ? GREY : opt.color, fontSize: sub ? opt.fontSize - 2 : opt.fontSize } };
    }), opt);
  };
  const fig = (s, file, o = {}) => exists(path.join(FIG, file)) &&
    s.addImage(Object.assign({ path: path.join(FIG, file), x: 4.55, y: 1.5, w: 5.0, h: 5.0 * 4.2 / 6.2 }, o));
  const rows = (s, items, y0 = 1.75, gap = 0.66) => items.forEach((m, i) => {
    const y = y0 + i * gap, hot = m[2];
    s.addShape(RECT, { x: MX, y, w: 0.1, h: 0.52, fill: { color: hot ? PURPLE : LILAC } });
    s.addText([{ text: m[0] + "  ", options: { bold: true, color: hot ? PURPLE : INK, fontSize: 15 } },
               { text: m[1], options: { color: GREY, fontSize: 12.5 } }],
      { x: MX + 0.24, y, w: 8.7, h: 0.52, fontFace: MAN, valign: "middle", margin: 0 });
  });
  const qrBlock = (s, file, label, x, y, size = 1.35) => {
    if (exists(path.join(QR, file))) s.addImage({ path: path.join(QR, file), x, y, w: size, h: size });
    s.addText(label, { x: x - 0.3, y: y + size + 0.05, w: size + 0.6, h: 0.3, fontFace: MAN, fontSize: 11, bold: true, color: INK, align: "center", margin: 0 });
  };
  // ---- diagram primitives ----
  const dbox = (s, x, y, w, h, title, sub, o = {}) => {
    const txt = [{ text: title, options: { bold: true, fontSize: o.fs || 12, color: o.color || INK, breakLine: true } }];
    if (sub) txt.push({ text: sub, options: { fontSize: (o.fs || 12) - 3, color: GREY } });
    s.addText(txt, { x, y, w, h, shape: RR, fill: { color: o.fill || PANEL }, line: { color: o.line || LILAC, width: o.lw || 1.25 },
      rectRadius: 0.07, fontFace: MAN, align: "center", valign: "middle", margin: 4 });
  };
  const arr = (s, x, y, w, h, o = {}) => s.addShape(LINE,
    { x, y, w, h, line: { color: o.color || MID, width: o.width || 1.75, endArrowType: o.end === false ? "none" : "triangle", beginArrowType: o.bi ? "triangle" : "none", dashType: o.dash || "solid" } });
  const tag = (s, x, y, w, t, color = PURPLE) => s.addText(t,
    { x, y, w, h: 0.32, shape: RR, fill: { color: WHITE }, line: { color, width: 1 }, rectRadius: 0.05, fontFace: MAN, fontSize: 10.5, bold: true, color, align: "center", valign: "middle", margin: 1 });
  const caption = (s, t, y = 5.0) => s.addText(t, { x: MX, y, w: 8.8, h: 0.32, fontFace: MAN, fontSize: 12, italic: true, color: GREY, margin: 0 });

  // ============================ MAIN DECK ============================
  // 1 — Title
  let s = p.addSlide(); s.background = { color: INK };
  s.addImage({ data: lockupInv, x: MX, y: 0.5, w: 2.4, h: 2.4 * 110 / 692 });
  s.addText("AI TINKERERS · CALGARY · JUNE 23, 2026", { x: MX, y: 1.55, w: 9, h: 0.3, fontFace: SYNE, fontSize: 11, bold: true, color: PURPLE, charSpacing: 3, margin: 0 });
  s.addText("Context Engineering", { x: MX, y: 1.95, w: 9, h: 0.9, fontFace: SYNE, fontSize: 42, bold: true, color: WHITE, margin: 0 });
  s.addText("Inside the Harness", { x: MX, y: 2.85, w: 9, h: 0.9, fontFace: SYNE, fontSize: 42, bold: true, color: PURPLE, margin: 0 });
  s.addText("Which way of forgetting keeps a long-running agent alive?", { x: MX, y: 3.85, w: 9, h: 0.4, fontFace: MAN, fontSize: 16, color: ICE, margin: 0 });
  s.addText([{ text: "Kanishk Patel", options: { bold: true, color: WHITE } }, { text: "   ·   Founsi AI   ·   Learn Agentic AI", options: { color: MID } }],
    { x: MX, y: 4.7, w: 9, h: 0.4, fontFace: MAN, fontSize: 12, margin: 0 });

  // 2 — The title, unpacked
  s = content("The title, unpacked", "Three words, one thesis.", 2, 27);
  rows(s, [
    ["Context engineering", "deciding what the model sees on every single turn — the working set, not the prompt."],
    ["Long-running", "agents that take 50+ steps, where the transcript outgrows the window."],
    ["Inside the harness", "the code around the model — pin, truncate, compact, externalize, cap — is where you win or lose."],
  ], 1.85, 0.72);
  s.addText([{ text: "Thesis:  ", options: { bold: true, color: PURPLE } },
             { text: "the model is a commodity you rent; the harness is the part you build — and ", options: { color: INK } },
             { text: "which way it forgets decides whether the agent survives.", options: { bold: true, color: INK } }],
    { x: MX, y: 4.25, w: 8.8, h: 0.7, fontFace: MAN, fontSize: 14, margin: 0 });

  // ---- SECTION: how long-running agents work ----
  // 3 — Agent loop 101 (diagram)
  s = content("How long-running agents work", "The loop is trivial. The transcript is not.", 3, 24);
  const cx = 2.0, cyc = [["Perceive", "read tool results", 0.7, 1.75], ["Think", "the LLM call", 4.0, 1.75], ["Act", "call a tool", 7.0, 1.75]];
  cyc.forEach((b) => dbox(s, b[2], b[3], 2.1, 0.8, b[0], b[1], { fs: 13 }));
  arr(s, 2.8, 2.15, 1.2, 0);
  arr(s, 6.1, 2.15, 0.9, 0);
  arr(s, 8.05, 2.6, 0, 0.55); // act down
  arr(s, 8.05, 3.15, -6.4, 0, { color: PURPLE }); // loop back
  arr(s, 1.65, 3.15, 0, -0.55, { color: PURPLE });
  s.addText("every turn appends to the message list", { x: 5.1, y: 3.2, w: 3.6, h: 0.3, fontFace: MAN, fontSize: 11, italic: true, color: PURPLE, align: "center", margin: 0 });
  bullets(s, [
    "The model is stateless — each turn it gets ONE list of messages, and that list is the agent's entire mind.",
    ["Every loop appends: tool outputs, reasoning, results. The working set only grows.", true],
  ], { y: 3.75, fontSize: 13.5 });

  // 4 — The wall
  s = content("How long-running agents work", "Brilliant at 5 steps. Dead at 50.", 4, 25);
  bullets(s, [
    "Cost scales — you re-send the whole history every single turn.",
    "Latency scales — time-to-first-token grows with prompt length.",
    "Attention dilutes — the model gets lost in the middle.",
    ["Then it dies — drifts, repeats, forgets the goal, hits the hard limit.", true],
  ], { y: 1.85, w: 5.1 });
  s.addShape(RECT, { x: 6.3, y: 2.2, w: 3.0, h: 0.55, fill: { color: "F7C1C1" } });
  s.addText("context_length_exceeded", { x: 6.3, y: 2.2, w: 3.0, h: 0.55, fontFace: MONO, fontSize: 12, bold: true, color: "A32D2D", align: "center", valign: "middle", margin: 0 });
  s.addText("step 51 →", { x: 6.3, y: 2.85, w: 3.0, h: 0.3, fontFace: MAN, fontSize: 11, italic: true, color: GREY, align: "center", margin: 0 });

  // 5 — The reframe
  s = p.addSlide(); s.background = { color: BG };
  overline(s, "The reframe");
  s.addText([{ text: "The context window is a ", options: { color: INK } }, { text: "budget", options: { color: PURPLE, italic: true } }, { text: ",", options: { color: INK } }],
    { x: 0.8, y: 1.85, w: 8.4, h: 0.85, fontFace: SYNE, fontSize: 33, bold: true, align: "center", margin: 0 });
  s.addText([{ text: "not a ", options: { color: INK } }, { text: "backpack", options: { color: GREY, italic: true } }, { text: ".", options: { color: INK } }],
    { x: 0.8, y: 2.7, w: 8.4, h: 0.85, fontFace: SYNE, fontSize: 33, bold: true, align: "center", margin: 0 });
  s.addText("A bigger window raises the ceiling, not the curve. Engineer the working set and keep it roughly constant — no matter how long the run.",
    { x: 1.4, y: 3.75, w: 7.2, h: 0.7, fontFace: MAN, fontSize: 14, color: GREY, align: "center", margin: 0 });
  footer(s, 5);

  // 6 — Why it breaks (lost in the middle)
  s = content("Why it breaks", "A long raw context is worse than a short clean one.", 6, 24);
  fig(s, "EXP-002_recall_vs_length_v1.png", { x: 0.7, y: 1.5, w: 5.3, h: 3.64 });
  bullets(s, [
    "Lost-in-the-middle: as context grows, the model attends to the ends, not the middle.",
    "Raw no-compaction collapses 0.62 → 0.12 as the run lengthens.",
    ["Compaction holds flat near 0.58 — a short clean summary beats a long raw transcript.", true],
    "So compaction is net-positive, not just survival.",
  ], { x: 6.2, y: 1.65, w: 3.3, fontSize: 12.5 });

  // 7 — The job: compaction
  s = content("The job", "Compaction: summarize the middle, drop the raw turns.", 7, 24);
  bullets(s, [
    "Over budget? Replace the stale middle with one dense summary; throw the raw turns away.",
    "Why the middle? It's the low-attention zone anyway — lost in the middle.",
    ["The gotcha: never split a tool-call from its result — real APIs reject that transcript (we preserve the pairing in _safe_split).", true],
    "Lossy on purpose — and the whole question is: lossy which way?",
  ]);

  // ---- SECTION: techniques ----
  // 8 — The landscape
  s = content("The techniques · the landscape", "Everyone compacts. Nobody measured which way is best.", 8, 22);
  rows(s, [
    ["Anthropic", "names the moves — compaction, structured note-taking, “context rot.”"],
    ["Cognition (Devin)", "“context engineering is the #1 job”; don't fragment it across agents."],
    ["LangChain · LlamaIndex", "memory abstractions — summary buffers, vector memory."],
    ["MemGPT · Letta", "treat the window like RAM; page facts to an external store."],
    ["RAG (Lewis, 2020)", "retrieve from a store instead of stuffing the prompt."],
  ]);

  // 9 — All seven policies at a glance (table)
  s = content("The techniques · at a glance", "Seven ways to forget (cost = relative tokens).", 9, 25);
  const tdata = [
    ["policy", "what it does", "keeps", "cost"],
    ["truncate", "drop the oldest raw turns", "recent only", "$"],
    ["recency", "summarize stale middle (shipped default)", "summary + recent", "$$"],
    ["importance", "keep highest-signal turns verbatim", "key turns", "$$$"],
    ["semantic", "cluster by topic, summarize each", "topic structure", "$$$$"],
    ["externalize", "write raw to a store, retrieve at answer", "all (indexed)", "$"],
    ["subagent", "isolate sub-tasks in fresh windows", "per-task context", "$$$$$"],
    ["reversible_hybrid", "summary in window + raw retrievable", "both", "$$"],
  ];
  const colX = [MX, 2.2, 5.1, 8.3], colW = [1.6, 2.9, 3.1, 1.1];
  tdata.forEach((r, i) => {
    const y = 1.5 + i * 0.44, head = i === 0, hot = r[0] === "reversible_hybrid";
    if (hot) s.addShape(RECT, { x: MX - 0.05, y: y - 0.02, w: 8.95, h: 0.44, fill: { color: WASH } });
    r.forEach((c, j) => s.addText(c, { x: colX[j], y, w: colW[j], h: 0.40, fontFace: head ? SYNE : MAN, fontSize: head ? 11 : 12,
      bold: head || hot || j === 0, color: head ? PURPLE : (hot ? PDARK : (j === 3 ? GREY : INK)), valign: "middle", margin: 0 }));
  });

  // 10 — Flowcharts: truncate vs recency
  s = content("The techniques · flow", "Drop it, or summarize the middle.", 10, 25);
  const flow = (s, y0, name, color, steps, note) => {
    s.addText(name, { x: MX, y: y0, w: 2.0, h: 0.7, fontFace: MAN, fontSize: 13.5, bold: true, color, valign: "middle", margin: 0 });
    let x = 2.4;
    steps.forEach((st, i) => {
      dbox(s, x, y0, st[1], 0.7, st[0], st[2], { fs: 11, fill: st[3] || PANEL, line: st[4] || LILAC, color: st[5] || INK });
      if (i < steps.length - 1) { arr(s, x + st[1], y0 + 0.35, 0.3, 0); x += st[1] + 0.3; }
    });
    if (note) s.addText(note, { x: 2.4, y: y0 + 0.74, w: 7.0, h: 0.26, fontFace: MAN, fontSize: 10, italic: true, color: GREY, margin: 0 });
  };
  flow(s, 1.7, "truncate", FLOOR, [["window", 1.4, "[old … recent]"], ["drop old", 1.5, "no LLM"], ["recent only", 1.6, "facts lost"]], "Cheapest. Loses the most — old facts vanish without a trace.");
  flow(s, 3.4, "recency", ORANGE, [["window", 1.4, "[old … recent]"], ["summarize middle", 1.8, "1 LLM call"], ["summary + recent", 1.9, "stale flattened"]], "The default in Claude Code / LangChain. Flattens the middle into one summary.");
  caption(s, "Both are summary-or-drop: once a fact leaves the window, only the (possibly lossy) summary remains.");

  // 11 — Flowcharts: importance vs semantic
  s = content("The techniques · flow", "Keep the signal, or cluster the topics.", 11, 25);
  flow(s, 1.7, "importance", PURPLE, [["window", 1.4, "[turns]"], ["rank by signal", 1.7, "score turns"], ["keep top verbatim", 1.9, "structure kept"]], "Keeps the highest-signal turns word-for-word; drops the chatter.");
  flow(s, 3.4, "semantic", MINT, [["window", 1.4, "[turns]"], ["cluster by topic", 1.8, "embeddings"], ["summarize each", 1.8, "topic map"]], "Groups by topic, summarizes each cluster — preserves the shape of the work.");
  caption(s, "Structure-preserving: these led on FRAMES factual QA, where a summarized reasoning chain helps.");

  // 12 — Flowcharts: externalize vs subagent
  s = content("The techniques · flow", "Page it out, or spin up a fresh mind.", 12, 25);
  flow(s, 1.7, "externalize", INK, [["window", 1.4, "[turns]"], ["write raw → store", 1.9, "embeddings"], ["retrieve at answer", 1.9, "k-NN lookup"]], "Pages raw turns to a vector store; pulls the relevant ones back at answer time.");
  flow(s, 3.4, "subagent", GREY, [["task", 1.4, "sub-goal"], ["fresh window", 1.7, "isolated run"], ["return result", 1.8, "5x the cost"]], "Isolates a sub-task in its own clean window — the multi-agent move. Expensive.");
  caption(s, "Retrieval-based: externalize keeps the literal fact, which wins on conversational memory.");

  // 13 — Our technique: reversible-hybrid (diagram)
  s = content("Our technique", "reversible-hybrid: keep the summary AND the raw.", 13, 24);
  dbox(s, 0.7, 2.05, 1.7, 0.95, "stale window", "[old turns]", { fs: 12 });
  arr(s, 2.45, 2.5, 0.45, 0);
  dbox(s, 2.95, 1.45, 1.9, 0.85, "summary", "in the window", { fs: 12, fill: WASH, line: PURPLE, color: PDARK });
  dbox(s, 2.95, 2.65, 1.9, 0.85, "raw turns", "→ embedding store", { fs: 12, fill: PANEL, line: INK });
  arr(s, 2.9, 2.2, 0.05, -0.3); arr(s, 2.9, 2.85, 0.05, 0.3);
  dbox(s, 5.5, 1.45, 1.9, 0.85, "answer prompt", "summary + recent", { fs: 12, fill: WASH, line: PURPLE, color: PDARK });
  arr(s, 4.85, 1.85, 0.65, 0);
  arr(s, 4.85, 3.05, 2.55, -0.55, { color: INK, dash: "dash" });
  dbox(s, 7.7, 1.85, 1.7, 0.95, "retrieve top-k", "raw, on demand", { fs: 12, fill: PANEL, line: INK });
  arr(s, 7.4, 1.9, 0.3, 0.2);
  caption(s, "The summary keeps the gist cheaply in-window; the raw stays losslessly retrievable. It is the only policy that hedges both ways.", 4.05);
  caption(s, "Novel here: prior memory systems do one or the other — we keep both and measure the payoff.", 4.45);

  // 14 — Why we think it wins
  s = content("Our technique", "Why we bet on it.", 14, 25);
  bullets(s, [
    "Summary-only loses specific facts (dates, numbers) — fatal on memory tasks.",
    "Retrieval-only lacks the compressed reasoning chain — weaker on multi-hop factual tasks.",
    ["The hybrid carries both, so it can pick up whichever mechanism the task needs.", true],
    "Prediction: never the single best, but never in the loser group — robust across task type and model size.",
    "That cross-domain robustness, not one peak score, is the case for keeping the raw retrievable.",
  ], { fontSize: 14 });

  // ---- SECTION: setup ----
  // 15 — How we test it (protocol)
  s = content("How we test it", "Mechanism first, then impact.", 15, 25);
  dbox(s, 0.7, 1.8, 4.0, 1.0, "Layer 1 · Mechanism", "Does a planted fact survive a compaction? Does compaction beat raw as context grows?", { fs: 13, fill: PANEL });
  dbox(s, 5.1, 1.8, 4.0, 1.0, "Layer 2 · Impact", "On a real agent answering real questions, which policy wins, and at what cost?", { fs: 13, fill: WASH, line: PURPLE, color: PDARK });
  arr(s, 4.7, 2.3, 0.4, 0, { color: PURPLE });
  bullets(s, [
    "A minimal, readable agent harness — the loop is ~100 lines; the ContextManager is the point.",
    "Every run is a traceable folder: manifest + every prompt + results + figures (reproducible).",
    ["The bar: a stranger clones the repo and regenerates the figure.", true],
  ], { y: 3.1, fontSize: 13.5 });

  // 16 — Datasets (diagrams)
  s = content("The datasets", "Two task types, on purpose.", 16, 25);
  dbox(s, 0.7, 1.7, 4.0, 0.55, "FRAMES — multi-hop factual QA", null, { fs: 13, fill: WASH, line: PURPLE, color: PDARK });
  [["Q", "multi-hop question"], ["A1..A5", "gold Wikipedia articles"], ["answer", "reason across them"]].forEach((b, i) =>
    dbox(s, 0.7 + i * 1.35, 2.4, 1.2, 0.7, b[0], b[1], { fs: 10.5 }));
  arr(s, 1.9, 2.75, 0.15, 0); arr(s, 3.25, 2.75, 0.15, 0);
  s.addText("824 questions · oracle retrieval isolates compaction from search", { x: 0.7, y: 3.2, w: 4.0, h: 0.3, fontFace: MAN, fontSize: 10, italic: true, color: GREY, margin: 0 });
  dbox(s, 5.1, 1.7, 4.0, 0.55, "LoCoMo — conversational memory", null, { fs: 13, fill: PANEL, line: INK });
  [["S1", ""], ["S2", ""], ["…", ""], ["S19", "sessions"]].forEach((b, i) =>
    dbox(s, 5.1 + i * 1.02, 2.4, 0.9, 0.7, b[0], b[1], { fs: 10.5 }));
  s.addText("10 convos · ~19 sessions · ~150 Qs each — facts scattered across the history", { x: 5.1, y: 3.2, w: 4.0, h: 0.3, fontFace: MAN, fontSize: 10, italic: true, color: GREY, margin: 0 });
  bullets(s, [
    "FRAMES rewards a summarized reasoning chain; LoCoMo rewards exact scattered facts.",
    ["If the winner transfers across both, it is a property of the policy, not the benchmark.", true],
  ], { y: 3.75, fontSize: 13 });

  // 17 — Metrics
  s = content("The metrics", "What we measure, and why it's honest.", 17, 25);
  rows(s, [
    ["LLM-as-judge", "credits a correct-but-paraphrased answer; substring match inverted the ranking (EXP-003a).", true],
    ["Accuracy", "fraction of questions answered correctly, judged by a fixed 70B."],
    ["Cost", "tokens billed per cell — the x-axis of every Pareto plot."],
    ["Latency", "per-call wall-clock, by model (approximate — observed, not logged per cell)."],
    ["Pressure", "compaction events per question; policy only matters when pressure is high."],
  ]);

  // 18 — Models & why
  s = content("The models", "A capability axis, on the free tier.", 18, 25);
  rows(s, [
    ["Llama 3.1 8B", "small instruct — the dev model; fast, cheap, runs the bulk of cells."],
    ["Llama 3.3 70B", "large instruct — does the 8B ranking hold as the model gets stronger?"],
    ["Nemotron 30B-A3B", "a reasoning model — does answer-time reasoning change the ranking? (FRAMES)"],
    ["70B judge (fixed)", "the same grader across every arm and model — the metric held constant.", true],
  ], 1.85, 0.72);
  caption(s, "All on the free NVIDIA NIM API. Every prompt + response saved; the response cache makes re-runs free.", 4.5);

  // ---- SECTION: results ----
  // 19 — Results: mechanism
  s = content("Results · mechanism", "Facts survive, and compaction beats raw.", 19, 24);
  fig(s, "EXP-002_recall_vs_length_v1.png", { x: 0.7, y: 1.5, w: 5.3, h: 3.64 });
  bullets(s, [
    "EXP-001: planted facts survive a compaction — truncation drops them, summaries keep ~2-3x more.",
    "EXP-002: the crossover — raw context collapses with length while compaction holds flat.",
    ["The mechanism that explains every impact result below.", true],
  ], { x: 6.2, y: 1.7, w: 3.3, fontSize: 12.5 });

  // 20 — Results: impact (the bake-off)
  s = content("Results · impact", "Under pressure, the policies separate.", 20, 24);
  fig(s, "EXP-003b_pareto_v1.png", { x: 0.7, y: 1.5, w: 5.3, h: 3.6 });
  bullets(s, [
    "First the metric: substring scoring made our hybrid look worst (0.21); the fair judge flipped it to best (0.62).",
    "Under high pressure the 7 arms separate on a clear Pareto frontier.",
    ["The shipped default (recency) is dominated by plain truncation — 7x the cost, no gain.", true],
    "Sub-agent isolation: 5x cost, no accuracy gain.",
  ], { x: 6.2, y: 1.6, w: 3.3, fontSize: 12 });

  // 21 — Results: model axis (FRAMES)
  s = content("Results · the model axis", "Capability widens the smart-vs-blind gap.", 21, 24);
  fig(s, "EXP-003c_modelaxis_v1.png", { x: 0.7, y: 1.5, w: 5.3, h: 3.5 });
  bullets(s, [
    "Five arms across 8B → 70B → reasoning, judge fixed at 70B.",
    "Blind truncation never improves (0.37, 0.27, 0.40) — a better model can't recover dropped context.",
    ["Every structure/retrieval arm climbs; the gap to truncation grows ~0.2 → ~0.3.", true],
    "Our reversible-hybrid leads at 0.70 on the reasoning model.",
  ], { x: 6.2, y: 1.6, w: 3.3, fontSize: 12 });

  // 22 — Results: cross-domain
  s = content("Results · cross-domain", "The ranking inverts — but the hybrid wins both.", 22, 24);
  fig(s, "EXP-004_transfer_v1.png", { x: 0.7, y: 1.5, w: 5.3, h: 3.6 });
  bullets(s, [
    "Same 5 arms on LoCoMo (memory) vs FRAMES (factual).",
    "Inversion: on memory, retrieval wins (externalize 0.55), pure summary collapses (semantic 0.27).",
    "Specific scattered facts survive a retrievable copy; a summary smooths them away.",
    ["reversible-hybrid is top-group in BOTH domains (0.47 / 0.54) — it keeps both.", true],
  ], { x: 6.2, y: 1.6, w: 3.3, fontSize: 12 });

  // 23 — Results: LoCoMo model axis
  s = content("Results · capability on memory", "Capability does not rescue summarization.", 23, 24);
  fig(s, "EXP-004_modelaxis_v1.png", { x: 0.7, y: 1.5, w: 5.3, h: 3.6 });
  bullets(s, [
    "LoCoMo, 8B → 70B. The mirror of FRAMES: every line flat or falling.",
    "Retrieval arms stay flat at the top (0.55, 0.53).",
    ["Summary arms fall — semantic 0.27 → 0.17 — the bigger model can't fill a fact the summary dropped.", true],
    "Retrieval wins on memory at every model size.",
  ], { x: 6.2, y: 1.6, w: 3.3, fontSize: 12 });

  // 24 — The full matrix
  s = content("Results · the full picture", "One policy wins every cell.", 24, 25);
  const M = [
    ["arm", "FR-8B", "FR-70B", "LC-8B", "LC-70B"],
    ["reversible_hybrid", "0.47", "0.67", "0.54", "0.53"],
    ["externalize", "0.40", "0.63", "0.55", "0.55"],
    ["importance", "0.50", "0.60", "0.26", "0.23"],
    ["semantic", "0.57", "0.53", "0.27", "0.17"],
    ["truncate", "0.37", "0.27", "0.12", "0.09"],
  ];
  const mX = [MX, 3.0, 4.4, 5.8, 7.2], mW = [2.4, 1.4, 1.4, 1.4, 1.4];
  M.forEach((r, i) => {
    const y = 1.7 + i * 0.5, head = i === 0, hot = r[0] === "reversible_hybrid";
    if (hot) s.addShape(RECT, { x: MX - 0.05, y: y - 0.03, w: 8.4, h: 0.5, fill: { color: WASH } });
    r.forEach((c, j) => s.addText(c, { x: mX[j], y, w: mW[j], h: 0.46, fontFace: head ? SYNE : MAN, fontSize: head ? 11.5 : 13,
      bold: head || hot || j === 0, color: head ? PURPLE : (hot ? PDARK : INK), valign: "middle", margin: 0 }));
  });
  caption(s, "FR = FRAMES (factual), LC = LoCoMo (memory). reversible-hybrid is in the top group of all four cells — the only arm that is.", 4.95);

  // 25 — Cost / latency / accuracy
  s = content("Results · cost & latency", "What each policy costs to run.", 25, 25);
  const C = [
    ["arm", "accuracy*", "tokens/q", "rel. latency"],
    ["truncate", "0.37", "1.2k", "fastest"],
    ["externalize", "0.40", "1.9k", "fast (+embed)"],
    ["reversible_hybrid", "0.47", "9.9k", "moderate"],
    ["importance", "0.50", "14.2k", "slow"],
    ["semantic", "0.57", "18.7k", "slowest"],
  ];
  const cX2 = [MX, 3.0, 5.0, 7.0], cW2 = [2.4, 2.0, 2.0, 2.2];
  C.forEach((r, i) => {
    const y = 1.65 + i * 0.5, head = i === 0, hot = r[0] === "reversible_hybrid";
    if (hot) s.addShape(RECT, { x: MX - 0.05, y: y - 0.03, w: 8.7, h: 0.5, fill: { color: WASH } });
    r.forEach((c, j) => s.addText(c, { x: cX2[j], y, w: cW2[j], h: 0.46, fontFace: head ? SYNE : MAN, fontSize: head ? 11.5 : 13,
      bold: head || hot || j === 0, color: head ? PURPLE : (hot ? PDARK : (j === 3 ? GREY : INK)), valign: "middle", margin: 0 }));
  });
  caption(s, "*FRAMES 8B high pressure (EXP-003b). Latency is per-call observed: 8B ~2s, 70B ~6-8s, nano ~5s; reasoning models bill ~6x tokens.", 4.7);

  // 26 — The through-line
  s = content("The through-line", "Six claims, now backed by evidence.", 26, 25);
  bullets(s, [
    "Policy matters only under pressure — at low pressure they tie.",
    "The metric must credit paraphrase — a careless metric inverts the ranking.",
    "The shipped default (recency summary) is weak — dominated by truncation under pressure.",
    "The smart-vs-blind gap widens with capability (FRAMES), and persists on memory (LoCoMo).",
    "The best single policy is task-dependent — summary on factual, retrieval on memory.",
    ["But the reversible-hybrid is robust: top group across task type AND model size. Keep the raw retrievable.", true],
  ], { fontSize: 13.5 });

  // 27 — Aligns with others
  s = content("This matches what others see", "We're not alone.", 27, 24);
  rows(s, [
    ["Lost in the Middle (2307.03172)", "long contexts attend to the ends — our EXP-002 crossover is the same effect."],
    ["MemGPT / Mem0 / Letta", "page facts to an external store — our externalize & hybrid win exactly where memory matters."],
    ["ACON (2510.00615)", "compress agent context; we add the which-way-is-best measurement."],
    ["Multi-agent debate", "our cost-normalized sub-agent arm favors the single-agent side on this task."],
    ["RAG (Lewis, 2020)", "retrieval-as-compaction — our hybrid is RAG fused with summary memory."],
  ]);

  // 28 — Future work + help
  s = content("Future work · how you can help", "Where this goes next.", 28, 25);
  bullets(s, [
    "Hold the summarizer constant across tiers — isolate the answer model perfectly.",
    "A reasoning tier on LoCoMo; larger N for tight error bars; more domains (code, web).",
    "Trained importance/semantic rankers instead of heuristics; a tuned reversible store.",
    "LangChain summary-memory as a head-to-head baseline arm.",
    ["You can help: try a policy on your agent, add a dataset, or PR an arm. It's all reproducible.", true],
  ], { fontSize: 14 });

  // 29 — Find me
  s = p.addSlide(); s.background = { color: INK };
  s.addText("FIND ME", { x: MX, y: 0.6, w: 9, h: 0.4, fontFace: SYNE, fontSize: 12, bold: true, color: PURPLE, charSpacing: 4, margin: 0 });
  s.addText("Clone it. Read the write-ups. Say hi.", { x: MX, y: 1.0, w: 9, h: 0.7, fontFace: SYNE, fontSize: 30, bold: true, color: WHITE, margin: 0 });
  qrBlock(s, "qr_repo.png", "Repo", 0.95, 2.3, 1.25);
  qrBlock(s, "qr_newsletter.png", "Learn Agentic AI", 3.25, 2.3, 1.25);
  qrBlock(s, "qr_x.png", "X · @above_almighty", 5.55, 2.3, 1.25);
  qrBlock(s, "qr_linkedin.png", "LinkedIn", 7.85, 2.3, 1.25);
  footer(s, 29, true);

  // ============================ APPENDIX ============================
  // 30 — divider
  s = p.addSlide(); s.background = { color: INK };
  s.addText("APPENDIX", { x: MX, y: 1.9, w: 9, h: 0.5, fontFace: SYNE, fontSize: 13, bold: true, color: PURPLE, charSpacing: 4, margin: 0 });
  s.addText("Every experiment, in detail", { x: MX, y: 2.35, w: 9, h: 0.9, fontFace: SYNE, fontSize: 34, bold: true, color: WHITE, margin: 0 });
  s.addText("Protocol · repo map · implementation · EXP-001 → 004 in full · cost model · references.",
    { x: MX, y: 3.4, w: 8.8, h: 0.5, fontFace: MAN, fontSize: 14, color: ICE, margin: 0 });
  footer(s, 30, true);

  // 31 — protocol
  s = content("How we keep it honest", "Every experiment is a traceable run", 31, 24);
  bullets(s, [
    "Hypothesis + assumptions first — stated before any code is written.",
    "Each run writes experiments/runs/EXP-NNN__slug__<UTC>/ with:",
    ["manifest.yaml (config + git sha + deps) · prompts.jsonl (every LLM call) · results.csv · figures/ · README.", true],
    "Figures in publication style (figstyle.py); rate-limited + cached so reruns are free.",
    "Seed everything; guard loops; fail soft per cell; a watchdog kills any hung call.",
  ], { fontSize: 14 });

  // 32 — project map
  s = content("How to read this repo", "What's in the project", 32, 25);
  const tree = [
    "agent-harness/",
    "├─ harness/        the teaching harness: the loop + ContextManager",
    "├─ experiments/    the research: bench/ + applied/ (FRAMES, LoCoMo)",
    "│   ├─ applied/     runner · policies · agent · embed · judge",
    "│   └─ runs/        one folder per run: manifest + prompts + results",
    "├─ docs/research-track/   curriculum · paper · literature · protocol",
    "├─ presentation/   this deck + Founsi brand + figures",
    "└─ tests/          offline tests (no API key needed)",
  ];
  s.addShape(RECT, { x: MX, y: 1.65, w: 8.8, h: 2.7, fill: { color: PANEL }, line: { color: LILAC, width: 1 } });
  s.addText(tree.map((t) => ({ text: t, options: { breakLine: true } })),
    { x: MX + 0.2, y: 1.8, w: 8.5, h: 2.4, fontFace: MONO, fontSize: 12.5, color: INK, margin: 0, lineSpacingMultiple: 1.18 });
  caption(s, "Start at harness/loop.py (the agent loop), then experiments/applied/policies.py (the seven arms).", 4.55);

  // 33 — implementation (the heart)
  s = content("Appendix · implementation", "The compaction loop, and the one hard constraint.", 33, 24);
  bullets(s, [
    "Read sources in sequence; when _toks(window) > budget, compact under the policy and continue.",
    "_safe_split: never cut a tool-call from its result — split on a safe boundary or skip.",
    "Each policy is a small class: compact(old, llm, store) -> (block, usage); .retrieves flag.",
    "Reasoning models: strip <think>…</think> before judging; raise the watchdog for long calls.",
    ["LoCoMo flow: compact a conversation once, answer many questions — read_and_compact + answer_from_window.", true],
  ], { fontSize: 13.5 });

  // 34 — EXP-001 hypothesis/method
  s = content("EXP-001 · compaction-bakeoff", "Hypothesis, method, threats", 34, 25);
  s.addText("Hypothesis", { x: MX, y: 1.45, w: 8.8, h: 0.3, fontFace: MAN, fontSize: 12.5, bold: true, color: PURPLE, margin: 0 });
  s.addText("Under a fixed budget, summary-based compaction preserves more needle-facts per token than truncation; a budget B* trades fact-loss against lost-in-the-middle.",
    { x: MX, y: 1.72, w: 8.8, h: 0.6, fontFace: MAN, fontSize: 12.5, color: INK, margin: 0 });
  bullets(s, [
    "Method: seeded needle-bearing transcript → compact under each policy → probe recall of planted facts.",
    "Metric: needle recall per token — objective, no LLM-judge needed at this layer.",
    "Threats: synthetic data + simulated agent; recall is a proxy; 8B under-reads; crude heuristics.",
  ], { y: 2.5, fontSize: 13 });

  // 35 — EXP-001 results
  s = content("EXP-001 · results", "Truncation is the floor; summaries win at a cost.", 35, 24);
  fig(s, "EXP-001_pareto_v1.png", { x: 0.7, y: 1.5, w: 5.3, h: 3.59 });
  bullets(s, [["Upper-left wins: more recall per token.", true], "Truncate is the floor.", "Summary policies preserve 2-3x more.", "semantic best at B*=1000 (8B)."], { x: 6.2, y: 1.8, w: 3.3, fontSize: 13 });

  // 36 — EXP-002
  s = content("EXP-002 · length-degradation", "Does compaction beat raw context? Yes.", 36, 25);
  fig(s, "EXP-002_recall_vs_length_v1.png", { x: 0.7, y: 1.5, w: 5.3, h: 3.64 });
  bullets(s, [
    "Baseline collapses with length: 0.62 → 0.12 by 32 sources.",
    "Summary compaction holds flat near 0.58.",
    ["Crossover ~16 sources: compaction goes from tied to decisively better.", true],
    "Truncate is the floor (0.08).",
  ], { x: 6.2, y: 1.7, w: 3.3, fontSize: 12.5 });

  // 37 — EXP-003a/b
  s = content("EXP-003a/b · applied FRAMES", "The metric flip, and the bake-off", 37, 24);
  fig(s, "EXP-003a_pareto_v1.png", { x: 0.7, y: 1.5, w: 5.3, h: 3.59 });
  bullets(s, [
    "EXP-003a: substring scoring made the hybrid look worst (0.21); the judge flipped it to best (0.62).",
    "At low pressure all arms cluster ~0.6 — compaction barely fires.",
    ["EXP-003b: high pressure separates 7 arms; recency dominated by truncate; sub-agent a cost trap.", true],
  ], { x: 6.2, y: 1.7, w: 3.3, fontSize: 12 });

  // 38 — EXP-003c full matrix
  s = content("EXP-003c · the model axis", "FRAMES, 8B / 70B / reasoning (n=30)", 38, 24);
  const T3 = [["arm", "8B", "70B", "reason"], ["truncate", "0.37", "0.27", "0.40"], ["externalize", "0.40", "0.63", "0.67"],
    ["importance", "0.50", "0.60", "0.70"], ["semantic", "0.57", "0.53", "0.63"], ["reversible_hybrid", "0.47", "0.67", "0.70"]];
  const t3X = [MX, 3.2, 4.4, 5.6], t3W = [2.6, 1.2, 1.2, 1.3];
  T3.forEach((r, i) => {
    const y = 1.7 + i * 0.5, head = i === 0, hot = r[0] === "reversible_hybrid";
    if (hot) s.addShape(RECT, { x: MX - 0.05, y: y - 0.03, w: 6.4, h: 0.5, fill: { color: WASH } });
    r.forEach((c, j) => s.addText(c, { x: t3X[j], y, w: t3W[j], h: 0.46, fontFace: head ? SYNE : MAN, fontSize: head ? 11.5 : 13,
      bold: head || hot || j === 0, color: head ? PURPLE : (hot ? PDARK : INK), valign: "middle", margin: 0 }));
  });
  caption(s, "Reasoning tier: fast 8B summarizer for compaction (the reasoning model self-summarized too slowly); it only answers.", 4.8);

  // 39 — EXP-004 full
  s = content("EXP-004 · cross-domain", "FRAMES vs LoCoMo, and the LoCoMo model axis", 39, 24);
  fig(s, "EXP-004_transfer_v1.png", { x: 0.7, y: 1.5, w: 4.55, h: 3.12 });
  fig(s, "EXP-004_modelaxis_v1.png", { x: 5.4, y: 1.5, w: 4.0, h: 2.74 });
  caption(s, "Left: the ranking inverts across domains. Right: on LoCoMo capability doesn't rescue summarization. The hybrid is top-group in all four cells.", 4.75);

  // 40 — cost model / catalog
  s = content("Appendix · cost & models", "What a full study would cost, and what we used.", 40, 24);
  bullets(s, [
    "Ran on the free NVIDIA NIM API — $0; the response cache makes re-runs free.",
    "A full 824-question x 7-arm x 10-model study on paid OpenRouter (2026 models) ≈ $140 (4 arms) to ~$1,560 (all arms, 2 frontier).",
    "2026 catalog considered: Llama 4 / 3.3, GPT-5.x, Claude 4.x, Gemini 3.x, DeepSeek V4, Qwen3.5, Kimi K2.6, GLM 5.1, Nemotron 3.",
    ["Models used: Llama 3.1 8B, Llama 3.3 70B, Nemotron 30B-A3B (reasoning); judge = Llama 3.3 70B, fixed.", true],
  ], { fontSize: 13 });

  // 41 — references
  s = content("References", "The literature this stands on", 41, 26);
  bullets(s, [
    "Lost in the Middle, Liu et al., arXiv:2307.03172.",
    "RULER 2404.06654 · HELMET 2410.02694 · NoLiMa 2502.05167.",
    "MemGPT 2310.08560 · Mem0 2504.19413 · ACON 2510.00615.",
    "Judging LLM-as-a-Judge, Zheng et al., 2306.05685.",
    "FRAMES 2409.12941 · LoCoMo 2402.17753 · RAG (Lewis) 2005.11401.",
  ], { fontSize: 13, color: GREY });

  await p.writeFile({ fileName: path.join(__dirname, "founsi-context-engineering.pptx") });
  console.log("wrote presentation/founsi-context-engineering.pptx (41 slides)");
})();
