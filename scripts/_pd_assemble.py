#!/usr/bin/env python3
"""PD assemble: VO body + bridge bookends + full-timeline Boss BGM whisper.

Env:
  OUTDIR, EP, BGM_VOLUME, BGM_PATH
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd, label=""):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "")[-500:]
        raise SystemExit(f"FAIL {label}: {err}")
    return r


def probe_dur(path: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=nw=1:nk=1",
            str(path),
        ],
        text=True,
    ).strip()
    try:
        return float(out or "0")
    except ValueError:
        return 0.0


def normalize_av(src: Path, dest: Path, silence=False, max_t=None):
    cmd = ["ffmpeg", "-y", "-i", str(src)]
    if silence:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
    if max_t is not None:
        cmd += ["-t", str(max_t)]
    cmd += [
        "-vf",
        "scale=1080:1920:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,format=yuv420p",
        "-c:v", "libx264", "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p",
        "-preset", "veryfast", "-crf", "20",
    ]
    if silence:
        cmd += [
            "-map", "0:v", "-map", "1:a",
            "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2", "-shortest",
        ]
    else:
        cmd += ["-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2"]
    cmd += ["-movflags", "+faststart", str(dest)]
    run(cmd, f"norm {dest.name}")


def is_open_bridge(br: dict) -> bool:
    bid = br.get("id") or ""
    return (
        br.get("before") == "01_hero"
        or (br.get("after") is None and "open" in bid)
        or bid.endswith("open")
        or bid.startswith("b_open")
    )


def main() -> int:
    outdir = Path(os.environ.get("OUTDIR", "/root/work/out/pd_intro"))
    ep = os.environ.get("EP", "pd_intro")
    bgm_vol = float(os.environ.get("BGM_VOLUME", "0.025"))
    bgm_path = (os.environ.get("BGM_PATH") or "").strip()
    work = outdir / "work"
    work.mkdir(parents=True, exist_ok=True)

    vo = outdir / f"{ep}_vo.mp4"
    raw = outdir / f"{ep}_final.mp4"
    body_src = vo if vo.exists() else raw
    if not body_src.exists():
        cands = list(outdir.glob("*_vo.mp4")) + list(outdir.glob("*_final.mp4"))
        if not cands:
            raise SystemExit("no body mp4 from render")
        body_src = cands[0]
    print(f"  body_src={body_src.name} (VO-only preferred for single BGM pass)")

    bible_path = outdir / "shot_bible.json"
    bible = json.loads(bible_path.read_text(encoding="utf-8")) if bible_path.exists() else {}
    bridges = []
    for br in bible.get("bridges") or []:
        p = outdir / br["file"]
        if p.exists():
            bridges.append((br, p))

    body_n = work / "body_n.mp4"
    normalize_av(body_src, body_n)

    seq = []
    for br, p in bridges:
        if not is_open_bridge(br):
            continue
        d = work / f"open_{br['id']}.mp4"
        normalize_av(p, d, silence=True, max_t=5.5)
        seq.append(d)

    seq.append(body_n)

    for br, p in bridges:
        if is_open_bridge(br):
            continue
        d = work / f"close_{br['id']}.mp4"
        normalize_av(p, d, silence=True, max_t=5.5)
        seq.append(d)

    lst = work / "seq_v2.txt"
    lst.write_text("".join(f"file '{s.resolve()}'\n" for s in seq), encoding="utf-8")
    print("  concat parts:", [s.name for s in seq])

    concat_raw = work / "concat_raw.mp4"
    run(
        [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
            "-c:v", "libx264", "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p",
            "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart", str(concat_raw),
        ],
        "concat",
    )

    bgm_cands = []
    if bgm_path and Path(bgm_path).exists():
        bgm_cands.append(Path(bgm_path))
    for c in [
        outdir / "bgm_shorts.m4a",
        outdir / "bgm.m4a",
        outdir / "bgm.mp3",
        Path("/root/work/helena-piano/bgm/output/satie_gymnopedie1.mp3"),
        Path("/root/work/helena-piano/bgm/output/satie_gymnopedie3.mp3"),
        Path("/root/work/helena-piano/bgm/output/clair_de_lune.mp3"),
    ]:
        if c.exists() and c not in bgm_cands:
            bgm_cands.append(c)
    bgm = bgm_cands[0] if bgm_cands else None

    play = outdir / f"{ep}_playable.mp4"
    if bgm:
        dur = probe_dur(concat_raw)
        fade_out = max(0.5, dur - 2.5)
        duck_enabled = os.environ.get("AUDIO_DUCKING", "1") not in ("0", "false", "no")
        duck_thr = float(os.environ.get("DUCK_THRESHOLD", "0.02"))
        duck_ratio = os.environ.get("DUCK_RATIO", "3")
        duck_att = os.environ.get("DUCK_ATTACK", "5")
        duck_rel = os.environ.get("DUCK_RELEASE", "300")
        if duck_enabled:
            print(f"  🎵 FULL-timeline BGM {bgm.name} vol={bgm_vol} 🔊 ducking dur={dur:.1f}s")
            filter_cplx = (
                f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=1.0[voice];"
                f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,"
                f"volume={bgm_vol},afade=t=in:st=0:d=1.5,afade=t=out:st={fade_out:.1f}:d=2.0[music_pre];"
                f"[music_pre][voice]sidechaincompress="
                f"threshold={duck_thr}:ratio={duck_ratio}:attack={duck_att}:release={duck_rel}:makeup=1[music_ducked];"
                f"[voice][music_ducked]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[aout]"
            )
        else:
            print(f"  🎵 FULL-timeline BGM {bgm.name} vol={bgm_vol} dur={dur:.1f}s")
            filter_cplx = (
                f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=1.0[voice];"
                f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,"
                f"volume={bgm_vol},afade=t=in:st=0:d=1.5,afade=t=out:st={fade_out:.1f}:d=2.0[music];"
                f"[voice][music]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[aout]"
            )
        run(
            [
                "ffmpeg", "-y",
                "-i", str(concat_raw),
                "-stream_loop", "-1", "-i", str(bgm),
                "-filter_complex", filter_cplx,
                "-map", "0:v", "-map", "[aout]",
                "-c:v", "copy",
                "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
                "-shortest", "-movflags", "+faststart",
                str(play),
            ],
            "bgm-full",
        )
        print(f"  ✅ BGM mixed full timeline → {play.name}")
    else:
        print("  ⚠️ no BGM — shipping concat as playable")
        shutil.copy(concat_raw, play)

    (outdir / "settings_whisper.json").write_text(
        json.dumps(
            {
                "BGM_VOLUME": bgm_vol,
                "BGM_PATH": str(bgm) if bgm else None,
                "body_src": body_src.name,
                "bridges": [br["id"] for br, _ in bridges],
                "encode": "yuv420p High@L4.0 AAC 48kHz",
                "font": "Noto Sans/Serif CJK KR (fontconfig)",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    info = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=profile,pix_fmt,width,height",
            "-of", "default=nw=1:nk=1", str(play),
        ],
        text=True,
    ).strip().splitlines()
    print("  playable:", info, "size", play.stat().st_size, f"dur={probe_dur(play):.1f}s")
    if any("444" in x or "4:4:4" in x for x in info):
        raise SystemExit("GATE FAIL: still yuv444")
    print("  GATE playable encode OK")

    # Slide diversity / non-black QA (blocks ship on freeze/black tail)
    qa = Path(__file__).resolve().parent / "_qa_video_slides.py"
    if qa.exists():
        r = subprocess.run([sys.executable, str(qa), str(play), "10"], capture_output=True, text=True)
        print(r.stdout or "")
        if r.returncode != 0:
            print(r.stderr or "")
            raise SystemExit("QA GATE FAIL: slides not changing or black frames — do not ship")
        print("  GATE slides QA OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
