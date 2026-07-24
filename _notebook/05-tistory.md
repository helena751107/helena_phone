# 블로그 포트폴리오 + 자동화 전략

## 블로그 목록

### 티스토리 5종 세트

| 번호 | 이름 | URL | 주제 |
|------|------|-----|------|
| 1 | My Note | `mynote11605.tistory.com` | 개인 메모/기술 노트 |
| 2 | Helana Christianity | `helana-christianity.tistory.com` | 기독교/신앙 |
| 3 | Helena Piano | `helena-piano.tistory.com` | 피아노/음악 |
| 4 | Galaxy S21 PWUser | `galaxys21-pwuser.tistory.com` | S21 폰 활용/사용자 가이드 |
| 5 | Helena Metal Care | `helena-metalcare.tistory.com` | 금속 케어/공예 |

### 네이버 블로그

| 이름 | URL | 성격 |
|------|-----|------|
| Helena Park / YK Park | `m.blog.naver.com/helena1975` | 🏛️ **관저탑** — 대중 홍보용 그림첩 |

## 생성 일자

- 2026-07-24: 티스토리 5개 + 네이버 1개 계정 정리 완료

---

## 자동화 전략 (리서치 기반)

### 티스토리 — 공식 API ❌

| 항목 | 내용 |
|------|------|
| **공식 Open API** | **2024년 2월부로 완전 종료** (notice.tistory.com/2664) |
| 종료 사유 | API 기반 자동 등록 스팸이 과도하게 발생 |
| **현재 자동화 방법** | Playwright/Selenium **Headless 브라우저**로 글쓰기 페이지 DOM 직접 조작 |

### 네이버 블로그 — 공식 API ❌

| 항목 | 내용 |
|------|------|
| **공식 포스팅 API** | **원래부터 존재한 적 없음** |
| **현재 자동화 방법** | Playwright Headless 브라우저 + **storage_state(쿠키) 재사용** 방식이 표준 |
| 참고 도구 | `@oddeye/naver-blog-mcp` — MCP 기반 네이버 블로그 자동화 (Playwright 내장) |

### 공통 자동화 방식: Headless Browser (Playwright)

두 플랫폼 모두 공식 API가 없으므로, 유일한 방법은 **Headless Chromium + Playwright**를 통한 브라우저 자동화

```
proot Ubuntu (CLI only, no display)
       ↓
Playwright + Chromium headless (화면 없이 DOM 조작)
       ↓
  ① 세션 저장: 수동 1회 로그인 → storage_state 저장
  ② 세션 복원: 저장된 쿠키로 로그인 생략 → 글쓰기 자동화
  ③ 발행 완료: tg.sh 로 텔레그램 보고
```

### Playwright 설치

```bash
apt install -y python3-venv fonts-nanum
python3 -m venv ~/browser-env
~/browser-env/bin/pip install playwright
~/browser-env/bin/playwright install --with-deps chromium
```

### 세션 저장/재사용 구조

```python
# ① 최초 1회: 수동 로그인 후 세션 저장 (headful 필요시 로컬에서 실행)
context.storage_state(path=".naver_session.json")

# ② 이후: headless로 세션만 복원하여 자동화
context = await browser.new_context(storage_state=".naver_session.json")
```

### 네이버 주의사항

- ID/PW 자동 로그인은 캡차/2FA 차단 위험 높음
- **세션 쿠키 재사용이 정석** (1~3개월 유효)
- 해외 IP 차단 가능성 → 국내 IP 권장
- 일일 발행 제한: 안전하게 5개 이하 권장

## 참고 링크

- 티스토리 종료 공지: `notice.tistory.com/2664`
- 네이버 블로그 MCP: `npmjs.com/package/@oddeye/naver-blog-mcp`
- Playwright 쿠키 재사용: `dev.to/junhee916` (2026)
