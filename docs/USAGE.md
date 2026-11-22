# Usage guide

`K` = the skill folder (e.g. `~/.claude/skills/make-explainer-animated-videos`). Replace `my_video` with your project name.

## 0. One-time setup
```bash
bash K/scripts/setup.sh          # Node 22+, ffmpeg, whisper-cli + ggml-small.en, GSAP cache, fonts, numpy
cp K/config.example.json K/config.local.json   # edit: handle, library paths, drive destination
pip install librosa numpy         # only if you will index your own music
```
Music: put tracks you may use in a folder and run `python3 -I K/scripts/build_music_index.py <folder>` (add `--meta meta.json` for genre/licence). Point `music_dir` at it. Rank what the picker would choose: `python3 -I K/scripts/audio_lib.py --rank premium`.

## 1. Record
Quiet room, mouth ~10 cm from the mic, one sentence per breath, ~0.3-0.5 s of silence between sentences (essential for Hinglish timing). If you slip, repeat the sentence from its start; silence is cut for free, filler sounds are not. Save as `~/Documents/explainer-videos/my_video/voice.wav` (or .mp3/.m4a). No microphone yet? `say -v Samantha -o voice.aiff -f script.txt` (macOS) makes a test voice.

## 2. Write the storyboard
`scenes.json` = `meta` + one scene per spoken sentence (8-18 words; split long ones at commas). Start from `examples/sample/scenes.json`; every field is documented in `references/STAGE_LIBRARY.md`. Rules of thumb: one new visual idea per scene, persist the diagram (same `id`s), mark meaning words with `*key*`, put a sourced `src` on every counter, `"shock": true` on 3-4 reveals, cards <= 780 px wide, content within y 480-1450.
With Claude Code just say `/make-explainer-animated-videos`, attach the voice and paste the script; it writes this file for you.

## 3. Build (also cleans the voice and masters the audio)
```bash
python3 -I K/scripts/build_explainer.py ~/Documents/explainer-videos/my_video
```
It prints: the world (look), voice cleanup stats, facts register, transitions/punches, music chosen, mix balance, "script/voice match %". Below 80% match = the script differs from the recording. Read `assets/voice_edit.json` (every removed span + reason). Re-solve only the mix: `python3 -I K/scripts/mix_audio.py <proj>`. Try another bed: `python3 -I K/scripts/alt_mix.py <proj> <track>`.

Language: `"language": "hinglish"` in `meta` for Roman-script Hinglish (or any language whisper cannot read). A hand-timed `words_override.json` (`[[start, end, "word"], ...]`, in the ORIGINAL voice's timeline) always wins.

## 4. Check, look, render
```bash
cd ~/Documents/explainer-videos/my_video
python3 -I K/scripts/layout_check.py .                                   # MUST print PASS: overlaps, margins, caption zone, cuts, spacing
npx --yes hyperframes@0.8.209 check                                  # 0 errors required
npx --yes hyperframes@0.8.209 snapshot --at 1,6,12,20               # look at the frames
npx --yes hyperframes@0.8.209 preview                                # Studio preview (scrub in the browser)
npx --yes hyperframes@0.8.209 render -o renders/picture.mp4 -q delivery -f 30   # -q draft while iterating
bash K/scripts/finalize.sh renders/picture.mp4 renders/my_video_final.mp4 assets/audio/master.wav
python3 -I K/scripts/qa_explainer.py . renders/my_video_final.mp4     # loudness, balance, voice, pacing, budgets
python3 -I K/scripts/safe_zone_check.py . renders/my_video_final.mp4  # platform UI zones; read qa/safe_sheet.jpg
```
The picture is rendered silent-mixed on purpose: `finalize.sh` muxes the mastered audio, so remixing never needs a re-render.

## 5. Publish pack
```bash
# add to scenes.json meta:  "headline": {"lines": ["Belief?", "Twist!"], "t1": 2.3},
#                           "cover": {"a": {"t": 1.0, "lines": ["BIG PROMISE", "IN 8 WORDS"], "accent": 1, "kicker": "TOPIC"}, "b": {...}}
python3 -I K/scripts/make_cover.py .          # covers/cover_a.jpg, cover_b.jpg, grid_check.png
python3 -I K/scripts/make_srt.py .            # renders/my_video.srt
python3 -I K/scripts/seo_research.py "topic" "related" --out seo_research.json   # then web searches, then write posting_kit.md (assets/posting-kit-template.md)
python3 K/scripts/kit_lint.py posting_kit.md  # PASS
python3 -I K/scripts/make_linkedin_image.py . --kicker "TOPIC" --headline "Big *idea*." --points "one|two|three"
python3 -I K/scripts/publish_check.py .       # checklist
```
## 6. Upload (gated)
```bash
bash K/scripts/upload_drive.sh . --dry-run                              # shows destination + files
bash K/scripts/upload_drive.sh . --approved-video --approved-cover      # only after YOU approved both; needs rclone configured
```
Destination: `<drive_dest>/my_video/` (re-edits `my_video_v2` go to `my_video/v2/`). Never overwrites a previous cut.

## Re-edits
Copy the folder to `my_video_v2/` and change there; the world and music track are kept unless you change them.
