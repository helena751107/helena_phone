#!/usr/bin/env python3
"""SRT subtitle generator — shot_bible VO text → YouTube-ready .srt

Reads the rendered clip durations and VO text to produce frame-accurate subtitles.
Timestamps account for b_open bridge offset so captions sync with the playable video.
"""
from __future__ import annotations

import json, os, subprocess, sys
from pathlib import Path


def format_srt_time(seconds: float) -> str:
    """Convert float seconds to SRT timestamp: HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main() -> int:
    outdir = Path(os.environ.get("OUTDIR", "/root/work/out/pd_intro"))
    ep = os.environ.get("EP", "pd_intro")

    bible_path = outdir / "shot_bible.json"
    if not bible_path.exists():
        print("  ⚠️ no shot_bible.json — SRT skip")
        return 0

    bible = json.loads(bible_path.read_text(encoding="utf-8"))
    beats = bible.get("beats") or []
    bridges = bible.get("bridges") or []

    # ── Calculate bridge_open offset ──
    # b_open is trimmed to 5.5s by _pd_assemble.py
    b_open_dur = 0.0
    for br in bridges:
        bid = br.get("id") or ""
        if br.get("before") == beats[0]["id"] if beats else False or \
           bid.startswith("b_open") or "open" in bid:
            b_open_dur = 5.5  # normalize_av max_t
            break
    # Also check if bridge file actually exists
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

    # ── Probe audio durations from rendered clips ──
    srt_entries = []
    cursor = b_open_dur

    for beat in beats:
        bid = beat["id"]
        text = beat.get("vo") or beat.get("caption") or bid
        mp3 = outdir / f"{bid}.mp3"

        dur = 0.0
        if mp3.exists():
            try:
                dur = float(subprocess.check_output([
                    "ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=nw=1:nk=1", str(mp3),
                ], text=True).strip() or "0")
            except Exception:
                dur = 3.0  # fallback
        else:
            dur = 3.0

        start = cursor
        end = cursor + dur
        srt_entries.append((start, end, text))
        cursor = end

    # ── Write SRT ──
    srt_path = outdir / f"{ep}.srt"
    lines = []
    for i, (start, end, text) in enumerate(srt_entries, 1):
        lines.append(str(i))
        lines.append(f"{format_srt_time(start)} --> {format_srt_time(end)}")
        # Break long lines into max 2 lines for readability
        if len(text) > 40:
            mid = text.rfind(" ", 0, len(text) // 2)
            if mid > 10:
                lines.append(text[:mid].strip())
                lines.append(text[mid:].strip())
            else:
                lines.append(text)
        else:
            lines.append(text)
        lines.append("")

    srt_path.write_text("\n".join(lines), encoding="utf-8")
    total_dur = cursor
    print(f"  📝 SRT: {len(srt_entries)} entries · {total_dur:.1f}s total · {srt_path}")
    print(f"  ⏱️  b_open offset: {b_open_dur:.1f}s")

    return 0


if __name__ == "__main__":
    sys.exit(main())
