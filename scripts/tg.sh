#!/bin/bash
# Telegram 보고 스크립트 (+ 음성 읽기)
# 사용법:
#   bash tg.sh "메시지"              # 텍스트만
#   bash tg.sh --voice "메시지"      # 텍스트 + 음성 읽기
#   bash tg.sh --speak "메시지"      # 음성만
# 환경변수: TG_TOKEN, TG_CHAT

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TTS_SCRIPT="$SCRIPT_DIR/tts-speak.py"

TOKEN="${TG_TOKEN:-}"
CHAT="${TG_CHAT:-}"

if [ -z "$TOKEN" ] || [ -z "$CHAT" ]; then
  echo "❌ TG_TOKEN 또는 TG_CHAT 환경변수가 설정되지 않았습니다." >&2
  exit 1
fi

MODE="text"
if [ "$1" = "--voice" ] || [ "$1" = "-v" ]; then
  MODE="both"
  shift
elif [ "$1" = "--speak" ] || [ "$1" = "-s" ]; then
  MODE="voice"
  shift
fi

MESSAGE="$*"
if [ -z "$MESSAGE" ]; then
  echo "❌ 메시지를 입력하세요. 사용법: bash tg.sh [--voice] '메시지'" >&2
  exit 1
fi

# ── 텍스트 전송 ──────────────────────────────────
if [ "$MODE" = "text" ] || [ "$MODE" = "both" ]; then
  RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
    -d chat_id="$CHAT" \
    -d text="$MESSAGE" \
    -d parse_mode="HTML" \
    -w "\n%{http_code}")

  HTTP_CODE=$(echo "$RESPONSE" | tail -1)
  BODY=$(echo "$RESPONSE" | sed '$d')

  if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ 텍스트 전송 성공"
  else
    echo "❌ 실패 (HTTP $HTTP_CODE)"
    echo "$BODY"
    exit 1
  fi
fi

# ── 음성 전송 ────────────────────────────────────
if [ "$MODE" = "voice" ] || [ "$MODE" = "both" ]; then
  if [ -f "$TTS_SCRIPT" ]; then
    # HTML 태그 제거한 순수 텍스트로 TTS
    CLEAN=$(echo "$MESSAGE" | sed 's/<[^>]*>//g')
    TTS_MP3=$(python3 "$TTS_SCRIPT" --output /tmp/tg_voice_$$.mp3 "$CLEAN" 2>&1 | grep "✅ 저장:" | awk '{print $NF}' || echo "/tmp/tg_voice_$$.mp3")
    MP3_FILE="/tmp/tg_voice_$$.mp3"

    if [ -f "$MP3_FILE" ] && [ -s "$MP3_FILE" ]; then
      curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendVoice" \
        -F "chat_id=$CHAT" \
        -F "voice=@$MP3_FILE" \
        -F "caption=🔊 음성 읽기" > /dev/null
      rm -f "$MP3_FILE"
      echo "✅ 음성 전송 성공"
    else
      echo "⚠️ TTS 변환 실패 — 텍스트만 전송됨"
    fi
  else
    echo "⚠️ tts-speak.py 없음 — pip install edge-tts 필요"
  fi
fi
