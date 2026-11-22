# Architecture

```
voice.wav + scenes.json
        |
build_explainer.py ──► clean_voice.py        voice_clean.wav, assets/voice_edit.json (edit list)
        |   ──► alignment (whisper words / island-anchored Hinglish / words_override remapped through the edit list)
        |   ──► resolve(): scene times, element windows + keyframes, facts register, notes
        |   ──► fx_plan.py: transitions, camera punches, impact rings, SFX cue list
        |   ──► audio_lib.py: music pick (+ beat grid), SFX files by role
        |   ──► mix_audio.py: duck/ride/level music, place SFX, solve the music gain for the voice balance, loudnorm → master.wav
        └──► index.html (engine.js + explainer.css + data inlined)  ──►  hyperframes render  ──►  picture.mp4
                                                                  finalize.sh (mux master.wav, x264) ──► final.mp4
```
## The one idea: everything is a pure function of time
`studio.js` (loaded before the engine) draws the per-scene backdrops on a 2D canvas and, when the storyboard has `gl` elements, renders three.js objects on a WebGL canvas, also as a pure function of `t`; it also owns the light/dark theme flip. `engine.js` exposes `render(t)`. One paused GSAP tween calls it on every seek, so renders are deterministic and scrubbable. Canvas (dust, hero particles, wireframes, links, packets, impact rings, grain) and DOM (captions, chips, cards, counters, headline) are both positioned from `t`; element lifetimes and keyframes are precomputed by `resolve()`; randomness is seeded (no `Math.random`, no wall clock).

## Data model
`scenes.json` -> scenes {text, hero, stage[], keep[], shock}; `stage` entries become elements {id, type, wins[[t0,t1]], ats[], frames[{t, x, y, ...props}]}; an element listed again in the next scene persists and its numeric props glide over 0.7 s.

## Camera
`camAt(t)` = scene drift + opening snap + punches + transitions (whip = x/y slide with SVG directional blur, focus pull = blur + scale, push = scale + blur) + a tiny beat pulse; applied to the canvas with `ctx.transform`, to the DOM stage with CSS transform, and the blur to the `#cam` wrapper.

## Audio
Stems are numpy arrays at 48 kHz. Voice untouched (after `clean_voice`), music = leveled, carved (sidechain-style envelope) and ridden with the voice, SFX = each file leveled to -10 dBFS peak then x role volume + 10% room reverb. The music gain is solved by bisection so that per-second (speech seconds only) voice-over-residual has median 12 dB and minimum >= 8 dB; then two-pass linear loudnorm to -14 LUFS / -1.5 dBTP.

## Gates
`qa_explainer.py` (video/audio/voice/pacing), `safe_zone_check.py`, `publish_check.py`, `kit_lint.py`, `upload_drive.sh` (approval flags).
