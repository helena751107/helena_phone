# 📖 S21 Phone 최적화 — 전체 가이드

> 이 저장소의 모든 문서를 단계별로 연결한 로드맵.
> 순서대로 따라 하면 놀고 있는 갤럭시 폰이 풀스택 서버로 변신한다.

---

## 0단계: 준비물

| 필요 | 설명 |
|------|------|
| 📱 안드로이드 폰 | 갤럭시 S21 기준, 아무 안드로이드나 가능 |
| 🔌 WiFi | 같은 네트워크에서 PC/폰 연결 |
| ⏱ 시간 | 처음 세팅에 2~3시간 |
| 💵 비용 | **0원** (GitHub 무료 + DeepSeek Radar 우회) |
| 🔑 GitHub 계정 | github.com 가입 (무료) |

---

## 1단계: 기반 설치 (01-foundation/)

> **폰을 리눅스 서버로 만드는 과정**

| # | 문서 | 내용 | 난이도 |
|---|------|------|--------|
| 1.1 | [Termux 설치](./01-foundation/termux-setup.md) | F-Droid → Termux + 기본 패키지 | 초급 |
| 1.2 | [proot Ubuntu](./01-foundation/proot-ubuntu.md) | proot-distro로 Ubuntu 컨테이너 | 중급 |
| 1.3 | [Claude Code + DeepSeek](./01-foundation/claude-code.md) | AI 에이전트 설치 + 과금 우회 | 중급 |
| 1.4 | [Git/GitHub 연결](./01-foundation/git-github.md) | 저장소 연결 + push 자동화 | 초급 |

**결과물:** 폰에서 AI 코딩 에이전트가 돌아가는 상태

---

## 2단계: 통신망 구축 (02-network/)

> **폰을 외부와 연결하는 채널 3종 세트**

| # | 문서 | 내용 | 난이도 |
|---|------|------|--------|
| 2.1 | [GitHub Pages](./02-network/github-pages.md) | 정적 웹사이트 호스팅 + Giscus 댓글 | 초급 |
| 2.2 | [Discord 서버](./02-network/discord.md) | 실시간 채팅방 + 위젯 | 초급 |
| 2.3 | [Telegram 봇](./02-network/telegram.md) | 알림/보고 자동화 | 초급 |

**결과물:** 웹사이트 + 채팅방 + 알림봇 완비

---

## 3단계: 방송/발행 (03-broadcast/)

> **폰으로 콘텐츠를 만들어 내보내는 단계**

| # | 문서 | 내용 | 난이도 | 진행 |
|---|------|------|--------|------|
| 3.1 | [YouTube 채널](./03-broadcast/youtube.md) | 5개 채널 아키텍처 + API 준비 | 중급 | 🔧 설계 |
| 3.2 | [티스토리 자동화](./03-broadcast/tistory-auto.md) | Playwright로 자동 포스팅 | 고급 | 🔧 설계 |
| 3.3 | [네이버 블로그](./03-broadcast/naver-auto.md) | Playwright + 쿠키 세션 | 고급 | 🔧 설계 |

**결과물:** 폰에서 콘텐츠 발행 자동화

---

## 4단계: 폰 원격 제어 (04-phone-control/)

> **PC에서 폰을 마음대로 조종하는 단계**

| # | 문서 | 내용 | 난이도 |
|---|------|------|--------|
| 4.1 | [Termux:API](./04-phone-control/termux-api.md) | 80여개 하드웨어 API | 중급 |
| 4.2 | [phone-mcp-server](./04-phone-control/phone-mcp.md) | MCP로 18개 도구 원격 호출 | 중급 |
| 4.3 | [건강 검진](./04-phone-control/health-check.md) | 하드웨어 자동 진단 스크립트 | 중급 |

**결과물:** Claude Code가 폰 배터리 읽고, 플래시 켜고, 문자 보냄

---

## 5단계: 최적화 (05-optimization/)

> **오래된 폰을 최대한 오래, 빠르게 쓰는 법**

| # | 문서 | 내용 | 난이도 |
|---|------|------|--------|
| 5.1 | [배터리 관리](./05-optimization/battery-saving.md) | 충전 사이클 최적화 | 초급 |
| 5.2 | [성능 튜닝](./05-optimization/performance.md) | proot 메모리/CPU 설정 | 중급 |
| 5.3 | [저장공간](./05-optimization/storage.md) | 캐시/로그 정리 자동화 | 초급 |

---

## 설정 파일 모음 (configs/)

그대로 복사해서 쓰면 되는 실제 설정 파일들:

| 파일 | 설명 |
|------|------|
| `configs/settings.json` | Claude Code MCP 설정 |
| `configs/bashrc-example.sh` | .bashrc 예시 (자동시작 포함) |
| `configs/phone-mcp.sh` | MCP 서버 실행 스크립트 |
| `configs/tg.sh` | 텔레그램 메시지 발송 |
| `configs/phone-health.sh` | 건강 검진 스크립트 |

---

## 스크립트 모음 (scripts/)

단독 실행 가능한 유틸리티:

| 스크립트 | 설명 |
|---------|------|
| `scripts/phone-health.sh` | 27개 항목 하드웨어 진단 |
| `scripts/tg.sh` | 텔레그램 메시지 보내기 |
| `scripts/setup-all.sh` | (예정) 전체 자동 설치 |

---

## 연대기 (chronicle/)

이 모든 과정이 실제로 어떻게 진행되었는지 생생한 기록:

| 파일 | 내용 |
|------|------|
| [CHRONICLE.md](./CHRONICLE.md) | DAY 1~2 전체 스토리 |
| `chronicle/` | 세부 기록들 |

---

## 퀵스타트 — 5분 컷

이미 Termux가 설치된 폰이 있다면:

```bash
# 1. Ubuntu 컨테이너
pkg install proot-distr o
proot-distro install ubuntu
proot-distro login ubuntu

# 2. 기본 도구
apt update && apt install git curl nodejs -y

# 3. 이 저장소 클론
git clone https://github.com/helena751107/helena_phone.git
cd helena_phone

# 4. 설정 복사
cp configs/settings.json ~/.claude/
source configs/bashrc-example.sh

# 5. 건강 검진
bash scripts/phone-health.sh
```

---

> **궁금한 거 있으면?**
> - [Discord](https://discord.gg/JTYSZv2WQE) — 실시간 질문
> - [GitHub Issues](https://github.com/helena751107/helena_phone/issues) — 버그/제안
> - 직접 포크해서 마음대로 고쳐쓰셈
