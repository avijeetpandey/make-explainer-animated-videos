#!/usr/bin/env python3
"""Index a folder of tracks YOU may use, so the picker can choose beds for you.

  python3 -I build_music_index.py <music_dir> [--meta meta.json]      (needs: pip install librosa numpy)

Writes <music_dir>/INDEX.json (bpm, beat grid, energy 0-100, centroid, intro length, 3 bar-aligned energetic start points) and <music_dir>/music_features.json
(share of energy 30-120 Hz / above 5 kHz, groove regularity, drive). Optional meta.json: {"track.mp3": {"genre": "house", "moods": ["upbeat"], "source": "Mixkit", "licence": "Mixkit License (free, no attribution)"}}.
Genre matters: the 'premium' scoring prefers techno / tech-house / house / technology / cinematic and avoids pop, funk, corporate. Keep the licence line: it is copied next to every video.
Free no-attribution sources: Mixkit (mixkit.co/license), YouTube Audio Library (Attribution not required), Pixabay Music. Check each licence yourself."""
import json, os, sys
import numpy as np
try: import librosa
except ImportError: sys.exit("pip install librosa numpy")
d = os.path.abspath(sys.argv[1]); meta = json.load(open(sys.argv[sys.argv.index("--meta") + 1])) if "--meta" in sys.argv else {}
idx, feats = {}, {}
for f in sorted(os.listdir(d)):
    if not f.lower().endswith((".mp3", ".wav", ".m4a", ".ogg", ".flac")): continue
    try:
        y, sr = librosa.load(os.path.join(d, f), sr=22050, mono=True); dur = len(y) / sr
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=512); bt = librosa.frames_to_time(beats, sr=sr, hop_length=512); bpm = int(round(float(np.atleast_1d(tempo)[0])))
        rms = librosa.feature.rms(y=y, hop_length=512)[0]; db = 20 * np.log10(rms + 1e-9); t = np.arange(len(rms)) * 512 / sr
        energy = int(np.clip((np.mean(db[rms > np.percentile(rms, 40)]) + 32) / 26 * 100, 0, 100)); cen = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
        sm = np.convolve(rms, np.ones(20) / 20, "same"); intro = float(t[np.argmax(sm > .6 * np.median(sm))]) if (sm > .6 * np.median(sm)).any() else 0.0
        bars = bt[::4]; sc = []
        for b in bars:
            if b < 4 or b + 32 > dur: continue
            sc.append((float(np.mean(rms[(t >= b) & (t < b + 30)])), float(b)))
        starts = []
        for _, b in sorted(sc, reverse=True):
            if all(abs(b - s) > 12 for s in starts): starts.append(round(b, 2))
            if len(starts) == 3: break
        m = meta.get(f, {})
        idx[f] = {"duration": round(dur, 1), "bpm": bpm, "beats": [round(float(x), 2) for x in bt], "energy": energy, "loud_db": round(float(np.mean(db)), 1), "intro_s": round(intro, 1), "centroid": int(cen), "starts": starts or [0.0], "source": m.get("source", ""), "licence": m.get("licence", ""), "genre": m.get("genre", ""), "moods": m.get("moods", ["upbeat"])}
        S = np.abs(librosa.stft(y[: int(30 * sr)], n_fft=2048, hop_length=512)) ** 2; fr = librosa.fft_frequencies(sr=sr, n_fft=2048); tot = S.sum() + 1e-12
        oenv = librosa.onset.onset_strength(y=y[: int(30 * sr)], sr=sr, hop_length=512); ac = librosa.autocorrelate(oenv - oenv.mean())
        feats[f] = {"low": round(float(S[(fr >= 30) & (fr <= 120)].sum() / tot), 3), "mid": round(float(S[(fr > 120) & (fr <= 2000)].sum() / tot), 3), "hi": round(float(S[fr > 5000].sum() / tot), 4), "groove": round(float(ac[1:].max() / ac[0]), 3), "drive": round(float(oenv.mean()), 2)}
        print(f"{f}: {bpm} bpm, energy {energy}, centroid {int(cen)} Hz, starts {starts}")
    except Exception as e: print("skipped", f, e)
json.dump(idx, open(os.path.join(d, "INDEX.json"), "w")); json.dump(feats, open(os.path.join(d, "music_features.json"), "w"), indent=0); print(f"indexed {len(idx)} tracks -> {d}/INDEX.json")
