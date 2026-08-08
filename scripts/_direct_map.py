#!/usr/bin/env python3
"""P0.6 Directing Map — beat 내용 기반 연출 자동 결정

VO 길이, caption, role을 분석해 per-beat 연출을 결정:
- zoom type (in/out/pan_right/pan_left)
- color_tag (gold/warm/teal/cool/cinematic)
- scroll_sel 검증 (selector 유효성)

LLM 불필요 — 순수 규칙 기반.

Usage:
  python3 scripts/_direct_map.py <OUTDIR>
  python3 scripts/_direct_map.py /root/work/out/pd_tistory_v2
"""
from __future__ import annotations

import json, os, sys
from pathlib import Path


# ── Valid color tags (matching _render_video.py COLOR_GRADES) ──
VALID_COLORS = {"warm", "cinematic", "natural", "cool", "gold", "teal"}

# ── Valid zoom types ──
VALID_ZOOMS = {"in", "out", "pan_right", "pan_left"}


def choose_zoom(beat: dict) -> dict:
    """Choose zoom type based on VO text length and role."""
    role = beat.get("role", "build")
    vo_text = beat.get("vo", "")
    vo_len = len(vo_text)

    # Role-based defaults
    role_zoom = {
        "hook":    {"type": "out", "pan": "none"},       # wide establishing shot
        "build":   {"type": "in", "pan": "none"},        # focus on details
        "climax":  {"type": "pan_right", "pan": "none"}, # dramatic reveal
        "resolve": {"type": "out", "pan": "none"},       # pull back, wrap up
    }

    base = role_zoom.get(role, {"type": "in", "pan": "none"})

    # Refine based on text length
    if vo_len <= 30:
        base["type"] = "out"          # short text = wide view
    elif vo_len > 80:
        if base["type"] == "in":
            base["type"] = "pan_right"  # long text = scan across

    return base


def choose_color(beat: dict, beat_index: int, total_beats: int) -> str:
    """Choose color grade based on role + position in sequence."""
    role = beat.get("role", "build")

    # Position in overall sequence
    progress = beat_index / max(total_beats - 1, 1)

    role_color = {
        "hook":    "gold",
        "build":   "warm",
        "climax":  "gold",
        "resolve": "warm",
    }

    base = role_color.get(role, "warm")

    # Add variety: alternate "warm"/"teal" for consecutive build beats
    if role == "build":
        base = "teal" if beat_index % 2 == 1 else "warm"

    # Ensure valid
    return base if base in VALID_COLORS else "warm"


def choose_pause(beat: dict) -> float:
    """Choose breathing pause between beats."""
    role = beat.get("role", "build")
    pause_map = {"hook": 0.8, "build": 0.4, "climax": 0.6, "resolve": 1.0}
    return pause_map.get(role, 0.5)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 _direct_map.py <OUTDIR>")
        return 1

    outdir = Path(sys.argv[1])
    bible_path = outdir / "shot_bible.json"

    if not bible_path.exists():
        print(f"❌ No shot_bible.json in {outdir}")
        return 1

    bible = json.loads(bible_path.read_text(encoding="utf-8"))
    beats = bible.get("beats") or []

    if not beats:
        print("⚠️  No beats in shot_bible — skip directing")
        return 0

    total = len(beats)
    print(f"🎬 P0.6 Directing Map — {total} beats")

    page_beats = [b for b in beats if b.get("kind") != "bridge"]
    page_total = len(page_beats)

    for i, beat in enumerate(beats):
        if beat.get("kind") == "bridge":
            continue

        # Position among page beats
        page_idx = [j for j, b in enumerate(page_beats) if b["id"] == beat["id"]]
        page_idx = page_idx[0] if page_idx else i

        # ── Zoom ──
        beat["zoom"] = choose_zoom(beat)

        # ── Color ──
        beat["color_tag"] = choose_color(beat, page_idx, page_total)

        # ── Pause ──
        beat["pause"] = choose_pause(beat)

        # ── Emotion ──
        role = beat.get("role", "build")
        emotion_map = {
            "hook": "hook", "build": "trust",
            "climax": "rise", "resolve": "handoff",
        }
        beat["emotion"] = emotion_map.get(role, "trust")

        # ── Validate scroll_sel ──
        sel = beat.get("scroll_sel") or beat.get("section_selector")
        if sel:
            # Basic sanity: should not be empty or too generic
            if sel in ("body", "html", "*", ""):
                beat["scroll_sel"] = None
            else:
                beat["scroll_sel"] = sel

        zoom_str = beat["zoom"]["type"]
        print(f"  {beat['id']:25s} | {beat['role']:7s} | zoom={zoom_str:10s} | color={beat['color_tag']:6s} | pause={beat['pause']:.1f}s")

    # ── Save ──
    bible["version"] = "v10"
    bible_path.write_text(
        json.dumps(bible, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"  ✅ Directing complete — ready for P1 capture")
    print(f"  Next: bash scripts/produce_pd.sh {bible['id']} {bible.get('url','')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
