#!/usr/bin/env python3
"""
Grok / xAI Text-to-Speech — 성우 엔진 (edge 아님)

API: POST https://api.x.ai/v1/tts
Auth: XAI_API_KEY 또는 ~/.grok/auth.json 세션 JWT

Usage:
  python3 scripts/grok_tts.py --text "안녕하세요" --out /tmp/a.mp3
  python3 scripts/grok_tts.py --file line.txt --out line.mp3 --voice ara --lang ko
  python3 scripts/grok_tts.py --list-voices
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API_TTS = "https://api.x.ai/v1/tts"
API_VOICES = "https://api.x.ai/v1/tts/voices"
DEFAULT_VOICE = os.environ.get("GROK_TTS_VOICE", "ara")  # warm, narration-friendly
DEFAULT_LANG = os.environ.get("GROK_TTS_LANG", "ko")


def resolve_token() -> str:
    env = os.environ.get("XAI_API_KEY") or os.environ.get("GROK_CODE_XAI_API_KEY")
    if env:
        return env.strip()
    auth_path = Path(os.environ.get("GROK_AUTH_JSON", Path.home() / ".grok" / "auth.json"))
    if not auth_path.exists():
        raise RuntimeError(
            "No XAI_API_KEY and no ~/.grok/auth.json — grok login 또는 API 키 필요"
        )
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


def list_voices(token: str) -> list[dict]:
    req = urllib.request.Request(
        API_VOICES, headers={"Authorization": f"Bearer {token}"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read())
    return list(payload.get("voices") or [])


def synthesize(
    text: str,
    dest: Path,
    *,
    voice_id: str = DEFAULT_VOICE,
    language: str = DEFAULT_LANG,
    speed: float = 1.0,
    retries: int = 4,
) -> float:
    """Write MP3 to dest. Returns duration seconds (ffprobe if available, else 0)."""
    text = (text or "").strip()
    if not text:
        raise ValueError("empty text")
    token = resolve_token()
    body = json.dumps(
        {
            "text": text,
            "voice_id": voice_id,
            "language": language,
            "speed": speed,
            "output_format": {
                "codec": "mp3",
                "sample_rate": 44100,
                "bit_rate": 192000,
            },
        }
    ).encode("utf-8")
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(
            API_TTS,
            data=body,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                audio = resp.read()
            if len(audio) < 200:
                raise RuntimeError(f"TTS too small: {len(audio)} bytes")
            dest.write_bytes(audio)
            return _ffprobe_duration(dest)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")[:300]
            last_err = RuntimeError(f"HTTP {e.code}: {err_body}")
            if e.code in (429, 500, 503):
                time.sleep(min(12, 2**attempt))
                continue
            raise last_err from e
        except Exception as e:
            last_err = e
            time.sleep(min(8, attempt * 2))
    raise RuntimeError(f"grok tts failed: {last_err}")


def _ffprobe_duration(path: Path) -> float:
    import subprocess

    try:
        r = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=nw=1:nk=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return float(r.stdout.strip() or "0")
    except Exception:
        return 0.0


def main() -> int:
    ap = argparse.ArgumentParser(description="Grok xAI TTS")
    ap.add_argument("--text", help="Text to speak")
    ap.add_argument("--file", help="UTF-8 text file")
    ap.add_argument("--out", help="Output mp3 path")
    ap.add_argument("--voice", default=DEFAULT_VOICE)
    ap.add_argument("--lang", default=DEFAULT_LANG)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--list-voices", action="store_true")
    args = ap.parse_args()

    if args.list_voices:
        for v in list_voices(resolve_token()):
            print(f"{v.get('voice_id', '?'):12}  {v.get('name', '')}  {v.get('language', '')}")
        return 0

    if not args.out:
        print("--out required", file=sys.stderr)
        return 2
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    elif args.text:
        text = args.text
    else:
        print("--text or --file required", file=sys.stderr)
        return 2

    dur = synthesize(text, Path(args.out), voice_id=args.voice, language=args.lang, speed=args.speed)
    print(f"OK {args.out}  voice={args.voice}  lang={args.lang}  dur={dur:.2f}s  bytes={Path(args.out).stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
