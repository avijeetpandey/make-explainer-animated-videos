# Design principles: what "premium" means here (learned the hard way, 22 Nov 2026)

History: v0.7 shipped a loud multicolour 3D look (aurora blobs, pastel glossy toys, lime pills, colour flashes, chrome type, decorative objects). The owner's verdict: *"too flashy, not premium, text and images overlapping, uneven gaps, uglier than the older one."* The studied reels are premium because of **restraint and composition**, not because of effects. v0.8 rebuilt the default look on the rules below; the loud worlds remain only as an opt-in (`tier: expressive`).

## The rules
1. **One accent colour per video.** Near-black ink background, one accent hue (blue / violet / teal / amber), neutral glass for everything else. Semantic red / green appear only as *small state signals* (a dot, a stamp, a lit cube, a ✓ / ✗ row), never as full-screen washes or flashes. Zone tinting of the backdrop is gentle (38% mix), never a hue jump.
2. **Every visual must explain something.** No decorative objects (a floating torus, gem or orb that the sentence never mentions is "junior"). 3D is for *mechanisms*: a cube grid for pools / memory / slots (lit = in use, dark = free), a database stack, a server rack, a ribbon for a signal. Text scenes stay text.
3. **One composition system, not free placement.** Caption owns y 180-340; stage band y 560-1400; stage centre of mass y 700-1000; the bottom 400 px stay empty. Vertical stack inside a scene: object -> its label (automatic, directly below) -> one supporting element (chip / counter / card), gaps 40-160 px. Headline text 170-250 px, chips 29 px, counters 156 px: legible at arm's length.
4. **Quiet type.** One sans (Hanken Grotesk 800, tight tracking) + serif-italic accent word in the accent colour + mono micro-labels. No chrome gradients, no outline numerals, no lime highlighter pills in the default look.
5. **Captions are karaoke, not typewriter.** The whole sentence is laid out from the first frame; unspoken words sit at 30% opacity and brighten on their word; `text-wrap: balance`. (Hiding unspoken words made lines look off-centre and "unformatted".)
6. **Calm motion.** One entrance (fade + 16 px rise + 7 px focus pull), camera punches at half strength, no opening snap, no shock rings, no flashes, transitions limited to blur-in / push. Motion budget goes to the *one thing that changes* in the scene.
7. **Consistency beats variety inside a video; variety lives between videos** (accent hue, world, music), never between scenes.

## The gate that enforces it: `scripts/layout_check.py`
Loads the built page in headless Chrome (`?layout=1`), samples every scene twice (entrances settled, before exit) and FAILs on: overlaps between any two visible things (text, cards, chips, 3D objects, labels, caption, frame-0 headline), stage content under y 470, content outside x 60-1020 or below y 1500; WARNs on tight (< 28 px) or loose (> 340 px) stacks and on content centred outside y 640-1040. Run it before every render; fix the storyboard until it prints PASS. 3D objects are boxed analytically (`glBox` in engine.js): when you add a kind, calibrate its box against a snapshot, or the gate will miss collisions (the cube-grid label overlap was invisible to the gate until its box was enlarged).

## Review checklist before showing a draft
Open the snapshot contact sheets **at full size** and look for: anything touching anything; a gap that is 3x another; text that is not centred under its object; a scene with nothing explaining anything; more than one accent hue; a word-by-word caption that shifts position as it reveals.
