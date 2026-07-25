# 디스코드 서버/봇/위젯

## 서버 정보

| 항목 | 값 |
|------|-----|
| 서버명 | S21 Phone |
| 서버 ID | `REDACTED` |
| 개설일 | 2026-07-23 |
| 소유자 | helena19751107 (ID: 1529766339441328178) |

## 채널 목록

| ID | 이름 | 용도 |
|----|------|------|
| `REDACTED` | #로비 | 일반 채팅 |
| `REDACTED` | #ai-보고 | AI 웹훅 보고 |

## 초대링크

```
https://discord.gg/JTYSZv2WQE
```

## 위젯 활성화 (API)

```bash
curl -s -X PATCH "https://discord.com/api/v9/guilds/REDACTED/widget" \
  -H "Content-Type: application/json" \
  -H "Authorization: $DCT" \
  -d '{"enabled":true,"channel_id":"REDACTED"}'
```

## WidgetBot (랜딩 페이지 임베드)

```html
<script src="https://cdn.jsdelivr.net/npm/@widgetbot/crate@3" async defer>
  new Crate({
    server: 'REDACTED',
    channel: 'REDACTED',
    shard: 'https://disweb.defla.dev'
  })
</script>
```

## 디스코드 API 자동화 키포인트

- 로그인: `POST /api/v9/auth/login` → user token
- 서버 생성: `POST /api/v9/guilds` → `{"name":"..."}`
- 채널 생성: `POST /api/v9/guilds/{id}/channels`
- 위젯: `PATCH /api/v9/guilds/{id}/widget`
- 앱(봇) 생성: `POST /api/v9/applications` → hCaptcha 필요 (수동)
- 초대링크: `POST /api/v9/channels/{id}/invites`

---

## 현재 상태 (2026-07-25)
- 서버: S21 Phone ✅
- 채널: #로비 (공개) + #ai-보고 (웹훅)
- WidgetBot: GitHub Pages에 임베드
- 웹훅 알림: dc.sh (예정)
