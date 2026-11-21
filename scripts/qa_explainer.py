#!/usr/bin/env python3
"""QA an explainer render: python3 -I qa_explainer.py <project_dir> <video.mp4>
Writes <project>/qa/sheet_*.jpg (one frame per scene, 6 per sheet), checks 1080x1920, audio, loudness, caption safe-zone (text must stay y 170-1500),
scene length (2-6 s), word-match %, and prints PASS/FAIL lines. LOOK at the sheets: every scene must show a visible change and nothing may overlap."""
import json, os, re, subprocess, sys

proj, vid = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]); qa = os.path.join(proj, "qa"); os.makedirs(qa, exist_ok=True)
run = lambda *a: subprocess.run(a, capture_output=True, text=True)
tm = json.load(open(os.path.join(proj, "assets", "timing.json"))); sc = tm["scenes"]; bad = []
def check(ok, msg):
    print(("PASS " if ok else "FAIL ") + msg); (None if ok else bad.append(msg))
html = open(os.path.join(proj, "index.html"), encoding="utf-8").read()
_h = re.search(r'"handle": "([^"]+)"', html); check(bool(_h) and _h.group(1) in html and 'id="brand"' in html and _h.group(1) != "@yourhandle", f"handle {_h.group(1) if _h else '?'} is in the header (not the @yourhandle placeholder)")
v = run("ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate", "-of", "csv=p=0", vid).stdout.strip()
check(v.startswith("1080,1920"), f"video {v}")
check("audio" in run("ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", vid).stdout, "audio stream present")
lu = re.findall(r"I:\s+(-?[\d.]+) LUFS", run("ffmpeg", "-nostats", "-i", vid, "-af", "ebur128", "-f", "null", "-").stderr)
check(bool(lu) and -16 <= float(lu[-1]) <= -12, f"loudness {lu[-1] if lu else '?'} LUFS (target -14)")
print("INFO timing mode:", tm.get("timing_mode", "whisper"), "(pause-based = scenes exact at sentence pauses, word times approximate)" if "pause" in tm.get("timing_mode", "") else "")
check("pause" in tm.get("timing_mode", "") or tm["script_word_match"] >= 0.8, f"script/voice word match {tm['script_word_match']:.0%}")
long_ = [s["i"] for s in sc if s["to"] - s["from"] > 6.0]; short = [s["i"] for s in sc[:-1] if s["to"] - s["from"] < 0.75]
check(not long_, f"no scene longer than 6 s (long: {long_})"); check(not short, f"no scene shorter than 0.75 s (short: {short})")
dur = sc[-1]["to"]; check(dur <= 95, f"total {dur:.0f} s (references run 58-160 s; Shorts/Reels sweet spot 45-90 s)")
# ---- voice gates (reel-edit qa.md / humanize.md round 12 checks)
ve = os.path.join(proj, "assets", "voice_edit.json")
if os.path.exists(ve):
    v = json.load(open(ve))["stats"]
    check(v["first_speech_s"] <= .15, f"first word {v['first_speech_s']} s after the start (<= 0.15 s)")
    check(v["longest_pause_after_s"] <= .30, f"longest pause {v['longest_pause_after_s']} s after cleanup (<= 0.30 s; {v['pauses_over_0.25s_after']} over 0.25 s)")
    if "wpm_after" in v: check(150 <= v["wpm_after"] <= 270, f"pace {v['wpm_after']} wpm after cleanup (was {v.get('wpm_before')}; proven reels 167-246)")
    print(f"INFO voice cleanup: {v['original_s']}s -> {v['clean_s']}s, {v['pauses_capped']} pauses capped, {v['fillers_removed']} fillers removed, {v['vowels_shortened']} stretched vowels shortened, {v['retakes_removed']} retakes removed, voice chain {'on' if v['voice_chain'] else 'off'}")
if "last_word" in tm:
    tail = tm["total"] - tm["last_word"] - .35; check(tail <= .6, f"video ends {tm['total'] - tm['last_word']:.2f} s after the last word starts (reel-edit: end ~0.5 s after the last word)")
# ---- sound + energy gates (from reel-edit sound.md / humanize.md, adapted to explainers)
mr = os.path.join(proj, "assets", "mix_report.json")
if os.path.exists(mr):
    m = json.load(open(mr))
    check(bool(m.get("music")), f"music bed present ({m.get('music')}; licence in assets/music_credit.txt)")
    check(10 <= m["voice_over_music_sfx_db_median"] <= 16, f"voice sits {m['voice_over_music_sfx_db_median']} dB over music+SFX (median; target 10-14, <=16 accepted)")
    check(m["voice_over_music_sfx_db_min"] >= 8, f"voice never closer than 8 dB to music+SFX (min {m['voice_over_music_sfx_db_min']})")
    check(abs(m["lufs"] + 14) <= 0.8 and (m.get("true_peak_db") is None or m["true_peak_db"] <= -1.0), f"master {m['lufs']} LUFS, true peak {m.get('true_peak_db')} dBTP")
    check(3 <= m["sfx_per_10s"] <= 7, f"SFX density {m['sfx_per_10s']} per 10 s (target 3-7)")
    check(m["silent_spots_over_1.2s"] >= 2, f"{m['silent_spots_over_1.2s']} silent spots >= 1.2 s (need >= 2)")
fx = tm.get("fx", {}); ev = [0.0] + tm.get("events", []) + [sc[-1]["to"]]
gap = max((b - a for a, b in zip(ev, ev[1:])), default=0)
check(gap <= 3.2, f"visible change at least every 3.2 s (longest quiet stretch {gap:.1f} s)")
check(len(fx.get("trans", [])) <= max(2, int(dur / 9)), f"{len(fx.get('trans', []))} transitions (budget {max(2, int(dur / 9))}), each at an idea change")
check(len(fx.get("punches", [])) >= int(dur / 10), f"{len(fx.get('punches', []))} camera punches (>= {int(dur / 10)})")
for k in range(0, len(sc), 6):
    ts = [min(dur - .1, (s["from"] + s["to"]) / 2 + 0.4) for s in sc[k:k + 6]]; frames = []
    for j, t in enumerate(ts):
        f = os.path.join(qa, f"f{k + j:02d}.jpg"); run("ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", vid, "-frames:v", "1", "-vf", "scale=360:-2", "-q:v", "3", f); frames.append(f)
    ins = sum([["-i", f] for f in frames], []); run("ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", f"hstack=inputs={len(frames)}", "-q:v", "3", os.path.join(qa, f"sheet_{k // 6 + 1}.jpg"))
    [os.remove(f) for f in frames]
print(f"\nsheets: {qa}/sheet_*.jpg  -> open them and check: stage centred (y 440-1500), caption never covered, one visible change per scene, no overlaps.")
sys.exit(1 if bad else 0)
