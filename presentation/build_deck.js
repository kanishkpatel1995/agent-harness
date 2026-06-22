// Build the Founsi-branded deck for AI Tinkerers.
//   node presentation/build_deck.js  ->  founsi-context-engineering.pptx
//
// v2 — depth-first rebuild.
// MAIN (11): title -> the corpse (cold open) -> why it dies (budget + chart) ->
//   reframe -> the list IS the mind -> five moves (compact spotlit) -> compact deeply
//   (code + before/after) -> LIVE DEMO -> the open question / bake-off -> the result
//   (top group in every cell) -> close.
// APPENDIX: landscape, 7 policies, flow diagrams, our technique, setup, every result,
//   full matrices, protocol, repo, references.
// Fixes vs v1: footer safe-zone (no more collisions); brand-coloured NATIVE charts on
//   main result slides; accurate result framing ("top group", not "wins every cell");
//   the heart slide now SHOWS code + before/after; a real demo slide; tour -> appendix.
const pptxgen = require("pptxgenjs");
const sharp = require("sharp");
const fs = require("fs");
const path = require("path");

const BRAND = path.join(__dirname, "brand");
const FIG = path.join(__dirname, "figures");
const QR = path.join(__dirname, "assets", "qr");
const BG = "FAFAFE", INK = "2E2C32", PURPLE = "9378FF", PDARK = "7B5EF0",
      GREY = "655E74", MID = "7E7A8A", WHITE = "FFFFFF", ICE = "CADCFC", WASH = "EFEBFF",
      PANEL = "F4F2F8", LILAC = "D4C9FF", FLOOR = "A09DAC", RED = "E5534B",
      GREEN = "2DA44E", AMBER = "D4880F", MINT = "1B9E77", DSURF = "1A1920";
const SYNE = "Syne", MAN = "Manrope", MONO = "Courier New";
const MX = 0.6;
// One colour per policy, used on every chart for consistency.
const POL = { baseline: RED, truncate: FLOOR, recency: PURPLE, importance: PDARK,
              semantic: INK, externalize: GREEN, reversible_hybrid: AMBER, subagent: MID };

async function png(file, w) {
  const out = await sharp(fs.readFileSync(file), { density: 300 }).resize({ width: w }).png().toBuffer();
  return "image/png;base64," + out.toString("base64");
}
const exists = (f) => fs.existsSync(f);

(async () => {
  const markPurple = await png(path.join(BRAND, "founsi-mark.svg"), 400);
  const lockupInv = await png(path.join(BRAND, "founsi-logo-horizontal-inverted.svg"), 1600);

  const p = new pptxgen();
  p.layout = "LAYOUT_16x9"; // 10 x 5.625 in
  p.author = "Kanishk Patel";
  p.title = "Context Engineering Inside the Harness";
  const RR = p.shapes.ROUNDED_RECTANGLE, RECT = p.shapes.RECTANGLE, LINE = p.shapes.LINE;

  // ---- chrome (footer pinned to the very bottom => safe zone above it) ----
  const FOOT = 5.42; // content must end by ~5.25
  const footer = (s, n, dark = false) => {
    s.addImage({ data: markPurple, x: MX, y: FOOT, w: 0.22, h: 0.22 * 110 / 146 });
    s.addText([{ text: "Founsi", options: { color: dark ? WHITE : INK } }, { text: ".", options: { color: PURPLE } }],
      { x: MX + 0.28, y: FOOT - 0.04, w: 1.4, h: 0.26, fontFace: SYNE, fontSize: 10, bold: true, margin: 0, valign: "middle" });
    s.addText(String(n), { x: 9.0, y: FOOT - 0.04, w: 0.4, h: 0.26, fontFace: MAN, fontSize: 9, color: MID, align: "right", valign: "middle", margin: 0 });
  };
  const overline = (s, t, color = PURPLE) => s.addText(t.toUpperCase(),
    { x: MX, y: 0.38, w: 8.8, h: 0.3, fontFace: SYNE, fontSize: 11, bold: true, color, charSpacing: 3, margin: 0 });
  const titleTx = (s, t, size = 26) => s.addText(t,
    { x: MX, y: 0.68, w: 8.8, h: 0.8, fontFace: SYNE, fontSize: size, bold: true, color: INK, margin: 0, valign: "top", lineSpacing: size * 1.04 });
  const content = (ov, t, n, size) => {
    const s = p.addSlide(); s.background = { color: BG };
    overline(s, ov); titleTx(s, t, size); footer(s, ++PG); return s;
  };
  const bullets = (s, items, o = {}) => {
    const opt = Object.assign({ x: MX, y: 1.7, w: 8.8, h: 3.2, fontFace: MAN, fontSize: 14, color: INK, valign: "top" }, o);
    s.addText(items.map((it) => {
      const [txt, sub] = Array.isArray(it) ? it : [it, false];
      return { text: txt, options: { bullet: { indent: 16 }, breakLine: true, paraSpaceAfter: 7, color: sub ? GREY : opt.color, fontSize: sub ? opt.fontSize - 1.5 : opt.fontSize } };
    }), opt);
  };
  const rows = (s, items, y0 = 1.7, gap = 0.66) => items.forEach((m, i) => {
    const y = y0 + i * gap, hot = m[2];
    s.addShape(RECT, { x: MX, y, w: 0.1, h: 0.5, fill: { color: hot ? PURPLE : LILAC } });
    s.addText([{ text: m[0] + "  ", options: { bold: true, color: hot ? PURPLE : INK, fontSize: 15 } },
               { text: m[1], options: { color: GREY, fontSize: 12.5 } }],
      { x: MX + 0.24, y, w: 8.7, h: 0.5, fontFace: MAN, valign: "middle", margin: 0 });
  });
  const caption = (s, t, y = 4.85) => s.addText(t, { x: MX, y: Math.min(y, 5.0), w: 8.8, h: 0.3, fontFace: MAN, fontSize: 11.5, italic: true, color: GREY, margin: 0 });
  const fig = (s, file, o = {}) => exists(path.join(FIG, file)) &&
    s.addImage(Object.assign({ path: path.join(FIG, file), x: 0.7, y: 1.5, w: 5.3, h: 3.5 }, o));
  const qrBlock = (s, file, label, x, y, size = 1.25) => {
    if (exists(path.join(QR, file))) s.addImage({ path: path.join(QR, file), x, y, w: size, h: size });
    s.addText(label, { x: x - 0.35, y: y + size + 0.06, w: size + 0.7, h: 0.3, fontFace: MAN, fontSize: 10.5, bold: true, color: WHITE, align: "center", margin: 0 });
  };
  // diagram primitives
  const dbox = (s, x, y, w, h, title, sub, o = {}) => {
    const txt = [{ text: title, options: { bold: true, fontSize: o.fs || 12, color: o.color || INK, breakLine: !!sub } }];
    if (sub) txt.push({ text: sub, options: { fontSize: (o.fs || 12) - 3, color: o.subc || GREY } });
    s.addText(txt, { x, y, w, h, shape: RR, fill: { color: o.fill || PANEL }, line: { color: o.line || LILAC, width: o.lw || 1.25 },
      rectRadius: 0.07, fontFace: MAN, align: "center", valign: "middle", margin: 4 });
  };
  const arr = (s, x, y, w, h, o = {}) => s.addShape(LINE,
    { x, y, w, h, line: { color: o.color || MID, width: o.width || 1.75, endArrowType: o.end === false ? "none" : "triangle", beginArrowType: o.bi ? "triangle" : "none", dashType: o.dash || "solid" } });
  // terminal mock (dark)
  const term = (s, x, y, w, h, lines) => {
    s.addShape(RECT, { x, y, w, h, fill: { color: DSURF }, line: { color: "2A2833", width: 1 } });
    [["E5534B", 0], ["D4880F", 1], ["2DA44E", 2]].forEach(([c, i]) =>
      s.addShape(p.shapes.OVAL, { x: x + 0.18 + i * 0.18, y: y + 0.16, w: 0.1, h: 0.1, fill: { color: c }, line: { type: "none" } }));
    s.addText(lines, { x: x + 0.22, y: y + 0.42, w: w - 0.44, h: h - 0.6, fontFace: MONO, fontSize: 11.5, valign: "top", lineSpacing: 16, margin: 0 });
  };
  // code box (light)
  const code = (s, x, y, w, h, lines, fs = 11.5) => {
    s.addShape(RECT, { x, y, w, h, fill: { color: WHITE }, line: { color: LILAC, width: 1 } });
    s.addText(lines.map((ln) => ({ text: ln === "" ? " " : ln, options: { breakLine: true,
      color: ln.trim().startsWith("#") ? MID : INK } })),
      { x: x + 0.18, y: y + 0.14, w: w - 0.36, h: h - 0.28, fontFace: MONO, fontSize: fs, valign: "top", lineSpacing: fs * 1.32, margin: 0 });
  };
  // message-stack (before/after)
  const stack = (s, x, y0, head, items, w = 1.95) => {
    s.addText(head, { x, y: y0, w, h: 0.3, fontFace: MAN, fontSize: 12, bold: true, color: GREY, align: "center", margin: 0 });
    let y = y0 + 0.36;
    items.forEach(([t, c]) => {
      s.addShape(RECT, { x, y, w, h: 0.4, fill: { color: c }, line: { color: LILAC, width: 1 } });
      s.addText(t, { x: x + 0.08, y, w: w - 0.16, h: 0.4, fontFace: MONO, fontSize: 9.5, color: INK, valign: "middle", margin: 0 });
      y += 0.47;
    });
  };
  // native charts
  const lineChart = (s, x, y, w, h, series, opt = {}) => {
    s.addChart(p.charts.LINE, series.map((q) => ({ name: q.name, labels: q.labels, values: q.values })), {
      x, y, w, h, chartColors: series.map((q) => q.color), lineSize: 2.6, lineSmooth: false,
      showLegend: true, legendPos: "b", legendFontFace: MAN, legendFontSize: 10, legendColor: GREY,
      showTitle: false, chartArea: { fill: { color: WHITE } }, plotArea: { fill: { color: WHITE } },
      valAxisMinVal: 0, valAxisMaxVal: 1, valAxisMajorUnit: 0.2,
      catAxisLabelColor: MID, valAxisLabelColor: MID, catAxisLabelFontFace: MAN, valAxisLabelFontFace: MAN,
      catAxisLabelFontSize: 10, valAxisLabelFontSize: 10, catAxisTitleColor: MID, showCatAxisTitle: !!opt.catTitle,
      catAxisTitle: opt.catTitle || "", catAxisTitleFontSize: 10, catAxisTitleFontFace: MAN,
      valGridLine: { color: "ECE8F6", size: 0.5 }, catGridLine: { style: "none" }, lineDataSymbolSize: 6,
    });
  };
  const colChart = (s, x, y, w, h, labels, values, colors) => {
    s.addChart(p.charts.BAR, [{ name: "accuracy", labels, values }], {
      x, y, w, h, barDir: "col", chartColors: colors, chartColorsOpacity: 100,
      showLegend: false, showTitle: false, chartArea: { fill: { color: WHITE } }, plotArea: { fill: { color: WHITE } },
      valAxisMinVal: 0, valAxisMaxVal: 0.65, valAxisMajorUnit: 0.2,
      showValue: true, dataLabelColor: INK, dataLabelFontFace: MAN, dataLabelFontSize: 10, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00",
      catAxisLabelColor: INK, valAxisLabelColor: MID, catAxisLabelFontFace: MAN, valAxisLabelFontFace: MAN,
      catAxisLabelFontSize: 10, valAxisLabelFontSize: 10, barGapWidthPct: 40,
      valGridLine: { color: "ECE8F6", size: 0.5 }, catGridLine: { style: "none" },
    });
  };
  const matrix = (s, M, y0, mX, mW, hotName, step = 0.5) => M.forEach((r, i) => {
    const y = y0 + i * step, head = i === 0, hot = r[0] === hotName;
    if (hot) s.addShape(RECT, { x: MX - 0.05, y: y - 0.02, w: (mX[mX.length - 1] + mW[mW.length - 1]) - MX + 0.1, h: step - 0.04, fill: { color: WASH } });
    r.forEach((c, j) => s.addText(c, { x: mX[j], y, w: mW[j], h: step - 0.05, fontFace: head ? SYNE : MAN, fontSize: head ? 11.5 : 13,
      bold: head || hot || j === 0, color: head ? PURPLE : (hot ? PDARK : INK), valign: "middle", margin: 0 }));
  });

  let PG = 1; // title is page 1 (no footer); every later slide does ++PG
  const winCol = (s, x, y, blocks, w = 2.6, bh = 0.5) => blocks.forEach((b, i) => {
    s.addShape(RECT, { x, y: y + i * (bh + 0.08), w, h: bh, fill: { color: b.fill || PANEL }, line: { color: b.line || LILAC, width: 1 } });
    s.addText(b.t, { x: x + 0.12, y: y + i * (bh + 0.08), w: w - 0.24, h: bh, fontFace: MAN, fontSize: 11.5, bold: !!b.bold, color: b.color || INK, valign: "middle", margin: 0 });
  });
  const meter = (s, y, label, pct, val) => {
    s.addText(label, { x: 1.7, y, w: 1.8, h: 0.4, fontFace: MAN, fontSize: 13, bold: true, color: INK, valign: "middle", margin: 0 });
    s.addShape(RECT, { x: 3.6, y: y + 0.09, w: 3.6, h: 0.24, fill: { color: PANEL }, line: { color: LILAC, width: 1 } });
    s.addShape(RECT, { x: 3.6, y: y + 0.09, w: 3.6 * pct, h: 0.24, fill: { color: PURPLE }, line: { type: "none" } });
    s.addShape(LINE, { x: 7.2, y: y + 0.02, w: 0, h: 0.4, line: { color: RED, width: 2 } });
    s.addText(val, { x: 7.35, y, w: 2.0, h: 0.4, fontFace: MONO, fontSize: 11, color: GREY, valign: "middle", margin: 0 });
  };
  const moveSlide = (idx, name, file, oneliner, why) => {
    const s = p.addSlide(); s.background = { color: BG };
    overline(s, `MOVE ${idx} / 5  ·  ${file}`);
    s.addText(name, { x: MX, y: 0.66, w: 8.8, h: 0.7, fontFace: SYNE, fontSize: 29, bold: true, color: INK, margin: 0 });
    s.addText(oneliner, { x: MX, y: 1.4, w: 8.8, h: 0.4, fontFace: MAN, fontSize: 15, color: GREY, margin: 0 });
    s.addText(why, { x: MX, y: 4.6, w: 8.8, h: 0.5, fontFace: MAN, fontSize: 14, bold: true, color: PDARK, margin: 0 });
    footer(s, ++PG); return s;
  };

  // ============================ MAIN DECK ============================
  // 1 — Title
  let s = p.addSlide(); s.background = { color: INK };
  s.addImage({ data: lockupInv, x: MX, y: 0.55, w: 2.4, h: 2.4 * 110 / 692 });
  s.addText("AI TINKERERS · CALGARY · JUNE 23, 2026", { x: MX, y: 1.6, w: 9, h: 0.3, fontFace: SYNE, fontSize: 11, bold: true, color: PURPLE, charSpacing: 3, margin: 0 });
  s.addText("Context Engineering", { x: MX, y: 2.0, w: 9, h: 0.85, fontFace: SYNE, fontSize: 42, bold: true, color: WHITE, margin: 0 });
  s.addText("Inside the Harness", { x: MX, y: 2.85, w: 9, h: 0.85, fontFace: SYNE, fontSize: 42, bold: true, color: PURPLE, margin: 0 });
  s.addText("Which way of forgetting keeps a long-running agent alive? I built the bake-off to find out.",
    { x: MX, y: 3.85, w: 8.6, h: 0.4, fontFace: MAN, fontSize: 15, color: ICE, margin: 0 });
  s.addText([{ text: "Kanishk Patel", options: { bold: true, color: WHITE } }, { text: "   ·   Founsi AI   ·   Learn Agentic AI", options: { color: MID } }],
    { x: MX, y: 4.75, w: 9, h: 0.4, fontFace: MAN, fontSize: 12, margin: 0 });

  // 2 — Cold open: the corpse
  s = p.addSlide(); s.background = { color: INK };
  s.addText("THE PROBLEM", { x: MX, y: 0.5, w: 8.8, h: 0.3, fontFace: SYNE, fontSize: 11, bold: true, color: PURPLE, charSpacing: 3, margin: 0 });
  s.addText("Brilliant at 5 steps. Dead at 50.", { x: MX, y: 0.84, w: 8.8, h: 0.7, fontFace: SYNE, fontSize: 28, bold: true, color: WHITE, margin: 0 });
  term(s, MX, 1.75, 5.7, 3.2, [
    { text: "step 05  search(\"France GDP 2023\")   ✓ found\n", options: { color: "9FE8B0" } },
    { text: "step 06  reason → draft answer       ✓\n\n", options: { color: "C9C4D6" } },
    { text: "step 48  search(\"France GDP 2023\")   ✓\n", options: { color: "C9C4D6" } },
    { text: "step 49  search(\"France GDP 2023\")   ↺ already knew\n", options: { color: "D4880F" } },
    { text: "step 50  search(\"France capital\")    ↺ looping\n", options: { color: "D4880F" } },
    { text: "step 51  ...\n", options: { color: "C9C4D6" } },
    { text: "         ✗ context_length_exceeded (8192 tok)", options: { color: "F07A72" } },
  ]);
  s.addText([
    { text: "Same model. Same code.\n", options: { color: WHITE, bold: true, fontSize: 18, breakLine: true } },
    { text: "Nothing changed in the model — ", options: { color: ICE, fontSize: 15 } },
    { text: "something filled up.", options: { color: PURPLE, fontSize: 15, bold: true } },
  ], { x: 6.55, y: 2.4, w: 2.9, h: 1.6, fontFace: MAN, valign: "top", lineSpacing: 22, margin: 0 });
  footer(s, ++PG, true);

  // 3 — Why it dies: the window is a budget (native chart)
  s = content("Why it dies", "The window is a budget, not a backpack.", 3, 25);
  lineChart(s, 0.55, 1.55, 5.3, 3.3, [
    { name: "no-compaction", color: RED, labels: ["8", "16", "32", "48"], values: [0.62, 0.33, 0.12, 0.16] },
    { name: "truncate", color: FLOOR, labels: ["8", "16", "32", "48"], values: [0.08, 0.08, 0.08, 0.08] },
    { name: "recency (summary)", color: PURPLE, labels: ["8", "16", "32", "48"], values: [0.66, 0.58, 0.58, 0.58] },
    { name: "semantic", color: INK, labels: ["8", "16", "32", "48"], values: [0.59, 0.54, 0.62, 0.58] },
  ], { catTitle: "run length (sources read)" });
  bullets(s, [
    "Stateless model: every turn you re-send the whole history. Cost and latency climb with it.",
    "Attention spreads thin — models read the middle of a long context worst (“lost in the middle”).",
    ["Raw context collapses 0.62 → 0.12 as the run grows. A short clean summary holds near 0.58.", true],
  ], { x: 6.1, y: 1.6, w: 3.35, fontSize: 13 });
  caption(s, "EXP-002 · needle recall vs. run length, Llama-3.1-8B. Bigger window raises the ceiling; it doesn't bend the curve.", 4.95);

  // 4 — The reframe + one sentence
  s = p.addSlide(); s.background = { color: BG };
  overline(s, "The reframe");
  s.addText([{ text: "Engineer ", options: { color: INK } }, { text: "what the model sees", options: { color: PURPLE, italic: true } }, { text: ",", options: { color: INK } }],
    { x: 0.7, y: 1.55, w: 8.6, h: 0.8, fontFace: SYNE, fontSize: 32, bold: true, align: "center", margin: 0 });
  s.addText("every single turn.", { x: 0.7, y: 2.32, w: 8.6, h: 0.8, fontFace: SYNE, fontSize: 32, bold: true, color: INK, align: "center", margin: 0 });
  s.addShape(RECT, { x: 1.7, y: 3.5, w: 6.6, h: 0.02, fill: { color: LILAC }, line: { type: "none" } });
  s.addText([{ text: "The model is a commodity you rent. ", options: { color: GREY } },
             { text: "The harness is the part you build.", options: { color: PDARK, bold: true } }],
    { x: 1.0, y: 3.7, w: 8.0, h: 0.6, fontFace: MAN, fontSize: 16, align: "center", margin: 0 });
  footer(s, ++PG);

  // 5 — The list IS the mind
  s = content("The mental model", "The list IS the mind.", 5, 26);
  ["Perceive", "Think", "Act"].forEach((t, i) => dbox(s, 0.7 + i * 3.15, 1.7, 2.1, 0.8,
    t, ["read tool results", "the LLM call", "call a tool"][i], { fs: 13 }));
  arr(s, 2.8, 2.1, 1.05, 0); arr(s, 5.95, 2.1, 1.05, 0);
  arr(s, 7.85, 2.5, 0, 0.5); arr(s, 7.85, 3.0, -6.05, 0, { color: PURPLE }); arr(s, 1.8, 3.0, 0, -0.5, { color: PURPLE });
  s.addText("every turn, the harness rebuilds one list of messages and hands it over", { x: 1.8, y: 3.05, w: 6.0, h: 0.3, fontFace: MAN, fontSize: 11, italic: true, color: PURPLE, align: "center", margin: 0 });
  bullets(s, [
    "The model remembers nothing. That freshly-built list is the agent's entire mind for the turn.",
    ["If the agent forgot its goal, the goal wasn't in the list. No magic — just: what do we put in the list?", true],
  ], { y: 3.6, fontSize: 13.5 });

  // 6 — Five moves, one matters
  s = content("The levers", "Five moves. One matters tonight.", 6, 26);
  rows(s, [
    ["Pin", "keep the goal + system prompt — never dropped."],
    ["Truncate", "cap giant tool outputs before they land."],
    ["Compact", "summarize the stale middle, drop the raw turns — where agents live or die.", true],
    ["Externalize", "write findings to disk; the window stays small."],
    ["Cap", "hard limits on steps, tokens, dollars."],
  ], 1.7, 0.64);
  caption(s, "I could give a talk on each. Tonight I go deep on compaction — it's the one doing the real work.", 4.95);

  // 6a–6e — the five moves, one visual each (5-second reads)
  // PIN
  s = moveSlide(1, "Pin", "context.py", "Keep the goal + system prompt fixed at the top — never dropped.",
    "Pinned: survives every compaction. The agent never forgets why it's here.");
  winCol(s, 2.0, 2.05, [{ t: "goal + system", fill: WASH, line: PURPLE, color: PDARK, bold: true },
    { t: "tool result (old)" }, { t: "tool result" }, { t: "recent turn" }], 2.7);
  s.addText("PINNED", { x: 2.0, y: 2.05, w: 2.46, h: 0.5, fontFace: SYNE, fontSize: 9, bold: true, color: PURPLE, charSpacing: 2, align: "right", valign: "middle", margin: 6 });
  arr(s, 4.75, 2.3, 0.6, 0, { color: PURPLE });
  s.addText([{ text: "everything else can be dropped.\n", options: { color: GREY, breakLine: true } },
             { text: "this block cannot.", options: { color: PDARK, bold: true } }],
    { x: 5.5, y: 2.15, w: 3.6, h: 0.8, fontFace: MAN, fontSize: 14, valign: "top", lineSpacing: 20, margin: 0 });

  // TRUNCATE
  s = moveSlide(2, "Truncate", "context.py", "Cap a giant tool output before it lands in the window.",
    "Keep the head; the full text goes to disk. One 200 KB page can't drown the window.");
  dbox(s, 1.5, 2.3, 3.0, 0.95, "tool output", "200 KB", { fs: 13, fill: PANEL });
  arr(s, 4.6, 2.78, 0.55, 0, { color: PURPLE });
  dbox(s, 5.25, 2.45, 2.0, 0.6, "first 2 KB", "kept", { fs: 12, fill: WASH, line: PURPLE, color: PDARK });
  arr(s, 6.25, 3.05, 0, 0.45, { color: GREEN, dash: "dash" });
  dbox(s, 5.25, 3.55, 2.0, 0.55, "rest → notes.md", null, { fs: 11, fill: PANEL, line: INK });

  // COMPACT
  s = moveSlide(3, "Compact", "context.py", "Summarize the stale middle into one note; drop the raw turns.",
    "The middle is the low-attention zone anyway — replace it with a tight summary.");
  stack(s, 2.2, 2.0, "before", [["sys + goal", LILAC], ["turn A", WHITE], ["turn B", WHITE], ["turn C", WHITE]], 2.0);
  arr(s, 4.35, 2.6, 0.5, 0, { color: PURPLE });
  stack(s, 5.35, 2.0, "after", [["sys + goal", LILAC], ["summary A–C", WASH], ["recent", WHITE]], 2.0);

  // EXTERNALIZE
  s = moveSlide(4, "Externalize", "memory.py", "Write findings to disk; keep only a pointer in the window.",
    "The window stays small; memory is unbounded — and compaction becomes safe.");
  winCol(s, 1.6, 2.05, [{ t: "goal + system", fill: WASH, line: PURPLE, color: PDARK },
    { t: "[saved #3] ↩", color: PDARK }, { t: "[saved #4] ↩", color: PDARK }, { t: "recent turn" }], 2.5);
  arr(s, 4.2, 2.9, 1.6, 0, { color: GREEN, dash: "dash" });
  dbox(s, 5.9, 2.45, 2.7, 1.0, "notes.md  (disk)", "full findings, unbounded", { fs: 12, fill: PANEL, line: INK });

  // CAP
  s = moveSlide(5, "Cap", "budget.py", "Hard limits on steps, tokens, and dollars — the kill switch.",
    "Fail soft: when a cap trips, stop and return the best answer so far. Never crash.");
  meter(s, 2.2, "steps", 0.6, "18 / 30");
  meter(s, 2.95, "tokens", 0.45, "9.9k / 50k");
  meter(s, 3.7, "dollars", 0.12, "$0.12 / $1.00");
  s.addText("red line = the cap", { x: 6.6, y: 4.0, w: 2.4, h: 0.3, fontFace: MAN, fontSize: 11, italic: true, color: RED, margin: 0 });

  // 7 — Compact, deeply (CODE + before/after)
  s = content("The heart", "Compact: summarize the middle.", 7, 26);
  code(s, MX, 1.55, 4.6, 2.25, [
    "def maybe_compact(msgs, budget):",
    "    if tokens(msgs) <= budget:",
    "        return msgs        # under budget",
    "    head, mid, tail = split(msgs)",
    "    mid = safe_split(mid)  # keep pairs",
    "    summary = llm.summarize(mid)",
    "    return head + [summary] + tail",
  ], 11.5);
  stack(s, 5.45, 1.55, "before", [["system + goal", LILAC], ["tool: 2KB page", WHITE], ["tool: 2KB page", WHITE], ["tool: 2KB page", WHITE]], 1.85);
  arr(s, 7.35, 2.35, 0.2, 0, { color: PURPLE });
  stack(s, 7.6, 1.55, "after", [["system + goal", LILAC], ["summary", WASH], ["recent turn", WHITE]], 1.85);
  s.addText([{ text: "The gotcha: ", options: { bold: true, color: PDARK } },
             { text: "never split a tool-call from its result — real APIs reject that transcript. ", options: { color: INK } },
             { text: "_safe_split handles it.", options: { color: GREY } }],
    { x: MX, y: 4.3, w: 8.8, h: 0.4, fontFace: MAN, fontSize: 12.5, margin: 0, valign: "top" });
  s.addText([{ text: "But compaction always forgets something — on purpose. ", options: { bold: true, color: INK } },
             { text: "So which way of forgetting loses the least?", options: { color: PDARK } }],
    { x: MX, y: 4.92, w: 8.8, h: 0.35, fontFace: MAN, fontSize: 13, margin: 0 });

  // 8 — LIVE DEMO
  s = p.addSlide(); s.background = { color: INK };
  s.addText("LIVE DEMO", { x: MX, y: 0.5, w: 8.8, h: 0.3, fontFace: SYNE, fontSize: 11, bold: true, color: PURPLE, charSpacing: 3, margin: 0 });
  s.addText("Watch it compact — and keep going.", { x: MX, y: 0.84, w: 8.8, h: 0.6, fontFace: SYNE, fontSize: 26, bold: true, color: WHITE, margin: 0 });
  term(s, MX, 1.6, 8.8, 2.7, [
    { text: "$ python run.py \"context engineering for long-running agents\"\n", options: { color: ICE } },
    { text: "[FakeLLM: offline, deterministic — no API key, no network]\n\n", options: { color: MID } },
    { text: "STEP 6   tokens=3,662   ", options: { color: WHITE } },
    { text: "context [", options: { color: "8A8694" } }, { text: "███████████████████", options: { color: PURPLE } }, { text: "·············] 53%\n", options: { color: "8A8694" } },
    { text: "STEP 7   tokens=5,516   ", options: { color: WHITE } },
    { text: "context [", options: { color: "8A8694" } }, { text: "██████████████████████████████", options: { color: PURPLE } }, { text: "···] 77%\n", options: { color: "8A8694" } },
    { text: "  ⚙ COMPACTED → window 1,336 tok. old turns summarized.\n", options: { color: AMBER } },
    { text: "STEP 8   context back down — agent keeps working → finish()\n", options: { color: WHITE } },
    { text: "═══ DONE   10 steps · facts intact in run/notes.md ═══", options: { color: "6FCf97" } },
  ]);
  s.addText("the bar crosses the threshold, snaps back, and the run survives — 5 steps vs 50.", { x: MX, y: 4.5, w: 8.8, h: 0.3, fontFace: MONO, fontSize: 11.5, color: ICE, margin: 0 });
  s.addText([{ text: "Run it yourself:  ", options: { color: PURPLE, bold: true } },
             { text: "git clone github.com/kanishkpatel1995/agent-harness && python run.py", options: { color: WHITE } },
             { text: "   — no API key. Swap models with --model.", options: { color: MID } }],
    { x: MX, y: 4.88, w: 8.8, h: 0.3, fontFace: MONO, fontSize: 10.5, margin: 0 });
  footer(s, ++PG, true);

  // 9 — The open question -> the bake-off
  s = content("Zero to one · which compaction?", "Which way of forgetting loses the least?", 9, 24);
  s.addText([{ text: "Compaction stays bounded by forgetting — on purpose. ", options: { color: INK } },
             { text: "Each policy below forgets differently (drop · summarize · externalize · or both). I measured which keeps the most answer-relevant facts per token.", options: { color: GREY } }],
    { x: MX, y: 1.42, w: 8.8, h: 0.6, fontFace: MAN, fontSize: 12.5, valign: "top", margin: 0 });
  const tdata = [
    ["policy", "how it forgets", "cost"],
    ["truncate", "drop the oldest raw turns", "$"],
    ["recency", "summarize stale middle (the shipped default)", "$$"],
    ["importance", "keep highest-signal turns verbatim", "$$$"],
    ["semantic", "cluster by topic, summarize each", "$$$$"],
    ["externalize", "write raw to a store, retrieve at answer", "$"],
    ["reversible_hybrid", "summary in window + raw retrievable (ours)", "$$"],
  ];
  const cX = [MX, 2.7, 8.4], cW = [2.1, 5.6, 1.0];
  tdata.forEach((r, i) => {
    const y = 2.1 + i * 0.38, head = i === 0, hot = r[0] === "reversible_hybrid";
    if (hot) s.addShape(RECT, { x: MX - 0.05, y: y - 0.02, w: 8.95, h: 0.42, fill: { color: WASH } });
    r.forEach((c, j) => s.addText(c, { x: cX[j], y, w: cW[j], h: 0.38, fontFace: head ? SYNE : MAN, fontSize: head ? 11 : 12.5,
      bold: head || hot || j === 0, color: head ? PURPLE : (hot ? PDARK : (j === 2 ? GREY : INK)), valign: "middle", margin: 0 }));
  });
  caption(s, "Plant checkable facts in the sources; count how many survive each policy, per token spent. Judged by a fixed 70B. (+subagent in appendix.)", 4.9);

  // The experiment + models
  s = content("How we test it", "The bake-off: what we actually ran.", 0, 25);
  [["read sources", "the agent reads"], ["compact", "under each policy"], ["answer", "the question"], ["judge", "fixed 70B"]]
    .forEach((b, i) => dbox(s, 0.7 + i * 2.15, 1.65, 1.9, 0.8, b[0], b[1],
      { fs: 12, fill: i === 1 ? WASH : PANEL, line: i === 1 ? PURPLE : LILAC, color: i === 1 ? PDARK : INK }));
  [2.6, 4.75, 6.9].forEach((x) => arr(s, x, 2.05, 0.25, 0));
  s.addText("A tight 1.5k-token budget forces 10–20 compactions per question — so the policy actually matters. Oracle sources isolate compaction from search.",
    { x: 0.7, y: 2.6, w: 8.7, h: 0.5, fontFace: MAN, fontSize: 12, italic: true, color: GREY, margin: 0 });
  rows(s, [
    ["Llama 3.1 8B", "the dev model — runs the bulk of the cells."],
    ["Llama 3.3 70B", "does the 8B ranking hold as the model gets stronger?"],
    ["Nemotron 30B-A3B", "a reasoning model — does answer-time reasoning change the ranking?"],
    ["70B judge (fixed)", "the same grader across every arm and model — the metric held constant.", true],
  ], 3.25, 0.48);

  // Datasets + metric (with examples)
  s = content("The datasets & the metric", "Two task types, one judge.", 0, 25);
  dbox(s, 0.7, 1.55, 4.0, 0.5, "FRAMES — multi-hop factual QA", null, { fs: 12.5, fill: WASH, line: PURPLE, color: PDARK });
  s.addText([{ text: "Q  ", options: { bold: true, color: PDARK } },
             { text: "“Who was U.S. president when the maker of the iPhone was founded?”\n", options: { color: INK } },
             { text: "A  ", options: { bold: true, color: GREEN } },
             { text: "Gerald Ford — Apple was founded in 1976.", options: { color: GREY } }],
    { x: 0.7, y: 2.15, w: 4.0, h: 1.15, fontFace: MAN, fontSize: 11.5, valign: "top", lineSpacing: 16, margin: 0 });
  s.addText("824 questions · reason across several gold articles.", { x: 0.7, y: 3.35, w: 4.0, h: 0.4, fontFace: MAN, fontSize: 10.5, italic: true, color: MID, margin: 0 });
  dbox(s, 5.0, 1.55, 4.0, 0.5, "LoCoMo — conversational memory", null, { fs: 12.5, fill: PANEL, line: INK });
  s.addText([{ text: "Q  ", options: { bold: true, color: PDARK } },
             { text: "“What pet did Maria say she adopted last spring?”\n", options: { color: INK } },
             { text: "A  ", options: { bold: true, color: GREEN } },
             { text: "a rescue greyhound named Pip — said back in session 4.", options: { color: GREY } }],
    { x: 5.0, y: 2.15, w: 4.0, h: 1.15, fontFace: MAN, fontSize: 11.5, valign: "top", lineSpacing: 16, margin: 0 });
  s.addText("10 convos · ~19 sessions · facts scattered across the history.", { x: 5.0, y: 3.35, w: 4.0, h: 0.4, fontFace: MAN, fontSize: 10.5, italic: true, color: MID, margin: 0 });
  s.addText([{ text: "The metric:  ", options: { bold: true, color: PDARK } },
             { text: "an LLM judge (fixed 70B) credits a correct-but-paraphrased answer — a naive substring match inverted the ranking. FRAMES rewards a summarized reasoning chain; LoCoMo rewards exact scattered facts.", options: { color: INK } }],
    { x: 0.7, y: 3.95, w: 8.7, h: 0.9, fontFace: MAN, fontSize: 12.5, valign: "top", lineSpacing: 17, margin: 0 });
  caption(s, "Q/A examples are illustrative of each task type.", 5.0);

  // How reversible-hybrid differs
  s = content("Our technique", "How reversible-hybrid differs from the five.", 0, 24);
  const cm = [["policy", "compressed gist\nin-window", "lossless raw\nretrievable"],
    ["truncate", "—", "—"], ["recency · importance · semantic", "✓", "—"],
    ["externalize", "—", "✓"], ["reversible_hybrid", "✓", "✓"]];
  const cmX = [MX, 5.0, 7.2], cmW = [4.2, 2.0, 2.2];
  cm.forEach((r, i) => {
    const y = 1.75 + i * 0.62, head = i === 0, hot = r[0] === "reversible_hybrid";
    if (hot) s.addShape(RECT, { x: MX - 0.05, y: y - 0.04, w: 8.85, h: 0.6, fill: { color: WASH } });
    r.forEach((c, j) => {
      const isMark = j > 0 && !head;
      s.addText(c, { x: cmX[j], y, w: cmW[j], h: head ? 0.6 : 0.54, fontFace: head ? SYNE : (isMark ? MAN : MAN),
        fontSize: head ? 11 : (isMark ? 18 : 13), bold: head || hot || j === 0 || (isMark && c === "✓"),
        color: head ? PURPLE : (isMark ? (c === "✓" ? GREEN : "B9B4C6") : (hot ? PDARK : INK)),
        align: isMark ? "center" : "left", valign: "middle", margin: 0, lineSpacing: head ? 12 : 14 });
    });
  });
  s.addText([{ text: "Every other policy keeps ONE thing. ", options: { color: INK } },
             { text: "reversible-hybrid keeps both", options: { bold: true, color: PDARK } },
             { text: " — so it can pick up whichever mechanism the task needs (gist for reasoning, raw for exact facts).", options: { color: GREY } }],
    { x: MX, y: 4.75, w: 8.8, h: 0.6, fontFace: MAN, fontSize: 13, valign: "top", margin: 0 });

  // The bake-off graph
  s = content("Results · the bake-off", "Under pressure, the policies separate.", 0, 24);
  colChart(s, 0.55, 1.6, 5.4, 3.4,
    ["semantic", "importance", "subagent", "rev_hyb", "extern.", "truncate", "recency"],
    [0.57, 0.50, 0.50, 0.47, 0.40, 0.37, 0.37],
    [INK, PDARK, MID, AMBER, GREEN, FLOOR, PURPLE]);
  bullets(s, [
    "EXP-003b · FRAMES, 8B, high pressure, judged (n=30).",
    ["The shipped default (recency) is Pareto-dominated by plain truncation — 7x the cost, same accuracy.", true],
    ["Sub-agent isolation: 5x the cost of importance, no accuracy gain.", true],
    "Structure-preserving (semantic, importance) lead on accuracy; reversible-hybrid is Pareto-efficient.",
  ], { x: 6.15, y: 1.6, w: 3.35, fontSize: 11.5 });
  caption(s, "Accuracy by policy. Cost (tokens/q) is in the appendix table.", 5.05);

  // 10 — The result
  s = content("The result", "Never the best. Never the worst. Everywhere.", 10, 24);
  matrix(s, [
    ["arm", "FR-8B", "FR-70B", "LC-8B", "LC-70B"],
    ["reversible_hybrid", "0.47", "0.67", "0.54", "0.53"],
    ["externalize", "0.40", "0.63", "0.55", "0.55"],
    ["importance", "0.50", "0.60", "0.26", "0.23"],
    ["semantic", "0.57", "0.53", "0.27", "0.17"],
    ["truncate", "0.37", "0.27", "0.12", "0.09"],
  ], 1.5, [MX, 3.0, 4.4, 5.8, 7.2], [2.4, 1.4, 1.4, 1.4, 1.4], "reversible_hybrid", 0.45);
  s.addText([{ text: "reversible-hybrid is in the top group of every cell — the only arm that is. ", options: { bold: true, color: INK } },
             { text: "The single winner is task-dependent (semantic on factual, externalize on memory) — the ranking even inverts.", options: { color: GREY } }],
    { x: MX, y: 4.4, w: 8.8, h: 0.5, fontFace: MAN, fontSize: 12.5, margin: 0, valign: "top" });
  caption(s, "FR = FRAMES (factual), LC = LoCoMo (memory). n=30, judged by a fixed 70B; SE ≈ 0.09. Full matrices in appendix.", 5.0);

  // 11 — Close
  s = p.addSlide(); s.background = { color: INK };
  s.addText("THE ONE SENTENCE", { x: MX, y: 0.55, w: 9, h: 0.3, fontFace: SYNE, fontSize: 11, bold: true, color: PURPLE, charSpacing: 3, margin: 0 });
  s.addText([{ text: "The model is a commodity you rent.\n", options: { color: WHITE, breakLine: true } },
             { text: "The harness — what it forgets — is the part you build.", options: { color: PURPLE } }],
    { x: MX, y: 0.95, w: 8.8, h: 1.35, fontFace: SYNE, fontSize: 21, bold: true, lineSpacing: 28, margin: 0 });
  s.addText("Clone it tonight — it runs with no API key. Any model, one flag.", { x: MX, y: 2.5, w: 8.8, h: 0.35, fontFace: MAN, fontSize: 14, color: ICE, margin: 0 });
  qrBlock(s, "qr_repo.png", "Repo", 0.95, 3.15, 1.2);
  qrBlock(s, "qr_newsletter.png", "Learn Agentic AI", 3.15, 3.15, 1.2);
  qrBlock(s, "qr_x.png", "@above_almighty", 5.35, 3.15, 1.2);
  qrBlock(s, "qr_linkedin.png", "LinkedIn", 7.55, 3.15, 1.2);
  footer(s, ++PG, true);

  // ============================ APPENDIX ============================
  s = p.addSlide(); s.background = { color: INK };
  s.addText("APPENDIX", { x: MX, y: 1.9, w: 9, h: 0.5, fontFace: SYNE, fontSize: 13, bold: true, color: PURPLE, charSpacing: 4, margin: 0 });
  s.addText("The full trace", { x: MX, y: 2.35, w: 9, h: 0.9, fontFace: SYNE, fontSize: 34, bold: true, color: WHITE, margin: 0 });
  s.addText("Landscape · the 7 policies · our technique · setup · every result · protocol · references.",
    { x: MX, y: 3.4, w: 8.8, h: 0.5, fontFace: MAN, fontSize: 14, color: ICE, margin: 0 });
  footer(s, ++PG, true);

  // landscape
  s = content("The landscape", "Everyone compacts. Nobody measured which way.", 13, 23);
  rows(s, [
    ["Anthropic", "names the moves — compaction, structured note-taking, “context rot.”"],
    ["Cognition (Devin)", "“context engineering is the #1 job”; don't fragment it across agents."],
    ["LangChain · LlamaIndex", "memory abstractions — summary buffers, vector memory."],
    ["MemGPT · Letta", "treat the window like RAM; page facts to an external store."],
    ["RAG (Lewis, 2020)", "retrieve from a store instead of stuffing the prompt."],
  ]);

  // 7 policies table
  s = content("The techniques · at a glance", "Seven ways to forget.", 14, 25);
  const T = [["policy", "what it does", "keeps", "cost"],
    ["truncate", "drop the oldest raw turns", "recent only", "$"],
    ["recency", "summarize stale middle (default)", "summary + recent", "$$"],
    ["importance", "keep highest-signal turns", "key turns", "$$$"],
    ["semantic", "cluster by topic, summarize", "topic structure", "$$$$"],
    ["externalize", "write to store, retrieve", "all (indexed)", "$"],
    ["subagent", "isolate sub-tasks", "per-task context", "$$$$$"],
    ["reversible_hybrid", "summary + raw retrievable", "both", "$$"]];
  const TX = [MX, 2.5, 5.4, 8.3], TW = [1.9, 2.9, 2.9, 1.0];
  T.forEach((r, i) => {
    const y = 1.55 + i * 0.42, head = i === 0, hot = r[0] === "reversible_hybrid";
    if (hot) s.addShape(RECT, { x: MX - 0.05, y: y - 0.02, w: 8.95, h: 0.42, fill: { color: WASH } });
    r.forEach((c, j) => s.addText(c, { x: TX[j], y, w: TW[j], h: 0.38, fontFace: head ? SYNE : MAN, fontSize: head ? 11 : 12,
      bold: head || hot || j === 0, color: head ? PURPLE : (hot ? PDARK : (j === 3 ? GREY : INK)), valign: "middle", margin: 0 }));
  });

  // flow diagrams
  const flow = (s, y0, name, color, steps, note) => {
    s.addText(name, { x: MX, y: y0, w: 2.0, h: 0.7, fontFace: MAN, fontSize: 13, bold: true, color, valign: "middle", margin: 0 });
    let x = 2.4;
    steps.forEach((st, i) => {
      dbox(s, x, y0, st[1], 0.7, st[0], st[2], { fs: 11 });
      if (i < steps.length - 1) { arr(s, x + st[1], y0 + 0.35, 0.3, 0); x += st[1] + 0.3; }
    });
    if (note) s.addText(note, { x: 2.4, y: y0 + 0.72, w: 7.0, h: 0.26, fontFace: MAN, fontSize: 9.5, italic: true, color: GREY, margin: 0 });
  };
  s = content("The techniques · flow", "Drop it, or summarize the middle.", 15, 24);
  flow(s, 1.7, "truncate", FLOOR, [["window", 1.4, "old … recent"], ["drop old", 1.5, "no LLM"], ["recent only", 1.6, "facts lost"]], "Cheapest. Loses the most — old facts vanish without a trace.");
  flow(s, 3.4, "recency", PURPLE, [["window", 1.4, "old … recent"], ["summarize middle", 1.8, "1 LLM call"], ["summary + recent", 1.9, "stale flattened"]], "The shipped default (Claude Code / LangChain). Flattens the middle.");
  caption(s, "Both are summary-or-drop: once a fact leaves the window, only the (possibly lossy) summary remains.");

  s = content("The techniques · flow", "Keep the signal, or cluster the topics.", 16, 24);
  flow(s, 1.7, "importance", PDARK, [["window", 1.4, "turns"], ["rank by signal", 1.7, "score turns"], ["keep top verbatim", 1.9, "structure kept"]], "Keeps the highest-signal turns word-for-word; drops the chatter.");
  flow(s, 3.4, "semantic", INK, [["window", 1.4, "turns"], ["cluster by topic", 1.8, "embeddings"], ["summarize each", 1.8, "topic map"]], "Groups by topic, summarizes each cluster — preserves the shape of the work.");
  caption(s, "Structure-preserving: these led on FRAMES factual QA, where a summarized reasoning chain helps.");

  s = content("The techniques · flow", "Page it out, or spin up a fresh mind.", 17, 24);
  flow(s, 1.7, "externalize", GREEN, [["window", 1.4, "turns"], ["write → store", 1.9, "embeddings"], ["retrieve at answer", 1.9, "k-NN lookup"]], "Pages raw turns to a vector store; pulls the relevant ones back at answer time.");
  flow(s, 3.4, "subagent", MID, [["task", 1.4, "sub-goal"], ["fresh window", 1.7, "isolated run"], ["return result", 1.8, "5x the cost"]], "Isolates a sub-task in its own clean window — the multi-agent move. Expensive.");
  caption(s, "Retrieval-based: externalize keeps the literal fact, which wins on conversational memory.");

  // our technique
  s = content("Our technique", "reversible-hybrid: keep the summary AND the raw.", 18, 24);
  dbox(s, 0.7, 2.05, 1.7, 0.95, "stale window", "old turns", { fs: 12 });
  arr(s, 2.45, 2.5, 0.45, 0);
  dbox(s, 2.95, 1.45, 1.9, 0.85, "summary", "in the window", { fs: 12, fill: WASH, line: PURPLE, color: PDARK });
  dbox(s, 2.95, 2.65, 1.9, 0.85, "raw turns", "→ embedding store", { fs: 12, fill: PANEL, line: INK });
  arr(s, 2.9, 2.2, 0.05, -0.3); arr(s, 2.9, 2.85, 0.05, 0.3);
  dbox(s, 5.5, 1.45, 1.9, 0.85, "answer prompt", "summary + recent", { fs: 12, fill: WASH, line: PURPLE, color: PDARK });
  arr(s, 4.85, 1.85, 0.65, 0);
  arr(s, 4.85, 3.05, 2.55, -0.55, { color: INK, dash: "dash" });
  dbox(s, 7.7, 1.85, 1.7, 0.95, "retrieve top-k", "raw, on demand", { fs: 12, fill: PANEL, line: INK });
  arr(s, 7.4, 1.9, 0.3, 0.2);
  caption(s, "Summary keeps the gist cheaply in-window; raw stays losslessly retrievable. Prior systems do one or the other — we keep both.", 4.1);
  bullets(s, [["Prediction (and result): never the single best, but never in the loser group — robust across task type and model size.", true]],
    { y: 4.5, fontSize: 12.5 });

  // results (publication figures)
  s = content("Results · mechanism", "Facts survive, and compaction beats raw.", 23, 24);
  fig(s, "EXP-002_recall_vs_length_v1.png", { x: 0.7, y: 1.5, w: 5.3, h: 3.5 });
  bullets(s, [
    "EXP-001: planted facts survive a compaction — truncation drops them, summaries keep ~2-3x more.",
    "EXP-002: raw context collapses with length while compaction holds flat. Crossover ≈ 16 sources.",
    ["The mechanism behind every impact result.", true],
  ], { x: 6.2, y: 1.6, w: 3.3, fontSize: 12 });

  s = content("Results · the model axis", "Capability widens the smart-vs-blind gap.", 25, 24);
  fig(s, "EXP-003c_modelaxis_v1.png", { x: 0.7, y: 1.5, w: 5.3, h: 3.4 });
  bullets(s, [
    "Five arms across 8B → 70B → reasoning, judge fixed at 70B.",
    "Blind truncation never improves (0.37, 0.27, 0.40) — a better model can't recover dropped context.",
    ["Every structure/retrieval arm climbs; the gap to truncation grows ~0.2 → ~0.3.", true],
  ], { x: 6.2, y: 1.6, w: 3.3, fontSize: 12 });

  s = content("Results · cross-domain", "The ranking inverts — the hybrid spans both.", 26, 24);
  fig(s, "EXP-004_transfer_v1.png", { x: 0.7, y: 1.5, w: 5.3, h: 3.5 });
  bullets(s, [
    "Same arms on LoCoMo (memory) vs FRAMES (factual).",
    "Inversion: on memory, retrieval wins (externalize 0.55); pure summary collapses (semantic 0.27).",
    ["reversible-hybrid is top-group in BOTH (0.47 / 0.54) — it keeps both mechanisms.", true],
  ], { x: 6.2, y: 1.6, w: 3.3, fontSize: 12 });

  // full matrices
  s = content("Results · FRAMES model axis", "FRAMES · 8B / 70B / reasoning (n=30).", 27, 24);
  matrix(s, [["arm", "8B", "70B", "reason"], ["truncate", "0.37", "0.27", "0.40"], ["externalize", "0.40", "0.63", "0.67"],
    ["importance", "0.50", "0.60", "0.70"], ["semantic", "0.57", "0.53", "0.63"], ["reversible_hybrid", "0.47", "0.67", "0.70"]],
    1.58, [MX, 3.2, 4.4, 5.6], [2.6, 1.2, 1.2, 1.3], "reversible_hybrid", 0.46);
  caption(s, "Reasoning tier uses a fast 8B summarizer for compaction (the reasoning model self-summarized too slowly); it only answers.", 4.6);

  s = content("Results · cost & latency", "What each policy costs to run.", 28, 25);
  matrix(s, [["arm", "accuracy*", "tokens/q", "rel. latency"], ["truncate", "0.37", "1.2k", "fastest"],
    ["externalize", "0.40", "1.9k", "fast (+embed)"], ["reversible_hybrid", "0.47", "9.9k", "moderate"],
    ["importance", "0.50", "14.2k", "slow"], ["semantic", "0.57", "18.7k", "slowest"]],
    1.58, [MX, 3.0, 5.0, 7.0], [2.4, 2.0, 2.0, 2.2], "reversible_hybrid", 0.46);
  caption(s, "*FRAMES 8B high pressure (EXP-003b). Latency observed: 8B ~2s, 70B ~6-8s; reasoning models bill ~6x tokens.", 4.6);

  // through-line (accurate)
  s = content("The through-line", "Six claims, backed by evidence.", 29, 25);
  bullets(s, [
    "Policy matters only under pressure — at low pressure they tie.",
    "The metric must credit paraphrase — a careless substring metric inverts the ranking.",
    "The shipped default (recency-summary) is weak — Pareto-dominated by truncation under pressure.",
    "The smart-vs-blind gap widens with capability (FRAMES) and persists on memory (LoCoMo).",
    "The best single policy is task-dependent — summary on factual, retrieval on memory.",
    ["reversible-hybrid is the robust hedge: top group across task type AND model size. Keep the raw retrievable.", true],
  ], { fontSize: 13 });

  // aligns
  s = content("This matches what others see", "We're not alone.", 30, 24);
  rows(s, [
    ["Lost in the Middle (2307.03172)", "long contexts attend to the ends — our EXP-002 crossover is the same effect."],
    ["MemGPT / Mem0 / Letta", "page facts to an external store — our externalize & hybrid win where memory matters."],
    ["ACON (2510.00615)", "compress agent context; we add the which-way-is-best measurement."],
    ["RAG (Lewis, 2020)", "retrieval-as-compaction — our hybrid is RAG fused with summary memory."],
  ]);

  // future + protocol + repo
  s = content("Future work · how you can help", "Where this goes next.", 31, 25);
  bullets(s, [
    "Hold the summarizer constant across tiers; a reasoning tier on LoCoMo; larger N for tight bars.",
    "Trained importance/semantic rankers instead of heuristics; a tuned reversible store.",
    "LangChain summary-memory as a head-to-head baseline arm.",
    ["You can help: try a policy on your agent, add a dataset, or PR an arm. It's all reproducible.", true],
  ], { fontSize: 13.5 });

  s = content("How we keep it honest", "Every experiment is a traceable run.", 32, 24);
  bullets(s, [
    "Hypothesis + assumptions stated before any code is written.",
    ["Each run writes EXP-NNN__slug__<UTC>/ with manifest.yaml · prompts.jsonl · results.csv · figures/ · README.", true],
    "Rate-limited + cached so reruns are free; seed everything; fail soft per cell; a watchdog kills hung calls.",
  ], { fontSize: 13.5 });

  s = content("How to read this repo", "What's in the project.", 33, 25);
  s.addShape(RECT, { x: MX, y: 1.6, w: 8.8, h: 2.5, fill: { color: PANEL }, line: { color: LILAC, width: 1 } });
  s.addText([
    "agent-harness/", "├─ harness/        the teaching harness: the loop + ContextManager",
    "├─ experiments/    the research: bench/ + applied/ (FRAMES, LoCoMo)",
    "│   └─ runs/        one folder per run: manifest + prompts + results",
    "├─ docs/research-track/   curriculum · paper · literature · protocol",
    "├─ presentation/   this deck + Founsi brand + figures",
    "└─ tests/          offline tests (no API key needed)",
  ].map((t) => ({ text: t, options: { breakLine: true } })),
    { x: MX + 0.2, y: 1.74, w: 8.5, h: 2.2, fontFace: MONO, fontSize: 12, color: INK, margin: 0, lineSpacing: 17 });
  caption(s, "Start at harness/loop.py (the loop), then experiments/applied/policies.py (the seven arms).", 4.3);

  // references
  s = content("References", "The literature this stands on.", 34, 26);
  bullets(s, [
    "Lost in the Middle, Liu et al., arXiv:2307.03172.",
    "RULER 2404.06654 · HELMET 2410.02694 · NoLiMa 2502.05167.",
    "MemGPT 2310.08560 · Mem0 2504.19413 · ACON 2510.00615.",
    "Judging LLM-as-a-Judge, Zheng et al., 2306.05685.",
    "FRAMES 2409.12941 · LoCoMo 2402.17753 · RAG (Lewis) 2005.11401.",
  ], { fontSize: 13, color: GREY });

  await p.writeFile({ fileName: path.join(__dirname, "founsi-context-engineering.pptx") });
  console.log("wrote presentation/founsi-context-engineering.pptx");
})();
