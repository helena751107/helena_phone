#!/usr/bin/env python3
"""
CapCut-style Auto Captions — word-by-word animated subtitles

Generates ASS subtitle file with per-word/phrase timing and bounce animation.
CapCut's signature feature: each word pops (scale up + gold highlight) as spoken,
then settles back. Simulated via FFmpeg ASS \t transform tags.

Usage:
  python3 scripts/capcut_captions.py --text "안녕하세요 S21 Phone입니다" \
    --start 0.0 --duration 4.5 --out /tmp/caps.ass
  python3 scripts/capcut_captions.py --srt input.srt --style bounce --out subs.ass

Style presets:
  bounce  — CapCut classic: pop-up + gold flash + settle
  type    — typewriter: fade-in one by one
  glow    — soft glow pulse
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

W, H = 1080, 1920
FONT = os.environ.get(
    "CAPTION_FONT",
    "/usr/share/fonts/truetype/noto/NotoSansKR-Bold.ttf",
)

# ── style presets ──
STYLES = {
    "bounce": {
        "fontsize": 44,
        "color": "&H00F0C75E",       # gold bright
        "outline_color": "&H001A1508",  # near-black
        "back_color": "&H99000000",     # semi-transparent black
        "outline": 2.5,
        "shadow": 1.5,
        "scale_up": 130,    # % at peak
        "bounce_dur": 0.35,  # seconds to settle
    },
    "type": {
        "fontsize": 42,
        "color": "&H00F4EFE6",       # warm white
        "outline_color": "&H001A1508",
        "back_color": "&H99000000",
        "outline": 2.5,
        "shadow": 1,
        "scale_up": 105,
        "bounce_dur": 0.25,
    },
    "glow": {
        "fontsize": 44,
        "color": "&H003DB8A8",       # teal
        "outline_color": "&H001A1508",
        "back_color": "&H99000000",
        "outline": 3,
        "shadow": 2,
        "scale_up": 115,
        "bounce_dur": 0.4,
    },
}

# ── Korean word splitting (2-4 char groups) ──
def split_korean_words(text: str) -> list[str]:
    """Split Korean text into visual word groups (2-4 chars each)."""
    text = text.strip()
    if not text:
        return []
    # Split by spaces first
    chunks = text.split()
    result = []
    for chunk in chunks:
        # If chunk has mixed Korean/English, keep as-is if short
        has_korean = bool(re.search(r'[가-힣]', chunk))
        if not has_korean or len(chunk) <= 4:
            result.append(chunk)
        else:
            # Break long Korean chunks into 3-4 char groups
            i = 0
            while i < len(chunk):
                size = min(3 + (1 if len(chunk) - i > 6 else 0), len(chunk) - i)
                result.append(chunk[i:i+size])
                i += size
    return result


def estimate_word_duration(word: str, total_dur: float, all_words: list[str]) -> float:
    """Estimate how long each word should display based on char count."""
    total_chars = sum(len(w) for w in all_words)
    if total_chars == 0:
        return total_dur / max(len(all_words), 1)
    return total_dur * len(word) / total_chars


# ── ASS generator ──
def ass_timestamp(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def generate_ass(
    text: str,
    start_time: float,
    duration: float,
    style: str = "bounce",
    output: Path | None = None,
) -> str:
    """Generate CapCut-style animated ASS subtitle content."""
    cfg = STYLES.get(style, STYLES["bounce"])
    words = split_korean_words(text)
    if not words:
        return ""

    fs = cfg["fontsize"]
    color = cfg["color"]
    outline_color = cfg["outline_color"]
    back_color = cfg["back_color"]
    outline = cfg["outline"]
    shadow = cfg["shadow"]
    scale_up = cfg["scale_up"]
    bounce_dur = cfg["bounce_dur"]

    margin_v = max(80, int(H * 0.12))  # lower-third safe zone

    header = f"""[Script Info]
Title: CapCut Auto Captions
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Noto Sans KR,{fs},{color},&H000000FF,{outline_color},{back_color},-1,0,0,0,100,100,0,0,1,{outline},{shadow},2,60,60,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events = []
    t = start_time

    for i, word in enumerate(words):
        w_dur = estimate_word_duration(word, duration, words)
        # Slight overlap: next word starts 0.05s before current ends
        start = t
        end = start + w_dur + 0.05
        t = start + w_dur

        # ASS transform: scale up quickly then settle
        # \t(accel, t1, t2, ...) — accelerate from start to t1
        settle = min(bounce_dur, w_dur * 0.6)
        peak_scale = scale_up  # percent
        # animation: start at peak_scale%, ease to 100% over settle time
        anim_tag = (
            f"{{\\t(0,{int(settle*1000)},\\fscx{peak_scale}\\fscy{peak_scale})}}"
            f"{{\\fscx{peak_scale}\\fscy{peak_scale}}}"
        )

        word_escaped = word.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
        text_line = f"{{\\fscx{peak_scale}\\fscy{peak_scale}}}{word_escaped}"
        # After settle, back to 100%
        text_line += f"{{\\t(0,{int(settle*1000)},\\fscx100\\fscy100)}}"

        events.append(
            f"Dialogue: 0,{ass_timestamp(start)},{ass_timestamp(end)},"
            f"Cap,,0,0,0,,{text_line}"
        )

    result = header + "\n".join(events) + "\n"
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(result, encoding="utf-8")
    return result


# ── SRT to ASS converter ──
def srt_to_ass(srt_path: Path, style: str = "bounce", output: Path | None = None) -> str:
    """Convert SRT subtitle file to CapCut-style animated ASS."""
    import re as _re

    text = srt_path.read_text(encoding="utf-8")
    # Parse SRT blocks
    blocks = _re.split(r'\n\s*\n', text.strip())
    all_events = []

    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        # Skip index line
        time_line = lines[1] if len(lines) > 1 else lines[0]
        subtitle_text = ' '.join(lines[2:]) if len(lines) > 2 else ''

        # Parse SRT timestamp: 00:00:01,000 --> 00:00:04,000
        ts_match = _re.match(
            r'(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})',
            time_line
        )
        if not ts_match:
            continue
        h1, m1, s1, ms1, h2, m2, s2, ms2 = [int(x) for x in ts_match.groups()]
        start = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000
        end = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000
        dur = end - start

        if subtitle_text and dur > 0:
            ass_block = generate_ass(subtitle_text, start, dur, style)
            # Extract only the events (skip headers)
            event_lines = [l for l in ass_block.split('\n') if l.startswith('Dialogue:')]
            all_events.extend(event_lines)

    cfg = STYLES.get(style, STYLES["bounce"])
    fs = cfg["fontsize"]
    color = cfg["color"]
    outline_color = cfg["outline_color"]
    back_color = cfg["back_color"]
    outline = cfg["outline"]
    shadow = cfg["shadow"]
    margin_v = max(80, int(H * 0.12))

    header = f"""[Script Info]
Title: CapCut Auto Captions (from SRT)
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Noto Sans KR,{fs},{color},&H000000FF,{outline_color},{back_color},-1,0,0,0,100,100,0,0,1,{outline},{shadow},2,60,60,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    result = header + "\n".join(all_events) + "\n"
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(result, encoding="utf-8")
    return result


# ── CLi ──
def main():
    ap = argparse.ArgumentParser(description="CapCut-style Auto Captions")
    ap.add_argument("--text", help="Single text line for captions")
    ap.add_argument("--srt", help="SRT subtitle file to convert")
    ap.add_argument("--start", type=float, default=0.0, help="Start time (for --text)")
    ap.add_argument("--duration", type=float, default=3.0, help="Duration (for --text)")
    ap.add_argument("--style", default="bounce", choices=["bounce", "type", "glow"])
    ap.add_argument("--out", help="Output ASS file path")
    args = ap.parse_args()

    if not args.out:
        print("--out required", file=sys.stderr)
        sys.exit(2)

    if args.srt:
        srt_to_ass(Path(args.srt), style=args.style, output=Path(args.out))
        print(f"✅ SRT→ASS  style={args.style}  → {args.out}")
    elif args.text:
        generate_ass(args.text, args.start, args.duration, style=args.style, output=Path(args.out))
        print(f"✅ {args.style} captions  dur={args.duration:.2f}s  → {args.out}")
    else:
        print("--text or --srt required", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
