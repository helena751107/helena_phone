# Naver Admin 자동화 가능 여부 — 폰 Playwright 1회 시드 (_Grok)

> 저장일: 2026-07-27 · agent _Grok  
> Boss 질문: “꼭 수동이냐? 자동화 방법 찾아라. 폰 안 GUI/Playwright 되냐? 한 번만 하면 되는 거 아니냐?”

---

## 1. 결론 먼저

| 질문 | 답 |
|------|----|
| 매번 손으로만 해야 하냐? | **아니요.** 카테고리 추가는 스크립트로 반복 가능 |
| Playwright로 되냐? | **된다.** 이 폰 Ubuntu에 Playwright + Chromium **이미 있음** |
| 폰 안에서 GUI 오토 되냐? | **브라우저(웹) 기준 된다.** 네이버 **앱 화면 터치 자동화**는 다른 판 (더 빡셈, 비추) |
| 한 번만 하면 되냐? | **구조 한 번 짜면**, 이후는 스크립트 재실행. 단 **쿠키 죽으면 로그인만 사람 1회** |
| 매주 발행까지 오토? | **기술은 반쯤, 전략적으로 비추** (퀼트·계정 리스크). **관리 1회 시드**와 분리 |

**한 줄:** 완전 수동 아님 · 완전 무인 아님 · **1회 시드 + 스크립트 재사용 = YES.**

---

## 2. 폰 안 자동화 = 두 갈래

```
① 웹 Playwright (권장)          ② 안드로이드 앱 GUI
   proot Ubuntu                  네이버 블로그 APK 터치
   Chromium + Playwright         UIAutomator / Appium / 손가락 APK
   PC 버전 관리 페이지 클릭       좌표·뷰 계층 깨지기 쉬움
   ✅ 이 폰에 도구 이미 있음      ❌ 유지비 지옥 · 비추
```

카테고리 관리·스킨·글쓰기 관리 = **전부 웹 관리자**  
→ **①만으로 충분.** 네이버 앱을 누르는 자동화가 아니다.  
폰에서 **웹 Playwright**를 돌리는 것이다.

### 환경 확인 (2026-07-27)

- `node` + `playwright` 패키지: OK (`/root/work/node_modules/playwright`)
- Chromium 브라우저 캐시: OK (`~/.cache/ms-playwright`)
- 기존 자산: `tistory-naver/login.cjs`, `post.cjs`, `post.py`

---

## 3. “한 번만”의 정확한 의미

```
[1회 설계]
  login (사람: 캡차) → storageState 저장
  category_seed 스크립트 작성 (이름 목록)
  실행 → 카테고리 5~10개 생성

[이후]
  스크립트만 다시 돌림 (같은 쿠키)
  쿠키 만료/로그아웃 때만 login 다시 (사람 1분)
  드래그 정렬은 여전히 손 30초~1분이 이득
```

Boss 감: “나중에 다 스크립트로 짜 버리면 된다”  
→ **카테고리 시드·설정 쪽은 YES.**

---

## 4. 가능한 것 / 빡센 것

| 작업 | 폰 Playwright | 비고 |
|------|---------------|------|
| 로그인 후 쿠키 저장 | ✅ | 캡차 뜨면 **headed + 손** (`login.cjs` 패턴) |
| 카테고리 **추가** (이름·공개) | ✅ | `get_by_text("카테고리 추가")` 등 locator |
| 글쓸 때 카테고리 **선택** | ✅ | `post.py` 이미 있음 |
| 카테고리 **드래그 순서** | ⚠️ | 가능은 한데 실패율↑ → 손 추천 |
| 스킨 CSS 붙여넣기 | ⚠️ | 1회라 손도 OK |
| 서식 저장 | ⚠️ | SE 내부 UI 복잡 → 손 1회 추천 |
| 매주 본문 자동 발행 | ⚠️기술 / ❌전략 | 퀼트 손맛·정책 |

**좌표 클릭 = 금지.** 해상도·배율에 즉시 깨짐. locator / (가능하면) XHR 재현.

---

## 5. 권장 파이프

```
1) node login.cjs  (headed, 캡차 손)     ← 사람 게이트
2) node admin_category_seed.cjs \
     --names "주간퀼트,시범,설치,판단,링크"
3) 끝. 다음부터 2)만 재실행 or 새 이름만 추가
4) 주간 글 = Marine Quilt 손바느질 (정본)
```

### 3층 구조

```
L0 사람: 캡차 로그인 · 스킨 · 서식 · (카테고리 이름 시드)
L1 반자동: 쿠키로 카테고리 "추가" 스크립트 · 쿠키 만료 시 TG "재로그인"
L2 매주: Marine Quilt Paste Pipeline only  ← 봇 넣지 마
```

---

## 6. 관련 문서

| 문서 | 역할 |
|------|------|
| `_notebook/44-naver-admin-automation-review_Grok.md` | Claude 지시 리뷰 + 방법 지도 (상세) |
| `_notebook/45-naver-admin-playwright-feasibility_Grok.md` | **이 문서** — 가능 여부 Q&A |
| `_notebook/23-naver-webzine-solution.md` | 웹진·서식 원칙 |
| `_notebook/24-paste-pipeline.md` | 주간 손 발행 |
| `naver/quilt/BOSS-CARD.md` | 퀼트 3분 설치 |
| `tistory-naver/login.cjs` | 쿠키·storageState |
| `tistory-naver/post.cjs` / `post.py` | 글쓰기 Playwright |

개발일지: `99-devlog.md` §94 (Claude 분석 + Grok 리뷰)

---

## 7. 미구현 (다음 작업 후보)

- [ ] `tistory-naver/admin_category_seed.cjs` (또는 `.py`) — 이름 배열 → 카테고리 추가
- [ ] 쿠키 만료 감지 → TG 알림
- [ ] helena1975 storageState 1회 확보 (headed 로그인)

*한 땀 한 땀 · 1회 시드는 기계, 매주 퀼트는 손 · _Grok*
