---
date: 2026-08-08
agent: Claude
mark: _Claude
type: standard
status: active
---

# 페이지 작법 표준 — md 원고 → 웹페이지 품질 규칙

> 모든 `_notebook/*.md`가 통일된 웹 UI로 번역되기 위해 지켜야 할 최소·권장·프리미엄 규칙.  
> `publishing_metrics.py`는 이 규칙을 기준으로 품질 등급을 자동 측정한다.

---

## 1. 품질 등급

| 등급 | 조건 | 허용 |
|------|------|------|
| **프리미엄 (premium)** | H1 + deck + H2≥3 + 표≥2 + 체크리스트 + 내부링크≥1 | 모든 출판물 |
| **표준 (standard)** | H1 + deck + H2≥2 + (표 or 코드블록)≥1 | 신규·유지보수 |
| **최소 (minimal)** | H1 제목만 | WIP 드래프트만 임시 허용 |

> **원칙:** 신규 페이지는 standard 이상. 기존 minimal은 주간 1개 이상 승격.

---

## 2. 요소별 작성 요령

### H1 (`# 타이틀`)
- **필수.** 모든 페이지에 딱 1개.
- 한글로 작성. "S21" 같은 코드명 허용.
- 빌드 시 `<h1>`, `<title>`, breadcrumb에 사용됨.
- 없으면 파일명 stem이 기계식 타이틀로 들어감 → 발견성 저하.

```markdown
# 좋은 예: 클라우드 비용 최적화 — 2026년 8월 기준
# 나쁜 예: cloud-cost-optimization (영문, 기계식)
```

### Deck (`> 설명문`)
- H1 바로 다음 줄에 blockquote.
- **권장 (standard 등급 필수).** 한 문장으로 페이지 내용 요약.
- 빌드 시 `meta description` + hero 아래 `.deck` 문단이 됨.
- 없으면 검색엔진 미리보기가 비어 보임.

```markdown
> 2026년 7~8월 S21 생태계 5레포의 인프라 비용과 최적화 방안을 정리한다.
```

### H2 (`## 섹션`)
- **권장 2~6개.** standard 등급은 최소 2개 필수.
- 빌드 시 accordion 섹션으로 접힘. 토글 버튼(+/-)이 자동 생성됨.
- H2가 없으면 페이지 전체가 하나의 평문 블록 — 탐색 어려움.
- H3(`###`)는 accordion 내부 소제목으로 사용.

```markdown
## 좋은 예: 클라우드 비용 현황
## 좋은 예: 최적화 적용 결과
## 나쁜 예: section-1 (의미 없는 레이블)
```

### 표 (Table)
- **권장.** 비교 데이터, 설정, 체크리스트 요약에 사용.
- 헤더 행 **필수.** 헤더 없는 표는 웹에서 정렬되지 않음.
- premium 등급은 2개 이상.

```markdown
| 항목 | Before | After | 절감 |
|------|--------|-------|------|
| GitHub Actions | 0원 | 0원 | - |
| Grok API | 45,000원 | 45,000원 | - |
```

### 코드블록 (```)
- 기술 문서에 적극 활용.
- 언어 지정 권장 (```bash, ```python, ```json 등).
- 빌드 시 monospace + syntax highlight 컨테이너로 렌더링.

### 체크리스트 (`- [ ]`)
- 액션 아이템, TODO, 진행 상황에 사용.
- 빌드 시 스타일된 체크박스로 렌더링.
- **완료된 항목은 `- [x]`로 업데이트** — 방치된 미완료 체크리스트는 신뢰도 저하.

```markdown
- [x] 빌드 스크립트 수정
- [ ] CI 게이트 추가
- [ ] 텔레그램 보고 자동화
```

### 내부 링크
- 다른 `_notebook` 페이지 참조 시 **상대경로 .md**로 작성.
- 빌드 시 `.html`로 자동 변환됨.
- **절대 URL 사용 금지** — 로컬-원격 불일치 발생.

```markdown
좋은 예: [에이전트 역할 분장](./31-agent-roles_Grok.md)
나쁜 예: [에이전트 역할](https://helena751107.github.io/helena_phone/notebook/31-agent-roles_Grok.html)
```

---

## 3. 요소 → UI 매핑

| Markdown | HTML 출력 | UI 효과 |
|----------|----------|---------|
| `# Title` | `<h1>` + `<title>` | Hero 타이틀 + 브라우저 탭 |
| `> Deck` (H1 직후 blockquote) | `<p class="deck">` + `<meta name="description">` | Hero 부제목 + SEO |
| `## Section` | Accordion `.wz-sec` > `.wz-sec-h` | 접기/펼치기 토글 |
| `### Sub` | `<h3>` | Accordion 내부 소제목 |
| `| Table |` | `<table>` + 테마 스타일 | 정렬된 데이터 표 |
| `- [ ] item` | 체크박스 | 액션 추적 |
| `` ```code``` `` | `<pre><code>` | Monospace 하이라이트 |
| `[text](./file.md)` | `<a href="./file.html">` | 내부 탐색 |
| `**bold**` | `<strong>` | 강조 |
| `*italic*` | `<em>` | 기울임 |

---

## 4. 안티패턴 (하지 말 것)

### ❌ H1 없음
```
파일이 바로 본문으로 시작하면 타이틀이 파일명 stem이 됨.
→ "70-font-bgm-fix" 같은 제목이 웹에 노출.
```

### ❌ 평문만 주르륵
```
H2 섹션 구분 없이 긴 텍스트만 있으면:
- accordion UI 미작동 → 전체가 한 덩어리
- in-page 검색이 섹션 단위로 안 됨
- TOC 자동 생성 불가
```

### ❌ 절대 URL 내부 링크
```
[문서](https://helena751107.github.io/.../file.html)
→ 로컬 개발 환경에서 클릭하면 프로덕션으로 날아감
→ 상대경로 .md로 쓰고 빌드 시 .html로 자동 변환됨
```

### ❌ 이미지 경로 상이
```
![img](/absolute/path.png) → 페이지스에서 404
![img](../assets/img.png) → 상대경로로, 실제 파일이 그 위치에 있는지 확인
```

---

## 5. 표준 템플릿

```markdown
# 페이지 제목 (한글)

> 이 페이지가 다루는 내용을 한 문장으로 요약.

## 첫 번째 섹션

핵심 내용을 여기에. 표가 필요하면:

| 항목 | 설명 | 비고 |
|------|------|------|
| A | ... | ... |
| B | ... | ... |

## 두 번째 섹션

추가 내용.

- [ ] 할 일 1
- [ ] 할 일 2

## 세 번째 섹션 (선택)

코드 예시:

```bash
echo "hello"
```

참고: [관련 문서](./31-agent-roles_Grok.md)
```

---

## 6. 품질 측정 방법

`scripts/publishing_metrics.py`는 각 md 파일을 열어 아래 항목을 검사한다:

| 항목 | 검출 방법 | 점수 |
|------|----------|------|
| H1 | `^# ` 정규식 | +1 |
| Deck | `^> ` 정규식 (H1 이후 첫 blockquote) | +1 |
| H2 구조 | `^## ` 개수 ≥ 2 | +1 |
| 표 | `|` 포함 행 2줄 이상 | +1 |
| 코드/체크 | ` ``` ` 또는 `- [ ]` 존재 | +1 |

**점수 → 등급:**
- 5점 → premium
- 3~4점 → standard
- 0~2점 → minimal

```bash
# 전체 품질 현황
python3 scripts/publishing_metrics.py

# 특정 파일 점수 확인
python3 -c "
from publishing_metrics import score_page
print(score_page('_notebook/01-arch.md'))
"
```

---

*출판부 표준문서 · agent mark `_Claude` · 2026-08-08*
