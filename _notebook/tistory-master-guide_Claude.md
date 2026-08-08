# 📝 티스토리 완전 정복 — 5채널 전략·자동화·파이프 총정리

> 2026-08-08 · Claude Code 종합 정리  
> 출처: `_notebook/05`, `24`, `44`, `45`, `99-devlog` · `CONSTITUTION.md` · `CLAUDE.md` · `CHRONICLE.md` · `tistory-naver/`

---

## 1. 티스토리 5종 세트

| # | 이름 | URL | 주제 | GitHub | YouTube |
|---|------|-----|------|--------|---------|
| 1 | Galaxy S21 PWUser | `galaxys21-pwuser.tistory.com` | S21 폰 개발·활용 | `helena_phone` | @helena_phone |
| 2 | My Note | `mynote11605.tistory.com` | 개인 메모·기술 노트 | `helana_log` | @helana_log |
| 3 | Helana Christianity | `helana-christianity.tistory.com` | 기독교·신앙 | `helana-faith` | Helana Faith |
| 4 | Helena Piano | `helena-piano.tistory.com` | 피아노·음악 | `helena-piano` | Helena Piano |
| 5 | Helena Metal Care | `helena-metalcare.tistory.com` | 돌봄·금속공예 | `helena-psycare` | Metal Craft |

**생태계 법칙:** 5개 티스토리 = 5개 YouTube 채널 = 5개 GitHub 레포 = **1:1:1 매칭**

---

## 2. 기술 현실 — API는 죽었다

| 장벽 | 상태 | 상세 |
|------|------|------|
| **티스토리 Open API** | ❌ 2024년 2월 완전 종료 | `notice.tistory.com/2664` — 스팸 때문에 카카오가 내림 |
| **Kakao OAuth** | ❌ KOE006 에러 | Tistory 쪽 앱 설정 문제. 자동 로그인 불가 |
| **Android Chrome 북마크릿** | ❌ 차단 | 구글 7년째 방치된 버그. JS URL 실행 불가 |
| **네이버 포스팅 API** | ❌ 원래 없음 | 애초에 존재한 적 없음 |

**시도하고 실패한 것들:**
- Playwright headless → Kakao OAuth URL 직접 구성 → KOE006
- `Kakao.Auth.authorize()` 우회 → 동일 KOE006
- Chrome 북마크릿 → 메뉴에서 차단
- `am start` Intent로 javascript URL → Android SecurityException
- Chrome cookie DB 직접 접근 → `/data/data/` sandbox 차단

---

## 3. 자동화 진화 (3단계)

### 1단계: Playwright 풀오토 (폐기) — 2026-07-24

```
proot Ubuntu (CLI only)
       ↓
Playwright + Chromium headless
       ↓
① 1회 로그인 → storage_state 저장
② 쿠키 복원 → 글쓰기 DOM 조작
③ 발행 완료 → TG 보고
```

**판정:** 기술적으로 반쪽 가능하나, 전략적으로 폐기.

### 2단계: Boss 전략 판단 — 2026-07-25

> "티스토리랑 네이버는 기를 쓰고 뚫을 필요 없다.  
> API 죽었고, 안티봇에 막히고, 북마크릿도 차단된다.  
> 여기는 업무일지·관제탑으로 사람이 직접 한다."

**확정:** 사람 수동 발행으로 방향 전환. 자동화는 GitHub·Pages·YouTube·Telegram·건강검진·돌봄데몬에 집중.

### 3단계: HTML 조각 박물관 (현재) — 2026-08-05

**전환:** 쓰레기통(스크린샷 덤프) → **HTML 조각 박물관**(인터랙티브 웹문서)

```
Boss + 무료LLM 대화
    → 요약·HTML 조각
    → 티스토리 HTML 모드 복붙
    → RSS 피드
    → helana_log 동기화
    → Claude Code 리뷰
    → GitHub Pages 승격
```

**왜 괜찮은가:**
- 공짜 LLM 대화가 증발하지 않음
- HTML 모드 = SVG·표·구조 자유로운 캔버스
- JS 포기해도 충분한 인터랙티브
- RSS로 자동 수집 → 한곳에서 리뷰
- 티스토리 = 공짜 무제한 CMS

---

## 4. Paste Pipeline — 현재 운영 방식

```
Claude Code → 텔레그램 전문 배달 → 사람 복사 → 블로그 붙여넣기 → 발행 (5분)
                      │
        YouTube + GitHub Pages = 무료 영구 CDN
```

### 왜 막을 수 없는가

| 방어 레이어 | 대응 |
|------------|------|
| API 차단 | API 전혀 사용 안 함. TG는 정식 Bot API |
| HTML 모드 제거 | 순수 텍스트 전달. 에디터가 거부 불가 |
| 안티봇 | 사람이 직접 복붙 — 모든 행동이 인간 패턴 |
| 매크로 감지 | 주 1회, 사람의 마우스/터치 조작 |
| IP 차단 | 정상 사용자 트래픽 |

### CDN 인프라 (전부 무료)

| 자산 유형 | CDN | 비용 |
|----------|-----|------|
| 이미지·문서 | GitHub Pages | $0 |
| 영상·클립 | YouTube | $0 |
| 코드·데이터 | GitHub Raw | $0 |

### 텔레그램 패키지 형식

```
[제목]
[본문 — 볼드·줄바꿈·구분선]
[📺 영상 제안]
[🖼️ 이미지 제안]
[🔗 링크 — 전체 URL]
```

---

## 5. 3층 아키텍처 (L0→L1→L2)

```
┌──────────────────────────────────────┐
│ L0  1회 사람 게이트                   │
│  로그인 캡차 · 스킨 CSS · 서식 저장    │
│  카테고리 이름 5~10개 (손 or 1회 봇)   │
└─────────────┬────────────────────────┘
              │ storageState
┌─────────────▼────────────────────────┐
│ L1  반자동 (선택)                     │
│  admin_category_seed.py  (추가만)     │
│  cookie 수명 모니터링 → TG "재로그인"  │
│  글 대량 백필 시에만 post.cjs (비정기) │
└─────────────┬────────────────────────┘
              │
┌─────────────▼────────────────────────┐
│ L2  매주 정본                         │
│  Marine Quilt Paste Pipeline          │
│  자동화 0 · 손맛 100                  │
└──────────────────────────────────────┘
```

---

## 6. 보유 코드 자산 (보존)

| 파일 | 용도 | 상태 |
|------|------|------|
| `tistory-naver/post.py` | 티스토리 Playwright 자동 포스팅 | 📦 보존 |
| `tistory-naver/post.cjs` | 네이버 SE 글쓰기 Playwright | 📦 보존 |
| `tistory-naver/login.cjs` | 쿠키·storageState 추출 | 📦 보존 |
| `tistory-naver/session_post.py` | 터미널→네이버 원클릭 파이프 | 📦 보존 |
| `tistory-naver/skin.py` | 스킨 관리 | 📦 보존 |
| `tistory-naver/NAVER_WORKBOOK_AUTOMATION.md` | 캡차·RustDesk 교훈 | 📖 참고 |
| `scripts/publish.py` | 티스토리 5종 + 네이버 일괄 포스팅 | ⏳ 미완성 |
| `scripts/save_tistory_cookie.py` | 쿠키 저장 유틸 | 📦 보존 |
| `scripts/tistory_sync.sh` | 동기화 스크립트 | 📦 보존 |
| `scripts/extract_cookie.js` | 쿠키 추출 | 📦 보존 |

---

## 7. 네이버 블로그 (헬레나 관저탑)

| 항목 | 내용 |
|------|------|
| URL | `m.blog.naver.com/helena1975` |
| 성격 | 🏛️ **관저탑** — 대중 홍보용 그림첩 |
| 발행 | 주간 Marine Quilt 수공예 |
| RSS | `rss.blog.naver.com/helena1975.xml` |
| HTML 모드 | 스마트에디터 ONE — HTML 직접 입력 가능 |

**네이버 주의사항:**
- ID/PW 자동 로그인 = 캡차·2FA 차단 위험
- 세션 쿠키 재사용이 정석 (1~3개월 유효)
- 해외 IP 차단 가능 → 국내 IP 권장
- 일일 발행 제한: 5개 이하 권장

---

## 8. 판정 매트릭스

| 질문 | 답 |
|------|----|
| API로 자동화 가능? | ❌ API 종료 |
| Playwright로 가능? | ⚠️ 기술 반쪽, 전략 비추 |
| 매주 풀오토? | ❌ 퀼트 브랜드 자살 + 계정 리스크 |
| 1회 카테고리 시드? | ✅ 쿠키 + locator로 가능 |
| 사람이 하는 게 맞나? | ✅ **업무일지·관제탑은 손맛이 브랜드** |
| 완전 무방법인가? | ❌ 아님. 방법은 있다 |

---

## 9. 핵심 인사이트

> **"자동화할 수 없는 것을 자동화하려고 기를 쓰는 대신,  
> 사람과 기계의 협업 지점을 정확히 찾아 최적화하라."**

- AI의 강점: 원고 생성·자산 준비·포맷팅
- 사람의 강점: 복사·붙여넣기·미적 판단·발행 버튼 클릭
- 둘을 분리하면 API가 없어도 파이프라인은 돈다

---

## 10. 관련 문서 맵

```
헌법·규칙
├── CONSTITUTION.md     → 티스토리 5종 = 누나의 분신
├── CLAUDE.md           → Paste Pipeline 운영 규칙
└── CHRONICLE.md        → 연대기

노트북
├── 05-tistory.md              → 블로그 6종 + Playwright 전략
├── 09-ecosystem.md            → 생태계 브릿지 (1:1:1 매칭)
├── 24-paste-pipeline.md       → Paste Pipeline 방법론
├── 44-naver-admin-automation-review_Grok.md  → Claude 지시 리뷰
├── 45-naver-admin-playwright-feasibility_Grok.md → 폰 Playwright 가능성
└── 99-devlog.md               → 전체 타임라인

코드
└── tistory-naver/             → 보존된 자동화 코드
```

---

*agent _Claude · 2026-08-08 · 전체 레포지토리 + 업무수첩 파싱 완료*
