/* Studio layer (v0.7): multicolour animated backdrops + real 3D (WebGL / three.js) objects. Everything is a PURE FUNCTION OF TIME like engine.js.
   Loaded before engine.js, which calls  const ST = await window.__studio(api)  then  ST.back(t)  and  ST.gl(t, cam)  every frame.
   - backdrops (per scene, crossfaded): aurora | fluted | duotone | studio | cream | deep   (+ scene.flash colour pulse)
   - 3D elements (stage type "gl"): orb | knot | torus | ring | slab | cubes | gem | capsule | db | server | coin | shield | ribbon
   three.js is vendored (MIT) in assets/vendor/; it renders inside HyperFrames on the GPU path (verified: hardware WebGL, deterministic per seek). */
window.__studio = async function (api) {
  const { M, W0, S, EL, TONE, rgba, cl, lerp, eo3, eio3, eoB, prop, win, sceneAt, root } = api, W = 1080, H = 1920;
  const col = c => { if (Array.isArray(c)) return c; if (TONE[c]) return TONE[c]; if (/^#/.test(c)) { const h = c.length === 4 ? c.replace(/[^#]/g, m => m + m).slice(1) : c.slice(1); return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16)); } return TONE.white; };
  const rg = (c, a) => { c = col(c); return `rgba(${c[0]},${c[1]},${c[2]},${a})`; };
  const mix = (a, b, k) => [0, 1, 2].map(i => Math.round(lerp(a[i], b[i], k)));

  /* ============ backdrops ============ */
  const bd = document.getElementById("bd"), bx = bd.getContext("2d");
  const DEF = { aurora: { base: "#06081a", colors: ["blue", "violet", "yellow"] }, fluted: { base: "#03080c", colors: ["blue", "green"], sw: 58 }, duotone: { colors: ["#0a1240", "#ff7a2f"] }, studio: { base: "#07081a", colors: ["blue"] }, cream: { base: "#efe9dc", colors: ["yellow"], light: true }, deep: { base: "#050506", colors: ["white"] }, ink: { base: "#060912", colors: ["blue", "violet"] } };
  function specOf(i) {
    const sc = S[i], w = W0 && W0.backdrop, own = sc.bg;
    let s = typeof own === "string" ? { kind: own } : own ? Object.assign({}, own) : null;
    if (!s) s = typeof w === "string" ? { kind: w } : w ? Object.assign({}, w) : { kind: "deep" };
    if (typeof s === "string") s = { kind: s };
    const d = DEF[s.kind] || DEF.deep; s = Object.assign({}, d, W0 && typeof W0.backdrop === "object" && W0.backdrop.kind === s.kind ? W0.backdrop : {}, s);
    const z = sc.zone && W0 && W0.zones && W0.zones[sc.zone];
    if (z) { if (s.kind === "ink") { const zm = (W0 && W0.zone_mix) || .38; s.colors = [mix(col(s.colors[0]), col(z), zm), ...s.colors.slice(1)]; } else s.colors = [z, ...(s.colors || []).filter(c => c !== z)].slice(0, 4); s.zone = z; }
    return s;
  }
  function paint(s, t, a, i) {
    const c = bx; c.save(); c.globalAlpha = a; const cs = (s.colors || ["white"]).map(col);
    if (s.kind === "cream") {
      c.fillStyle = s.base; c.fillRect(0, 0, W, H); let g = c.createRadialGradient(540, 600 + 40 * Math.sin(t * .3), 60, 540, 700, 1100); g.addColorStop(0, "rgba(255,255,255,.75)"); g.addColorStop(1, "rgba(0,0,0,.06)"); c.fillStyle = g; c.fillRect(0, 0, W, H);
      cs.forEach((k, j) => { const g2 = c.createRadialGradient(W * (.2 + .6 * j), H * .85, 0, W * (.2 + .6 * j), H * .85, 700); g2.addColorStop(0, `rgba(${k[0]},${k[1]},${k[2]},.16)`); g2.addColorStop(1, "rgba(0,0,0,0)"); c.fillStyle = g2; c.fillRect(0, 0, W, H); });
      dots(c, t, "rgba(20,20,30,.07)", 44);
    } else if (s.kind === "duotone") {
      const A = cs[0], B = cs[1] || cs[0]; let g = c.createLinearGradient(0, 0, W * .45, H); g.addColorStop(0, `rgb(${A})`); g.addColorStop(.55, `rgb(${mix(A, B, .35)})`); g.addColorStop(1, `rgb(${B})`); c.fillStyle = g; c.fillRect(0, 0, W, H);
      const hx = W * (.5 + .22 * Math.sin(t * .27)), hy = H * (.62 + .08 * Math.sin(t * .21)); let g2 = c.createRadialGradient(hx, hy, 0, hx, hy, 900); g2.addColorStop(0, `rgba(${B[0]},${B[1]},${B[2]},.55)`); g2.addColorStop(1, `rgba(${B[0]},${B[1]},${B[2]},0)`); c.globalCompositeOperation = "lighter"; c.fillStyle = g2; c.fillRect(0, 0, W, H); c.globalCompositeOperation = "source-over";
      let v = c.createRadialGradient(540, 900, 500, 540, 900, 1300); v.addColorStop(0, "rgba(0,0,0,0)"); v.addColorStop(1, "rgba(0,0,12,.5)"); c.fillStyle = v; c.fillRect(0, 0, W, H); dots(c, t, "rgba(255,255,255,.16)", 40);
    } else if (s.kind === "fluted") {
      c.fillStyle = s.base; c.fillRect(0, 0, W, H); c.globalCompositeOperation = "lighter";
      cs.forEach((k, j) => { const x = W * (j % 2 ? .95 : .05) + 70 * Math.sin(t * .22 + j * 2), y = H * (.3 + .4 * ((j * .37) % 1)) + 120 * Math.sin(t * .17 + j); const g = c.createRadialGradient(x, y, 0, x, y, 1150); g.addColorStop(0, `rgba(${k[0]},${k[1]},${k[2]},.85)`); g.addColorStop(.45, `rgba(${k[0]},${k[1]},${k[2]},.22)`); g.addColorStop(1, `rgba(${k[0]},${k[1]},${k[2]},0)`); c.fillStyle = g; c.fillRect(0, 0, W, H); });
      c.globalCompositeOperation = "source-over"; const sw = s.sw || 58, off = (t * 9) % sw;
      for (let x = -sw + off; x < W + sw; x += sw) { const g = c.createLinearGradient(x, 0, x + sw, 0); g.addColorStop(0, "rgba(0,0,0,.72)"); g.addColorStop(.4, "rgba(0,0,0,.05)"); g.addColorStop(.52, "rgba(255,255,255,.10)"); g.addColorStop(1, "rgba(0,0,0,.78)"); c.fillStyle = g; c.fillRect(x, 0, sw, H); }
      let v = c.createRadialGradient(540, 900, 450, 540, 900, 1250); v.addColorStop(0, "rgba(0,0,0,0)"); v.addColorStop(1, "rgba(0,0,0,.55)"); c.fillStyle = v; c.fillRect(0, 0, W, H);
    } else if (s.kind === "studio") {
      let g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, s.base); g.addColorStop(1, "#020208"); c.fillStyle = g; c.fillRect(0, 0, W, H); c.globalCompositeOperation = "lighter";
      const k = cs[0], sx = 540 + 90 * Math.sin(t * .31); let g1 = c.createRadialGradient(sx, 260, 0, sx, 260, 1000); g1.addColorStop(0, `rgba(${k[0]},${k[1]},${k[2]},.5)`); g1.addColorStop(1, `rgba(${k[0]},${k[1]},${k[2]},0)`); c.fillStyle = g1; c.fillRect(0, 0, W, H);
      const k2 = cs[1] || k; let g2 = c.createRadialGradient(540, 1500, 0, 540, 1500, 800); g2.addColorStop(0, `rgba(${k2[0]},${k2[1]},${k2[2]},.30)`); g2.addColorStop(1, `rgba(${k2[0]},${k2[1]},${k2[2]},0)`); c.fillStyle = g2; c.fillRect(0, 0, W, H); c.globalCompositeOperation = "source-over";
    } else if (s.kind === "ink") {
      let g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, "#080c18"); g.addColorStop(.55, s.base); g.addColorStop(1, "#04060c"); c.fillStyle = g; c.fillRect(0, 0, W, H); c.globalCompositeOperation = "lighter";
      const k = cs[0], k2 = cs[1] || k, dx = 40 * Math.sin(t * .17 + (i || 0) * .3);
      let g1 = c.createRadialGradient(540 + dx, 800, 0, 540 + dx, 800, 1000); g1.addColorStop(0, `rgba(${k[0]},${k[1]},${k[2]},.30)`); g1.addColorStop(.5, `rgba(${k[0]},${k[1]},${k[2]},.09)`); g1.addColorStop(1, `rgba(${k[0]},${k[1]},${k[2]},0)`); c.fillStyle = g1; c.fillRect(0, 0, W, H);
      let g2 = c.createRadialGradient(540 - dx, 1650, 0, 540 - dx, 1650, 820); g2.addColorStop(0, `rgba(${k2[0]},${k2[1]},${k2[2]},.13)`); g2.addColorStop(1, `rgba(${k2[0]},${k2[1]},${k2[2]},0)`); c.fillStyle = g2; c.fillRect(0, 0, W, H);
      c.globalCompositeOperation = "source-over"; let v = c.createRadialGradient(540, 960, 520, 540, 960, 1300); v.addColorStop(0, "rgba(0,0,6,0)"); v.addColorStop(1, "rgba(0,0,6,.55)"); c.fillStyle = v; c.fillRect(0, 0, W, H);
    } else if (s.kind === "aurora") {
      c.fillStyle = s.base; c.fillRect(0, 0, W, H); c.globalCompositeOperation = "lighter";
      cs.forEach((k, j) => { const ph = j * 2.1 + (i || 0) * .35, x = W * (.5 + .42 * Math.sin(t * .23 + ph)), y = H * (.48 + .36 * Math.sin(t * .19 + ph * 1.3 + 1)), r = 760 + 140 * Math.sin(t * .3 + j); const g = c.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, `rgba(${k[0]},${k[1]},${k[2]},${j ? .5 : .62})`); g.addColorStop(.5, `rgba(${k[0]},${k[1]},${k[2]},.16)`); g.addColorStop(1, `rgba(${k[0]},${k[1]},${k[2]},0)`); c.fillStyle = g; c.fillRect(0, 0, W, H); });
      c.globalCompositeOperation = "source-over"; let v = c.createRadialGradient(540, 900, 380, 540, 900, 1250); v.addColorStop(0, "rgba(0,0,6,0)"); v.addColorStop(1, "rgba(0,0,6,.62)"); c.fillStyle = v; c.fillRect(0, 0, W, H);
    } else { /* deep */
      c.fillStyle = s.base; c.fillRect(0, 0, W, H); const k = cs[0]; const g = c.createRadialGradient(540, 900, 0, 540, 900, 900); g.addColorStop(0, `rgba(${k[0]},${k[1]},${k[2]},.14)`); g.addColorStop(1, `rgba(${k[0]},${k[1]},${k[2]},0)`); c.fillStyle = g; c.fillRect(0, 0, W, H);
    }
    c.restore();
  }
  function dots(c, t, color, gap) { c.fillStyle = color; for (let y = gap / 2; y < H; y += gap) for (let x = gap / 2; x < W; x += gap) { const d = Math.hypot(x - 540, y - 900) / 900, a = cl(1.15 - d); if (a > .05) { c.globalAlpha *= 1; c.fillRect(x - 1.2, y - 1.2, 2.4, 2.4); } } }
  const SPEC = S.map((_, i) => specOf(i)); let lastLight = -1;
  function back(t) {
    const i = sceneAt(t), sc = S[i], k = i > 0 ? eio3((t - sc.from + .12) / .62) : 1, prev = i > 0 ? SPEC[i - 1] : null;
    bx.clearRect(0, 0, W, H);
    if (prev && k < 1) paint(prev, t, 1, i - 1);
    paint(SPEC[i], t, prev ? k : 1, i);
    const L = (SPEC[i].light ? k : 0) + (prev && prev.light ? 1 - k : 0), li = L > .5 ? 1 : 0; if (li !== lastLight) { lastLight = li; root.classList.toggle("light", !!li); }
    if (sc.flash && !(W0 && W0.flash_gain === 0)) { const u = (t - sc.from - (sc.flash_at || 0)) / .7; if (u > 0 && u < 1) { bx.save(); bx.globalCompositeOperation = "lighter"; bx.fillStyle = rg(sc.flash, .42 * Math.pow(1 - u, 1.6)); bx.fillRect(0, 0, W, H); bx.restore(); } }
    /* parallax: the backdrop moves a little less than the stage */
    return L;
  }

  /* ============ 3D (three.js) ============ */
  const GL = /[?&]layout=1/.test(location.search) ? [] : EL.filter(e => e.type === "gl"); let gl = () => { };
  if (GL.length) {
    const THREE = await import("./assets/vendor/three.module.min.js"), cv = document.getElementById("gl");
    const r = new THREE.WebGLRenderer({ canvas: cv, antialias: true, alpha: true, preserveDrawingBuffer: true }); r.setPixelRatio(1); r.setSize(W, H, false); r.setClearColor(0x000000, 0); r.toneMapping = THREE.ACESFilmicToneMapping; r.toneMappingExposure = (W0 && W0.gl_exposure) || 1.12;
    const sc = new THREE.Scene(), FOV = 30, ZC = (H / 2) / Math.tan(FOV * Math.PI / 360), cam = new THREE.PerspectiveCamera(FOV, W / H, 10, 12000);
    const OBS = W0 && W0.mat === "obsidian";
    const C3 = c => { const a = col(c); return new THREE.Color().setRGB(a[0] / 255, a[1] / 255, a[2] / 255, THREE.SRGBColorSpace); };      // palette values are sRGB: convert, or every colour renders washed out
    /* studio environment from the world's own colours: emissive panels -> PMREM, gives every object coloured rim light + reflections, no files */
    const env = new THREE.Scene(); env.background = new THREE.Color(0x04050a); const pal = (W0 && W0.gl_env) || ["blue", "violet", "yellow", "white"];
    { const cvn = document.createElement("canvas"); cvn.width = 4; cvn.height = 256; const cx = cvn.getContext("2d"), g = cx.createLinearGradient(0, 0, 0, 256), c0 = col(pal[0]);
      const c1 = col(pal[1 % pal.length]); g.addColorStop(0, `rgb(${c1.map(v => Math.round(v * .5))})`); g.addColorStop(.38, `rgb(${c0.map(v => Math.round(v * .85))})`); g.addColorStop(.62, `rgb(${c0.map(v => Math.round(v * .22))})`); g.addColorStop(1, "#070914"); cx.fillStyle = g; cx.fillRect(0, 0, 4, 256);
      const tx = new THREE.CanvasTexture(cvn); tx.colorSpace = THREE.SRGBColorSpace; env.add(new THREE.Mesh(new THREE.SphereGeometry(9000, 32, 24), new THREE.MeshBasicMaterial({ map: tx, side: THREE.BackSide }))); }
    /* softboxes: tall coloured strips left/right (rim colours), a thin white top strip, a warm low kicker */
    [[pal[0], 420, 2600, -2700, 300, 900, 7], [pal[1 % pal.length], 380, 2400, 2700, 200, 700, 6], ["white", 2400, 160, 0, 3000, 300, 4], [pal[2 % pal.length], 4200, 900, 0, -3200, 1500, 1.4], ["white", 900, 2000, 1500, 900, 2600, 1.6]].forEach(([c, w, h, x, y, z, k]) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ color: C3(c).multiplyScalar(k * (OBS ? .75 : 1)), side: THREE.DoubleSide })); m.position.set(x, y, z); m.lookAt(0, 0, 0); env.add(m); });
    const pm = new THREE.PMREMGenerator(r); sc.environment = pm.fromScene(env, .03, 1, 30000).texture;
    const key = new THREE.DirectionalLight(0xffffff, 1.1); key.position.set(-900, 1400, 1400); sc.add(key); sc.add(new THREE.HemisphereLight(0xb8c4ff, 0x20123a, .8));
    const rrect = (w, h, rr) => { const s = new THREE.Shape(), x = -w / 2, y = -h / 2; s.moveTo(x + rr, y); s.lineTo(x + w - rr, y); s.quadraticCurveTo(x + w, y, x + w, y + rr); s.lineTo(x + w, y + h - rr); s.quadraticCurveTo(x + w, y + h, x + w - rr, y + h); s.lineTo(x + rr, y + h); s.quadraticCurveTo(x, y + h, x, y + h - rr); s.lineTo(x, y + rr); s.quadraticCurveTo(x, y, x + rr, y); return s; };
    const slabGeo = (w, h, d, rr) => { const b = Math.min(d * .3, rr * .5); const g = new THREE.ExtrudeGeometry(rrect(Math.max(2, w - 2 * b), Math.max(2, h - 2 * b), Math.max(1, rr - b)), { depth: Math.max(1, d - 2 * b), bevelEnabled: true, bevelThickness: b, bevelSize: b, bevelSegments: 7, curveSegments: 18 }); g.translate(0, 0, -(d - 2 * b) / 2); return g; };
    const MATS = { glossy: { metalness: .32, roughness: .2, clearcoat: 1, clearcoatRoughness: .05, envMapIntensity: 1.15 }, chrome: { metalness: 1, roughness: .1, envMapIntensity: 1.25 }, glass: { metalness: 0, roughness: .06, clearcoat: 1, transparent: true, opacity: .5, envMapIntensity: 2.4 }, neon: { metalness: 0, roughness: .35, envMapIntensity: .6 } };
    const mat = (tone, style = "glossy", em = .0) => { const c = C3(tone), o = Object.assign({ color: c.clone().multiplyScalar(OBS && style !== "neon" ? .2 : style === "chrome" ? .85 : .72), iridescence: 0 }, MATS[style] || MATS.glossy); if (OBS && style !== "neon") Object.assign(o, { metalness: .6, roughness: .24, envMapIntensity: 1.1 }); const m = new THREE.MeshPhysicalMaterial(o); if (style === "glossy" && !em) em = OBS ? .1 : .16; if (OBS && style === "chrome") style = "glossy"; m.userData.neon = style === "neon"; m.userData.hasEm = !!em || style === "neon"; if (style === "neon" || em) { m.emissive = c; m.emissiveIntensity = style === "neon" ? 1.35 : em; } return m; };
    const dark = () => new THREE.MeshPhysicalMaterial({ color: C3(OBS ? "#1a2240" : "#26357a"), metalness: .5, roughness: .3, clearcoat: 1, clearcoatRoughness: .12, envMapIntensity: 1.15, emissive: C3("#0a1030"), emissiveIntensity: 1 });
    const tube = (pts, rad, seg = 160) => { const cu = new THREE.CatmullRomCurve3(pts.map(p => new THREE.Vector3(p[0], -p[1], p[2] || 0))); return new THREE.TubeGeometry(cu, seg, rad, 18, false); };
    const stateSince = (e, t, fn) => { const fr = e.frames; let k = 0; for (let i = 0; i < fr.length; i++) if (t >= fr[i].t) k = i; const s = fn(fr[k]); let j = k; while (j > 0 && fn(fr[j - 1]) === s) j--; return [s, j === 0 && fn(fr[0]) === s ? -9 : fr[j].t]; };
    const INST = GL.map(e => {
      const g = new THREE.Group(), k = e.kind || "orb", f0 = e.frames[0], R = e.r || 150, tone0 = f0.tone || e.tone || "blue", style = e.mat || (k === "ring" ? "neon" : "glossy"), parts = {}; let upd = null;
      const add = (m, p) => { g.add(m); return m; };
      if (k === "orb") { add(new THREE.Mesh(new THREE.SphereGeometry(R, 96, 72), parts.m = mat(tone0, style))); }
      else if (k === "knot") { add(new THREE.Mesh(new THREE.TorusKnotGeometry(R * .72, R * .26, 360, 48, e.p || 2, e.q || 3), parts.m = mat(tone0, style === "glossy" ? "chrome" : style))); }
      else if (k === "torus") { add(new THREE.Mesh(new THREE.TorusGeometry(R, R * .3, 48, 160), parts.m = mat(tone0, style))); }
      else if (k === "ring") { add(new THREE.Mesh(new THREE.TorusGeometry(R, e.tube || R * .035, 24, 240), parts.m = mat(tone0, "neon"))); }
      else if (k === "gem") { add(new THREE.Mesh(new THREE.IcosahedronGeometry(R, e.detail || 0), parts.m = Object.assign(mat(tone0, "chrome", .22), { flatShading: true }))); }
      else if (k === "capsule") { add(new THREE.Mesh(new THREE.CapsuleGeometry(R * .45, R * 1.1, 24, 48), parts.m = mat(tone0, style))); }
      else if (k === "coin") { const m = new THREE.Mesh(new THREE.CylinderGeometry(R, R, R * .16, 96), parts.m = mat(tone0, "chrome", .3)); m.rotation.x = Math.PI / 2; add(m); const rim = new THREE.Mesh(new THREE.TorusGeometry(R * .86, R * .02, 16, 120), mat(tone0, "neon")); rim.position.z = R * .085; add(rim); }
      else if (k === "slab") { const w = e.w3 || 300, h = e.h3 || 200, d = e.d3 || 46; add(new THREE.Mesh(slabGeo(w, h, d, e.round || 34), parts.m = mat(tone0, style))); if (e.screen) { const sm = new THREE.Mesh(new THREE.ShapeGeometry(rrect(w * .86, h * .86, 20), 12), parts.s = new THREE.MeshBasicMaterial({ color: C3(e.screen).multiplyScalar(.5) })); sm.position.z = d / 2 + 1.5; add(sm); } }
      else if (k === "db") { const n = e.n || 3, rd = (e.w3 || 240) / 2; parts.rims = []; for (let i = 0; i < n; i++) { const m = new THREE.Mesh(new THREE.CylinderGeometry(rd, rd, 46, 80), parts.m = mat(tone0, style)); m.position.y = (i - (n - 1) / 2) * 62; add(m); const rim = new THREE.Mesh(new THREE.TorusGeometry(rd + .5, 3.2, 12, 100), mat(e.rim || "white", "neon")); rim.rotation.x = Math.PI / 2; rim.position.y = m.position.y + 24; add(rim); parts.rims.push(rim); } }
      else if (k === "server") { const n = e.units || 3, w = e.w3 || 300, uh = (e.h3 || 240) / n - 12; parts.leds = []; for (let i = 0; i < n; i++) { const m = new THREE.Mesh(slabGeo(w, uh, e.d3 || 120, 18), parts.m = mat(tone0, style)); m.position.y = (i - (n - 1) / 2) * (uh + 12); add(m); for (let q = 0; q < 3; q++) { const led = new THREE.Mesh(new THREE.SphereGeometry(5, 12, 10), new THREE.MeshBasicMaterial({ color: C3(q ? "green" : "yellow") })); led.position.set(-w / 2 + 28 + q * 18, m.position.y, (e.d3 || 120) / 2 + 3); add(led); parts.leds.push(led); } } }
      else if (k === "shield") { const s = new THREE.Shape(); s.moveTo(0, 1); s.bezierCurveTo(.35, .86, .72, .8, .9, .78); s.lineTo(.9, .1); s.bezierCurveTo(.9, -.55, .45, -.85, 0, -1.05); s.bezierCurveTo(-.45, -.85, -.9, -.55, -.9, .1); s.lineTo(-.9, .78); s.bezierCurveTo(-.72, .8, -.35, .86, 0, 1); const geo = new THREE.ExtrudeGeometry(s, { depth: .22, bevelEnabled: true, bevelThickness: .08, bevelSize: .06, bevelSegments: 6, curveSegments: 24 }); geo.translate(0, 0, -.11); geo.scale(R, R, R); add(new THREE.Mesh(geo, parts.m = mat(tone0, style))); const ck = new THREE.Mesh(tube([[-.42 * R, 0, 0], [-.1 * R, .32 * R, 0], [.46 * R, -.34 * R, 0]].map(p => [p[0], p[1], R * .2]), R * .07, 40), parts.c = new THREE.MeshBasicMaterial({ color: 0xffffff })); parts.ck = ck; ck.geometry.setDrawRange(0, 0); add(ck); }
      else if (k === "ribbon") { const pts = e.pts || [[-380, 80, 0], [-190, -90, 60], [0, 70, -40], [190, -60, 50], [380, 40, 0]], seg = 200, geo = tube(pts, e.tube || 12, seg); parts.geo = geo; parts.seg = seg; add(new THREE.Mesh(geo, parts.m = mat(tone0, e.mat || "neon"))); }
      else if (k === "cubes") { const n = e.n || 12, cols = e.cols || 4, cw = e.cw || 120, rows = Math.ceil(n / cols), cg = slabGeo(cw * .78, cw * .78, cw * .62, cw * .16); parts.cubes = []; for (let i = 0; i < n; i++) { const m = new THREE.Mesh(cg, dark()); m.userData = { c: i % cols, r: Math.floor(i / cols), dk: m.material }; m.position.set((m.userData.c - (cols - 1) / 2) * cw, 0, (m.userData.r - (rows - 1) / 2) * cw); m.rotation.x = Math.PI / 2; add(m); parts.cubes.push(m); } }
      sc.add(g); g.visible = false;
      return { e, g, k, parts, R };
    });
    gl = function (t, c) {
      cam.position.set(Math.sin(t * .27) * 70, Math.cos(t * .21) * 40, ZC); cam.lookAt(0, 0, 0);       /* gentle orbit = parallax; shake/zoom come from the CSS camera transform */
      INST.forEach(I => {
        const e = I.e, wv = win(e, t), g = I.g; if (!wv) { g.visible = false; return; }
        const f = prop(e, t), a = wv.a * (f.alpha == null ? 1 : f.alpha), pop = eoB((t - wv.t0) / .62);
        g.visible = a > .01; if (!g.visible) return;
        const bob = Math.sin(t * 1.3 + e.id.length * 1.9) * (f.bob == null ? 10 : f.bob), s = (f.sc == null ? 1 : f.sc) * lerp(.55, 1, pop) * (.35 + .65 * cl(wv.a * 1.4));
        g.position.set((f.x || 540) - 540, 960 - (f.y || 900) + bob, f.z || 0); g.scale.setScalar(Math.max(.001, s));
        const spins = ["orb", "knot", "torus", "ring", "gem", "coin", "capsule"].indexOf(I.k) >= 0, sp = f.spin == null ? (e.spin == null ? (spins ? .4 : 0) : e.spin) : f.spin, sway = spins || I.k === "cubes" ? 0 : (e.sway == null ? .42 : e.sway) * Math.sin(t * .7 + e.id.length); g.rotation.set((f.grx == null ? (I.k === "cubes" ? -1.02 : I.k === "coin" ? -.55 : .25) : f.grx) + (f.wob == null ? .08 : f.wob) * Math.sin(t * .8), (f.gry == null ? (I.k === "cubes" ? -.5 : 0) : f.gry) + (I.k === "cubes" ? Math.sin(t * .4) * .12 : t * sp + sway), f.grz || 0);
        const tone = f.tone || e.tone || "blue", P = I.parts; if (P.m && P.m.color && f.tone != null) { const c0 = C3(tone); P.m.color.copy(c0).multiplyScalar(OBS && !P.m.userData.neon ? .2 : P.m.metalness === 1 ? .85 : .72); if (P.m.userData.hasEm) P.m.emissive.copy(c0); }
        if (I.k === "ribbon") P.geo.setDrawRange(0, Math.floor(P.seg * cl(f.draw == null ? wv.p * 1.3 : f.draw) * 1) * 18 * 6);
        if (I.k === "shield" && P.ck) { const q = cl((t - wv.t0 - .5) / .5); P.ck.geometry.setDrawRange(0, Math.floor(40 * eo3(q)) * 18 * 6); }
        if (I.k === "db" && P.rims) P.rims.forEach((m, j) => { m.material.emissiveIntensity = 1.2 + (f.active || 0) * 1.4 * (.6 + .4 * Math.sin(t * 4 + j)); });
        if (I.k === "cubes") {
          const n = P.cubes.length, cw = e.cw || 120, tn = f.tones || [];
          P.cubes.forEach((m, i) => {
            const [on, since] = stateSince(e, t, fr => (fr.lit || []).indexOf(i) >= 0), u = on ? eio3((t - since) / .38) : 1 - eio3((t - since) / .38), ap = cl(wv.p * 2.2 - i / n * 1.1), tt = tn[i] || tone;
            m.visible = ap > 0; m.position.y = (u * cw * .22 + (1 - eo3(ap)) * -cw * .6); m.scale.setScalar(lerp(.7, 1, eo3(ap)) * (1 + .1 * u));
            const lit = C3(tt); if (!m.userData.mt) m.userData.mt = mat(tt, "glossy", 0); m.material = u > .02 ? m.userData.mt : m.userData.dk;
            if (u > .02) { m.material.color.copy(lit).multiplyScalar(OBS ? .35 : .7); m.material.emissive = lit; m.material.emissiveIntensity = .12 + (OBS ? .5 : .55) * u; }
          });
        }
      });
      r.render(sc, cam);
    };
  }
  return { back, gl: (t, c) => gl(t, c), has3d: GL.length > 0 };
};
