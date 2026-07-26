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

## AI 에이전트 3종
| 호출 | 에이전트 | 역할 | 비용 |
|------|---------|------|------|
| `cc` | Claude Code (DeepSeek) | 코드·문서·자동화·GitHub·TG | $0 |
| `grok` | Grok CLI (xAI SuperGrok) | 시각·Naver·이미지·클립·채팅검색 | 45,000원/월 |
| `ds` / `dsflash` | Aider (DeepSeek Pro/Flash) | 보조 코딩·자동화 루프 | 포함 |

> Termux: `grok` / `groklogin` / `grokc` / `agent` · `ds`는 `scripts/ds.sh` 래퍼 사용.  
> 예전 `gr`/`grlogin`/`grc` 호환 유지.
## AI 에이전트 규칙
- 세션 시작 시 CONSTITUTION.md → CLAUDE.md 순으로 참고할 것
- AI 출력은 전부 1차 가설 — 검증 없이 수용하지 말 것
- 모든 설정 변경 전후로 기록을 남길 것

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
├── Claude Code (DeepSeek Radar) — 메인 코딩
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
