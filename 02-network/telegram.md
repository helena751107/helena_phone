# 2.3 Telegram 봇 구축

> AI 작업 완료 알림 + 자동 보고 시스템

## 봇 생성

1. 텔레그램 앱에서 `@BotFather` 검색
2. `/newbot` 입력
3. 봇 이름 입력 (예: S21 Phone Bot)
4. 봇 username 입력 (예: `@S21Phone_Bot`)
5. 발급된 **토큰** 저장 (예: `8988031320:AAH...`)

## 환경변수 설정

`.secrets.env`에 저장 (절대 git에 올리지 말 것):

```bash
TG_TOKEN="8988031320:AAH_여기에_토큰"
TG_CHAT="8579179811"  # 봇이 메시지 보낼 방 ID
```

## 텔레그램 보고 스크립트 (`tg.sh`)

```bash
#!/bin/bash
TOKEN="${TG_TOKEN:-}"
CHAT="${TG_CHAT:-}"
curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
  -d chat_id="$CHAT" -d text="$1"
```

사용법:
```bash
bash tg.sh "✅ 작업 완료 — 배터리 68% / 플래시 테스트 통과"
```

## chat_id 찾는 방법

봇은 "먼저 말을 걸지 못함" — 사용자가 먼저 메시지를 보내야 chat_id가 생성됨:

```bash
# 봇한테 아무 메시지나 보낸 후
curl -s "https://api.telegram.org/bot$TG_TOKEN/getUpdates"
# → response에서 chat.id 값 확인
```

## 응용: AI가 자기 일을 스스로 보고하게

`CLAUDE.md`에 규칙을 추가:

```markdown
## 텔레그램 보고 의무
작업 완료 후 보고가 필요하면:
bash ~/work/tg.sh '✅ 작업명 — 결과'
```

이러면 AI 에이전트가 작업 끝나고 스스로 텔레그램에 보고한다.
