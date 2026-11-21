#!/usr/bin/env bash
# finalize.sh <video.mp4> <out.mp4> [master.wav]
#  with master.wav (the normal path): mux the mastered mix from mix_audio.py onto the silent-picture render (video re-encoded x264 crf 20 / max 10 Mbps because the grain layer makes the raw render huge; audio already -14 LUFS / TP <= -1.5).
#  without it: loudness-normalise whatever audio the video has to -14 LUFS (legacy path).
set -euo pipefail
in="$1"; out="$2"; master="${3:-}"
if [ -n "$master" ]; then
  ffmpeg -v error -y -i "$in" -i "$master" -map 0:v:0 -map 1:a:0 -c:v libx264 -preset medium -crf 20 -maxrate 10M -bufsize 20M -pix_fmt yuv420p -c:a aac -b:a 256k -ar 48000 -movflags +faststart -shortest "$out"   # grain is incompressible: cap the rate (~50 MB per 40 s)
else
  ffmpeg -v error -y -i "$in" -c:v copy -af "loudnorm=I=-14:TP=-1.5:LRA=11" -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$out"
fi
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,duration -of csv=p=0 "$out"
ffmpeg -nostats -i "$out" -af ebur128=peak=true -f null - 2>&1 | grep -A12 Summary | grep -E "^\s+I:|Peak:" | tr -s ' ' | tr '\n' ' '; echo
