# Third-party notices
- **HyperFrames** (HeyGen) renders the HTML to video: Apache-2.0. https://github.com/heygen-com/hyperframes (installed on demand with `npx`, not vendored).
- **whisper.cpp** (ggml-org): MIT. Used for word timing; models are downloaded by `scripts/setup.sh`.
- **ffmpeg**: LGPL/GPL depending on your build. Not bundled.
- **GSAP** (GreenSock): used only as the paused timeline clock. Free under GreenSock's standard licence (https://gsap.com/standard-license/), which is not an OSI open-source licence. It is downloaded by `setup.sh`, not vendored. To avoid it, swap the clock for Anime.js (MIT) or the Web Animations API (see docs/TWEAKING.md).
- **Fonts** (SIL Open Font License 1.1, files in `assets/fonts/`): Hanken Grotesk, JetBrains Mono, Instrument Serif. Licence texts: https://openfontlicense.org/ and each font's upstream repository (google/fonts `ofl/hankengrotesk`, `ofl/jetbrainsmono`, `ofl/instrumentserif`).
- **Music and SFX are not included.** You supply tracks you may use (see `library/README.md`).
