# Tweaking guide

Everything is plain JSON / JS / CSS / Python. No build step.

## A new look ("world")
Add an entry to `assets/worlds.json`:
```json
"my_world": {"label": "...", "bg": "#05070a", "glow": "rgba(255,120,80,.09)",
  "tones": {"white": "#fff", "red": "#ff5a5a", "blue": "#ffa94d", "yellow": "#ffd43b", "green": "#69db7c", "violet": "#da77f2"},
  "caption": "underline|highlight|serif|mono", "overlay": "none|grid|scan", "grain": 0.5, "drift": 0.04, "punch": 1.0,
  "trans": ["whip_h","blur_in","whip_v","push"], "music_genres": {"house": 5, "techno": 3}}
```
`tones` keep their meaning (`blue` = primary/active, `red` = failure ...) but not their hue. New caption style or overlay: add a CSS block at the end of `scripts/explainer.css` (`.cap-<name> #cap .k {...}`, `.ov-<name> {...}`). Use it with `"world": "my_world"` or let the rotation pick it.

## A new hero shape
`scripts/engine.js` -> `shape(h)`: add `else if (k === "myshape") { x = ...; y = ...; z = ...; }` inside the per-particle loop (positions in pixels around 0). Use it as `"hero": {"shape": "myshape", "r": 240}`. Text and SVG paths already work (`shape: "text"`, `"path"` with a 100x100 SVG path `d`).

## A new element type
1. DOM: in `engine.js` find the `EL.forEach(e => { ... })` builder and add `else if (e.type === "mytype") { n = mk("div", "mytype", ...); }`.
2. Per-frame behaviour: in `render()` inside the DOM loop add an `else if (el === "mytype") {...}` that sets text/styles from `t` (pure function of time!).
3. Style it in `explainer.css`. Optionally give `fx_plan.py`/`build_explainer.py` a rule for its sound (`plan_cues`) and its facts check.
Canvas elements (drawn with the 2D context) follow `drawObj` / `drawLink`.

## New wireframe kind
`objEdges(e, f)` in `engine.js`: return a list of `[[x,y,z],[x2,y2,z2]]` edges for `kind: "mykind"`.

## Transitions, punches, camera
`scripts/fx_plan.py`: `TYPES` (order), budgets (`maxn`, gap >= 5 s, none in the first 3 s / last 4 s), punch candidates (`NEG` words), fill-gap threshold (2.8 s). `engine.js` -> `camAt(t)`: the motion of each transition type, punch amount/shake, opening snap, drift.

## Sound
- SFX roles and volumes: `fx_plan.plan_cues` (role per element type, volume 0.12-0.36, density cap, silent sentence before the CTA).
- Your own SFX: put files in `library/sfx/<role>/` (or `sfx_dir`). Roles: whip, hit_soft, impact, riser, pop, tick, click, notif, success, error, negation.
- Music scoring: `audio_lib.py` -> `PREMIUM_GENRES`, `CHEESY_GENRES`, `music_score()` (genre, centroid, measured drive/groove/low-end/brightness). Force a track: `"music_file": "<name in INDEX.json>"`; no music: `"music": false`.
- Mix targets: `mix_audio.py` (`--target 12` dB median; min 8 dB; duck depth/release; level riding exponent; lift under the CTA).

## Voice cleanup
`clean_voice.py`: gap caps (`meta.sentence_gap`, `meta.phrase_gap`), filler detector thresholds (`sus`: flux percentile, voicing, zero-crossing), minimum run (0.16 s), level matching clamp (+/-3 dB), `VOICE_CHAIN` (ffmpeg filter string). Add filler WORDS (needs word timings) in the standalone/inside-word logic.

## Language
Any language whisper cannot read: `"language": "hinglish"` (island timing). Captions use Hanken Grotesk (Latin only): for Devanagari or other scripts add a font with those glyphs in `explainer.css` (`@font-face`) and the `font-family` stacks. For a language whisper reads well, leave `language` unset.

## Replace GSAP
It is only the clock: `tl.to({}, {duration: T, ease: "none", onUpdate(){ render(this.time()); }})`. Any seekable timeline works (Anime.js, WAAPI): keep `render(t)` pure.

## Safe zones
`safe_zone_check.py` zones and thresholds; header/caption positions are in `explainer.css` (`#brand`, `#rail`, `#kicker`, `#cap`).

## Tests
`python3 -m unittest discover tests` (parsing, alignment, voice cleanup on synthetic audio, lint, config, worlds).
