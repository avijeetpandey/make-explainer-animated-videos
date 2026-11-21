#!/usr/bin/env bash
# One-time setup for /make-explainer-animated-videos. Safe to re-run. Everything it installs is free; nothing needs a login.
set -uo pipefail
K="$(cd "$(dirname "$0")/.." && pwd)"; ok(){ echo "OK   $*"; }; no(){ echo "MISS $*"; }
node -v | grep -qE '^v(2[2-9]|[3-9][0-9])' && ok "node $(node -v)" || no "Node 22+ (brew install node)"
command -v ffmpeg >/dev/null && ok "ffmpeg" || no "ffmpeg (brew install ffmpeg)"
command -v yt-dlp >/dev/null && ok "yt-dlp (only needed for study mode)" || no "yt-dlp (brew install yt-dlp) - only for study mode"
if command -v whisper-cli >/dev/null; then ok "whisper-cli"; else no "whisper-cli (brew install whisper-cpp)"; fi
M="$HOME/.cache/hyperframes/whisper/models/ggml-small.en.bin"
if [ ! -f "$M" ]; then mkdir -p "$(dirname "$M")"; curl -fL -o "$M" https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin && ok "downloaded whisper small.en model" || no "whisper model (download ggml-small.en.bin to $M)"; else ok "whisper small.en model"; fi
mkdir -p "$HOME/.cache/explainer-skill"
[ -f "$HOME/.cache/explainer-skill/gsap.min.js" ] || curl -fsSL -o "$HOME/.cache/explainer-skill/gsap.min.js" https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js
[ -s "$HOME/.cache/explainer-skill/gsap.min.js" ] && ok "gsap (timeline clock only)" || no "gsap"
B=https://github.com/google/fonts/raw/main/ofl; F="$K/assets/fonts"; mkdir -p "$F"
[ -s "$F/HankenGrotesk.ttf" ] || curl -fsSL -o "$F/HankenGrotesk.ttf" "$B/hankengrotesk/HankenGrotesk%5Bwght%5D.ttf"
[ -s "$F/JetBrainsMono.ttf" ] || curl -fsSL -o "$F/JetBrainsMono.ttf" "$B/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf"
[ -s "$F/InstrumentSerif-Italic.ttf" ] || curl -fsSL -o "$F/InstrumentSerif-Italic.ttf" "$B/instrumentserif/InstrumentSerif-Italic.ttf"
[ -s "$F/InstrumentSerif-Regular.ttf" ] || curl -fsSL -o "$F/InstrumentSerif-Regular.ttf" "$B/instrumentserif/InstrumentSerif-Regular.ttf"
ls "$F"/*.ttf >/dev/null 2>&1 && ok "fonts (OFL: Hanken Grotesk, JetBrains Mono, Instrument Serif)"
python3 -c "import numpy" 2>/dev/null && ok "numpy (SFX + study metrics)" || no "numpy (python3 -m pip install numpy)"
echo "Render engine: npx --yes hyperframes@0.8.209 (downloads Chrome on first use, ~1-2 min)."
