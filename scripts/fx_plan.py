#!/usr/bin/env python3
"""Edit plan for an explainer: camera punches, transitions, impact rings, and the SFX cue list.
Rules are adapted from the reel-edit pipeline (humanize.md / variety.md / sound.md) to a faceless explainer:
  - transitions only where the IDEA changes (hero shape changes or the stage is mostly replaced), >= 5 s apart, none in the first 3 s / last 4 s, never the same type twice in a row, each with its own sound 40-140 ms early
  - camera punches only on words that carry the idea (numbers, negations, the first key word of a scene), >= 1.4 s apart, never right at a transition, ~2 per 10 s, every 3rd with a handheld shake
  - fill_gaps: nothing visible for > 2.8 s gets a small punch (the "visible change every <= 3 s" rule)
  - sound: every visual event has one sound, none without an event, a sound every 1.5-3 s on average, never two within 0.3 s, the sentence before the CTA stays silent,
    one riser -> hit build (max one per reel) with 120 ms of silence before the hit, SFX volumes 0.12-0.36 (always under the voice)
"""
import re

NEG = {"nahi", "not", "never", "bug", "crash", "stutter", "dangerous", "delete", "fail", "galat", "expensive", "spikes", "bhool", "slow", "problem", "down"}
norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
TYPES = ["whip_h", "blur_in", "whip_v", "push"]


def _ids(scenes, els):
    out = [set() for _ in scenes]
    for e in els:
        for a, b in e["wins"]:
            for i, s in enumerate(scenes):
                if s["from"] >= a - .01 and s["to"] <= b + .01: out[i].add(e["id"])
    return out


def plan_fx(scenes, els, total, beats, reel, types=None, punch=1.0):
    TY = types or TYPES
    stamps = [e["ats"][0] for e in els if e["type"] == "stamp"] + [s["from"] + .12 for s in scenes if s.get("shock")]
    ids = _ids(scenes, els); trans = []; last = -9.0; k = sum(map(ord, reel)) % 4; maxn = max(2, int(total / 9))
    for i in range(1, len(scenes)):
        a, b = scenes[i - 1], scenes[i]; sa, sb = (a.get("hero") or {}).get("shape"), (b.get("hero") or {}).get("shape")
        change = ((sa or sb) and sa != sb) or len(ids[i - 1] & ids[i]) / max(1, len(ids[i - 1] | ids[i])) < .5
        t = b["from"]
        if not change or t < 3.0 or t > total - 4.0 or t - last < 5.0 or len(trans) >= maxn or any(0 <= x - t <= 1.0 for x in stamps): continue
        trans.append({"t": round(t, 2), "type": TY[k % len(TY)], "dir": 1 if len(trans) % 2 == 0 else -1, "i": i}); k += 1; last = t
    cands = []
    for s in scenes:
        keys = [(w["t"], w["txt"]) for w in s["words"] if w["key"]]
        sc = sorted(((3 if re.search(r"\d", tx) else 0) + (2 if norm(tx) in NEG else 0) + (1 if j == 0 else 0), t, tx) for j, (t, tx) in enumerate(keys))
        cands += sorted(sc, key=lambda x: (-x[0], x[1]))[:2]
    cands.sort(key=lambda x: (-x[0], x[1])); punches = []; cap = max(3, int(total / 10 * 2.4))
    for sc, t, tx in cands:
        if t < .9 or t > total - 1.2 or len(punches) >= cap: continue
        if any(abs(t - p["t"]) < 1.4 for p in punches) or any(-.2 <= t - tr["t"] <= .5 for tr in trans): continue
        punches.append({"t": t, "amt": round((.09 if sc >= 2 else .065) * punch, 3), "shake": False, "w": tx})
    allw = [(w["t"], w["txt"]) for s in scenes for w in s["words"]]
    def events(): return sorted([s["from"] for s in scenes] + [x for e in els for x in e["ats"]] + [p["t"] for p in punches] + [tr["t"] for tr in trans] + [0.0, total])
    for _ in range(12):                                                       # fill_gaps
        ev = events(); gaps = [(b - a, a, b) for a, b in zip(ev, ev[1:]) if b - a > 2.8]
        if not gaps: break
        _, a, b = max(gaps); mid = (a + b) / 2
        cand = [w for w in allw if a + .8 < w[0] < b - .5 and not any(abs(w[0] - p["t"]) < .8 for p in punches)]
        if not cand: break
        t, tx = min(cand, key=lambda w: abs(w[0] - mid)); punches.append({"t": t, "amt": round(.05 * punch, 3), "shake": False, "w": tx})
    punches.sort(key=lambda p: p["t"])
    for p in punches:                                                         # snap to a beat only if it sits <= 120 ms before the word (speech wins)
        b = [x for x in beats if 0 <= p["t"] - x <= .12]
        if b: p["t"] = b[-1]
        p["t"] = round(p["t"], 2)
    for j, p in enumerate(punches): p["shake"] = (j % 3 == 2)
    shocks = []
    for e in els:
        if e["type"] == "stamp":
            f = e["frames"][0]; shocks.append({"t": round(e["ats"][0], 2), "x": f.get("x", 540), "y": f.get("y", 900), "tone": e.get("tone") or "red"})
    for s in scenes:                                                          # scene-level "shock": true = impact ring on a big reveal
        if s.get("shock"): h = s.get("hero") or {}; shocks.append({"t": round(s["from"] + .12, 2), "x": 540, "y": 900 + h.get("y", 0), "tone": h.get("tone", "white"), "scene": True})
    return {"trans": trans, "punches": punches, "shocks": shocks}


def plan_cues(scenes, els, fx, total, reel):
    """-> [{role, t, vol, prio, max_dur?}] after thinning. Roles map to files in audio_lib.pick_sfx (shared library) or the synthetic fallback."""
    c = [{"role": "impact", "t": 0.0, "vol": .26, "prio": 9, "max_dur": 1.0}]
    trt = {tr["t"] for tr in fx["trans"]}
    for tr in fx["trans"]: c.append({"role": "whip", "t": tr["t"] - .14, "vol": .34, "prio": 10, "max_dur": .9})
    for i, s in enumerate(scenes):
        if i and round(s["from"], 2) not in trt: c.append({"role": "hit_soft", "t": s["from"] - .04, "vol": .2, "prio": 3, "max_dur": .8})
    for p in fx["punches"]:
        if p["shake"]: c.append({"role": "hit_soft", "t": p["t"] - .03, "vol": .22, "prio": 4, "max_dur": .8})
    risered = False
    for sk in fx["shocks"]:
        if sk.get("scene"): c.append({"role": "impact", "t": sk["t"] - .04, "vol": .22, "prio": 8, "max_dur": 1.0})
    for e in els:
        ty, at, tone = e["type"], round(e["ats"][0], 2), (e.get("tone") or ((e["frames"][0].get("tone")) or ""))
        if ty in ("obj", "gl"): c.append({"role": "pop", "t": at - .03, "vol": .24, "prio": 5, "max_dur": .6})
        elif ty in ("chip", "packet"):
            role = "negation" if tone == "red" else "success" if tone == "green" and ty == "chip" else "click"
            c.append({"role": role, "t": at - .02, "vol": .2, "prio": 5, "max_dur": .7})
        elif ty in ("card", "list", "compare", "search", "bars", "cells", "rows", "pill"): c.append({"role": "click", "t": at - .02, "vol": .2, "prio": 4, "max_dur": .6})
        elif ty == "big": c.append({"role": "pop", "t": at - .03, "vol": .26, "prio": 5, "max_dur": .6})
        elif ty == "counter":
            n = int(min(3, (e.get("dur") or 1.6) / .5)); c += [{"role": "tick", "t": at + .45 * j, "vol": .14, "prio": 2, "max_dur": .3} for j in range(n)]
        elif ty == "stamp":
            if not risered: c.append({"role": "riser", "t": at - 1.0, "vol": .26, "prio": 8, "max_dur": .9, "end_at": at - .12}); risered = True
            c.append({"role": "impact" if tone not in ("green",) else "success", "t": at - .04, "vol": .28, "prio": 9, "max_dur": 1.0})
        elif ty == "cta":
            c.append({"role": "notif", "t": at, "vol": .26, "prio": 7, "max_dur": 1.0}); c.append({"role": "success", "t": at + .8, "vol": .2, "prio": 5, "max_dur": 1.0})
    quiet = (scenes[-2]["from"] + .5, scenes[-2]["to"]) if len(scenes) > 2 else None      # the sentence before the CTA stays silent
    out = []
    for x in sorted(c, key=lambda x: (-x["prio"], x["t"])):
        if x["t"] < 0 or x["t"] > total - 1.0: continue
        if quiet and quiet[0] <= x["t"] < quiet[1]: continue
        if any(abs(x["t"] - y["t"]) < (.18 if x["role"] == "whip" or y["role"] == "whip" else .3) for y in out): continue
        out.append(x)
    cap = int(total / 10 * 6.0)                                                # density ceiling: a sound every >= 1.7 s on average; drop the least important first
    while len(out) > cap:
        out.remove(min((x for x in out if x["prio"] < 7), key=lambda x: (x["prio"], x["t"]), default=out[-1]))
    return sorted(out, key=lambda x: x["t"])
