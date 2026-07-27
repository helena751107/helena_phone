# S21 Phone — 개발 백서 (완결판)

**버전 2.0 | 2026-07-27 | 5일·145커밋·265파일·46,650줄**

---

## 1. 개요

구형 Galaxy S21(2021년·중고가 20만원) 1대로 풀스택 AI 개발·방송·출판 미니 스튜디오를 구축한 프로젝트. 100% STT 음성입력. 비용 0원. 대필작가-간병인 모델.

```
STT 음성 → Claude Code(코드) + Grok(시각) + Aider(보조)
         → GitHub(공장) → Naver(칠판) → YouTube(강의) → 수익(누나)
```

---

## 2. 5×5 생태계 — 하나의 Naver 블로그로 수렴

| # | GitHub (누나 명의) | 티스토리 | YouTube | 테마 | 한국 이해 축 |
|---|-------------------|---------|---------|------|------------|
| 1 | helena_phone | galaxys21-pwuser | @helena_phone | 📱 폰 최적화 바이블 | IT·기술 |
| 2 | helana_log | mynote11605 | 추후 | 🗃️ 행정 대화록 | **행정·복지** |
| 3 | helena-faith | helana-christianity | 추후 | ✝️ 가족 신앙사 | **문화·종교** |
| 4 | helena-piano | helena-piano | 추후 | 🎹 피아노·AI음원 | **음악·예술** |
| 5 | helena-psycare | helena-psycare | 추후 | 🧠 정신의학·분석 | **정신건강·돌봄** |

**모든 콘텐츠는 Naver helena1975 웹진으로 수렴.**
한국어 귀화 시험 준비생에게 5개 축의 진짜 한국을 보여주는 교재.

---

## 3. 8개 워크센터

| # | 워크센터 | 플랫폼 | 주체 | 가동 |
|---|---------|--------|------|------|
| ① | 공장 | GitHub | Claude Code | 🟢 |
| ② | 전시장 | GitHub Pages | 자동배포 | 🟢 |
| ③ | 방송탑 | YouTube @helena_phone | Claude Code | 🟢 |
| ④ | 인터컴 | Telegram @S21Phone_Bot | tg.sh | 🟢 |
| ⑤ | 업무일지 | 티스토리 | 사람 | 🟡 |
| ⑥ | 웹진·칠판 | Naver helena1975 | 사람+Grok | 🟡 |
| ⑦ | 로비 | Discord | WidgetBot | 🟢 |
| ⑧ | 기억복원루프 | 티스토리 RSS | Claude Code | 🟢 |

---

## 4. 기술 스택

```
Galaxy S21 5G (SM-G991N·Android 15)
├── Termux + proot Ubuntu 26.04
├── Claude Code (DeepSeek·$0)
├── Grok CLI (xAI SuperGrok·45,000원/월)
├── Aider (DeepSeek·$0)
├── phone-mcp-server (18도구·루트 없음)
├── phone-health.sh (27항목 건강검진)
├── care-daemon.sh (트랙1 돌봄·AI 의존성 제로)
├── g/install.sh v2 (사용자 변수화·1줄 설치)
├── scripts/yt_upload.py (YouTube OAuth)
├── scripts/grok_api.py (Grok 연동)
└── Playwright + Chromium headless
```

---

## 5. 핵심 방법론

| 방법론 | 설명 |
|--------|------|
| **칠판 모델** | Naver=AI가 정리한 사고의 공개 작업 공간 (§59) |
| **Paste Pipeline** | API 없는 플랫폼: Claude→TG→복사→발행 (§24) |
| **액자식 메타** | 만드는 과정 자체가 교재 (§57) |
| **AI가 독자다** | 사람보다 AI 에이전트 파싱에 최적화 (§58) |
| **이중 칠판** | YouTube 녹화 시 Naver(무엇)+Pages(어떻게) (§64) |
| **역방향 글로벌** | 해외→한국어학습→Naver로 진입 (§80) |
| **귀화 교재** | 5레포=한국 이해의 5개 축 (§81) |

---

## 6. 독자성 ID — 제약을 설계로

| 제약 | 대부분 반응 | 이 프로젝트 |
|------|----------|----------|
| 돈 없음 | 포기 | $0 스택 설계 |
| 키보드 못 씀 | 좌절 | 100% STT |
| 돌봄 병행 | 개발 중단 | 핸드오프=성공 |
| API 없음 | 자동화 포기 | Paste Pipeline |
| LLM이 학습 | 저작권 방어 | 홍보 채널로 역이용 |

---

## 7. 주요 수치

| 지표 | 값 |
|------|-----|
| 구축 기간 | 5일 (2026-07-23~27) |
| 커밋 | 145회 |
| 파일 | 265개 |
| 코드+문서 | 46,650줄 |
| 문서 분량 | 국판 500페이지+ |
| AI 에이전트 | 3종 |
| 워크센터 | 8개 |
| GitHub 레포 | 5개 |
| Pages 사이트 | 5개 |
| YouTube 채널 | 2개 |
| 텔레그램 봇 | 6개 |
| 총 플랫폼 계정 | 25개 |
| 월 운영비 | ~55,000원 (프로모 ~15,000원) |
| 입력 방식 | 100% STT 음성 |
| 개발일지 | 81섹션 |
| 업무수첩 | 40종 |

---

## 8. 설치

```bash
# 변수 지정
GITHUB_USER="내아이디" GITHUB_TOKEN="ghp_..." bash <(curl -sL https://raw.github.com/helena751107/helena_phone/main/g/install.sh)

# 또는 대화형
bash <(curl -sL https://raw.github.com/helena751107/helena_phone/main/g/install.sh)
```

상세: `install-guide.html`

---

## 9. 3층 최종 출판 구조

```
Naver (한국 칠판·검색·AI 원천)
  │  백서·원칙·구조·한국 독자
  ▼
YouTube (글로벌 강의·수익)
  │  튜토리얼·멤버십·광고
  ▼
GitHub Pages (자체 IP 플랫폼)
  │  PWA·대시보드·인터랙티브·CDN·$0
  ▼
GitHub (원본·코드·SSOT)
```

---

## 10. 링크

| 플랫폼 | URL |
|--------|-----|
| 📱 포털 | helena751107.github.io/helena_phone |
| 💻 GitHub | github.com/helena751107/helena_phone |
| 📺 YouTube | youtube.com/@helena_phone |
| 🌐 Naver | m.blog.naver.com/helena1975 |
| 📝 티스토리 | galaxys21-pwuser.tistory.com |
| 💬 Discord | discord.gg/JTYSZv2WQE |

---

> © 2026 Helena Park · 대필작가-간병인
> 모든 계정은 누나 명의입니다.
> 이 백서는 S21 Phone 개발일지 §1~81을 1장으로 압축한 완결판입니다.
