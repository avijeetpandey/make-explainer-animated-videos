#!/usr/bin/env python3
"""Master the audio of an explainer: voice + music bed + SFX -> assets/audio/master.wav  (48 kHz stereo, -14 LUFS, TP <= -1.5 dBTP).

  python3 -I mix_audio.py <project_dir> [--target 12]

Priority one is the VOICE: it is never filtered or ducked (only measured). The music is ducked a little under speech (sidechain-style carve, ~6.5 dB, 15 ms attack / 1 s release (holds through short pauses, swells only in real gaps)),
then its level is SOLVED so that, per second of speech, the voice sits `target` dB (default 12; band 10-14, minimum >= 9) above music + SFX (reel-edit sound.md / balance.py rule).
Music: full energy from second 1 (trimmed to a bar-aligned start), 0.25 s fade-in, lift x1.3 under the CTA, fades out with the last word (no tail).
SFX: each file peak-levelled to -10 dBFS, then x vol, 8 ms fade-in / 40 ms fade-out, light shared-room reverb (10% wet) so they sit in one space.
Reads  assets/audio_plan.json  (written by build_explainer.py). Writes assets/audio/master.wav + assets/mix_report.json.
"""
import json, os, subprocess, sys
import numpy as np

SR = 48000
proj = os.path.abspath(sys.argv[1]); A = os.path.join(proj, "assets")
target = float(sys.argv[sys.argv.index("--target") + 1]) if "--target" in sys.argv else 12.0
plan = json.load(open(os.path.join(A, "audio_plan.json"))); total = plan["total"]; n = int(total * SR)


def load(path, ch=2):
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"], capture_output=True)
    a = np.frombuffer(p.stdout, np.float32).astype(np.float64)
    return a.reshape(-1, ch) if ch > 1 else a


def fit(a, n):
    out = np.zeros((n,) + a.shape[1:]); m = min(n, len(a)); out[:m] = a[:m]; return out


def ramp(n_, a, b): return np.linspace(a, b, max(1, n_))


# ---- voice (untouched)
V = fit(load(os.path.join(A, "audio", "voice.wav"), 1), n)
# ---- music
M = None; mus = plan.get("music")
if mus and os.path.exists(os.path.join(proj, mus["path"])):
    M = fit(load(os.path.join(proj, mus["path"]), 2), n)
    # bed leveling: a slow (1.5 s) compressor so a track's loud section never climbs over the voice (and its quiet part never vanishes)
    mm = M.mean(1); kk = SR // 100; pe = (mm[: (n // kk) * kk].reshape(-1, kk) ** 2).mean(1); sl = np.sqrt(np.convolve(pe, np.ones(150) / 150, "same") + 1e-12); rf = np.median(sl[sl > 1e-4]) if (sl > 1e-4).any() else 1.0
    lev = np.clip(rf / np.maximum(sl, 1e-6), .45, 2.2) ** .85; M = M * np.interp(np.arange(n) / SR, np.arange(len(lev)) / 100, lev)[:, None]
    g_t = np.ones(n); fi = int(.25 * SR); g_t[:fi] = ramp(fi, 0, 1)
    lift_at = int(plan.get("cta_t", total) * SR); g_t[lift_at:] *= 1.3                       # lifts under the CTA question
    fo0 = int(max(0.5, plan["voice_end"] - .1) * SR); g_t[fo0:] *= np.linspace(1, 0, n - fo0) ** 1.5  # gone with the last word
    # carve: voice envelope (1 kHz control rate) -> music gain dip
    k = SR // 1000; p = (V[: (n // k) * k].reshape(-1, k) ** 2).mean(1); env = np.sqrt(np.convolve(p, np.ones(25) / 25, "same") + 1e-12)
    db = 20 * np.log10(env + 1e-9); duck = np.clip((db + 42) / 24, 0, 1)
    sm = np.zeros_like(duck); a_att, a_rel = np.exp(-1 / 15), np.exp(-1 / 1000)
    for i in range(1, len(duck)):
        c = a_att if duck[i] > sm[i - 1] else a_rel; sm[i] = c * sm[i - 1] + (1 - c) * duck[i]
    gain_db = -6.5 * sm; ctl = np.interp(np.arange(n) / SR, np.arange(len(sm)) / 1000, 10 ** (gain_db / 20))
    # level riding: the bed follows the voice's loudness over ~1.2 s (quiet phrase -> quieter bed, loud phrase -> slightly more), so the voice-to-music ratio stays steady instead of swinging
    slow = np.sqrt(np.convolve(p, np.ones(1200) / 1200, "same") + 1e-12); ref = np.median(slow[slow > .004]) if (slow > .004).any() else 1.0
    ride = np.clip(slow / ref, .3, 2.6) ** 1.35; ctl = ctl * np.interp(np.arange(n) / SR, np.arange(len(ride)) / 1000, ride)
    M = M * (g_t * ctl)[:, None]
# ---- SFX bus
S = np.zeros((n, 2)); placed = 0
for c in plan["cues"]:
    p = os.path.join(proj, c["path"])
    if not os.path.exists(p): continue
    x = load(p, 2); pk = np.max(np.abs(x)) + 1e-9; x = x / pk * 10 ** (-10 / 20) * c["vol"]      # level every file to -10 dBFS peak, THEN the role volume (reel-edit rule: vol 0.12-0.36 = peaks around -20 dBFS)
    x = x[: int(c.get("max_dur", 3.0) * SR)]; f_in, f_out = int(.008 * SR), min(len(x), int(.04 * SR))
    x[:f_in] *= ramp(f_in, 0, 1)[:, None]; x[-f_out:] *= ramp(f_out, 1, 0)[:, None]
    s0 = int(max(0, c["t"]) * SR); e0 = min(n, s0 + len(x))
    if e0 > s0: S[s0:e0] += x[: e0 - s0]; placed += 1
rng = np.random.default_rng(5); L = int(.3 * SR); ir = rng.standard_normal(L) * np.exp(-np.arange(L) / SR / .07); ir /= np.sqrt((ir ** 2).sum())
if placed:
    N2 = 1 << int(np.ceil(np.log2(n + L)))
    for ch in range(2): S[:, ch] = S[:, ch] + .10 * np.fft.irfft(np.fft.rfft(S[:, ch], N2) * np.fft.rfft(ir, N2), N2)[:n]
# ---- solve the music level for the voice/residual target (per second of speech)
mono = lambda a: a.mean(1) if a.ndim > 1 else a
rv = np.array([np.sqrt(np.mean(V[s * SR:(s + 1) * SR] ** 2)) for s in range(n // SR)]); live = rv > max(.004, .35 * np.median(rv[rv > .004]))      # seconds with real speech (not breaths / pause tails)


def ratios(g):
    res = (M * g if M is not None else 0) + S
    rr = np.array([np.sqrt(np.mean(mono(res[s * SR:(s + 1) * SR]) ** 2)) + 1e-9 for s in range(n // SR)])
    r = 20 * np.log10(rv / rr); return r[live]


g = 1.0; lo, hi = .005, 3.0
if M is not None:
    for _ in range(22):
        g = (lo + hi) / 2; r = ratios(g)
        if np.median(r) > target: lo = g
        else: hi = g
    while np.min(ratios(g)) < 8.0 and g > .01: g *= .97                                # reel-edit rule: never closer than 8 dB in any second of speech
r = ratios(g); mix = np.stack([V, V], 1) + (M * g if M is not None else 0) + S
# ---- master: two-pass linear loudnorm to -14 LUFS / -1.5 dBTP
raw = os.path.join(A, "audio", "_premaster.wav"); out = os.path.join(A, "audio", "master.wav")
import wave
pcm = (np.clip(mix, -1, 1) * 32767).astype("<i2"); w = wave.open(raw, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
st = subprocess.run(["ffmpeg", "-nostats", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
j = json.loads(st[st.rindex("{"):st.rindex("}") + 1])
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true", "-ar", str(SR), out], check=True)
os.remove(raw)
fin = subprocess.run(["ffmpeg", "-nostats", "-i", out, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
lufs = float(fin.split("I:")[-1].split("LUFS")[0]); tp = float(fin.split("Peak:")[-1].split("dBFS")[0]) if "Peak:" in fin else None
gaps = [b - a for a, b in zip([0] + sorted(c["t"] for c in plan["cues"]), sorted(c["t"] for c in plan["cues"]) + [total])]
rep = {"music": (mus or {}).get("file"), "music_gain_solved": round(float(g), 3), "voice_over_music_sfx_db_median": round(float(np.median(r)), 1), "voice_over_music_sfx_db_min": round(float(np.min(r)), 1), "target_db": target,
       "lufs": round(lufs, 1), "true_peak_db": tp, "sfx_placed": placed, "sfx_per_10s": round(placed / total * 10, 1), "silent_spots_over_1.2s": sum(1 for x in gaps if x >= 1.2), "voice_processing": "none (untouched)"}
secs = np.where(live)[0]; rr_m = np.array([np.sqrt(np.mean(mono((M * g if M is not None else 0)[s * SR:(s + 1) * SR] if M is not None else S[s * SR:(s + 1) * SR]) ** 2)) for s in range(n // SR)]); rr_s = np.array([np.sqrt(np.mean(mono(S[s * SR:(s + 1) * SR]) ** 2)) for s in range(n // SR)])
w = np.argsort(r)[:3]; rep["worst_seconds"] = [{"t": int(secs[i]), "ratio_db": round(float(r[i]), 1), "voice_rms": round(float(rv[secs[i]]), 4), "music_rms": round(float(rr_m[secs[i]]), 4), "sfx_rms": round(float(rr_s[secs[i]]), 4)} for i in w]
json.dump(rep, open(os.path.join(A, "mix_report.json"), "w"), indent=1); print(json.dumps(rep, indent=1))
