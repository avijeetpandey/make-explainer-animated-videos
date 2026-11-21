# Energy, music, SFX and transitions (added 21 Nov 2026)

## Why the first version felt dull (User feedback on the first render)
Measured on that cut: no music bed, 7 synthetic "thump/tick/pop" sounds per 10 s that all sounded alike, 50% of the time nothing moved on the stage, scenes changed by dissolve only (no camera, no transition), small mono labels (15–24 px), 18-word sentences held for 4 s with one visual, nothing locked to a beat. The reference reels are voice-only but they are *dense*: something changes every sentence and the layout is large. A music-less explainer without that density feels empty; with music it must be mixed properly.

## Rules adopted from professional talking-head editing, and how they are applied here
These are established editing rules (music bed, SFX by job, voice-first mix, camera and transition grammar) adapted to a faceless explainer.
| Practice | explainer implementation |
|---|---|
| Every reel has a music bed, full energy from second 1, 100–126 BPM, bar-aligned start, YouTube Audio Library / Mixkit with the licence line, never the last 3 reels' track | `audio_lib.pick_music`: same scoring over `music/INDEX.json` (energy ≥ 72, BPM near 112, mood upbeat/bright/curious), precomputed bar-aligned `starts`, skips the last 3 tracks used (its own log, plus an optional second pipeline's log via `pipeline_root`), writes `assets/music_credit.txt` |
| Bed ≈ −20 dB under the voice, carved under speech, fades with the last word, lifts under the CTA | `mix_audio.py`: sidechain-style carve (−5.5 dB, 15 ms / 600 ms), level-riding that follows the voice loudness, bed leveling (slow compressor), ×1.3 lift at the CTA, fade-out with the last word, 0.25 s fade-in |
| Voice 10–14 dB over music + SFX (median), never < 8 dB | the music level is SOLVED per project from the stems (bisection), reported in `assets/mix_report.json`; the voice is never processed |
| Master −14 LUFS, TP ≤ −1 dBTP | two-pass linear loudnorm to −14 / −1.5 |
| SFX filed by job (whip, hit_soft, impact, riser, pop, tick, click, notif, success, error, negation); one file per role per reel; levelled to −10 dBFS then × 0.12–0.36; land 40 ms early; never two within 0.3 s; the sentence before the CTA silent; ≥ 2 silent spots; one riser → hit per reel | `audio_lib.pick_sfx` over `sfx/ROLES.json`, `fx_plan.plan_cues`, `mix_audio.py` (8 ms in / 40 ms out, 10% shared-room reverb on the bus) |
| Sound every 1.5–3 s, every visual event has one | density capped at ≈ 6 per 10 s, least important dropped first (tick < hit < pop/click < transition/impact) |
| Transitions only where the idea changes, ≤ ~1 per 9 s, ≥ 5 s apart, none in the first 3 s / last 4 s, never the same type twice, each with a sound 40 ms early | `fx_plan.plan_fx`: whip_h → blur_in → whip_v → push rotation, eligibility = hero shape change or < 50% of stage ids carried over, never right before a stamp |
| Camera: slow drift always on, opening snap, punches 0.09 s up / 0.5 s settle on emphasis words (numbers, negations, key terms) ≥ 1.4 s apart, shake every 3rd, snap to a beat only if it is ≤ 120 ms before the word | `engine.js camAt()` + `fx_plan` punches; ≈ 2.4 per 10 s |
| Visible change at least every 3 s (`fill_gaps`) | gaps > 2.8 s get a small punch on the middle word; QA fails above 3.2 s |
| One texture over everything (grain), no glass panels / flashes / light streaks on whips | seeded grain layer jittered at 12 fps; whips are camera smear only (directional blur), no overlays |
| Settle, don't pop; exits faster than entrances | ease-out-cubic entrances 0.42 s, 16 px travel; whip exits cut in 0.06 s |
| Cut graphics on the beat | punches snap to the music beat grid; glow, dust and particle size pulse on every beat (strong on the bar) |

## Music selection: premium, not pop (21 Nov 2026, user feedback: "too chapri")
The first pick ("What About Action", genre dance-pop) measured 44% low / **50% mid** / 2.3% highs: a bright melodic lead that sounds cheap under a voice. The scoring now (`audio_lib.music_score`, style `premium`):
- genre: techno / tech-house / deep-house / house / "technology" +10–12, electro-house / electronic / cinematic / rhythmic-underscore +6; dance-pop, pop, indie-pop, synthpop, electropop −38…−45, funk −34, corporate −28, ambient/chillout/downtempo −14 (too soft to drive), library −14
- spectrum (INDEX centroid): ≤ 1700 Hz +10, ≤ 2100 +4, > 2600 −10: darker = more expensive
- measured with librosa on each track's best start (`assets/music_features.json`): drive (onset strength), groove regularity, share of energy at 30–120 Hz, share above 5 kHz, share of mids; rewards a driving, bass-led groove and penalises a shrill or mid-heavy lead
- must hit from second 1 (intro ≤ 1.5 s), BPM near 122, energy ≥ 72, never the last 3 tracks of either pipeline
- a bright bed (centroid > 1800) is tamed with −2.5 dB above 6 kHz and a 35 Hz high-pass at trim time
Result for the GTA reel: `mixkit/house-02-744` (house, 123 BPM, groove 0.87, drive 2.6, 70% low end, 0.55% highs); next: `hazy-after-hours-132` (technology), `deep-techno-ambience-134` (techno, calmer). To audition: `python3 -I scripts/alt_mix.py <project> mixkit/<track>.mp3` (same mix, other bed, seconds, no re-render).

## Authoring rules that keep it energetic
1. **Split sentences at commas** when a sentence has > 12 words or lasts > 3.5 s: each half is its own scene with its own visual (v2 of the GTA reel went 13 → 21 scenes).
2. **One new thing per scene**, large: objects ≥ 260 px wide (`objScale` 1.3 is automatic), labels ≥ 28 px, counters 124 px, hero words 270–360 px wide.
3. **Reveal moments get `"shock": true`** (impact ring + sound): the twist word, the solution name, the final question. Max 4 per reel.
4. **Stamps** (`NOT A BUG`, `EXPENSIVE`) land on the spoken word via `"at"`; the first stamp gets the riser → hit build automatically.
5. **Fill the upper stage**: when a diagram sits low, keep a hero word/shape above it (a morphing hero is the cheapest way to add motion).
6. **Check the cut frames**: snapshot at `T-0.07, T, T+0.1` of every transition; the incoming scene must already show content at T (the builder times default objects to the cut).
7. **Never use whisper on Hinglish for timing** (see SKILL.md); `meta.language: "hinglish"`.

## Options (`scenes.json → meta`)
`music: false` (voice + SFX only; only when asked) · `music_moods: ["upbeat","bright","curious"]` · `music_bpm: 112` · `music_file: "mixkit/valley-sunset-127.mp3"` (force a track from the music/SFX library) · `objScale: 1.3` · `drift: 0.04` (camera push per scene) · scene key `shock: true`.

## Files
`scripts/audio_lib.py` (library access) · `scripts/fx_plan.py` (punches, transitions, cue list) · `scripts/mix_audio.py` (stems → master.wav + mix_report.json) · `scripts/finalize.sh <picture.mp4> <out.mp4> assets/audio/master.wav` (mux).
The picture is rendered WITHOUT the mix (the composition keeps only the voice for Studio scrubbing); the mastered `master.wav` is muxed in, so the mix can be re-solved in seconds without re-rendering.
