#!/usr/bin/env bash
# upload_drive.sh <project_dir> --approved-video --approved-cover [--dry-run]
# Enforced approval gate: the creator must have approved BOTH the video and the cover(s). Nothing is ever uploaded without both flags.
# Remote: <drive_dest>/<reel>/ (config.local.json "drive_dest" or EXPLAINER_DRIVE_DEST, default gdrive:explainer_videos; always a NEW subfolder, never the base itself); a re-edit <reel>_vN goes to <drive_dest>/<reel>/vN/ . Sizes are verified with rclone lsl.
set -euo pipefail
P="$(cd "$1" && pwd)"; shift; V=0; C=0; DRY=0
for a in "$@"; do case "$a" in --approved-video) V=1;; --approved-cover) C=1;; --dry-run) DRY=1;; esac; done
NAME="$(basename "$P")"; BASE="$NAME"; VER=""
if [[ "$NAME" =~ ^(.+)_v([0-9]+)$ ]]; then BASE="${BASH_REMATCH[1]}"; VER="v${BASH_REMATCH[2]}"; fi
BASEDEST="$(python3 -I -c "import sys;sys.path.insert(0,'$(dirname "${BASH_SOURCE[0]}")');import config;print(config.get('drive_dest','gdrive:explainer_videos'))")"
DEST="$BASEDEST/$BASE${VER:+/$VER}"
FILES=("renders/${NAME}_final.mp4:${NAME}.mp4" "covers/cover_a.jpg:${NAME}_thumbnail.jpg" "covers/cover_b.jpg:${NAME}_thumbnail_b.jpg" "renders/${NAME}.srt:${NAME}.srt" "posting_kit.md:${NAME}_posting_kit.md")
echo "destination: $DEST"; MISS=0
for f in "${FILES[@]}"; do src="${f%%:*}"; if [ -f "$P/$src" ]; then echo "  ok   $src ($(du -h "$P/$src" | cut -f1))"; else echo "  MISSING $src"; MISS=1; fi; done
if [ $DRY -eq 1 ]; then echo "DRY RUN: nothing uploaded. Real run needs --approved-video --approved-cover."; exit $MISS; fi
if [ $V -ne 1 ] || [ $C -ne 1 ]; then echo "REFUSED: upload only after the creator approves BOTH the video and the cover (pass --approved-video --approved-cover)."; exit 3; fi
[ $MISS -eq 0 ] || { echo "REFUSED: files missing"; exit 4; }
command -v rclone >/dev/null || { echo "rclone not installed"; exit 5; }
rclone mkdir "$DEST"
for f in "${FILES[@]}"; do rclone copyto "$P/${f%%:*}" "$DEST/${f##*:}" -P; done
rclone lsl "$DEST"
echo "verify: the sizes above must match the local files (ls -l). If auth fails: rclone config reconnect gdrive:"
