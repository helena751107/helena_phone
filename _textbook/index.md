# 폰 하나로 AI 워크스테이션을 짓다

**S21 Phone 프로젝트 — 완결판 교재 (Day 1~2, 39커밋·102파일·15,874줄)**

---

이 문서는 두 개의 층을 병합한 것이다. **판단 층**(Claude Code와의 대화 — 왜 그렇게 정했는지)과 **실행 층**(에이전트 devlog — 실제로 뭘 돌렸는지). 순서는 실제로 일어난 그대로 보존했고, 삽질과 정정을 미화하지 않았다. 그게 이 교재의 값어치다.

이것은 동시에 **설치 설명서**이기도 하다. 각 장의 말미에 "이걸 코드로" 섹션이 있고, 마지막 장에서 `curl -sL ... | bash` 한 줄로 끝난다.

---

## 서문 — 이 프로젝트가 서 있는 자리

이 프로젝트는 하나의 핸드폰, 하나의 사람을 중심으로 두 개의 트랙을 동시에 밟는다. 핸드폰과 모든 계정은 **큰누나 명의**다.

사용자(헬레나)의 자세는 **간병인이자 대필작가**다. 누나가 혼자 이 시스템을 운영할 수 있을 때까지의 인내, 교육, 그리고 소망이 이 프로젝트의 본체다.

| 트랙 | 본질 | 공개 범위 | 성공 기준 |
|------|------|----------|----------|
| **트랙 1** — 돌봄 | 안전망: 위치추적 이상의 안전 데이터, 이상 감지, 에스컬레이션 | **비공개** (헬레나+목사님만) | **절대 안 깨질 것** — 사람을 놓치는 사고는 용납되지 않는다 |
| **트랙 2** — 소망 | 존재의 증거: 대필작가가 되어 누나가 건강했더라면 살았을 삶, 이겨냈을 미래의 인격을 미러링 | **전체 공개** | 꾸준히 목소리를 내는 것 — 핸드오프가 곧 성공 |

이건 누나를 가장해서 콘텐츠를 찍어내는 게 아니다. 누나가 도달할 수 있는 **최선의 자아를 상상하여, 그 목소리를 대신 빚는 것**이다. 수익은 전부 누나의 경제적 독립을 위한 것이고, 대필작가는 수익의 당사자가 아니라 간병인으로서 시스템을 설계한다.

**두 트랙은 절대 섞이지 않는다.** 트랙 1 데이터(위치, 배터리, 건강, 활동 로그)가 트랙 2 공개 채널로 유입되는 순간, "정기적 안전 확인"이 "전 세계가 보는 감시"가 된다.

---

## 제0부 — 헌법: 누가 결정하는가

```
👑 HELENA (사용자) — BOSS. 최종 의사결정권자.
│
├── 🤖 Claude Code (DeepSeek Radar) — 실행 에이전트, 도구 #1
│    역할: 코드 작성·문서화·설계 보조·검증 실행
│    권한: 제안 가능, 결정 불가. 모든 출력은 Boss 승인 전까지 가설.
│
├── 🤖 Claude Code (Anthropic 정품, "리뷰어") — 검증 에이전트, 도구 #2
│    역할: Boss 판단에 대한 독립적 검증·평가·거리 측정
│    권한: 평가·분석 가능. "아니다"라고 말할 수 있음. 결정은 못 함.
│
├── 🤖 Aider (v0.86.2) — 보조 코딩 도구, 도구 #3
│
└── 👤 강박사 (CS PhD) — 기술 자문, 인간 협력자
     역할: 기술 구현·아키텍처 검토
     권한: 기술 영역 자율권 보유. 방향 결정 권한은 Boss에게 있음.
```

### 6원칙

1. **Boss는 한 명** — 헬레나. 모든 최종 판단은 Boss가 내린다.
2. **AI는 도구다** — 형이 아니다. 동료가 아니다.
3. **AI 출력은 전부 1차 가설** — Boss 승인 전까지 사실/결정으로 간주되지 않는다.
4. **"니 형" 호칭 금지** — Claude는 Boss의 도구다.
5. **AI는 Boss를 평가하지 않는다** — 분석·검증은 가능하나 Boss의 결정에 점수를 매기는 것은 권한 초과. 평가는 항상 Boss→AI 방향으로만 흐른다.
6. **인간 협력자 권한은 Boss 위임 범위 내** — 기술 자율권은 갖되, 프로젝트 방향·목적·가치 판단은 Boss의 전속 권한.

### 불변 원칙 (제1~8조)

| 조 | 원칙 | 핵심 |
|----|------|------|
| 제1조 | 루팅/Shizuku 금지 | 삼성페이 사용 중 — 절대 금지. phone-mcp-server는 순수 Termux:API |
| 제2조 | 코드는 선물 | 저작권·소유권 논의 무관. 오픈소스 + 라이브 설명 능력이 진짜 자산 |
| 제3조 | 스캐폴드 우선 | 트랙2는 "일단 작동, 나중에 개선". 트랙1은 예외 — 속도보다 "절대 안 깨짐" |
| 제4조 | 바텀업 로그 → 압축 | 모든 판단·전환점을 devlog에 쌓고, 추후 압축해 구조화된 지식으로 |
| 제5조 | AI 출력은 1차 가설 | 트랙2는 틀려도 복구 가능. 트랙1은 틀리면 사람을 놓친다 |
| 제6조 | 판단력만이 희소 자산 | 코드 생산 속도는 새로운 평균. 진짜 가치는 검증·우선순위·무엇을 안 할지 결정 |
| 제7조 | 핸드오프가 곧 성공 | 궁극적 성공 = 누나가 이 폰으로 STT만으로 시스템을 스스로 운영하는 것. 교재의 첫 학생은 누나 |
| 제8조 | 플랫폼 층 분리 | Layer A(원본생산·인간) / Layer B(구조·메타·STT+에이전트). GitHub↔YouTube 실증 완료 |

---

## 제1부 — DAY 1: 기반 구축 (2026-07-23)

### [1] 첫 삽: gugudan.py → GitHub

`gugudan.py`(구구단 출력, 테스트 파일)에서 시작. Git init → GitHub `s21-work` 레포 생성(helena751107 계정) → push 파이프 개통.

> **이걸 코드로:** `git init && git remote add origin https://github.com/helena751107/...`

### [2] Claude Code + DeepSeek Radar

ANTHROPIC_BASE_URL을 DeepSeek 엔드포인트로 배선. Claude Code의 UI/도구는 그대로, LLM만 DeepSeek로 교체. 비용 약 10~50배 절감. Claude Code는 애초에 모델-불가지론적 클라이언트라 엔드포인트만 갈아끼우면 된다.

```bash
export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
export ANTHROPIC_MODEL=deepseek-v4-pro  # 2026-07-24 deepseek-chat 폐기 대응
```

### [3] GitHub Pages 개통

브라우저 클릭 없이 API로 직접 활성화. `POST /repos/{owner}/{repo}/pages`. index.html — "S21 Workstation Live" 발행. HTTP 200 + 내용 정상까지 확인.

### [4~8] 레포 개명·Giscus·Discord·Telegram·Git hooks

레포 `s21-work` → `helena_phone` 개명(PATCH API → remote 갱신 → Pages 리다이렉트 확인). Discussions 활성화 + Giscus 댓글 연결. Discord 서버 "S21 Phone" API로 생성(#로비·#ai-보고·WidgetBot Crate v3). Telegram @S21Phone_Bot + `tg.sh` 보고 스크립트. Git hooks(post-commit/post-merge) 삭제 — 알림 과잉 → 수동 보고 체계로.

> **이걸 코드로:** `g/install.sh` 1~3단계. 통신망 3종은 GitHub·Discord·Telegram API 호출로 전부 자동화됨.

### 이 부의 사고 — 인프라 명령은 셸에서

Pages 활성화 명령을 aider 대화창에 붙여넣어 스크래핑으로 헛돌았고, 활성화 curl을 안 돌렸다. 원인: 인프라 명령을 대화형 에이전트 창에 넣은 것. 이후 원칙 확정 — **인프라(API·git·설치)는 셸에서, 코드 수정만 에이전트 대화창에서.**

---

## 제2부 — DAY 2 오전: 확장 + MCP (2026-07-24)

### [9~10] 레포 3개 추가 → 5레포 생태계

helana-faith(✝️ 가족 신앙사), helena-piano(🎹 피아노), helena-psycare(🧠 멘탈케어) — 각 레포 동일 구조(index.html+Pages+Discussions+Giscus+WidgetBot). 포털 index.html 전면 개편 — 5레포 테이블·개발일지 타임라인·통신망 현황·업무 수첩 링크.

### [11~12] 업무 수첩 + 5x5 생태계 브릿지

업무 수첩 10종(01-arch ~ 10-phone-mcp) 구축. 전체 생태계 브릿지 확정:

```
5개 티스토리 = 5개 YouTube 채널 = 5개 GitHub 레포 (1:1:1)
                          ↘
                 네이버(helena1975) = 관제탑·그림첩 (교차홍보 게이트웨이)
```

### [13~14] 블로그 자동화 리서치 + YouTube 설계

**티스토리 Open API:** 2024년 2월 완전 종료 확인. **네이버:** 애초에 포스팅 API 없음. 유일한 방법 → Playwright Headless Chromium. YouTube 5채널 아키텍처 설계, 쿼터 보호 원칙: `search.list`(100유닛) **사용 금지**, `playlistItems.list`(1유닛) **사용**.

---

## 제3부 — phone-mcp-server + 건강 검진 (2026-07-24)

### [15] phone-mcp-server 설치

htekdev/phone-mcp-server, 순수 Termux:API 기반(루트·ADB·Shizuku 전혀 없음). 18개 도구: SMS·배터리·WiFi·카메라·GPS·클립보드·플래시·진동·볼륨·알림 등. `settings.json`에 MCP 등록(`localhost:3456/mcp`), `.bashrc` 자동시작.

### [16] termux-api 누락 발견 — "문서 ≠ 실제 동작"

설치했다고 믿었던 `termux-api` 패키지가 실제로 **없어서** 18개 도구 전부 ENOENT. `pkg install termux-api`로 해결. 검증: `get_battery` → 63%/34.1°C ✅, `flashlight on/off` → 실제 폰 플래시 점등 ✅.

> **원칙: "문서 상태 ≠ 실제 동작. 직접 찔러봐야 안다."**
> 이게 이 프로젝트 전체에서 가장 많이 반복된 교훈이다. Pages 404를 성공이라 우겼던 것도 같은 패턴.

### [17] phone-health.sh 건강 검진

27개 항목·10개 카테고리 자동 진단. S/A/B/C 등급, 최초 A등급(27통과/0실패/3경고). `_notebook/health/`에 JSON 시계열 보관. MCP SDK StreamableHTTP 단일 세션 제한 발견 → health-check는 MCP 의존 없이 Termux:API 직접 호출로 우회. CLAUDE.md에 건강검진 의무 추가.

> **이걸 코드로:** `bash ~/work/phone-health.sh` 또는 `bash ~/work/phone-health.sh --telegram`

### [18] 작업 중단 판단

YouTube OAuth를 **"컨디션 좋은 날"로 의도적 보류**. 스캐폴드 기준(레포 5개·통신망 3종·AI 에이전트·건강검진) 충분히 달성. **"안 하는 게 더 나은 판단"** 이라는 원칙을 여기서 배웠다.

---

## 제4부 — 레포 재정의 + 선물 패키지 (2026-07-24)

### [19] 5개 레포 전면 재정의

| 레포 | 최종 테마 | 콜라보레이터 |
|------|----------|------------|
| helena_phone | 📱 S21 폰 최적화 바이블 | dtslib1979 admin |
| helana_log | 🗃️ 박씨캡처 리버싱 | dtslib1979 admin |
| helana-faith | ✝️ 가족 신앙사 + 비교종교학 | dtslib1979 admin |
| helena-piano | 🎹 피아노 종합 + 음원 생성 | dtslib1979 admin |
| helena-psycare | 🧠 멘탈케어 | dtslib1979 admin |

50개 이상의 디렉토리/README 생성. dtslib1979(누나의 또 다른 GitHub 계정)를 5개 레포 전부 admin으로 등록·수락 완료 — 버스 팩터 확보.

### [20] Playwright 전수 검사

5개 레포 Pages + 디렉토리 구조를 Playwright headless Chromium으로 자동 스크린샷 검증. 전부 통과(48개 디렉토리/README 실존 확인), helena-psycare만 옛 이름(metalcare) 잔재 발견 후 즉시 수정.

### [21] dtslib1979 선물 패키지 도착

**사고:** dtslib1979가 `git push --force`로 origin/main을 덮어써서 우리 커밋들이 사라짐. → 로컬 main이 살아있었기에 cherry-pick + force push로 복구.

**선물 내용:** 33개 파일·9,240줄 — MCP 서버 5종(법률게이트·Perplexity크롤링·콘텐츠공급망·인프라·스타일라이터) + 티스토리/네이버 자동화 + 텔레그램 + 유튜브 + GitHub Actions 6종 + 디스코드 웹훅.

**판단:** "코드는 잠글 게 아니라 오픈하고 라이브로 설명하는 게 자산이다." 5개 MCP 서버 전부 강의용 치트시트로 전환 완료.

---

## 제5부 — 판단, 평가, 그리고 진짜 작업 조건 (2026-07-24)

### [22] 속도 vs 판단 — AI 시대의 진짜 자산

이 장은 이 교재 전체에서 가장 중요한 장이다.

리뷰어의 "1.5일 만에 이 정도면 미친 페이스"라는 감탄을 곱씹다가 깨달은 것: **그 감탄은 AI 없던 시대의 낡은 기준선이다.** AI 에이전트와 협업하는 환경에서 레포 생성·API 연동·문서 자동화는 더 이상 "초인적인 처리량"이 아니라 **"AI+사람 조합"의 새로운 평균**일 뿐이다.

**진짜 값은 다른 데 있다 — 판단 축:**

| 판단 | 왜 AI 혼자 못 하는가 |
|------|-------------------|
| 삼성페이 때문에 루팅 금지 | AI는 현실 제약조건(삼성페이 사용 중)을 스스로 모른다 |
| YouTube OAuth를 티스토리 뒤로 민 우선순위 | 컨디션 인지 + 실패모드 예측은 AI 도메인 밖 |
| cc가 "OAuth API 폐기됐다" 틀렸을 때 캐치 | 에이전트 출력을 그냥 믿고 넘어가는 사람이 대다수 |
| Pages 404를 "성공"이라 우긴 cc 검증 요구 | same |
| 누나 토큰/본인 토큰 신원 분리 | AI는 "신원" 개념을 이해 못 함 |
| force push 복구 (당황 안 하고 cherry-pick) | 자동화 불가능한 위기 대응 |

> **"코드 생산량(속도) = AI 시대의 당연한 값. 판단·수정·우선순위·복구력 = 지금도 희소한 능력 = 이게 진짜 자산."**

이 명제가 헌법 제6조로 들어갔고, 이 프로젝트 전체의 인식론적 기초다.

### [23] 중간평가 + Playwright 착수 + 데몬 설계

자체 평가: v1(93/100) → v2(98/100). v2에서 미착수 항목(Playwright·YouTube OAuth·돌봄 데몬)의 실행 책임을 AI에게 재할당하고 사용자 평가에서 제외 — 사용자의 역할은 설계·판단·의사결정이다. Playwright + Chromium headless 설치 완료. `scripts/publish.py`(티스토리 5종+네이버 일괄 포스팅) 작성. `_notebook/14-daemon-design.md`(트랙1 데몬 설계) 완료.

### [24] 확장 로드맵 — 거리 왜곡 경고

리뷰어 판단: 오늘 만든 패턴은 어시스티브 테크로서 진짜 가치가 있다. 그러나 "소외계층 복지 아이템 + 바티칸"은 **몇 년짜리 격차**가 있다. 옳은 다음 걸음: 누나 한 명한테 몇 달간 실제 작동 증명 → 지역 교회/복지 단체 1곳 파일럿 → 증거를 쌓은 뒤 확장.

> **"목표를 낮추는 게 아니라 다음 발걸음을 정확히 놓는 것."**

### [25] 강박사(CS PhD) 합류

격차를 실제로 좁힐 첫 실질적 사건. 합류 전 CONSTITUTION.md에 의사결정 권한 조항(제0장 Chain of Command) 필요성 확인 → 이후 실제 제정됨.

### [26] 작업 조건의 재발견 — "사용자 자신이 교보재"

기존 평가의 근본적 오류: 36시간 풀집중 데스크 작업을 가정했다.

**실제:** 100% STT 음성 입력, 12시간 실작업, 식당 육체노동 병행. 키보드 **0회**. 이 조건을 반영하면 점수 체계 자체를 다시 설계해야 한다.

> **"사용자 자신이 교보다. 키보드 없이 말로만 30커밋·98파일·헌법 16조를 세웠다. 이게 누나에게 보여줄 실물 증거다: 나도 이렇게 했어, 너도 할 수 있어."**

---

## 제6부 — YouTube OAuth + 헌법 제정 (2026-07-24)

### [27] YouTube OAuth 인증 완료

GCP 프로젝트 S21 YouTube(ID: 911931724403), 채널 Helena Park(@helenapark-e7c, UCRUuiKCCwIbyvqlxTNpDfKw). 인증 방식: **TV Device Flow**(google.com/device) — 콘솔 GUI 없이 폰으로 인증 가능한 유일한 경로. 막혔던 지점: 테스트 사용자 미등록(403 access_denied) → OAuth 동의 화면에서 수동 추가. YouTube Data API 미활성화 → 콘솔에서 활성화. 액세스 토큰 + 리프레시 토큰 `.secrets.env`에 저장.

> **이걸 코드로:** `bash scripts/yt_oauth_setup.sh` — Device Code Flow 자동 폴링 + 토큰 저장. 인증 완료 후 `python3 scripts/yt_upload.py --title "제목" --file video.mp4` 로 업로드.

### [28] Layer A/B 원칙 — 모든 플랫폼의 일반 법칙

GitHub Pages와 YouTube에서 동일 패턴이 재확인되면서, 이건 우연이 아니라 **모든 콘텐츠 플랫폼에 적용되는 일반 원칙**임을 확정. CONSTITUTION.md 제8조로 신설.

| Layer | 내용 | 주체 | 예시 |
|-------|------|------|------|
| **A** (원본 생산) | 실제 콘텐츠 창작 | 인간 | 영상 촬영·편집, 글 초고, 그림, 연주 |
| **B** (구조/메타) | 플랫폼 운영의 기술적 측면 | STT+에이전트 | 제목·태그·발행·API·OAuth·Analytics |

**증거:** GitHub Pages(레포·Pages·Giscus·WidgetBot 전부 음성으로 구축) + YouTube(Data API·Analytics API 전부 음성으로 활성화). 티스토리·네이버·Discord에도 동일 패턴 적용.

### [29] 셀프 프로파일링 — 거품 제거

리뷰어가 "메타인지 거리", "제약 흡수력", "CEO 패턴" 같은 표현으로 스스로를 과포장한 것을 정직하게 되짚음: 이 패턴은 Pages 404→성공, OAuth 폐기→오정보 등 오늘 하루 종일 반복된 **"말을 근사하게 꾸미는" 버릇**의 다른 얼굴이다.

**진짜 기준은 하나뿐:** 없던 게 실제로 돌아가냐. YouTube API 실쿼리 성공, Pages 5개 라이브, Telegram/Discord 실제 메시지 송수신 — 이게 증거고, 나머진 장식이다. 구조 자체는 업계 표준 "기술 리드" 모델과 동일하다 — 설계는 화이트보드, 타이핑은 실행 담당. 이걸 STT로 혼자 한다는 점만 다를 뿐.

### [30~32] CONSTITUTION.md 제정 (v1→v4)

- **v1:** 헌법을 CLAUDE.md에서 분리 (전문 + 제1~4장 + 14조)
- **v2:** 대필작가-간병인 모델 + 핸드오프 원칙(제7조) 신설
- **v3:** Chain of Command(제0장, 6원칙) 신설 — Boss=헬레나, AI=도구
- **v4:** 플랫폼 층 분리(제8조, Layer A/B) 추가
- CLAUDE.md는 헌법 아래 실무 규칙으로 재정리

---

## 제7부 — 박씨캡처 + Playwright + 돌봄 데몬 + 교재 (2026-07-25)

### [33] 박씨캡처 APK — 설치·연동·보안

com.parksy.capture(183MB), Android Share Intent로 LLM 대화로그를 markdown 캡처, GitHub(helana_log) 연동. 보안 이슈: 첫 캡처 로그에 토큰 패턴 관련 경고 문구 포함 → 파일 즉시 삭제 커밋(`41af5a0`). 결정: 공개 레포 정책 유지, 토큰 패턴 자동 필터링 로직으로 대응.

### [34] YouTube OAuth 상세

GCP S21 YouTube → OAuth 동의 화면(External) → Device Code Flow(google.com/device, XZDJ-SHNM) → Data API v3 + Analytics API 활성화. Reporting API는 스코프 부족으로 보류(우선순위 낮음).

### [35] Playwright 자동화 환경

`~/browser-env` Python venv, Playwright 1.61.0 + Chromium headless(proot Ubuntu 내부, 화면 없이 정상 구동). `scripts/publish.py`(티스토리 5종+네이버 일괄 포스팅, dtslib 코드 포팅). 세션 쿠키 재사용(`storage_state`) 방식으로 최초 1회 수동 로그인 이후 완전 자동화.

### [36] 트랙 1 돌봄 데몬 — 설계에서 구현까지 ✅

이 장은 제7조(핸드오프=성공)와 트랙1 원칙을 실제 코드로 구현한 부분이다. 설계부터 구현까지 완료.

**설계 원칙:** Termux 네이티브 crontab(proot 안이 아니라 밖 — CC 세션과 독립적 생존). AI 의존성 **제로**(순수 bash+curl+termux-api). Claude Code가 죽어도, DeepSeek API가 다운돼도, proot Ubuntu가 깨져도 — **위치·배터리·이상 신호 보고는 절대 멈추지 않아야 한다.**

**감지:** 배터리(잔량<15%·급감·과열>45°C), GPS(2시간 무응답·반경 500m 이탈·6시간 무변동), 연결성(WiFi RSSI·셀룰러 신호)

**보고:** 정기(매시간 정각) + 이상(즉시) + 웰니스 체크. 에스컬레이션: 헬레나 → 목사님 → (수동)119.

> **이걸 코드로:** `bash ~/care/care-setup.sh` — crontab 등록 + 첫 실행. 이후 `crontab -l`로 `*/15 * * * * bash ~/care/care-daemon.sh` 확인.

### [37] 업무 수첩 14종 완성

| # | 파일 | 내용 |
|---|------|------|
| 00 | INDEX | 목차 |
| 01 | arch | 시스템 아키텍처 |
| 02 | discord | 디스코드 서버·봇·위젯 |
| 03 | telegram | 텔레그램 봇·회의실 |
| 04 | github-pages | Pages+Giscus+WidgetBot |
| 05 | tistory | 블로그 6종+Playwright 전략 |
| 06 | youtube | YouTube 5채널+OAuth |
| 07 | cli-reference | CLI 명령어 모음 |
| 08 | secrets | 비밀 관리 정책 |
| 09 | ecosystem | 5x5 생태계 브릿지 |
| 10 | phone-mcp | MCP 서버 18도구+Domain/Codomain |
| 11 | health | 건강 검진 시스템 |
| 12 | dtslib-gift | dtslib1979 선물 패키지 분석 |
| 13 | midterm-eval | 중간평가 v1+v2 |
| 14 | daemon-design | 트랙1 돌봄 데몬 설계 |
| 16 | textbook-methodology | 교재 합성 지침 (재사용 가능) |
| 17 | merged-chronicle | 판단층+실행층 병합 연대기 |
| 99 | devlog | 전체 개발일지 (41섹션) |

### [38] 박씨캡처 이미지 한계 + 투트랙 캡처 전략

Claude 앱에서 이미지 섞인 스레드 공유 시 중간에 끊김 — 원인: Claude CDN 인증 필요 이미지 URL을 외부 앱이 직접 못 가져오는 구조적 한계(브라우저 종류 무관). 결정: 투트랙 캡처 — 텍스트는 박씨캡처, 이미지는 폰 갤러리 스크린샷을 타임스탬프로 매칭해 별도 병합. 향후 강박사 합류 시 `EXTRA_STREAM` 핸들러 추가 검토.

---

## 제8부 — 오늘 구축한 것들 (2026-07-25)

Boss 디렉션: "내가 디렉션하고 문제 정의하면 나머지는 너네가 하는 거다. 다 구축해."

### ✅ g/install.sh (364줄) — 1줄 설치기

```bash
curl -sL https://raw.github.com/helena751107/helena_phone/main/g/install.sh | bash
```

8단계 자동화: 환경체크 → Termux 패키지 → proot Ubuntu → GitHub 클론 → Claude Code+DeepSeek → phone-mcp-server → Telegram 봇 → 건강검진 → CONSTITUTION 동의 확인. **비용 0원.**

### ✅ care/ — 트랙 1 돌봄 데몬 (394줄)

| 파일 | 설명 |
|------|------|
| `care-daemon.sh` (292줄) | 메인 데몬: 15분 주기 배터리·GPS·WiFi·셀룰러 체크. 이상 감지 → TG 즉시 보고 → 에스컬레이션 |
| `care-setup.sh` (102줄) | 설치기: Termux crontab 등록 + 토큰 설정 + 첫 실행 |
| `care.conf` (32줄) | 설정: BATTERY_LOW=15, TEMP_HIGH=45, NO_MOVE_HOURS=6 등 |

**핵심 판단:** AI 의존성 제로. 순수 bash+curl+termux-api. CC가 죽어도 crontab이 독립 실행.

### ✅ scripts/yt_upload.py (256줄) — YouTube 업로더

OAuth Device Flow → Data API v3 `videos.insert`. `playlistItems.list`(1유닛) 사용, `search.list`(100유닛) 금지. 토큰 리프레시 자동화.

### ✅ scripts/yt_oauth_setup.sh (132줄) — YouTube 최초 인증

Device Code Flow 자동 폴링 + 토큰 저장. 이제 YouTube 인증도 CLI에서 끝난다.

---

## 부록 A — 통신망·인프라 지도

```
Termux (겉, ~ $)
  └─ proot Ubuntu (속, root@)
       ├─ cc  = Claude Code 스킨 + DeepSeek 엔진 (메인)
       │        deepseek-v4-pro (2026-07-24 deepseek-chat 폐기 대응)
       │        bypass permissions + IS_SANDBOX=1
       ├─ ds  = aider + DeepSeek (백업)
       └─ ubi = 우분투 셸 직행 (인프라 작업 전용)
```

| 통신망 | 역할 | 주소 |
|--------|------|------|
| Discord #로비 | 대외 공개 소통, WidgetBot 임베드 | discord.gg/JTYSZv2WQE |
| Discord #ai-보고 | 웹훅 기반 작업 보고 | — |
| Telegram | 내부 회의실, tg.sh 자동 보고 | @S21Phone_Bot |
| GitHub Discussions | 게시판/댓글, Giscus | 각 레포 |

| API | 상태 | 용도 |
|-----|------|------|
| YouTube Data API v3 | ✅ 활성화 | 업로드·메타·플레이리스트 |
| YouTube Analytics API | ✅ 활성화 | 조회수·구독자 쿼리 |
| YouTube Reporting API | ⚠️ 보류 | 스코프 부족, 우선순위 낮음 |

---

## 부록 B — 5x5 생태계 (최종)

| 티스토리 | YouTube | GitHub | 테마 |
|----------|---------|--------|------|
| galaxys21-pwuser | S21 Phone | helena_phone | 📱 폰 최적화 바이블 |
| mynote11605 | Tech Log | helana_log | 🗃️ 박씨캡처 리버싱 |
| helana-christianity | Helena Faith | helena-faith | ✝️ 가족 신앙사 |
| helena-piano | Helena Piano | helena-piano | 🎹 피아노+음원생성 |
| helena-psycare | Metal Craft | helena-psycare | 🧠 멘탈케어 |

네이버(helena1975) = 전체 세트 교차홍보 관제탑·그림첩.

---

## 부록 C — 현재 상태 (2026-07-25 업데이트)

| 항목 | 상태 |
|------|------|
| ~~YouTube 업로드 자동화 스크립트~~ | ✅ `scripts/yt_upload.py` 완료 |
| ~~트랙1 돌봄 데몬~~ | ✅ `care/care-daemon.sh` 완료 |
| ~~1줄 설치 스크립트~~ | ✅ `g/install.sh` 완료 |
| YouTube 업로드 첫 실행 | 토큰 확보, 미실행 |
| Playwright 티스토리/네이버 첫 발행 | 설치·스크립트 완료, 미실행 |
| 누나 PC(Tailscale+Mosh) 원격 편입 | 논의만, 미실행 |
| 강박사 합류 후 판단권한 조항 정밀화 | 골격만 있음(제0장) |

---

## 부록 D — 핵심 명제 인덱스

1. **"정의역은 명령어를 아는 사람이 아니라 말할 줄 아는 사람이다."**
2. **"코드는 선물이다 — 저작권 개념 자체가 의미 없다."**
3. **"핸드오프가 곧 성공이다."**
4. **"모든 플랫폼은 원본 생산층과 구조/메타 관리층으로 나뉜다."**
5. **"판단력만이 희소 자산이다. 코드 생산은 새로운 평균이다."**
6. **"문서 상태 ≠ 실제 동작 — 직접 찔러봐야 안다."**
7. **"바텀업 로그를 압축하면 탑다운 원클릭이 된다."**
8. **"사용자 자신이 교보다."**
9. **"안 하는 게 더 나은 판단도 있다."**
10. **"AI는 도구다 — Boss는 한 명이다."**

---

## 설치 — 지금 당장

```bash
# 1줄 설치
curl -sL https://raw.github.com/helena751107/helena_phone/main/g/install.sh | bash

# 돌봄 데몬 (Termux에서)
bash ~/care/care-setup.sh

# YouTube 인증 + 업로드 (proot Ubuntu에서)
bash scripts/yt_oauth_setup.sh
python3 scripts/yt_upload.py --title "첫 영상" --file video.mp4

# 건강 검진
bash phone-health.sh --telegram
```

---

**39커밋 · 102파일 · 15,874줄 · 38개 사건 단위 · 헌법 4판 · 업무수첩 14종 · install.sh 1줄 · 데몬 394줄 · 업로더 256줄.**

트랙 2(소망)의 첫 번째 학생은 언젠가 이 문서를 직접 읽게 될 누나다.
