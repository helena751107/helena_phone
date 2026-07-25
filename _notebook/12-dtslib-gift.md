# 🎁 dtslib1979 선물 패키지 분석서

> 수령: 2026-07-24 15:42 UTC
> 기증: dtslib1979
> 브랜치: gift/helena (dtslib-papyrus)
> 전체 규모: **33개 파일, +9,240줄**

---

## PHASE 1 — 이 선물의 전략적 의미

**이 코드가 중요한 게 아니라, 이걸 라이브로 설명할 수 있는 능력이 자산이다.**

비즈니스 모델 = 코드 잠금 ❌ → 오픈소스 + 실시간 강의 능력 ✅  
코드 자체는 증거 전시물. 진짜 상품은 **"이걸 만들고 설명할 수 있는 사람"**.

→ 강의 치트시트를 먼저 만들고, 그 다음 채널별 콘텐츠 소재로 매핑한다.

---

## PHASE 2 — 5개 MCP 서버 강의용 치트시트

### 1. parksy_law_mcp.py (1,056줄 / 45KB)
**법률 게이트 MCP — AI 에이전트의 행동을 정책으로 통제하는 검문소**

| 항목 | 내용 |
|------|------|
| **하는 일** | Claude Code의 모든 액션을 법률 위계(헌법 > 글로벌법 > 역할계약 > SOP)에 따라 검사. 위반 시 차단 또는 인간 승인 요청 |
| **왜 이 구조인가** | 자율 AI에게 법적 책임을 묻는 건 무의미. 대신 행동을 실시간 검열해서 "에이전트는 제안만, 결정은 인간이" 구조를 강제 |
| **핵심 기능 3가지** | ① `check_policy` — 액션 합법성 검사 ② `detect_mental_state` — 사용자 감정 감지(고위험 시 설계/파괴 작업 차단) ③ `audit_log` — 모든 의사결정 기록 |
| **라이브 강의 포인트** | `PRIORITY` 딕셔너리(mild < strong < stop < delegate)를 보여주며 "이게 어떻게 인간-에이전트 경계를 설정하는지" 부터 설명. 11개 self_test 케이스가 이해를 도와줌 |

### 2. parksy_rawmat_mcp.py (938줄 / 33KB)
**Raw Material MCP — Playwright로 Perplexity 크롤링하는 지식 추출 게이트**

| 항목 | 내용 |
|------|------|
| **하는 일** | Playwright로 Perplexity Space에 접속 → Computer 모드 → 질문 전송 → 응답을 구조화된 JSON으로 저장 |
| **왜 이 구조인가** | AI 검색 결과를 API 없이 브라우저 자동화로 추출해야 할 때. Perplexity가 API 안 열어줘도 쓸 수 있음 |
| **핵심** | Playwright headless 모드 + `space_id` 기반 라우팅 |
| **라이브 강의 포인트** | `_PLAYWRIGHT_AVAILABLE` 플래그 처리 (Termux/폰에서는 비활성화)를 먼저 보여주며 "이 코드는 환경에 따라 동작이 달라진다"는 설계 철학부터 |

### 3. parksy_scm_mcp.py (714줄 / 25KB)
**SCM MCP — 콘텐츠 공급망 관리 (Node C)**

| 항목 | 내용 |
|------|------|
| **하는 일** | 아이디어 → 리서치(Perplexity) → 아티클 생성 → 배포(텔레그램/디스코드/네이버/티스토리)까지 콘텐츠 생애주기 관리 |
| **왜 이 구조인가** | 콘텐츠 제작을 공장의 공급망처럼 관리. 각 Node가 독립적으로 동작하고 SCM이 중앙 조율 |
| **3개 카테고리** | ① Publishing — 완성된 콘텐츠 발행 ② Research — 에피소드 실행/아티클 작성 ③ Utility — 아티클 목록/조회 |
| **라이브 강의 포인트** | `TOOLS_DIR` / `ARTICLES_DIR` 경로 체계부터 보여주며 "이게 콘텐츠 공급망의 물류 창고 역할을 한다"고 설명 |

### 4. eae_mcp_platform.py (648줄 / 23KB)
**EAE MCP Platform — SCM의 인프라 버전**

| 항목 | 내용 |
|------|------|
| **하는 일** | parsky_scm과 유사한 콘텐츠 파이프라인. `dtsli` 사용자 경로 하드코딩되어 있음 |
| **라이브 강의 포인트** | SCM과 Platform의 차이점을 비교: "SCM은 현재 발행, Platform은 장기 지식 축적"이라는 구도로 설명. `ARTICLE_WRITER` 경로 등 dtsli 전용 경로를 우리 환경에 맞게 수정하는 과정을 라이브로 보여주면 좋음 |

### 5. eae_mcp_writer.py (486줄 / 17KB)
**EAE MCP Writer — 박씨 스타일 라이터 (파인튜닝)**

| 항목 | 내용 |
|------|------|
| **하는 일** | LLM 출력을 특정 발화 스타일(박씨 스타일)로 변환하는 필터. STYLE_PARAMS 딕셔너리로 즉시 반영 가능 |
| **왜 이 구조인가** | "살아있는 파인튜닝" — 모델 재학습 없이 파라미터 수정만으로 스타일 변경. 300개 JSONL 예제로 few-shot |
| **핵심** | `STYLE_PARAMS` + `parksy_voice_filter.md` + `parksy_v3_300.jsonl` |
| **라이브 강의 포인트** | `STYLE_PARAMS` 딕셔너리 하나만 바꿔서 콘텐츠 스타일이 즉시 바뀌는 걸 라이브로 시연. "이게 17KB 모델 파인튜닝이다" |

---

## PHASE 3 — 전체 자산 인벤토리 + 채널 매핑

### 📦 카테고리별 자산

| 카테고리 | 포함 파일 | 용도 | 즉시 사용 |
|---------|---------|------|---------|
| **🤖 MCP 서버 5종** | law, rawmat, scm, platform, writer | AI 도구 체인 구축 | ✅ 분석 완료 |
| **📝 티스토리/네이버** | post.py, skin.py, login.cjs, post.cjs, session_post.py, workbook | 블로그 자동 포스팅 | ✅ 다음 발주 대상 |
| **✈️ 텔레그램 3종** | core.py, telegram-bot.py, telegram-bridge.py | 메시징 자동화 | ✅ 기존 tg.sh 업그레이드 |
| **🎬 구글/유튜브** | yt_oauth_channel.cjs, orbit_publish.py, sync.cjs, community.cjs, check_channel.cjs | YouTube 업로드 자동화 | ⏳ OAuth 토큰 대기 |
| **💬 디스코드** | webhook.sh, discord-notify.yml | CI/CD 알림 | ✅ |
| **⚙️ GitHub Actions 6종** | rule-tuner, design-library-guard, issue-terminal, acceptance-tests, router-compiler, feedback-collector | 자동화 파이프라인 | ✅ |
| **📱 phone-claude** | INSTALL.sh | Termux→Ubuntu→Claude Code 설치 | ✅ |

### 📺 채널별 콘텐츠 소재

| 채널 | 소재 | 설명 | 우선순위 |
|------|------|------|---------|
| **🎬 YouTube** | "AI 에이전트에게 법을 가르치다" | parksy_law_mcp 라이브 코딩 — 법률 게이트가 뭔지, 왜 필요한지 실제 코드로 설명 | 🔴 최우선 |
| | "폰으로 MCP 서버 5개 돌리기" | S21 폰에서 law_mcp/rawmat_mcp/scm_mcp 실행 시연 | 🟡 |
| | "콘텐츠 공급망 자동화" | SCM MCP로 아이디어→리서치→발행 전과정 라이브 | 🔴 최우선 |
| **📝 티스토리** | "Playwright로 네이버/티스토리 자동 포스팅" | tistory-naver 폴더 분석 + 설정 가이드 | 🔴 최우선 |
| | "MCP 서버 5종 완전 해설" | 각 서버의 구조와 철학을 글로 정리 | 🟡 |
| **✈️ 텔레그램** | 매 라이브/포스팅 알림 | 모든 새 콘텐츠 자동 보고 | 🔴 항상 |
| | dtslib 선물 패키지 분석 결과 | 이 문서 자체를 텔레그램 브리핑 | ✅ 완료 |

### 🗺️ 콘텐츠 발행 파이프라인 (SCM 모델 적용)

```
아이디어 (라이브 방송/에피소드)
    ↓
Perplexity 리서치 ← rawmat_mcp
    ↓
스크립트/아티클 ← writer_mcp (박씨 스타일)
    ↓
법률 검사 ← law_mcp
    ↓
발행 ← scm_mcp
    ├── YouTube (영상)
    ├── 티스토리 (글)
    ├── 네이버 (그림첩)
    ├── 텔레그램 (알림)
    └── 디스코드 (알림)
```

---

## PHASE 4 — 즉시 실행 가능한 것 vs 기다려야 하는 것

| 상태 | 작업 | 필요 조건 |
|------|------|----------|
| ✅ **즉시** | MCP 서버 5개 구조 분석 + 강의 | 이 치트시트만 있으면 가능 |
| ✅ **즉시** | GitHub Actions 6종 활성화 | `.github/workflows/`에 이미 있음 |
| ✅ **즉시** | 텔레그램 브릿지 업그레이드 | core.py + telegram-bridge.py 병합 |
| ✅ **즉시** | 디스코드 웹훅 알림 | webhook.sh 설정만 |
| ⏳ **대기** | 티스토리/네이버 자동 포스팅 | Playwright + 쿠키 세션 발급 (컨디션 좋은 날) |
| ⏳ **대기** | YouTube 자동 업로드 | OAuth TV 클라이언트 ID (컨디션 좋은 날) |
| ⏳ **보류** | 원자재 MCP (rawmat) | Playwright + Perplexity 계정 필요 |

---

> **결론:** 5개 MCP 서버는 라이브로 설명할 준비 완료.  
> 다음 스텝 = tistory-naver Playwright 발주 (컨디션 회복 후).  
> 그 다음 = YouTube OAuth (좋은 날).
