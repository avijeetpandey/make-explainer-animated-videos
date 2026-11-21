#!/usr/bin/env bash
# study_reference.sh <out_dir> <instagram/youtube url> [more urls...]
# Downloads reels (yt-dlp, public posts need no login), then per reel: 2 fps frames, a 6x4 overview sheet (24 evenly spaced frames),
# beat/motion metrics (measure_beats.py: caption beats, median beat length, stage motion energy, still fraction, luma) and loudness.
# Then LOOK at <out>/sheets/*.jpg and cut 5 fps strips of any transition you care about:
#   ffmpeg -ss T -t 2.4 -i rNN.mp4 -vf "fps=5,scale=200:-2,tile=12x2:padding=2" -frames:v 1 strip.jpg
set -euo pipefail
OUT="$1"; shift; mkdir -p "$OUT/sheets"; cd "$OUT"; i=$(ls r??.mp4 2>/dev/null | wc -l)
for u in "$@"; do i=$((i+1)); n=$(printf "r%02d" $i); yt-dlp -q --no-progress --write-info-json -o "$n.%(ext)s" "$u"; sleep 2; done
for f in r??.mp4; do n=${f%.mp4}; [ -f sheets/${n}_overview.jpg ] && continue; mkdir -p $n/frames
  ffmpeg -v error -y -i $f -vf "fps=2,scale=360:-2" -q:v 5 $n/frames/f_%04d.jpg
  N=$(ls $n/frames | wc -l); K=$(( (N+23)/24 ))
  ffmpeg -v error -y -framerate 2 -i $n/frames/f_%04d.jpg -vf "select='not(mod(n\,$K))',scale=216:-2,tile=6x4:padding=3:color=black" -frames:v 1 -q:v 4 sheets/${n}_overview.jpg
  echo -n "$n loudness: "; ffmpeg -nostats -i $f -af ebur128 -f null - 2>&1 | grep -A12 Summary | grep -E "^\s+I:" | tr -s ' '; done
python3 -I "$(dirname "$0")/measure_beats.py" $(ls r??.mp4 | sed 's/.mp4//')
