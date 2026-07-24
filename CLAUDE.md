# S21 Phone — 작업 규칙

> 헌법: 이 문서는 AI 에이전트(Claude Code)가 이 레포지토리에서
> 자율적으로 작업할 때 따라야 할 규칙과 패턴을 정의한다.

## 작업 원칙
- **커밋 자주, 작게**: 기능 단위로 쪼개서 커밋
- **설명 남겨라**: "왜"를 커밋 메시지에 포함
- **깨져도 괜찮다**: 일단 작동, 나중에 개선

## Git 작업
- 작업 전 `git pull`로 최신 상태 확인
- 커밋 메시지는 한글/영문 혼용 가능, 간결하게
- push 전 확인할 것
- 완료 후 `git push` 자동 실행

## AI 에이전트 규칙
- 세션 시작 시 이 파일을 참고할 것
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

## 파일 구조
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
