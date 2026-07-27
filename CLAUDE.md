# S21 Phone — 실무 규칙

> ⚠️ **작업 시작 전 반드시 `CONSTITUTION.md`를 먼저 읽을 것.**
> 이 문서는 CONSTITUTION.md 아래에서 실제 작업에 적용되는 실무 규칙이다.
> 목적·불변 원칙·신원 규칙은 CONSTITUTION.md에, 작업 방법은 여기에.

---

## 작업 원칙
- **커밋 자주, 작게**: 기능 단위로 쪼개서 커밋
- **설명 남겨라**: "왜"를 커밋 메시지에 포함
- **깨져도 괜찮다**: 트랙 2(소망)에 한함. 트랙 1(돌봄)은 절대 안 깨지는 게 유일한 기준.
- **스캐폴드 우선**: 일단 작동, 나중에 개선. Grok 80% 드래프트 → Claude Code 100% 완성.

## Git 작업
- 작업 전 `git pull`로 최신 상태 확인
- 커밋 메시지는 한글/영문 혼용 가능, 간결하게
- `git push --force`는 원격이 로컬보다 뒤처진 게 확실할 때만. 함부로 쓰지 말 것.
- 완료 후 `git push` 자동 실행

## AI 에이전트 3종 — 직함 (Boss 2026-07-26)

| 호출 | 마크 | 직함 | 영역 | 비용 | 설치 |
|------|------|------|------|------|------|
| `grok` / `gr` | **`_Grok`** | **디자이너** | 콘텐츠·비주얼·톤·랜딩·웹진·아이콘·카피·Naver 드래프트 | 45,000원/월 | ✅ |
| `ds` / `dsflash` | **`_Aider`** | **작업 반장** | 패치 큐·디프·반복 시공·실행 감독 | DeepSeek 포함 | ✅ |
| `cc` (추후) | **`_Claude`** | **감사** | 거리 둔 검증·보안·헌법·통과/보류/반려 | 정책에 따름 | ⏳ 미설치 |

**파이프:** Boss 방향 → `_Grok` 시안 → `_Aider` 시공 → `_Claude` 감사(있을 때) → Boss 최종.  
**상세:** `_notebook/31-agent-roles_Grok.md` · 마크 규약: `30-agent-file-marks.md`

> Termux: `grok` / `groklogin` / `grokc` / `agent` · `ds`는 `scripts/ds.sh` 래퍼.  
> 예전 `gr`/`grlogin`/`grc` 호환 유지.

## AI 에이전트 규칙
- 세션 시작 시 CONSTITUTION.md → CLAUDE.md → (역할) `31-agent-roles_Grok.md` 순
- AI 출력은 전부 1차 가설 — 검증 없이 수용하지 말 것
- **디자이너는 톤·구조, 반장은 패치, 감사는 「아니다」** — 직함 침범 최소화
- Claude가 아직 없으면 감사 간이 게이트는 **Boss**
- 모든 설정 변경 전후로 기록을 남길 것 (`*_Grok` / `*_Aider` / `*_Claude`)

## 텔레그램 보고 의무
작업 완료 후 보고가 필요하면:
```bash
bash ~/work/tg.sh '✅ 작업명 — 결과'
```

## 건강 검진 의무
- 세션 시작 시 또는 하드웨어 관련 작업 전후 `bash ~/work/phone-health.sh` 실행
- 결과는 자동으로 `_notebook/health/`에 타임스탬프 저장
- --telegram 플래그로 채팅 보고 가능
- 등급 A 이하(Grade B/C)면 점검 항목 확인 후 조치

## 업무일지
- 주요 작업, 판단, 전환점은 `_notebook/99-devlog.md`에 바텀업으로 기록
- AI와의 주요 대화 중 결정적 전환이 있었으면 요지 함께 기록
- 추후 `g/zero.sh`로 압축·정제 예정

## 에이전트 파일 마크 (필수 · 2026-07-26~)
- 업무 수첩·세션 메모·단독 로그를 **새로 쓸 때** 파일명 접미 마크:
  - Grok → **`_Grok`** (예: `session-2026-07-26_Grok.md`)
  - Claude Code (`cc`) → **`_Claude`**
  - Aider (`ds`) → **`_Aider`**
  - 사람 → `_Boss` / 공용 규약 → `_Shared` 또는 번호 문서 유지
- 규약 전문: `_notebook/30-agent-file-marks.md`
- 공용 `99-devlog.md` 섹션을 추가할 때는 제목 끝에 `(_Grok)` / `(_Claude)` / `(_Aider)` 표기
- **다른 에이전트 마크 파일은 덮어쓰지 말 것** — 이어서 할 거면 자기 마크 신규 파일 + handoff 체크리스트

## 웹페이지 커버리지 (Grok 상시 · 2026-07-26~)
- **`_notebook/*.md` 는 반드시 `notebook/*.html` 웹페이지**가 있어야 한다.
- `_Grok` 는 세션마다 갭을 검사하고, 없으면 빌드한다:
  ```bash
  python3 scripts/check_webpages_Grok.py   # gap_count
  python3 scripts/build_webzine.py         # 전체 생성 + coverage JSON
  ```
- 인터랙티브 앱: `notebook/webpage-coverage.html`
- 역할 문서: `_notebook/33-webpage-coverage_Grok.md`
- 문서 페이지는 공통 **웹앱 UI**(검색·접기·펼치기·본문 복사) — `assets/webzine.js`

## Paste Pipeline (네이버·티스토리 수동 발행)
- API 없는 플랫폼은 Paste Pipeline으로 대응:
  `Claude Code → TG 원고 배달 → 사람 복사붙여넣기 → 발행 (5분)`
- 티스토리 = 업무일지 (TG리포트 + git log + 스크린샷)
- 네이버 = 웹진·미끼 (Grok 80% 드래프트 → 주간 발행)

## 파일 구조
```
helena_phone/
├── CONSTITUTION.md  ← 헌법 (무엇을, 왜)
├── CLAUDE.md        ← 실무 규칙 (어떻게)
├── index.html       ← 랜딩 포털
├── _notebook/       ← 업무 수첩 (34종)
├── _textbook/       ← 완결판 교재
├── g/               ← install.sh
├── care/            ← 트랙1 돌봄 데몬
├── scripts/         ← 자동화 스크립트
├── configs/         ← 설정 파일
├── 01~05/           ← GUIDE.md 챕터
├── mcp-servers/     ← dtslib MCP
└── tistory-naver/   ← dtslib 블로그코드(보존)
```

## 현재 인프라

```
📱 S21 (Android + Termux + proot Ubuntu)
├── Claude Code (DeepSeek) — 메인 코딩
├── Grok CLI (xAI SuperGrok) — 시각·Naver
├── Aider (DeepSeek) — 보조 코딩
├── phone-mcp-server (18 도구, 포트 3456)
├── 5개 GitHub 레포 → Pages + Giscus + WidgetBot
├── Discord S21 Phone 서버 (#로비, #ai-보고)
├── Telegram @S21Phone_Bot (tg.sh 보고)
├── 티스토리 5종 (수동 업무일지)
├── YouTube @helena_phone (OAuth 완료)
└── 네이버 helena1975 (웹진·미끼)
```
