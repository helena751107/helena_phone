// LFAI 그래프 런타임 — three.js WebGPURenderer(WebGPU 우선, 안 되면 WebGL2 자동) 위의 자체 지식 그래프 층
// · 노드 = 인스턴싱 스프라이트 1회 그리기 · 관계 = 선분 1회 그리기(정점 셰이더가 노드 위치를 직접 읽음)
// · 배치 · 발화 · 신호 흐름 = WebGPU 컴퓨트(GPU) / WebGL2 폴백은 같은 식을 CPU로
// · 프레임마다 물체 · 버퍼 생성 없음(누수 구조적 차단) — 스타일 변경은 기존 버퍼 갱신만
import * as THREE from "three/webgpu";
import { Fn, instancedArray, instanceIndex, uniform, float, int, vec3, vec4, uint, Loop, If, hash, attribute, uv, smoothstep, mix, max, fract, sin, pass, select } from "three/tsl";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const C = new THREE.Color();
const rgba = (hex, a = 1) => { C.set(hex); return [C.r, C.g, C.b, a]; };

export async function createGraph(container, data, opts = {}) {
  const low = opts.low ?? ((navigator.hardwareConcurrency || 8) <= 4 || (navigator.deviceMemory || 8) <= 4 || matchMedia("(pointer: coarse)").matches);
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const G = {}; // 공개 API 객체(아래에서 채움)
  const forceGL = /[?&]gl=1/.test(location.search) || sessionStorage.getItem("hmc_gl") === "1";
  const renderer = new THREE.WebGPURenderer({ antialias: !low, alpha: false, forceWebGL: forceGL });
  await renderer.init();
  const GPU = !!renderer.backend.isWebGPUBackend;
  // GPU 장치 상실(드라이버 리셋 · 과부하) → 이 세션은 WebGL2 경로로 다시 시작
  if (GPU && renderer.backend.device?.lost) renderer.backend.device.lost.then((info) => { if (info.reason === "destroyed") return; sessionStorage.setItem("hmc_gl", "1"); location.reload(); });
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, low ? 1 : 1.5));
  renderer.setClearColor(0x000000, 1);
  container.append(renderer.domElement);
  const scene = new THREE.Scene(), camera = new THREE.PerspectiveCamera(42, 1, 1, 8000);
  camera.position.set(0, 120, 1100);
  const controls = new OrbitControls(camera, renderer.domElement); controls.enableDamping = true; controls.enableZoom = false; controls.enablePan = false; controls.autoRotate = !reduce; controls.autoRotateSpeed = 0.45;

  // ── 데이터
  const nodes = data.nodes, N = nodes.length, byId = new Map(nodes.map((n, i) => [n.id, i]));
  nodes.forEach((n, i) => (n.__i = i));
  const links = data.links.filter((l) => byId.has(l.source?.id ?? l.source) && byId.has(l.target?.id ?? l.target));
  links.forEach((l) => { l.source = nodes[byId.get(l.source?.id ?? l.source)]; l.target = nodes[byId.get(l.target?.id ?? l.target)]; });
  const E = links.length;
  // 인접(CSR): 배치 인력 · 발화 전파
  const deg = new Uint32Array(N); links.forEach((l) => { deg[l.source.__i]++; deg[l.target.__i]++; });
  const start = new Uint32Array(N); for (let i = 1; i < N; i++) start[i] = start[i - 1] + deg[i - 1];
  const adj = new Uint32Array(E * 2), fillc = new Uint32Array(N);
  links.forEach((l) => { const a = l.source.__i, b = l.target.__i; adj[start[a] + fillc[a]++] = b; adj[start[b] + fillc[b]++] = a; });

  // ── GPU 버퍼 (한 번 만들고 재사용)
  const P0 = new Float32Array(N * 4); nodes.forEach((n, i) => P0.set([n.x ?? (Math.random() - 0.5) * 900, n.y ?? (Math.random() - 0.5) * 600, n.z ?? (Math.random() - 0.5) * 900, 0], i * 4));
  const bPos = instancedArray(P0, "vec4"), bVel = instancedArray(new Float32Array(N * 4), "vec4");
  const aTgt = new Float32Array(N * 4), bTgt = instancedArray(aTgt, "vec4"); // xyz 목표 · w 강도
  const aPin = new Float32Array(N * 2), bPin = instancedArray(aPin, "vec2");  // x 고정 z · y 고정 여부
  const aCol = new Float32Array(N * 4), bCol = instancedArray(aCol, "vec4");  // rgb · a(밝기)
  const aSz = new Float32Array(N * 2), bSz = instancedArray(aSz, "vec2");     // x 크기 · y 위험(붉은 맥동)
  const bFire = instancedArray(new Float32Array(N), "float");
  // 인접 목록은 실수 버퍼로(정수 저장 버퍼 경로의 이식성 문제 회피) — 인덱스는 셰이더에서 int 변환
  const bStart = instancedArray(Float32Array.from(start), "float"), bDeg = instancedArray(Float32Array.from(deg), "float"), bAdj = instancedArray(Float32Array.from(adj), "float");
  const aECol = new Float32Array(E * 4), bECol = instancedArray(aECol, "vec4"); // 관계 rgb · a
  const aEFlow = new Float32Array(E), bEFlow = instancedArray(aEFlow, "float");

  const K = Math.min(N, opts.repSamples || 96);
  const U = { dt: uniform(0.016), alpha: uniform(1), rep: uniform(1400), spring: uniform(0.06), len: uniform(26), damp: uniform(0.86), flat: uniform(0), shapeK: uniform(1), fireRate: uniform(reduce ? 0 : 0.0035), time: uniform(0), kick: uniform(-1) };

  // ── 컴퓨트: 반발(전체 쌍) + 관계 스프링 + 형태 목표 + 2D/시간 고정 + 발화 · 전파
  const step = Fn(() => {
    const i = instanceIndex, p = bPos.element(i).xyz.toVar(), v = bVel.element(i).xyz.toVar(), f = vec3(0).toVar();
    // 반발: 표본 K개(무작위)만 계산하고 N/K로 보정 — O(N·K), 프레임마다 표본이 바뀌어 평균적으로 전체 쌍과 같음
    Loop(K, ({ i: m }) => { const j = hash(i.mul(131).add(m.toUint().mul(7919)).add(U.time.mul(1000.0).toUint())).mul(N).toUint().min(N - 1), d = p.sub(bPos.element(j).xyz), r2 = d.dot(d).add(36); f.addAssign(d.mul(U.rep.mul(N / K).div(r2.mul(r2.sqrt())))); });
    const s0 = bStart.element(i).toInt().toVar(), c = bDeg.element(i).toInt().toVar(), nbFire = float(0).toVar();
    Loop({ start: int(0), end: c, type: "int" }, ({ i: k }) => { const j = bAdj.element(s0.add(k)).toInt(), q = bPos.element(j).xyz, d = q.sub(p), L = d.length().add(0.001);
      f.addAssign(d.div(L).mul(L.sub(U.len).min(240)).mul(U.spring)); nbFire.assign(max(nbFire, bFire.element(j))); });
    const t = bTgt.element(i); f.addAssign(t.xyz.sub(p).mul(t.w).mul(U.shapeK));
    const pin = bPin.element(i), fz = select(pin.y.greaterThan(0.5), pin.x.sub(p.z).mul(0.5), float(0)).sub(p.z.mul(U.flat));
    f.assign(f.add(vec3(0, 0, fz)));
    const fm = f.length(), fc = f.mul(fm.min(60).div(fm.add(0.0001))); // 힘 상한
    const nv0 = v.add(fc.mul(U.alpha)).mul(U.damp), sp = nv0.length(), nv = nv0.mul(sp.min(12).div(sp.add(0.0001))).toVar(); // 속도 상한
    bVel.element(i).assign(vec4(nv, 0)); bPos.element(i).assign(vec4(p.add(nv), 0)); // 고정 간격
    const fr = bFire.element(i).mul(0.9).toVar(), h = hash(i.add(U.time.mul(997.0).toUint()));
    If(h.lessThan(U.fireRate), () => { fr.assign(1); });
    If(nbFire.greaterThan(0.75).and(hash(i.mul(7).add(U.time.mul(613.0).toUint())).lessThan(0.06)), () => { fr.assign(max(fr, 0.85)); });
    If(U.kick.equal(float(i)), () => { fr.assign(1); });
    bFire.element(i).assign(fr);
  })().compute(N);

  // CPU 폴백: 같은 식
  const P = P0, V = new Float32Array(N * 4), F = new Float32Array(N); let kickCPU = -1;
  function stepCPU() {
    const rep = U.rep.value, sp = U.spring.value, len = U.len.value, al = U.alpha.value, dmp = U.damp.value, fl = U.flat.value, k0 = U.shapeK.value;
    for (let i = 0; i < N; i++) {
      const px = P[i * 4], py = P[i * 4 + 1], pz = P[i * 4 + 2]; let fx = 0, fy = 0, fz = 0, nb = 0;
      for (let j = 0; j < N; j++) { const dx = px - P[j * 4], dy = py - P[j * 4 + 1], dz = pz - P[j * 4 + 2], r2 = dx * dx + dy * dy + dz * dz + 36, s = rep / (r2 * Math.sqrt(r2)); fx += dx * s; fy += dy * s; fz += dz * s; }
      for (let k = 0; k < deg[i]; k++) { const j = adj[start[i] + k], dx = P[j * 4] - px, dy = P[j * 4 + 1] - py, dz = P[j * 4 + 2] - pz, L = Math.hypot(dx, dy, dz) + 0.001, s = (Math.min(L - len, 240) * sp) / L; fx += dx * s; fy += dy * s; fz += dz * s; nb = Math.max(nb, F[j]); }
      const w = aTgt[i * 4 + 3] * k0; fx += (aTgt[i * 4] - px) * w; fy += (aTgt[i * 4 + 1] - py) * w; fz += (aTgt[i * 4 + 2] - pz) * w;
      if (aPin[i * 2 + 1] > 0.5) fz += (aPin[i * 2] - pz) * 0.5; fz -= pz * fl;
      const fm = Math.hypot(fx, fy, fz), fs = Math.min(fm, 60) / (fm + 1e-4); fx *= fs; fy *= fs; fz *= fs;
      let vx = (V[i * 4] + fx * al) * dmp, vy = (V[i * 4 + 1] + fy * al) * dmp, vz = (V[i * 4 + 2] + fz * al) * dmp; const vm = Math.hypot(vx, vy, vz), vs = Math.min(vm, 12) / (vm + 1e-4); V[i * 4] = vx * vs; V[i * 4 + 1] = vy * vs; V[i * 4 + 2] = vz * vs;
      let fr = F[i] * 0.9; if (Math.random() < U.fireRate.value) fr = 1; if (nb > 0.75 && Math.random() < 0.06) fr = Math.max(fr, 0.85); if (kickCPU === i) fr = 1; F[i] = fr;
    }
    const m = 1; for (let i = 0; i < N; i++) { P[i * 4] += V[i * 4] * m; P[i * 4 + 1] += V[i * 4 + 1] * m; P[i * 4 + 2] += V[i * 4 + 2] * m; }
    bPos.value.needsUpdate = true; bFire.value.array.set(F); bFire.value.needsUpdate = true; kickCPU = -1;
  }

  // ── 노드: 발광 신경세포체(인스턴싱 스프라이트)
  const nm = new THREE.SpriteNodeMaterial({ transparent: true, depthWrite: false, blending: THREE.AdditiveBlending });
  const fire = bFire.toAttribute(), sz = bSz.toAttribute(), col = bCol.toAttribute();
  const hotPulse = sz.y.mul(sin(U.time.mul(6)).mul(0.35).add(0.9));
  nm.positionNode = bPos.toAttribute().xyz;
  nm.scaleNode = sz.x.mul(fire.mul(1.6).add(1).add(hotPulse));
  const r = uv().sub(0.5).length(), glow = float(1).sub(smoothstep(0.0, 0.5, r)).pow(2.2).add(float(1).sub(smoothstep(0.0, 0.12, r)).mul(0.9));
  nm.colorNode = mix(col.rgb, vec3(1, 0.3, 0.24), sz.y.min(1)).mul(fire.mul(0.9).add(1));
  nm.opacityNode = glow.mul(col.a.add(fire.mul(0.9)).min(1));
  const sprites = new THREE.Sprite(nm); sprites.count = N; sprites.frustumCulled = false; scene.add(sprites);

  // ── 관계: 선분 1회 그리기 · 정점 셰이더가 노드 위치를 읽고, 흐름 = 셰이더 펄스(입자 물체 없음)
  const eg = new THREE.BufferGeometry(), nid = new Float32Array(E * 2), eid = new Float32Array(E * 2), et = new Float32Array(E * 2);
  links.forEach((l, k) => { nid[k * 2] = l.source.__i; nid[k * 2 + 1] = l.target.__i; eid[k * 2] = eid[k * 2 + 1] = k; et[k * 2 + 1] = 1; });
  eg.setAttribute("position", new THREE.BufferAttribute(new Float32Array(E * 6), 3)); eg.setAttribute("nid", new THREE.BufferAttribute(nid, 1)); eg.setAttribute("eid", new THREE.BufferAttribute(eid, 1)); eg.setAttribute("et", new THREE.BufferAttribute(et, 1));
  const lm = new THREE.LineBasicNodeMaterial({ transparent: true, depthWrite: false, blending: THREE.AdditiveBlending });
  const eI = attribute("eid", "float").toUint(), ec = bECol.element(eI), flow = bEFlow.element(eI);
  lm.positionNode = bPos.element(attribute("nid", "float").toUint()).xyz;
  const pulse = flow.mul(smoothstep(0.82, 1.0, fract(attribute("et", "float").sub(U.time.mul(0.55)).add(attribute("eid", "float").mul(0.37)))));
  lm.colorNode = ec.rgb.mul(pulse.mul(3).add(1));
  lm.opacityNode = ec.a.add(pulse.mul(0.8)).min(1);
  const lines = new THREE.LineSegments(eg, lm); lines.frustumCulled = false; scene.add(lines);

  // ── 후처리: 블룸(저사양이면 끔)
  let post = null;
  if (!low) { try { const { bloom } = await import("three/addons/tsl/display/BloomNode.js"); post = new THREE.PostProcessing(renderer); const sp = pass(scene, camera); post.outputNode = sp.add(bloom(sp, 0.75, 0.45, 0.18)); } catch (e) { post = null; } }

  // ── 스타일(접근자) — 바뀔 때만 버퍼 갱신
  const acc = {
    nodeColor: (n) => "#4ff0a8", nodeAlpha: () => 0.9, nodeVal: (n) => n.val || 1, nodeSize: null, nodeHot: () => 0, nodeVisibility: () => true,
    linkColor: () => "#2bd6b0", linkAlpha: () => 0.18, linkWidth: () => 0, linkVisibility: () => true, linkDirectionalParticles: () => 0, nodeLabel: (n) => n.label || n.id,
  };
  function restyle() {
    nodes.forEach((n, i) => { const vis = acc.nodeVisibility(n) ? 1 : 0, [r_, g_, b_] = rgba(acc.nodeColor(n)); aCol.set([r_, g_, b_, acc.nodeAlpha(n) * vis], i * 4);
      aSz[i * 2] = vis * (acc.nodeSize ? acc.nodeSize(n) : 3.2 + Math.sqrt(acc.nodeVal(n)) * 3.6); aSz[i * 2 + 1] = vis * (acc.nodeHot(n) ? 1 : 0); });
    links.forEach((l, k) => { const vis = acc.linkVisibility(l) && acc.nodeVisibility(l.source) && acc.nodeVisibility(l.target) ? 1 : 0, w = acc.linkWidth(l) || 0, [r_, g_, b_] = rgba(acc.linkColor(l));
      aECol.set([r_, g_, b_, vis * Math.min(1, acc.linkAlpha(l) + w * 0.25)], k * 4); aEFlow[k] = vis * Math.min(1, (acc.linkDirectionalParticles(l) || 0) / 3); });
    bCol.value.array.set(aCol); bCol.value.needsUpdate = true; bSz.value.array.set(aSz); bSz.value.needsUpdate = true;
    bECol.value.array.set(aECol); bECol.value.needsUpdate = true; bEFlow.value.array.set(aEFlow); bEFlow.value.needsUpdate = true;
  }
  function targets() { nodes.forEach((n, i) => { const t = G._target ? G._target(n) : null; if (t) aTgt.set([t[0], t[1], t[2], t[3] ?? 0.09], i * 4); else aTgt[i * 4 + 3] = 0;
      if (n.fz !== undefined && n.fz !== null) { aPin[i * 2] = n.fz; aPin[i * 2 + 1] = 1; } else aPin[i * 2 + 1] = 0; });
    bTgt.value.array.set(aTgt); bTgt.value.needsUpdate = true; bPin.value.array.set(aPin); bPin.value.needsUpdate = true; }

  // ── CPU 미러(피킹 · 화면 맞춤 · 카메라 이동용): GPU 경로는 주기적으로 읽어 옴
  let reading = false, lastRead = 0;
  async function mirror(now) {
    if (!GPU) { nodes.forEach((n, i) => { n.x = P[i * 4]; n.y = P[i * 4 + 1]; n.z = P[i * 4 + 2]; }); return; }
    if (reading || now - lastRead < 350) return; reading = true; lastRead = now;
    try { const buf = new Float32Array(await renderer.getArrayBufferAsync(bPos.value)); nodes.forEach((n, i) => { n.x = buf[i * 4]; n.y = buf[i * 4 + 1]; n.z = buf[i * 4 + 2]; }); } catch (e) {} reading = false;
  }

  // ── 피킹 · 툴팁
  const tip = document.createElement("div"); tip.className = "scene-tooltip"; Object.assign(tip.style, { position: "fixed", pointerEvents: "none", zIndex: 40, display: "none", maxWidth: "280px" }); document.body.append(tip);
  const V3 = new THREE.Vector3();
  function pick(cx, cy, rad = 14) { let best = null, bd = rad * rad; const w2 = innerWidth / 2, h2 = innerHeight / 2;
    for (const n of nodes) { if (!acc.nodeVisibility(n)) continue; V3.set(n.x, n.y, n.z).project(camera); if (V3.z > 1) continue; const dx = (V3.x + 1) * w2 - cx, dy = (1 - V3.y) * h2 - cy, d = dx * dx + dy * dy; if (d < bd) { bd = d; best = n; } }
    return best; }
  let hoverT = 0, onClick = null, onBg = null, onHover = null, downAt = null;
  renderer.domElement.addEventListener("pointermove", (e) => { const now = performance.now(); if (now - hoverT < 70) return; hoverT = now; const n = pick(e.clientX, e.clientY);
    renderer.domElement.style.cursor = n ? "pointer" : ""; if (n) { tip.innerHTML = acc.nodeLabel(n); tip.style.left = Math.min(innerWidth - 290, e.clientX + 14) + "px"; tip.style.top = e.clientY + 14 + "px"; tip.style.display = "block"; } else tip.style.display = "none"; onHover && onHover(n); });
  renderer.domElement.addEventListener("pointerleave", () => (tip.style.display = "none"));
  renderer.domElement.addEventListener("pointerdown", (e) => (downAt = [e.clientX, e.clientY]));
  renderer.domElement.addEventListener("pointerup", (e) => { if (!downAt || Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1]) > 6) return; const n = pick(e.clientX, e.clientY, 18); n ? onClick && onClick(n, e) : onBg && onBg(e); });

  // ── 카메라 트윈 · 화면 맞춤
  let tw = null;
  function cameraPosition(pos, look, ms = 1000) { if (!pos) return camera.position; const from = camera.position.clone(), ft = controls.target.clone(), to = new THREE.Vector3(pos.x, pos.y, pos.z), tt = look ? new THREE.Vector3(look.x, look.y, look.z) : ft.clone();
    if (!ms) { tw = null; camera.position.copy(to); controls.target.copy(tt); controls.update(); return G; } tw = { from, ft, to, tt, t0: performance.now(), ms }; return G; }
  function zoomToFit(ms = 1000, pad = 40, filter = () => true) { const pts = nodes.filter((n) => acc.nodeVisibility(n) && filter(n)); if (!pts.length) return G;
    const c = new THREE.Vector3(); pts.forEach((n) => c.add(V3.set(n.x, n.y, n.z))); c.divideScalar(pts.length); let r = 0; pts.forEach((n) => (r = Math.max(r, V3.set(n.x, n.y, n.z).distanceTo(c))));
    const dir = camera.position.clone().sub(controls.target).normalize(), dist = (r + pad) / Math.sin(THREE.MathUtils.degToRad(camera.fov / 2)) * (camera.aspect < 1 ? 1.25 : 0.85);
    return cameraPosition(c.clone().add(dir.multiplyScalar(dist)), c, ms); }

  // ── 루프
  let last = performance.now(), frames = 0, fps = 0, ft = last, simT = 0;
  function frame() {
    const now = performance.now(), dt = Math.min(0.05, (now - last) / 1000); last = now;
    if (tw) { const k = Math.min(1, (now - tw.t0) / tw.ms), e = k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2; camera.position.lerpVectors(tw.from, tw.to, e); controls.target.lerpVectors(tw.ft, tw.tt, e); if (k >= 1) tw = null; }
    controls.update();
    U.dt.value = dt; U.time.value = now / 1000; simT += dt; U.alpha.value = Math.max(0.04, U.alpha.value * 0.992);
    if (GPU) { renderer.compute(step); U.kick.value = -1; } else stepCPU();
    mirror(now);
    post ? post.render() : renderer.render(scene, camera);
    frames++; if (now - ft > 1000) { fps = Math.round((frames * 1000) / (now - ft)); frames = 0; ft = now; }
  }
  const size = () => { renderer.setSize(innerWidth, innerHeight); camera.aspect = innerWidth / innerHeight; camera.fov = camera.aspect < 0.85 ? 56 : 42; camera.updateProjectionMatrix(); G._offset && G._offset(); };
  addEventListener("resize", size); size();
  const run = () => renderer.setAnimationLoop(document.hidden ? null : frame);
  document.addEventListener("visibilitychange", run); run();

  // ── 공개 API (3d-force-graph 호환 부분집합 + 확장)
  const chain = (k) => function (f) { if (f === undefined) return acc[k]; acc[k] = typeof f === "function" ? f : () => f; restyle(); return G; };
  Object.assign(G, {
    backend: GPU ? "WebGPU" : "WebGL2", low, U,
    nodeColor: chain("nodeColor"), nodeAlpha: chain("nodeAlpha"), nodeVal: chain("nodeVal"), nodeHot: chain("nodeHot"), nodeSize: chain("nodeSize"), nodeVisibility: chain("nodeVisibility"), nodeLabel: chain("nodeLabel"),
    linkColor: chain("linkColor"), linkAlpha: chain("linkAlpha"), linkWidth: chain("linkWidth"), linkVisibility: chain("linkVisibility"), linkDirectionalParticles: chain("linkDirectionalParticles"),
    onNodeClick(f) { if (f === undefined) return onClick; onClick = f; return G; }, onBackgroundClick(f) { if (f === undefined) return onBg; onBg = f; return G; }, onNodeHover(f) { onHover = f; return G; },
    graphData: () => ({ nodes, links }), camera: () => camera, controls: () => controls, renderer: () => renderer, scene: () => scene,
    cameraPosition, zoomToFit,
    setTargets(fn) { G._target = fn; targets(); U.alpha.value = 1; return G; }, refreshTargets() { targets(); return G; },
    d3ReheatSimulation() { targets(); U.alpha.value = 1; return G; },
    numDimensions(d) { U.flat.value = d === 2 ? 0.6 : 0; U.alpha.value = 1; return G; },
    fire(n) { if (GPU) U.kick.value = n.__i; else kickCPU = n.__i; return G; },
    restyle() { restyle(); return G; },
    async snapshot() { post ? post.render() : renderer.render(scene, camera); return await new Promise((res) => renderer.domElement.toBlob(res)); },
    stats() { let objs = 0; scene.traverse(() => objs++); return { backend: G.backend, fps, nodes: N, links: E, objects: objs, geometries: renderer.info.memory?.geometries, textures: renderer.info.memory?.textures, calls: renderer.info.render?.drawCalls ?? renderer.info.render?.calls }; },
    width() { return G; }, height() { return G; },
    async read(name, n = 12) { const b = { pos: bPos, vel: bVel, fire: bFire, deg: bDeg, start: bStart, tgt: bTgt }[name]; return GPU ? Array.from(new (Float32Array)(await renderer.getArrayBufferAsync(b.value))).slice(0, n) : Array.from(b.value.array).slice(0, n); },
    pause(on) { renderer.setAnimationLoop(on ? null : frame); }, stepOnce() { renderer.compute(step); },
    renderOnce(t) { U.time.value = t ?? performance.now() / 1000; controls.update(); if (GPU) renderer.compute(step); else stepCPU(); post ? post.render() : renderer.render(scene, camera); },
  });
  restyle(); targets();
  return G;
}
