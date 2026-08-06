#!/usr/bin/env python3
"""ParkSyTTS v1 — 박씨 목소리로 말하기.

사용법:
    python3 say.py "안녕 헬레나!"
    python3 say.py "안녕하세요" --out hello.wav
    python3 say.py "빠르게 읽어줘" --speed 1.3
    echo "파일로 읽기" | python3 say.py --out output.wav
    python3 say.py --file script.txt --out narration.wav
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))


def play(wav_path: Path) -> None:
    for cmd in (["ffplay", "-nodisp", "-autoexit", str(wav_path)],
                ["aplay", str(wav_path)]):
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    print(f"재생 불가 — 파일 위치: {wav_path}", file=sys.stderr)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="ParkSyTTS v1 — 박씨 목소리 합성기",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""예시:
  python3 say.py "안녕 헬레나!"
  python3 say.py "텍스트" --out 파일.wav --speed 1.2
  python3 say.py --file 대본.txt --out 나레이션.wav""",
    )
    ap.add_argument("text", nargs="?", help="합성할 텍스트 (또는 --file / stdin)")
    ap.add_argument("--file", "-f", help="텍스트 파일 경로")
    ap.add_argument("--out", "-o", default="/tmp/parksy_say.wav",
                    help="출력 WAV 경로 (기본: /tmp/parksy_say.wav)")
    ap.add_argument("--speed", "-s", type=float, default=1.0,
                    help="속도 (1.0=기본, 1.2=빠름, 0.9=느림)")
    ap.add_argument("--lang", default="ko", help="언어 코드 (기본: ko)")
    ap.add_argument("--play", "-p", action="store_true", help="합성 후 바로 재생")
    ap.add_argument("--model-dir", help="모델 디렉토리 (기본: ~/parksy-tts-v1/models)")
    ap.add_argument("--gptsovits-dir", help="GPT-SoVITS 경로 (기본: ~/GPT-SoVITS)")
    args = ap.parse_args()

    if args.text:
        text = args.text
    elif args.file:
        text = Path(args.file).read_text(encoding="utf-8").strip()
    elif not sys.stdin.isatty():
        text = sys.stdin.read().strip()
    else:
        ap.error("텍스트를 입력하세요. 예: python3 say.py '안녕하세요'")

    if not text:
        ap.error("텍스트가 비어있습니다.")

    model_dir = Path(args.model_dir) if args.model_dir else None
    gptsovits_dir = Path(args.gptsovits_dir) if args.gptsovits_dir else None

    print("모델 로드 중...", flush=True)
    from core import ParkSyTTS
    tts = ParkSyTTS(model_dir=model_dir, gptsovits_dir=gptsovits_dir)

    print(f"합성 중: {text[:60]}{'...' if len(text)>60 else ''}", flush=True)
    import time
    t0 = time.time()
    out = tts.say(text, args.out, lang=args.lang, speed=args.speed)
    elapsed = time.time() - t0

    import soundfile as sf
    import numpy as np
    data, sr = sf.read(str(out))
    dur = len(data) / sr
    peak = float(np.max(np.abs(data)))

    print(f"완료: {out}")
    print(f"길이: {dur:.1f}s  |  추론: {elapsed:.0f}s  |  peak: {peak:.3f}")

    if args.play:
        play(out)


if __name__ == "__main__":
    main()
