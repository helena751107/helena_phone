# 📋 S21 Phone — 전체 개발 종합 보고서
> 구축: 2026-07-23 ~ 2026-07-25
> 환경: Galaxy S21 → Termux → proot Ubuntu → Claude Code (DeepSeek Radar)
> 입력: 100% STT 음성입력 (12시간 실작업)
> 신체: 식당 육체노동 병행
> 산출: 39커밋 · 102파일 · 15,874줄

---

## 1. Git 커밋 히스토리 (전체 39개)

```
dd11356 교재 합성 지침 — 판단층+실행층 병합 방법론
3ab1736 proot 개발 종합 보고서 (15,874줄·39커밋·14문서)
ce68cfc devlog: 박씨캡처 이미지 한계 + 투트랙 캡처 전략 (섹션 38)
347ca5d devlog 완성 — 섹션 30~37 추가
c15d079 devlog: 거품 제거 — 진짜 기준은 '돌아가냐'
ed59b4c 헌법 v4 — 제8조 플랫폼 층 분리 원칙 (Layer A/B)
fb80ccd YouTube OAuth 인증 완료 — @helenapark-e7c 채널 연결
76d67af 너가 교보재다 — STT 교재 첫 번째 증명은 사용자 자신
be2b59e devlog: 작업 조건 재발견 — STT 12시간+식당노동 병행
24d86ea 헌법 v3 — 제0장 지위·계급·역할 (Chain of Command) 신설
282acac 중간평가 v2 + Playwright 착수 + 트랙1 데몬 설계
24802c8 헌법 v2 — 대필작가-간병인 모델 + 핸드오프 원칙
cde3fae 헌법 제정 — CONSTITUTION.md + CLAUDE.md 실무규칙 분리
2a6a78e dtslib1979 gift analysis
a5abae7 dtslib 선물 패키지 — Phone Claude 풀스택 생태계
f913664 Playwright verification results
00f1f32 Apple-level redesign of landing page
6c85bf7 rename: helena-metalcare → helena-psycare
10dd701 5-repo ecosystem restructuring
0d2aa61 restructure helena_phone as public optimization bible
aea95ce DAY2 wrap-up — health check + work-stop decision
234dadd phone-health.sh 27-item check
f0a7893 install termux-api, verify phone-mcp-server live
43c7e8d full devlog (DAY1-2) + phone-mcp to portal
7a85076 phone-mcp-server (18 tools, no root)
d94ab26 transform portal with devlog timeline
52431fd blog automation strategy (Playwright)
79c4974 ecosystem bridge table (5x5)
acb16a5 Naver blog (helena1975)
23aad5a tistory 5-blog set
cb21ebd operation notebook
66d18a5 Telegram reporting rules
ac68b03 Discord embed + Giscus
c85819e Giscus, repo links, responsive design
94202c9 TG reporting, Discord bridge, index.html
51e6ae3 update index
7356711 pages rebuild for aider
9f63576 pages rebuild
39c12a5 Add aider install manual
330f7b2 Add index.html for GitHub Pages
026d295 gugudan.py
```

---

## 2. CONSTITUTION.md — 헌법 전문 (v4, 제0장 + 제1~4장 + 총 16조)

### 전문 — 투트랙: 돌봄과 소망

**트랙 1: 돌봄 (Caregiving)**
- 대상: 큰누나 — 통화 상대 너랑 목사님뿐, 정신 질환, 케어 필요
- g(돌봄) = 위치추적 이상의 안전 데이터 + 이상 신호 감지 + 에스컬레이션
- 성공 기준: "절대 안 깨질 것"

**트랙 2: 소망 (Aspiration)**
- f(소망) = 대필작가가 되어 누나가 건강했더라면 살았을 삶을 미러링하여 세상에 표현
- 대필작가-간병인 모델: 누나가 주인공, 운영자는 대필작가이자 간병인
- 핸드오프가 곧 성공 — 누나가 스스로 운영할 수 있게 되는 것이 목표
- 모든 계정은 큰누나 명의 (helena751107, helena1975, @HelenaPark-e7c)

### 제0장 — Chain of Command
- HELENA = Boss, AI = 도구, "니 형" 호칭 금지
- AI 출력은 전부 1차 가설, Boss 승인 전까지 가설
- 강박사(CS PhD) 기술 자문 — 판단 권한은 Boss 위임 범위 내

### 제1장 — 불변 원칙 (제1~8조)
1. 루팅/Shizuku 금지 (삼성페이 사용 중)
2. 코드는 선물 — 저작권 무의미
3. 스캐폴드 우선 — 일단 작동, 나중에 개선
4. 바텀업 로그 → 압축 (99-devlog.md)
5. AI 출력은 전부 1차 가설
6. 판단력만이 희소 자산
7. 핸드오프가 곧 성공 — 대필작가는 영원한 역할이 아니다
8. 플랫폼 층 분리 — Layer A(원본·인간) / Layer B(구조·STT+에이전트)

### 제2장 — 신원 규칙 (제9~11조)
- 계정 분리: helena751107, helena1975, dtslib1979, YouTube @HelenaPark-e7c
- 토큰 및 인증 분리: 누나 계정 / 본인 계정 완전 분리

### 제3장 — 세션 규칙 (제12~14조)
- 작업 우선순위: 티스토리 Playwright → 네이버 → YouTube OAuth

### 제4장 — 보안 경계 (제15~16조)
- 식별정보 보호, 위치 데이터 격리

---

## 3. 전체 인프라 구성

```
📱 S21 (Android + Termux + proot Ubuntu)
├── Claude Code (DeepSeek Radar)
├── phone-mcp-server (18 도구, 포트 3456)
├── 5개 GitHub 레포 → Pages + Giscus + WidgetBot
├── Discord S21 Phone 서버 (#로비, #ai-보고)
├── Telegram @S21Phone_Bot (tg.sh 보고)
├── 티스토리 5종 (Playwright 발주 대기)
└── YouTube 5채널 (OAuth 완료)
```

### 5개 GitHub 레포

| 레포 | 정체성 | Pages |
|------|--------|-------|
| helena_phone | S21 폰 최적화 바이블 | ✅ |
| helana_log | 박식캡처 리버싱 | ✅ |
| helana-faith | 가족 신앙사/비교종교학 | ✅ |
| helena-piano | 피아노 종합 + 음원 생성 | ✅ |
| helena-psycare | 뷰티풀마인드 정신분석 | ✅ |

### 5x5 생태계 매트릭스
```
GitHub 5레포 ↔ 티스토리 5종 ↔ YouTube 5채널 (1:1:1)
              ↘
          네이버 관저탑 (helena1975, 교차홍보 게이트웨이)
```

---

## 4. phone-mcp-server — 폰 통제 (18개 도구)

- 순수 Termux:API 기반, 루트/ADB/Shizuku 불필요
- 배터리, GPS, WiFi, 카메라, SMS, 플래시, 진동, 클립보드, 볼륨, 알림, 통화...

### Domain (가능) vs Codomain (불가능)
- 백그라운드 API: 100% 통제 가능
- GUI 조작 (tap_screen): 0% — root/ADB 필요, 삼성페이와 충돌

---

## 5. 건강 검진 시스템 (phone-health.sh)

- 27개 항목, 10개 카테고리
- 등급: S/A/B/C
- 최초 검진: A등급 (27통과/0실패/3경고)
- 6회 검진 완료, JSON 시계열 보관

---

## 6. YouTube OAuth 인증 완료

- GCP 프로젝트: S21 YouTube (ID: 911931724403)
- 채널: Helena Park (@helenapark-e7c, UCRUuiKCCwIbyvqlxTNpDfKw)
- TV Device Flow: google.com/device
- YouTube Data API v3 + Analytics API 활성화 완료

---

## 7. dtslib1979 선물 패키지 (33파일, 9,240줄)

### MCP 서버 5종
1. parksy_law_mcp.py (1,056줄) — AI 법률 게이트
2. parksy_rawmat_mcp.py (938줄) — Perplexity 크롤링
3. parksy_scm_mcp.py (714줄) — 콘텐츠 공급망
4. eae_mcp_platform.py (648줄) — SCM 인프라 버전
5. eae_mcp_writer.py (486줄) — 박씨 스타일 라이터

### 기타
- 티스토리/네이버: post.py, session_post.py, skin.py
- 텔레그램: core.py, telegram-bot.py, telegram-bridge.py
- GitHub Actions 6종
- YouTube: yt_oauth_channel.cjs, orbit_publish.py

---

## 8. 중간평가 (v1→v2)

| 축 | v1 | v2 | 만점 |
|----|-----|-----|------|
| 산출물 | 27 | 30 | 30 |
| 아키텍처 | 19 | 20 | 20 |
| 판단 품질 | 25 | 25 | 25 |
| 철학 정합성 | 15 | 15 | 15 |
| 지속가능성 | 7 | 8 | 10 |
| 총점 | 93 | 98 | 100 |

---

## 9. 핵심 테제

1. 코드는 인스턴스, 사고 서식이 자산
2. 핸드오프가 곧 성공 — 대필작가는 영원하지 않다
3. 모든 플랫폼 = Layer A(원본·인간) + Layer B(구조·STT+에이전트)
4. AI 출력은 전부 1차 가설
5. 사용자 자신이 교보재 — STT 12시간+식당노동으로 풀스택 구축

---

## 10. 판단 10선 (판단 품질 25/25)

1. DeepSeek 우회 — "비싸서 못 쓴다" → "우회해서 쓴다"
2. 삼성페이 → 루팅 금지
3. 티스토리 API 종료 → Playwright 즉시 전환
4. YouTube OAuth 보류 — "컨디션 좋은 날만"
5. force push 복구 — cherry-pick으로 당황 안 하고
6. CC 오류 캐치 — "OAuth API 폐기됐다" 검증 요구
7. 코드는 선물 — 저작권 무의미, 설명 가능성이 자산
8. 알림 제거 + 작업 중단 — "무엇을 하지 않을지" 결정
9. 대필작가-간병인 모델 정립
10. 핸드오프 = 성공

---

## 11. 트랙 1 돌봄 데몬 설계

- Termux 네이티브 (proot 위 아님), AI 의존성 제로
- 배터리·GPS·활동패턴·연결성 감지
- 보고: 정기(1시간) + 이상(즉시) + 웰니스 체크
- 에스컬레이션: 헬레나 → 목사님 → 119(수동)

---

## 12. 교재 합성 지침

- 판단층(Claude 스레드) + 실행층(devlog) 병합 방법론
- 타임스탬프 매칭 → 사건 단위 → 챕터 구조
- 재사용 가능한 방법론 (다른 프로젝트에도 적용)

---

## 13. 파일 통계

```
_notebook/ 19개 md 파일 (2,119줄)
루트 문서: CHRONICLE(178), CLAUDE(69), CONSTITUTION(284), GIFT(114), GUIDE(156), README(83)
실행 코드: phone-health.sh(383), tg.sh(36), tg_discord_bridge.py(61), gugudan.py(10)
메인 페이지: index.html(556)
총합: 4,055줄
```

---

## 14. 현재 인프라 한눈에

| 채널 | 주소 |
|------|------|
| GitHub | github.com/helena751107/helena_phone |
| Pages | helena751107.github.io/helena_phone/ |
| Discord | discord.gg/JTYSZv2WQE |
| Telegram | t.me/S21Phone_Bot |
| YouTube | youtube.com/@HelenaPark-e7c |
| Naver | m.blog.naver.com/helena1975 |

---

> 이 보고서는 2026-07-25 S21 Phone의 전 개발 이력을 종합한 것입니다.
> 39커밋, 102파일, 15,874줄, 헌법 16조, 5레포 생태계, 3종 통신망, 18개 MCP 도구.
