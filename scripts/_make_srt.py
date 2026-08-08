#!/usr/bin/env python3
"""SRT subtitle generator V9 — shot_bible VO text → YouTube-ready .srt

V9: Reads _timing.json from _render_video.py for frame-accurate per-beat timestamps.
The xfade concat compresses the timeline; naive cumulative VO+dur+pause doesn't match.
Bridge open offset is probed from actual bridge files (not hardcoded).
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

    # ── V9: Read _timing.json from render (xfade-aware per-beat start/end) ──
    timing_path = outdir / "work" / "_timing.json"
    beat_timing = {}  # beat_id → {start, end, duration}
    if timing_path.exists():
        timing = json.loads(timing_path.read_text(encoding="utf-8"))
        for tb in timing.get("beats", []):
            beat_timing[tb["id"]] = tb
        print(f"  ⏱️  _timing.json: {len(beat_timing)} beats, body={timing.get('body_duration', 0):.1f}s")
    else:
        print("  ⚠️ no _timing.json — fallback to ffprobe-based (may be out of sync)")

    # ── Calculate bridge_open offset (only if shot_bible defines bridges) ──
    b_open_dur = 0.0
    bridges = bible.get("bridges") or []
    has_open_bridge = False
    for br in bridges:
        bid = br.get("id") or ""
        if bid.startswith("b_open") or "open" in bid or br.get("before") == (beats[0]["id"] if beats else ""):
            has_open_bridge = True
            b_open_dur = 5.5
            break
    if has_open_bridge:
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

    # ── Build SRT entries ──
    srt_entries = []

    for beat in beats:
        bid = beat["id"]
        text = beat.get("vo") or beat.get("caption") or bid

        if bid in beat_timing:
            # V9: use frame-accurate timing from xfade concat
            start = b_open_dur + beat_timing[bid]["start"]
            end = b_open_dur + beat_timing[bid]["end"]
        else:
            # Fallback: probe MP3 (old method, inaccurate for xfade)
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
            start = b_open_dur
            end = b_open_dur + dur
            print(f"  ⚠️ {bid}: no timing data — using fallback {start:.1f}s→{end:.1f}s")

        srt_entries.append((start, end, text))

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
    total_dur = srt_entries[-1][1] if srt_entries else 0
    print(f"  📝 SRT: {len(srt_entries)} entries · {total_dur:.1f}s total · {srt_path}")
    print(f"  ⏱️  b_open offset: {b_open_dur:.1f}s")

    return 0


if __name__ == "__main__":
    sys.exit(main())
