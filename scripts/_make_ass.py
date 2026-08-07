#!/usr/bin/env python3
r"""ASS karaoke subtitle generator V8 — shot_bible VO → .ass with \k word-level tags

Word timing: character-proportional heuristic (chars_in_word / total_chars * mp3_dur).
This avoids requiring a forced aligner (MFA) or Whisper ASR on the S21.

Output is rendered via FFmpeg `ass` filter onto the final video.
"""
from __future__ import annotations

import json, os, subprocess, sys
from pathlib import Path


def format_ass_time(seconds: float) -> str:
    """Convert float seconds to ASS timestamp: H:MM:SS.cc (centiseconds)"""
    cs = int(seconds * 100)
    h = cs // 360000
    m = (cs % 360000) // 6000
    s = (cs % 6000) // 100
    c = cs % 100
    return f"{h}:{m:02d}:{s:02d}.{c:02d}"


def split_korean_words(text: str) -> list[str]:
    """Split Korean text into words. Korean uses spaces as word boundaries."""
    # Split on spaces, preserve punctuation with preceding word
    words = text.split()
    # Merge very short fragments
    merged = []
    for w in words:
        if merged and len(w) <= 2 and len(merged[-1]) <= 3:
            merged[-1] += " " + w
        else:
            merged.append(w)
    return merged


def main() -> int:
    outdir = Path(os.environ.get("OUTDIR", "/root/work/out/pd_intro"))
    ep = os.environ.get("EP", "pd_intro")

    bible_path = outdir / "shot_bible.json"
    if not bible_path.exists():
        print("  ⚠️ no shot_bible.json — ASS skip")
        return 0

    bible = json.loads(bible_path.read_text(encoding="utf-8"))
    beats = bible.get("beats") or []
    bridges = bible.get("bridges") or []

    # ── Calculate bridge_open offset ──
    b_open_dur = 0.0
    for br in bridges:
        if br.get("before") == beats[0]["id"] if beats else False or \
           (br.get("id") or "").startswith("b_open") or "open" in (br.get("id") or ""):
            b_open_dur = 5.5
            break
    b_open_file = outdir / "bridge" / "b_open.mp4"
    if b_open_file.exists():
        try:
            probe = float(subprocess.check_output([
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=nw=1:nk=1", str(b_open_file),
            ], text=True).strip() or "0")
            b_open_dur = min(probe, 5.5)
        except Exception:
            pass
    else:
        b_open_dur = 0.0

    # ── Generate ASS dialogue lines with karaoke \k tags ──
    dialogues = []
    cursor = b_open_dur

    # ASS header
    ass_lines = [
        "[Script Info]",
        f"Title: {ep}",
        "ScriptType: v4.00+",
        "PlayResX: 1080",
        "PlayResY: 1920",
        "WrapStyle: 2",  # smart wrapping at bottom
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        # Primary=&H00FFFFFF (white active), Secondary=&H00666666 (dim gray inactive)
        # Outline=&H00000000 (black), BackColour=&H99000000 (semi-transparent black bg)
        "Style: Karaoke,Noto Sans CJK KR,34,&H00FFFFFF,&H00666666,&H00000000,&H99000000,"
        "-1,0,0,0,100,100,0,0,1,2.5,0,2,80,80,140,1",
        # Title style for captions (small, top-ish)
        "Style: Title,Noto Serif CJK KR,28,&H00D4A84B,&H00000000,&H001A1508,&H99000000,"
        "-1,0,0,0,100,100,0,0,1,2,0,2,100,100,40,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    for beat in beats:
        bid = beat["id"]
        vo_text = beat.get("vo") or beat.get("caption") or bid
        caption = beat.get("caption") or ""
        pause = float(beat.get("pause", 0))
        mp3 = outdir / f"{bid}.mp3"

        dur = 0.0
        if mp3.exists():
            try:
                dur = float(subprocess.check_output([
                    "ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=nw=1:nk=1", str(mp3),
                ], text=True).strip() or "0")
            except Exception:
                dur = 3.0
        else:
            dur = 3.0

        # ── Word-level karaoke timing ──
        words = split_korean_words(vo_text)
        total_chars = sum(len(w) for w in words)
        if total_chars <= 0:
            total_chars = 1
        char_dur = dur / total_chars  # seconds per character

        # Build \k sequence
        karaoke_parts = []
        for w in words:
            w_dur_cs = max(1, int(len(w) * char_dur * 100))  # centiseconds, min 1
            karaoke_parts.append(f"{{\\k{w_dur_cs}}}{w}")

        karaoke_text = " ".join(karaoke_parts)

        start_ass = format_ass_time(cursor)
        end_ass = format_ass_time(cursor + dur)
        dialogues.append(f"Dialogue: 0,{start_ass},{end_ass},Karaoke,,0,0,0,,{karaoke_text}")

        # ── Caption line (static title at top) ──
        if caption:
            dialogues.append(
                f"Dialogue: 1,{start_ass},{end_ass},Title,,0,0,0,,{caption}"
            )

        cursor = cursor + dur + pause

    ass_lines.extend(dialogues)
    ass_lines.append("")

    ass_path = outdir / f"{ep}.ass"
    ass_path.write_text("\n".join(ass_lines), encoding="utf-8")

    total_dur = cursor
    print(f"  📝 ASS karaoke: {len(beats)} beats · {total_dur:.1f}s · {ass_path}")
    print(f"  ⏱️  b_open offset: {b_open_dur:.1f}s")

    return 0


if __name__ == "__main__":
    sys.exit(main())
