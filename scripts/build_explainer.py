#!/usr/bin/env python3
"""Build a HyperFrames project for one animated explainer reel.

  python3 build_explainer.py <project_dir> [--words]      # --words: only transcribe, print word times, write assets/words.json

Project dir needs:  voice.(wav|mp3|m4a|aiff)   your voice-over (English, or Roman-script Hinglish with meta.language = hinglish)
                    scenes.json                 {"meta": {...}, "scenes": [{"text": "...", "hero": {...}, "stage": [...]}]}
Writes:             index.html (+ assets/: fonts, gsap, audio/voice.wav, audio/sfx/*.wav, words.json, timing.json)
Pure standard library (+ numpy for SFX, + ffmpeg and whisper-cli on PATH). Run with `python3 -I`.
"""
import difflib, json, os, re, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import config

HERE = os.path.dirname(os.path.abspath(__file__)); SKILL = os.path.dirname(HERE)
MODELS = [os.path.expanduser(p) for p in ("~/.cache/hyperframes/whisper/models/ggml-small.en.bin", "~/.cache/hyperframes/whisper/models/ggml-medium.en.bin", "~/.cache/whisper/ggml-small.en.bin")]
GSAP = os.path.expanduser("~/.cache/explainer-skill/gsap.min.js")
FRAME_KEYS = {"x", "y", "sc", "alpha", "tone", "active", "on", "dash", "w", "w3", "h3", "d3", "ry", "rx", "ly", "gap", "rot", "cw", "lit", "vals", "tones", "lines"}
GLOW = {"white": "rgba(255,255,255,.07)", "red": "rgba(255,77,94,.11)", "blue": "rgba(90,169,255,.11)", "yellow": "rgba(255,210,63,.09)", "green": "rgba(74,222,128,.10)", "violet": "rgba(167,139,250,.11)"}


def run(*a, **k):
    return subprocess.run(a, capture_output=True, text=True, **k)


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def transcribe(wav):
    model = next((m for m in MODELS if os.path.exists(m)), None)
    if not shutil.which("whisper-cli") or not model:
        sys.exit("whisper-cli or an English ggml model is missing. Run scripts/setup.sh (brew install whisper-cpp + model download).")
    cmd = ["whisper-cli", "-m", model, "-f", wav, "-l", "en", "-ml", "1", "-sow", "-np"]
    out = run(*cmd).stdout; ws = []
    for l in out.splitlines():
        m = re.match(r"\[(\d+):(\d+):([\d.]+) --> (\d+):(\d+):([\d.]+)\]\s+(.*)", l)
        if m and m.group(7).strip() and not m.group(7).strip().startswith("["):
            a = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]); b = int(m[4]) * 3600 + int(m[5]) * 60 + float(m[6])
            ws.append([round(a, 2), round(b, 2), m.group(7).strip()])
    return ws


def tokens(text):
    """'Over HTTP, this is sent *without* encryption. _next Reel_' -> [(display, key, serif, blue)] ; * = key term (bold+underline), _ = serif italic accent, ^ = blue accent.
    Punctuation glued to a marker ('*load balancer*,') stays attached to the previous word."""
    out, key, ser, c1 = [], False, False, False
    for part in re.split(r"(\*|_|\^)", text):
        if part in ("*", "_", "^"):
            if part == "*": key = not key
            elif part == "_": ser = not ser
            else: c1 = not c1
            continue
        ws = part.split()
        if ws and out and not part[:1].isspace() and not re.match(r"\w", ws[0]):     # leading punctuation -> glue to previous word
            out[-1] = (out[-1][0] + ws.pop(0),) + out[-1][1:]
        for w in ws: out.append((w, key, ser, c1))
    return out


def align(script, words):
    """Map every script word to a spoken time using difflib over normalised words; interpolate the unmatched ones."""
    A = [norm(w[0]) for w in script]; B = [norm(w[2]) for w in words]
    t = [None] * len(A)
    for m in difflib.SequenceMatcher(None, A, B, autojunk=False).get_matching_blocks():
        for k in range(m.size):
            t[m.a + k] = words[m.b + k][0]
    known = [i for i, v in enumerate(t) if v is not None]
    if not known:
        sys.exit("No script word matched the transcript: wrong voice file or script?")
    for i in range(len(t)):
        if t[i] is not None: continue
        lo = max((k for k in known if k < i), default=None); hi = min((k for k in known if k > i), default=None)
        if lo is None: t[i] = max(0.0, t[hi] - 0.3 * (hi - i))
        elif hi is None: t[i] = t[lo] + 0.3 * (i - lo)
        else: t[i] = t[lo] + (t[hi] - t[lo]) * (i - lo) / (hi - lo)
    for i in range(1, len(t)): t[i] = max(t[i], t[i - 1] + 0.04)
    return [round(v, 2) for v in t], len(known) / len(A)


def speech_segments(wav, scenes_n, db=None):
    """Speech segments [(start,end)] from silence detection. Tries several thresholds until there are >= scenes-1 pauses."""
    dur = float(run("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav).stdout.strip())
    best = None
    for th in ([db] if db else [-35, -30, -40, -28, -45]):
        err = run("ffmpeg", "-nostats", "-i", wav, "-af", f"silencedetect=noise={th}dB:d=0.22", "-f", "null", "-").stderr
        st = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", err)]; en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
        sil = list(zip([max(0.0, s) for s in st], en + [dur] * (len(st) - len(en))))
        segs, p = [], 0.0
        for s, e in sil:
            if s - p > 0.08: segs.append((p, s))
            p = e
        if dur - p > 0.08: segs.append((p, dur))
        if segs and (best is None or len(segs) > len(best)): best = segs
        if segs and len(segs) - 1 >= scenes_n - 1: break
    return best or [(0.0, dur)]


def pause_times(script, n_scenes, wav, db=None):
    """Hinglish / any-accent timing without speech recognition: scenes snap to the pauses between sentences; words are spread by length inside each sentence."""
    segs = speech_segments(wav, n_scenes, db); S = sum(e - s for s, e in segs)
    gaps = [(segs[k + 1][0] - segs[k][1]) for k in range(len(segs) - 1)]; cum = [sum(e - s for s, e in segs[:k + 1]) for k in range(len(segs) - 1)]
    per = [[] for _ in range(n_scenes)]
    for i, tk in enumerate(script): per[tk[-1]].append(i)
    chars = [sum(len(norm(script[i][0])) + 1 for i in idx) for idx in per]; tot = sum(chars) or 1
    bounds = [0.0]                                              # cumulative speech-time at each scene start
    if n_scenes > 1 and len(gaps) >= n_scenes - 1:              # DP: pick increasing pauses closest to the expected sentence shares
        T = [S * sum(chars[:j]) / tot for j in range(1, n_scenes)]; INF = 1e9
        cost = lambda j, k: abs(cum[k] - T[j]) / S * 10 - min(gaps[k], 1.2) * 0.8
        best = [[INF] * len(gaps) for _ in T]; back = [[-1] * len(gaps) for _ in T]
        for k in range(len(gaps)): best[0][k] = cost(0, k)
        for j in range(1, len(T)):
            for k in range(len(gaps)):
                for k2 in range(k):
                    v = best[j - 1][k2] + cost(j, k)
                    if v < best[j][k]: best[j][k], back[j][k] = v, k2
        k = min(range(len(gaps)), key=lambda k: best[-1][k]); pick = [k]
        for j in range(len(T) - 1, 0, -1): k = back[j][k]; pick.append(k)
        bounds += [cum[k] for k in reversed(pick)]
    else:                                                       # fewer pauses than sentences: cut at expected speech-time shares
        bounds += [S * sum(chars[:j]) / tot for j in range(1, n_scenes)]
    bounds.append(S)
    def absolute(x):
        for s, e in segs:
            if x < e - s - 1e-6: return s + x          # exactly on a boundary -> start of the NEXT speech segment
            x -= e - s
        return segs[-1][1]
    times = [0.0] * len(script)
    for si, idx in enumerate(per):
        if not idx: continue
        w = [len(norm(script[i][0])) + 1.5 + (2.5 if re.search(r"[,.?!:;]$", script[i][0]) and i != idx[-1] else 0) for i in idx]; tw = sum(w); acc = 0.0
        for i, wi in zip(idx, w):
            times[i] = round(absolute(bounds[si] + (bounds[si + 1] - bounds[si]) * acc / tw), 2); acc += wi
    return times


def _sim(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio() if a and b else 0.0


def fuzzy_align(S, A):
    """Needleman-Wunsch over normalised words with a similarity score, so Hinglish spelling drift ('kyu' vs 'kyun', 'peeche' vs 'pichhe') still matches.
    S = script words, A = [(start, end, word)] from the recogniser. Returns (time per script word or None, share of script words matched)."""
    n, m = len(S), len(A); an = [norm(w[2]) for w in A]
    sc = [[0.0] * (m + 1) for _ in range(n + 1)]; bk = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1): sc[i][0] = -.8 * i; bk[i][0] = 1
    for j in range(1, m + 1): sc[0][j] = -.8 * j; bk[0][j] = 2
    sim = [[_sim(S[i], an[j]) for j in range(m)] for i in range(n)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            s = sim[i - 1][j - 1]; d = sc[i - 1][j - 1] + (2.5 * s if s >= .6 else -1.0)
            u = sc[i - 1][j] - .8; l = sc[i][j - 1] - .8
            sc[i][j], bk[i][j] = max((d, 0), (u, 1), (l, 2))
    i, j, t = n, m, [None] * n; hit = 0
    while i > 0 or j > 0:
        k = bk[i][j]
        if i > 0 and j > 0 and k == 0:
            if sim[i - 1][j - 1] >= .6: t[i - 1] = A[j - 1][0]; hit += 1
            i -= 1; j -= 1
        elif i > 0 and (k == 1 or j == 0): i -= 1
        else: j -= 1
    return t, hit / max(1, n)


def island_times(script, isl, asr_t=None):
    """Island-anchored timing. The speech islands (acoustic, reliable) fix WHERE the words are; the script words are partitioned over them by a DP:
    expected duration of an island ~ summed character weight, punctuation should fall at island ends, and any ASR time that lands inside an island is soft evidence.
    Inside an island words are spread by weight, snapped to ASR times when those agree within 0.35 s."""
    N, K = len(script), len(isl); toks = [w[0] for w in script]
    wt = [len(norm(t)) + 1.0 + (1.5 if re.search(r"[,.?!:;]$", t) else 0) for t in toks]; pre = [0.0]
    for v in wt: pre.append(pre[-1] + v)
    D = [b_ - a_ for a_, b_ in isl]; r = sum(D) / pre[-1]; INF = 1e18
    def cost(k, i, j):
        a_, b_ = isl[k]
        if j == i: return 2.5
        err = (D[k] - r * (pre[j] - pre[i])) / (.25 * D[k] + .2); c = err * err
        if j < N and re.search(r"[,.?!:;]$", toks[j - 1]): c -= .6
        if asr_t: c -= .7 * sum(1 for q in range(i, j) if asr_t[q] is not None and a_ - .2 <= asr_t[q] <= b_ + .2)
        return c
    f = [[INF] * (N + 1) for _ in range(K + 1)]; bk = [[0] * (N + 1) for _ in range(K + 1)]; f[0][0] = 0.0
    for k in range(K):
        for i in range(N + 1):
            if f[k][i] >= INF: continue
            for j in range(i, min(N, i + 40) + 1):
                v = f[k][i] + cost(k, i, j)
                if v < f[k + 1][j]: f[k + 1][j] = v; bk[k + 1][j] = i
    cuts = [0] * (K + 1); cuts[K] = N; j = N
    for k in range(K, 0, -1): cuts[k - 1] = bk[k][j]; j = cuts[k - 1]
    times = [0.0] * N
    for k in range(K):
        i, j = cuts[k], cuts[k + 1]
        if j <= i: continue
        a_, b_ = isl[k]; tot = pre[j] - pre[i]
        for q in range(i, j):
            est = a_ + (b_ - a_) * (pre[q] - pre[i]) / tot
            times[q] = asr_t[q] if (asr_t and asr_t[q] is not None and a_ - .05 <= asr_t[q] <= b_ and abs(asr_t[q] - est) <= .35) else est
    for q in range(1, N): times[q] = max(times[q], times[q - 1] + .04)
    return [round(v, 2) for v in times]


def asr_times(script, wav, proj, prompt_words, log=print):
    """Roman-Hinglish word times (reel-edit humanize.md round 10/13): split the voice at its pauses into speech islands, run whisper-MEDIUM on ONE island at a time
    (parallel runs silently produced nothing) with a Roman-script prompt (-l en would translate, -l hi gives Devanagari), clamp each word to its island, then fuzzy-align to the script."""
    model = next((m for m in (os.path.expanduser("~/.cache/hyperframes/whisper/models/ggml-medium.bin"), os.path.expanduser("~/.cache/whisper/ggml-medium.bin")) if os.path.exists(m)), None)
    if not model or not shutil.which("whisper-cli"):
        import clean_voice; return island_times(script, [(round(x, 3), round(y, 3)) for x, y in clean_voice.speech_islands(wav)]), 0.5
    sys.path.insert(0, HERE); cache = os.path.join(proj, "assets", "asr_islands.json"); st = os.stat(wav); key = f"v2-{st.st_size}-{int(st.st_mtime)}"
    words = None; import clean_voice
    isl_cache = [[(round(x, 3), round(y, 3)) for x, y in clean_voice.speech_islands(wav)]]
    if os.path.exists(cache):
        c = json.load(open(cache))
        if c.get("key") == key: words = c["words"]
    if words is None:
        isl = isl_cache[0]
        prompt = "Yeh ek Hinglish video hai. Hindi words Roman script mein likhe hain: acha, kya, hai, nahi, aur, mein, ke, ka, ki, toh, jaise, bas. " + " ".join(prompt_words[:14])
        words = []
        for k, (a_, b_) in enumerate(isl):
            s0 = max(0.0, a_ - .05); tmp = os.path.join(proj, "assets", f"_isl{k}.wav")
            run("ffmpeg", "-v", "error", "-y", "-ss", f"{s0:.3f}", "-t", f"{b_ - s0 + .1:.3f}", "-i", wav, "-ar", "16000", "-ac", "1", tmp)
            out = run("whisper-cli", "-m", model, "-f", tmp, "-l", "en", "-ml", "1", "-sow", "-np", "--prompt", prompt).stdout; os.remove(tmp)
            for l in out.splitlines():
                m = re.match(r"\[(\d+):(\d+):([\d.]+) --> (\d+):(\d+):([\d.]+)\]\s+(.*)", l)
                if m and m.group(7).strip() and not m.group(7).strip().startswith("["):
                    x0 = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]); x1 = int(m[4]) * 3600 + int(m[5]) * 60 + float(m[6])
                    words.append([round(s0 + x0, 2), round(min(s0 + x1, b_), 2), m.group(7).strip()])
        json.dump({"key": key, "words": words}, open(cache, "w"))
    S = [norm(w[0]) for w in script]; t, cov = fuzzy_align(S, words)
    return island_times(script, isl_cache[0], t if cov >= .3 else None), cov


def resolve(spec, words, total, wav=None, proj=None):
    meta = {"handle": config.get("handle", "@yourhandle"), "series": "EXPLAINER · 01", "accent": "white", "particles": 4200, "seed": 7, "drift": 0.02, "kickers": True}
    meta.update(spec.get("meta", {})); meta["handle"] = meta.get("handle") or config.get("handle", "@yourhandle"); meta.pop("brand", None)
    if meta["handle"] == "@yourhandle": print("NOTE: header shows the placeholder @yourhandle: set meta.handle in scenes.json or \"handle\" in config.local.json")
    scenes = spec["scenes"]
    script = []
    for si, s in enumerate(scenes):
        for tk in tokens(s["text"]): script.append(tk + (si,))
    lang = meta.get("language", "en"); mode = "whisper word alignment"
    if lang == "hinglish":
        pw = []; [pw.append(w[0]) for s_ in scenes for w in tokens(s_["text"]) if False]
        keys = []; [keys.append(w[0].strip(".,?!:;")) for s_ in scenes for w in tokens(s_["text"]) if w[1] and w[0].strip(".,?!:;") not in keys]
        times, cover = (asr_times(script, wav, proj, keys) if proj and meta.get("hinglish_asr", True) else (None, 0.0))
        if times and cover >= .55: mode = f"Hinglish island-wise ASR + fuzzy align ({cover:.0%} of words matched)"
        else:
            print(f"Hinglish ASR matched only {cover:.0%}: using pause-based timing (sentence-accurate, words approximate)." if proj else "")
            times, cover, mode = pause_times(script, len(scenes), wav, meta.get("silence_db")), 1.0, "pause-based (Hinglish)"
    else:
        times, cover = align(script, words)
        if cover < 0.6 and wav:
            print(f"Only {cover:.0%} of the script matched the transcript: switching to pause-based timing (sentence-accurate, words approximate)."); times, cover, mode = pause_times(script, len(scenes), wav, meta.get("silence_db")), 1.0, "pause-based (auto fallback)"
    for s in scenes: s["words"] = []
    for (w, key, ser, c1, si), t in zip(script, times): scenes[si]["words"].append({"t": t, "txt": w, "key": key, "serif": ser, "c1": c1})
    for i, s in enumerate(scenes):
        s["from"] = 0.0 if i == 0 else max(round(s["words"][0]["t"] - 0.08, 2), scenes[i - 1]["from"] + 0.8)
    for i, s in enumerate(scenes): s["to"] = scenes[i + 1]["from"] if i + 1 < len(scenes) else total
    for s in scenes:
        tone = (s.get("hero") or {}).get("tone") or s.get("glow_tone") or meta["accent"]; s["glow"] = GLOW.get(tone, GLOW["white"]); s["gt"] = tone
    # ---- stage elements: ids persist across scenes (window extends, props interpolate); entries missing from the next scene leave
    def when(v, s, default):
        if v is None: return default
        if isinstance(v, (int, float)): return round(s["from"] + float(v), 2)
        for w in s["words"]:
            if norm(w["txt"]) == norm(v): return round(w["t"], 2)
        sys.exit(f'scene {scenes.index(s)}: "at": "{v}" is not a word of that scene ("{s["text"]}")')
    els, live, sfx = {}, {}, []
    for i, s in enumerate(scenes):
        entries = list(s.get("stage", [])); keep = set(s.get("keep", []))
        ids = []
        for k, e in enumerate(entries):
            e = dict(e); e.setdefault("id", f"e{i}_{k}"); ids.append(e["id"])
            el = els.get(e["id"])
            at = when(e.get("at"), s, round(s["from"] + 0.15 + 0.14 * k, 2))
            if el is None:
                el = els[e["id"]] = {"id": e["id"], "type": e.get("type"), "wins": [], "ats": [], "frames": []}
                if not el["type"]: sys.exit(f'scene {i}: new element "{e["id"]}" needs a "type"')
            if e["id"] not in live:                          # (re)open a window
                el["wins"].append([s["from"], s["to"]]); el["ats"].append(at); el.setdefault("dflt", []).append(e.get("at") is None); live[e["id"]] = el
                if e.get("sfx") != "none": sfx.append((el, at, e))
            else: el["wins"][-1][1] = s["to"]
            last = el["frames"][-1] if el["frames"] else {"x": 540, "y": 900}
            fr = dict(last); fr["t"] = s["from"]
            for kk, v in e.items():
                if kk in FRAME_KEYS: fr[kk] = v
                if kk not in ("id", "at", "sfx") and kk not in el: el[kk] = v      # static props: first appearance wins
            el["frames"].append(fr)
        for eid in list(live):                                # leave unless listed or kept
            if eid not in ids:
                if eid in keep: live[eid]["wins"][-1][1] = s["to"]; live[eid]["frames"].append({**live[eid]["frames"][-1], "t": s["from"]})
                else: del live[eid]
    # ---- sound cues (observed in the references: one soft low thump per beat, a click/pop per new object, whoosh when the hero morphs)
    cues = []
    for i, s in enumerate(scenes):
        cues.append(("thump", round(s["from"] + 0.02, 2), 0.45))
        if i and (s.get("hero") or {}).get("shape") != (scenes[i - 1].get("hero") or {}).get("shape") and s.get("hero"): cues.append(("whoosh", round(s["from"] - 0.25, 2), 0.28))
    for el, at, e in sfx:
        ty, tone = el["type"], (e.get("tone") or "")
        if ty == "obj": cues.append(("pop", round(at - 0.03, 2), 0.3))
        elif ty in ("chip", "packet"): cues.append(("tick", round(at - 0.02, 2), 0.28))
        elif ty in ("card", "list", "compare", "search", "bars"): cues.append(("click", round(at - 0.02, 2), 0.28))
        elif ty == "counter":
            n = int(min(8, (e.get("dur") or 1.6) / 0.16)); cues += [("tick", round(at + 0.16 * j, 2), 0.16) for j in range(n)]
        elif ty == "stamp": cues.append(("error" if tone in ("", "red") else "ding", round(at - 0.02, 2), 0.35)); cues.append(("stamp", round(at + 0.03, 2), 0.45))
        elif ty == "cta": cues.append(("ding", round(at, 2), 0.3))
        elif ty == "big": cues.append(("pop", round(at - 0.03, 2), 0.3))
    cues.sort(key=lambda c: c[1]); keepc, lastn = [], {}
    for n, t, v in cues:                                       # thin out: same sound >= 0.18 s apart, anything >= 0.07 s apart
        if t < 0: continue
        if keepc and t - keepc[-1][1] < 0.07: continue
        if t - lastn.get(n, -9) < 0.18: continue
        keepc.append((n, t, v)); lastn[n] = t
    return meta, scenes, list(els.values()), keepc, cover, mode


def main():
    if len(sys.argv) < 2: sys.exit(__doc__)
    proj = os.path.abspath(sys.argv[1]); a = os.path.join(proj, "assets"); os.makedirs(os.path.join(a, "audio", "sfx"), exist_ok=True); os.makedirs(os.path.join(a, "fonts"), exist_ok=True)
    voice = next((os.path.join(proj, f) for f in sorted(os.listdir(proj)) if f.startswith("voice.") and not f.endswith(".json")), None)
    if not voice: sys.exit("Put the voice-over in the project folder as voice.wav / voice.mp3 / voice.m4a")
    spec = json.load(open(os.path.join(proj, "scenes.json"), encoding="utf-8")) if os.path.exists(os.path.join(proj, "scenes.json")) else None
    sys.path.insert(0, HERE); import clean_voice
    ov = os.path.join(proj, "words_override.json"); vedl = None
    if spec and spec.get("meta", {}).get("voice_clean", True) is not False and "--words" not in sys.argv:       # silence / filler / breath trimming + reel-edit voice chain (voice_clean.py)
        vc = os.path.join(proj, "voice_clean.wav"); wl0 = json.load(open(ov)) if os.path.exists(ov) else None
        if not os.path.exists(vc) or not os.path.exists(os.path.join(a, "voice_edit.json")) or os.path.getmtime(vc) < os.path.getmtime(voice) or spec["meta"].get("voice_reclean"):
            st, rem = clean_voice.clean(proj, len(wl0) if wl0 else None, spec["meta"].get("voice_chain", True) is not False, spec["meta"].get("sentence_gap", .22), spec["meta"].get("phrase_gap", .12), .45, wl0)
            print("VOICE:", f"{st['original_s']}s -> {st['clean_s']}s, {st['pauses_capped']} pauses capped, {st['fillers_removed']} fillers, {st['vowels_shortened']} vowels shortened, longest pause {st['longest_pause_after_s']}s, {st.get('wpm_before', '?')}->{st.get('wpm_after', '?')} wpm")
        voice = vc; vedl = json.load(open(os.path.join(a, "voice_edit.json")))
    wav = os.path.join(a, "audio", "voice.wav"); w16 = os.path.join(a, "voice16.wav")
    run("ffmpeg", "-v", "error", "-y", "-i", voice, "-ar", "48000", "-ac", "1", wav); run("ffmpeg", "-v", "error", "-y", "-i", voice, "-ar", "16000", "-ac", "1", w16)
    dur = float(run("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav).stdout.strip())
    hing = bool(spec) and spec.get("meta", {}).get("language") == "hinglish"
    words = (clean_voice.remap_words(json.load(open(ov)), vedl) if vedl else json.load(open(ov))) if os.path.exists(ov) else ([] if hing else transcribe(w16))
    json.dump(words, open(os.path.join(a, "words.json"), "w"))
    if hing and "--words" in sys.argv:
        print(f"{dur:.2f}s voice; Hinglish mode (no transcription). Speech segments: " + ", ".join(f"{s:.2f}-{e:.2f}" for s, e in speech_segments(w16, len(spec["scenes"]))))
        return
    if "--words" in sys.argv or not spec:
        print(f"{dur:.2f}s voice, {len(words)} words\n" + " ".join(f"{t}:{w}" for t, _, w in words)); return
    total = round(dur + 0.1, 2)                                              # the voice already ends 0.45 s after the last word (reel-edit: end <= 0.5 s after it)
    meta, scenes, els, cues, cover, mode = resolve(spec, words, total, w16, proj)
    for f in os.listdir(os.path.join(SKILL, "assets", "fonts")):
        if f.endswith(".ttf"): shutil.copy(os.path.join(SKILL, "assets", "fonts", f), os.path.join(a, "fonts", f))
    if not os.path.exists(GSAP): sys.exit("GSAP missing: run scripts/setup.sh")
    shutil.copy(GSAP, os.path.join(a, "gsap.min.js"))
    sys.path.insert(0, HERE); import audio_lib, fx_plan
    # ---- facts gate (reel-edit SKILL.md section 4 "on-screen facts", motion.md): every data visual is sourced or visibly labelled as a simplified example
    facts, notes = [], []
    for el in els:
        if el["type"] in ("counter", "bars"):
            src = el.get("src"); st = "sourced" if src else "illustrative"
            facts.append({"id": el["id"], "type": el["type"], "value": (f'{el.get("from")}->{el.get("to")}' if el["type"] == "counter" else el.get("values")), "status": st, "src": src or None})
            notes.append({"id": "note_" + el["id"], "type": "note", "text": (f"SOURCE: {src}" if src else meta.get("illustrative_label", "SIMPLIFIED EXAMPLE · NUMBERS ARE ILLUSTRATIVE")), "wins": el["wins"], "ats": [x + .1 for x in el["ats"]], "frames": [{"t": el["frames"][0]["t"], "x": 540, "y": 1452}], "dflt": [False] * len(el["wins"])})
        elif el["type"] in ("chip", "card", "big", "list", "compare", "stamp") and re.search(r"\d", json.dumps({k: el.get(k) for k in ("text", "lines", "items", "cards")}, ensure_ascii=False)):
            facts.append({"id": el["id"], "type": el["type"], "value": el.get("text") or el.get("lines") or el.get("items"), "status": "sourced" if el.get("src") else "illustrative" if el.get("illustrative") else "unchecked", "src": el.get("src")})
    uniq = {}
    for n_ in notes: uniq.setdefault((n_["text"], round(n_["wins"][0][0], 2)), n_)                  # one note per label per scene
    notes = list(uniq.values())
    els += notes
    json.dump(facts, open(os.path.join(a, "facts.json"), "w"), indent=1, ensure_ascii=False)
    nI = sum(1 for f_ in facts if f_["status"] == "illustrative"); nU = sum(1 for f_ in facts if f_["status"] == "unchecked")
    print(f"FACTS: {sum(1 for f_ in facts if f_['status'] == 'sourced')} sourced, {nI} data visuals labelled \"simplified example\", {nU} other on-screen numbers to verify before posting (assets/facts.json)")
    name = os.path.basename(proj); sfxdir = os.path.join(a, "audio", "sfx")
    worlds = json.load(open(os.path.join(SKILL, "assets", "worlds.json"))); LOG = os.path.join(audio_lib.PROJECTS, "_style_log.json")
    try: slog = json.load(open(LOG))
    except Exception: slog = []
    wname = meta.get("world")
    if wname not in worlds:                                                    # auto: never repeat either of the last two reels' worlds (variety.md section 1)
        last2 = [r["world"] for r in slog if r.get("reel") != name][-2:]
        pool = [w for w in worlds if w not in last2] or list(worlds)
        wname = pool[audio_lib.seed(name, "world") % len(pool)]
    wd = worlds[wname]; meta["world"] = wname; meta["world_def"] = wd
    print(f"WORLD: {wname} ({wd['label']})" + (f"; last two were {', '.join(r['world'] for r in slog[-2:])}" if slog else ""))
    if not os.path.exists(os.path.join(sfxdir, "thump.wav")): run(sys.executable, "-I", os.path.join(HERE, "make_sfx.py"), sfxdir)
    # ---- music bed (shared library, energetic from second 1, beat grid) -> beats drive punches + the glow/particle pulse
    music = None
    if meta.get("music", True) is not False:
        music = audio_lib.pick_music(total, name, tuple(meta.get("music_moods", ("upbeat", "bright", "curious"))), meta.get("music_bpm"), meta.get("music_file"), os.path.join(a, "audio", "bgm.mp3"), meta.get("music_style", "premium"), tuple(meta.get("music_skip", ())), genres=wd.get("music_genres"))
        if not music: print("WARNING: no music library found (set music_dir in config.local.json, or run scripts/build_music_index.py on a folder of tracks you may use): building WITHOUT music. Every explainer should have a bed.")
    beats = music["beats"] if music else []
    fx = fx_plan.plan_fx(scenes, els, total, beats, name, wd.get("trans"), wd.get("punch", 1.0))
    for tr in fx["trans"]:                                                    # no empty frames after a cut: default-timed objects of the incoming scene are already there at the cut
        s_, k_ = scenes[tr["i"]], 0
        for el in els:
            for wi, (wa, wb) in enumerate(el["wins"]):
                if abs(wa - s_["from"]) < .01 and el.get("dflt", [])[wi:wi + 1] == [True]: el["ats"][wi] = round(s_["from"] + .03 * k_, 2); k_ += 1
    plan = fx_plan.plan_cues(scenes, els, fx, total, name)
    DUR = {"whip": (.2, .9), "hit_soft": (.1, 1.2), "impact": (.3, 2.5), "riser": (.7, 1.8), "pop": (.05, .6), "tick": (.03, .4), "click": (.03, .5), "notif": (.2, 1.5), "success": (.2, 1.5), "error": (.1, 1.2), "negation": (.1, 1.2)}
    SYN = {"whip": "whoosh", "hit_soft": "thump", "impact": "stamp", "riser": "riser", "pop": "pop", "tick": "tick", "click": "click", "notif": "ding", "success": "ding", "error": "error", "negation": "error"}
    cues = []
    for c in plan:
        f = audio_lib.pick_sfx(c["role"], name, DUR.get(c["role"], (0, 9)))
        if f: src = os.path.join(audio_lib.SFX, f); dst = f"{c['role']}__{os.path.basename(f)}"; shutil.copy(src, os.path.join(sfxdir, dst))
        else: dst = SYN[c["role"]] + ".wav"
        d = float(run("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", os.path.join(sfxdir, dst)).stdout.strip() or 0.5)
        t = c["t"] if "end_at" not in c else c["end_at"] - min(d, c["max_dur"])
        cues.append({"role": c["role"], "t": round(max(0.0, t), 2), "vol": c["vol"], "path": f"assets/audio/sfx/{dst}", "max_dur": c["max_dur"]})
    last_w = scenes[-1]["words"][-1]["t"] if scenes[-1]["words"] else dur - .5
    cta_t = next((s["from"] for s in scenes[::-1] if any(e["type"] == "cta" and any(a_ >= s["from"] - .01 and b_ <= s["to"] + .01 for a_, b_ in e["wins"]) for e in els)), scenes[-1]["from"])
    json.dump({"total": total, "voice_end": round(min(dur, last_w + .6), 2), "cta_t": cta_t, "music": ({"path": "assets/audio/bgm.mp3", **{k: v for k, v in music.items() if k != "beats"}} if music else None), "cues": cues}, open(os.path.join(a, "audio_plan.json"), "w"), indent=1)
    if music: open(os.path.join(a, "music_credit.txt"), "w").write(f"{music['file']} | {music['source']} | {music['licence']}\n")
    audio = [f'<audio id="voice" src="assets/audio/voice.wav" data-start="0" data-duration="{dur:.2f}" data-track-index="1" data-volume="1"></audio>']   # preview only: the final audio is assets/audio/master.wav (mix_audio.py)
    data = {"meta": meta, "total": total, "scenes": [{k: v for k, v in s.items() if k in ("from", "to", "words", "hero", "kicker", "glow", "gt")} for s in scenes], "els": els, "fx": fx, "beats": beats}
    json.dump({"scenes": [{"from": s["from"], "to": s["to"], "words": [{"t": w["t"], "txt": w["txt"]} for w in s["words"]]} for s in scenes], "last_word": round(last_w, 2), "total": total}, open(os.path.join(a, "captions.json"), "w"), ensure_ascii=False)
    css = open(os.path.join(HERE, "explainer.css"), encoding="utf-8").read(); eng = open(os.path.join(HERE, "engine.js"), encoding="utf-8").read()
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=1080, height=1920"/><title>{meta["handle"]}</title>
<script src="assets/gsap.min.js"></script><style>{css}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1080" data-height="1920">
{chr(10).join(audio)}
<div id="cam"><div id="glow"></div><canvas id="fx" width="1080" height="1920" data-layout-allow-overflow></canvas><div id="stage"></div></div><canvas id="grain" width="540" height="960" data-layout-ignore></canvas>
<svg width="0" height="0" style="position:absolute"><filter id="hb" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur id="hbv" stdDeviation="0 0"/></filter></svg>
<div id="hl"></div><div id="cv"></div>
<div id="hud"><div id="brand"></div><div id="series" data-layout-ignore></div><div id="rail"><div id="fill"></div></div><div id="kicker" data-layout-ignore></div><div id="cap"></div></div>
</div>
<script>window.EXPLAINER={json.dumps(data, ensure_ascii=False)};</script>
<script>{eng}</script></body></html>"""
    open(os.path.join(proj, "index.html"), "w", encoding="utf-8").write(html)
    try:
        slog = [r for r in slog if r.get("reel") != name] + [{"reel": name, "world": wname, "music": music["file"] if music else None, "genre": music.get("genre") if music else None, "trans": [t["type"] for t in fx["trans"]], "date": __import__("datetime").date.today().isoformat()}]
        os.makedirs(os.path.dirname(LOG), exist_ok=True); json.dump(slog, open(LOG, "w"), indent=1)
    except Exception: pass
    for f, body in {"hyperframes.json": {"$schema": "https://hyperframes.heygen.com/schema/hyperframes.json", "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry", "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}},
                    "meta.json": {"id": name, "name": name}, "package.json": {"name": name.replace("_", "-"), "private": True, "type": "module"}}.items():
        if not os.path.exists(os.path.join(proj, f)): json.dump(body, open(os.path.join(proj, f), "w"), indent=2)
    json.dump({"scenes": [{"i": i, "from": s["from"], "to": s["to"], "text": s["text"]} for i, s in enumerate(scenes)], "fx": fx, "events": sorted(set([round(s["from"], 2) for s in scenes] + [round(x, 2) for e in els for x in e["ats"]] + [p["t"] for p in fx["punches"]] + [x["t"] for x in fx["trans"]] + [x["t"] for x in fx["shocks"]])), "cues": cues, "script_word_match": round(cover, 2), "timing_mode": mode, "last_word": round(last_w, 2), "total": total}, open(os.path.join(a, "timing.json"), "w"), indent=1)
    print(f"{proj}/index.html  {total}s  {len(scenes)} scenes  {len(els)} elements  {len(cues)} sfx  {len(fx["trans"])} transitions  {len(fx["punches"])} punches  music: {music["file"] if music else "none"}  script/voice match {cover:.0%}  timing: {mode}")
    r = run(sys.executable, "-I", os.path.join(HERE, "mix_audio.py"), proj)
    print("MIX:", " ".join(l.strip() for l in r.stdout.splitlines() if any(k in l for k in ("median", "min", "lufs", "gain", "sfx_per", "silent"))) or r.stderr[-400:])
    if cover < 0.8: print("WARNING: <80% of script words matched the transcript: re-record, or fix words_override.json ([[start,end,word],...]) and rebuild.")


if __name__ == "__main__":
    main()
