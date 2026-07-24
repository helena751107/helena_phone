# 텔레그램 봇/회의실

## 봇 정보

| 항목 | 값 |
|------|-----|
| 봇 이름 | S21 Phone Bot |
| 봇 유저네임 | @S21Phone_Bot |
| 봇 토큰 | `8988031320:AAH...` (.secrets.env 참조) |
| 채팅방 ID | `8579179811` |

## 보고 스크립트 (`~/work/tg.sh`)

```bash
#!/bin/bash
# 사용법: bash ~/work/tg.sh "메시지 내용"
TOKEN="${TG_TOKEN:-}"
CHAT="${TG_CHAT:-}"
curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
  -d chat_id="$CHAT" -d text="$1"
```

## 환경변수

```bash
# .secrets.env 에서 로드
source /root/work/.secrets.env
# 또는 직접 export (토큰은 .secrets.env 참조)
export TG_TOKEN="${TG_TOKEN:-}"
export TG_CHAT="${TG_CHAT:-}"
```

## 텔레그램 API 자동화 키포인트

- 봇 생성: `@BotFather` → `/newbot` (수동, 텔레그램 앱)
- 메시지 수신 확인: `GET /bot{token}/getUpdates`
- 메시지 발송: `POST /bot{token}/sendMessage`
- 봇은 먼저 말을 못 검 → 사용자가 먼저 메시지 보내야 chat_id 생성됨
