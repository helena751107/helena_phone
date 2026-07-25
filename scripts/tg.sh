#!/bin/bash
# Telegram 보고 스크립트
# 사용법: bash ~/work/tg.sh "메시지 내용"
# 환경변수: TG_TOKEN, TG_CHAT

TOKEN="${TG_TOKEN:-}"
CHAT="${TG_CHAT:-}"

if [ -z "$TOKEN" ] || [ -z "$CHAT" ]; then
  echo "❌ TG_TOKEN 또는 TG_CHAT 환경변수가 설정되지 않았습니다." >&2
  exit 1
fi

MESSAGE="$*"
if [ -z "$MESSAGE" ]; then
  echo "❌ 메시지를 입력하세요. 사용법: bash ~/work/tg.sh '메시지'" >&2
  exit 1
fi

# API 호출
RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
  -d chat_id="$CHAT" \
  -d text="$MESSAGE" \
  -d parse_mode="HTML" \
  -w "\n%{http_code}")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ 텔레그램 전송 성공"
else
  echo "❌ 텔레그램 전송 실패 (HTTP $HTTP_CODE)"
  echo "$BODY"
  exit 1
fi
