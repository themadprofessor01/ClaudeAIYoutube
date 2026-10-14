#!/usr/bin/env bash
# Loudness-master the rendered video for YouTube (-14 LUFS integrated, -1 dBTP), video stream copied untouched.
# usage: bash tools/master.sh [in=out/render_raw.mp4] [out=out/how-supermarkets-trick-your-brain.mp4]
set -euo pipefail
cd "$(dirname "$0")/.."
IN=${1:-out/render_raw.mp4}
OUT=${2:-out/how-supermarkets-trick-your-brain.mp4}
J=$(ffmpeg -hide_banner -i "$IN" -af loudnorm=I=-14:TP=-1:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
get() { echo "$J" | python3 -c "import json,sys;print(json.load(sys.stdin)['$1'])"; }
ffmpeg -hide_banner -y -i "$IN" -c:v copy \
  -af "loudnorm=I=-14:TP=-1:LRA=11:measured_I=$(get input_i):measured_TP=$(get input_tp):measured_LRA=$(get input_lra):measured_thresh=$(get input_thresh):offset=$(get target_offset):linear=true,aresample=48000" \
  -c:a aac -b:a 192k -movflags +faststart "$OUT"
# re-encode video at CRF 20 so the deliverable stays under GitHub's 100 MB file limit (~56 MB)
ffmpeg -hide_banner -v error -y -i "$OUT" -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -c:a copy -movflags +faststart "$OUT.tmp.mp4" && mv "$OUT.tmp.mp4" "$OUT"
ffmpeg -hide_banner -i "$OUT" -af ebur128=peak=true -f null - 2>&1 | grep -A8 Summary | grep -E "I:|Peak:"
