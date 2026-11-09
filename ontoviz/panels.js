/* 3D type — every panel on the WebGPU page is a CanvasTexture.
 * No HTML text sits over the canvas: titles, decks, chips, buttons, stats,
 * navigation and the inspector are 3D planes with UV hotspots.
 *
 * Two layouts: wide (desktop) and narrow (portrait phones), because text
 * size on screen is a ratio of texture width to panel width.
 */
import { COL, BRAND, SECTIONS, stats } from './ontology.js';

const SERIF = '"Cormorant Garamond", Georgia, "Times New Roman", serif';
const SANS = '"DM Sans", system-ui, "Noto Sans KR", sans-serif';
const MONO = '"JetBrains Mono", ui-monospace, Menlo, monospace';

export async function loadFonts() {
  if (!document.fonts) return;
  const jobs = [
    `600 100px ${SERIF}`, `italic 400 100px ${SERIF}`, `500 40px ${SANS}`, `300 34px ${SANS}`,
    `500 28px ${MONO}`, `400 28px ${MONO}`
  ].map((f) => document.fonts.load(f).catch(() => {}));
  await Promise.race([Promise.all(jobs), new Promise((r) => setTimeout(r, 2500))]);
}

export const rr = (ctx, x, y, w, h, r) => {
  const k = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  if (ctx.roundRect) { ctx.roundRect(x, y, w, h, k); return; }
  ctx.moveTo(x + k, y); ctx.arcTo(x + w, y, x + w, y + h, k); ctx.arcTo(x + w, y + h, x, y + h, k);
  ctx.arcTo(x, y + h, x, y, k); ctx.arcTo(x, y, x + w, y, k); ctx.closePath();
};

const decode = (s) => String(s)
  .replace(/&nbsp;/g, ' ')
  .replace(/&#8217;|&rsquo;/g, '’').replace(/&#8216;|&lsquo;/g, '‘')
  .replace(/&#8220;|&ldquo;/g, '“').replace(/&#8221;|&rdquo;/g, '”')
  .replace(/&#8212;|&mdash;/g, '—').replace(/&#8211;|&ndash;/g, '–')
  .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"');

export function parseRich(str) {
  str = decode(str);
  const out = [];
  const re = /<em>([\s\S]*?)<\/em>|<br\s*\/?>|([^<]+)/gi;
  let m;
  while ((m = re.exec(str))) {
    if (m[1] != null) out.push({ text: m[1], em: true });
    else if (m[0].toLowerCase().startsWith('<br')) out.push({ br: true });
    else if (m[2]) out.push({ text: m[2], em: false });
  }
  return out;
}

export function wrapRich(ctx, runs, maxW, fonts) {
  const words = [];
  runs.forEach((run) => {
    if (run.br) { words.push({ br: true }); return; }
    const font = run.em ? fonts.em : fonts.base;
    run.text.split(/\s+/).filter(Boolean).forEach((w) => words.push({ w, em: !!run.em, font }));
  });
  const lines = [];
  let line = [];
  let width = 0;
  words.forEach((word) => {
    if (word.br) { if (line.length) lines.push(line); line = []; width = 0; return; }
    ctx.font = word.font;
    const ww = ctx.measureText(word.w).width;
    let gap = line.length ? 14 : 0;
    if (line.length && width + gap + ww > maxW) { lines.push(line); line = []; width = 0; gap = 0; }
    line.push({ ...word, x: width + gap });
    width += gap + ww;
  });
  if (line.length) lines.push(line);
  return lines;
}

export function drawRich(ctx, runs, { x, y, maxW, size = 92, lh = 1.03, color = '#f4efe6', emColor = '#ff7a6a', weight = 600 }) {
  const fonts = { base: `${weight} ${size}px ${SERIF}`, em: `italic 400 ${size}px ${SERIF}` };
  const lines = wrapRich(ctx, runs, maxW, fonts);
  let cy = y;
  lines.forEach((line) => {
    line.forEach((word) => {
      ctx.font = word.font;
      ctx.fillStyle = word.em ? emColor : color;
      ctx.fillText(word.w, x + word.x, cy);
    });
    cy += size * lh;
  });
  return cy;
}

export function wrapText(ctx, text, maxW, font, size, lh) {
  ctx.font = font;
  const words = String(text || '').split(/\s+/).filter(Boolean);
  const lines = [];
  let line = '';
  words.forEach((w) => {
    const t = line ? line + ' ' + w : w;
    if (line && ctx.measureText(t).width > maxW) { lines.push(line); line = w; }
    else line = t;
  });
  if (line) lines.push(line);
  return { lines, height: lines.length * size * lh, step: size * lh };
}

function shell(ctx, w, h, { accent = '#d4a84b', fill = '#0a0908' } = {}) {
  ctx.clearRect(0, 0, w, h);
  rr(ctx, 2, 2, w - 4, h - 4, 22);
  ctx.fillStyle = fill;
  ctx.fill();
  ctx.strokeStyle = 'rgba(244,239,230,.16)';
  ctx.lineWidth = 2;
  ctx.stroke();
  ctx.strokeStyle = accent;
  ctx.lineWidth = 3;
  [[18, 18, 1, 1], [w - 18, 18, -1, 1], [18, h - 18, 1, -1], [w - 18, h - 18, -1, -1]].forEach(([x, y, sx, sy]) => {
    ctx.beginPath(); ctx.moveTo(x, y + 18 * sy); ctx.lineTo(x, y); ctx.lineTo(x + 18 * sx, y); ctx.stroke();
  });
}

function kicker(ctx, text, x, y, { color = '#d4a84b', size = 27 } = {}) {
  ctx.save();
  ctx.font = `400 ${size}px ${MONO}`;
  ctx.fillStyle = color;
  if ('letterSpacing' in ctx) ctx.letterSpacing = '5px';
  ctx.fillText(String(text).toUpperCase(), x, y);
  if ('letterSpacing' in ctx) ctx.letterSpacing = '0px';
  ctx.restore();
}

function button(ctx, x, y, w, h, label, { solid = true, small = false } = {}) {
  rr(ctx, x, y, w, h, 4);
  if (solid) {
    ctx.fillStyle = '#d4a84b'; ctx.fill();
    ctx.fillStyle = '#171208';
  } else {
    ctx.fillStyle = 'rgba(9,8,7,.6)'; ctx.fill();
    ctx.strokeStyle = 'rgba(244,239,230,.28)'; ctx.lineWidth = 2; ctx.stroke();
    ctx.fillStyle = '#d8cbb8';
  }
  let fs = small ? 19 : 23;
  const text = label.toUpperCase();
  ctx.font = `500 ${fs}px ${MONO}`;
  if ('letterSpacing' in ctx) ctx.letterSpacing = '2px';
  while (fs > 12 && ctx.measureText(text).width + 58 > w) { fs -= 1; ctx.font = `500 ${fs}px ${MONO}`; }
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, x + w / 2, y + h / 2 + 1);
  if ('letterSpacing' in ctx) ctx.letterSpacing = '0px';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'alphabetic';
}

function chip(ctx, x, y, w, h, label, color, size = 19) {
  rr(ctx, x, y, w, h, 3);
  ctx.fillStyle = 'rgba(9,8,7,.62)'; ctx.fill();
  ctx.strokeStyle = 'rgba(244,239,230,.2)'; ctx.lineWidth = 1.5; ctx.stroke();
  ctx.beginPath(); ctx.arc(x + 15, y + h / 2, 4, 0, Math.PI * 2); ctx.fillStyle = color; ctx.fill();
  ctx.font = `400 ${size}px ${MONO}`;
  ctx.fillStyle = 'rgba(244,239,230,.86)';
  ctx.fillText(String(label).toUpperCase(), x + 27, y + h / 2 + size * 0.35);
}

/* ── chapter panel ──────────────────────────────────────────────── */
export function chapterTexture(sec, nodes, narrow = false) {
  const W = narrow ? 760 : 1200, P = narrow ? 56 : 74;
  const FS = narrow ? 84 : 104, FD = narrow ? 27 : 30;
  const raw = document.createElement('canvas');
  raw.width = W; raw.height = 2100;
  const x = raw.getContext('2d');
  const hotspots = [];

  kicker(x, `${sec.num || ''} · ${sec.label}`, P, narrow ? 104 : 118, { size: narrow ? 24 : 27 });
  x.fillStyle = 'rgba(212,168,75,.5)';
  x.fillRect(P + 4, narrow ? 126 : 142, 118, 2);

  const titleRh = drawRich(x, parseRich(sec.title), { x: P, y: narrow ? 232 : 262, maxW: W - P * 2, size: FS, lh: 1.0 });

  let y = Math.max(titleRh + 18, narrow ? 430 : 470);
  const deck = wrapText(x, sec.deck, W - P * 2, `300 ${FD}px ${SANS}`, FD, 1.62);
  x.fillStyle = '#b9ad9d';
  deck.lines.forEach((line, i) => x.fillText(line, P, y + i * deck.step));
  y += deck.height + (narrow ? 32 : 46);

  const chipH = narrow ? 48 : 52, chipSize = narrow ? 17 : 19;
  let cx = P;
  nodes.slice(0, 8).forEach((n) => {
    x.font = `400 ${chipSize}px ${MONO}`;
    const w = Math.max(narrow ? 128 : 150, x.measureText(n.label.toUpperCase()).width + (narrow ? 52 : 62));
    if (cx + w > W - P) { cx = P; y += chipH + 12; }
    chip(x, cx, y, w, chipH, n.label, COL[n.s], chipSize);
    hotspots.push({ x: cx, y, w, h: chipH, action: { type: 'node', id: n.id } });
    cx += w + 12;
  });

  const bw = narrow ? 236 : 268, bh = narrow ? 68 : 72;
  let by = y + chipH + (narrow ? 56 : 66);
  button(x, P, by, bw, bh, 'Inspect chapter', { solid: true });
  hotspots.push({ x: P, y: by, w: bw, h: bh, action: { type: 'node', id: 'ch.' + sec.id } });
  button(x, P + bw + 16, by, narrow ? 236 : 286, bh, 'Read chapter →', { solid: false });
  hotspots.push({ x: P + bw + 16, y: by, w: narrow ? 236 : 286, h: bh, action: { type: 'reader', id: sec.id } });

  const sourceY = by + bh + (narrow ? 50 : 58);
  x.fillStyle = 'rgba(169,157,140,.6)';
  x.font = `400 ${narrow ? 18 : 20}px ${MONO}`;
  if ('letterSpacing' in x) x.letterSpacing = '3px';
  x.fillText(`SOURCE OF TRUTH · #${sec.id}`, P, sourceY);
  if ('letterSpacing' in x) x.letterSpacing = '0px';

  const H = Math.max(Math.ceil(sourceY + (narrow ? 92 : 110)), narrow ? 900 : 980);
  const out = document.createElement('canvas');
  out.width = W; out.height = H;
  const o = out.getContext('2d');
  shell(o, W, H);
  o.save();
  o.font = `600 ${narrow ? 360 : 430}px ${SERIF}`;
  o.fillStyle = 'rgba(244,239,230,.035)';
  o.textAlign = 'right';
  o.fillText(String(sec.num || ''), W - P + 10, H - (narrow ? 150 : 170));
  o.restore();
  o.drawImage(raw, 0, 0, W, H, 0, 0, W, H);

  return { canvas: out, hotspots, w: W, h: H };
}

/* ── dashboard panel (station 0) ────────────────────────────────── */
export function dashboardTexture({ stats, legend, modes, mode, narrow = false }) {
  const W = narrow ? 760 : 1300, H = narrow ? 1400 : 1360, P = narrow ? 56 : 76;
  const c = document.createElement('canvas');
  c.width = W; c.height = H;
  const x = c.getContext('2d');
  const hotspots = [];
  shell(x, W, H, { fill: '#0a0908' });

  kicker(x, narrow ? BRAND.kicker : BRAND.kickerDash, P, narrow ? 92 : 112, { size: narrow ? 20 : 24 });
  x.fillStyle = 'rgba(212,168,75,.5)'; x.fillRect(P + 4, narrow ? 112 : 134, 150, 2);

  const titleRh = drawRich(x, [{ text: BRAND.nameA, em: false }, { text: BRAND.nameB, em: true }],
    { x: P - 4, y: narrow ? 206 : 268, maxW: W - P * 2, size: narrow ? 84 : 116, lh: 1 });

  x.fillStyle = '#b9ad9d';
  const lede = wrapText(x, BRAND.lede,
    W - P * 2, `300 ${narrow ? 25 : 30}px ${SANS}`, narrow ? 25 : 30, 1.62);
  const ly = Math.max(titleRh + 10, narrow ? 246 : 340);
  lede.lines.forEach((line, i) => x.fillText(line, P, ly + i * lede.step));

  let y = ly + lede.height + (narrow ? 36 : 44);
  const cells = [['Entities', stats.nodes], ['Relations', stats.relations], ['Chapters', stats.chapters], ['Sources', stats.sources]];
  const cellH = narrow ? 92 : 116;
  const cols = narrow ? 2 : 4;
  const cw = (W - P * 2 - (cols - 1) * 3) / cols;
  cells.forEach(([k, v], i) => {
    const col = i % cols, row = Math.floor(i / cols);
    const cx = P + col * (cw + 3), cy = y + row * (cellH + 8);
    x.fillStyle = 'rgba(244,239,230,.05)';
    x.fillRect(cx, cy, cw, cellH);
    x.fillStyle = '#f4efe6';
    x.font = `600 ${narrow ? 46 : 58}px ${SERIF}`;
    x.fillText(String(v), cx + (narrow ? 14 : 18), cy + (narrow ? 56 : 62));
    x.fillStyle = 'rgba(169,157,140,.8)';
    x.font = `400 ${narrow ? 16 : 18}px ${MONO}`;
    if ('letterSpacing' in x) x.letterSpacing = narrow ? '2px' : '2px';
    x.fillText(k.toUpperCase(), cx + (narrow ? 14 : 18), cy + (narrow ? 82 : 94));
    if ('letterSpacing' in x) x.letterSpacing = '0px';
  });
  y += cellH * Math.ceil(cells.length / cols) + (cols > 1 && narrow ? 8 : 0) + (narrow ? 36 : 48);

  kicker(x, 'Classes', P, y, { color: 'rgba(169,157,140,.9)', size: narrow ? 17 : 19 });
  y += narrow ? 30 : 34;
  const half = (W - P * 2) / 2;
  const legRows = Math.ceil(legend.length / 2);
  legend.forEach((l, i) => {
    /* column-major so the reader scans down a column, even with an odd count */
    const col = Math.floor(i / legRows), row = i % legRows;
    const lx = P + col * half, lyy = y + row * (narrow ? 42 : 46);
    x.beginPath(); x.arc(lx + 6, lyy + 11, 5.5, 0, Math.PI * 2);
    x.fillStyle = COL[l.s]; x.fill();
    x.fillStyle = 'rgba(244,239,230,.82)';
    x.font = `400 ${narrow ? 20 : 23}px ${MONO}`;
    x.fillText(l.cls, lx + 22, lyy + 18);
    x.fillStyle = 'rgba(169,157,140,.65)';
    x.textAlign = 'right';
    x.fillText(String(l.n), lx + half - 22, lyy + 18);
    x.textAlign = 'left';
  });
  y += legRows * (narrow ? 42 : 46) + (narrow ? 30 : 42);

  kicker(x, 'Filter', P, y, { color: 'rgba(169,157,140,.9)', size: narrow ? 17 : 19 });
  y += narrow ? 22 : 26;
  let mx = P;
  modes.forEach((m) => {
    x.font = `400 ${narrow ? 18 : 21}px ${MONO}`;
    const w = x.measureText(m.label.toUpperCase()).width + (narrow ? 36 : 48);
    if (mx + w > W - P) { mx = P; y += narrow ? 60 : 66; }
    rr(x, mx, y, w, narrow ? 50 : 54, 3);
    const on = m.key === mode;
    x.fillStyle = on ? 'rgba(212,168,75,.14)' : 'rgba(9,8,7,.5)'; x.fill();
    x.strokeStyle = on ? 'rgba(212,168,75,.85)' : 'rgba(244,239,230,.2)'; x.lineWidth = 2; x.stroke();
    x.fillStyle = on ? '#f0c75e' : 'rgba(244,239,230,.7)';
    x.fillText(m.label.toUpperCase(), mx + (narrow ? 18 : 24), y + (narrow ? 32 : 35));
    hotspots.push({ x: mx, y, w, h: narrow ? 50 : 54, action: { type: 'mode', mode: m.key } });
    mx += w + 10;
  });
  y += narrow ? 82 : 92;

  const bw = narrow ? 350 : 380, bh = narrow ? 68 : 78;
  if (narrow) y = Math.max(y, H - 330);
  button(x, P, y, bw, bh, BRAND.startLabel + ' →', { solid: true });
  hotspots.push({ x: P, y, w: bw, h: bh, action: { type: 'goto', id: BRAND.startId } });
  if (narrow) {
    button(x, P, y + 82, bw, bh, 'Read as text', { solid: false });
    hotspots.push({ x: P, y: y + 82, w: bw, h: bh, action: { type: 'reader', id: 'cover' } });
  } else {
    button(x, P + 398, y, 300, bh, 'Read as text', { solid: false });
    hotspots.push({ x: P + 398, y, w: 300, h: bh, action: { type: 'reader', id: 'cover' } });
  }

  x.fillStyle = 'rgba(169,157,140,.62)';
  x.font = `400 ${narrow ? 14 : 20}px ${MONO}`;
  if ('letterSpacing' in x) x.letterSpacing = narrow ? '1px' : '3px';
  const note = narrow ? (BRAND.noteWrap || [BRAND.noteShort || BRAND.note]) : [BRAND.note];
  note.forEach((line, i) => x.fillText(line, P, H - (narrow ? 84 : 74) + i * 24));
  if ('letterSpacing' in x) x.letterSpacing = '0px';

  return { canvas: c, hotspots, w: W, h: H };
}

/* ── intro panel ────────────────────────────────────────────────── */
export function introTexture(narrow = false) {
  const W = narrow ? 760 : 1280, H = narrow ? 1000 : 840, P = narrow ? 56 : 86;
  const c = document.createElement('canvas');
  c.width = W; c.height = H;
  const x = c.getContext('2d');
  const hotspots = [];
  x.clearRect(0, 0, W, H);
  rr(x, 2, 2, W - 4, H - 4, 26);
  x.fillStyle = '#0a0908'; x.fill();
  x.strokeStyle = 'rgba(244,239,230,.18)'; x.lineWidth = 2; x.stroke();

  kicker(x, BRAND.kickerIntro, P, narrow ? 92 : 118, { size: narrow ? 20 : 23 });
  drawRich(x, [{ text: BRAND.introA, em: false }], { x: P - 4, y: narrow ? 214 : 250, maxW: W - P * 2, size: narrow ? 76 : 100 });
  drawRich(x, [{ text: BRAND.introB, em: true }], { x: P - 4, y: narrow ? 302 : 356, maxW: W - P * 2, size: narrow ? 76 : 100 });

  const sub = wrapText(x, `${BRAND.introSub} ${stats.nodes} entities, ${stats.relations} relations.`,
    W - P * 2, `300 ${narrow ? 25 : 27}px ${SANS}`, narrow ? 25 : 27, 1.6);
  x.fillStyle = '#b9ad9d';
  sub.lines.forEach((line, i) => x.fillText(line, P, (narrow ? 420 : 486) + i * sub.step));

  const by = narrow ? 640 : 630;
  button(x, P, by, narrow ? 320 : 300, narrow ? 68 : 76, 'Enter the map', { solid: true });
  hotspots.push({ x: P, y: by, w: narrow ? 320 : 300, h: narrow ? 68 : 76, action: { type: 'enter' } });
  if (narrow) {
    button(x, P, by + 84, 320, 68, 'Read as text', { solid: false });
    hotspots.push({ x: P, y: by + 84, w: 320, h: 68, action: { type: 'reader', id: 'cover' } });
  } else {
    button(x, P + 318, by, 250, 76, 'Read as text', { solid: false });
    hotspots.push({ x: P + 318, y: by, w: 250, h: 76, action: { type: 'reader', id: 'cover' } });
  }

  x.fillStyle = 'rgba(169,157,140,.6)';
  x.font = `400 ${narrow ? 15 : 18}px ${MONO}`;
  if ('letterSpacing' in x) x.letterSpacing = '2px';
  x.fillText(narrow ? BRAND.noteShort : BRAND.note, P, narrow ? 910 : 796);
  if ('letterSpacing' in x) x.letterSpacing = '0px';
  return { canvas: c, hotspots, w: W, h: H };
}

/* ── inspector panel ────────────────────────────────────────────── */
export function inspectorTexture(node, rels, narrow = false) {
  const W = narrow ? 760 : 980, P = narrow ? 48 : 62;
  const raw = document.createElement('canvas');
  raw.width = W; raw.height = 1600;
  const x = raw.getContext('2d');
  const hotspots = [];

  x.beginPath(); x.arc(P + 5, 80, 6, 0, Math.PI * 2); x.fillStyle = COL[node.s]; x.fill();
  kicker(x, node.cls, P + 22, 88, { color: COL[node.s], size: narrow ? 18 : 21 });
  const closeX = W - P - 24;
  x.strokeStyle = 'rgba(244,239,230,.5)'; x.lineWidth = 2;
  x.beginPath(); x.moveTo(closeX - 9, 64); x.lineTo(closeX + 9, 82); x.moveTo(closeX + 9, 64); x.lineTo(closeX - 9, 82); x.stroke();
  hotspots.push({ x: closeX - 28, y: 52, w: 56, h: 48, action: { type: 'close' } });

  const titleRh = drawRich(x, [{ text: node.label, em: false }], { x: P - 2, y: narrow ? 174 : 196, maxW: W - P * 2, size: narrow ? 56 : 64, lh: 1.0 });
  let y = titleRh - 12;
  const desc = wrapText(x, node.desc || '', W - P * 2, `300 ${narrow ? 24 : 25}px ${SANS}`, narrow ? 24 : 25, 1.55);
  x.fillStyle = '#b9ad9d';
  const maxDesc = narrow ? 7 : 5;
  desc.lines.slice(0, maxDesc).forEach((line, i) => x.fillText(line, P, y + i * desc.step));
  y += Math.min(desc.lines.length, maxDesc) * desc.step + (narrow ? 14 : 18);

  if (node.quote) {
    x.fillStyle = 'rgba(212,168,75,.6)'; x.fillRect(P, y - 12, 3, narrow ? 54 : 58);
    const q = wrapText(x, `“${node.quote}”`, W - P * 2 - 20, `italic 400 ${narrow ? 23 : 24}px ${SERIF}`, narrow ? 23 : 24, 1.4);
    x.fillStyle = 'rgba(244,239,230,.8)';
    q.lines.slice(0, 2).forEach((line, i) => x.fillText(line, P + 18, y + 10 + i * q.step));
    y += Math.min(q.lines.length, 2) * q.step + (narrow ? 30 : 42);
  }
  x.fillStyle = 'rgba(169,157,140,.7)';
  x.font = `400 ${narrow ? 17 : 19}px ${MONO}`;
  x.fillText(`SOURCE · ${String(node.ref || '').toUpperCase()}`, P, y);
  y += narrow ? 32 : 38;

  x.strokeStyle = 'rgba(244,239,230,.12)'; x.lineWidth = 1;
  x.beginPath(); x.moveTo(P, y - 14); x.lineTo(W - P, y - 14); x.stroke();
  x.fillStyle = 'rgba(169,157,140,.7)';
  x.font = `400 ${narrow ? 15 : 17}px ${MONO}`;
  x.fillText('RELATIONS', P, y + 6);
  y += narrow ? 28 : 30;
  rels.slice(0, narrow ? 4 : 5).forEach((r) => {
    x.beginPath(); x.arc(P + 5, y - 7, 4, 0, Math.PI * 2); x.fillStyle = COL[r.node.s]; x.fill();
    x.fillStyle = 'rgba(244,239,230,.82)';
    x.font = `400 ${narrow ? 19 : 22}px ${MONO}`;
    x.fillText(`${r.dir === 'out' ? '→' : '←'} ${r.node.label}`, P + 18, y);
    x.fillStyle = 'rgba(169,157,140,.6)';
    x.font = `400 ${narrow ? 14 : 17}px ${MONO}`;
    x.textAlign = 'right';
    x.fillText(String(r.rel).toUpperCase(), W - P, y);
    x.textAlign = 'left';
    hotspots.push({ x: P, y: y - 26, w: W - P * 2, h: 34, action: { type: 'node', id: r.node.id } });
    y += narrow ? 34 : 38;
  });

  const bh = narrow ? 60 : 64, by = y + 26;
  button(x, P, by, narrow ? 200 : 250, bh, 'Read chapter', { solid: false, small: narrow });
  hotspots.push({ x: P, y: by, w: narrow ? 200 : 250, h: bh, action: { type: 'reader', id: node.chapter } });
  if (node.href) {
    button(x, P + (narrow ? 214 : 268), by, narrow ? 200 : 230, bh, 'Open lane ↗', { solid: true, small: true });
    hotspots.push({ x: P + (narrow ? 214 : 268), y: by, w: narrow ? 200 : 230, h: bh, action: { type: 'href', href: node.href } });
  }

  const H = Math.max(by + bh + (narrow ? 66 : 70), narrow ? 720 : 600);
  const out = document.createElement('canvas');
  out.width = W; out.height = H;
  const o = out.getContext('2d');
  shell(o, W, H, { fill: '#0a0908' });
  o.drawImage(raw, 0, 0, W, H, 0, 0, W, H);

  return { canvas: out, hotspots, w: W, h: H };
}

/* ── station bar: 3D navigation under each chapter ─────────────── */
export function barTexture({ current, label, narrow = false }) {
  const W = narrow ? 760 : 1500, H = narrow ? 280 : 270;
  const c = document.createElement('canvas');
  c.width = W; c.height = H;
  const x = c.getContext('2d');
  const hotspots = [];
  x.clearRect(0, 0, W, H);
  rr(x, 2, 2, W - 4, H - 4, 10);
  x.fillStyle = 'rgba(7,6,5,.9)'; x.fill();
  x.strokeStyle = 'rgba(244,239,230,.14)'; x.lineWidth = 2; x.stroke();

  const n = SECTIONS.length;
  if (narrow) {
    x.fillStyle = 'rgba(169,157,140,.82)';
    x.font = `400 21px ${MONO}`;
    if ('letterSpacing' in x) x.letterSpacing = '2px';
    x.fillText('DRAG · SCROLL · CLICK', 30, 86);
    if ('letterSpacing' in x) x.letterSpacing = '0px';

    x.fillStyle = 'rgba(244,239,230,.92)';
    x.font = `600 30px ${SERIF}`;
    x.textAlign = 'right';
    x.fillText(String(label || ''), 730, 84);
    x.fillStyle = 'rgba(169,157,140,.6)';
    x.font = `400 16px ${MONO}`;
    x.fillText(`${String(current).padStart(2, '0')} / ${String(n - 1).padStart(2, '0')}`, 730, 114);
    x.textAlign = 'left';

    const x0 = 90, step = Math.min(52, (552 - x0) / (n - 1));
    for (let i = 0; i < n; i++) {
      const cx = x0 + i * step, cy = 182, on = i === current;
      if (on) { x.beginPath(); x.arc(cx, cy, 15, 0, Math.PI * 2); x.strokeStyle = 'rgba(212,168,75,.55)'; x.lineWidth = 2; x.stroke(); }
      x.beginPath(); x.arc(cx, cy, on ? 9 : 6, 0, Math.PI * 2);
      x.fillStyle = on ? '#f0c75e' : 'rgba(244,239,230,.32)'; x.fill();
      x.font = `400 15px ${MONO}`; x.textAlign = 'center';
      x.fillStyle = on ? 'rgba(240,199,94,.95)' : 'rgba(169,157,140,.5)';
      x.fillText(i === 0 ? '00' : String(i).padStart(2, '0'), cx, 222);
      x.textAlign = 'left';
      hotspots.push({ x: cx - 24, y: 148, w: 48, h: 92, action: { type: 'station', i } });
    }

    rr(x, 604, 156, 126, 52, 4);
    x.fillStyle = 'rgba(9,8,7,.5)'; x.fill();
    x.strokeStyle = 'rgba(244,239,230,.3)'; x.lineWidth = 2; x.stroke();
    x.fillStyle = 'rgba(216,203,184,.95)';
    x.font = `500 19px ${MONO}`; x.textAlign = 'center';
    x.fillText('TEXT', 667, 189);
    x.textAlign = 'left';
    hotspots.push({ x: 604, y: 156, w: 126, h: 52, action: { type: 'reader', id: null } });
  } else {
    x.fillStyle = 'rgba(169,157,140,.82)';
    x.font = `400 24px ${MONO}`;
    if ('letterSpacing' in x) x.letterSpacing = '3px';
    x.fillText('DRAG TO ORBIT', 44, 96);
    x.fillText('SCROLL TO WALK', 44, 142);
    x.fillStyle = 'rgba(169,157,140,.45)';
    x.fillText('CLICK A GLOW', 44, 188);
    if ('letterSpacing' in x) x.letterSpacing = '0px';

    const x0 = 420, step = Math.min(74, (1040 - x0) / (n - 1));
    for (let i = 0; i < n; i++) {
      const cx = x0 + i * step, cy = 106, on = i === current;
      if (on) { x.beginPath(); x.arc(cx, cy, 17, 0, Math.PI * 2); x.strokeStyle = 'rgba(212,168,75,.55)'; x.lineWidth = 2; x.stroke(); }
      x.beginPath(); x.arc(cx, cy, on ? 10 : 7, 0, Math.PI * 2);
      x.fillStyle = on ? '#f0c75e' : 'rgba(244,239,230,.32)'; x.fill();
      x.font = `400 19px ${MONO}`; x.textAlign = 'center';
      x.fillStyle = on ? 'rgba(240,199,94,.95)' : 'rgba(169,157,140,.5)';
      x.fillText(i === 0 ? '00' : String(i).padStart(2, '0'), cx, 162);
      x.textAlign = 'left';
      hotspots.push({ x: cx - 26, y: 74, w: 52, h: 100, action: { type: 'station', i } });
    }

    x.fillStyle = 'rgba(244,239,230,.88)';
    x.font = `600 30px ${SERIF}`;
    x.textAlign = 'right';
    x.fillText(String(label || ''), 1310, 98);
    x.fillStyle = 'rgba(169,157,140,.6)';
    x.font = `400 20px ${MONO}`;
    if ('letterSpacing' in x) x.letterSpacing = '3px';
    x.fillText(`${String(current).padStart(2, '0')} / ${String(n - 1).padStart(2, '0')}`, 1310, 146);
    if ('letterSpacing' in x) x.letterSpacing = '0px';
    x.textAlign = 'left';

    rr(x, 1330, 78, 132, 62, 4);
    x.fillStyle = 'rgba(9,8,7,.5)'; x.fill();
    x.strokeStyle = 'rgba(244,239,230,.3)'; x.lineWidth = 2; x.stroke();
    x.fillStyle = 'rgba(216,203,184,.95)';
    x.font = `500 22px ${MONO}`; x.textAlign = 'center';
    x.fillText('TEXT', 1396, 118);
    x.textAlign = 'left';
    hotspots.push({ x: 1330, y: 78, w: 132, h: 62, action: { type: 'reader', id: null } });
  }

  return { canvas: c, hotspots, w: W, h: H };
}
