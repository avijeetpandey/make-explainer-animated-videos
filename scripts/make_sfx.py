#!/usr/bin/env python3
"""Synthesise the explainer SFX set (original, no third-party licence): python3 -I make_sfx.py <out_dir>
Measured on the reference reels: voice-only mix + one soft low thump per beat, small clicks/pops per object. Everything here is short, dry and quiet."""
import sys, wave, os
import numpy as np

SR = 48000
rng = np.random.default_rng(11)


def t(d): return np.arange(int(SR * d)) / SR
def env(x, a=0.004, r=None):
    n = len(x); r = r or n / SR * 0.9; e = np.minimum(np.arange(n) / (a * SR), 1) * np.exp(-np.arange(n) / SR / (r / 5)); return x * e
def lp(x, fc):  # one-pole low-pass
    a = np.exp(-2 * np.pi * fc / SR); y = np.zeros_like(x); s = 0.0
    for i, v in enumerate(x): s = (1 - a) * v + a * s; y[i] = s
    return y
def norm(x, peak=0.9): return x / (np.max(np.abs(x)) + 1e-9) * peak
def save(path, x):
    x = np.clip(x, -1, 1); w = wave.open(path, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype("<i2").tobytes()); w.close()

def thump():
    x = t(0.32); f = 62 + 40 * np.exp(-x * 30); y = np.sin(2 * np.pi * np.cumsum(f) / SR); return env(y, 0.003, 0.28) + 0.25 * env(lp(rng.standard_normal(len(x)), 900), 0.001, 0.03)
def tick():
    x = t(0.08); return env(np.sin(2 * np.pi * 2600 * x) * 0.6 + lp(rng.standard_normal(len(x)), 6000) * 0.4, 0.0008, 0.03)
def click():
    x = t(0.12); return env(np.sin(2 * np.pi * 1500 * x) + 0.5 * np.sin(2 * np.pi * 900 * x), 0.001, 0.05)
def pop():
    x = t(0.16); f = 360 + 700 * (1 - np.exp(-x * 40)); return env(np.sin(2 * np.pi * np.cumsum(f) / SR), 0.002, 0.09)
def whoosh():
    x = t(0.5); n = rng.standard_normal(len(x)); y = lp(n, 2500) - lp(n, 400); sw = np.sin(np.pi * x / 0.5) ** 2; return y * sw
def riser():
    x = t(1.0); n = rng.standard_normal(len(x)); y = (lp(n, 5000) - lp(n, 600)) * (x / 1.0) ** 2 + 0.2 * np.sin(2 * np.pi * np.cumsum(200 + 900 * x) / SR) * (x / 1.0); return y
def ding():
    x = t(0.9); return env(np.sin(2 * np.pi * 988 * x) + 0.5 * np.sin(2 * np.pi * 1976 * x) + 0.25 * np.sin(2 * np.pi * 2960 * x), 0.002, 0.8)
def error():
    x = t(0.3); return env(np.sign(np.sin(2 * np.pi * 150 * x)) * 0.5 + np.sin(2 * np.pi * 110 * x), 0.003, 0.22)
def stamp():
    x = t(0.35); return env(np.sin(2 * np.pi * (48 + 60 * np.exp(-x * 25)) * x) + 0.6 * lp(rng.standard_normal(len(x)), 1800) * np.exp(-x * 40), 0.001, 0.3)

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."; os.makedirs(out, exist_ok=True)
    for name, fn, pk in [("thump", thump, .9), ("tick", tick, .7), ("click", click, .6), ("pop", pop, .7), ("whoosh", whoosh, .6), ("riser", riser, .6), ("ding", ding, .6), ("error", error, .7), ("stamp", stamp, .9)]:
        save(os.path.join(out, name + ".wav"), norm(fn(), pk))
    print("wrote 9 sfx to", out)
