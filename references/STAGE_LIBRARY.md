# scenes.json reference

```json
{"meta": {"series": "SYSTEM DESIGN · 01", "accent": "white", "seed": 7, "particles": 4200, "drift": 0.02, "kickers": true},
 "scenes": [ { "text": "...", "kicker": "01 · THE QUESTION", "hero": {...} | null, "stage": [ ... ], "keep": ["id", ...] } ]}
```
`meta.handle` is the header text on the left (your own handle; default from `config.local.json`, else the placeholder `@yourhandle`). `meta.series` is the right-hand tag. `meta.language`: `"hinglish"` = pause-based timing for Hinglish/any-accent voices (no speech recognition; `meta.silence_db` tunes pause detection); omit for English. `accent` = default glow tone. `drift` = camera push per scene (0 = off). `kickers:false` hides the small `01 · THE …` label.

## Meta fields added 21 Nov 2026
`world` (mono_pulse · blueprint · amber_signal · terminal_green, default auto-rotation) · `headline` `{lines:[l1,l2], strike?, t1?}` · `cover` `{a:{t,lines,accent,kicker}, b:{...}}` · `illustrative_label` · `hinglish_asr` (false = pause-based only). Element fields: `src` (where a counter/bars number comes from) · `illustrative: true` (a number that is a concept, not data). The `note` element is created automatically.

## Scene
| field | meaning |
|---|---|
| `text` | The spoken sentence, **exactly as in the voice-over** (the builder aligns it to the transcript, ≥80% of words must match). `*key term*` = bold + underline, `_serif phrase_` = serif italic (editorial look), `^blue^` = accent colour. Punctuation after a marker stays attached. 8–18 words, 2.5–6 s. |
| `kicker` | optional section label, `NN · UPPERCASE` |
| `hero` | particle hero for this scene, or `null` to let the particles dissolve (use when the stage has its own objects) |
| `stage` | list of elements to show this scene (see below) |
| `keep` | ids from the previous scene that stay unchanged without being re-listed |
| `shock` | `true` = impact ring + hit sound at the start of this scene (use on the 3–4 reveal scenes) |

**Persistence rule:** an element with an `id` that was on screen in the previous scene *stays* (its window extends) and its frame props (`x,y,tone,active,alpha,lines,…`) glide to the new values over 0.7 s. Listing it again with only `{"id": "..", "active": 1}` is the normal way to highlight. An element not listed (and not in `keep`) fades out when the scene ends. New elements need `type`.
**Timing:** `at` = seconds after scene start, **or a word of the sentence** (`"at": "crashes"`) to land exactly on that spoken word. Default: staggered 0.14 s apart from +0.15 s. Static props (label, text, items, kind …) are taken from the first appearance; to change them make a new id.

## Hero (particle system, ≈4 k dots, morphs between scenes automatically)
`{"shape": "sphere|globe|torus|ring|line|cloud|grid|cylinder|cube|phone|text|path", "r": 240, "y": 0, "spin": 0.35, "tilt": 0.18, "alpha": 1, "size": 1, "tone": "white|red|blue|yellow|green|violet", ...}`
- `text`: `"value": "KAFKA"` (use `\n` for two lines), `"size": 200` (font px for sampling), `r` = half the width in px (≈ 260–420 for words).
- `path`: `"d": "M…"` an SVG path in a 100×100 box (Lucide/Tabler icons are MIT) for padlock, key, cloud etc.
- `y` offsets the centre from 900 px (use −250…−350 when the hero sits above a diagram). `alpha` < 0.6 for a hero behind objects.
- Spin 0.2–0.9 rad/s. The ring/line shapes only read as such while spinning edge-on.

## Stage elements (canvas = 1080×1920; x,y are the element CENTRE; stage band y 480–1450, never below 1500)
| type | props |
|---|---|
| `obj` | 3D wireframe + label. `kind`: `box`·`cube`·`rack`(`units`)·`db`·`browser`·`phone`·`globe`; `w3,h3,d3` size (≈110–220), `label`, `sub`, `tone`, `active` 0–1 (glow), `ry`,`rx` view angles (−0.5 / 0.42), `ly` label offset, `dots` (LED dots on rack) |
| `link` | `a`,`b` = element ids or `[x,y]`; `arrow`, `dash:false`, `gap` (px trimmed at each end, 70), `tone`, `alpha` |
| `packet` | glowing dot travelling `a`→`b` over `dur` s, optional `label` chip riding above, `tone` |
| `chip` | `text`, `tone` white·dark·ghost·red·blue·yellow·green·violet |
| `card` | `title`, `lines`[], `w`, `tone` (coloured border), `type_cps` (typewriter speed), `on:true` (inverts white), `dash:true`. Line markup: `{r:red} {g:grey} {bl:blue} {gr:green} {y:yellow}` and `*bold*` |
| `big` | `text` (`\n`, `*serif italic*`), `sub` (mono line) |
| `counter` | `from`,`to`,`fmt` indian·plain·k·pct·default, `prefix`,`suffix`,`label`,`dur`,`tone` |
| `list` | `items`[], `active` index (−1 none), `w`; items reveal one by one, active inverts to a white pill. The recap. |
| `compare` | `cards`:[{title,lines,tone},…], `active` 0/1 (inverts), `w` |
| `stamp` | `text`, `tone` red·green·white, `rot` |
| `search` | `text` (typed), `ph`, `cps`, `w` |
| `bars` | `values`:[0–1,…], `active` |
| `cells` | grid of mini 3D boxes (bit array / partitions): `n`,`cols`,`cw`, frame props `lit`:[indices], `vals`:[…], `tones`:[…] |
| `cta` | `text` ("Comment in\nthis reel"), `sub` |

Palette meaning: white = default, **blue = active/primary**, yellow = second concept, violet = third, green = success/cache/healthy, red = failure/attack/danger.

## Layout cheat-sheet
Caption occupies y 185–400. Hero centre ≈ 800–900. Typical stage: top node (540, 590) → middle (540, 890) → row of 3 at y 1230 (x 220/540/860) → note card (540, 1330) → status chip (540, 1420). Two-column compare: x 300 / 780. Bottom 400 px stay empty.

## Recipes (scene by scene)
1. **Hook:** `sphere`/`text` hero + a chip (`INTERVIEW QUESTION`) or a `search` bar; sentence = the question with the topic word `*underlined*`.
2. **Concrete example:** a familiar product (Instagram, Swiggy, Google Pay) as `obj` browser/phone + a `counter` of scale (`fmt: "indian"`).
3. **Name the concept:** hero `text` morph with the concept's name while the sentence says it.
4. **Mechanism, one step per sentence:** persistent `obj`s + `link`s; each sentence adds one `packet`/`chip`; highlight the active `obj` (`active: 1`).
5. **Twist/failure:** active object `tone: red`, `stamp` on the spoken word, red chip.
6. **Fix + result:** green `active`, `counter` going down/up, `compare` of before/after.
7. **Recap:** `list` with `active` stepping 0→n over the last 3–4 sentences.
8. **CTA:** `cta` bubble + hero at alpha .5.

## Limits (be honest in the checkpoint message)
Wireframes are edges only (no solid faces); text in 3D scenes is HTML (always crisp); one particle hero at a time; no video/footage; max ≈25 simultaneous elements per scene (canvas redraws every frame; render ≈2× real time on a laptop).
