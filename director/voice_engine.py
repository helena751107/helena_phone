#!/usr/bin/env python3
"""
Voice Engine — 성우 플러그인 (swappable TTS backends)

Priority chain:
  1) Grok / xAI TTS (ara/altair/…) — SuperGrok 성우 본체 · 라이선스 🟢
  2) OpenAI tts-1-hd — 보조 (OPENAI_API_KEY 있을 때)
  3) edge-tts + broadcast humanize — 공짜 폴백 (비상업 전용 · 상업/홍보 금지)

Usage:
  from director.voice_engine import synthesize, VoiceEngine
  dur, provider = synthesize("안녕하세요", Path("/tmp/out.mp3"))
  dur, provider = synthesize("안녕하세요", Path("/tmp/out.mp3"), engine="grok")

Env:
  TTS_ENGINE=grok|openai|edge  (기본: grok)
  GROK_TTS_VOICE=ara
  XAI_API_KEY=…  or  ~/.grok/auth.json
  OPENAI_API_KEY=…

라이선스 가이드 (Boss 2026-08-06):
  - Grok (Ara 등): 유료 구독 → 상업 이용 🟢 · 유튜브 수익화 가능 · AI 라벨 체크
  - Edge TTS: 개인·내부 시연만 🟡 · 수익화/홍보/브랜드 = 약관 위반 + 채널 스트라이크 위험
  - 비수익화라도 Edge는 저작권 경고 가능 → Grok 권장
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import json
from pathlib import Path

# ── engine registry ──
ENGINE_PRIORITY = ["grok", "openai", "edge"]
VOICE_DEFAULT = "ko-KR-SunHiNeural"
GROK_VOICE_DEFAULT = os.environ.get("GROK_TTS_VOICE", "ara")
OPENAI_VOICE_DEFAULT = "nova"

# ── loudnorm / broadcast humanize chain ──
# Grok TTS already broadcast-grade → light polish only
# Edge TTS → heavier humanize to reduce machine-detectable patterns
HUMANIZE_LIGHT = (
    "highpass=f=80,"
    "acompressor=threshold=-22dB:ratio=2.5:attack=8:release=60:makeup=1.5,"
    "loudnorm=I=-16:TP=-1.5:LRA=11"
)
HUMANIZE_HEAVY = (
    "highpass=f=90,"
    "equalizer=f=2800:t=q:w=1.1:g=2.4,"
    "equalizer=f=6500:t=q:w=1.0:g=1.6,"
    "acompressor=threshold=-20dB:ratio=3.5:attack=5:release=70:makeup=2.2,"
    "loudnorm=I=-16:TP=-1.5:LRA=11"
)


def ffprobe_duration(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float((r.stdout or "0").strip() or "0")
    except ValueError:
        return 0.0


def _resolve_grok_token() -> str:
    env = os.environ.get("XAI_API_KEY") or os.environ.get("GROK_CODE_XAI_API_KEY")
    if env:
        return env.strip()
    auth_path = Path(os.environ.get("GROK_AUTH_JSON", Path.home() / ".grok" / "auth.json"))
    if not auth_path.exists():
        raise RuntimeError("No XAI_API_KEY and no ~/.grok/auth.json — grok login 또는 API 키 필요")
    data = json.loads(auth_path.read_text())
    if not isinstance(data, dict) or not data:
        raise RuntimeError(f"empty auth: {auth_path}")
    entry = next(iter(data.values()))
    if not isinstance(entry, dict):
        raise RuntimeError("auth entry shape unexpected")
    token = entry.get("key") or entry.get("access_token")
    if not token:
        raise RuntimeError("auth has no key/access_token")
    return str(token)


# ── individual engine implementations ──

def _tts_grok(text: str, dest: Path, voice: str = GROK_VOICE_DEFAULT,
              lang: str = "ko", speed: float = 0.95, retries: int = 4) -> float:
    """xAI TTS API — SuperGrok 구독 성우 본체."""
    token = _resolve_grok_token()
    body = json.dumps({
        "text": text,
        "voice_id": voice,
        "language": lang,
        "speed": speed,
        "output_format": {"codec": "mp3", "sample_rate": 44100, "bit_rate": 192000},
    }).encode("utf-8")
    dest.parent.mkdir(parents=True, exist_ok=True)
    last_err = None
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(
            "https://api.x.ai/v1/tts",
            data=body,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                audio = resp.read()
            if len(audio) < 200:
                raise RuntimeError(f"TTS too small: {len(audio)} bytes")
            dest.write_bytes(audio)
            return ffprobe_duration(dest)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")[:300]
            last_err = RuntimeError(f"HTTP {e.code}: {err_body}")
            if e.code in (429, 500, 503, 502):
                time.sleep(min(12, 2 ** attempt))
                continue
            raise last_err from e
        except Exception as e:
            last_err = e
            time.sleep(min(8, attempt * 2))
    raise RuntimeError(f"grok tts failed after {retries} retries: {last_err}")


def _tts_openai(text: str, dest: Path, voice: str = OPENAI_VOICE_DEFAULT,
                model: str = "tts-1-hd", speed: float = 0.95) -> float:
    """OpenAI Audio Speech API."""
    key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")
    if not key:
        raise RuntimeError("no OPENAI_API_KEY")
    dest.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({
        "model": model, "voice": voice, "input": text,
        "response_format": "mp3", "speed": speed,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/speech",
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        dest.write_bytes(resp.read())
    if dest.stat().st_size < 200:
        raise RuntimeError("openai tts empty")
    return ffprobe_duration(dest)


def _tts_edge(text: str, dest: Path, voice: str = VOICE_DEFAULT,
              rate: str = "-8%", retries: int = 4) -> float:
    """Edge TTS — 공짜 폴백. 비상업 용도 전용."""
    import asyncio
    import edge_tts

    dest.parent.mkdir(parents=True, exist_ok=True)
    async def _run():
        last_err = None
        for attempt in range(1, retries + 1):
            try:
                if dest.exists():
                    dest.unlink()
                communicate = edge_tts.Communicate(text, voice, rate=rate)
                await communicate.save(str(dest))
                if dest.stat().st_size < 100:
                    raise RuntimeError(f"TTS empty: {dest}")
                return ffprobe_duration(dest)
            except Exception as e:
                last_err = e
                await asyncio.sleep(min(8, attempt * 2))
        raise RuntimeError(f"edge-tts failed: {last_err}")
    return asyncio.run(_run())


# ── post-processing ──

def _polish(raw: Path, polished: Path, engine: str) -> Path:
    """Apply broadcast humanize chain, varying by engine quality."""
    chain = HUMANIZE_LIGHT if engine == "grok" else HUMANIZE_HEAVY
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", str(raw), "-af", chain,
         "-ar", "48000", "-ac", "2", "-c:a", "aac", "-b:a", "192k", str(polished)],
        capture_output=True, text=True,
    )
    if r.returncode != 0 or not polished.exists() or polished.stat().st_size < 200:
        shutil.copy(raw, polished)
    return polished


# ── main public API ──

def synthesize(
    text: str,
    dest: Path,
    *,
    engine: str = "auto",
    voice: str | None = None,
    lang: str = "ko",
    speed: float = 0.95,
    polish: bool = True,
) -> tuple[float, str]:
    """
    Synthesize voice from text.

    Args:
        text: Korean narration text
        dest: output path (.mp3 or .m4a)
        engine: "auto" (priority chain) | "grok" | "openai" | "edge"
        voice: override voice ID
        lang: language code
        speed: speech speed multiplier
        polish: apply broadcast humanize chain

    Returns:
        (duration_seconds, provider_tag) — e.g. (12.34, "grok/ara")

    Provider tags:
        grok/ara      — 🟢 상업 가능 · 정식 경로
        openai/nova   — 🟢 상업 가능 · API 키 필요
        edge/SunHi    — 🟡 비상업 전용 · 수익화 금지 (폴백)
    """
    text = (text or "").strip()
    if not text:
        raise ValueError("empty text")

    # Resolve engine
    if engine == "auto":
        env_engine = os.environ.get("TTS_ENGINE", "").strip()
        if env_engine and env_engine != "auto":
            order = [env_engine]
        else:
            order = list(ENGINE_PRIORITY)
    else:
        order = [engine]

    raw = dest.parent / f"._{dest.name}.raw.mp3"
    polished = dest

    last_err = None
    for provider in order:
        try:
            if provider == "grok":
                v = voice or GROK_VOICE_DEFAULT
                dur = _tts_grok(text, raw, voice=v, lang=lang, speed=speed)
                if polish:
                    _polish(raw, polished, "grok")
                    dur = ffprobe_duration(polished)
                else:
                    shutil.move(str(raw), str(polished))
                return dur, f"grok/{v}"

            elif provider == "openai":
                if not (os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")):
                    print("  ! openai skip — no API key", flush=True)
                    continue
                v = voice or OPENAI_VOICE_DEFAULT
                dur = _tts_openai(text, raw, voice=v, speed=speed)
                if polish:
                    _polish(raw, polished, "openai")
                    dur = ffprobe_duration(polished)
                else:
                    shutil.move(str(raw), str(polished))
                return dur, f"openai/{v}"

            elif provider == "edge":
                v = voice or VOICE_DEFAULT
                dur = _tts_edge(text, raw, voice=v)
                if polish:
                    _polish(raw, polished, "edge")
                    dur = ffprobe_duration(polished)
                else:
                    shutil.move(str(raw), str(polished))
                return dur, f"edge/{v}"

        except Exception as e:
            last_err = e
            print(f"  ⚠ tts/{provider} failed: {e}", flush=True)
            # cleanup raw
            if raw.exists():
                raw.unlink(missing_ok=True)
            continue

    raise RuntimeError(f"All TTS providers failed. Last error: {last_err}")


def list_voices_grok() -> list[dict]:
    """List available Grok/xAI TTS voices."""
    token = _resolve_grok_token()
    req = urllib.request.Request(
        "https://api.x.ai/v1/tts/voices",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read())
    return list(payload.get("voices") or [])


# ── CLI ──
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Voice Engine — 성우 플러그인")
    ap.add_argument("--text", help="Text to speak")
    ap.add_argument("--file", help="UTF-8 text file")
    ap.add_argument("--out", required=True, help="Output path (.mp3/.m4a)")
    ap.add_argument("--engine", default="auto", choices=["auto", "grok", "openai", "edge"])
    ap.add_argument("--voice", help="Voice ID override")
    ap.add_argument("--lang", default="ko")
    ap.add_argument("--speed", type=float, default=0.95)
    ap.add_argument("--no-polish", action="store_true")
    ap.add_argument("--list-voices", action="store_true")
    args = ap.parse_args()

    if args.list_voices:
        for v in list_voices_grok():
            print(f"  {v.get('voice_id', '?'):14} {v.get('name', ''):20} {v.get('language', '')}")
        sys.exit(0)

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    elif args.text:
        text = args.text
    else:
        print("--text or --file required", file=sys.stderr)
        sys.exit(2)

    dur, provider = synthesize(
        text, Path(args.out), engine=args.engine,
        voice=args.voice, lang=args.lang, speed=args.speed,
        polish=not args.no_polish,
    )
    size_kb = Path(args.out).stat().st_size // 1024
    print(f"✅ {provider:20s} dur={dur:.2f}s  size={size_kb}KB  → {args.out}")
