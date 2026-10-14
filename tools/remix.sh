#!/usr/bin/env bash
# Re-mix the audio stems onto an already-rendered video (use after changing only audio).
# Same mix as the HyperFrames render: narration + music + sfx at unity, then master.sh.
set -euo pipefail
cd "$(dirname "$0")/.."
IN=${1:-out/render_raw.mp4}
ffmpeg -hide_banner -v error -y -i "$IN" -i assets/audio/narration.wav -i assets/audio/music.wav -i assets/audio/sfx.wav \
  -filter_complex "[1:a]aresample=48000,pan=stereo|c0=c0|c1=c0[v];[2:a]aresample=48000[m];[3:a]aresample=48000[s];[v][m][s]amix=inputs=3:normalize=0:duration=first[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a pcm_s16le -t "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")" out/render_remix.mkv
bash tools/master.sh out/render_remix.mkv
