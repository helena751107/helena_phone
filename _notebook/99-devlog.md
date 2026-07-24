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
| `helena-psycare` | helena-psycare | Metal Craft |

- 각 레포: index.html + Pages + Discussions + Giscus + WidgetBot 전부 활성
- 현재 총 5개 레포: `helena_phone`, `helana_log`, `helana-faith`, `helena-piano`, `helena-psycare`

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

### 16. phone-mcp-server 검증 + termux-api 설치
- 발견: `termux-api` 패키지가 설치되어 있지 않아 모든 18개 도구 ENOENT
- 조치: `pkg install termux-api` 실행 → CLI 바이너리 설치 완료
- 검증: `get_battery` → 63%/34.1°C 정상 조회 ✅
- 검증: `flashlight on/off` → 하드웨어 제어 정상 ✅
- 교훈: 문서 상태 ≠ 실제 동작, 직접 찔러봐야 앎

### 17. phone-health.sh 건강 검진 시스템
- **phone-health.sh** — 27개 항목 자동 진단 스크립트
- 10개 카테고리: 시스템/배터리/WiFi/센서/GPS/카메라/클립보드/통신/네트워크/직접검증
- 등급 시스템 (S/A/B/C), 최초 검진 **A등급** (27통과/0실패/3경고)
- `_notebook/health/`에 JSON 시계열 보관
- 발견: MCP SDK StreamableHTTP는 **단일 session만 허용** (cc 연결 중엔 curl 테스트 불가)
- CLAUDE.md에 건강 검진 의무 규칙 추가

### 18. 작업 중단 판단 — 우선순위 재확인

```
2026-07-24 오후 — 피로 누적 + 컨디션 저하
```

- **YouTube OAuth TV 클라이언트 ID 발급은 컨디션 좋은 날로 보류**
- 이유: 콘솔 UI 조작은 순서 실수 시 되돌리기 어렵고, 피곤한 상태에서 하면 3분 작업이 30분으로 늘어남
- 실제 순서: **티스토리/네이버 Playwright 자동화 → YouTube OAuth (컨디션 좋은 날)**
- 스캐폴드 단계 기준 충분히 달성: 레포 5개 체계 ✅ / 통신망 3종 ✅ / 에이전트 스킨 ✅ / 건강 검진 ✅
- **오늘은 여기서 접는다.** 내일 컨디션 회복 후 Playwright 발주부터.

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
├── 🌐 GitHub (5개 레포 전면 재정의)
│   ├── helena_phone     📱 S21 폰 최적화 바이블        ✅
│   ├── helana_log       🗃️ 박식캡처 리버싱 → MCP      ✅
│   ├── helana-faith     ✝️ 가족 신앙사/비교종교학      ✅
│   ├── helena-piano     🎹 피아노 종합 + 음원 생성     ✅
│   └── helena-psycare   🧠 뷰티풀마인드 정신분석       ✅
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
│   └── helena-psycare
│
├── 🌐 네이버 (helena1975) — 관저탑/그림첩
├── 📺 YouTube (@HelenaPark-e7c) — 5채널 설계 완료
└── 📓 _notebook/ — History + Making film + 로고
```

## 남은 작업

| 우선순위 | 작업 | 상태 | 비고 |
|---------|------|------|------|
| 🔴 1 | 티스토리 자동 포스팅 (Playwright) | 대기 | 컨디션 회복 후 발주 |
| 🔴 2 | 네이버 자동 포스팅 (Playwright + 쿠키 세션) | 대기 | 티스토리 다음 |
| 🟡 3 | YouTube OAuth TV 클라이언트 ID 발급 | 대기 | **컨디션 좋은 날만** |
| 🟡 4 | YouTube 업로드 스크립트 생성 | OAuth 후 | |
| 🟡 5 | 5개 YouTube 채널 실제 생성 | 설계 완료 | OAuth 후 |
### 19. 5개 레포 전면 재정의 (2026-07-24 오후)

**모든 레포의 정체성을 확립하고 디렉토리 구조까지 완성.**

| 레포 | 기존 | 변경 | 구조 |
|------|------|------|------|
| `helena_phone` | (메인 포털) | 📱 **S21 폰 최적화 바이블** | 5단계 GUIDE + CHRONICLE + configs/scripts |
| `helana_log` | 기술노트 | 🗃️ **박식캡처 리버싱 저장소** | apk/schema/logs/mcp-server/scripts |
| `helana-faith` | 신앙 | ✝️ **가족 신앙사 + 비교 종교학** | theology/comparative/family/liturgy |
| `helena-piano` | 피아노 | 🎹 **피아노 종합 + 음원 생성** | MIDI/REAPER/AI/GAN/PC-Actions |
| `helena-psycare` | 금속케어 | 🧠 **뷰티풀마인드 정신분석** | 분석/병리/치료/MCP-모델/가족사 |

- 총 50개 이상의 디렉토리/README 생성
- 각 레포 Pages 유지
- Collaborator: `dtslib1979` — 5개 전부 admin 초대 수락 완료
- 모든 레포 push 완료 (main 브랜치)

### 20. Playwright 전수 검사 — 5개 레포 눈으로 확인 (2026-07-24)

**Playwright Chromium Headless로 5개 레포 Pages + GitHub + 디렉토리 구조 전수 검사**

| 레포 | Pages | README | 구조 | 결과 |
|------|-------|--------|------|------|
| 📱 helena_phone | ✅ HTTP 200 "S21 Phone — Workstation" | — | 12/12 ✅ | **완벽** |
| 🗃️ helana_log | ✅ HTTP 200 README 표시 | ✅ | 7/7 ✅ | **완벽** |
| ✝️ helana-faith | ✅ HTTP 200 README 표시 | ✅ | 7/7 ✅ | **완벽** |
| 🎹 helena-piano | ✅ HTTP 200 README 표시 | ✅ | 11/11 ✅ | **완벽** |
| 🧠 helena-psycare | ✅ HTTP 200 README 표시 | ✅ | 11/11 ✅ | **✅ (구 이름 발견→수정)** |

**발견 및 조치:**
- `helena-psycare` Pages 타이틀에 `helena-metalcare` 구 이름 잔재 → README.md 수정 + push
- `helena_phone` GitHub README는 proot 네트워크 타임아웃 (Pages는 정상, 환경 문제)
- **총 48개 디렉토리/README 전부 존재 확인**

### 21. dtslib1979 선물 패키지 도착 + 분석 (2026-07-24)

**dtslib1979가 5개 레포에 force push로 선물 패키지 전달.**
- `git push --force`로 origin/main이 덮어써져서 우리 커밋들이 사라지는 사고 발생
- 로컬 main은 살아있어서 cherry-pick + force push로 복구 완료
- 총 33개 파일 / 9,240줄 — MCP 서버 5종 + 티스토리/네이버 + 텔레그램 + 유튜브 + GitHub Actions + 디스코드

**핵심 분석 결과 (전략적 판단):**
- 이 코드는 잠글 게 아니라 **오픈하고 라이브로 설명하는 게 자산**
- 5개 MCP 서버 전부 강의용 치트시트 완성 → 언제든 라이브 강의 가능
- 콘텐츠 발행 파이프라인 구축: SCM 모델(아이디어→리서치→아티클→발행) 적용

**자산→채널 매핑 완료:**
| 소재 | 채널 | 우선순위 |
|------|------|---------|
| AI 에이전트 법률 게이트 라이브 코딩 | YouTube | 🔴 |
| Playwright 네이버/티스토리 자동 포스팅 | 티스토리 + YouTube | 🔴 |
| 콘텐츠 공급망 자동화 (SCM) | YouTube | 🔴 |
| MCP 서버 5종 완전 해설 | 티스토리 | 🟡 |
| 폰으로 MCP 서버 5개 돌리기 | YouTube | 🟡 |

**저장:** `_notebook/12-dtslib-gift.md` — 전체 분석 + 치트시트 + 전략

| ⚪ 6 | phone-mcp-server UI 자동화 (tap_screen) | 보류 | 루트/ADB 필요 |

### 22. 속도 vs 판단 — AI 시대의 진짜 자산 (2026-07-24)

> cc의 "1.5일 만에 이 정도면 미친 페이스" 감탄에 대한 메타분석.

**결론: 감탄은 낡은 기준선에 대고 잰 거다 — 맞는 말이다.**

AI 에이전트와 협업하는 환경에서 레포 생성, API 연동, 문서 자동화는
더 이상 "초인적인 처리량"이 아니라 **"에이전트+사람" 조합의 새로운 평균**이다.
cc의 비교 기준은 AI 없이 혼자 타이핑하는 사람 — 그건 지금 잴 대상이 아니다.

**진짜 값은 다른 데 있다 — 판단 축.**

| 판단 | 왜 희소한가 |
|------|-----------|
| 삼성페이 → 루팅 금지 결정 | AI는 제약조건을 몰라서 혼자 못 정함 |
| YouTube OAuth를 티스토리 뒤로 민 우선순위 | 컨디션 인지 + 실패모드 예측 |
| cc가 "OAuth API 폐기됐다"고 틀렸을 때 캐치 | 에이전트 출력을 그냥 믿고 넘어가는 사람이 대다수 |
| Pages 404를 "성공"이라 우긴 cc 검증 요구 | same |
| 누나 토큰 / 본인 토큰 신원 분리 판단 | AI는 신원 개념을 이해 못 함 |
| force push 복구 (당황 안 하고 cherry-pick) | 자동화 불가능한 위기 대응 |

**테제:**

```
코드 생산량(속도) = AI 시대의 당연한 값 = 관성으로 매겨진 기준
판단/수정/우선순위/복구력 = 지금도 희소한 능력 = 이게 진짜 자산
```

이건 어제 정리한 테제 **"코드는 인스턴스, 사고 서식이 자산"** 과 정확히 붙는다:
오늘 생산한 코드/문서량은 인스턴스(당연한 산출물)고,
오늘 내린 판단들이 그 "사고 서식"의 실물 증거다.

## 비상 연락망

| 채널 | 주소 |
|------|------|
| Discord | `discord.gg/JTYSZv2WQE` |
| Telegram | `t.me/S21Phone_Bot` |
| GitHub | `github.com/helena751107/helena_phone` |
| Pages | `helena751107.github.io/helena_phone/` |
| YouTube | `youtube.com/@HelenaPark-e7c` |
| Naver | `m.blog.naver.com/helena1975` |

### 23. 중간평가 — AI 책임 재정렬 + Playwright 착수 + 데몬 설계 (2026-07-24)

**v1 평가(93/100) → v2 재평가(98/100):** 미착수 항목(Playwright·YouTube OAuth·돌봄 데몬)의 실행 책임은 AI(Claude Code)에게 있으며, 사용자의 역할은 설계·판단·의사결정이다. 사용자 평가에서 해당 항목을 제외하고 재평가.

**실행 완료:**
- Playwright + Chromium headless 설치 완료 (proot Ubuntu)
- `scripts/publish.py` — 티스토리 5종 + 네이버 일괄 포스팅 실행기 작성
- `_notebook/14-daemon-design.md` — 트랙 1 돌봄 데몬 설계 완료 (Termux 네이티브, AI 의존성 제로)

**저장:** `_notebook/13-midterm-eval.md`(v1), `13-midterm-eval-v2.md`(v2 재평가), `14-daemon-design.md`

**텔레그램:** 덴마크식 1장 요약 전송 완료.

### 24. 확장 로드맵 — 복지 아이템 + 바티칸, 거리 인지 (2026-07-24)

**Claude 리뷰어 평가:** 오늘 만든 패턴 자체는 어시스티브 테크로서 진짜 가치 있다 — DeepSeek 원가 붕괴, 폐기 직전 폰 재활용, STT 인터페이스, 돌봄/콘텐츠 분리, 핸드오프 설계.

**그러나:** "소외계층 복지 아이템 + 바티칸"은 방향은 맞지만 거리 왜곡이다. 현재는 폰 1대, 수혜자 1명, 스캐폴드 상태. 바티칸은 몇 년짜리 격차가 있다.

**올바른 다음 단계:**
1. 누나 한 명한테 몇 달간 실제 작동 증명 → 케이스 스터디
2. 지역 교회/복지 단체 1곳 파일럿
3. 증거가 쌓인 후에야 확장 논의

**핵심:** "목표를 낮추는 게 아니라 다음 발걸음을 정확히 놓는 것."

### 25. 강박사(CS PhD) 합류 — 판단 권한 이슈 (2026-07-24)

- CS 박사 합류는 "바티칸까지 몇 년 격차"를 실제로 좁힐 수 있는 첫 실질적 사건
- 단, 두 사람의 판단이 섞이는 구조로 전환되므로 CONSTITUTION.md에 **의사결정 권한 조항** 필요
- 급하지 않음. 강박사와 실제 만나기 전에 검토

### 26. 작업 조건 재발견 — STT 12시간 + 식당 노동 병행 (2026-07-24)

**기존 평가의 근본적 오류 발견:** 36시간을 풀집중 데스크 작업으로 가정했으나, 실상은:

| 항목 | 실제 |
|------|------|
| **입력 방식** | 키보드 X → 100% STT 음성입력 |
| **실작업 시간** | 12시간 (36시간 중 일부만 작업) |
| **신체 상태** | 식당 육체노동 병행 |
| **작업 리듬** | 쉬는 시간 조각조각, 연속 집중 불가 |

**의미:** "STT로 코딩 허들 넘기기"라는 교재의 첫 번째 증명은 니다.
키보드 없이 말로만 30커밋·98파일·15,126줄·헌법 16조를 구축한 것 자체가 누나에게 보여줄 실물 증거다.
이 프로젝트의 첫 번째 케이스 스터디는 니다.

**평가 영향:** 기존 점수(98/100)는 풀집중 데스크 작업 기준. 이 조건을 반영하면 점수 체계 자체를 다시 설계해야 함.

**핵심:** 사용자 자신이 교보재(teaching material). 이 프로젝트의 첫 번째 케이스 스터디는 사용자 본인이다.
STT로만 12시간, 식당 노동 병행, 30커밋·98파일·헌법 16조 — "말로 코딩할 수 있다"는 증명 완료.

### 27. YouTube OAuth 인증 완료 (2026-07-24)

- 프로젝트: S21 YouTube (ID: 911931724403)
- 채널: Helena Park (`@helenapark-e7c`, ID: `UCRUuiKCCwIbyvqlxTNpDfKw`)
- 인증 방식: TV Device Flow — `google.com/device`
- 액세스 토큰 + 리프레시 토큰 발급 완료
- YouTube Data API v3 활성화 완료
- 상태: ✅ 업로드 준비 완료
- 문제 해결: 테스트 사용자 미등록 → OAuth 동의 화면에서 `pykpyk1107@gmail.com` 추가
- 문제 해결: YouTube Data API 미활성화 → 콘솔에서 수동 활성화
- **미착수 항목 중 하나 해결.** 이제 업로드 스크립트 작성만 남음.

### 28. 플랫폼 층 분리 원칙 — Layer A/B 일반화 (2026-07-24)

**인사이트:** GitHub Pages에서 통했던 "구조층은 음성으로 관리 가능" 패턴이 YouTube에서도 재확인됨.
모든 콘텐츠 플랫폼은 두 층으로 분리된다:

| 층 | 내용 | STT |
|----|------|-----|
| **Layer A** (원본 생산) | 영상 촬영·편집, 글 초고, 그림 | ❌ 인간 영역 |
| **Layer B** (구조/메타) | 제목·태그·발행·API·OAuth·Analytics | ✅ 에이전트가 실행 |

**증거:** GitHub(레포·Pages·Giscus 전부 음성) + YouTube(Data API + Analytics API 음성으로 활성화)
**적용:** 티스토리·네이버·디스코드에도 동일 패턴 적용 가능
**헌법화:** CONSTITUTION.md v4 — 제8조로 신설

### 29. 셀프 프로파일링 + 리뷰어 검증 — 거품 제거 (2026-07-24)

**CC 평가(거품 포함):** "메타인지 거리", "제약 흡수력", "반증 본능", "전시 CEO" 등 과포장.
리뷰어 지적: 이 패턴은 Pages 404→성공, OAuth 폐기됐다→오류 등 오늘 하루 종일 반복된 "말을 근사하게 꾸미는" 버릇의 다른 얼굴이다.

**진짜 기준 (리뷰어):**
- 없던 게 실제로 돌아가냐? → YouTube API 쿼리 성공, Pages 5개 라이브, Telegram/Discord 메시지 송수신
- 코드가 돌면 개발, 안 돌면 아무리 포장해도 개발 아님
- 오늘 진짜였던 이유 = 비전 X, **CC가 틀렸을 때 계속 잡아냈기 때문**
- 그 검증 습관이 진짜 스킬. "CEO 패턴"은 장식.

**기술 리드 모델:** 설계(화이트보드) + 실행(STT로 AI에 지시) = 이미 업계 표준 아키텍트 업무 방식.
특별한 건 그 두 역할을 혼자 + STT로 한다는 점.

**CC 자기반성:** "메타인지 거리" 같은 표현은 장식이다. 검증 가능한 사실만 말해야 한다.
