/* Explainer engine: everything on screen is a PURE FUNCTION OF TIME t (seek-safe, deterministic, no random at runtime).
   Layers: #glow (css) < canvas#fx (particles, wireframes, links, packets) < #stage (DOM cards/chips/labels) < HUD (brand, rail, kicker, caption).
   GSAP is only the clock: one paused tween whose onUpdate calls render(t). Data comes from window.EXPLAINER (written by build_explainer.py). */
(async function () {
  const D = window.EXPLAINER, M = D.meta, W = 1080, H = 1920, CY = 900, F = 1900;
  const $ = (s, p) => (p || document).querySelector(s), mk = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };
  const cl = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x)), lerp = (a, b, k) => a + (b - a) * k;
  const eo3 = u => 1 - Math.pow(1 - cl(u), 3), eio3 = u => { u = cl(u); return u < .5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2; };
  const eoB = u => { u = cl(u); const c = 1.70158; return 1 + (c + 1) * Math.pow(u - 1, 3) + c * Math.pow(u - 1, 2); };
  const rng = s => { let a = s >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; };
  const hash = s => { let h = 2166136261; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; };
  const TONE = { white: [244, 244, 245], red: [255, 77, 94], blue: [90, 169, 255], yellow: [255, 210, 63], green: [74, 222, 128], violet: [167, 139, 250], dim: [154, 154, 160] };
  const W0 = M.world_def || null;                                     // a "world" (assets/worlds.json): palette, background, caption style, overlay, motion strength
  if (W0) {
    const hx = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16)), R = document.documentElement.style, root = document.getElementById("root");
    Object.keys(W0.tones).forEach(k => { TONE[k] = hx(W0.tones[k]); R.setProperty("--" + k, W0.tones[k]); }); R.setProperty("--bg", W0.bg); R.setProperty("--ink", W0.tones.white); R.setProperty("--glowc", W0.glow);
    root.classList.add("w-" + M.world, "cap-" + W0.caption, "ov-" + W0.overlay); document.body.style.background = W0.bg;
  }
  const rgba = (tone, a) => { const c = TONE[tone] || TONE.white; return `rgba(${c[0]},${c[1]},${c[2]},${a})`; };
  const indian = n => { n = Math.round(n); let s = String(Math.abs(n)); if (s.length > 3) { const l = s.slice(-3); let r = s.slice(0, -3).replace(/\B(?=(\d{2})+(?!\d))/g, ","); s = r + "," + l; } return (n < 0 ? "-" : "") + s; };
  const fmtNum = (n, f) => f === "indian" ? indian(n) : f === "plain" ? String(Math.round(n)) : f === "k" ? (n / 1000).toFixed(1) + "K" : f === "pct" ? Math.round(n) + "%" : Math.round(n).toLocaleString("en-US");
  const trunc = (html, n) => { let out = "", stack = [], i = 0; while (i < html.length && n > 0) { if (html[i] === "<") { const j = html.indexOf(">", i), tag = html.slice(i, j + 1); out += tag; if (tag[1] === "/") stack.pop(); else stack.push(tag.match(/^<(\w+)/)[1]); i = j + 1; } else if (html[i] === "&") { const j = html.indexOf(";", i); out += html.slice(i, j + 1); i = j + 1; n--; } else { out += html[i++]; n--; } } return out + stack.reverse().map(t => `</${t}>`).join(""); };
  const plainLen = html => html.replace(/<[^>]*>/g, "").replace(/&\w+;/g, "x").length;
  const mark = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/\{(r|g|b|bl|gr|y):([^}]*)\}/g, '<span class="$1">$2</span>').replace(/\*([^*]+)\*/g, "<b>$1</b>");

  await Promise.all(['800 120px "Hanken Grotesk"', '500 24px "JetBrains Mono"', 'italic 40px "Instrument Serif"'].map(f => document.fonts.load(f))); await document.fonts.ready;

  /* ---------- scenes, header, caption ---------- */
  const S = D.scenes, T = D.total, FX = Object.assign({ trans: [], punches: [], shocks: [] }, D.fx || {}), BEATS = D.beats || [], OS = M.objScale || 1.3, DRIFT = M.drift == null ? (M.world_def ? M.world_def.drift : .04) : M.drift;
  const WHIPS = FX.trans.filter(x => x.type === "whip_h" || x.type === "whip_v").map(x => x.t);
  const bp = t => { let b = -1, k = -1; for (let i = 0; i < BEATS.length && BEATS[i] <= t; i++) { b = BEATS[i]; k = i; } return b < 0 ? 0 : Math.exp(-(t - b) * 9) * (k % 4 === 0 ? 1 : .55); };
  /* camera: scene drift + opening snap + punches (0.09 s up, 0.55 s settle) + handheld shake + whip / blur-in / push transitions */
  function camAt(t) {
    const i = sceneAt(t), sc = S[i], su = cl((t - sc.from) / Math.max(.1, sc.to - sc.from)), dir = i % 2 ? 1 : -1;
    let s = 1 + DRIFT * eio3(su), x = dir * 34 * (su - .5), y = -14 * (su - .5), blur = 0, hx = 0, hy = 0;
    if (t < .6) s *= 1 + .16 * (1 - eo3(t / .55));
    FX.punches.forEach(p => { const dt = t - p.t; if (dt > -.02 && dt < .7) { const k = dt < .09 ? eo3(Math.max(0, dt) / .09) : 1 - eio3((dt - .09) / .55); s *= 1 + p.amt * k; if (p.shake && dt < .35) { const a = 1 - dt / .35; x += Math.sin(t * 83) * 9 * a; y += Math.cos(t * 71) * 7 * a; } } });
    FX.trans.forEach(tr => {
      const dt = t - tr.t, d = tr.dir || 1;
      if (tr.type === "whip_h" || tr.type === "whip_v") {
        let off = 0, b = 0; if (dt > -.14 && dt <= 0) { const u = (dt + .14) / .14; off = -d * Math.pow(u, 2.2); b = u; } else if (dt > 0 && dt < .3) { const u = dt / .3; off = d * .9 * (1 - eo3(u)); b = 1 - u; }
        if (off || b) { if (tr.type === "whip_h") { x += off * W; hx = Math.max(hx, 30 * b); } else { y += off * H * .6; hy = Math.max(hy, 30 * b); } }
      } else if (tr.type === "blur_in") { if (dt >= 0 && dt < .5) { const u = eo3(dt / .5); blur = Math.max(blur, 16 * (1 - u)); s *= 1 + .07 * (1 - u); } }
      else if (tr.type === "push") { if (dt > -.2 && dt <= 0) { const u = (dt + .2) / .2; s *= 1 + .22 * u * u; blur = Math.max(blur, 14 * u); } else if (dt > 0 && dt < .45) { const u = eo3(dt / .45); s *= .88 + .12 * u; blur = Math.max(blur, 12 * (1 - u)); } }
    });
    const pu = bp(t); s *= 1 + .005 * pu;
    return { s, x, y, blur, hx, hy, pu };
  }
  const sceneAt = t => { let k = 0; for (let i = 0; i < S.length; i++) if (t >= S[i].from) k = i; return k; };
  document.documentElement.style.setProperty("--accent", rgba(M.accent || "white", 1));
  const hud = $("#hud"); $("#brand").textContent = M.handle; $("#series").textContent = M.series;
  const rail = $("#rail"), fill = $("#fill"), ticks = S.map(s => { const k = mk("i", "tick"); k.style.left = (972 * s.from / T) + "px"; rail.appendChild(k); return k; });
  const kick = $("#kicker"), cap = $("#cap");
  S.forEach(s => {
    s.node = mk("div", "cap-s"); s.node.style.cssText = "position:absolute;left:0;right:0;top:0;opacity:0";
    s.wn = s.words.map(w => { const sp = mk("span", "w" + (w.key ? " k" : "") + (w.serif ? " s" : "") + (w.c1 ? " c1" : ""), w.txt.replace(/&/g, "&amp;").replace(/</g, "&lt;")); s.node.appendChild(sp); s.node.appendChild(document.createTextNode(" ")); return sp; });
    cap.appendChild(s.node);
  });
  cap.style.height = "220px"; cap.style.position = "absolute";

  /* ---------- particles ---------- */
  const N = M.particles || 4200, SEED = M.seed || 7;
  const TX = document.createElement("canvas"); TX.width = 1000; TX.height = 520; const tx = TX.getContext("2d", { willReadFrequently: true });
  function rasterPoints(drawFn, scale) {
    tx.clearRect(0, 0, 1000, 520); tx.fillStyle = "#fff"; tx.strokeStyle = "#fff"; drawFn(tx);
    const d = tx.getImageData(0, 0, 1000, 520).data, pts = []; let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
    for (let y = 0; y < 520; y += 3) for (let x = 0; x < 1000; x += 3) if (d[(y * 1000 + x) * 4 + 3] > 128) { pts.push([x, y]); x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); }
    const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2, k = scale / Math.max(1, x1 - x0); return pts.map(p => [(p[0] - cx) * k, (p[1] - cy) * k]);
  }
  function shape(h) {
    const R = rng(SEED ^ hash(JSON.stringify(h))), a = new Float32Array(N * 3), r = h.r || 240, k = h.shape, set = (i, x, y, z) => { a[i * 3] = x; a[i * 3 + 1] = y; a[i * 3 + 2] = z; };
    if (k === "text" || k === "path") {
      const lines = String(h.value || "").split("\n"), sz = h.size || 200;
      const pts = rasterPoints(c => { if (k === "text") { c.font = `800 ${sz}px "Hanken Grotesk"`; c.textAlign = "center"; c.textBaseline = "middle"; lines.forEach((l, j) => c.fillText(l, 500, 260 + (j - (lines.length - 1) / 2) * sz * 1.05)); } else { c.translate(500 - 50 * 4, 260 - 50 * 4); c.scale(4, 4); c.lineWidth = 3; c.stroke(new Path2D(h.d)); } }, r * 2);
      for (let i = 0; i < N; i++) { const p = pts[Math.floor(R() * pts.length)] || [0, 0]; set(i, p[0] + (R() - .5) * 2, p[1] + (R() - .5) * 2, (R() - .5) * 10); }
    } else for (let i = 0; i < N; i++) {
      let x = 0, y = 0, z = 0; const u = R() * Math.PI * 2, v = R(), w = R();
      if (k === "sphere") { if (h.rings !== false && w < .62) { const K = 13, ri = Math.floor(R() * K), lat = (-78 + 156 * ri / (K - 1)) * Math.PI / 180; x = r * Math.cos(lat) * Math.cos(u); y = r * Math.sin(lat); z = r * Math.cos(lat) * Math.sin(u); } else { const ph = Math.acos(1 - 2 * v); x = r * Math.sin(ph) * Math.cos(u); y = r * Math.cos(ph); z = r * Math.sin(ph) * Math.sin(u); } }
      else if (k === "globe") { if (w < .5) { const m = Math.floor(R() * 12) * Math.PI / 6, t = (R() - .5) * Math.PI; x = r * Math.cos(t) * Math.cos(m); y = r * Math.sin(t); z = r * Math.cos(t) * Math.sin(m); } else { const lat = (Math.floor(R() * 9) - 4) * Math.PI / 9.5; x = r * Math.cos(lat) * Math.cos(u); y = r * Math.sin(lat); z = r * Math.cos(lat) * Math.sin(u); } }
      else if (k === "torus") { const q = R() * Math.PI * 2, tr = r * .3; x = (r + tr * Math.cos(q)) * Math.cos(u); z = (r + tr * Math.cos(q)) * Math.sin(u); y = tr * Math.sin(q); }
      else if (k === "ring") { x = r * Math.cos(u); z = r * Math.sin(u); y = (R() - .5) * 8; }
      else if (k === "line") { x = (R() - .5) * 14; y = (v - .5) * r * 2; z = (R() - .5) * 14; }
      else if (k === "grid") { const c = 36, gx = Math.floor(R() * c), gz = Math.floor(R() * 26); x = (gx / (c - 1) - .5) * r * 2; z = (gz / 25 - .5) * r * 1.5; y = 0; }
      else if (k === "cylinder") { const hh = h.h || r * 1.3; if (w < .3) { const q = Math.sqrt(R()) * r; x = q * Math.cos(u); z = q * Math.sin(u) * .5; y = -hh / 2; } else if (w < .45) { x = r * Math.cos(u); z = r * Math.sin(u) * .5; y = hh / 2; } else { x = r * Math.cos(u); z = r * Math.sin(u) * .5; y = (R() - .5) * hh; } }
      else if (k === "cube") { const f = Math.floor(R() * 3), s = (R() < .5 ? -1 : 1) * r * .7, p = (R() * 2 - 1) * r * .7, q = (R() * 2 - 1) * r * .7; if (f === 0) { x = s; y = p; z = q; } else if (f === 1) { x = p; y = s; z = q; } else { x = p; y = q; z = s; } }
      else if (k === "phone") { const pw = r * .8, ph2 = r * 1.7; if (w < .4) { const e = R() * 2 * (pw + ph2); let q = e; if (q < pw) { x = -pw / 2 + q; y = -ph2 / 2; } else if ((q -= pw) < ph2) { x = pw / 2; y = -ph2 / 2 + q; } else if ((q -= ph2) < pw) { x = pw / 2 - q; y = ph2 / 2; } else { q -= pw; x = -pw / 2; y = ph2 / 2 - q; } } else { x = (Math.floor(R() * 12) / 11 - .5) * pw * .84; y = (Math.floor(R() * 20) / 19 - .5) * ph2 * .86; } z = 0; }
      else { const g = () => Math.sqrt(-2 * Math.log(R() + 1e-9)) * Math.cos(R() * 6.283); x = g() * r * .42; y = g() * r * .34; z = g() * r * .42; } /* cloud / scatter */
      set(i, x, y, z);
    }
    return a;
  }
  const dir = new Float32Array(N * 3), ph = new Float32Array(N), Rd = rng(SEED + 1);
  for (let i = 0; i < N; i++) { const u = Rd() * 6.283, v = Rd() * 2 - 1, s = Math.sqrt(1 - v * v), m = .35 + Rd() * 1.1; dir[i * 3] = s * Math.cos(u) * m; dir[i * 3 + 1] = v * m; dir[i * 3 + 2] = s * Math.sin(u) * m; ph[i] = Rd() * 6.283; }
  let prevT = shape({ shape: "cloud", r: 420 }), prevH = { alpha: 0, spin: 0, tilt: 0, y: 0, r: 240, size: 1 };
  S.forEach((s, i) => { const h = s.hero; if (h) { s.T = shape(h); s.hp = { alpha: h.alpha == null ? 1 : h.alpha, spin: h.spin == null ? .35 : h.spin, tilt: h.tilt == null ? .18 : h.tilt, y: h.y || 0, size: h.shape === "text" ? 1 : (h.size || 1), tone: h.tone || "white" }; } else { s.T = prevT; s.hp = Object.assign({}, prevH, { alpha: 0 }); } prevT = s.T; prevH = s.hp; });
  const dust = (() => { const R = rng(SEED + 5), a = []; for (let i = 0; i < 70; i++) a.push([R() * W, 160 + R() * 1400, R() * 6.28, .5 + R() * .9]); return a; })();

  /* ---------- elements: windows + keyframes (resolved by the builder) ---------- */
  const EL = D.els, byId = {}; EL.forEach(e => byId[e.id] = e);
  function prop(e, t) { // interpolated numeric props between scene keyframes, instant for the rest
    const fr = e.frames; let k = 0; for (let i = 0; i < fr.length; i++) if (t >= fr[i].t) k = i; const c = fr[k], p = fr[Math.max(0, k - 1)], u = eio3((t - c.t) / .7), o = {};
    for (const key in c) o[key] = (typeof c[key] === "number" && typeof p[key] === "number" && key !== "t") ? lerp(p[key], c[key], u) : c[key]; return o;
  }
  function win(e, t) { for (let i = 0; i < e.wins.length; i++) { const [a, b] = e.wins[i], at = e.ats[i]; if (t >= at - .001 && t <= b + .35) { const inn = eo3((t - at) / .42), od = WHIPS.some(w => Math.abs(w - b) < .02) ? .06 : .3, out = 1 - cl((t - b) / od); return { a: inn * out, p: cl((t - at) / .75), t0: at, live: t <= b }; } } return null; }
  const stage = $("#stage");
  EL.forEach(e => { // build DOM for every non-canvas element
    if (e.type === "link" || e.type === "cells" || (e.type === "packet" && !e.label) || (e.type === "obj" && !e.label && !e.sub)) return;
    const f = e.frames[0]; let n;
    if (e.type === "obj") { n = mk("div", "lbl", `<div class="t">${mark(e.label || "")}</div>${e.sub ? `<div class="s" data-layout-ignore>${mark(e.sub)}</div>` : ""}`); }
    else if (e.type === "chip" || e.type === "packet") { n = mk("div", "", `<span class="chip ${e.tone || ""}">${mark(e.text || e.label || "")}</span>`); }
    else if (e.type === "card") { n = mk("div", "card " + (e.tone || ""), (e.title ? `<div class="h" data-layout-ignore>${mark(e.title)}</div>` : "") + `<div class="ln"></div>`); n.style.width = (f.w || 820) + "px"; }
    else if (e.type === "big") { n = mk("div", "big", mark(e.text).replace(/<b>/g, "<i>").replace(/<\/b>/g, "</i>") + (e.sub ? `<span class="sub">${mark(e.sub)}</span>` : "")); }
    else if (e.type === "counter") { n = mk("div", "counter " + (e.tone || ""), `<div class="l" data-layout-ignore>${mark(e.label || "")}</div><div class="n"></div>`); }
    else if (e.type === "list") { n = mk("div", "list", `<div class="rail"></div>` + e.items.map((t2, i) => `<div class="it"><span class="nu" data-layout-ignore>${String(i + 1).padStart(2, "0")}</span><span class="pill">${mark(t2)}</span></div>`).join("")); n.style.width = (f.w || 760) + "px"; }
    else if (e.type === "compare") { n = mk("div", "", ""); n.style.cssText = `display:flex;gap:24px;width:${f.w || 900}px`; e.cards.forEach(c => { const k = mk("div", "card " + (c.tone || ""), `<div class="h" data-layout-ignore>${mark(c.title || "")}</div><div class="ln">${(c.lines || []).map(mark).join("\n")}</div>`); k.style.flex = "1"; n.appendChild(k); }); }
    else if (e.type === "cta") { n = mk("div", "", `<div class="bubble">${mark(e.text || "Comment in\nthis reel").replace(/\n/g, "<br>")}</div><div class="cta-sub" data-layout-ignore>${mark(e.sub || "")}</div>`); n.style.width = "560px"; }
    else if (e.type === "note") { n = mk("div", "note", mark(e.text)); n.setAttribute("data-layout-ignore", ""); }
    else if (e.type === "stamp") { n = mk("div", "", `<span class="stamp ${e.tone === "red" || !e.tone ? "" : e.tone}">${mark(e.text)}</span>`); }
    else if (e.type === "search") { n = mk("div", "search", `<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#9a9aa0" stroke-width="1.6"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"/></svg><span class="tt"></span><span class="en">ENTER ↵</span>`); n.style.width = (f.w || 880) + "px"; }
    else if (e.type === "bars") { n = mk("div", "bars", e.values.map(() => "<i></i>").join("")); }
    else return;
    n.classList.add("el"); stage.appendChild(n); e.node = n;
  });
  EL.forEach(e => { if (e.node) { e.w = e.node.offsetWidth; e.h = e.node.offsetHeight; } });

  /* ---------- canvas drawing ---------- */
  const cv = $("#fx"), ctx = cv.getContext("2d");
  const rot = (x, y, z, ry, rx) => { let c = Math.cos(ry), s = Math.sin(ry), X = x * c + z * s, Z = -x * s + z * c; c = Math.cos(rx); s = Math.sin(rx); const Y = y * c - Z * s; Z = y * s + Z * c; return [X, Y, Z]; };
  const proj = (x, y, z, cx, cy) => { const s = F / (F + z); return [cx + x * s, cy + y * s, s]; };
  const boxEdges = (w, h, d) => { const x = w / 2, y = h / 2, z = d / 2, v = [[-x, -y, -z], [x, -y, -z], [x, y, -z], [-x, y, -z], [-x, -y, z], [x, -y, z], [x, y, z], [-x, y, z]]; return [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4], [0, 4], [1, 5], [2, 6], [3, 7]].map(([a, b]) => [v[a], v[b]]); };
  const loop = (cx, cy, cz, rx, rz, n, plane) => { const o = []; for (let i = 0; i < n; i++) { const a = i / n * 6.2832, b = (i + 1) / n * 6.2832; o.push([[cx + rx * Math.cos(a), cy, cz + rz * Math.sin(a)], [cx + rx * Math.cos(b), cy, cz + rz * Math.sin(b)]]); } return o; };
  function objEdges(e, f) {
    const k = e.kind, w = (f.w3 || 150) * OS, h = (f.h3 || 110) * OS, d = (f.d3 || 110) * OS;
    if (k === "box" || k === "cube") return boxEdges(w, h, d);
    if (k === "rack") { const n = e.units || 3, uh = h / n - 8; let o = []; for (let i = 0; i < n; i++) boxEdges(w, uh, d).forEach(([a, b]) => o.push([[a[0], a[1] + (i - (n - 1) / 2) * (uh + 8), a[2]], [b[0], b[1] + (i - (n - 1) / 2) * (uh + 8), b[2]]])); return o; }
    if (k === "db") { const r = w / 2, hh = h, o = [...loop(0, -hh / 2, 0, r, r * .45, 28), ...loop(0, hh / 2, 0, r, r * .45, 28), ...loop(0, -hh / 6, 0, r, r * .45, 28), ...loop(0, hh / 6, 0, r, r * .45, 28)]; o.push([[-r, -hh / 2, 0], [-r, hh / 2, 0]], [[r, -hh / 2, 0], [r, hh / 2, 0]]); return o; }
    if (k === "browser") { const o = boxEdges(w, h, 12); o.push([[-w / 2, -h / 2 + 22, -6], [w / 2, -h / 2 + 22, -6]]); for (let i = 0; i < 3; i++) o.push([[-w / 2 + 10 + i * 12, -h / 2 + 11, -6], [-w / 2 + 12 + i * 12, -h / 2 + 11, -6]]); for (let i = 0; i < 3; i++) o.push([[-w / 2 + 14, -h / 2 + 44 + i * 16, -6], [w / 2 - 14 - (i % 2) * 40, -h / 2 + 44 + i * 16, -6]]); return o; }
    if (k === "phone") { const o = boxEdges(w * .55, h * 1.3, 10); o.push([[-w * .1, -h * .6, -5], [w * .1, -h * .6, -5]]); return o; }
    if (k === "globe") { const r = w / 2; let o = [...loop(0, 0, 0, r, r, 36)]; for (let i = -2; i <= 2; i++) { const y = i * r * .35, rr = Math.sqrt(Math.max(0, r * r - y * y)); o.push(...loop(0, y, 0, rr, rr, 30)); } for (let m = 0; m < 4; m++) { const a = m * Math.PI / 4; for (let j = 0; j < 24; j++) { const t1 = j / 24 * 6.2832, t2 = (j + 1) / 24 * 6.2832, P = t => [r * Math.cos(t) * Math.cos(a), r * Math.sin(t), r * Math.cos(t) * Math.sin(a)]; o.push([P(t1), P(t2)]); } } return o; }
    return boxEdges(w, h, d);
  }
  const ctr = (e, t) => { const p = prop(e, t); return [p.x, p.y, p]; };
  function drawObj(e, t, wv) {
    const [x0, y0, f] = ctr(e, t), x = x0, y = y0 + Math.sin(t * 1.4 + e.id.length * 1.7) * 5, ry = (f.ry == null ? -.5 : f.ry) + Math.sin(t * .5 + e.id.length) * .05, rx = f.rx == null ? .42 : f.rx, sc = f.sc == null ? 1 : f.sc;
    const edges = objEdges(e, f), tone = f.tone || "white", act = f.active || 0, al = wv.a * (f.alpha == null ? 1 : f.alpha), pg = wv.p;
    if (act > .02) { const g = ctx.createRadialGradient(x, y, 10, x, y, 250 * sc); g.addColorStop(0, rgba(tone, .3 * act * al)); g.addColorStop(1, rgba(tone, 0)); ctx.fillStyle = g; ctx.fillRect(x - 300, y - 300, 600, 600); }
    ctx.lineWidth = 1.7; ctx.lineCap = "round"; const nE = edges.length;
    edges.forEach((ed, i) => {
      const q = cl(pg * 1.6 - i / nE * .6); if (q <= 0) return;
      const a = rot(ed[0][0] * sc, ed[0][1] * sc, ed[0][2] * sc, ry, rx), b0 = rot(ed[1][0] * sc, ed[1][1] * sc, ed[1][2] * sc, ry, rx), b = [lerp(a[0], b0[0], q), lerp(a[1], b0[1], q), lerp(a[2], b0[2], q)];
      const pa = proj(a[0], a[1], a[2], x, y), pb = proj(b[0], b[1], b[2], x, y), depth = cl(1 - (a[2] + b[2]) / 2 / 220, .35, 1);
      ctx.strokeStyle = rgba(tone, al * depth * (.55 + .4 * act)); ctx.beginPath(); ctx.moveTo(pa[0], pa[1]); ctx.lineTo(pb[0], pb[1]); ctx.stroke();
    });
    if (e.dots) { ctx.fillStyle = rgba(tone, al * .9); for (let i = 0; i < e.dots; i++) { const pt = rot(-(f.w3 || 150) / 2 + 16, -(f.h3 || 110) / 2 + 14 + i * 18, (f.d3 || 110) / 2, ry, rx), pp = proj(pt[0], pt[1], pt[2], x, y); ctx.beginPath(); ctx.arc(pp[0], pp[1], 2.2, 0, 6.3); ctx.fill(); } }
  }
  function drawCells(e, t, wv) {
    const f = prop(e, t), n = e.n || 16, cols = e.cols || 8, cw = f.cw || 96, al = wv.a, rows = Math.ceil(n / cols), lit = f.lit || [], vals = f.vals || [];
    const ry = f.ry == null ? -.35 : f.ry, rx = f.rx == null ? .8 : f.rx;
    for (let i = 0; i < n; i++) {
      const c = i % cols, r = Math.floor(i / cols), px = (c - (cols - 1) / 2) * cw, pz = (r - (rows - 1) / 2) * cw * .9, on = lit.indexOf(i) >= 0, hh = on ? 30 : 12, ap = cl(wv.p * 2.4 - i / n * 1.2);
      if (ap <= 0) continue; const col = (f.tones && f.tones[i]) || (on ? "white" : "dim");
      boxEdges(cw * .72, hh, cw * .62).forEach(([a, b]) => { const pa = rot(a[0] + px, a[1] - hh / 2, a[2] + pz, ry, rx), pb = rot(b[0] + px, b[1] - hh / 2, b[2] + pz, ry, rx), A = proj(pa[0], pa[1], pa[2], f.x, f.y), B = proj(pb[0], pb[1], pb[2], f.x, f.y); ctx.strokeStyle = rgba(col, al * ap * (on ? .95 : .4)); ctx.lineWidth = 1.4; ctx.beginPath(); ctx.moveTo(A[0], A[1]); ctx.lineTo(B[0], B[1]); ctx.stroke(); });
      if (on) { const c0 = rot(px, -hh - 1, pz, ry, rx), c1 = proj(c0[0], c0[1], c0[2], f.x, f.y); ctx.fillStyle = rgba(col, al * ap * .9); ctx.beginPath(); ctx.ellipse(c1[0], c1[1], cw * .3, cw * .17, 0, 0, 6.3); ctx.fill(); }
      const tp = rot(px, 12, pz + cw * .38, ry, rx), tpp = proj(tp[0], tp[1], tp[2], f.x, f.y); ctx.font = '500 19px "JetBrains Mono"'; ctx.textAlign = "center"; ctx.fillStyle = rgba(on ? "white" : "dim", al * ap * (on ? 1 : .7)); ctx.fillText(vals[i] != null ? vals[i] : (on ? "1" : "0"), tpp[0], tpp[1]);
    }
  }
  const endPt = (id, t) => { if (Array.isArray(id)) return id; const e = byId[id]; if (!e) return [540, 900]; const p = prop(e, t); return [p.x, p.y]; };
  function drawLink(e, t, wv) {
    const f = prop(e, t), A = endPt(e.a, t), B = endPt(e.b, t), dx = B[0] - A[0], dy = B[1] - A[1], L = Math.hypot(dx, dy) || 1, gap = f.gap == null ? 70 : f.gap, a = [A[0] + dx / L * gap, A[1] + dy / L * gap], b = [B[0] - dx / L * gap, B[1] - dy / L * gap], q = eo3(wv.p * 1.4), tone = f.tone || "white";
    ctx.strokeStyle = rgba(tone, wv.a * (f.alpha == null ? .55 : f.alpha)); ctx.lineWidth = 1.5; ctx.setLineDash(e.dash === false ? [] : [3, 9]); ctx.lineDashOffset = -t * 18; ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(lerp(a[0], b[0], q), lerp(a[1], b[1], q)); ctx.stroke(); ctx.setLineDash([]);
    if (e.arrow && q > .95) { const ang = Math.atan2(dy, dx); ctx.fillStyle = rgba(tone, wv.a * .8); ctx.beginPath(); ctx.moveTo(b[0], b[1]); ctx.lineTo(b[0] - 14 * Math.cos(ang - .45), b[1] - 14 * Math.sin(ang - .45)); ctx.lineTo(b[0] - 14 * Math.cos(ang + .45), b[1] - 14 * Math.sin(ang + .45)); ctx.fill(); }
  }
  function packetPos(e, t) { const A = endPt(e.a, t), B = endPt(e.b, t), u = eio3((t - e.ats[0]) / (e.dur || 1)); return [lerp(A[0], B[0], u), lerp(A[1], B[1], u), u]; }
  function drawPacket(e, t, wv) { const [x, y] = packetPos(e, t), c = e.tone || "white"; const g = ctx.createRadialGradient(x, y, 0, x, y, 22); g.addColorStop(0, rgba(c, .9 * wv.a)); g.addColorStop(1, rgba(c, 0)); ctx.fillStyle = g; ctx.fillRect(x - 24, y - 24, 48, 48); ctx.fillStyle = rgba("white", wv.a); ctx.beginPath(); ctx.arc(x, y, 5, 0, 6.3); ctx.fill(); }

  /* ---------- render(t) ---------- */
  const glowEl = $("#glow"), camEl = $("#cam"), svgB = $("#hbv"); let lastScene = -1;
  const gcv = $("#grain"), gctx = gcv.getContext("2d"), tile = document.createElement("canvas"); tile.width = tile.height = 128; { const tc = tile.getContext("2d"), im = tc.createImageData(128, 128), R = rng(SEED + 9); for (let i = 0; i < 128 * 128; i++) { const v = R() < .5 ? 255 : 0; im.data[i * 4] = im.data[i * 4 + 1] = im.data[i * 4 + 2] = v; im.data[i * 4 + 3] = R() * 34; } tc.putImageData(im, 0, 0); }
  const gpat = gctx.createPattern(tile, "repeat");
  let render; render = function (t) {
    const i = sceneAt(t), sc = S[i], su = cl((t - sc.from) / Math.max(.1, sc.to - sc.from));
    if (i !== lastScene) { lastScene = i; glowEl.style.setProperty("--glowc", sc.gt ? rgba(sc.gt, sc.gt === "white" ? .07 : .105) : (sc.glow || (W0 ? W0.glow : "rgba(255,255,255,.07)"))); kick.textContent = sc.kicker || ""; ticks.forEach((k, j) => k.classList.toggle("on", j <= i)); }
    fill.style.width = (972 * cl(t / T)) + "px";
    kick.style.opacity = M.kickers === false ? 0 : cl((t - sc.from) / .3) * (1 - cl((t - (sc.to - .25)) / .25));
    S.forEach((s, j) => { if (j !== i) { s.node.style.opacity = 0; return; } s.node.style.opacity = 1 - cl((t - (s.to - .22)) / .22); s.words.forEach((w, q) => { const u = eo3((t - w.t) / .2), el = s.wn[q]; el.style.opacity = u * (w.key ? 1 : .96); el.style.transform = `translateY(${(1 - u) * 10}px) scale(${1 + (w.key ? .09 * Math.sin(Math.PI * cl((t - w.t) / .32)) : 0)})`; if (w.key) el.style.setProperty("--u", eo3((t - w.t - .05) / .3)); }); });
    const cam = camAt(t), pu = cam.pu;
    const ct0 = `translate(${cam.x}px,${cam.y}px) scale(${cam.s})`; stage.style.transform = ct0; glowEl.style.transform = ct0; glowEl.style.opacity = .85 + .55 * pu;
    camEl.style.filter = cam.hx > .5 ? (svgB.setAttribute("stdDeviation", cam.hx + " 0"), "url(#hb)") : cam.hy > .5 ? (svgB.setAttribute("stdDeviation", "0 " + cam.hy), "url(#hb)") : cam.blur > .4 ? `blur(${cam.blur}px)` : "none";
    /* canvas */
    ctx.clearRect(0, 0, W, H); ctx.save(); ctx.translate(540 + cam.x, 900 + cam.y); ctx.scale(cam.s, cam.s); ctx.translate(-540, -900);
    dust.forEach(d => { const yy = 160 + (((d[1] - 160 - t * d[3] * 11) % 1400) + 1400) % 1400, xx = d[0] + Math.sin(t * .5 + d[2]) * 12; ctx.fillStyle = `rgba(255,255,255,${.12 + .2 * Math.abs(Math.sin(t * .8 + d[2])) + .25 * pu})`; ctx.fillRect(xx, yy, d[3] * (1 + pu), d[3] * (1 + pu)); });
    const mo = i === 0 ? cl(.8 + t / 1.5) : cl((t - (sc.from - .3)) / 1.05), e1 = eio3(mo), pT = i > 0 ? S[i - 1].T : prevT0, pp = i > 0 ? S[i - 1].hp : { alpha: 0, spin: 0, tilt: 0, y: 0, size: 1, tone: "white" }, hp = sc.hp, cur = sc.T;
    const al = lerp(pp.alpha, hp.alpha, e1), spin = lerp(pp.spin, hp.spin, e1), tilt = lerp(pp.tilt, hp.tilt, e1), cy = CY + lerp(pp.y, hp.y, e1), size = lerp(pp.size, hp.size, e1), scat = Math.sin(Math.PI * e1) * 320 + (1 - cl(al * 3)) * 140;
    if (al > .01) {
      const ang = t * spin, ca = Math.cos(ang), sa = Math.sin(ang), ct = Math.cos(tilt), st = Math.sin(tilt), buckets = [[], [], [], []];
      for (let n = 0; n < N; n++) {
        const b = n * 3; let x = lerp(pT[b], cur[b], e1) + dir[b] * scat + Math.sin(t * .9 + ph[n]) * 2.5, y = lerp(pT[b + 1], cur[b + 1], e1) + dir[b + 1] * scat, z = lerp(pT[b + 2], cur[b + 2], e1) + dir[b + 2] * scat;
        const X = x * ca + z * sa, Z0 = -x * sa + z * ca, Y = y * ct - Z0 * st, Z = y * st + Z0 * ct, s = F / (F + Z), dep = cl(1 - Z / 600, .25, 1);
        const tw = .72 + .28 * Math.sin(t * 2.2 + ph[n] * 3), a = dep * tw; buckets[Math.min(3, Math.floor(a * 4))].push(540 + X * s * size, cy + Y * s * size, s);
      }
      buckets.forEach((arr, q) => { if (!arr.length) return; ctx.fillStyle = rgba(hp.tone, al * (.28 + q * .24)); ctx.beginPath(); for (let n = 0; n < arr.length; n += 3) { const r = 1.6 * arr[n + 2] * (.85 + q * .12) * (1 + .16 * pu); ctx.moveTo(arr[n] + r, arr[n + 1]); ctx.arc(arr[n], arr[n + 1], r, 0, 6.3); } ctx.fill(); });
    }
    EL.forEach(e => { const wv = win(e, t); if (!wv) return; if (e.type === "link") drawLink(e, t, wv); else if (e.type === "obj") drawObj(e, t, wv); else if (e.type === "cells") drawCells(e, t, wv); else if (e.type === "packet") drawPacket(e, t, wv); });
    FX.shocks.forEach(sk => { const u = (t - sk.t) / .75; if (u < 0 || u > 1) return; [0, .09].forEach((dl, q) => { const uu = cl(u - dl); if (uu <= 0) return; ctx.strokeStyle = rgba(sk.tone || "white", .6 * (1 - uu) * (q ? .6 : 1)); ctx.lineWidth = 1 + 6 * (1 - uu); ctx.beginPath(); ctx.arc(sk.x || 540, sk.y || 900, 50 + 560 * eo3(uu), 0, 6.3); ctx.stroke(); }); });
    ctx.restore();
    /* grain: seeded noise tile jittered at 12 fps = one texture over everything */
    const gf = Math.floor(t * 12), gx = (gf * 53) % 128, gy = (gf * 91) % 128; gctx.setTransform(1, 0, 0, 1, 0, 0); gctx.clearRect(0, 0, 540, 960); gctx.fillStyle = gpat; gctx.setTransform(1, 0, 0, 1, -gx, -gy); gctx.fillRect(gx, gy, 540 + 128, 960 + 128);
    /* DOM */
    EL.forEach(e => {
      const n = e.node; if (!n) return; const wv = win(e, t); if (!wv) { n.style.opacity = 0; return; }
      const f = prop(e, t); let x = f.x, y = f.y; if (e.type === "packet") { const q = packetPos(e, t); x = q[0]; y = q[1] - 38; }
      const pop = e.type === "stamp" ? eoB((t - wv.t0) / .35) : eo3((t - wv.t0) / .45), sc2 = (f.sc == null ? 1 : f.sc) * (e.type === "stamp" ? lerp(1.7, 1, pop) : lerp(.94, 1, pop)), rotz = e.type === "stamp" ? (f.rot == null ? -6 : f.rot) : 0;
      const isO = e.type === "obj", off = isO ? (f.ly == null ? ((f.h3 || 110) * .55 + (f.d3 || 110) * .25) * OS + 34 : f.ly) : 0, dy = (e.type === "packet" || isO) ? 0 : (1 - pop) * 16, ox = e.w / 2, oy = isO ? 0 : e.h / 2;
      n.style.transform = `translate(${x - ox}px,${y - oy + off + dy}px) rotate(${rotz}deg) scale(${sc2})`; n.style.opacity = wv.a * (f.alpha == null ? 1 : f.alpha);
      n.style.transformOrigin = `${ox}px ${oy}px`;
      const el = e.type, ln = n.querySelector(".ln");
      if (el === "card" && ln) { const lines = f.lines || e.lines || []; if (e.type_cps) { let left = Math.max(0, Math.floor((t - wv.t0 - .25) * e.type_cps)), out = [], cursor = false; for (const L of lines) { const h = mark(L), pl = plainLen(h); out.push(trunc(h, left)); left -= pl + 1; if (left <= 0) { cursor = true; break; } } ln.innerHTML = out.join("\n") + (cursor && Math.floor(t * 2) % 2 ? '<span class="g">▍</span>' : ""); } else ln.innerHTML = lines.map(mark).join("\n"); n.classList.toggle("on", !!f.on); n.classList.toggle("dash", !!f.dash); }
      else if (el === "counter") { const v = lerp(e.from || 0, e.to || 0, eo3((t - wv.t0) / (e.dur || 1.6))); n.querySelector(".n").textContent = (e.prefix || "") + fmtNum(v, e.fmt) + (e.suffix || ""); }
      else if (el === "search") { const s = e.text || "", c = Math.floor(cl((t - wv.t0 - .2) * (e.cps || 14), 0, s.length)); n.querySelector(".tt").innerHTML = c ? s.slice(0, c).replace(/</g, "&lt;") + (Math.floor(t * 2) % 2 ? '<span class="car"></span>' : "") : `<span class="ph">${e.ph || "Search or type a URL"}</span>` + (Math.floor(t * 2) % 2 ? '<span class="car"></span>' : ""); }
      else if (el === "list") { const act = Math.round(f.active == null ? -1 : f.active); n.querySelectorAll(".it").forEach((it, j) => { it.style.opacity = eo3((t - wv.t0 - .25 - j * .11) / .3); it.classList.toggle("on", j === act); }); }
      else if (el === "compare") { n.querySelectorAll(".card").forEach((c, j) => { const on = f.active === j; c.classList.toggle("on", on); c.classList.toggle("dash", !on && f.active != null && f.active >= 0); }); }
      else if (el === "bars") { n.querySelectorAll("i").forEach((b, j) => { b.style.height = (e.values[j] * 150 * eo3((t - wv.t0 - j * .08) / .6)) + "px"; b.style.opacity = j === f.active ? 1 : .55; }); }
    });
  }
  /* frame-0 headline (reel-edit humanize R12): the claim in two lines, line 1 = the belief, line 2 = the twist; present from frame 0 to t1 */
  const HL = M.headline, hlEl = document.getElementById("hl");
  if (HL && hlEl) hlEl.innerHTML = HL.lines.map((l, i) => `<div class="hl${i + 1}">${String(l).split(" ").map(w => HL.strike && w.toLowerCase().replace(/[^a-z0-9]/g, "") === HL.strike.toLowerCase() ? `<s>${w}</s>` : w).join(" ")}</div>`).join("");
  const CV = M.cover && M.cover.lines ? M.cover : null, cvEl = document.getElementById("cv");
  if (CV && cvEl) { document.getElementById("root").classList.add("cover"); const fs = Math.round(Math.max(92, Math.min(150, 880 / (.6 * Math.max(...CV.lines.map(l => String(l).length)))))); cvEl.innerHTML = `<div class="cv-k">${CV.kicker || ""}</div><div class="cv-w" style="font-size:${fs}px;line-height:${Math.round(fs * 1.04)}px">` + CV.lines.map((l, i) => `<div class="cv-l${i === (CV.accent == null ? 1 : CV.accent) ? " ac" : ""}">${l}</div>`).join("") + `</div><div class="cv-b">${M.handle}  ·  ${M.series}</div>`; }
  function hlRender(t) { if (!HL || !hlEl) return; const t1 = HL.t1 || 2.3, u = eo3(t / .35); hlEl.style.opacity = CV ? 0 : 1 - cl((t - t1) / .25); hlEl.style.transform = `translateY(${(1 - u) * 14}px) scale(${1.05 - .05 * u})`; hlEl.querySelectorAll("s").forEach(s => s.style.setProperty("--s", eo3((t - .5) / .3))); }
  const _render = render; render = t => { _render(t); hlRender(t); };
  const prevT0 = shape({ shape: "cloud", r: 420 });
  render(0);
  const tl = gsap.timeline({ paused: true }); tl.to({}, { duration: T, ease: "none", onUpdate() { render(this.time()); } }, 0);
  window.__timelines = window.__timelines || {}; window.__timelines["main"] = tl; window.__explainerRender = render;
})();
