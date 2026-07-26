---
date: 2026-07-26
agent: Grok
mark: _Grok
role: designer + coverage guardian
status: active
---

# 웹페이지 커버리지 체크 — `_Grok` 상시 역할

> **Boss 지시 (2026-07-26)**  
> helena_phone 레포의 문서·수첩이 **웹페이지로 안 만들어진 것**을 파악하고 전부 페이지화.  
> 가급적 **인터랙티브 / JS 웹앱 형태**.  
> **Grok은 항상 이 갭을 체크하는 역할**을 갖는다.

---

## 1. 역할 한 줄

| 마크 | 추가 의무 |
|------|-----------|
| **`_Grok`** | 세션 시작·종료 시 **문서 ↔ HTML 갭** 검사. 갭 있으면 페이지 생성 후 빌드. |
| `_Aider` | 빌드 스크립트·CI 패치 시공 (반장) |
| `_Claude` | 감사 시 “문서만 있고 링크 죽은 페이지” 지적 |

---

## 2. SSOT · 명령

```bash
# 갭 리포트 (JSON)
python3 scripts/check_webpages_Grok.py

# 전체 웹진 빌드 (노트북 자동 발견 + coverage 기록)
python3 scripts/build_webzine.py

# 인터랙티브 앱
# https://helena751107.github.io/helena_phone/notebook/webpage-coverage.html
```

산출물:
- `assets/webpage-coverage.json` — 기계 판독 리포트  
- `assets/catalog.json` — 빌드 카탈로그  
- `notebook/*.html` — 수첩 웹페이지  
- `archive.html` — 전체 인덱스  

---

## 3. 규칙 (불변에 가깝게)

1. **`_notebook/*.md` 가 생기면 같은 이름의 `notebook/*.html` 이 있어야 한다.**  
2. 제목 맵은 `scripts/build_webzine.py` 의 `NOTEBOOK_TITLES` (없어도 자동 발견).  
3. 새 문서는 가능하면 **표·단계·체크리스트**를 넣어 웹앱 UI(접기/검색/필터)가 살게 쓴다.  
4. 순수 정적 뷰어보다 **검색·아코디언·카운터·필터**를 `assets/webzine.js` 로 공통 제공.  
5. 갭이 0이 될 때까지 “완료”라고 말하지 않는다 (커버 히어로 제외).  
6. 파일 마크: 이 역할 문서·체커·앱은 **`_Grok`**.

---

## 4. 체크리스트 (세션마다)

- [ ] `python3 scripts/check_webpages_Grok.py` → `gap_count == 0`  
- [ ] 신규 md 있으면 `build_webzine.py` 실행 후 push  
- [ ] 라이브 `notebook/…html` 200 확인 (핵심 페이지만)  
- [ ] `00-INDEX.md` 에 새 문서 링크  
- [ ] 인터랙티브 앱 페이지가 깨지지 않았는지 (`webpage-coverage.html`)

---

## 5. 2026-07-26 초기 감사 결과

| 항목 | 상태 |
|------|------|
| `_notebook/32-ecosystem-whitepaper.md` | HTML 없음 → **빌드로 생성** |
| 나머지 수첩 md | HTML 존재 |
| `notebook/53-self-eval.html` | md 없는 레거시 단독 페이지 (orphan 허용·유지) |
| 가이드 01~05 | catalog + HTML 존재 |
| 자동 발견 | build에 **glob 전체 md** 추가 |
| 공통 웹앱 UI | 검색·접기·펼치기·본문복사 (`webzine.js`) |

---

## 6. 관련

- 직함: [`31-agent-roles_Grok.md`](./31-agent-roles_Grok.md) — 디자이너 + **커버리지 가디언**  
- 마크: [`30-agent-file-marks.md`](./30-agent-file-marks.md)  
- 앱: `notebook/webpage-coverage.html`  
- 스크립트: `scripts/check_webpages_Grok.py` · `scripts/build_webzine.py`
