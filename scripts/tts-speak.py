#!/usr/bin/env python3
"""
Helena TTS — 텍스트를 음성으로 읽어주는 온디맨드 엔진

사용법:
  echo "안녕하세요" | python3 tts-speak.py
  python3 tts-speak.py "보고서 전문..."
  python3 tts-speak.py --voice ko-KR-SunHiNeural --file report.txt
  python3 tts-speak.py --list-voices  # 사용 가능한 한국어 음성 목록

특징:
  - Microsoft Edge TTS (무료, 브라우저 불필요, HTTP API)
  - 필요할 때만 실행 → 종료 (램 상주 없음)
  - 한국어 다중 음성 지원
  - termux-tts-speak 폴백 (안드로이드 기본 TTS)

필요:
  pip install edge-tts
  apt install ffmpeg (ffplay 재생용)
"""

import sys
import os
import subprocess
import tempfile
import argparse
import asyncio

# ── 설정 ───────────────────────────────────────────
DEFAULT_VOICE = "ko-KR-SunHiNeural"   # 한국어 여성, 밝은 톤
FALLBACK_VOICE = "ko-KR-InJoonNeural" # 한국어 남성
PLAYER = "ffplay"                      # 또는 termux-media-player

# ── Edge TTS ───────────────────────────────────────
async def edge_speak(text: str, voice: str, output_path: str) -> bool:
    """Edge TTS로 텍스트 → 음성 파일 생성"""
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"[edge-tts] 실패: {e}", file=sys.stderr)
        return False


# ── 안드로이드 기본 TTS 폴백 ─────────────────────────
def termux_speak(text: str) -> bool:
    """Termux TTS API 호출 (오프라인, 무료, 항상 가능)"""
    tts_bin = "/data/data/com.termux/files/usr/bin/termux-tts-speak"
    if not os.path.exists(tts_bin):
        return False
    try:
        subprocess.run([tts_bin, text], timeout=30, capture_output=True)
        return True
    except Exception as e:
        print(f"[termux-tts] 실패: {e}", file=sys.stderr)
        return False


# ── 재생 ──────────────────────────────────────────
def play_audio(filepath: str) -> bool:
    """오디오 파일 재생"""
    # ffplay (FFmpeg 내장) — 가장 가볍고 의존성 없음
    try:
        subprocess.run(
            [PLAYER, "-nodisp", "-autoexit", "-loglevel", "quiet", filepath],
            timeout=120, capture_output=True
        )
        return True
    except Exception:
        pass

    # termux-media-player 폴백
    try:
        subprocess.run(
            ["termux-media-player", "play", "-t", "audio", filepath],
            timeout=120, capture_output=True
        )
        return True
    except Exception:
        pass

    print("[play] 재생 실패 — ffplay나 termux-media-player 필요", file=sys.stderr)
    return False


# ── 음성 목록 ──────────────────────────────────────
async def list_voices():
    """사용 가능한 한국어 음성 출력"""
    try:
        import edge_tts
        voices = await edge_tts.list_voices()
        for v in voices:
            if "ko-KR" in v["ShortName"] or "korean" in v["Locale"].lower():
                name = v["ShortName"]
                gender = v.get("Gender", "?")
                locale = v.get("Locale", "?")
                print(f"  {name:<35} {gender:<8} {locale}")
    except Exception as e:
        print(f"음성 목록 조회 실패: {e}")
        print("온라인 상태에서 다시 시도하세요.")


# ── 메인 ──────────────────────────────────────────
async def main():
    parser = argparse.ArgumentParser(description="Helena TTS — 텍스트→음성 온디맨드")
    parser.add_argument("text", nargs="*", help="읽을 텍스트 (생략 시 stdin)")
    parser.add_argument("--voice", "-v", default=DEFAULT_VOICE, help=f"음성 선택 (기본: {DEFAULT_VOICE})")
    parser.add_argument("--file", "-f", help="파일에서 읽기")
    parser.add_argument("--list-voices", "-l", action="store_true", help="한국어 음성 목록")
    parser.add_argument("--native", "-n", action="store_true", help="안드로이드 기본 TTS 사용 (오프라인)")
    parser.add_argument("--output", "-o", help="MP3 파일로 저장만 하고 재생 안 함")
    args = parser.parse_args()

    # 음성 목록
    if args.list_voices:
        await list_voices()
        return

    # 텍스트 수집
    text = ""
    if args.file:
        with open(args.file) as f:
            text = f.read()
    elif args.text:
        text = " ".join(args.text)
    else:
        text = sys.stdin.read()

    text = text.strip()
    if not text:
        print("❌ 읽을 텍스트가 없습니다.")
        print("   echo '안녕하세요' | python3 tts-speak.py")
        sys.exit(1)

    print(f"🔊 읽는 중... ({len(text)}자)")

    # 안드로이드 기본 TTS (오프라인, 경량)
    if args.native:
        if termux_speak(text):
            print("✅ 완료 (안드로이드 TTS)")
            return
        print("⚠️ 안드로이드 TTS 실패 → Edge TTS로 시도")

    # Edge TTS → MP3 → 재생
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        ok = await edge_speak(text, args.voice, tmp_path)
        if not ok:
            # 폴백 음성으로 재시도
            if args.voice != FALLBACK_VOICE:
                print(f"⚠️ {args.voice} 실패 → {FALLBACK_VOICE}로 재시도")
                ok = await edge_speak(text, FALLBACK_VOICE, tmp_path)

        if not ok:
            # 안드로이드 TTS 최후 폴백
            print("⚠️ Edge TTS 실패 → 안드로이드 TTS")
            if termux_speak(text):
                print("✅ 완료 (안드로이드 TTS 폴백)")
                return
            print("❌ 모든 TTS 실패")
            sys.exit(1)

        # 저장만
        if args.output:
            os.rename(tmp_path, args.output)
            print(f"✅ 저장: {args.output}")
            return

        # 재생
        if play_audio(tmp_path):
            print("✅ 완료")
        else:
            # 재생 실패해도 파일은 있음
            print(f"⚠️ 재생 실패 — 파일: {tmp_path}")

    finally:
        if not args.output and os.path.exists(tmp_path):
            os.unlink(tmp_path)


if __name__ == "__main__":
    asyncio.run(main())
