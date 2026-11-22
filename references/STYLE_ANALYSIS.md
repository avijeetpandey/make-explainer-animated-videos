# Style analysis: 17 reference reels (studied 21 Nov 2026)

> The 17 studied reels are third-party public videos. Their frames are **not** redistributed in this repository (they stay in the author's private working copy); everything below is measured numbers and design observations written for building an original look.

Method: downloaded 17 public reels (yt-dlp, 1080x1920, 37-159 s), extracted frames at 2 fps (about 3,400 frames), built 24-frame overview sheets per reel plus 5 fps strips of transitions and full-resolution crops, measured scene-change/caption beats and motion energy with numpy, loudness with ffmpeg ebur128, SFX events with a sub-bass/air-band detector, and looked at spectrograms. Every number below is measured unless it says "estimate". Copy the *format*, never a brand, characters, scripts or wording.

## 1. The corpus
| # | Topic | Length | Caption beats (median) | Palette | Signature visuals |
|---|---|---|---|---|---|
| r01 | DNS (what happens when you type instagram.com) | 63 s | 19 (2.9 s) | white | dot-sphere → ring → line → "DNS" particle text, ring/torus resolver objects, TCP/TLS handshake ladder, recap list |
| r02 | Bloom filter | 60 s | 19 (3.1 s) | white + red | username word-cloud, "BLOOM FILTER" particle text, 3D bit-array cells that light up, red FALSE POSITIVE, rule cards |
| r03 | Idempotency | 58 s | 13 (2.9 s) | white + red | phone UI mock, tap counter 0→5, "CHARGED TWICE" stamp, key-store table with highlighted row, particle key |
| r04 | Kafka | 85 s | 21 (3.7 s) | white | wireframe event lane + live counter 10,61,262, "KAFKA" particle text, partitions table, consumer-group cards |
| r05 | HTTPS | 86 s | 23 (4.0 s) | white + red | particle padlock, login card, hooded "eavesdropper", TLS tunnel, handshake ladder, 3 pillar cards |
| r06 | RAG | 107 s | 23 (4.9 s) | white | particle cloud → vector DB, document stacks counter, embedding bars, 3D vector scatter, with/without RAG cards |
| r07 | Access vs refresh token | 95 s | 30 (3.3 s) | blue + yellow | token cards, 15:00 timer ring, lifetime bars, attacker, side-by-side recap |
| r08 | Outbox pattern | 118 s | 30 (3.7 s) | blue/yellow/red/green | service boxes, "OUTBOX" particle text, table slabs, worker + broker lane |
| r09 | Partitioning / replication / sharding / clustering | 137 s | 36 (3.8 s) | one colour per concept | ambient glow tinted per concept, lettered recap list |
| r10 | NGINX | 105 s | 25 (4.2 s) | blue/yellow/violet/green | browser mock, racks, travelling packets, role glows, thread-vs-worker compare |
| r11 | How companies build AI | 159 s | 37 (3.9 s) | multi, tinted glow per step | big chips ("AI WRAPPER", "TAKING ACTION"), requests/day and cost counters |
| r12 | Instagram prefetching + CDN | 94 s | 25 (3.7 s) | white + blue + red | **editorial variant**: serif-italic key words, dotted-grid phone, dotted globe, dotted buffer; densest motion |
| r13 | Canary deployment | 86 s | 23 (3.4 s) | yellow | 85,00,000 laptop grid turning red, 95%/5% version racks, metric sparkline cards, rollback |
| r14 | GTA 6 pre-load / CDN | 85 s | 21 (3.5 s) | blue | server tower + lock, calendar, download bar, globe with nodes, encryption card, midnight clock, spike chart, follow card |
| r15 | UPI / NPCI | 123 s | 31 (4.0 s) | blue + red | petrol-pump UI, UPI-ID card, PIN pad, NPCI network graph, settlement table |
| r16 | API vs MCP | 110 s | 20 (6.2 s) | white + red | box diagrams, 3×3=9 red links vs 3+3=6, API/MCP compare cards |
| r17 | Promo for a live "make reels with Claude" session (different account) | 37 s | n/a | green neon on navy | **different format**: flat illustrated cartoon people, Devanagari captions, very high motion; not copied here |

r01–r16 are one template ("series" look). Their frames are identical in structure; only topic, accent colour and objects change.

## 2. Frame template (1080×1920, measured from full-resolution crops)
- **Background:** near-black (#050506–#0a0a0c; mean luma 6–26 of 255) with a very faint radial tint behind the stage; a few dust specks. Tinted per concept in r07–r11 (blue/yellow/violet/green at ~10% opacity).
- **Header (y≈56–75):** brand left (bold ~21 px caps, 0.24 em tracking), series tag right (mono ~18 px, grey, e.g. `SYSTEM DESIGN · 07`).
- **Progress rail (y≈121):** 972 px hairline, **one tick per scene**, white fill grows with time. It is the visible "how long is left" bar.
- **Kicker (y≈150, r11–r15 only):** tiny mono caps `02 · THE MYSTERY`, grey.
- **Caption (top y≈185, ≤3 lines, 52 px/70 px, Hanken-Grotesk-like geometric grotesque, medium):** one sentence per scene, grey (≈60%) with **key terms white, bold, underlined** (2–3 px bar that wipes in). Words fade in on the spoken word (≈0.2 s), the whole sentence fades out ≈0.2 s before the next. Editorial variant (r12): key words in **serif italic** (Instrument-Serif-like), one accent colour word.
- **Stage band (y≈440–1500):** the diagram. Everything is centred; nothing important below y≈1500 (the bottom ≈400 px is deliberately empty: Instagram's caption/buttons live there, matching published safe-zone guides: ~35% bottom on Reels).
- **Mono labels:** JetBrains-Mono-like, uppercase, tracked, 15–24 px for node names and sub-labels.
- **Endcard:** white speech bubble "Comment in this reel" (≈58 px bold, black on white, tail bottom-left) + one mono sub-line "Most-asked X interview questions, in your DMs." Some reels add a profile "Follow" card first.
- **Colour discipline:** monochrome; at most ONE accent per concept: blue = main/active, yellow = second, violet = third, green = success/cache, red = failure/attack/warning (red also tints the glow behind the stage).

## 3. Motion language (what makes it feel premium)
Measured on 5 fps strips: a "beat" (one sentence) lasts 2.9–6.2 s, median ≈3.7 s, and has the same choreography every time.
1. **Hero particles.** One persistent system of ≈4–6 k dots (1.5–3 px, depth-cued brightness, slow twinkle) that **morphs** between shapes: sphere with latitude rings → ring seen edge-on → vertical line → scatter → text ("DNS", "KAFKA", "BLOOM FILTER", "OUTBOX") → key/padlock/phone/globe. The transition is a ≈1 s ease-in-out with an outward scatter (sin(π·e) burst) in the middle. No hard cuts.
2. **Wireframe 3D objects** (thin 1.5 px edges, 3/4 view, slightly from above, back edges dimmer, ±3° idle sway): browser window, server rack (stacked flat boxes), database cylinder, cube, globe, phone. They **draw on** edge by edge in ≈0.7 s with a stagger; the *active* one gets a soft coloured glow.
3. **Persistence:** diagram parts stay on screen across sentences; each beat adds/highlights one thing (a new node, a link, a packet). Removed parts fade over ≈0.3 s.
4. **Packets:** a glowing dot travels along a dashed link in ≈0.8–1 s with a small label chip riding above it (`GET /feed`, `→ ask .com TLD`). Links draw on with a moving dash.
5. **Chips & cards** pop in: ≈0.4 s ease-out, rise 16 px, scale .94→1. Terminal/JSON cards type their text. Cards highlight by inverting to white (recap list, compare cards).
6. **Counters** roll with ease-out over 1.6–2.4 s, **Indian digit grouping** (10,61,262; 85,00,000). Numbers are the hook of the data beat.
7. **Stamp:** red rotated border text slams in (scale 1.7→1, overshoot) for FAILURE/NOT SENT/CHARGED TWICE.
8. **Camera:** barely perceptible push-in (~2% per scene) so the frame is never dead. Stage motion energy: median "still" share of time 40% (range 2–72%): holds are intentional, followed by a burst on each new sentence.
9. **Recap:** vertical rail with items; the active item inverts to a white pill, advancing in sync with the last sentences.
10. **Hook (first 1.5 s):** a particle/3D hero already moving + the sentence "If an interviewer asks: …" with the topic word underlined; no logo intro, no title card.

## 4. Sound
- **Voice only. No music bed** (spectrograms show no tonal bed; all 16 series reels sit at **−14.1 LUFS** integrated, LRA 2–3 LU, peak ≈ −0.8 dBFS: loudness-normalised and heavily compressed).
- Voice is warm and close (energy 100–600 Hz, steep roll-off above ≈3 kHz).
- Sparse sub-bass **thumps**: 1.6–4.4 detected per 10 s (≈ one per beat, the "new thing arrived" cue) plus tiny clicks. No whoosh wall. Silence between is real.
- I could not verify whether the narration is a human or synthetic voice; whisper.cpp could not transcribe it cleanly (garbled output), so timing here comes from the on-screen captions.

## 5. What this means for production
- The look is **entirely code-renderable**: text, dots, hairlines, rounded cards, glows. No footage, no AI video. Pixel-identical layout across 16 reels + crisp 1080 text = templated code, not an editor timeline. (r17's own caption describes the creator's process as: topic + 3-second hook, a script where every line has one picture, AI voice + captions, and scenes built from scratch with Claude. That is exactly the loop this skill automates.)
- Pace: 13–37 beats and 58–160 s per reel. This is much longer than the talking-head Shorts rules (25–35 s); it is a different format (educational explainer). Default here: **45–90 s, 12–25 scenes**, longer only if the topic needs it.
- Retention devices: the progress rail (one tick per scene), one concrete everyday example per topic (Instagram, Swiggy, Google Pay, Amazon, GTA), a "twist"/failure beat (red) before the fix, a recap, then a single comment CTA.

## 6. Not determined
Exact SFX files, exact font files (Hanken Grotesk / JetBrains Mono / Instrument Serif are the closest OFL matches, chosen by eye), the author's renderer, and the true voice source.

---

# Second batch: 17 more reels, the "polished studio" look (studied 22 Nov 2026)

> Same rule as above: third-party public videos, frames not redistributed (they live in the author's private working copy). Below are measured observations and the design vocabulary we rebuilt **from scratch**; no brand, character, script or wording is copied.

**Why this batch matters.** The first 17 reels are one monochrome template (near-black, white hairlines, one accent). Rendering that look faithfully gave videos that read as "the same type, junior": every video was black-and-white particles and wireframes. This batch is the opposite end: motion designers who light, colour and compose every scene differently. Method: 17 reels downloaded (yt-dlp), 2 fps frames, 24-frame overview sheets, full-resolution detail montages and 5 fps motion strips on the transitions that carry the polish.

## What they do that the first template never did
| # | Device | How it is built | Where it lives in the skill |
|---|---|---|---|
| 1 | **Colour is lighting, not decoration.** Each scene gets its own light: deep-navy aurora (blue / violet / magenta), teal-and-blue light through reeded glass, navy-to-orange duotone with a dot grid, a cream editorial page. | big blurred radial lights drifting on slow Lissajous paths, additive blend, vignette, grain | `studio.js` backdrops `aurora` `fluted` `duotone` `studio` `cream` `deep`, crossfaded between scenes |
| 2 | **Semantic colour zones.** Problem scenes go red, mechanism blue, the fix green, outro violet; the background itself changes, and a success/failure beat **flashes the whole frame** green or red for ~0.5 s. | scene tag -> tone | scene `zone`, `flash`, `flash_at`; world `zones` |
| 3 | **Real depth.** Glossy objects with reflections: spheres, knots, rounded slabs, stacked server units, database discs, shield + check, ribbons that draw on. Lit by coloured softboxes, so each object carries rim light in the scene's colours. | WebGL (three.js) with a procedural studio environment | stage type `gl` (13 kinds) |
| 4 | **Glass UI.** Cards are translucent gradient panels with a bright top edge and a coloured outer glow keyed to the concept; slight 3D tilt; window chrome (traffic-light dots + mono title) for terminals/chats; status rows with check / cross that glow green / red. | CSS gradients, inset highlights, `perspective()` tilt | `card` (`chrome`, `tiltx`), `rows`, world `style: glass` |
| 5 | **Type system with contrast.** Giant **outline** numerals, **chrome-gradient condensed** titles (Anton), serif-italic accents, lime highlighter pills for kickers, mono micro-labels. Never the same face for everything. | text-stroke, background-clip text gradient, pill chips | `big` `style: outline | chrome | grad | condensed`, `pill`, caption styles `glow` / `lime` |
| 6 | **Scene-to-scene continuity.** Backgrounds crossfade while the old content blurs out and the new content arrives with a *different* entrance (slide, scale, blur-focus, flip, drop). Light and dark scenes alternate. | per-element entrance variants | `in: rise | scale | blur | left | right | flip | drop`, scene `bg` |
| 7 | **State shown on the object.** A lit cube is "in use", a dark glass cube is "free"; rows dim, light up, fail; counters roll. The picture explains the mechanism without words. | per-item state read from keyframes, eased | `gl kind: cubes` `lit` / `tones`, `rows` `st` |
| 8 | **Karaoke captions in a high-contrast style**, key words coloured / glowing / lime-highlighted rather than just underlined. | | caption styles per world |

## Measured / observed numbers
Scene length 2.5-4.5 s; a new idea or entrance every 1.5-2.5 s; 1-2 large objects per scene, never a diagram of ten thin lines; text and 3D share one colour story per scene; background change at every scene cut (crossfade ~0.5 s); motion blur / refocus on 1 of 4 cuts.

## Honest limits
This is a **look reconstruction**, not a clone: exact fonts, assets and some of the 3D scenes in the originals were created in other tools. Ours is open source end to end: three.js (MIT) for 3D, Canvas 2D for lights, HTML/CSS for UI, HyperFrames to render. Verified: WebGL renders on the GPU path inside HyperFrames (hardware ANGLE/Metal on the author's Mac) and is deterministic per seek.

> **Correction (22 Nov 2026, after owner review).** The first reconstruction of this batch (v0.7) copied the *devices* (colour, depth, glass, type) and stacked them, and came out loud. What actually makes these reels premium is the discipline around the devices: one accent, one composition grid, every object explaining something, calm motion. See `DESIGN_PRINCIPLES.md`; the default look is now `ink_*`, the devices above are used sparingly.
