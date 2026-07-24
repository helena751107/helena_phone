# S21 Phone — 실무 규칙

> ⚠️ **작업 시작 전 반드시 `CONSTITUTION.md`를 먼저 읽을 것.**
> 이 문서는 CONSTITUTION.md 아래에서 실제 작업에 적용되는 실무 규칙이다.
> 목적·불변 원칙·신원 규칙은 CONSTITUTION.md에, 작업 방법은 여기에.

---

## 작업 원칙
- **커밋 자주, 작게**: 기능 단위로 쪼개서 커밋
- **설명 남겨라**: "왜"를 커밋 메시지에 포함
- **깨져도 괜찮다**: 미션 A에 한함. 미션 B는 절대 안 깨지는 게 유일한 기준.
- **스캐폴드 우선**: 일단 작동, 나중에 개선

## Git 작업
- 작업 전 `git pull`로 최신 상태 확인
- 커밋 메시지는 한글/영문 혼용 가능, 간결하게
- `git push --force`는 원격이 로컬보다 뒤처진 게 확실할 때만. 함부로 쓰지 말 것.
- 완료 후 `git push` 자동 실행

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

## 파일 구조
- `CONSTITUTION.md` = 헌법 (목적, 불변 원칙, 신원) — **무엇을, 왜**
- `CLAUDE.md` = 실무 규칙 (방법, 절차) — **어떻게**
- `index.html` = 랜딩 페이지 (루트)
- `_notebook/` = 업무 수첩/개발일지
- `notebook/` = HTML 변환 문서
- `configs/` = 설정 파일
- `scripts/` = 자동화 스크립트
- `.github/workflows/` = CI/CD
- `mcp-servers/` = MCP 서버 모음
- `tistory-naver/` = 블로그 자동화
- `telegram/` = 텔레그램 연동
- `google-api/` = YouTube/Google API
- `discord/` = 디스코드 연동

## 현재 인프라

```
📱 S21 (Android + Termux + proot Ubuntu)
├── Claude Code (DeepSeek Radar)
├── phone-mcp-server (18 도구, 포트 3456)
├── 5개 GitHub 레포 → Pages + Giscus + WidgetBot
├── Discord S21 Phone 서버 (#로비, #ai-보고)
├── Telegram @S21Phone_Bot (tg.sh 보고)
├── 티스토리 5종 (Playwright 발주 대기)
└── YouTube 5채널 (설계 완료, OAuth 대기)
```
