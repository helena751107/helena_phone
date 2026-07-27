---
date: 2026-07-27
agent: Grok
mark: _Grok
type: designer-workpad
status: active
role: 웹 디자이너 업무 수첩
---

# 웹 디자이너 업무 수첩 · `_Grok`

> Boss 요청: 문서↔웹페이지 브릿지 + 5레포 통일 웹 표면.  
> 이 파일이 **디자이너 레인 현황판(workpad)** 이다.

---

## 1. 역할 리마인드

| 직함 | 마크 | 이 수첩에서 |
|------|------|-------------|
| **웹 디자이너** | `_Grok` | 랜딩·문서 HTML·톤·아이콘·커버리지·브릿지 |
| 작업 반장 | `_Aider` | 패치 루프 시공 |
| 감사 | `_Claude` | (미설치) 품질 반려 |

명령:
```bash
python3 scripts/check_webpages_Grok.py      # phone 수첩 갭
python3 scripts/build_webzine.py            # phone md→html
python3 scripts/build_satellite_docs_Grok.py  # 위성 4종 md→html
```

---

## 2. 5레포 현황 (2026-07-27 감사)

### helena_phone (허브)
| 항목 | 상태 |
|------|------|
| 랜딩 | ✅ A급 웹진 · 아코디언 접힘 · 모바일 거터 22px |
| 수첩 `_notebook` | ✅ **gap_count=0** (45 md → html) |
| 웹진 catalog | ✅ ~86 페이지 |
| 커버리지 앱 | ✅ `notebook/webpage-coverage.html` |
| 디자이너 문서 | ✅ 31 roles · 33 coverage · 36 PM비교 · 37 백서 · **38 workpad(본문)** |

### helana_log (행정 대화록)
| 항목 | 상태 |
|------|------|
| 랜딩 | ✅ 초A · teal |
| docs/* | ✅ **통일 문서 웹페이지** (IDENTITY, METHOD, tracks, dialogue…) |
| Docs hub | ✅ `docs/index.html` |
| Pages bridge | ✅ `pages/index.html` |
| CLAUDE / logs | ✅ html 브릿지 |

### helana-faith / helena-piano / helena-psycare
| 항목 | 상태 |
|------|------|
| 랜딩 | ✅ 각 브랜드 초A |
| README · CLAUDE | ✅ html |
| Pages bridge | ✅ `pages/index.html` |
| 추가 본문 docs | △ 아직 md 적음 (랜딩이 주 표면) |

---

## 3. 브릿지 규칙 (통일성)

1. **md가 생기면 같은 stem의 html** (phone: `build_webzine` / 위성: `build_satellite_docs_Grok`)  
2. 문서 HTML 공통: dark/light · spine · 검색 · h2 접기 · 모바일 gutter 22px · 허브 링크  
3. 액센트: Log teal · Faith gold · Piano lilac · PsyCare coral · Phone gold  
4. 랜딩 nav에 **Docs / pages** 링크  
5. 보고: 갭 있으면 빌드 후 `tg.sh`

---

## 4. 라이브 URL 맵

| 레포 | Landing | Docs bridge |
|------|---------|-------------|
| phone | [/helena_phone/](https://helena751107.github.io/helena_phone/) | [archive](https://helena751107.github.io/helena_phone/archive.html) · [coverage app](https://helena751107.github.io/helena_phone/notebook/webpage-coverage.html) |
| log | [/helana_log/](https://helena751107.github.io/helana_log/) | [docs/](https://helena751107.github.io/helana_log/docs/) · [pages/](https://helena751107.github.io/helana_log/pages/) |
| faith | [/helana-faith/](https://helena751107.github.io/helana-faith/) | [pages/](https://helena751107.github.io/helana-faith/pages/) |
| piano | [/helena-piano/](https://helena751107.github.io/helena-piano/) | [pages/](https://helena751107.github.io/helena-piano/pages/) |
| psycare | [/helena-psycare/](https://helena751107.github.io/helena-psycare/) | [pages/](https://helena751107.github.io/helena-psycare/pages/) |

---

## 5. 이번 작업 체크

- [x] 5레포 md 인벤토리  
- [x] phone gap 0 유지  
- [x] log docs 전부 html  
- [x] faith/piano/psycare README·CLAUDE html  
- [x] 통일 템플릿 빌더 스크립트  
- [x] 디자이너 workpad 문서화  
- [ ] 텔레그램 보고 (전송)  
- [ ] push 위성 4 + phone  

---

## 6. 다음 (백로그)

- 위성에 본문 docs가 늘면 같은 빌더로 재생성  
- phone 랜딩 library에 위성 Docs 카드  
- orphan `53-self-eval.html` 정리 여부 Boss 결정  

*웹 디자이너 업무 수첩 · _Grok · 2026-07-27*
