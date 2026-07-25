# 자주 쓰는 명령어 모음

## Git (ubi shell)

```bash
# 현재 상태
git status
git log --oneline -5

# push
git push

# remote 확인
git remote -v

# remote 변경 (레포 이름 바뀌었을 때)
git remote set-url origin https://helena751107:TOKEN@github.com/helena751107/새레포명.git
```

## GitHub API

```bash
# Pages 활성화
TOKEN="ghp_..."
curl -X POST -H "Authorization: token $TOKEN" \
  https://api.github.com/repos/helena751107/helena_phone/pages \
  -d '{"source":{"branch":"main","path":"/"}}'

# 레포 정보 조회
curl -s -H "Authorization: token $TOKEN" \
  https://api.github.com/repos/helena751107/helena_phone | jq .name

# Discussions 활성화
curl -X PATCH -H "Authorization: token $TOKEN" \
  https://api.github.com/repos/helena751107/helena_phone \
  -d '{"has_discussions":true}'
```

## 디스코드 API

```bash
# 로그인
DCT=$(curl -s -X POST https://discord.com/api/v9/auth/login \
  -d '{"login":"EMAIL","password":"PASS"}' | jq -r '.token')

# 서버 생성
curl -X POST -H "Authorization: $DCT" \
  https://discord.com/api/v9/guilds -d '{"name":"S21 Phone"}'

# 위젯 켜기
curl -X PATCH -H "Authorization: $DCT" \
  https://discord.com/api/v9/guilds/ID/widget \
  -d '{"enabled":true,"channel_id":"CID"}'

# 초대링크 생성
curl -X POST -H "Authorization: $DCT" \
  https://discord.com/api/v9/channels/CID/invites \
  -d '{"max_age":0,"max_uses":0}'
```

## 텔레그램 API

```bash
# 메시지 보내기
bash ~/work/tg.sh "✅ 작업 완료"

# 또는 직접 curl
curl -s -X POST "https://api.telegram.org/bot$TG_TOKEN/sendMessage" \
  -d chat_id=$TG_CHAT -d text="메시지"

# 업데이트 확인
curl -s "https://api.telegram.org/bot$TG_TOKEN/getUpdates"
```

## 다양한 용도

```bash
# Pages 배포 확인
curl -s -o /dev/null -w "%{http_code}" https://helena751107.github.io/helena_phone/

# 전체 레포 목록
curl -s -H "Authorization: token $TOKEN" \
  https://api.github.com/users/helena751107/repos | jq -r '.[].name'
```

---

## Grok CLI (2026-07-25 추가)
```bash
gr          # grok 실행 (proot Ubuntu)
grlogin     # device-auth 로그인
grc         # 이전 세션 이어가기
agent       # 헤드리스 에이전트
```
