# Lessons learned (gotchas that cost time, so they don't cost yours)

**Audio / voice**
- A fixed `silencedetect` dB threshold fails after the denoise/compress voice chain (it raises the noise floor): use the adaptive speech detector (`clean_voice.speech_islands`).
- whisper-cli: run **one island at a time** (parallel runs silently produced nothing), never `-l hi -ml 1` (splits Devanagari characters), `-l en` on Hinglish gives usable Roman text only with a Roman prompt, and a long `--prompt` on a whole-file run can make it skip the first seconds. Fast Hinglish gets garbled: anchor on acoustic islands, treat ASR as soft evidence.
- Judge the mix per second of **speech**, not per second: pause seconds and sound-effect seconds dominate the "worst" number. Level every SFX to -10 dBFS peak first, THEN apply the role volume (0.12-0.36); otherwise effects land 10 dB too loud. Level the music bed (slow compressor) and ride it with the voice before solving its gain.
- Detector sanity: validate against a hand-timed ground truth, but when two sources disagree, look at the energy structure (islands) before trusting either.

**Music**
- Genre tag + spectral centroid beat "mood" tags: a dance-pop track (centroid 2.6 kHz, 50% mid-range energy) sounds cheap under a voice; house/techno beds (centroid ~1.1-1.4 kHz, 70-85% of energy under 120 Hz, groove regularity 0.8+) sound expensive and still drive.
- A re-edit of the same video should keep its track unless asked.

**Rendering / HyperFrames**
- Pin the CLI (`hyperframes@0.8.209`); `check` flags `data-layout-ignore`-able texture text, real contrast and overlaps; a JS error in the page shows up as `page_error` and then a pile of bogus `text_occluded` findings: fix the error first.
- Grain makes the raw render huge (about 140 MB for 38 s): re-encode in `finalize.sh` (x264 crf 20, max 10 Mbps).
- When you wait for a background render, wait for a picture NEWER than the previous artifact; a stale `render.log` ends the wait too early.
- `python3 -I` does not put the script folder on `sys.path`: run linters that import siblings without `-I`.
- zsh: `$var[$i:v]` is array-subscript syntax (write `${var}[...]`); `rm -f s*.aiff` errors when nothing matches; macOS `sed -i` needs `-i ''`.

**Layout / platforms**
- Camera punches scale content (1.04-1.2x): a card at x 70-1010 reaches the right button strip while it zooms. Keep cards <= 780 px wide and stage content within y 480-1450; the safe-zone gate samples frames at scene midpoints, including punch frames.
- Instagram draws its own UI over the top 250 px, bottom 500 px, right 150 px.

**Honesty**
- Never state a company/product fact you could not source (a plausible-sounding claim about a game studio's engine was NOT supported by any documentation, so the copy says it as a concept). Label invented numbers on screen.
