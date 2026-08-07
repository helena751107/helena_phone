#!/usr/bin/env python3
"""QA: intro/playable must show DISTINCT non-black slides across timeline.

Exit 0 = pass, 2 = fail. Writes JSON report next to video.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def probe(path: Path):
    raw = subprocess.check_output(
        [
            "ffprobe", "-v", "error",
            "-show_streams", "-show_format",
            "-of", "json",
            str(path),
        ],
        text=True,
    )
    data = json.loads(raw)
    v = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), {})
    fmt = data.get("format") or {}

    def fnum(x, default=0.0):
        try:
            return float(x)
        except (TypeError, ValueError):
            return default

    return {
        "v_duration": fnum(v.get("duration") or fmt.get("duration")),
        "nb_frames": v.get("nb_frames") or "?",
        "width": v.get("width") or "?",
        "height": v.get("height") or "?",
        "pix_fmt": v.get("pix_fmt") or "?",
        "profile": v.get("profile") or "?",
        "a_duration": fnum(a.get("duration") or fmt.get("duration")),
        "format_duration": fnum(fmt.get("duration")),
        "size": int(fnum(fmt.get("size"))),
    }


def grab(path: Path, t: float, dest: Path) -> bool:
    r = subprocess.run(
        [
            "ffmpeg", "-y", "-ss", f"{t:.2f}", "-i", str(path),
            "-frames:v", "1", "-update", "1", str(dest),
        ],
        capture_output=True, text=True,
    )
    return r.returncode == 0 and dest.exists() and dest.stat().st_size > 2000


def frame_stats(img: Path):
    from PIL import Image
    im = Image.open(img).convert("RGB")
    # downsample for hash + luminance
    small = im.resize((48, 86))
    px = list(small.getdata())
    mean = sum(sum(c) / 3 for c in px) / len(px)
    # perceptual-ish hash: quantized blocks
    blocks = []
    w, h = small.size
    for by in range(0, h, 8):
        for bx in range(0, w, 8):
            vals = []
            for y in range(by, min(by + 8, h)):
                for x in range(bx, min(bx + 8, w)):
                    vals.append(sum(small.getpixel((x, y))) / 3)
            blocks.append(int(sum(vals) / max(1, len(vals)) // 16))
    return mean, tuple(blocks)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: _qa_video_slides.py <video.mp4> [n_samples]")
        return 1
    path = Path(sys.argv[1])
    n_samples = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    if not path.exists():
        print(f"FAIL missing {path}")
        return 2

    info = probe(path)
    dur = info["v_duration"] or info["format_duration"]
    adur = info["a_duration"] or info["format_duration"]
    fails = []
    notes = []

    if dur < 10:
        fails.append(f"video too short: {dur:.1f}s")
    if adur > 0 and dur < adur * 0.85:
        fails.append(f"video {dur:.1f}s << audio {adur:.1f}s (black tail risk)")
    if "444" in str(info.get("pix_fmt", "")):
        fails.append(f"pix_fmt {info['pix_fmt']} not phone-safe")

    # sample evenly across video (skip first/last 0.8s)
    lo, hi = 0.8, max(1.0, dur - 0.8)
    times = [lo + (hi - lo) * i / (n_samples - 1) for i in range(n_samples)]

    tmp = Path(tempfile.mkdtemp(prefix="qa_slides_"))
    means = []
    hashes = []
    black = 0
    for i, t in enumerate(times):
        dest = tmp / f"f{i:02d}_{t:.1f}.png"
        ok = grab(path, t, dest)
        if not ok:
            fails.append(f"frame grab fail @ {t:.1f}s")
            continue
        mean, h = frame_stats(dest)
        means.append(mean)
        hashes.append(h)
        if mean < 5.0:  # near-black (dark theme site content ~10-13, threshold must leave headroom)
            black += 1
            notes.append(f"blackish @ {t:.1f}s mean={mean:.1f}")

    unique = len(set(hashes))
    notes.append(f"unique_frames={unique}/{len(hashes)} black={black}")
    # need real scene diversity: at least half unique and ≤1 black sample
    min_unique = max(3, n_samples // 2)
    if unique < min_unique:
        fails.append(f"slides frozen/not changing: unique={unique} need>={min_unique}")
    if black > 1:
        fails.append(f"too many black frames: {black}/{len(hashes)}")

    report = {
        "path": str(path),
        "probe": info,
        "times": times,
        "means": means,
        "unique": unique,
        "black": black,
        "fails": fails,
        "notes": notes,
        "pass": not fails,
    }
    rep_path = path.with_suffix(path.suffix + ".qa.json")
    rep_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if fails:
        print("QA FAIL", path.name)
        for f in fails:
            print(" -", f)
        for n in notes:
            print(" ·", n)
        return 2
    print("QA PASS", path.name, f"dur={dur:.1f}s unique={unique}/{len(hashes)}")
    for n in notes:
        print(" ·", n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
