# 비밀 관리 정책

## 절대 git에 올리면 안 되는 것

| 항목 | 저장 위치 | git 추적 |
|------|-----------|----------|
| GitHub 토큰 | `.secrets.env` + remote URL에 내장 | ❌ `.gitignore` 차단 |
| Discord 계정/비번 | `.secrets.env` | ❌ `.gitignore` 차단 |
| Discord Bot 토큰 | `.secrets.env` | ❌ `.gitignore` 차단 |
| Telegram 봇 토큰 | `~/.bashrc` + `.secrets.env` | ❌ `.gitignore` 차단 |
| DeepSeek API 키 | 환경변수 (session env) | ❌ |
| Google OAuth 정보 | `.secrets.env` (예정) | ❌ |

## `.gitignore` 설정

```
.aider*
.secrets.env
.env
bot_token.txt
```

## 주의사항

- `.secrets.env`는 `source .secrets.env`로 로드 가능 (export 포함)
- 환경변수는 세션 지속성 없음 → `.bashrc`에 `export` 저장
- 각종 토큰이 대화 내역에 평문 노출될 수 있음 → 대화 종료 후 재발급 권장
- GitHub remote URL에 토큰이 포함되어 있음 (`https://USER:TOKEN@github.com/...`)
- 스크린샷/화면 공유 시 토큰 노출 주의
- **비밀 파일이 commit에 포함되지 않도록 항상 `git status`로 확인**
- GitHub Push Protection이 자동 감지함 (위반 시 push 거절)

## 토큰 재발급이 필요한 상황

- 대화 종료 후
- 토큰이 스크린샷/로그에 노출되었을 때
- 의심스러운 활동 감지 시

## 안전한 작업 순서

1. 작업 전 토큰은 `.secrets.env`에만 보관
2. 소스 코드에는 `"TOKEN", "API_KEY"` 같은 placeholder 사용
3. 실행 시 `source .secrets.env` 로 환경변수 로드
4. `git push` 전 반드시 `git status`로 시크릿 유출 확인
