# 에이전트 파일 마크 규약 — `_Grok` · `_Claude` · `_Aider`

> 제정: 2026-07-26  
> 이유: 한 폰(S21 · Termux · proot)에서 **cc / ds / grok** 가 같은 `_notebook/` · `logs/` 를 건드린다.  
> 누가 썼는지 파일명에 안 남으면 덮어쓰기·책임 추적이 안 된다.

---

## 1. 필수 마크 (파일명)

| 에이전트 | CLI | 직함 (2026-07-26) | 파일명 마크 | 예 |
|----------|-----|-------------------|-------------|-----|
| Grok Build / SuperGrok | `grok` · `gr` | **디자이너** (콘텐츠) | **`_Grok`** | `session-2026-07-26_Grok.md` |
| Aider + DeepSeek | `ds` · `dsflash` | **작업 반장** | **`_Aider`** | `queue-fix_Aider.md` |
| Claude (추후 진입) | `cc` | **감사** | **`_Claude`** | `audit-20260726_Claude.md` |
| 사람(Boss) 직접 | — | 최종 판단 | **`_Boss`** 또는 마크 없음 | `decision-2026-07-26_Boss.md` |
| 공동·합본·규약 자체 | 여러 명 | — | **`_Shared`** | `30-agent-file-marks.md` |

역할 본문: [`31-agent-roles_Grok.md`](./31-agent-roles_Grok.md)

### 규칙

1. **에이전트가 새로 쓰는 업무 수첩·일지·세션 메모**는 파일명 끝에 반드시 `_{Agent}` 를 붙인다.  
   - 예: `webzine-icons_Grok.md` · `aider-conf_Aider.md` · `review_Claude.md`
2. **공용 번호 문서** (`01-arch.md` ~ `29-…`, `99-devlog.md`, `00-INDEX.md`)는 번호를 유지하되,  
   - 본문 섹션 헤더/푸터에 `<!-- agent: Grok -->` 또는 `**agent:** _Grok` 를 남긴다.  
   - 큰 단독 기여 블록은 가능하면 **별도 `*_Grok.md` 로 빼고** INDEX에 링크한다.
3. **덮어쓰지 말 것.** 다른 에이전트 마크 파일은 수정 전 합의. 급하면 `*_Grok_note-on-Claude.md` 처럼 자기 마크 메모를 옆에 만든다.
4. **날짜**는 `YYYY-MM-DD` 또는 `YYYYMMDD` 를 파일명 앞에/중간에 넣는 것을 권장.
5. helana_log `logs/` 날것 캡처도 동일: `DevLog_20260726_Grok.md` (행정 대화록 `docs/dialogue/` 는 트랙 코드 DW/BL/DC 우선, 에이전트 마크는 메타에).

---

## 2. 본문 메타 (권장 YAML/헤더)

```markdown
---
date: 2026-07-26
agent: Grok
mark: _Grok
cli: grok
cowork: [Aider, Claude]   # 같이 볼 대상
status: done | wip | handoff
---
```

또는 마크다운 상단 한 줄:

```markdown
> **agent:** _Grok · 2026-07-26 · handoff → _Claude / _Aider
```

---

## 3. 핸드오프

| 상황 | 방법 |
|------|------|
| Grok → Claude 로 이어서 코딩 | `*_Grok.md` 끝에 **Next for _Claude** 체크리스트 |
| Aider 가 패치만 | `*_Aider.md` 에 diff 요약 + 건드릴 파일 목록 |
| 공유 일지 | `99-devlog.md` 에 섹션 추가 시 줄 끝에 `(_Grok)` |

---

## 4. 현재 상태 점검 (2026-07-26 감사)

| 항목 | 마크 규약 준수? | 비고 |
|------|----------------|------|
| `99-devlog.md` §50–61 | 부분 | 푸터에「작성: Grok」만 있음 → 섹션에 `(_Grok)` 보강 |
| `DevLog_Grok_20260726.md` | 유사 | 언더바 위치가 앞/중간 혼용 → `DevLog_20260726_Grok.md` 로 정렬 |
| `ai-agents-cc-ds-grok-comparison-…` | 이름에 grok 포함 | 비교 문서라 Shared 성격 |
| `supergrok-community-research-…` | 부분 | 연구 주제명; 에이전트 마크와 별개 |
| `.aider.chat.history*` | Aider 전용 로그 | 파일명에 `_Aider` 없음 (도구 기본 경로) |
| `.claude/` | Claude 상태 | 도구 기본 경로 |
| **`_Grok` / `_Claude` / `_Aider` 접미 규약** | **이전에는 없음** | 본 문서에서 신설 |

---

## 5. CLI 별칭 대응

| 별칭 | 마크 |
|------|------|
| `gr` / `grok` | `_Grok` |
| `cc` | `_Claude` |
| `ds` / `dsflash` | `_Aider` |

---

*Shared 규약 문서. 에이전트는 이 파일을 읽고 자기 마크 파일을 쓴다.*
