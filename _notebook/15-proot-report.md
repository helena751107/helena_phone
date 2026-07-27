# 📋 S21 Phone — proot Ubuntu 개발일지 종합 보고서

> 일시: 2026-07-23 ~ 2026-07-25
> 환경: Galaxy S21 → Termux → proot Ubuntu → Claude Code (DeepSeek)
> 입력: 100% STT 음성입력 (12시간 실작업)
> 신체: 식당 육체노동 병행
> 산출: 39커밋 · 102파일 · 15,874줄

---

## 1. 기반 인프라 (DAY 1, 7/23)

### GitHub 생태계
- helena_phone 레포 생성 → Pages 활성화 (`helena751107.github.io/helena_phone/`)
- 레포 개명: s21-work → helena_phone
- 3개 신규 레포: helana-faith, helena-piano, helena-psycare
- 총 5개 레포, 전부 Pages + Discussions + Giscus + WidgetBot 활성화
- Collaborator: dtslib1979 (5개 레포 admin)

### AI 엔진
- Claude Code → DeepSeek 우회
- `ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic`
- 비용 10~50배 절감

### 통신망 3종
- Discord: S21 Phone 서버 (#로비, #ai-보고) + WidgetBot Crate v3
- Telegram: @S21Phone_Bot + tg.sh 보고 스크립트
- GitHub Pages: index.html 포털 + 5레포 생태계

---

## 2. 업무 수첩 + 문서화 (DAY 2, 7/24)

### _notebook/ 14종
| # | 파일 | 내용 |
|---|------|------|
| 00 | INDEX | 목차 |
| 01 | arch | 시스템 아키텍처 (Termux→proot→GitHub→Discord→Telegram) |
| 02 | discord | 디스코드 서버 구축 상세 |
| 03 | telegram | 텔레그램 봇/회의실 구축 |
| 04 | github-pages | Pages + Giscus + WidgetBot |
| 05 | tistory | 블로그 6종 + Playwright 자동화 전략 |
| 06 | youtube | YouTube 채널 5종 아키텍처 + OAuth 설계 |
| 07 | cli-reference | CLI 명령어 모음 |
| 08 | secrets | 비밀 관리 정책 |
| 09 | ecosystem | 5x5 생태계 브릿지 테이블 (GitHub↔Tistory↔YouTube 1:1:1) |
| 10 | phone-mcp | MCP 서버 18개 도구 + Domain/Codomain 경계 분석 |
| 11 | health | 건강 검진 시스템 (27항목, S/A/B/C 등급) |
| 12 | dtslib-gift | dtslib1979 선물 패키지 분석 (33파일, 9,240줄) |
| 13 | midterm-eval | 중간평가 v1(93/100) + v2(98/100) |
| 14 | daemon-design | 트랙 1 돌봄 데몬 설계 (Termux 네이티브, AI 의존성 제로) |

### GUIDE.md + CHRONICLE.md
- GUIDE.md: 0~5단계 풀스택 로드맵 (Termux→proot→Claude Code→네트워크→방송→폰제어→최적화)
- CHRONICLE.md: DAY 1~2 전체 연대기

---

## 3. CONSTITUTION.md — 헌법 제정 (v1→v4)

### v1: 헌법 분리
- CLAUDE.md와 별도 문서로 분리
- 전문: 미션 A(콘텐츠) / 미션 B(돌봄)
- 제1~4장 + 제1~14조

### v2: 대필작가-간병인 + 핸드오프
- "미션 A/B" → "트랙 1: 돌봄 / 트랙 2: 소망"
- 제7조 신설: **"핸드오프가 곧 성공이다"**
  - 대필작가는 영원한 역할이 아님
  - 수익은 누나 명의로
  - 교재의 첫 번째 학생은 누나
  - 존엄과 일관성이 바이럴보다 우선

### v3: Chain of Command
- 제0장 신설: 지위·계급·역할
- 👑 HELENA = Boss. AI = 도구.
- "니 형" 호칭 금지
- 6원칙: 단일 Boss, AI=도구, 출력=가설, 호칭금지, 평가방향, 협력자권한

### v4: 플랫폼 층 분리
- 제8조 신설: Layer A(원본·인간) / Layer B(구조·STT+에이전트)
- GitHub Pages → YouTube API 두 플랫폼에서 동일 패턴 실증

**현재: 제0장 + 제1~4장 + 총 16조**

---

## 4. 실행 코드 + 스크립트

| 파일 | 줄수 | 설명 |
|------|------|------|
| phone-health.sh | 383 | 27항목 건강 진단 (10카테고리: 배터리/WiFi/GPS/카메라/센서/통신) |
| index.html | 556 | 포털 랜딩페이지 (5레포 테이블 + 개발일지 타임라인 + 통신망 현황) |
| tg.sh | 36 | 텔레그램 메시지 전송 |
| tg_discord_bridge.py | 61 | TG-디스코드 브릿지 봇 |
| phone-mcp.sh | 5 | MCP 서버 실행 래퍼 |
| scripts/publish.py | 신규 | 티스토리 5종 + 네이버 일괄 포스팅 실행기 |

---

## 5. YouTube OAuth 인증 (7/24)

- GCP 프로젝트: S21 YouTube (ID: 911931724403)
- OAuth 동의 화면 → External → 테스트 사용자 등록
- TV Device Flow: `google.com/device` → XZDJ-SHNM
- 문제 해결: 403 access_denied (테스트 사용자 미등록) → 수동 추가
- 문제 해결: YouTube Data API 미활성화 → 콘솔에서 활성화
- 결과: Helena Park (@helenapark-e7c, UCRUuiKCCwIbyvqlxTNpDfKw) 연결
- YouTube Analytics API 활성화 + 쿼리 성공
- Reporting API: 스킵 (강박사 합류 후)

---

## 6. Playwright 자동화 환경

- python3-venv + ~/browser-env 생성
- Playwright 1.61.0 + Chromium headless 설치 (proot Ubuntu)
- dtslib 기존 코드 분석: post.py(티스토리, 15KB), session_post.py(네이버, 7KB), post.cjs, login.cjs, skin.py
- scripts/publish.py 작성 — 5계정 일괄 발행 래퍼

---

## 7. 트랙 1 돌봄 데몬 설계

`_notebook/14-daemon-design.md`:
- **위치:** Termux 네이티브 (proot 위 아님) — CC 세션과 독립적 생존
- **감지:** 배터리(잔량/온도/충전상태), GPS(위치 이탈/무응답), 활동패턴, 연결성
- **보고:** 정기(1시간) + 이상(즉시) + 웰니스 체크
- **에스컬레이션:** 헬레나 → 목사님 → 119(수동)
- **AI 의존성 제로:** care-state.json 단방향 읽기만, CC가 죽어도 데몬은 산다

---

## 8. 박씨캡처(ParksyCapture) APK

- 패키지: com.parksy.capture (183MB)
- 기능: Claude 대화를 Android Share Intent로 마크다운 저장
- 연동: helana_log/logs/2026/07/ → GitHub 자동 푸시
- 한계: 이미지는 Claude CDN 인증 URL로만 전달 → 캡처 불가
- 전략: 텍스트=박씨캡처 / 이미지섞인=스크린샷 병행

---

## 9. 중간평가

| 축 | v1 | v2 |
|----|-----|-----|
| 산출물 | 27 | 30 |
| 아키텍처 | 19 | 20 |
| 판단 품질 | 25 | 25 |
| 철학 정합성 | 15 | 15 |
| 지속가능성 | 7 | 8 |
| **총점** | **93** | **98** |

v2 재평가 사유: 미착수 항목(Playwright·YouTube OAuth·돌봄 데몬)은 AI 실행 책임, 사용자 평가에서 제외.

---

## 10. 핵심 테제 (오늘 정립된 것)

1. **코드는 인스턴스, 사고 서식이 자산** — 생산량은 AI 시대 평균, 판단력이 희소
2. **핸드오프가 곧 성공** — 대필작가는 영원하지 않다, 누나가 직접 이어받는 것이 목표
3. **모든 플랫폼 = Layer A(원본·인간) + Layer B(구조·STT+에이전트)**
4. **AI 출력은 전부 1차 가설** — Boss의 검증 없이 팩트로 간주하지 않는다
5. **사용자 자신이 교보재** — STT 12시간+식당노동으로 풀스택 구축, 이게 누나에게 보여줄 첫 번째 케이스 스터디

---

> 📱 helena751107.github.io/helena_phone/
> 💬 discord.gg/JTYSZv2WQE
> 🤖 t.me/S21Phone_Bot
> 📺 youtube.com/@HelenaPark-e7c
