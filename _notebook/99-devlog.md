# 📋 S21 Phone — 전체 개발일지

> 구축 기간: 2026-07-23 ~ 2026-07-24
> 환경: Termux → proot Ubuntu → Claude Code (DeepSeek Radar)

---

## DAY 1 — 2026-07-23

### 1. 기반 구축
- `gugudan.py` 생성 (테스트 파일)
- Git 저장소 초기화 (`/root/work/`)
- GitHub 레포 `s21-work` 생성 → `helena751107/s21-work`
- GitHub 연결 + push 파이프 개통

### 2. Claude Code + DeepSeek Radar (Anthropic 과금 바이패스)
```env
ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
ANTHROPIC_MODEL=deepseek-chat
```
- Claude Code UI/도구는 그대로, LLM 엔진만 DeepSeek V3로 교체
- 비용 약 10~50배 절감

### 3. GitHub Pages 개통
- API로 Pages 활성화: `POST /repos/{owner}/{repo}/pages`
- `index.html` — "S21 Workstation Live" 발행
- Pages URL: `helena751107.github.io/helena_phone/`
- 검증: HTTP 200 + 내용 정상

### 4. 레포 개명 `s21-work` → `helena_phone`
- API: `PATCH /repos/{owner}/{repo}` `{"name":"helena_phone"}`
- 로컬 remote 업데이트 + git push 검증
- Pages 새 URL 자동 리다이렉트 확인

### 5. Discussions + Giscus 댓글 활성화
- `PATCH /repos/{owner}/{repo}` `{"has_discussions":true}`
- Giscus: repo-id + Announcements 카테고리 연결
- 양쪽 레포(`helena_phone`, `helana_log`)에 적용

### 6. 디스코드 서버 구축
- API 로그인: `POST /api/v9/auth/login`
- 서버 생성: `POST /api/v9/guilds` → **S21 Phone** (ID: 1529785842560794684)
- 채널 생성: **#로비** (1529785982818193469), **#ai-보고** (1529785985993408723)
- 위젯 활성화: `PATCH /api/v9/guilds/{id}/widget` `{"enabled":true}`
- 초대링크: `discord.gg/JTYSZv2WQE`
- WidgetBot Crate v3: index.html에 임베드 (우하단 플로팅 버튼)

### 7. 텔레그램 봇 구축
- `@BotFather` → `/newbot` → **@S21Phone_Bot**
- `tg.sh` — 텔레그램 보고 스크립트 (sendMessage API)
- `TG_TOKEN`, `TG_CHAT` 환경변수 등록
- `post-commit` hook → 커밋 시 자동 보고 (후에 제거)
- `CLAUDE.md` → 에이전트 보고 의무 규칙

### 8. Git hooks + 알림 제거
- `post-commit`, `post-merge` hook 삭제
- `CLAUDE.md` 간소화 (핵심만)
- 알림/자동보고 전부 OFF → 수동 보고 체계로 전환

---

## DAY 2 — 2026-07-24

### 9. GitHub 레포 3개 추가 생성
| 레포 | 매칭 티스토리 | YouTube |
|------|-------------|---------|
| `helana-faith` | helana-christianity | Helana Faith |
| `helena-piano` | helena-piano | Helena Piano |
| `helena-metalcare` | helena-metalcare | Metal Craft |

- 각 레포: index.html + Pages + Discussions + Giscus + WidgetBot 전부 활성
- 현재 총 5개 레포: `helena_phone`, `helana_log`, `helana-faith`, `helena-piano`, `helena-metalcare`

### 10. 포털 사이트 전면 개편 (`helena_phone` index.html)
- 레포지토리 생태계 5종 테이블
- 개발일지 타임라인
- 통신망 현황 (GitHub / Discord / Telegram)
- 업무 수첩 10개 링크 카드
- Giscus 게시판 + WidgetBot 채팅

### 11. 업무 수첩 노트북 구축 (`_notebook/ → notebook/`)
| # | 파일 | 내용 |
|---|------|------|
| 00 | INDEX | 목차 |
| 01 | arch | 전체 시스템 아키텍처 |
| 02 | discord | 디스코드 서버/봇/위젯 |
| 03 | telegram | 텔레그램 봇/회의실 |
| 04 | github-pages | Pages + Giscus + WidgetBot |
| 05 | tistory | 블로그 6종 + Playwright 자동화 전략 |
| 06 | youtube | YouTube 채널 5종 설계 + OAuth 대기 |
| 07 | cli-reference | CLI 명령어 모음 |
| 08 | secrets | 비밀 관리 정책 |
| 09 | ecosystem | 전체 생태계 브릿지 테이블 |
| 10 | phone-mcp | 폰 통제 MCP 서버 |

- 모든 md를 HTML로 변환하여 `notebook/`에 저장
- 포털에서 10개 전체 링크

### 12. 전체 생태계 브릿지 테이블 (09-ecosystem)
```
5개 티스토리 = 5개 YouTube 채널 = 5개 GitHub 레포 = 1:1:1 매칭
네이버(helena1975) = 관저탑/그림첩 — 전체 교차 홍보
_notebook/ = History + Making film + 로고 아카이브
```

### 13. 블로그 자동화 리서치
- 티스토리 Open API: **2024년 2월 완전 종료** ❌
- 네이버 포스팅 API: **원래 없음** ❌
- 유일한 방법: **Playwright Headless Chromium** 브라우저 자동화
- 세션 쿠키 재사용(`storage_state`)이 업계 표준

### 14. YouTube 채널 아키텍처 설계
- 5개 채널 = 티스토리 1:1 매칭
- GCP 프로젝트 + gcloud CLI 준비 완료
- OAuth 동의 화면 + TV 클라이언트 ID만 수동 대기 중
- 쿼터 보호: `search.list`(100유닛) 사용 금지, `playlistItems.list`(1유닛) 사용

### 15. phone-mcp-server 설치 (폰 통제)
- **htekdev/phone-mcp-server** — 순수 Termux:API 기반
- 루트/ADB/Shizuku 전혀 없음 ✅
- 18개 도구: SMS, 배터리, WiFi, 카메라, GPS, 클립보드, 플래시, 진동, 알림, 볼륨, 통화...
- `settings.json`에 MCP 등록 (`localhost:3456/mcp`)
- `.bashrc` 자동시작 등록
- 서비스 포트: 3456

---

## 현재 인프라 전체 구성

```
📱 폰 (Android + Termux)
├── proot Ubuntu 컨테이너
│   ├── Claude Code (DeepSeek Radar) ← 현재 너
│   ├── Aider v0.86.2
│   ├── phone-mcp-server (18 도구) ← 📲 폰 통제 가능
│   └── Git → GitHub
│
├── 🌐 GitHub
│   ├── helena_phone (메인 포털)       ✅ Pages + Giscus
│   ├── helana_log (기술노트)           ✅ Pages + Giscus
│   ├── helana-faith (신앙)             ✅ Pages + Giscus
│   ├── helena-piano (피아노)           ✅ Pages + Giscus
│   └── helena-metalcare (금속케어)     ✅ Pages + Giscus
│
├── 💬 Discord (S21 Phone 서버)
│   ├── #로비 (채팅, 위젯 활성)
│   └── #ai-보고 (웹훅 준비)
│
├── 🤖 Telegram (@S21Phone_Bot)
│   └── TG_CHAT=8579179811 (회의실)
│
├── 📝 티스토리 5종
│   ├── galaxys21-pwuser
│   ├── mynote11605
│   ├── helana-christianity
│   ├── helena-piano
│   └── helena-metalcare
│
├── 🌐 네이버 (helena1975) — 관저탑/그림첩
├── 📺 YouTube (@HelenaPark-e7c) — 5채널 설계 완료
└── 📓 _notebook/ — History + Making film + 로고
```

## 남은 작업

| 우선순위 | 작업 | 상태 |
|---------|------|------|
| ⏳ 1 | YouTube OAuth TV 클라이언트 ID 발급 (콘솔 수동) | 대기 |
| ⏳ 2 | YouTube 업로드 스크립트 생성 | 클라이언트 ID 후 |
| ⏳ 3 | 티스토리 자동 포스팅 (Playwright) | 대기 |
| ⏳ 4 | 네이버 자동 포스팅 (Playwright + 쿠키 세션) | 대기 |
| ⏳ 5 | phone-mcp-server UI 자동화 (tap_screen) | 루트/ADB 필요로 보류 |
| ⏳ 6 | 5개 YouTube 채널 실제 생성 | 설계 완료 |

## 비상 연락망

| 채널 | 주소 |
|------|------|
| Discord | `discord.gg/JTYSZv2WQE` |
| Telegram | `t.me/S21Phone_Bot` |
| GitHub | `github.com/helena751107/helena_phone` |
| Pages | `helena751107.github.io/helena_phone/` |
| YouTube | `youtube.com/@HelenaPark-e7c` |
| Naver | `m.blog.naver.com/helena1975` |
