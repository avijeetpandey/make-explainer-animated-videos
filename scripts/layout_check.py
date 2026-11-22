#!/usr/bin/env python3
"""Layout gate: python3 -I layout_check.py <project_dir> [--json]
Loads the built index.html in headless Chrome with ?layout=1 (3D skipped, boxes computed analytically), asks engine.js for the boxes of everything visible
just after the entrances settle and just before the exits of every scene, and checks the things that make a video look amateur:
  OVERLAP   two visible things (text, card, chip, 3D object, label, caption) intersect by more than a few pixels
  CAPTION   a stage element intrudes into the caption zone (y < 470)
  MARGIN    something outside x 60-1020 or below y 1500 (Instagram's bottom UI)
  TIGHT     two stacked elements closer than 28 px    |  LOOSE  a gap between stacked elements above 340 px (dead air)
  BALANCE   the stage content of a scene sits too high / too low (centre outside y 640-1040) or is a tiny island (< 200 px tall)
Add "overlap_ok": true to a storyboard element that is meant to overlap (rare). Exit 1 when anything FAILs."""
import http.server, json, os, re, subprocess, sys, threading, functools, socketserver
proj = os.path.abspath(sys.argv[1]); HERE = os.path.dirname(os.path.abspath(__file__))
def chrome():
    r = subprocess.run(["npx", "--yes", "hyperframes@0.8.209", "browser", "path"], capture_output=True, text=True, cwd=proj)
    for ln in (r.stdout + r.stderr).splitlines():
        if os.path.exists(ln.strip()): return ln.strip()
    sys.exit("headless Chrome not found: run  npx hyperframes browser ensure")
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Q, directory=proj)); port = srv.server_address[1]; threading.Thread(target=srv.serve_forever, daemon=True).start()
r = subprocess.run([chrome(), "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars", "--window-size=1080,1920", "--virtual-time-budget=25000", "--dump-dom", f"http://127.0.0.1:{port}/index.html?layout=1"], capture_output=True, text=True, timeout=120)
srv.shutdown()
m = re.search(r'<pre id="__layout">(.*?)</pre>', r.stdout, re.S)
if not m: sys.exit("layout probe did not run (page error?): " + r.stderr[-300:])
import html as H
scenes = json.loads(H.unescape(m.group(1))); fails, warns = [], []
def ov(a, b):
    w = min(a["r"], b["r"]) - max(a["l"], b["l"]); h = min(a["b"], b["b"]) - max(a["t"], b["t"]); return (w, h) if w > 8 and h > 8 else None
for sc in scenes:
    for sm in sc["samples"]:
        B = sm["boxes"]; stage = [b for b in B if b["kind"] != "caption"]; tag = f"scene {sc['i']} t={sm['t']}"
        for i, a in enumerate(B):
            for b in B[i + 1:]:
                if a["id"] == b["id"] or a.get("ok") or b.get("ok"): continue
                o = ov(a, b)
                if o: fails.append(f"OVERLAP {tag}: {a['id']} ({a['kind']}) x {b['id']} ({b['kind']}) by {o[0]}x{o[1]} px")
        for b in stage:
            if b.get("ok"): continue
            if b["t"] < 470 and b["kind"] not in ("caption", "headline"): fails.append(f"CAPTION {tag}: {b['id']} ({b['kind']}) starts at y={b['t']} (< 470)")
            if b["l"] < 60 or b["r"] > 1020: fails.append(f"MARGIN {tag}: {b['id']} ({b['kind']}) x {b['l']}-{b['r']} outside 60-1020")
            if b["b"] > 1500: fails.append(f"MARGIN {tag}: {b['id']} ({b['kind']}) bottom y={b['b']} (> 1500)")
        col = sorted([b for b in stage if b["kind"] not in ("note",)], key=lambda b: b["t"])
        for a, b in zip(col, col[1:]):
            if a["id"] == b["id"] or min(a["r"], b["r"]) - max(a["l"], b["l"]) < 40: continue        # an object and its own label are meant to sit close                      # not stacked (side by side)
            gap = b["t"] - a["b"]
            if 0 <= gap < 28: warns.append(f"TIGHT {tag}: {a['id']} -> {b['id']} gap {gap} px")
            if gap > 340: warns.append(f"LOOSE {tag}: {a['id']} -> {b['id']} gap {gap} px")
        if col:
            top, bot = min(b["t"] for b in col), max(b["b"] for b in col); c = (top + bot) / 2
            if c < 640 or c > 1040: warns.append(f"BALANCE {tag}: stage content centred at y={int(c)} (aim 700-1000)")
            if bot - top < 200: warns.append(f"BALANCE {tag}: stage content only {bot - top} px tall (sparse)")
mt = re.search(r'<pre id="__trans">(.*?)</pre>', r.stdout, re.S)
if mt:                                                                                        # cuts: old content leaving + new content arriving must never overlap (0.05-0.3 s after each cut)
    for sc in json.loads(H.unescape(mt.group(1))):
        for sm in sc["samples"]:
            B = sm["boxes"]
            for i, a in enumerate(B):
                for b in B[i + 1:]:
                    if a["id"] == b["id"] or a.get("ok") or b.get("ok"): continue
                    o = ov(a, b)
                    if o: fails.append(f"OVERLAP-AT-CUT scene {sc['i']} t={sm['t']}: {a['id']} ({a['kind']}) x {b['id']} ({b['kind']}) by {o[0]}x{o[1]} px (old and new content visible together)")
for x in sorted(set(fails)): print("  FAIL", x)
for x in sorted(set(warns)): print("  WARN", x)
print(("PASS" if not fails else "FAIL") + f" layout: {sum(len(s['samples']) for s in scenes)} samples over {len(scenes)} scenes; {len(set(fails))} fail, {len(set(warns))} warn")
if "--json" in sys.argv: json.dump(scenes, open(os.path.join(proj, "qa", "layout_boxes.json"), "w"))
sys.exit(1 if fails else 0)
