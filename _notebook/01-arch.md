# 전체 시스템 아키텍처

## 스택 구조

```
폰 (Android + Termux)
├── proot-distro Ubuntu 컨테이너 (ubi)
│   ├── /root/work/ ← Git 저장소
│   │   ├── index.html        ← GitHub Pages 랜딩 페이지
│   │   ├── gugudan.py        ← 구구단 (테스트)
│   │   ├── tg.sh             ← 텔레그램 보고 스크립트
│   │   ├── tg_discord_bridge.py ← TG-디스코드 브릿지 봇
│   │   ├── CLAUDE.md         ← AI 에이전트 규칙
│   │   ├── .secrets.env      ← 로컬 비밀 (git 제외)
│   │   └── _notebook/        ← 이 업무 수첩
│   │
│   ├── Claude Code (현재 엔진) ← AI 코딩 에이전트
│   │   └── DeepSeek 바이패스 ← Anthropic 과금 회피
│   │
│   └── Aider v0.86.2         ← 보조 AI 코딩 도구
│
├── GitHub → helena751107/helena_phone
│              helena751107/helana_log
│
├── Tistory → 5개 블로그 세트
│   ├── mynote11605.tistory.com
│   ├── helana-christianity.tistory.com
│   ├── helena-piano.tistory.com
│   ├── galaxys21-pwuser.tistory.com
│   └── helena-metalcare.tistory.com
│
├── Discord 서버: S21 Phone (ID: 1529785842560794684)
│   ├── #로비 (채팅)
│   └── #ai-보고 (웹훅/보고)
│
└── Telegram 봇: @S21Phone_Bot
    └── TG_CHAT: 8579179811
```

## DeepSeek (Anthropic 과금 바이패스)

Claude Code가 DeepSeek API 위에서 돌도록 우회:

```bash
ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
ANTHROPIC_MODEL=deepseek-chat
ANTHROPIC_AUTH_TOKEN=sk-xxxxx
DEEPSEEK_API_KEY=sk-xxxxx
```

→ Claude Code UI/도구는 그대로, LLM 엔진만 DeepSeek V3로 교체
→ 비용 약 10~50배 절감

## 통신망 3종

| 채널 | 용도 | 방식 |
|------|------|------|
| GitHub Pages | 정적 페이지 | git push 자동 발행 |
| Discord | 실시간 채팅/로비 | WidgetBot + 초대링크 |
| Telegram | AI 보고/알림 | tg.sh → sendMessage API |

## 전체 생태계

```
YouTube (5채널) ← 1:1 → Tistory (5블로그) ← 1:1 → GitHub (5레포)
                                                       ↓
                                                  _notebook (히스토리/로고)
                                                       ↓
                                                  Naver 관저탑 (그림첩/홍보)
```

자세한 내용: `_notebook/09-ecosystem.md`

---

## 현재 아키텍처 (2026-07-25 업데이트)

```
📱 Galaxy S21 5G (SM-G991N)
│  Android 15 · 8GB RAM · 256GB · Exynos 2100
│
├── Termux (Android 네이티브)
│   ├── termux-api (18개 CLI 도구)
│   ├── crontab → care-daemon.sh (돌봄)
│   └── proot-distro → Ubuntu 26.04 LTS
│
├── proot Ubuntu 컨테이너
│   ├── Claude Code (DeepSeek) — 메인
│   ├── Grok CLI (xAI SuperGrok) — 시각·Naver
│   ├── Aider (DeepSeek) — 보조 코딩
│   ├── phone-mcp-server (18도구·3456포트)
│   ├── Playwright + Chromium headless
│   ├── Python 3.14 + Node.js
│   └── Git → GitHub (5레포)
│
├── 🌐 출력 채널
│   ├── GitHub Pages (5사이트·자동배포)
│   ├── YouTube @helena_phone (OAuth)
│   ├── Discord (2채널·WidgetBot)
│   ├── Telegram @S21Phone_Bot
│   ├── 티스토리 5종 (수동)
│   └── 네이버 웹진 (수동+Grok)
│
└── 🛡️ 트랙1 독립 (Termux 네이티브)
    └── care-daemon.sh (AI 의존성 제로)
```

## AI 도구

| 도구 | 엔진 | 비용 | 용도 |
|------|------|------|------|
| Claude Code | DeepSeek | $0 | 코드·문서·자동화 |
| Grok CLI | xAI SuperGrok | 45,000원/월 | 시각·Naver·이미지 |
| Aider | DeepSeek | $0 | 보조 코딩 |
