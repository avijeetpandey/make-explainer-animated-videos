#!/usr/bin/env python3
"""Audio library access (read-only) for explainer videos: music bed + role-based SFX.

Where the libraries live (config.local.json or EXPLAINER_MUSIC_DIR / EXPLAINER_SFX_DIR, else <skill>/library/):
  <music_dir>/INDEX.json      bpm, beats, energy, moods, genre, bar-aligned `starts`, licence  (build it for YOUR tracks: scripts/build_music_index.py)
  <music_dir>/music_features.json   optional: groove / drive / low / mid / hi shares (same script)
  <sfx_dir>/ROLES.json        optional: files filed by job (whip, hit_soft, impact, riser, pop, tick, click, notif, success, error, negation ...); without it
                              sub-folders named after the roles are used; without any SFX library the synthetic set from make_sfx.py is used.
Only use tracks whose licence allows your use (free / no-attribution beds are ideal; keep the licence line in the index: it is copied into assets/music_credit.txt).
Selection logic: energetic from second 1 (precomputed start), energy >= 72, BPM near 122 for 'premium', genre + spectrum scoring (see music_score), never a track used by the last reels.
If no music library is found the video is built without music and says so.
"""
import hashlib, json, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import config
SKILL = config.SKILL
ROOT = config.get("pipeline_root")                                           # optional: another pipeline whose logs should also be respected
MUSIC = config.get("music_dir") or os.path.join(SKILL, "library", "music")
SFX = config.get("sfx_dir") or os.path.join(SKILL, "library", "sfx")
PROJECTS = os.path.expanduser(config.get("projects_dir") or "~/Documents/explainer-videos")
OWN_LOG = os.path.join(PROJECTS, "_music_log.json")
run = lambda *a: subprocess.run(a, capture_output=True, text=True)


def seed(*parts):
    return int(hashlib.md5("|".join(map(str, parts)).encode()).hexdigest()[:8], 16)


def recent_tracks(reel, n=3):
    """Tracks used by the last reels of BOTH pipelines (reel-edit logs + this skill's own log) so two videos in a row never share a bed."""
    used = []
    if ROOT:                                                                    # tracks used by another pipeline's last reels (optional)
        try:
            for ln in open(os.path.join(ROOT, "reels/style_log.md"), encoding="utf-8"):
                if ln.startswith("| 20") and len(ln.strip().strip("|").split("|")) >= 7: used.append(ln.strip().strip("|").split("|")[-1].strip().lower())
        except Exception: pass
        try: used += [r["music"] for r in json.load(open(os.path.join(ROOT, "reels/auto_style_log.json"))) if r.get("music")]
        except Exception: pass
    import re as _re; base = lambda n: _re.sub(r"_v\d+(__alt)?$", "", n or "")                     # a re-edit (_v2, _v3 ...) of the same reel keeps its track unless told otherwise
    try: used += [r["file"] for r in json.load(open(OWN_LOG)) if base(r.get("reel")) != base(reel)]
    except Exception: pass
    return [u.lower() for u in used if u][-n:]


PREMIUM_GENRES = {"techno": 12, "tech-house": 12, "deep-house": 12, "house": 10, "technology": 10, "electro-house": 6, "electronic": 6, "electronica": 6, "cinematic": 6, "rhythmic-underscore": 6, "underscore": 2}
CHEESY_GENRES = {"dance-pop": -45, "pop": -45, "indie-pop": -40, "synthpop": -40, "electropop": -38, "funk": -34, "funk-rock": -34, "jazz-funk": -30, "neo-soul": -20, "corporate-music": -28, "library": -14,
                 "breakbeat": -10, "hip-hop": -8, "dream-pop": -30, "lifestyle": -6, "chillout": -14, "downtempo": -14, "ambient": -14, "atmospheres": -16, "lo-fi-beats": -20, "future-bass": -6, "trap": -4, "": -4}


_feat = None
def features_of(f):
    """Precomputed audio features (assets/music_features.json via librosa): low = share of energy 30-120 Hz, hi = share above 5 kHz, groove = beat regularity, drive = onset strength."""
    global _feat
    if _feat is None:
        _feat = {}
        for p in (os.path.join(MUSIC, "music_features.json"), os.path.join(SKILL, "assets", "music_features.json")):
            try: _feat = json.load(open(p)); break
            except Exception: pass
    x = _feat.get(f) or {}
    return x if "drive" in x else None


def music_score(t, style="premium", bpm=None, f=None, genres=None):
    """Higher = better bed. 'premium' = modern tech/house/techno with a dark, warm spectrum (low centroid) and no pop hook; 'classic' = the old reel-edit scoring (energy + BPM + mood).
    Why: 'What About Action' (dance-pop, centroid 2571 Hz) sounded chapri under a tech explainer; premium beds are dark, steady, groove-led, never melodic-pop."""
    bpm = bpm or (122 if style == "premium" else 112)
    s = t["energy"] - abs(t["bpm"] - bpm) / 2.2 - (30 if t["energy"] < 72 else 0) - (4 if t["intro_s"] > 8 else 0)
    if style != "premium": return s
    g = (t.get("genre") or "").lower(); c = t.get("centroid", 2500)
    s += PREMIUM_GENRES.get(g, 0) + CHEESY_GENRES.get(g, 0) + (genres or {}).get(g, 0)         # a world nudges the premium genres it prefers
    s += 10 if c <= 1700 else 4 if c <= 2100 else 0 if c <= 2600 else -10                 # darker / warmer spectrum reads expensive
    s -= 8 if t["intro_s"] > 1.5 else 0                                                    # must hit from second 1
    x = features_of(f) if f else None
    if x:                                                                                  # measured: a driving groove, a deep low end, no shrill top = premium and energetic
        s += 7 * (x["drive"] - 1.8) + 8 * (x["groove"] - .8) + .12 * (x["low"] * 100 - 55) - 400 * max(0.0, x["hi"] - .012) - 20 * max(0.0, x["mid"] - .42)
    return s


def rank_music(reel="", style="premium", bpm=None, n=10):
    idx = json.load(open(os.path.join(MUSIC, "INDEX.json"))); used = recent_tracks(reel)
    rows = [(music_score(t, style, bpm, f), f, t) for f, t in idx.items() if not any(u and (u in f.lower() or f.lower().replace(".mp3", "") in u) for u in used) and t.get("starts")]
    return sorted(rows, key=lambda r: -r[0])[:n]


def pick_music(length, reel, moods=("upbeat", "bright", "curious"), bpm=None, force=None, out=None, style="premium", skip=(), log=True, genres=None):
    ip = os.path.join(MUSIC, "INDEX.json")
    if not os.path.exists(ip): return None
    idx = json.load(open(ip)); used = recent_tracks(reel); best = None
    for f, t in idx.items():
        if force and f != force: continue
        if not force and (f in skip or any(u and (u in f.lower() or f.lower().replace(".mp3", "") in u) for u in used) or t["duration"] < length + 12 or not t.get("starts")): continue
        s = music_score(t, style, bpm, f, genres)
        if style != "premium": s += 14 * max([1 - i * .35 for i, m in enumerate(moods) if m in t["moods"]] or [0])
        if best is None or s > best[0]: best = (s, f, t)
    if not best: return None
    _, f, t = best; k = seed(reel, "music") % len(t["starts"]); start = t["starts"][k]
    if start + length + 1 > t["duration"]: start = t["starts"][0]
    beats = [round(b - start, 3) for b in t["beats"] if start <= b <= start + length + .5]
    if out:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        polish = "highpass=f=35" + (",treble=g=-2.5:f=6000" if t.get("centroid", 0) > 1800 else "")             # tame a bright bed instead of letting it sound shrill under a voice
        run("ffmpeg", "-v", "error", "-y", "-ss", str(start), "-i", os.path.join(MUSIC, f), "-t", f"{length + .5:.2f}", "-af", polish, "-c:a", "libmp3lame", "-q:a", "2", out)
    try:
        if not log: raise RuntimeError
        log = [r for r in json.load(open(OWN_LOG)) if r.get("reel") != reel] if os.path.exists(OWN_LOG) else []
        log.append({"reel": reel, "file": f}); os.makedirs(os.path.dirname(OWN_LOG), exist_ok=True); json.dump(log, open(OWN_LOG, "w"), indent=1)
    except Exception: pass
    return {"file": f, "start": start, "bpm": t["bpm"], "energy": t["energy"], "genre": t.get("genre"), "centroid": t.get("centroid"), "moods": t["moods"], "source": t.get("source"), "licence": t.get("licence") or "", "beats": beats}


if __name__ == "__main__":      # python3 -I audio_lib.py --rank [classic|premium]  : show the ranked beds with their scores
    style = sys.argv[sys.argv.index("--rank") + 1] if "--rank" in sys.argv and len(sys.argv) > sys.argv.index("--rank") + 1 else "premium"
    for s_, f, t in rank_music("", style): print(f"{s_:6.1f}  {f:46s} {t.get('genre','')!s:14s} bpm {t['bpm']}  energy {t['energy']}  centroid {t.get('centroid')}  intro {t['intro_s']}s")


_roles = None
def pick_sfx(role, reel, dur=(0.0, 9.0)):
    """One file per role per reel (seeded by the reel name), taken from the best-scored originals/Mixkit files whose length fits."""
    global _roles
    if _roles is None:
        try: _roles = json.load(open(os.path.join(SFX, "ROLES.json")))
        except Exception:                                                         # no ROLES.json: sub-folders named after the roles
            _roles = {}
            for r in (os.listdir(SFX) if os.path.isdir(SFX) else []):
                d = os.path.join(SFX, r)
                if os.path.isdir(d): _roles[r] = [{"file": f"{r}/{f}", "dur": float(run("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", os.path.join(d, f)).stdout.strip() or 0), "score": 1} for f in sorted(os.listdir(d)) if f.lower().endswith((".wav", ".mp3", ".ogg", ".m4a", ".flac"))]
    pool = [x for x in _roles.get(role, []) if dur[0] <= x.get("dur", 0) <= dur[1] and os.path.exists(os.path.join(SFX, x["file"]))]
    pool.sort(key=lambda x: (-x.get("score", 0), x["file"]))
    pool = pool[:5]
    return pool[seed(reel, role) % len(pool)]["file"] if pool else None
