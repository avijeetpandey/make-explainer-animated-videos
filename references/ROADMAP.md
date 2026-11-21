# Roadmap

## Done (see CHANGELOG.md)
Music bed with beat grid + premium genre/warmth scoring · SFX by role · voice-first mix solved from stems · -14 LUFS / TP · camera punches, transitions at idea changes, gap filler · film grain · silence/filler/breath trimming + level matching + voice chain · worlds + style log · frame-0 headline · covers A/B · SRT · posting-kit workflow + lint · facts gate · safe-zone gate · gated upload · island-anchored Hinglish timing.

## Next (ordered by impact)
1. **Word-accurate timing for Roman-script Hinglish.** Today island starts are reliable and words inside a fast island are +/-0.2-0.4 s. Ideas: a multilingual aligner (e.g. forced alignment with a Hindi acoustic model), or hand-corrected `words_override.json` tooling (a tiny editor that plays an island and lets you nudge words).
2. **Two masters** (Instagram follow card, YouTube subscribe card) and A/B hook variants.
3. **Logo chips** for spoken brands (simple-icons) and real UI captures for named products.
4. **Colour = meaning on key words** (negative / good / number) and phrase-chunk markers for caption breaks.
5. **Beat-snapped entrances** (not only camera punches) and an optional audio-reactive element.
6. **Loop-friendly ending** (the last visual returns to the hook hero).
7. **Voice gate before cleanup**: sample rate, clipping, noise floor, echo report with a re-record verdict.
8. **Short fillers and filler words**: the detector only catches sustained sounds ("aaa", "ummm"); with reliable word timings it could also remove "so", "basically", "matlab".
9. **Solid faces** for wireframes and a WebGL hero for machines that have a GPU.
