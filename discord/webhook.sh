#!/bin/bash
# 디스코드 웹훅 발송
# 사용법: ./webhook.sh "WEBHOOK_URL" "메시지"
curl -H "Content-Type: application/json" \
  -X POST \
  -d "{\"content\":\"$2\"}" \
  "$1"
