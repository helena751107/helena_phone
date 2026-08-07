#!/usr/bin/env bash
# 🎬 produce_plugin.sh — STANDARD v3 (page-first · Grok PD/voice/bridge)
#
# Boss 역할 정정:
#   · 웹페이지 비주얼 본체 = Playwright/공짜 공장 (전 구간 재래스터 금지)
#   · Grok 토큰 = PD 대본 + 성우(xAI TTS) + 브릿지 컷(소수) 만
#   · 이어 붙이기 = FFmpeg only
#   · 공짜 produce_intro 보다 못하면 실패
#
# 기술: TTS-first · yuv420p High@L4.0 · AAC 48k · xfade · short ASS · BGM duck
# 스펙: configs/video_plugin_standard_v3.json
#
# 사용:
#   bash scripts/produce_plugin.sh <plugin_dir>
#
# plugin_dir:
#   manifest.json   (mode: page_first 권장)
#   stills/…        live 페이지 캡처 위주
#   motion/…        브릿지 모션만 (optional)
#   bgm.m4a

set -euo pipefail

PLUGIN_DIR="${1:?plugin_dir 필요}"
PLUGIN_DIR="$(cd "$PLUGIN_DIR" && pwd)"
MANIFEST="${PLUGIN_DIR}/manifest.json"
[[ -f "$MANIFEST" ]] || { echo "❌ manifest.json 없음: $MANIFEST"; exit 1; }

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GROK_TTS="${ROOT}/scripts/grok_tts.py"
STANDARD="${ROOT}/configs/video_plugin_standard_v3.json"
if [[ ! -f "$STANDARD" ]]; then
  STANDARD="${ROOT}/configs/video_plugin_standard_v1.json"
fi

if [[ -f "${ROOT}/.secrets.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${ROOT}/.secrets.env"
  set +a
fi

export PYTHONIOENCODING=utf-8

python3 - "$PLUGIN_DIR" "$GROK_TTS" "$STANDARD" <<'PY'
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

plugin = Path(sys.argv[1])
grok_tts = Path(sys.argv[2])
standard_path = Path(sys.argv[3])
man = json.loads((plugin / "manifest.json").read_text(encoding="utf-8"))
std = json.loads(standard_path.read_text(encoding="utf-8")) if standard_path.exists() else {}
bar = std.get("quality_bar") or {}

pid = man.get("id") or plugin.name
title = man.get("title") or pid
voice = man.get("voice") or (std.get("default_voice") or {}).get("voice_id") or "ara"
lang = man.get("lang") or "ko"
speed = float(man.get("speed") or 0.95)
# A-bar default 1080
resolution = man.get("resolution") or bar.get("resolution") or "1080:1920"
preset = man.get("preset") or bar.get("preset") or "veryfast"
crf = str(man.get("crf") or bar.get("crf") or 20)
bgm_vol = float(man.get("bgm_volume") or 0.07)
clip_sec = float(man.get("clip_sec") or 10)
xfade = float(man.get("xfade_sec") or bar.get("xfade_sec") or 0.45)
send_tg = bool(man.get("send_tg", True))
require_subs = bool(man.get("subs", bar.get("require_subs", True)))
allow_edge = bool(man.get("allow_edge_fallback", False))
kenburns = bool(man.get("kenburns", True))
slides = man["slides"]
assert slides, "slides empty"

W, H = map(int, resolution.split(":"))
out = Path(man.get("outdir") or f"/root/work/out/{pid}")
work = out / "work"
work.mkdir(parents=True, exist_ok=True)

# Hangul: fontconfig CJK KR (NotoSansKR.ttf often missing → DejaVu tofu)
import subprocess as _sp
def _fc(fam):
    r = _sp.run(["fc-list", fam, "file"], capture_output=True, text=True)
    return bool((r.stdout or "").strip())
if _fc("Noto Sans CJK KR"):
    FONT = "Noto Sans CJK KR"  # used as font= via fontconfig
    FONT_IS_FC = True
elif Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc").exists():
    FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    FONT_IS_FC = False
else:
    FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    FONT_IS_FC = False
    print("  ⚠ Hangul font missing — captions may tofu")

mode = man.get("mode") or "page_first"  # page_first | bridge_heavy (discouraged)
print(f"=== 🎬 produce_plugin STANDARD v3 (page-first · PD/voice/bridge) ===")
print(f"  id={pid}  title={title}  mode={mode}")
print(f"  voice=Grok/{voice}  res={resolution}  clip={clip_sec}s  xfade={xfade}s")
print(f"  roles: page/live=factory · VO=Grok · bridge=Grok optional · assemble=FFmpeg")
print(f"  out={out}")
if mode != "page_first":
    print("  ⚠ mode!=page_first — Boss 정본은 page_first (웹 재래스터 최소화)")


def run(cmd, check=True):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if check and r.returncode != 0:
        err = (r.stderr or r.stdout or "")[-800:]
        raise SystemExit(f"CMD FAIL ({r.returncode}): {' '.join(map(str, cmd[:6]))}…\n{err}")
    return r


def ffprobe_dur(path: Path) -> float:
    r = run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=nw=1:nk=1",
            str(path),
        ]
    )
    try:
        return float((r.stdout or "0").strip() or "0")
    except ValueError:
        return 0.0


def escape_drawtext(s: str) -> str:
    return (
        s.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace("%", "%%")
    )


def escape_ass(s: str) -> str:
    return s.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


# ── L1 TTS-first (Grok only) ──
print("[1/7] Grok TTS-first…")
tts_meta = []
for i, s in enumerate(slides, 1):
    sid = s.get("id") or f"{i:02d}"
    text = (s.get("text") or "").strip()
    if not text:
        raise SystemExit(f"slide {sid}: empty text")
    # speech-tag friendly: keep punctuation; optional tags from manifest
    if s.get("speech_tags"):
        text = s["speech_tags"]
    txt = work / f"{sid}.txt"
    mp3 = work / f"{sid}_raw.mp3"
    txt.write_text(text, encoding="utf-8")
    r = run(
        [
            sys.executable, str(grok_tts),
            "--file", str(txt),
            "--out", str(mp3),
            "--voice", voice,
            "--lang", lang,
            "--speed", str(speed),
        ],
        check=False,
    )
    if r.returncode != 0 or not mp3.exists() or mp3.stat().st_size < 200:
        if not allow_edge:
            print(r.stdout)
            print(r.stderr, file=sys.stderr)
            raise SystemExit(f"Grok TTS failed {sid} (edge fallback disabled)")
        # emergency edge only if allowed
        run(
            [
                "edge-tts", "-f", str(txt),
                "--voice", "ko-KR-InJoonNeural",
                "--write-media", str(mp3),
            ]
        )
        provider = "edge-FALLBACK"
    else:
        provider = f"grok/{voice}"
        print(f"  [{i}/{len(slides)}] {r.stdout.strip()}")

    # loudnorm narration
    nar = work / f"{sid}_nar.m4a"
    ln = (bar.get("audio") or {}).get("narration_loudnorm") or "I=-14:TP=-1.5:LRA=9"
    run(
        [
            "ffmpeg", "-y", "-i", str(mp3),
            "-af", f"loudnorm={ln},aformat=sample_rates=48000:channel_layouts=stereo",
            "-c:a", "aac", "-b:a", "192k", str(nar),
        ]
    )
    vo_dur = ffprobe_dur(nar)
    # VO must fill most of the clip — community: no dead air
    # If VO short, we still pad but GATE will warn if gap > 1.0s
    gap = max(0.0, clip_sec - vo_dur)
    pad = work / f"{sid}_pad.m4a"
    run(
        [
            "ffmpeg", "-y", "-i", str(nar),
            "-af", f"apad=whole_dur={clip_sec}",
            "-t", str(clip_sec), "-c:a", "aac", "-b:a", "192k", str(pad),
        ]
    )
    tts_meta.append(
        {
            "id": sid,
            "provider": provider,
            "vo_dur": vo_dur,
            "gap": gap,
            "text": text,
            "title": s.get("title") or "",
            "audio": pad,
        }
    )
    print(f"      vo={vo_dur:.2f}s gap={gap:.2f}s provider={provider}")


# ── L2 resolve visuals ──
print("[2/7] Visuals (motion mp4 or still+KenBurns)…")
vis_paths = []
for i, s in enumerate(slides, 1):
    sid = s.get("id") or f"{i:02d}"
    # motion ONLY if manifest explicitly sets "motion" (no auto-steal of live UI shots)
    motion = s.get("motion")
    still = s.get("still")
    mp4 = None
    if motion:
        p = (plugin / motion).resolve()
        if p.exists():
            mp4 = p
        else:
            raise SystemExit(f"slide {sid}: motion missing {motion}")
    img = None
    if still:
        img = (plugin / still).resolve()
        if not img.exists():
            for ext in (".jpg", ".png", ".jpeg", ".webp"):
                alt = plugin / "stills" / f"{sid}{ext}"
                if alt.exists():
                    img = alt
                    break
    if mp4 is None and (img is None or not img.exists()):
        raise SystemExit(f"slide {sid}: need still or motion")
    vis_paths.append({"id": sid, "motion": mp4, "still": img})
    kind = "motion" if mp4 else "still+KenBurns"
    print(f"  🖼  {sid}: {kind} ← {(mp4 or img).name}")


# ── L3 build per-clip video (Ken Burns / scale) + burn soft title ──
print("[3/7] Per-clip encode…")
clips = []
for i, (s, meta, vis) in enumerate(zip(slides, tts_meta, vis_paths)):
    sid = meta["id"]
    clip = work / f"clip_{sid}.mp4"
    # chip titles OFF by default when subs=on (double labels kill A-grade)
    on_title = ""
    if man.get("draw_title_chip") and meta["title"]:
        on_title = escape_drawtext(meta["title"][:28])
    title_vf = ""
    if on_title and (FONT_IS_FC or Path(FONT).exists()):
        font_opt = f"font={FONT.replace(' ', r'\\ ')}" if FONT_IS_FC else f"fontfile={FONT}"
        title_vf = (
            f",drawtext=text='{on_title}':fontcolor=#d4a84b:fontsize={max(20, H//60)}:"
            f"x=(w-text_w)/2:y=h-h*0.045:{font_opt}:"
            f"box=1:boxcolor=black@0.45:boxborderw=6"
        )

    if vis["motion"] is not None:
        # normalize motion to res/fps/dur
        vf = (
            f"scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H},fps=30,format=yuv420p,setsar=1"
            f"{title_vf}"
        )
        run(
            [
                "ffmpeg", "-y",
                "-i", str(vis["motion"]),
                "-i", str(meta["audio"]),
                "-filter_complex",
                f"[0:v]{vf},trim=duration={clip_sec},setpts=PTS-STARTPTS[v];"
                f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,"
                f"atrim=duration={clip_sec},asetpts=PTS-STARTPTS[a]",
                "-map", "[v]", "-map", "[a]",
                # Phone/Telegram: MUST yuv420p High — yuv444 High4:4:4 = black screen on play
                "-c:v", "libx264", "-preset", preset, "-crf", crf,
                "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
                "-movflags", "+faststart",
                "-t", str(clip_sec),
                str(clip),
            ]
        )
    else:
        # Ken Burns slow push-in (community: stills need motion)
        frames = int(clip_sec * 30)
        if kenburns:
            # zoompan: gentle 1.0 → 1.10 (scale ~2× output — phone-friendly, was 8000 too heavy)
            zvf = (
                f"scale={W*2}:{H*2},"
                f"zoompan=z='min(zoom+0.0004,1.10)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"d={frames}:s={W}x{H}:fps=30,"
                f"format=yuv420p{title_vf}"
            )
        else:
            zvf = (
                f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
                f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p{title_vf}"
            )
        run(
            [
                "ffmpeg", "-y",
                "-loop", "1", "-t", str(clip_sec), "-i", str(vis["still"]),
                "-i", str(meta["audio"]),
                "-filter_complex",
                f"[0:v]{zvf},format=yuv420p[v];"
                f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,"
                f"atrim=duration={clip_sec},asetpts=PTS-STARTPTS[a]",
                "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-preset", preset, "-crf", crf,
                "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
                "-movflags", "+faststart",
                "-t", str(clip_sec),
                str(clip),
            ]
        )
    d = ffprobe_dur(clip)
    print(f"  🎞  clip_{sid} {d:.2f}s ({clip.stat().st_size//1024}KB)")
    clips.append(clip)


# ── L4 ASS subtitles — CapCut-style word-by-word or simple (safe-zone) ──
capcut_style = man.get("capcut_style")  # "bounce" | "type" | "glow" | None
print(f"[4/7] Subtitles ASS (capcut={capcut_style or 'simple safe-zone'})…")
ass_path = work / "subs.ass"

def ts(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def _korean_word_split(text: str) -> list[str]:
    """Split Korean text into 2-4 char visual groups for CapCut bounce."""
    chunks = text.split()
    result = []
    for chunk in chunks:
        has_ko = bool(__import__('re').search(r'[가-힣]', chunk))
        if not has_ko or len(chunk) <= 4:
            result.append(chunk)
        else:
            i = 0
            while i < len(chunk):
                sz = min(3 + (1 if len(chunk) - i > 6 else 0), len(chunk) - i)
                result.append(chunk[i:i+sz])
                i += sz
    return result

# ── CapCut-style word-by-word animated captions ──
if capcut_style in ("bounce", "type", "glow"):
    CAP_STYLES = {
        "bounce":  {"fs": 44, "color": "&H00F0C75E", "scale_up": 130, "bounce_dur": 0.35},
        "type":    {"fs": 42, "color": "&H00F4EFE6", "scale_up": 105, "bounce_dur": 0.25},
        "glow":    {"fs": 44, "color": "&H003DB8A8", "scale_up": 115, "bounce_dur": 0.40},
    }
    cs = CAP_STYLES.get(capcut_style, CAP_STYLES["bounce"])
    cfs = cs["fs"]
    cmargin_v = max(80, int(H * 0.12))
    cheader = f"""[Script Info]
Title: {pid} CapCut
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Noto Sans CJK KR,{cfs},{cs["color"]},&H000000FF,&H001A1508,&H99000000,-1,0,0,0,100,100,0,0,1,2.5,1.5,2,60,60,{cmargin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    cevents = []
    t0 = 0.0
    for i, (s, meta) in enumerate(zip(slides, tts_meta)):
        vo_text = meta["text"].strip()
        vo_dur = max(meta["vo_dur"], 1.5)
        words = _korean_word_split(vo_text)
        if not words:
            words = [vo_text[:12]]
        total_chars = sum(len(w) for w in words)
        tw = t0
        for wi, word in enumerate(words):
            w_dur = vo_dur * len(word) / max(total_chars, 1) if total_chars > 0 else vo_dur / len(words)
            w_start = tw
            w_end = tw + w_dur + 0.03
            tw += w_dur
            settle = min(cs["bounce_dur"], w_dur * 0.55)
            peak = cs["scale_up"]
            word_esc = word.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
            anim = (
                f"{{\\fscx{peak}\\fscy{peak}}}"
                f"{word_esc}"
                f"{{\\t(0,{int(settle*1000)},\\fscx100\\fscy100)}}"
            )
            cevents.append(
                f"Dialogue: 0,{ts(w_start)},{ts(w_end)},Cap,,0,0,0,,{anim}"
            )
        t0 += clip_sec
    ass_path.write_text(cheader + "\n".join(cevents) + "\n", encoding="utf-8")

else:
    # ── Simple subtitle mode (original behavior) ──
    fs = max(28, H // 48)
    margin_v = max(48, int(H * 0.06))
    header = f"""[Script Info]
Title: {pid}
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Noto Sans CJK KR,{fs},&H00F4EFE6,&H000000FF,&H001A1508,&H99000000,-1,0,0,0,100,100,0,0,1,2,0,2,100,100,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    t0 = 0.0
    for i, (s, meta) in enumerate(zip(slides, tts_meta)):
        cap = (s.get("caption") or s.get("title") or "").strip()
        if not cap:
            raw = meta["text"].split(".")[0].strip()
            cap = (raw[:28] + "…") if len(raw) > 28 else raw
        if len(cap) > 16 and " " in cap:
            sp = cap.rfind(" ", 0, len(cap) // 2 + 4)
            if sp > 4:
                cap = cap[:sp] + "\\N" + cap[sp + 1 :]
        start = t0 + 0.25
        end = t0 + min(max(meta["vo_dur"] - 0.2, 2.0), clip_sec - 0.35)
        events.append(f"Dialogue: 0,{ts(start)},{ts(end)},Cap,,0,0,0,,{escape_ass(cap)}")
        t0 += clip_sec
    ass_path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")


# ── L5 xfade concat (video+audio) ──
print("[5/7] xfade concat…")
n = len(clips)
if n == 1:
    body = work / "body.mp4"
    run(["cp", str(clips[0]), str(body)])
    total_dur = clip_sec
else:
    # build xfade chain
    inputs = []
    for c in clips:
        inputs.extend(["-i", str(c)])
    # offset: each clip_sec - xfade
    filter_parts = []
    # video chain
    vprev = "[0:v]"
    aprev = "[0:a]"
    for i in range(1, n):
        off = i * (clip_sec - xfade)
        vout = f"[v{i}]" if i < n - 1 else "[vout]"
        aout = f"[a{i}]" if i < n - 1 else "[aout]"
        # for intermediate need unique labels
        if i < n - 1:
            vout = f"[vx{i}]"
            aout = f"[ax{i}]"
        else:
            vout = "[vout]"
            aout = "[aout]"
        filter_parts.append(
            f"{vprev}[{i}:v]xfade=transition=fade:duration={xfade}:offset={off:.3f}{vout}"
        )
        filter_parts.append(
            f"{aprev}[{i}:a]acrossfade=d={xfade}{aout}"
        )
        vprev = vout
        aprev = aout
    fc = ";".join(filter_parts)
    body = work / "body.mp4"
    run(
        [
            "ffmpeg", "-y", *inputs,
            "-filter_complex", fc + ";[vout]format=yuv420p[vfinal]",
            "-map", "[vfinal]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", preset, "-crf", crf,
            "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart",
            str(body),
        ]
    )
    total_dur = n * clip_sec - (n - 1) * xfade

print(f"  body duration≈{total_dur:.2f}s actual={ffprobe_dur(body):.2f}s")


# ── L6 burn subs + optional BGM duck ──
print("[6/7] Subs burn + BGM mix…")
final = out / f"{pid}_final.mp4"
body_sub = work / "body_sub.mp4"
if require_subs and ass_path.exists():
    # re-time ass for xfade is approximate; good enough for A-
    run(
        [
            "ffmpeg", "-y", "-i", str(body),
            # ass can up-convert chroma; force 420 after
            "-vf", f"ass={ass_path},format=yuv420p",
            "-c:v", "libx264", "-preset", preset, "-crf", crf,
            "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart",
            str(body_sub),
        ]
    )
    body_use = body_sub
else:
    body_use = body

bgm = None
for name in ("bgm.m4a", "bgm.mp3", "bgm.wav"):
    if (plugin / name).exists():
        bgm = plugin / name
        break
if not bgm and man.get("bgm"):
    p = plugin / man["bgm"]
    if p.exists():
        bgm = p

fln = (bar.get("audio") or {}).get("final_loudnorm") or "I=-15:TP=-1.3:LRA=10"
if bgm:
    print(f"  ♪ BGM {bgm.name} vol={bgm_vol}")
    # sidechain-like: low BGM weight under narration
    run(
        [
            "ffmpeg", "-y",
            "-i", str(body_use),
            "-stream_loop", "-1", "-i", str(bgm),
            "-filter_complex",
            f"[1:a]volume={bgm_vol},afade=t=in:st=0:d=1.2,"
            f"afade=t=out:st={max(1, total_dur-3):.2f}:d=2.5,"
            f"aformat=sample_rates=48000:channel_layouts=stereo[bg];"
            f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=1.12[nar];"
            f"[nar][bg]amix=inputs=2:duration=first:dropout_transition=2:weights=1 0.28,"
            f"loudnorm={fln}[a]",
            "-map", "0:v", "-map", "[a]",
            # video already yuv420p from prior stage; copy OK. audio re-encode 48k
            "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
            "-shortest",
            "-movflags", "+faststart",
            str(final),
        ]
    )
else:
    run(
        [
            "ffmpeg", "-y", "-i", str(body_use),
            "-af", f"loudnorm={fln}",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart",
            str(final),
        ]
    )

final_dur = ffprobe_dur(final)
size_mb = final.stat().st_size / 1048576
print(f"  ✅ {final}  ({size_mb:.1f}MB, {final_dur:.1f}s)")


# ── L7 quality gate ──
print("[7/7] Quality gate…")
fails = []
if any(m["provider"].startswith("edge") for m in tts_meta):
    fails.append("tts used edge fallback")
if any(m["gap"] > 1.0 for m in tts_meta):
    bad = [f"{m['id']}:{m['gap']:.1f}s" for m in tts_meta if m["gap"] > 1.0]
    fails.append(f"VO gap >1.0s (pad silence): {', '.join(bad)} — densify script or shorten clip_sec")
if require_subs and not ass_path.exists():
    fails.append("subs missing")
if W < 720 or H < 1280:
    fails.append(f"resolution too low {W}x{H}")
if final_dur < 40 or final_dur > 130:
    fails.append(f"duration odd {final_dur:.1f}s")
# Playback compatibility gate (Android/Telegram HW decoder)
try:
    rpix = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=pix_fmt,profile",
            "-of", "default=nw=1:nk=1", str(final),
        ],
        capture_output=True, text=True, check=True,
    )
    pix_lines = [x.strip() for x in (rpix.stdout or "").splitlines() if x.strip()]
    # order: pix_fmt then profile (depends on ffprobe order)
    pix_joined = " ".join(pix_lines).lower()
    if "yuv444" in pix_joined or "4:4:4" in pix_joined:
        fails.append("pix_fmt/profile not phone-playable (yuv444/High4:4:4) — force yuv420p High")
    if "yuv420p" not in pix_joined and "yuv420" not in pix_joined:
        # soft warn if unknown
        fails.append(f"unexpected pixel format: {pix_lines}")
except Exception as e:
    fails.append(f"ffprobe encode check failed: {e}")
# write report
report = {
    "id": pid,
    "standard": "video_plugin_standard_v1",
    "final": str(final),
    "duration": final_dur,
    "size_mb": round(size_mb, 2),
    "resolution": resolution,
    "voice": voice,
    "slides": [
        {"id": m["id"], "provider": m["provider"], "vo_dur": round(m["vo_dur"], 2), "gap": round(m["gap"], 2)}
        for m in tts_meta
    ],
    "gate_fails": fails,
    "grade": "FAIL" if fails else "PASS_A_BAR",
}
(out / "ship_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))

if fails:
    print("⚠ GATE WARNINGS (shipping anyway if TG on; fix scripts for true A):")
    for f in fails:
        print("  -", f)

# ── TG ──
token = os.environ.get("TG_TOKEN", "").strip().strip('"')
chat = os.environ.get("TG_CHAT", "").strip().strip('"')
if send_tg and token and chat:
    import urllib.request

    boundary = "----StdV1Boundary"
    grade = report["grade"]
    caption = (
        f"🎬 {title}\n"
        f"STANDARD v3 page-first · Grok TTS({voice}) · {resolution}\n"
        f"{final_dur:.1f}s · {size_mb:.1f}MB · gate={grade}\n"
        f"xfade={xfade}s · subs={'on' if require_subs else 'off'} · KenBurns={kenburns}\n"
        f"— produce_plugin A-bar / _Grok"
    )
    body_b = bytearray()

    def field(name, value):
        body_b.extend(f"--{boundary}\r\n".encode())
        body_b.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body_b.extend(f"{value}\r\n".encode())

    def file_field(name, path: Path, filename, ctype):
        body_b.extend(f"--{boundary}\r\n".encode())
        body_b.extend(
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
        )
        body_b.extend(f"Content-Type: {ctype}\r\n\r\n".encode())
        body_b.extend(path.read_bytes())
        body_b.extend(b"\r\n")

    field("chat_id", chat)
    field("supports_streaming", "true")
    field("caption", caption)
    file_field("video", final, final.name, "video/mp4")
    body_b.extend(f"--{boundary}--\r\n".encode())
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendVideo",
        data=bytes(body_b),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read())
    if data.get("ok"):
        print(f"  ✅ TG message_id={data['result']['message_id']}")
        report["tg_message_id"] = data["result"]["message_id"]
        (out / "ship_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    else:
        print("  ❌ TG", data)
else:
    print("  (TG skip)")

print("=== DONE ===", final)
if fails and man.get("strict_gate"):
    raise SystemExit(2)
PY
