#!/usr/bin/env python3
"""Cover A/B stills for an explainer:  python3 -I make_cover.py <project_dir>
Reads meta.cover = {"a": {"t": 1.2, "lines": ["RARE CAR?", "HAR STREET PAR!"], "accent": 1, "kicker": "GTA 6 · ENGINEERING"}, "b": {...}} from scenes.json
(promise <= 8 words, line `accent` in the world's primary colour, the cover is a frame of the video itself at time t: A = the hero, B = a reveal frame).
Writes covers/cover_a.jpg, covers/cover_b.jpg (1080x1920) and covers/grid_check.png (3:4 feed crop y 240-1680 marked). Covers are separate uploads, never part of the video (reel-edit section 8)."""
import json, os, re, shutil, subprocess, sys
proj = os.path.abspath(sys.argv[1]); spec = json.load(open(os.path.join(proj, "scenes.json"), encoding="utf-8")); cov = spec.get("meta", {}).get("cover")
if not cov: sys.exit('add meta.cover to scenes.json: {"a": {"t": 1.2, "lines": ["...", "..."], "accent": 1, "kicker": "..."}, "b": {...}}')
html = open(os.path.join(proj, "index.html"), encoding="utf-8").read(); out = os.path.join(proj, "covers"); os.makedirs(out, exist_ok=True)
m = re.search(r"window\.EXPLAINER=(\{.*?\});</script>", html, re.S); data = json.loads(m.group(1))
for key in ("a", "b"):
    c = cov.get(key)
    if not c: continue
    if len(" ".join(c["lines"]).split()) > 8: print(f"WARNING cover {key}: {len(' '.join(c['lines']).split())} words (> 8): shorten the promise")
    tmp = os.path.join(proj, f"_cover_{key}"); shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    os.symlink(os.path.join(proj, "assets"), os.path.join(tmp, "assets"))
    d = json.loads(json.dumps(data)); d["meta"]["cover"] = c
    open(os.path.join(tmp, "index.html"), "w", encoding="utf-8").write(html[:m.start(1)] + json.dumps(d, ensure_ascii=False) + html[m.end(1):])
    for f in ("hyperframes.json", "meta.json", "package.json"): shutil.copy(os.path.join(proj, f), tmp)
    r = subprocess.run(["npx", "--yes", "hyperframes@0.8.209", "snapshot", "--at", str(c["t"]), "--no-end"], cwd=tmp, capture_output=True, text=True)
    png = re.findall(r"(\S+frame-\d+-at-[\d.]+s\.png)", r.stdout + r.stderr)
    if not png: sys.exit("snapshot failed:\n" + (r.stdout + r.stderr)[-600:])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", png[0], "-vf", "scale=1080:1920", "-q:v", "2", os.path.join(out, f"cover_{key}.jpg")], check=True); shutil.rmtree(tmp)
imgs = [os.path.join(out, f"cover_{k}.jpg") for k in ("a", "b") if os.path.exists(os.path.join(out, f"cover_{k}.jpg"))]
for k, p in enumerate(imgs):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", p, "-vf", "drawbox=x=0:y=240:w=1080:h=1440:c=lime@0.9:t=4,drawbox=x=0:y=0:w=1080:h=240:c=red@0.30:t=fill,drawbox=x=0:y=1680:w=1080:h=240:c=red@0.30:t=fill,scale=540:-2", os.path.join(out, f"_g{k}.png")], check=True)
if imgs:
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + sum([["-i", os.path.join(out, f"_g{k}.png")] for k in range(len(imgs))], []) + ["-filter_complex", f"hstack=inputs={len(imgs)}", os.path.join(out, "grid_check.png")], check=True)
    [os.remove(os.path.join(out, f"_g{k}.png")) for k in range(len(imgs))]
print("covers ->", out, "(lime box = 3:4 feed crop; red = cropped away)")
