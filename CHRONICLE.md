# 📋 S21 Phone 최적화 연대기

> 이 저장소가 어떻게 만들어졌는지 — 생생한 현장 기록
> 기간: 2026-07-23 ~ 2026-07-24 (2일)
> 환경: 갤럭시 S21 → Termux → proot Ubuntu → Claude Code (DeepSeek Radar)

---

## DAY 1 — 2026-07-23: 폰을 서버로

### 오전: 첫 삽

**"갤럭시 폰 하나로 어디까지 할 수 있을까?"**

시작은 단순한 테스트 파일 하나였다.

```
gugudan.py  ← 구구단 출력 (Python 테스트)
```

여기서 시작해서 Git 저장소를 만들고, GitHub에 연결했다. 처음 만든 레포 이름은 `s21-work`. Pages도 바로 개통했다.

```
helena751107.github.io/helena_phone/  ← "S21 Workstation Live" 발행
```

### 오후: AI 에이전트 이식

진짜 핵심은 **Claude Code를 폰에서 돌리는 것**. 그런데 문제가 있었다:
- Anthropic API는 비싸다 (호출 한 번에 수백 원)
- DeepSeek는 1/10 가격

그래서 만든 게 **DeepSeek Radar** — `ANTHROPIC_BASE_URL`만 DeepSeek endpoint로 바꾸는 꼼수. Claude Code의 UI/도구는 그대로, LLM 엔진만 DeepSeek V3로 교체.

> **비용: 0원. 성능: 거의 동일.**

### 저녁: 통신망 구축

폰이 혼자 일하게 만들었으니, 밖에서도 상황을 알 수 있어야 했다.

1. **GitHub Pages** — 정적 웹사이트 (무료 호스팅)
2. **Discord 서버** — 실시간 채팅방 + WidgetBot 위젯
3. **Telegram 봇** — AI가 작업 완료를 보고하는 채널

```bash
# 텔레그램 보고는 이 한 줄이 전부
bash tg.sh "✅ 작업 완료"
```

CLAUDE.md에 "AI 에이전트는 작업 후 텔레그램으로 보고할 의무가 있다"는 규칙을 넣었다. 에이전트가 자기 일을 스스로 보고하게 만든 것.

### 밤: GitHub 레포 확장

레포를 5개로 늘렸다 — 각각 티스토리 블로그 1:1 매칭:

| 레포 | 매칭 블로그 | 용도 |
|------|-----------|------|
| `helena_phone` | (메인 포털) | 전체 허브 |
| `helana_log` | mynote11605 | 기술블로그 |
| `helana-faith` | helana-christianity | 신앙 |
| `helena-piano` | helena-piano | 피아노 |
| `helena-metalcare` | helena-metalcare | 금속공예 |

각 레포마다 Pages + Giscus 댓글 + WidgetBot 채팅 전부 자동 활성화.

---

## DAY 2 — 2026-07-24: 폰 통제와 검증

### 오전: phone-mcp-server 설치

PC에서 폰을 원격 조종하고 싶었다. 방법을 찾다가 발견한 게 **phone-mcp-server**:
- Termux:API 기반 (루트/ADB 불필요)
- 18개 도구: SMS, 배터리, WiFi, 카메라, GPS, 클립보드, 플래시, 진동...
- MCP 프로토콜로 Claude Code가 직접 호출 가능

설치는 5분 컷. 그런데...

### 발견: termux-api 패키지 누락

```
$ termux-battery-status
→ ENOENT (파일 없음)
```

😱 뭐야 왜 안 돼?

**원인:** `phone-mcp-server`만 설치했지, `termux-api` 패키지(실제 CLI 바이너리)를 안 깔았음.

```
pkg install termux-api  ← 이게 없었음
```

설치 후 테스트:

```
get_battery → 64% / 34.1°C ✅
flashlight  → ON / OFF  ✅  ← 🔦 실제 폰 플래시가 켜짐!
```

### 정오: 건강 검진 시스템

"이 하드웨어들이 진짜 살아있는지"를 정기적으로 확인해야겠다는 생각이 들어서 **phone-health.sh**를 만들었다:

- 10개 카테고리, 27개 항목 자동 검진
- 배터리/WiFi/플래시/진동/클립보드/GPS/카메라/SMS/연락처...
- 등급 시스템 (S/A/B/C)
- 결과를 JSON으로 시계열 저장

```
첫 검진 결과: A등급 (27통과 / 0실패 / 3경고)
```

경고 3개는 GPS(실내라 안 잡힘), 통화기록 권한, 마이크 권한 — 모두 허용 가능한 수준.

### 오후: 우선순위 정리

YouTube OAuth TV 클라이언트 ID를 발급받으려고 했는데, 문득 생각했다:

> **"지친 상태에서 콘솔 UI 붙잡았다가 실수하면? 3분 작업이 30분이 된다."**

그래서 YouTube는 **컨디션 좋은 날로 보류**. 티스토리/네이버 Playwright 자동화가 먼저다.

### 작업 중단

스캐폴드 단계 기준은 충분히 달성했다:
- ✅ 레포 5개 체계
- ✅ 통신망 3종 (Pages + Discord + Telegram)
- ✅ AI 에이전트 스킨
- ✅ 폰 원격 제어
- ✅ 건강 검진 자동화

> **"오늘은 여기서 접는다. 내일 컨디션 회복 후 Playwright 발주부터."**

---

## 현재 인프라 전체 구성

```
📱 갤럭시 S21 (Android + Termux)
├── 🐧 proot Ubuntu 컨테이너
│   ├── 🤖 Claude Code (DeepSeek Radar) ← AI 코딩 에이전트
│   ├── 📡 phone-mcp-server (18개 도구) ← 폰 통제
│   └── 🔗 Git → GitHub
│
├── 🌐 GitHub (5개 레포)
│   ├── helena_phone (메인 포털)       ✅ Pages + Giscus
│   ├── helana_log (기술노트)           ✅ Pages + Giscus
│   ├── helana-faith (신앙)             ✅ Pages + Giscus
│   ├── helena-piano (피아노)           ✅ Pages + Giscus
│   └── helena-metalcare (금속케어)     ✅ Pages + Giscus
│
├── 💬 Discord (S21 Phone 서버)
│   ├── #로비 (실시간 채팅)
│   └── #ai-보고 (웹훅/보고)
│
├── 🤖 Telegram (@S21Phone_Bot)
│
├── 📝 티스토리 5종 + 네이버 블로그
└── 📺 YouTube 5채널 (설계 완료, OAuth 대기)
```

---

## 남은 작업 (우선순위 순)

| 순위 | 작업 | 상태 | 조건 |
|------|------|------|------|
| 🔴 1 | 티스토리 자동 포스팅 (Playwright) | 🔧 준비 | 컨디션 회복 후 |
| 🔴 2 | 네이버 자동 포스팅 (Playwright) | 🔧 준비 | 티스토리 후 |
| 🟡 3 | YouTube OAuth 클라이언트 ID 발급 | ⏳ 대기 | **좋은 날만** |
| 🟡 4 | YouTube 업로드 스크립트 | ⏳ 대기 | OAuth 후 |
| ⚪ 5 | UI 자동화 (tap_screen) | 🚫 보류 | 루트/ADB 필요 |

---

> 이 연대기는 계속된다.  
> 다음 에피소드: 티스토리/네이버 Playwright 자동화 — 그리고 YouTube OAuth (좋은 날에)

---

## 현재 인프라 (2026-07-25 기준)

```
📱 S21 (Android + Termux + proot Ubuntu)
├── 🤖 Claude Code (DeepSeek Radar) — 메인 코딩 엔진
├── 🎨 Grok CLI (xAI SuperGrok) — 시각·Naver
├── 🔧 Aider (DeepSeek) — 보조 코딩
├── 📡 phone-mcp-server (18도구)
├── 🌐 GitHub (5레포) + Pages (5사이트)
├── 💬 Discord (2채널) + WidgetBot
├── 🤖 Telegram @S21Phone_Bot
├── 📝 티스토리 5종
├── 📺 YouTube @helena_phone
└── 🌐 네이버 웹진 (helena1975)
```

## AI 비용

| 도구 | 월 비용 | 역할 |
|------|--------|------|
| Claude Code (DeepSeek) | $0 | 코드·문서·자동화 |
| Grok CLI (SuperGrok) | 45,000원 | 시각·Naver·이미지 |
| Aider (DeepSeek) | 포함 | 보조 코딩 |
| **합계** | **~55,000원/월** | |

## 핵심 성과

- 41커밋 · 96파일 · 11,727줄
- CONSTITUTION.md 헌법 16조 제정
- g/install.sh 1줄 설치기
- care-daemon.sh 돌봄 데몬
- phone-health.sh 27항목 건강검진
- YouTube OAuth + 업로더
- Grok CLI + API 연동
- Paste Pipeline 방법론
- 국판 500페이지 분량 문서
