#!/usr/bin/env python3
"""Voice cleanup for an explainer voice-over: silence trimming, breath + filler removal, stretched-vowel shortening, level matching, the reel-edit voice chain.

  python3 -I clean_voice.py <project_dir> [--words N] [--no-chain] [--sentence-gap 0.22] [--phrase-gap 0.12] [--tail 0.45]

Reads  <project>/voice.<ext>   (the original is never touched)
Writes <project>/voice_clean.wav (48 kHz mono) + <project>/assets/voice_edit.json (the edit list: kept segments, every removed span + reason, stats).
`build_explainer.py` runs this automatically (unless meta.voice_clean is false), uses voice_clean.wav, and re-maps words_override.json through the edit list.

Rules (from reel-edit: SKILL.md §2, qa.md, variety.md §5, make_cut.py):
  - first word <= ~0.1 s after the start (pad 0.04-0.06 s before it), end <= 0.45 s after the last word (pad 0.06-0.08 s after each phrase)
  - pauses: sentence gaps (>= 0.30 s) capped at 0.22 s, phrase gaps (0.12-0.30 s) capped at 0.12 s, anything shorter untouched. The cut is taken from the MIDDLE of the gap so the room tone at both ends stays (no dead digital silence), and breaths inside the gap go with it.
  - fillers (um / uh / ahh / hmm): a sustained steady vowel (voiced, very low spectral change, low zero-crossing) >= 0.16 s. Standalone ones are deleted; one inside a word is a drawn-out vowel and is shortened to ~0.09 s (a steady vowel cuts cleanly).
  - retakes: with word timings, a repeated 2-word phrase back-to-back keeps only the last attempt.
  - level matching: every speech island is nudged (+/-3 dB) toward the median level, so parts recorded at different distances sit together.
  - voice chain (reel-edit make_cut.py VOICE): highpass 80, afftdn nr 12, -2.5 dB @220 Hz, +3 dB @3.2 kHz, treble +1.5, deesser, compressor 3:1. Skipped with --no-chain.
Needs only numpy + ffmpeg.
"""
import json, os, subprocess, sys
import numpy as np

SR = 48000; AR = 16000; HOP = .01
VOICE_CHAIN = "highpass=f=80,afftdn=nr=12:nf=-45,equalizer=f=220:t=q:w=1.2:g=-2.5,equalizer=f=3200:t=q:w=1:g=3,treble=g=1.5:f=8000,deesser=i=0.4,acompressor=threshold=-20dB:ratio=3:attack=10:release=150:makeup=2"


def run(*a): return subprocess.run(a, capture_output=True, text=True)


def load(path, sr, ch=1):
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", str(ch), "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
    return np.frombuffer(p.stdout, np.float32).astype(np.float64)


def features(x):
    """10 ms hop: energy dB, spectral change (flux), voicing, zero-crossing rate."""
    win, hop = int(.025 * AR), int(HOP * AR); n = (len(x) - win) // hop
    fr = np.stack([x[i * hop:i * hop + win] * np.hanning(win) for i in range(n)])
    S = np.abs(np.fft.rfft(fr, 512)) ** 2
    mel = lambda h: 2595 * np.log10(1 + h / 700); imel = lambda m: 700 * (10 ** (m / 2595) - 1)
    pts = imel(np.linspace(mel(60), mel(7600), 42)); bins = np.floor(513 * pts / AR).astype(int); fb = np.zeros((40, 257))
    for i in range(40):
        a, b, c = bins[i], bins[i + 1], bins[i + 2]
        fb[i, a:b] = (np.arange(a, b) - a) / max(1, b - a); fb[i, b:c] = (c - np.arange(b, c)) / max(1, c - b)
    L = np.log(S @ fb.T + 1e-10); flux = np.r_[0, np.abs(np.diff(L, axis=0)).mean(1)]
    e = 10 * np.log10(S.sum(1) + 1e-12); zcr = (np.abs(np.diff(np.sign(fr), axis=1)) > 0).mean(1)
    lo, hi = int(AR / 400), int(AR / 70); voi = np.zeros(n)
    for i in range(n):
        ac = np.correlate(fr[i], fr[i], "full")[win - 1:]
        if ac[0] > 0: voi[i] = ac[lo:hi].max() / ac[0]
    return e, np.convolve(flux, np.ones(5) / 5, "same"), voi, zcr


def runs(mask, min_len):
    out, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]: j += 1
            if (j - i) * HOP >= min_len: out.append((i * HOP, j * HOP))
            i = j
        else: i += 1
    return out


def islands(voiced, merge=.10, min_len=.08):
    segs = runs(voiced, 0.0); m = []
    for a, b in segs:
        if m and a - m[-1][1] < merge: m[-1] = (m[-1][0], b)
        else: m.append((a, b))
    return [s for s in m if s[1] - s[0] >= min_len]


def speech_islands(path, merge=.10):
    """Adaptive speech islands (noise floor + 14 dB, merged across gaps < merge s): robust to the raised noise floor after denoising, unlike a fixed dB silence threshold."""
    x = load(path, AR); e, _, _, _ = features(x); floor = np.percentile(e, 10); act = e > floor + 14
    return islands(np.convolve(act.astype(float), np.ones(3) / 3, "same") > .5, merge)


def clean(proj, n_words=None, chain=True, sentence_gap=.22, phrase_gap=.12, tail=.45, words=None):
    voice = next((os.path.join(proj, f) for f in sorted(os.listdir(proj)) if f.startswith("voice.") and not f.endswith(".json")), None)
    if not voice: sys.exit("no voice.<ext> in the project folder")
    x48 = load(voice, SR); x16 = load(voice, AR); dur = len(x48) / SR
    e, flux, voi, zcr = features(x16); n = len(e); floor = np.percentile(e, 10)
    act = e > floor + 14; voiced = np.convolve(act.astype(float), np.ones(3) / 3, "same") > .5
    removed = []
    # ---- fillers / drawn-out vowels
    thr = np.percentile(flux[act], 22) if act.any() else 0
    sus = runs((flux < thr) & (voi > .55) & act & (zcr < .15), .16)
    isl0 = islands(voiced)
    wlist = words or []
    cuts = []                                                                # (a, b, type) spans deleted INSIDE an island
    for a, b in sus:
        inw = [w for w in wlist if w[0] - .03 <= a and b <= w[1] + .03] if wlist else None
        standalone = (not any(w[0] < b and w[1] > a for w in wlist)) if wlist else any(abs(a - s) < .12 or abs(b - e2) < .12 for s, e2 in isl0)
        if standalone:
            voiced[int(a / HOP):int(b / HOP)] = False; removed.append({"type": "filler", "src": [round(a, 2), round(b, 2)], "why": "steady vowel outside any word (um/uh/ahh)"})
        elif b - a >= .17:
            ka, kb = a + .05, b - .04
            if kb - ka > .06: cuts.append((ka, kb)); removed.append({"type": "elongation", "src": [round(ka, 2), round(kb, 2)], "why": f"drawn-out vowel {b - a:.2f}s shortened to ~0.09s"})
    # ---- retakes (needs word timings): a 2-word phrase immediately repeated keeps the last attempt
    nz = lambda t: "".join(ch for ch in t.lower() if ch.isalnum())
    i = 0
    while wlist and i + 3 < len(wlist):
        if [nz(w[2]) for w in wlist[i:i + 2]] == [nz(w[2]) for w in wlist[i + 2:i + 4]] and wlist[i + 2][0] - wlist[i + 1][1] < .8:
            a, b = wlist[i][0] - .03, wlist[i + 2][0] - .03; voiced[int(a / HOP):int(b / HOP)] = False
            removed.append({"type": "retake", "src": [round(a, 2), round(b, 2)], "why": f'repeated "{wlist[i][2]} {wlist[i + 1][2]}"'}); i += 4
        else: i += 1
    isl = islands(voiced)
    if not isl: sys.exit("no speech found")
    # ---- keep list: islands with pads, gaps capped from the middle
    pad_b = .05
    first_word = isl[0][0]; start = max(0.0, isl[0][0] - pad_b); keep = []
    for k, (a_, b_) in enumerate(isl[:-1]):
        nxt = isl[k + 1][0]; gap = nxt - b_
        cap = sentence_gap if gap >= .30 else phrase_gap if gap >= .12 else None
        if cap is not None and gap > cap + .02:
            half = cap / 2; removed.append({"type": "pause", "src": [round(b_ + half, 2), round(nxt - half, 2)], "why": f"gap {gap:.2f}s capped to {cap:.2f}s"})
            keep.append([start, b_ + half]); start = nxt - half
    keep.append([start, min(dur, isl[-1][1] + tail)])
    # merge touching/overlapping segments (uncapped gaps stay inside one segment)
    merged = []
    for a, b in sorted(keep):
        if merged and a <= merged[-1][1] + 1e-3: merged[-1][1] = max(merged[-1][1], b)
        else: merged.append([a, b])
    # split merged segments at the in-word shortening cuts
    segs = []
    for a, b in merged:
        pts = [a]; pieces = []
        for ca, cb in sorted(c for c in cuts if a <= c[0] and c[1] <= b): pieces.append((pts[-1], ca)); pts.append(cb)
        pieces.append((pts[-1], b)); segs += [list(p) for p in pieces if p[1] - p[0] > .02]
    # ---- level matching per island (+/-3 dB toward the median)
    ie = []
    for a, b in isl:
        m = voiced[int(a / HOP):int(b / HOP)]; ee = e[int(a / HOP):int(b / HOP)][m] if m.any() else np.array([floor]); ie.append(np.mean(ee))
    med = np.median(ie)
    gains = np.interp(np.arange(int(dur * SR)) / SR, [t for ab in isl for t in (ab[0] - .1, ab[1] + .1)], [10 ** (np.clip(med - v, -3, 3) / 20) for v in ie for _ in (0, 1)])
    # ---- assemble with 12 ms crossfades
    xf = int(.012 * SR); out = np.zeros(0); edl = []; pos = 0
    for a, b in segs:
        s0, s1 = int(a * SR), int(b * SR); seg = (x48[s0:s1] * gains[s0:s1]).copy()
        if len(seg) <= 2 * xf: continue
        if len(out):
            ramp = np.linspace(0, 1, xf); out[-xf:] = out[-xf:] * (1 - ramp) + seg[:xf] * ramp; out = np.r_[out, seg[xf:]]; o0 = (len(out) - len(seg[xf:])) / SR - xf / SR
        else: seg[:xf] *= np.linspace(0, 1, xf); out = seg; o0 = 0.0
        edl.append({"src": [round(a, 4), round(b, 4)], "out": [round(o0, 4), round(o0 + (b - a), 4)]})
    out[-int(.03 * SR):] *= np.linspace(1, 0, int(.03 * SR))
    tmp = os.path.join(proj, "_voice_raw_clean.wav"); import wave
    w = wave.open(tmp, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(out, -1, 1) * 32767).astype("<i2").tobytes()); w.close()
    dst = os.path.join(proj, "voice_clean.wav")
    r = run("ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", VOICE_CHAIN if chain else "anull", "-ar", str(SR), "-ac", "1", dst); os.remove(tmp)
    if r.returncode: sys.exit("ffmpeg voice chain failed: " + r.stderr[-300:])
    newdur = len(out) / SR; os.makedirs(os.path.join(proj, "assets"), exist_ok=True)
    sd = run("ffmpeg", "-nostats", "-i", dst, "-af", "silencedetect=noise=-38dB:d=0.08", "-f", "null", "-").stderr
    import re as _re; ss = [float(v) for v in _re.findall(r"silence_start: (-?[\d.]+)", sd)]; se = [float(v) for v in _re.findall(r"silence_end: ([\d.]+)", sd)]
    inner = [e_ - s_ for s_, e_ in zip(ss, se) if s_ > .2 and e_ < newdur - .3]
    st = {"original_s": round(dur, 2), "clean_s": round(newdur, 2), "removed_s": round(dur - newdur, 2), "pauses_capped": sum(1 for r_ in removed if r_["type"] == "pause"), "fillers_removed": sum(1 for r_ in removed if r_["type"] == "filler"),
          "vowels_shortened": sum(1 for r_ in removed if r_["type"] == "elongation"), "retakes_removed": sum(1 for r_ in removed if r_["type"] == "retake"), "first_speech_s": round(first_word - edl[0]["src"][0], 2),
          "tail_after_speech_s": round(edl[-1]["src"][1] - isl[-1][1], 2), "longest_pause_after_s": round(max(inner), 2) if inner else 0.0, "pauses_over_0.25s_after": sum(1 for v in inner if v > .25), "level_match_db": [round(float(med - v), 1) for v in ie], "voice_chain": bool(chain), "noise_floor_db": round(float(floor), 1)}
    if n_words: st["wpm_before"] = round(n_words / (isl[-1][1] - isl[0][0]) * 60); st["wpm_after"] = round(n_words / max(1, (newdur - st["first_speech_s"] - st["tail_after_speech_s"])) * 60)
    json.dump({"segments": edl, "removed": removed, "stats": st, "xf": .012}, open(os.path.join(proj, "assets", "voice_edit.json"), "w"), indent=1)
    return st, removed


def remap(t, edl):
    """source time -> cleaned time (a time inside a removed span snaps to the start of the next kept segment)."""
    for s in edl["segments"]:
        if s["src"][0] - 1e-6 <= t <= s["src"][1] + 1e-6: return round(s["out"][0] + (t - s["src"][0]), 3)
    nxt = [s for s in edl["segments"] if s["src"][0] > t]
    return round(nxt[0]["out"][0], 3) if nxt else round(edl["segments"][-1]["out"][1], 3)


def remap_words(words, edl):
    out = []
    for a, b, tx in words:
        if not any(s["src"][0] - 1e-6 <= a <= s["src"][1] + 1e-6 for s in edl["segments"]): continue          # word fell in a removed span
        out.append([remap(a, edl), max(remap(a, edl) + .02, remap(b, edl)), tx])
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(__doc__)
    proj = os.path.abspath(sys.argv[1]); arg = lambda k, d: float(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
    ov = os.path.join(proj, "words_override.json"); words = json.load(open(ov)) if os.path.exists(ov) else None
    st, removed = clean(proj, int(arg("--words", len(words) if words else 0)) or None, "--no-chain" not in sys.argv, arg("--sentence-gap", .22), arg("--phrase-gap", .12), arg("--tail", .45), words)
    print(json.dumps(st, indent=1)); [print(f"  {r['type']:10s} {r['src'][0]:6.2f}-{r['src'][1]:6.2f}  {r['why']}") for r in removed]
