# Changelog

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
