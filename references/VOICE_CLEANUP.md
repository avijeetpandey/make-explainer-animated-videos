# Voice cleanup (added 21 Nov 2026)

User note on the v2 draft: the voice still had silences and "ahh" fillers; the skill did not trim them. This page is the fix and the editing practice behind each rule.

## What runs (automatically, `build_explainer.py` → `scripts/clean_voice.py`)
| Step | Rule | Source |
|---|---|---|
| Pause tightening | sentence gaps (≥ 0.30 s) → 0.22 s, phrase gaps (0.12–0.30 s) → 0.12 s, shorter ones untouched. The cut is taken from the middle of the gap, so the room tone at both ends stays and any breath inside the gap goes with it. Options `meta.sentence_gap`, `meta.phrase_gap` | standard editing practice: pauses over ~0.3 s go, pads 0.04-0.08 s, silences <= 0.12 s inside a phrase |
| Lead / tail | first word ≈ 0.05 s after the start; the video ends 0.45 s after the last word (+0.1 s) | first word within ~0.1 s, video ends within ~0.5 s of the last word |
| Filler removal | a sustained steady vowel ≥ 0.16 s (voiced, very low spectral change, low zero-crossing rate): standalone = deleted | um / uh / erm / hmm are the standard filler list |
| Stretched vowels | the same signature inside a word = a drawn-out vowel, shortened to ~0.09 s with a 12 ms crossfade | hold vowels <= ~0.12 s |
| Retakes | with word timings: a 2-word phrase repeated back-to-back keeps only the last attempt | keep the last clean take |
| Level matching | every speech island nudged ±3 dB toward the median, so parts recorded at different distances sit together | new (the GTA voice was 5 separate recordings) |
| Voice chain | highpass 80 · afftdn nr 12 · −2.5 dB @220 Hz · +3 dB @3.2 kHz · treble +1.5 · deesser · compressor 3:1. `meta.voice_chain: false` skips it | a typical speech chain: high-pass, denoise, de-mud, presence, de-ess, 3:1 compression |
| Edit list | `assets/voice_edit.json`: every kept segment and every removed span with its reason, plus stats (before/after duration, wpm, longest pause). `words_override.json` stays in the ORIGINAL voice's timeline and is re-mapped automatically | new |

Measured on the GTA 6 reel (Hinglish, 5 recorded parts): 40.3 s → 38.0 s, 10 pauses capped (0.35–0.57 s → 0.22 s, longest left 0.22 s), 1 stretched vowel shortened, level spread ±4 dB matched, pace 235 → 249 wpm, first word at 0.05 s.

## Honest limits
- Filler detection is acoustic (no speech recognition needed, so it works on Hinglish), but it only catches **sustained** sounds ("aaa", "ummm", "hmm"). A very short "uh" (< 0.16 s) or a filler that is a real word ("matlab", "basically", "so") is not detected: with word timings from whisper (English scripts) add the words to `FILLER_WORDS` in `clean_voice.py` or cut them in the script.
- Whenever the detector removes something it lists it in `assets/voice_edit.json` → `removed` with the time and reason: read the list at the checkpoint, and if a cut was wrong set `meta.voice_clean: false` (or re-record).
- It never rewrites words. A bad take is fixed by re-recording, not by the cleaner.
- Re-run after changing the voice file: delete `voice_clean.wav`, or set `meta.voice_reclean: true`.

## Recording advice that makes cleanup unnecessary (tell the creator when asking for the voice)
Quiet room, 10 cm from the mic, one sentence per breath, leave ~0.3 s between sentences (Hinglish timing needs it), if you slip say the line again from the start of the sentence, no "ahh" while thinking: stay silent, silence is cut for free, a filler sound is not.
