#!/usr/bin/env python3
"""Subtitles for YouTube/Instagram from the captions the engine shows:  python3 -I make_srt.py <project_dir> [out.srt]
Cues of 3-7 words, broken at punctuation, timed to the spoken words (assets/captions.json written by build_explainer.py).
The .srt mirrors the spoken Hinglish; it is the only text allowed to differ from the English-only metadata rule (reel-edit SKILL.md section 9)."""
import json, os, re, sys
proj = os.path.abspath(sys.argv[1]); c = json.load(open(os.path.join(proj, "assets", "captions.json")))
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(proj, "renders", os.path.basename(proj) + ".srt")
ws = [(w["t"], w["txt"]) for s in c["scenes"] for w in s["words"]]
fmt = lambda t: "%02d:%02d:%02d,%03d" % (int(t // 3600), int(t // 60) % 60, int(t) % 60, round((t - int(t)) * 1000) % 1000)
cues, cur = [], []
for i, (t, w) in enumerate(ws):
    cur.append((t, w))
    if (re.search(r"[.,?!:;]$", w) and len(cur) >= 3) or len(cur) >= 7 or i == len(ws) - 1: cues.append(cur); cur = []
os.makedirs(os.path.dirname(out), exist_ok=True); lines = []
for k, q in enumerate(cues):
    end = ws[ws.index(q[-1]) + 1][0] - .02 if ws.index(q[-1]) + 1 < len(ws) else min(c["total"], q[-1][0] + .6)
    end = min(end, q[-1][0] + 1.2)
    lines.append(f"{k + 1}\n{fmt(q[0][0])} --> {fmt(max(end, q[0][0] + .3))}\n{' '.join(x[1] for x in q)}\n")
open(out, "w", encoding="utf-8").write("\n".join(lines)); print(f"{len(cues)} cues -> {out}")
