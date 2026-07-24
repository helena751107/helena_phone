# 🎁 헬레나 선물 패키지 — 완전 명세

> **브랜치:** `gift/helena` (dtslib-papyrus)
> **SSOT:** 이 브랜치가 유일한 원본. 각 레포 배포는 여기서만 진행.

---

## 📋 5개 레포 맞춤 구성표

```
helena_phone (메인)         helana_log          helana-faith
├─ 1-phone-claude            ├─ 2-github-actions  ├─ 3-discord
├─ 2-github-actions          ├─ 4-telegram        ├─ 2-github-actions
├─ 3-discord                 └─ config             └─ config
├─ 4-telegram
├─ 5-youtube-google
├─ 6-tistory-naver
├─ 7-mcp
└─ config

helena-piano                helena-metalcare
├─ 5-youtube-google         ├─ 3-discord
├─ 1-phone-claude (MIDI)    ├─ 4-telegram
└─ config                   ├─ 2-github-actions
                             └─ config
```

---

## 📦 패키지 상세

### 1️⃣ phone-claude — 📱 갤럭시 AI 서버
**설치:** `bash INSTALL.sh` (Termux → Ubuntu → Claude Code 자동 설치)
**구성:** STT → Claude Code → Git → GitHub Pages
**파일:** INSTALL.sh | startup.sh | healthcheck.py | deepseek.py | tts-bridge.sh

### 2️⃣ github-actions — ⚙️ CI/CD 워크플로우 6종
| 파일 | 용도 |
|------|------|
| rule-tuner.yml | 규칙 튜너 |
| design-library-guard.yml | 디자인 가드 |
| issue-terminal.yml | 이슈 터미널 |
| acceptance-tests.yml | 수락 테스트 |
| router-compiler.yml | 라우터 컴파일러 |
| feedback-collector.yml | 피드백 수집 |

**배포:** 각 레포 `.github/workflows/` 에 복사

### 3️⃣ discord — 💬 웹훅 알림
**파일:** webhook.sh | discord-notify.yml | DISCORD_SETUP.md
**연동:** GitHub Actions push → Discord 채널 알림
**설정:** Discord 서버 → 웹훅 생성 → GitHub Secrets 등록

### 4️⃣ telegram — ✈️ 봇/브릿지 5종
**파일:** telegram-bridge.py | telegram-bot.py | core.py | TG_SETUP.md
**구성:** BotFather 토큰 → polling daemon → Claude Code 연동
**아키텍처:** TG 메시지 → tmux send-keys → Claude/DeepSeek 세션

### 5️⃣ youtube-google — 🎬 YouTube 자동화
**파일:** sync.cjs | community.cjs | yt_oauth_channel.cjs | check_channel.cjs | orbit_publish.py
**설정:** Google Cloud Console → YouTube Data API v3 → OAuth 발급

### 6️⃣ tistory-naver — 📝 블로그 자동화
**파일:** post.py | skin.py | login.py | post.cjs | login.cjs | session_post.py
**설정:** Playwright CDP 로그인 → 쿠키 저장 → 자동 발행

### 7️⃣ mcp — 🤖 MCP 서버 5종
**파일:** eae_mcp_platform.py | eae_mcp_writer.py | parksy_rawmat_mcp.py | parksy_law_mcp.py | parksy_scm_mcp.py
**설치:** `pip install mcp httpx` → `python3 파일.py`

---

## 🔧 config — 공통 설정 템플릿
- **CLAUDE.md** — AI 에이전트 운영 헌법 (레포당 1개 필수)
- **index.html** — GitHub Pages 랜딩 페이지 템플릿
- **data/stats.json** — 통계 데이터 스키마

---

## 📐 생태계 아키텍처 (전체도)

```
📱 갤럭시 폰 (Termux)
    │
    ├─ Claude Code (AI 코딩)
    │     ├── git add/commit/push → GitHub
    │     │     ├── GitHub Actions (테스트/빌드)
    │     │     └── GitHub Pages (웹배포)
    │     │
    │     ├── Discord 웹훅 → 채널 알림
    │     │
    │     └── Telegram 봇 → 원격 명령/리포트
    │
    ├── Google/YouTube API → 영상 업로드
    │
    └── MCP 서버 5종 → AI 도구 체인
```

---

## 🚀 빠른 시작 (30분)

```
1. Termux 설치 → bash gifts/helena/1-phone-claude/INSTALL.sh
2. GitHub 레포 Settings → Pages → main /root → 활성화
3. Discord 웹훅 → GitHub Secrets → DISCORD_WEBHOOK 등록
4. BotFather → 봇 생성 → config/token 입력
5. Google Cloud → YouTube API 키 발급 → OAuth 설정
```

---

*이 문서는 dtslib-papyrus `gift/helena` 브랜치의 SSOT입니다.*
*각 레포 배포는 이 브랜치에서만 진행하며, 직접 푸시는 금지됩니다.*
