# Changelog

## 0.8.0 (22 Nov 2026): calm premium default ("ink") + layout gate
Why: owner feedback on 0.7 output: too flashy, not premium, overlaps and uneven gaps. See `references/DESIGN_PRINCIPLES.md`.
- New default worlds `ink_blue / ink_violet / ink_teal / ink_amber`: near-black ink, ONE accent, neutral glass, quiet type (serif-italic accent word), obsidian 3D materials, no flashes / shock rings / opening snap, half-strength punches. The 0.7 loud worlds are now `tier: expressive` (opt-in).
- **`layout_check.py`**: headless-Chrome probe that fails on overlaps, caption-zone intrusions, margin / bottom-UI violations and flags tight / loose / unbalanced stacks; engine exposes `window.__layout(t)` (3D objects boxed analytically).
- Karaoke captions (unspoken words dim, not hidden) + `text-wrap: balance`; automatic label offset under cubes / db; compare cards sized for phones; `safe_zone_check.py` is theme-aware.

## 0.7.0 (22 Nov 2026): the polished studio look (loud: superseded as default by 0.8)
Why: the first look (white particles + wireframes on near-black) made every video look the same and "junior". Studied 17 more reels (see STYLE_ANALYSIS second batch) and rebuilt the visual layer.
- **New `studio.js`**: 6 animated multicolour backdrops (`aurora`, `fluted`, `duotone`, `studio`, `cream`, `deep`) crossfaded per scene, scene `zone` colours, scene `flash`, light/dark theme flip.
- **Real 3D** (three.js, vendored, MIT): stage type `gl` with 13 kinds (orb, knot, torus, ring, slab, cubes, gem, capsule, db, server, coin, shield, ribbon); procedural studio environment built from the world's colours; verified GPU WebGL inside HyperFrames.
- Glass UI cards, window chrome, status `rows`, `pill`, `big` styles (chrome / outline / grad), caption styles `glow` / `lime`, per-element entrances `in`, card tilt, tinted bars.
- 4 studio worlds (default) + the 4 classic worlds kept; Anton (OFL) condensed font added.
- Fixes found while building: counters measured with empty text (off-centre), outline text failed the HyperFrames contrast lint, colours washed out (sRGB handling), glossy materials flattened by emissive copy.


## 0.6.0 (21 Nov 2026) - public release
- Generic by default: per-user settings moved to a git-ignored `config.local.json` (handle, music/SFX library paths, drive destination, extra kit linter) and a git-ignored `PERSONAL.md`; the placeholder handle is `@yourhandle`.
- New generic tools: `seo_research.py`, `kit_lint.py`, `build_music_index.py` (index your own tracks; reproduces the reference numbers: BPM, centroid, bar-aligned starts), `make_linkedin_image.py`, `config.py`.
- Posting kit rebuilt as a research-first workflow (autosuggest + web searches + source verification + `research_notes.md`), LinkedIn post + image, `publish_check.py` checklist.
- Docs: README, USAGE, TWEAKING, ARCHITECTURE, PUBLISHING, LESSONS.

## 0.5.0 - must-haves
- **Worlds + style log** (`assets/worlds.json`: mono_pulse, blueprint, amber_signal, terminal_green; never repeats either of the last two videos' world; re-edits keep theirs).
- **Frame-0 headline** (`meta.headline`) and **cover A/B** (`make_cover.py`, auto-fit text, 3:4 feed-crop check).
- **Facts gate**: counters/bars need `src` or get a "SIMPLIFIED EXAMPLE" label; `assets/facts.json` lists unverified numbers.
- **Safe-zone gate** (`safe_zone_check.py`): bottom caption zone, right button strip, with a shaded review sheet.
- **Subtitles** (`make_srt.py`), **gated upload** (`upload_drive.sh`: refuses without explicit approval flags; new subfolder; size verification; re-edits in `/vN/`).
- **Hinglish timing**: island-anchored (acoustic speech islands + per-island whisper-medium + fuzzy alignment); a hand-timed `words_override.json` always wins.

## 0.4.0 - premium music
- Music picker rebuilt: genre scoring (techno / tech-house / house / technology / cinematic up; pop, funk, corporate, ambient down), spectral centroid, measured drive/groove/low-end/brightness features, brightness taming, `alt_mix.py` to A/B another bed in seconds. Re-edits keep their track.

## 0.3.0 - voice
- `clean_voice.py`: pause capping (0.22 s sentence / 0.12 s phrase, cut from the middle), filler and breath removal, stretched-vowel shortening, retake removal, +/-3 dB level matching, speech chain; edit list `assets/voice_edit.json`; words re-mapped through the edit list; video ends ~0.5 s after the last word.

## 0.2.0 - energy and sound
- Camera system (opening snap, drift, punches with shake), transitions at idea changes (whip h/v, focus pull, push), impact rings, beat-locked pulse, film grain, no empty frames after a cut, bigger graphics.
- Music bed + SFX by role + a mix solved from stems (voice 10-14 dB over music+SFX, never < 8 dB, -14 LUFS, TP <= -1.5): `audio_lib.py`, `fx_plan.py`, `mix_audio.py`; QA gates for all of it.

## 0.1.0 - first version
- Code-rendered look (near-black stage, particle hero, wireframe diagrams, word-synced captions, counters, stamps, recap, CTA), HyperFrames + Canvas, whisper alignment, Hinglish pause timing, `build_explainer.py`, `qa_explainer.py`.
