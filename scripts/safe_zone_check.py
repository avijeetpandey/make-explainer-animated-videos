#!/usr/bin/env python3
"""Safe-zone gate (reel-edit safe_zone.sh zones): python3 -I safe_zone_check.py <project_dir> <video.mp4>
Instagram Reels / YouTube Shorts draw their own UI over: top 250 px, bottom 500 px (caption, username, audio), right 150 px (buttons), left 60 px.
The reference reels keep the header + caption row inside the top band and leave the bottom ~400 px empty: that is the accepted layout. This gate checks what is NOT accepted:
  FAIL  bright content below y 1500 (under Instagram's caption block)  |  FAIL  text/cards touching the right 90 px (x > 990)
  WARN  content in the right button strip x 930-990 (y 250-1500)       |  INFO  top-band content (header/caption: the reference layout)
Writes qa/safe_sheet.jpg: 12 frames with the app-UI zones shaded red and the safe box in green. Exit 1 on FAIL."""
import json, os, subprocess, sys
import numpy as np
proj, vid = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]); qa = os.path.join(proj, "qa"); os.makedirs(os.path.join(qa, "_sz"), exist_ok=True)
tm = json.load(open(os.path.join(proj, "assets", "timing.json"))); sc = tm["scenes"]
ts = sorted({round((s["from"] + s["to"]) / 2 + .35, 2) for s in sc})[:40]; bad, warn, info = [], [], []
for i, t in enumerate(ts):
    f = os.path.join(qa, "_sz", f"f{i:02d}.png"); subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(min(t, tm["total"] - .1)), "-i", vid, "-frames:v", "1", f], check=True)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-vf", "scale=1080:1920,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    g = np.frombuffer(raw, np.uint8).reshape(1920, 1080); br = (g < 70) if np.median(g) > 140 else (g > 150)        # light (cream) scene: dark ink is the content; dark scenes: only near-white content counts, coloured aurora glows do not
    zones = {"bottom (y>1500)": br[1500:, :], "far-right (x>990)": br[250:1500, 990:], "button strip (x 930-990)": br[250:1500, 930:990]}
    for k, z in zones.items():
        n = int(z.sum())
        if n > 260 and k.startswith("bottom"): bad.append(f"t={t}s {k}: {n} bright px")
        elif n > 260 and k.startswith("far"): bad.append(f"t={t}s {k}: {n} bright px (card/text touching the edge)")
        elif n > 260: warn.append(f"t={t}s {k}: {n} bright px")
    if br[:250].sum() > 800: info.append(t)
for k in range(0, len(ts), 1):
    pass
vf = "drawbox=x=0:y=0:w=iw:h=250:c=red@0.35:t=fill,drawbox=x=0:y=ih-500:w=iw:h=500:c=red@0.35:t=fill,drawbox=x=iw-150:y=250:w=150:h=ih-750:c=red@0.35:t=fill,drawbox=x=0:y=250:w=60:h=ih-750:c=red@0.25:t=fill,drawbox=x=60:y=250:w=870:h=1170:c=lime@0.9:t=3,scale=270:480"
sel = [os.path.join(qa, "_sz", f"f{i:02d}.png") for i in np.linspace(0, len(ts) - 1, min(12, len(ts))).astype(int)]
for j, f in enumerate(sel): subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f, "-vf", vf, os.path.join(qa, "_sz", f"s{j:02d}.png")], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "1", "-i", os.path.join(qa, "_sz", "s%02d.png"), "-vf", "tile=6x2:padding=4", "-frames:v", "1", os.path.join(qa, "safe_sheet.jpg")], check=True)
import shutil; shutil.rmtree(os.path.join(qa, "_sz"), ignore_errors=True)
print(("PASS" if not bad else "FAIL") + f" safe zone: {len(ts)} frames checked; {len(bad)} fail, {len(warn)} warn")
[print("  FAIL", x) for x in bad[:8]]; [print("  WARN", x) for x in warn[:6]]
print(f"  INFO header/caption occupy the top 250 px in {len(info)} of {len(ts)} frames (reference-reel layout, accepted). Sheet: {os.path.join(qa, 'safe_sheet.jpg')} (red = app UI, green = safe box)")
sys.exit(1 if bad else 0)
