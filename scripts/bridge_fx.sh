#!/usr/bin/env bash
# bridge_fx.sh — Grok bridge still → motion + infographic FX (FFmpeg only)
# Usage: bash scripts/bridge_fx.sh <in.jpg|png> <out.mp4> [open|close] [sec]
set -euo pipefail
IN="${1:?input image}"
OUT="${2:?output mp4}"
MODE="${3:-open}"   # open | close
SEC="${4:-5.5}"
W=1080; H=1920
FRAMES=$(python3 -c "print(int(float('$SEC')*30))")

# open: push-in 1.0→1.10 · close: pull-out 1.10→1.0
if [[ "$MODE" == "close" ]]; then
  ZEXPR="1.10-0.10*(on/${FRAMES})"
  FADE_OUT_ST=$(python3 -c "print(max(0.0, float('$SEC')-1.2))")
  FADE="fade=t=in:st=0:d=0.6,fade=t=out:st=${FADE_OUT_ST}:d=1.2"
else
  ZEXPR="min(1.0+0.10*(on/${FRAMES}),1.10)"
  FADE="fade=t=in:st=0:d=0.8,fade=t=out:st=$(python3 -c "print(max(0.0,float('$SEC')-0.7))"):d=0.7"
fi

# Gold edge frame + soft vignette + zoom (infographic polish)
# drawbox = thin gold border · eq slight gold warmth
VF="scale=$((W*2)):$((H*2)):force_original_aspect_ratio=decrease,\
pad=$((W*2)):$((H*2)):(ow-iw)/2:(oh-ih)/2,\
zoompan=z='${ZEXPR}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=${FRAMES}:s=${W}x${H}:fps=30,\
eq=saturation=1.05:gamma=1.02,\
drawbox=x=24:y=24:w=iw-48:h=ih-48:color=#d4a84b@0.55:t=3,\
drawbox=x=36:y=36:w=iw-72:h=ih-72:color=#d4a84b@0.25:t=1,\
vignette=PI/4,\
${FADE},\
format=yuv420p"

ffmpeg -y -loop 1 -i "$IN" -t "$SEC" \
  -vf "$VF" \
  -c:v libx264 -profile:v high -level 4.0 -pix_fmt yuv420p \
  -preset ultrafast -crf 22 -an -movflags +faststart \
  "$OUT"
echo "OK $OUT ($MODE ${SEC}s)"
