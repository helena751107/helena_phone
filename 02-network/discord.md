# 2.2 Discord 서버 구축

> 실시간 채팅방 + AI 보고 채널

## 서버 생성

```bash
# Discord API 로그인
DCT=$(curl -s -X POST https://discord.com/api/v9/auth/login \
  -d '{"login":"이메일","password":"비번"}' | jq -r '.token')

# 서버 생성
curl -X POST -H "Authorization: $DCT" \
  https://discord.com/api/v9/guilds \
  -d '{"name":"S21 Phone"}'

# 채널 생성
curl -X POST -H "Authorization: $DCT" \
  https://discord.com/api/v9/guilds/서버ID/channels \
  -d '{"name":"로비","type":0}'
```

## 위젯 활성화

```bash
curl -X PATCH -H "Authorization: $DCT" \
  https://discord.com/api/v9/guilds/서버ID/widget \
  -d '{"enabled":true,"channel_id":"채널ID"}'
```

## WidgetBot 웹 임베드

```html
<script src="https://cdn.jsdelivr.net/npm/@widgetbot/crate@3" async defer>
  new Crate({
    server: '서버ID',
    channel: '채널ID',
    shard: 'https://disweb.defla.dev'
  })
</script>
```

이 스크립트를 `index.html`에 넣으면 웹사이트 우하단에 채팅 버튼이 생긴다.

## 권장 채널 구성

| 채널명 | 용도 |
|--------|------|
| #로비 | 일반 채팅/질문 |
| #ai-보고 | AI 에이전트 작업 보고 |
