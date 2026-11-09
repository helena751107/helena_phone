/* S21 PHONE — the page itself is the WebGPU scene.
 *
 * There is no HTML dashboard over the canvas. Chapter typography, the stats
 * board, the filter/legend, navigation, the intro and the inspector are all
 * 3D planes with CanvasTexture type and UV hotspots. Scroll walks the eight
 * stations, drag orbits the current one, clicks select glows.
 *
 * Renderer: three.js WebGPURenderer (GPU compute graph) with WebGL2 fallback.
 * If neither starts, the plain webzine returns.
 */
import * as THREE from 'three/webgpu';
import { createGraph } from './graph.js';
import { NODES, LINKS, COL, CLASS, SECTIONS, stats, BRAND } from './ontology.js';
import { loadFonts, chapterTexture, dashboardTexture, introTexture, inspectorTexture, barTexture } from './panels.js';

const MODE_KEY = 's21p-mode';
const INTRO_KEY = 's21p-onto-intro';
const MODES = {
  all: { label: 'All', cls: null },
  tracks: { label: 'Tracks', cls: ['Track'] },
  build: { label: 'Build', cls: ['Module'] },
  agents: { label: 'Agents', cls: ['Agent'] },
  flow: { label: 'Funnel', cls: ['Stage'] },
  gates: { label: 'Channels', cls: ['Channel', 'Install'] }
};
const RELCOL = { chapter: '#8fb3c9', contains: '#77858f', flow: '#d4a84b', routes: '#ff7a6a', support: '#3db8a8' };
const RELALPHA = { chapter: 0.18, contains: 0.15, flow: 0.36, routes: 0.44, support: 0.22 };

const GAP = 900;

const esc = (s) => String(s || '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const norm = (s) => String(s || '').replace(/\s+/g, ' ').trim();
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const zOf = (i) => -i * GAP;
const stationOf = (n) => {
  const c = n.chapter || 'cover';
  const i = SECTIONS.indexOf(c);
  return i < 0 ? 0 : i;
};

let inst = null;

export async function initOnto(opts = {}) {
  if (inst) return inst.api;
  const html = document.documentElement;
  const params = new URLSearchParams(location.search);
  const touch = matchMedia('(pointer: coarse)').matches;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const sections = readSections();
  /* The landing page always boots in 3D. Text mode is an explicit, visible
     choice (?text), never a stored flag that quietly hides the whole map on
     the next visit. */
  const startReader = params.has('text') || params.get('mode') === 'reader';
  const narrow = innerWidth / innerHeight < 0.9;
  const DIM = narrow
    ? { ch: [240, 474], dash: [240, 442], intro: [280, 368], ins: [240, 310], bar: [240, 88.5] }
    : { ch: [320, 340], dash: [320, 335], intro: [560, 367.5], ins: [320, 235], bar: [320, 57.6] };
  const stationH = {};
  const dimOfStation = (i) => (i === 0 ? DIM.dash : [DIM.ch[0], stationH[i] || DIM.ch[1]]);
  const barYFor = (i) => 90 - dimOfStation(i)[1] / 2 - 14 - DIM.bar[1] / 2;

  if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
  if (startReader) {
    html.removeAttribute('data-onto');
    inst = { api: stubApi(sections, html) };
    return inst.api;
  }

  try {
    await loadFonts();
  } catch (e) {}

  html.setAttribute('data-onto', 'on');

  /* ── shell: a scroll surface and one fixed WebGPU canvas ───────── */
  const root = document.createElement('div');
  root.className = 'onto';
  root.id = 'onto';
  root.innerHTML = `<div id="ontoGl" aria-hidden="true"></div>
    <a class="ov-sr" href="?text">Read this page as text instead</a>
    <div class="ov-scroll" aria-hidden="true"></div>`;
  document.body.appendChild(root);
  const glHost = root.querySelector('#ontoGl');
  const scrollEl = root.querySelector('.ov-scroll');
  scrollEl.style.height = `${SECTIONS.length * 100}vh`;

  /* One station = the real pixel height of the scroll surface. Using this
     instead of innerHeight keeps the station grid steady when a phone's URL
     bar slides away and innerHeight changes under us. */
  const stepPx = () => {
    const h = scrollEl.getBoundingClientRect().height / SECTIONS.length;
    return h > 10 ? h : Math.max(1, innerHeight);
  };
  const stationY = (i) => Math.round(i * stepPx());

  /* ── ontology layout → station coordinates ─────────────────────── */
  const P = layoutPositions(sections, narrow);
  const glNodes = NODES.map((n) => ({ ...n, x: P.get(n.id).x, y: P.get(n.id).y, z: P.get(n.id).z }));
  const glLinks = LINKS.map((l) => ({ source: l.source, target: l.target, rel: l.rel }));

  let G;
  try {
    G = await createGraph(glHost, { nodes: glNodes, links: glLinks });
  } catch (e) {
    console.warn('[onto] renderer unavailable:', e && e.message);
    root.remove();
    html.removeAttribute('data-onto');
    inst = { api: stubApi(sections, html) };
    return inst.api;
  }

  const scene = G.scene(), camera = G.camera(), controls = G.controls();
  const renderer = G.renderer();
  controls.autoRotate = false;
  controls.enableZoom = false;
  controls.enablePan = false;
  controls.enableDamping = true;
  controls.dampingFactor = 0.055;
  if (touch) controls.enableRotate = false;
  G.U.rep.value = 280; G.U.len.value = 40; G.U.spring.value = 0.02; G.U.damp.value = 0.9; G.U.fireRate.value = 0.0025;

  const byId = new Map(NODES.map((n) => [n.id, n]));
  const legend = CLASS.map((cls, s) => ({ cls, s, n: NODES.filter((n) => n.s === s).length }));
  const modeList = Object.entries(MODES).map(([key, m]) => ({ key, label: m.label }));
  let mode = 'all';

  const dimOf = (n) => { const m = MODES[mode]; return !m.cls || m.cls.includes(n.cls) ? 1 : 0; };
  const RINGCOL = {
    'ch.tracks': '#e85d4c', 'ch.system': '#3db8a8', 'ch.agents': '#8b7cf0', 'ch.centers': '#d4a84b',
    'ch.funnel': '#f0c75e', 'ch.economics': '#8fb3c9', 'ch.install': '#f0c75e',
    'ch.library': '#3db8a8', 'ch.channels': '#8b7cf0'
  };
  const big = (n) => (n.id === 'phone' ? 26 : n.id.startsWith('ch.') ? 22 : (4.6 + Math.sqrt(n.val || 1) * 2.2) * (n.chapter ? 1.85 : 1));

  function applyStyle() {
    G.nodeColor((n) => RINGCOL[n.id] || COL[n.s])
      .nodeAlpha((n) => (dimOf(n) ? (n.id === 'phone' ? 0.96 : 0.9) : 0.1))
      .nodeSize((n) => big(n) * (dimOf(n) ? 1 : 0.5))
      .nodeHot((n) => (n.hot ? 1 : 0))
      .linkColor((l) => RELCOL[l.rel] || '#8fb3c9')
      .linkAlpha((l) => (dimOf(l.source) && dimOf(l.target) ? RELALPHA[l.rel] ?? 0.16 : 0.02))
      .linkDirectionalParticles((l) => (l.rel === 'flow' || l.rel === 'routes' ? 1 : 0))
      .restyle();
  }
  applyStyle();
  G.setTargets((n) => {
    const p = P.get(n.id);
    return p ? [p.x, p.y, p.z, 0.92] : null;
  });

  /* ── 3D typography: every panel is a plane in the scene ───────── */
  const panels = [];
  function setTexture(mesh, tex) {
    const m = mesh.material;
    if (m.map) m.map.dispose();
    const t = new THREE.CanvasTexture(tex.canvas);
    t.colorSpace = THREE.SRGBColorSpace;
    t.anisotropy = 4;
    m.map = t;
    m.needsUpdate = true;
    mesh.userData.tex = tex;
    mesh.userData.hotspots = tex.hotspots || [];
  }
  function addPanel(tex, w, h, x, y, z, kind) {
    const t = new THREE.CanvasTexture(tex.canvas);
    t.colorSpace = THREE.SRGBColorSpace;
    t.anisotropy = 4;
    const mat = new THREE.MeshBasicMaterial({ map: t, transparent: true, depthWrite: false, toneMapped: false, opacity: 1 });
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(w, h), mat);
    mesh.position.set(x, y, z);
    mesh.renderOrder = 4;
    mesh.userData = { tex, hotspots: tex.hotspots || [], w, h, kind };
    scene.add(mesh);
    panels.push(mesh);
    return mesh;
  }

  const dashMesh = addPanel(dashboardTexture({ stats, legend, modes: modeList, mode, narrow }), DIM.dash[0], DIM.dash[1], 0, 90, zOf(0), 'dash');
  stationH[0] = DIM.dash[1];
  const chapterMeshes = sections.slice(1).map((s, i) => {
    const tex = chapterTexture(s, s.entities, narrow);
    const h = (DIM.ch[0] * tex.h) / tex.w;
    stationH[i + 1] = h;
    return addPanel(tex, DIM.ch[0], h, 0, 90, zOf(i + 1), 'chapter');
  });
  const introMesh = addPanel(introTexture(narrow), DIM.intro[0], DIM.intro[1], 0, 160, 280, 'intro');
  const barMesh = addPanel(barTexture({ current: 0, label: 'Cover', narrow }), DIM.bar[0], DIM.bar[1], 0, barYFor(0), zOf(0), 'bar');
  barMesh.visible = false;
  const ins0 = inspectorTexture(byId.get('phone'), [], narrow);
  const insH = narrow ? 268 : 260;
  const insMesh = addPanel(ins0, (insH * ins0.w) / ins0.h, insH, 0, 90, 60, 'ins');
  insMesh.visible = false;
  function fitInspector(tex) {
    const w = Math.max(180, dimOfStation(Math.max(0, current))[0] - (narrow ? 6 : 12));
    const h = (w * tex.h) / tex.w;
    setTexture(insMesh, tex);
    insMesh.geometry.dispose();
    insMesh.geometry = new THREE.PlaneGeometry(w, h);
    insMesh.userData.w = w;
    insMesh.userData.h = h;
  }

  /* hover highlight (one mesh, repositioned) */
  const hl = new THREE.Mesh(
    new THREE.PlaneGeometry(1, 1),
    new THREE.MeshBasicMaterial({ color: 0xf0c75e, transparent: true, opacity: 0.14, depthWrite: false, depthTest: false, toneMapped: false })
  );
  hl.renderOrder = 6; hl.visible = false; scene.add(hl);

  function showHighlight(mesh, spot) {
    const d = mesh.userData;
    const w = (d.w * spot.w) / d.tex.w, h = (d.h * spot.h) / d.tex.h;
    const lx = -d.w / 2 + ((spot.x + spot.w / 2) / d.tex.w) * d.w;
    const ly = d.h / 2 - ((spot.y + spot.h / 2) / d.tex.h) * d.h;
    hl.position.set(mesh.position.x + lx, mesh.position.y + ly, mesh.position.z + 0.8);
    hl.scale.set(w, h, 1);
    hl.visible = true;
  }
  const hideHighlight = () => { hl.visible = false; };

  /* ── camera stations ──────────────────────────────────────────── */
  let current = -1, selected = null, introOn = false, paused = false;

  /* One distance for every station: the reader never gets re-scaled when the
     card changes. The column just slides, like pages in a frame. */
  let frameD = 0;
  function computeFrameD() {
    const aspect = Math.max(0.3, innerWidth / innerHeight);
    const tan = Math.tan(((camera.fov || 42) * Math.PI) / 360);
    let d = 300;
    for (let i = 0; i < SECTIONS.length; i++) {
      const [w, h] = dimOfStation(i);
      const top = 90 + h / 2 + 8, bottom = barYFor(i) - DIM.bar[1] / 2 - 8;
      d = Math.max(d, ((top - bottom) / (2 * tan)) * (narrow ? 1.07 : 1.02), (w * (narrow ? 1.08 : 1.14)) / (2 * tan * aspect));
    }
    frameD = d;
  }

  function frameFor(i) {
    const fov = camera.fov || 42;
    const tan = Math.tan((fov * Math.PI) / 360);
    const h = dimOfStation(i)[1];
    const top = 90 + h / 2 + 8, bottom = barYFor(i) - DIM.bar[1] / 2 - 8;
    const lookY = (top + bottom) / 2;
    const d = frameD || 900;
    return { pos: { x: 0, y: lookY + d * 0.02, z: zOf(i) + d }, look: { x: 0, y: lookY, z: zOf(i) } };
  }

  let barShown = -1;
  function updateBar(i) {
    if (barShown !== i) {
      barShown = i;
      setTexture(barMesh, barTexture({ current: i, label: i === 0 ? 'Cover' : sections[i].label, narrow }));
    }
    barMesh.position.set(0, barYFor(i), zOf(i));
    barMesh.visible = true;
  }

  function panelOf(i) {
    return i === 0 ? dashMesh : chapterMeshes[Math.max(0, i - 1)];
  }

  /* Arrive with a short fade-in only: no zoom, no slide, no camera tween. */
  let fadeRaf = 0;
  function arrive(mesh, to) {
    if (!mesh) return;
    cancelAnimationFrame(fadeRaf);
    if (reduce) { mesh.material.opacity = to; return; }
    const t0 = performance.now();
    mesh.material.opacity = 0;
    const step = () => {
      const k = Math.min(1, (performance.now() - t0) / 130);
      mesh.material.opacity = to * (0.25 + 0.75 * k);
      if (k < 1) fadeRaf = requestAnimationFrame(step);
      else mesh.material.opacity = to;
    };
    fadeRaf = requestAnimationFrame(step);
  }

  /* The camera never moves by itself. Scroll picks the station; the cut is
     instant, so the scrollbar is always exactly where the reader left it. */
  function reframe(i = current) {
    if (i < 0) return;
    const f = frameFor(i);
    G.cameraPosition(f.pos, f.look, 0);
    updateBar(i);
    arrive(panelOf(i), selected ? 0.16 : 1);
  }

  function go(i) {
    hideHighlight();
    /* any programmatic walk leaves the intro card behind, never strands it */
    if (introOn) dismissIntro(true);
    i = clamp(i, 0, SECTIONS.length - 1);
    if (i === current) return;
    current = i;
    deselect();
    reframe(i);
    try { history.replaceState(null, '', location.pathname + location.search + '#' + SECTIONS[i]); } catch (e) {}
  }

  /* ── scroll ⇄ camera agreement ───────────────────────────────────
     The scrollbar is moved to the station so the reader's scroll position and
     the camera agree. While that write (or a settle) is in flight we ignore
     the echo scroll events — but any real input (wheel, touch, key, pointer)
     breaks the guard immediately, so no gesture is ever swallowed. */
  let settling = false, settleTo = 0, settleT = 0, idleT = 0;

  /* The snap runs on our own rAF clock: native `behavior:'smooth'` is dropped
     by some browsers/GPU states, and a drop here would leave the scrollbar and
     the camera on different stations. */
  function settleToStation(i, smooth = true) {
    const y = stationY(i);
    if (i !== current) go(i);
    if (Math.abs(scrollY - y) < 1) { settling = false; return; }
    settleTo = y; settling = true;
    clearTimeout(settleT);
    if (!smooth) { window.scrollTo(0, y); settleT = setTimeout(() => { settling = false; }, 90); return; }
    const from = scrollY, d = y - from, t0 = performance.now();
    const tick = () => {
      if (!settling) return;
      const k = Math.min(1, (performance.now() - t0) / 420);
      const e = k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
      window.scrollTo(0, Math.round(from + d * e));
      if (k < 1) requestAnimationFrame(tick); else settling = false;
    };
    requestAnimationFrame(tick);
    settleT = setTimeout(() => { settling = false; }, 900);
  }

  const breakSettle = () => { settling = false; clearTimeout(settleT); };
  function jumpTo(i) {
    clearTimeout(idleT);
    settleToStation(i, false);
  }

  function dismissIntro(keepScroll) {
    if (!introOn) return;
    introOn = false;
    try { localStorage.setItem(INTRO_KEY, '1'); } catch (e) {}
    introMesh.visible = false;
    introMesh.userData.hotspots = [];
    barMesh.visible = true;
    if (!keepScroll) { window.scrollTo(0, 0); go(0); }
  }

  function select(n) {
    if (!n) return;
    hideHighlight();
    selected = n;
    G.fire(n);
    const rels = LINKS.filter((l) => l.source === n.id || l.target === n.id).map((l) => {
      const other = byId.get(l.source === n.id ? l.target : l.source);
      return other ? { node: other, rel: l.rel, dir: l.source === n.id ? 'out' : 'in' } : null;
    }).filter(Boolean);
    fitInspector(inspectorTexture(n, rels, narrow));
    insMesh.visible = true;
    insMesh.material.opacity = 1;
    insMesh.position.set(0, 90, zOf(current < 0 ? 0 : current) + 3);
    const p = current === 0 ? dashMesh : chapterMeshes[Math.max(0, current - 1)];
    if (p) p.material.opacity = 0.16;
    insMesh.scale.setScalar(0.94);
    const t0 = performance.now();
    const step = () => { const k = Math.min(1, (performance.now() - t0) / 260); insMesh.scale.setScalar(0.94 + 0.06 * k); if (k < 1) requestAnimationFrame(step); };
    requestAnimationFrame(step);
  }

  function deselect() {
    hideHighlight();
    selected = null;
    insMesh.visible = false;
    if (dashMesh) dashMesh.material.opacity = 1;
    chapterMeshes.forEach((m) => (m.material.opacity = 1));
  }

  function setMode(m) {
    mode = MODES[m] ? m : 'all';
    applyStyle();
    setTexture(dashMesh, dashboardTexture({ stats, legend, modes: modeList, mode, narrow }));
  }

  function enterReader(secId) {
    try { localStorage.removeItem(MODE_KEY); } catch (e) {}
    html.removeAttribute('data-onto');
    try { history.replaceState(null, '', location.pathname + '?text' + (SECTIONS.includes(secId) ? '#' + secId : '')); } catch (e) {}
    root.style.display = 'none';
    G.pause(true);
    paused = true;
    backTo3D();
    const id = SECTIONS.includes(secId) ? secId : SECTIONS[Math.max(0, current)] || 'cover';
    const el = document.getElementById(id);
    if (el) {
      const head = el.querySelector('.acc-head');
      if (head && head.getAttribute('aria-expanded') !== 'true') head.click();
      /* the webzine uses CSS smooth scrolling; for this jump it should land,
         not glide, so the reader sees the chapter immediately */
      setTimeout(() => {
        const prev = html.style.scrollBehavior;
        html.style.scrollBehavior = 'auto';
        el.scrollIntoView({ behavior: 'auto', block: 'start' });
        html.style.scrollBehavior = prev;
      }, 60);
    }
  }

  /* ── pointer: panels first, then glows ────────────────────────── */
  const raycaster = new THREE.Raycaster();
  const ndc = new THREE.Vector2();
  const V3 = new THREE.Vector3();

  function hitPanel(cx, cy) {
    ndc.set((cx / innerWidth) * 2 - 1, -(cy / innerHeight) * 2 + 1);
    raycaster.setFromCamera(ndc, camera);
    const list = [introMesh, insMesh, barMesh, dashMesh, ...chapterMeshes].filter((m) => m.visible);
    const hits = raycaster.intersectObjects(list, false);
    for (const h of hits) {
      const m = h.object, d = m.userData;
      if (!h.uv || !d.tex) continue;
      const px = h.uv.x * d.tex.w, py = (1 - h.uv.y) * d.tex.h;
      const pad = touch ? 10 : 5;   /* a fingertip / a jittery hand still lands */
      const spot = (d.hotspots || []).find((s) => px >= s.x - pad && px <= s.x + s.w + pad && py >= s.y - pad && py <= s.y + s.h + pad);
      if (spot) return { mesh: m, spot };
      return { mesh: m, spot: null };
    }
    return null;
  }

  function pickNode(cx, cy, rad = 16) {
    let best = null, bd = rad * rad;
    const w2 = innerWidth / 2, h2 = innerHeight / 2;
    for (const n of glNodes) {
      if (typeof n.x !== 'number') continue;
      V3.set(n.x, n.y, n.z).project(camera);
      if (V3.z > 1) continue;
      const dx = (V3.x + 1) * w2 - cx, dy = (1 - V3.y) * h2 - cy, d = dx * dx + dy * dy;
      if (d < bd) { bd = d; best = n; }
    }
    return best;
  }

  function doAction(a) {
    if (!a) return;
    if (a.type === 'enter') return dismissIntro(false);
    if (a.type === 'station') { dismissIntro(false); jumpTo(a.i); return; }
    if (a.type === 'goto') { const i = SECTIONS.indexOf(a.id); if (i >= 0) jumpTo(i); return; }
    if (a.type === 'mode') return setMode(a.mode);
    if (a.type === 'node') { const n = byId.get(a.id); if (n) select(n); return; }
    if (a.type === 'reader') return enterReader(a.id || SECTIONS[Math.max(0, current)]);
    if (a.type === 'close') return deselect();
    if (a.type === 'href') return window.open(a.href, '_blank', 'noopener');
  }

  const canvas = renderer.domElement;
  canvas.style.touchAction = 'pan-y';
  let down = null, lastHover = 0;

  canvas.addEventListener('pointerdown', (e) => { down = [e.clientX, e.clientY, performance.now()]; }, { passive: true });
  canvas.addEventListener('pointerup', (e) => {
    if (!down) return;
    const dx = e.clientX - down[0], dy = e.clientY - down[1];
    down = null;
    if (Math.hypot(dx, dy) > (touch ? 16 : 10)) {
      if (touch && Math.abs(dx) > 70 && Math.abs(dx) > Math.abs(dy) * 1.6) {
        const i = clamp((current < 0 ? 0 : current) + (dx < 0 ? 1 : -1), 0, SECTIONS.length - 1);
        jumpTo(i);
      }
      return;
    }
    hideHighlight();
    const hit = hitPanel(e.clientX, e.clientY);
    if (hit) { if (hit.spot) doAction(hit.spot.action); return; }
    const n = pickNode(e.clientX, e.clientY, touch ? 30 : 20);
    if (n) select(n); else deselect();
  }, { capture: true });

  canvas.addEventListener('pointermove', (e) => {
    const now = performance.now();
    if (now - lastHover < 60) return;
    lastHover = now;
    const hit = hitPanel(e.clientX, e.clientY);
    if (hit && hit.spot) {
      canvas.style.cursor = 'pointer';
      showHighlight(hit.mesh, hit.spot);
    } else hideHighlight();
  }, { passive: true });
  canvas.addEventListener('pointerleave', hideHighlight);

  /* ── scroll · keys · resize ───────────────────────────────────── */
  /* Scroll is the authority. We read it and cut; a write only happens on an
     explicit station request or once the reader has stopped moving. */
  addEventListener('scroll', () => {
    if (paused) return;
    if (settling) { if (Math.abs(scrollY - settleTo) <= 2) settling = false; return; }
    if (introOn) {
      if (scrollY <= 24) return;
      introOn = false;
      try { localStorage.setItem(INTRO_KEY, '1'); } catch (e) {}
      introMesh.visible = false;
      introMesh.userData.hotspots = [];
      barMesh.visible = true;
      current = 0;
      reframe(0);
    }
    /* Cut only when the reader has actually crossed into the next station.
       The 2% past the midpoint keeps the boundary from flickering when a
       trackpad coasts to a stop right on the line. */
    const s = scrollY / stepPx();
    const cur = current < 0 ? 0 : current;
    if (s - cur > 0.52 || s - cur < -0.52) {
      const i = clamp(Math.round(s), 0, SECTIONS.length - 1);
      if (i !== cur) go(i);
    }
    /* the walk is made of stations, so when the hand stops, land on one */
    clearTimeout(idleT);
    idleT = setTimeout(snapIdle, 150);
  }, { passive: true });

  function snapIdle() {
    if (paused || introOn || settling || down) return;
    const s = scrollY / stepPx();
    const i = clamp(Math.round(s), 0, SECTIONS.length - 1);
    if (Math.abs(scrollY - stationY(i)) <= 2) { if (i !== current) go(i); return; }
    settleToStation(i, true);
  }

  /* A real wheel notch moves exactly one station. Trackpads send many tiny
     deltas — those keep native scrolling (the cut above follows them, the
     idle snap lands them), so a flick never fights the page. */
  let stepT = 0;
  addEventListener('wheel', (e) => {
    if (paused || e.ctrlKey || e.metaKey) return;
    const notch = e.deltaMode === 1 || Math.abs(e.deltaY) >= 50;
    if (!notch) return;
    e.preventDefault();
    const now = performance.now();
    if (now - stepT < 90) return;
    stepT = now;
    clearTimeout(idleT);
    if (introOn) { dismissIntro(false); return; }
    jumpTo(clamp((current < 0 ? 0 : current) + (e.deltaY > 0 ? 1 : -1), 0, SECTIONS.length - 1));
  }, { passive: false });

  /* any gesture cancels a settle that is still in flight */
  addEventListener('wheel', breakSettle, { passive: true, capture: true });
  addEventListener('touchstart', breakSettle, { passive: true, capture: true });
  addEventListener('pointerdown', breakSettle, { passive: true, capture: true });
  addEventListener('keydown', breakSettle, { capture: true });

  addEventListener('keydown', (e) => {
    const tag = (e.target && e.target.tagName) || '';
    if (/INPUT|TEXTAREA|SELECT/.test(tag)) return;
    const i = current < 0 ? 0 : current;
    if (e.key === 'ArrowDown' || e.key === 'PageDown' || e.key === ' ') {
      e.preventDefault();
      if (introOn) { dismissIntro(false); return; }
      const n = clamp(i + 1, 0, SECTIONS.length - 1);
      jumpTo(n);
    } else if (e.key === 'ArrowUp' || e.key === 'PageUp') {
      e.preventDefault();
      if (introOn) { dismissIntro(false); return; }
      const n = clamp(i - 1, 0, SECTIONS.length - 1);
      jumpTo(n);
    } else if (e.key === 'Home') { e.preventDefault(); dismissIntro(false); window.scrollTo(0, 0); go(0); }
    else if (e.key === 'End') { e.preventDefault(); dismissIntro(false); jumpTo(SECTIONS.length - 1); }
    else if (e.key === 'Escape') deselect();
    else if (e.key === 'Enter' && introOn) dismissIntro(false);
  });

  let rz = 0;
  addEventListener('resize', () => {
    clearTimeout(rz);
    rz = setTimeout(() => {
      if (paused) return;
      computeFrameD();
      if (introOn) { const f = heroFrame(); G.cameraPosition(f.pos, f.look, 0); return; }
      reframe(current);
    }, 160);
  });

  /* ── boot: intro or dashboard ─────────────────────────────────── */
  computeFrameD();
  function heroFrame() {
    const aspect = Math.max(0.3, innerWidth / innerHeight);
    const tan = Math.tan(((camera.fov || 42) * Math.PI) / 360);
    const [iw, ih] = DIM.intro;
    /* wide screens pull back a little so the crown of glows reads around the
       card; portrait keeps the card filling the frame */
    const k = narrow ? 1 : 1.3;
    const d = Math.max((ih * 1.22 * k) / (2 * tan), (iw * 1.12 * k) / (2 * tan * aspect));
    return { pos: { x: 0, y: 160 + d * 0.16, z: 280 + d }, look: { x: 0, y: 160, z: 280 } };
  }
  const hero = heroFrame();
  G.cameraPosition(hero.pos, hero.look, 0);
  updateBar(0);
  const seen = (() => { try { return localStorage.getItem(INTRO_KEY) === '1'; } catch (e) { return false; } })();
  const linked = Math.max(0, SECTIONS.indexOf(decodeURIComponent((location.hash || '').slice(1))));
  if (seen || reduce || linked > 0) {
    introMesh.visible = false;
    barMesh.visible = true;
    introOn = false;
    jumpTo(linked);
  } else {
    introOn = true;
    introMesh.visible = true;
    barMesh.visible = false;
    window.scrollTo(0, 0);
  }
  addEventListener('hashchange', () => {
    const i = SECTIONS.indexOf(decodeURIComponent((location.hash || '').slice(1)));
    if (i < 0 || i === current) return;
    if (introOn) {
      introOn = false;
      try { localStorage.setItem(INTRO_KEY, '1'); } catch (e) {}
      introMesh.visible = false;
      barMesh.visible = true;
    }
    jumpTo(i);
  });

  /* ── public API (WebMCP) ──────────────────────────────────────── */
  const api = {
    enter({ section } = {}) {
      if (html.getAttribute('data-onto') !== 'on') {
        html.setAttribute('data-onto', 'on');
        root.style.display = '';
        try { localStorage.setItem(MODE_KEY, 'ontology'); } catch (e) {}
        window.scrollTo(0, 0);
        G.pause(false);
        paused = false;
        go(0, { instant: true });
      }
      if (introOn) { introOn = false; introMesh.visible = false; barMesh.visible = true; go(0, { instant: true }); }
      if (section) {
        const i = SECTIONS.indexOf(section);
        if (i >= 0) jumpTo(i);
      }
      return api.state();
    },
    exit({ section } = {}) { enterReader(section); return api.state(); },
    focus({ target } = {}) {
      const q = norm(target).toLowerCase();
      if (!q) return { ok: false, note: 'target required' };
      let n = NODES.find((x) => x.id === target)
        || NODES.find((x) => `${x.id} ${x.label}`.toLowerCase() === q)
        || NODES.find((x) => `${x.id} ${x.label}`.toLowerCase().includes(q))
        || NODES.find((x) => `${x.desc || ''} ${x.quote || ''}`.toLowerCase().includes(q));
      if (!n) {
        const si = SECTIONS.findIndex((s) => s === q || s.includes(q));
        if (si >= 0) { jumpTo(si); return { ok: true, section: SECTIONS[si], station: si }; }
        return { ok: false, note: `no node or chapter matches "${target}"` };
      }
      if (introOn) { introOn = false; introMesh.visible = false; }
      const si = stationOf(n);
      jumpTo(si);
      select(n);
      return { ok: true, node: n.id, label: n.label, class: n.cls, station: si, section: SECTIONS[si] };
    },
    filter({ mode: m } = {}) { if (m) setMode(m); return api.state(); },
    search({ q } = {}) {
      const s = norm(q).toLowerCase();
      if (!s) return { q: '', count: 0, matches: [] };
      const matches = NODES.filter((n) => `${n.id} ${n.label} ${n.cls} ${n.desc || ''} ${n.quote || ''}`.toLowerCase().includes(s));
      if (matches.length) api.focus({ target: matches[0].id });
      return { q: s, count: matches.length, matches: matches.slice(0, 24).map((n) => ({ id: n.id, label: n.label, cls: n.cls, chapter: n.chapter })) };
    },
    camera({ preset, x, y, z, lookX, lookY, lookZ } = {}) {
      if (preset === 'overview') { G.cameraPosition({ x: 0, y: 620, z: 1350 }, { x: 0, y: 120, z: -900 }, 1100); return true; }
      if (preset) {
        const i = SECTIONS.indexOf(preset);
        if (i >= 0) { jumpTo(i); return true; }
      }
      if (typeof x === 'number' && typeof y === 'number' && typeof z === 'number') {
        G.cameraPosition({ x, y, z }, { x: lookX ?? 0, y: lookY ?? 0, z: lookZ ?? 0 }, 0);
        return true;
      }
      return false;
    },
    pause() { G.pause(true); paused = true; return true; },
    resume() { if (html.getAttribute('data-onto') !== 'on') return false; G.pause(false); paused = false; return true; },
    renderAt({ t } = {}) {
      const n = SECTIONS.length;
      const idx = typeof t === 'number' ? (t <= 1 ? Math.round(t * (n - 1)) : clamp(Math.round(t), 0, n - 1)) : (current < 0 ? 0 : current);
      if (current !== idx) go(idx);
      else reframe(idx);
      G.renderOnce(typeof t === 'number' ? t * 9 + 3 : 6);
      return api.state();
    },
    state() {
      return {
        mode: html.getAttribute('data-onto') === 'on' ? 'ontology' : 'reader',
        section: current < 0 ? 'cover' : SECTIONS[current],
        station: current,
        backend: G.backend,
        nodes: NODES.length,
        relations: LINKS.length,
        selected: selected ? selected.id : null,
        filter: mode,
        intro: introOn,
        paused,
        fps: G.stats().fps
      };
    },
    sections() {
      return sections.map((s) => ({ id: s.id, num: s.num, label: s.label, title: norm(s.title.replace(/<[^>]+>/g, ' ')), station: s.i }));
    },
    nodes() {
      return NODES.map((n) => ({ id: n.id, label: n.label, class: n.cls, chapter: n.chapter, source: n.ref }));
    },
    relations() {
      return LINKS.map((l) => ({ source: l.source, target: l.target, relation: l.rel }));
    },
    stats() { return { ...stats, backend: G.backend, fps: G.stats().fps, drawCalls: G.stats().calls }; }
  };

  /* expose for field debugging without adding DOM */
  window.__onto = { api, graph: G, panels, go, select, setMode, P, NODES };

  inst = { api };
  return api;
}

/* ── copy from the webzine (single source of truth) ─────────────── */
function readSections() {
  return SECTIONS.map((id, i) => {
    const el = document.getElementById(id);
    const num = norm(el?.querySelector('.ch-label .num')?.textContent || (id === 'cover' ? '00' : ''));
    const label = norm(el?.querySelector('.ch-label')?.textContent || '').replace(num, '').trim() || (id === 'cover' ? 'Cover' : id);
    const title = id === 'cover' ? BRAND.coverTitle
      : (el?.querySelector('.ch-title')?.innerHTML || esc(label));
    const deck = id === 'cover'
      ? BRAND.coverDeck
      : norm(el?.querySelector('.ch-deck')?.textContent || '');
    const entities = NODES.filter((n) => n.chapter === id && !n.id.startsWith('ch.') && n.id !== 'phone').slice(0, 8);
    return { id, i, num, label, title: cleanTitle(title), deck, entities };
  });
}

function cleanTitle(s) {
  return String(s || '')
    .replace(/<(?!\/?(?:em|br)\b)[^>]+>/gi, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&#8217;|&rsquo;/g, '’')
    .replace(/&#8216;|&lsquo;/g, '‘')
    .replace(/&#8220;|&ldquo;/g, '“')
    .replace(/&#8221;|&rdquo;/g, '”')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"');
}

/* ── layout: crown of chapters at station 0, one constellation per station ── */
function layoutPositions(sections, narrow) {
  const P = new Map();
  const chapters = SECTIONS.slice(1).map((id) => 'ch.' + id);
  if (narrow) {
    /* tall screen: the card fills the frame, so the crown arcs above it */
    P.set('phone', { x: 0, y: 560, z: -190 });
    chapters.forEach((id, k) => {
      const a = Math.PI * (0.1 + (0.8 * k) / (chapters.length - 1));
      P.set(id, { x: Math.cos(a) * 520, y: 360 + Math.sin(a) * 220, z: -270 - (k % 2) * 80 });
    });
  } else {
    /* wide screen: the crown floats in front of the cover card, so the first
       screen has real depth — big glows, parallax, links running past the
       panel — instead of a card on black. */
    P.set('phone', { x: -420, y: 210, z: 200 });
    chapters.forEach((id, k) => {
      const a = -Math.PI / 2 + (k / chapters.length) * Math.PI * 2;
      P.set(id, {
        x: Math.cos(a) * (k % 2 ? 430 : 385),
        y: 225 + Math.sin(a) * (k % 2 ? 268 : 300),
        z: 205 + (k % 3) * 18
      });
    });
  }
  sections.forEach((s, i) => {
    if (!i) return;
    const z = zOf(i);
    const ents = NODES.filter((n) => n.chapter === s.id && n.id !== 'phone' && !n.id.startsWith('ch.'));
    /* flank the card: two columns of glows, so the page reads as a 3D scene */
    ents.forEach((n, k) => {
      const side = k % 2 ? 1 : -1, row = Math.floor(k / 2);
      P.set(n.id, {
        x: side * (215 + (row % 2) * 45),
        y: 135 - row * 88,
        z: z - 30 - row * 38 + (k % 2) * 16
      });
    });
  });
  NODES.forEach((n) => { if (!P.has(n.id)) P.set(n.id, { x: 0, y: 200, z: -120 }); });
  return P;
}

/* ── reader-mode API (3D not started) ───────────────────────────── */
/* Text mode must never be a one-way door: one visible pill always leads back
   to the WebGPU map. */
function backTo3D() {
  if (document.getElementById('ontoBack')) return;
  const a = document.createElement('a');
  a.id = 'ontoBack';
  a.href = location.pathname + (location.hash || '#cover');
  a.setAttribute('aria-label', 'Open the interactive 3D map');
  a.innerHTML = '<span aria-hidden="true">◈</span> Open the 3D map';
  a.style.cssText =
    'position:fixed;right:16px;bottom:16px;z-index:99999;display:inline-flex;align-items:center;gap:9px;' +
    'padding:13px 19px;border-radius:999px;background:#0a0908;border:1px solid rgba(212,168,75,.6);' +
    'color:#f0c75e;font:600 11px/1 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.16em;' +
    'text-transform:uppercase;text-decoration:none;box-shadow:0 12px 34px rgba(0,0,0,.65)';
  document.body.appendChild(a);
}

function stubApi(sections, html) {
  const state = () => ({
    mode: html.getAttribute('data-onto') === 'on' ? 'ontology' : 'reader',
    section: (location.hash || '#cover').slice(1),
    station: -1, backend: null, nodes: NODES.length, relations: LINKS.length,
    selected: null, filter: 'all', intro: false, paused: true, fps: 0
  });
  backTo3D();
  return {
    enter() {
      try { localStorage.removeItem(MODE_KEY); } catch (e) {}
      location.replace(location.pathname + (location.hash || '#cover'));
      return state();
    },
    exit() { return state(); },
    focus() { return { ok: false, note: 'reader mode — call onto.enter first' }; },
    filter() { return state(); },
    search() { return { q: '', count: 0, matches: [], note: 'reader mode' }; },
    camera() { return false; },
    pause() { return true; },
    resume() { return false; },
    renderAt() { return state(); },
    state,
    sections: () => sections.map((s) => ({ id: s.id, num: s.num, label: s.label, title: norm(s.title.replace(/<[^>]+>/g, ' ')), station: s.i })),
    nodes: () => NODES.map((n) => ({ id: n.id, label: n.label, class: n.cls, chapter: n.chapter, source: n.ref })),
    relations: () => LINKS.map((l) => ({ source: l.source, target: l.target, relation: l.rel })),
    stats: () => ({ ...stats, backend: null, fps: 0 })
  };
}
