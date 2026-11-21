#!/usr/bin/env python3
"""LinkedIn image (1080x1350, 4:5) in the video's own look:
  python3 -I make_linkedin_image.py <project_dir> --kicker "OBJECT POOLING" --headline "Don't *create*. Reuse." --points "Create once at load|Reuse instead of delete|Reset state on every reuse"
`*word*` in the headline takes the world's primary colour. World + handle come from scenes.json / config. Output: <project>/linkedin_image.png (rendered with HyperFrames snapshot, so no browser path to configure)."""
import argparse, json, os, re, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); SKILL = os.path.dirname(HERE)
ap = argparse.ArgumentParser(); ap.add_argument("proj"); ap.add_argument("--kicker", required=True); ap.add_argument("--headline", required=True); ap.add_argument("--points", required=True); ap.add_argument("--world")
a = ap.parse_args(); proj = os.path.abspath(a.proj)
meta = json.load(open(os.path.join(proj, "scenes.json"), encoding="utf-8")).get("meta", {}) if os.path.exists(os.path.join(proj, "scenes.json")) else {}
worlds = json.load(open(os.path.join(SKILL, "assets", "worlds.json"))); w = worlds.get(a.world or meta.get("world")) or worlds["mono_pulse"]; T = w["tones"]
sys.path.insert(0, HERE); import config; handle = meta.get("handle") or config.get("handle", "@yourhandle")
hl = re.sub(r"\*([^*]+)\*", r'<span class="k">\1</span>', a.headline); pts = "".join(f'<div class="p"><i>{i + 1:02d}</i><span>{p.strip()}</span></div>' for i, p in enumerate(a.points.split("|")))
tmp = os.path.join(proj, "_li"); shutil.rmtree(tmp, ignore_errors=True); os.makedirs(os.path.join(tmp, "assets", "fonts"))
for f in os.listdir(os.path.join(SKILL, "assets", "fonts")):
    if f.endswith(".ttf"): shutil.copy(os.path.join(SKILL, "assets", "fonts", f), os.path.join(tmp, "assets", "fonts", f))
html = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=1080, height=1350"><style>
@font-face{{font-family:"Hanken Grotesk";src:url("assets/fonts/HankenGrotesk.ttf");font-weight:100 900}}@font-face{{font-family:"JetBrains Mono";src:url("assets/fonts/JetBrainsMono.ttf");font-weight:100 800}}
html,body{{margin:0;background:{w['bg']}}}#root{{position:relative;width:1080px;height:1350px;overflow:hidden;background:radial-gradient(ellipse 80% 45% at 50% 38%,{w['glow']},transparent 70%),{w['bg']};color:{T['white']};font-family:"Hanken Grotesk",sans-serif}}
.k{{color:{T['blue']}}}.top{{position:absolute;left:80px;right:80px;top:74px;display:flex;justify-content:space-between;font:600 26px "JetBrains Mono",monospace;letter-spacing:.2em;color:#9aa0aa;text-transform:uppercase}}
.kick{{position:absolute;left:80px;top:230px;font:600 32px "JetBrains Mono",monospace;letter-spacing:.24em;color:{T['blue']}}}.h{{position:absolute;left:80px;right:80px;top:300px;font-weight:800;font-size:150px;line-height:150px;letter-spacing:-.03em}}
.ps{{position:absolute;left:80px;right:80px;top:700px}}.p{{display:flex;align-items:center;gap:34px;height:150px;border-top:2px solid rgba(255,255,255,.14);font-weight:600;font-size:52px}}.p i{{font:600 30px "JetBrains Mono",monospace;font-style:normal;color:{T['blue']};letter-spacing:.1em}}
.foot{{position:absolute;left:80px;right:80px;bottom:70px;font:600 28px "JetBrains Mono",monospace;letter-spacing:.18em;color:#9aa0aa}}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="1" data-width="1080" data-height="1350"><div class="top"><span>{handle}</span><span>{meta.get('series', '')}</span></div><div class="kick">{a.kicker}</div><div class="h">{hl}</div><div class="ps">{pts}</div><div class="foot">{handle}</div></div></body></html>"""
open(os.path.join(tmp, "index.html"), "w", encoding="utf-8").write(html)
for f, body in {"hyperframes.json": {"$schema": "https://hyperframes.heygen.com/schema/hyperframes.json", "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}}, "meta.json": {"id": "li", "name": "li"}, "package.json": {"name": "li", "private": True, "type": "module"}}.items(): json.dump(body, open(os.path.join(tmp, f), "w"))
r = subprocess.run(["npx", "--yes", "hyperframes@0.8.209", "snapshot", "--at", "0.2", "--no-end"], cwd=tmp, capture_output=True, text=True); png = re.findall(r"(\S+frame-\d+-at-[\d.]+s\.png)", r.stdout + r.stderr)
if not png: sys.exit("snapshot failed:\n" + (r.stdout + r.stderr)[-500:])
shutil.copy(png[0], os.path.join(proj, "linkedin_image.png")); shutil.rmtree(tmp); print("->", os.path.join(proj, "linkedin_image.png"))
