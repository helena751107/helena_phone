#!/usr/bin/env python3
"""ASS animated subtitle generator V9.1 — CNN Breaking News style

Per-word pop-in animation with \\t() scale bounce.
No \\k karaoke — each word flies in with dramatic scale pop.
Red banner bar behind text (BorderStyle=3 opaque box).

V9.1: Reads _timing.json from _render_video.py for frame-accurate per-beat timestamps.
ASS timestamps are body-relative (t=0 at body start) because ASS is burned into
the body at P4 (before bridges are added at P5).

Usage:
  OUTDIR=/root/work/out/pd_intro EP=pd_intro python3 scripts/_make_ass.py
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
    """Split Korean text into display words. Short fragments merged."""
    words = text.split()
    merged = []
    for w in words:
        if merged and len(w) <= 2 and len(merged[-1]) <= 3:
            merged[-1] += " " + w
        else:
            merged.append(w)
    return merged


# ═══════════════════════════════════════════════════════════════
#  CNN Breaking News — Style Tokens
# ═══════════════════════════════════════════════════════════════

FONT_SIZE   = 72          # pt
SCALE_PEAK  = 200         # % — start at 2× size
SCALE_POP_MS = 100        # ms — pop animation duration
MARGIN_V    = 180         # px from bottom
PLAY_RES_X  = 1080
PLAY_RES_Y  = 1920
CENTER_X    = 540
SUBTITLE_Y   = PLAY_RES_Y - MARGIN_V  # 1740
WORD_GAP     = 12           # px between words
LINE_SPACING = int(FONT_SIZE * 1.45)  # px between baselines
MAX_LINE_W   = PLAY_RES_X - 120       # 960px — leave side margins


def estimate_word_width_px(word: str) -> int:
    """Rough pixel width for Korean + Latin mix at FONT_SIZE pt."""
    w = 0.0
    for ch in word:
        cp = ord(ch)
        if cp == 0x20:
            w += FONT_SIZE * 0.30
        elif 0xAC00 <= cp <= 0xD7AF:     # Hangul syllable
            w += FONT_SIZE * 0.88
        elif 0x3131 <= cp <= 0x318E:     # Hangul jamo
            w += FONT_SIZE * 0.55
        elif cp < 0x80:                  # ASCII / Latin / digits
            w += FONT_SIZE * 0.52
        else:                            # CJK punctuation etc.
            w += FONT_SIZE * 0.55
    return max(1, int(w))


def main() -> int:
    outdir = Path(os.environ.get("OUTDIR", "/root/work/out/pd_intro"))
    ep     = os.environ.get("EP", "pd_intro")

    bible_path = outdir / "shot_bible.json"
    if not bible_path.exists():
        print("  ⚠️  no shot_bible.json — ASS skip")
        return 0

    bible = json.loads(bible_path.read_text(encoding="utf-8"))
    beats = bible.get("beats") or []

    # ── V9.1: Read _timing.json from render (xfade-aware per-beat start/end) ──
    # ASS timestamps are body-relative (t=0 at body start) because burn-in
    # happens at P4 before bridges are added at P5.
    timing_path = outdir / "work" / "_timing.json"
    beat_timing = {}  # beat_id → {start, end, duration}
    body_duration = 0.0
    use_timing = False
    if timing_path.exists():
        timing = json.loads(timing_path.read_text(encoding="utf-8"))
        for tb in timing.get("beats", []):
            beat_timing[tb["id"]] = tb
        body_duration = timing.get("body_duration", 0)
        use_timing = True
        print(f"  ⏱️  _timing.json: {len(beat_timing)} beats, body={body_duration:.1f}s")
    else:
        print("  ⚠️  no _timing.json — falling back to ffprobe (timestamps may be out of sync)")

    # ── ASS Header ──────────────────────────────────────────
    # BorderStyle=3 = opaque box behind text → red banner bar
    # BackColour=&HB00D0DCC (dark red @ 75% alpha = 0xBB)
    # Outline=5, Shadow=2  → thick border for punch
    ass_header = [
        "[Script Info]",
        f"Title: {ep} — CNN Breaking News",
        "ScriptType: v4.00+",
        f"PlayResX: {PLAY_RES_X}",
        f"PlayResY: {PLAY_RES_Y}",
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        # CNN: Primary=white, BackColour=dark-red banner, Outline=black
        f"Style: CNN,Noto Sans CJK KR,{FONT_SIZE},&H00FFFFFF,&H00666666,&H00000000,&HBB0000CC,"
        f"-1,0,0,0,100,100,0,0,3,5,2,2,{MARGIN_V},{MARGIN_V},{MARGIN_V},1",
        # Caption (small warm title at top)
        "Style: Caption,Noto Serif CJK KR,24,&H00FFB060,&H00000000,&H00000000,&HAA000000,"
        "-1,0,0,0,100,100,0,0,1,2,0,8,80,80,40,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    dialogues = []

    # ── Fallback: probe bridge open + MP3 durations (old method) ──
    def _fallback_beat_timing(beat):
        """Return (start, end, dur) using old ffprobe-based method."""
        bid = beat["id"]
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
        return 0.0, dur, dur  # (start, end, dur) — start=0 is a guess

    # For fallback mode: track cumulative cursor
    fallback_cursor = 0.0
    if not use_timing:
        # old-style b_open_dur for fallback
        bridges = bible.get("bridges") or []
        fallback_cursor = 0.0
        for br in bridges:
            if (br.get("id") or "").startswith("b_open") or "open" in (br.get("id") or ""):
                fallback_cursor = 5.5
                break
        b_open_file = outdir / "bridge" / "b_open.mp4"
        if not b_open_file.exists():
            fallback_cursor = 0.0

    for beat in beats:
        bid      = beat["id"]
        vo_text  = beat.get("vo") or beat.get("caption") or bid
        caption  = beat.get("caption") or ""
        pause    = float(beat.get("pause", 0))

        if use_timing and bid in beat_timing:
            # V9.1: frame-accurate xfade timing — body-relative (no bridge offset)
            bt = beat_timing[bid]
            beat_start = bt["start"]
            beat_end   = bt["end"]
            dur        = bt["duration"]
        else:
            # Fallback
            fallback_start, fallback_end, dur = _fallback_beat_timing(beat)
            beat_start = fallback_cursor
            beat_end   = fallback_cursor + dur

        # ── Split & time words ──
        words = split_korean_words(vo_text)
        total_chars = sum(len(w) for w in words)
        if total_chars <= 0:
            total_chars = 1
        char_dur = dur / total_chars

        # ── Layout: word-wrap into lines (max MAX_LINE_W px) ──
        widths = [estimate_word_width_px(w) for w in words]

        # Group words into lines
        raw_lines = []          # list of (word_indices, line_width)
        cur_indices = []
        cur_w = 0
        for wi, ww in enumerate(widths):
            gap = WORD_GAP if cur_indices else 0
            if cur_w + gap + ww > MAX_LINE_W and cur_indices:
                raw_lines.append((cur_indices, cur_w))
                cur_indices = []
                cur_w = 0
                gap = 0
            cur_indices.append(wi)
            cur_w += gap + ww
        if cur_indices:
            raw_lines.append((cur_indices, cur_w))

        n_lines = len(raw_lines)
        # y positions: bottom-most line at SUBTITLE_Y, each line above by LINE_SPACING
        line_base_ys = [SUBTITLE_Y - (n_lines - 1 - li) * LINE_SPACING
                        for li in range(n_lines)]

        # ── Per-word animated Dialogue events ──
        word_time_cursor = 0.0    # seconds into the beat
        global_wi = 0             # across all lines

        for li, (indices, line_w) in enumerate(raw_lines):
            start_x = CENTER_X - line_w // 2
            x_cursor = start_x
            line_y = line_base_ys[li]

            for idx in indices:
                w = words[idx]
                ww = widths[idx]
                w_dur = max(0.06, len(w) * char_dur)   # at least 60 ms

                w_start = beat_start + word_time_cursor
                w_end   = beat_end
                w_x     = x_cursor + ww // 2

                # Layer = (line*100 + word_index) to avoid overlap issues
                layer = li * 100 + idx

                tag = (
                    f"{{\\an2\\pos({w_x},{line_y})"
                    f"\\fscx{SCALE_PEAK}\\fscy{SCALE_PEAK}"
                    f"\\t(0,{SCALE_POP_MS},\\fscx100\\fscy100)}}"
                    f"{w}"
                )

                dialogues.append(
                    f"Dialogue: {layer},{format_ass_time(w_start)},{format_ass_time(w_end)},"
                    f"CNN,,0,0,0,,{tag}"
                )

                word_time_cursor += w_dur
                x_cursor         += ww + WORD_GAP
                global_wi += 1

        # ── Caption line (small, top area) ──
        if caption:
            dialogues.append(
                f"Dialogue: 99,{format_ass_time(beat_start)},{format_ass_time(beat_end)},"
                f"Caption,,0,0,0,,{caption}"
            )

        if not use_timing:
            fallback_cursor = fallback_cursor + dur + pause

    # ── Write .ass ──────────────────────────────────────────
    ass_lines = ass_header + dialogues + [""]
    ass_path = outdir / f"{ep}.ass"
    ass_path.write_text("\n".join(ass_lines), encoding="utf-8")

    last_end = beat_timing[beats[-1]["id"]]["end"] if use_timing and beats and beats[-1]["id"] in beat_timing else (fallback_cursor if not use_timing else 0)
    total_dur = last_end
    print(f"  🎬 ASS CNN Breaking News: {len(beats)} beats · total={total_dur:.1f}s · {ass_path}")
    print(f"  🎯 Per-word pop: {SCALE_PEAK}%→100% over {SCALE_POP_MS}ms")
    print(f"  🟥 Red banner bg · {FONT_SIZE}pt bold · ≤{MAX_LINE_W}px/line · {LINE_SPACING}px spacing")
    timing_src = "xfade _timing.json" if use_timing else "ffprobe fallback"
    print(f"  ⏱️  timing source: {timing_src}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
