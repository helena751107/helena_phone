# 전체 생태계 브릿지 테이블

> 2026-07-24 기준 전체 채널/레포/플랫폼 매칭
> "YouTube 채널 = 티스토리와 1:1 매칭. 네이버 = 관저탑/그림첩. _notebook = History/Making film/로고 아카이브"

## 마스터 브릿지

| 도메인 | 티스토리 | YouTube 채널 | GitHub 레포 | 역할 | 레포 상태 |
|--------|---------|-------------|------------|------|----------|
| 📱 **테크/S21** | `galaxys21-pwuser` | S21 Phone Tech | `helena_phone` | 메인 워크스테이션 | ✅ 있음 |
| 📝 **기술노트** | `mynote11605` | Helena Tech Log | `helana_log` | 학습/기록 | ✅ 있음 |
| ✝️ **신앙** | `helana-christianity` | Helana Faith | _(helana-faith)_ | 영성 콘텐츠 | ⏳ 필요 |
| 🎹 **피아노** | `helena-piano` | Helena Piano | _(helena-piano)_ | 음악/연주 | ⏳ 필요 |
| 🔧 **금속케어** | `helena-metalcare` | Helena Metal Craft | _(helena-metalcare)_ | 공예/메이킹 필름 | ⏳ 필요 |

## 특수 플랫폼

| 플랫폼 | 계정/위치 | 성격 |
|--------|----------|------|
| 🌐 **네이버 블로그** | `m.blog.naver.com/helena1975` | 🏛️ **관저탑** — 대중 홍보용 그림첩. 모든 채널의 교차 홍보 게이트웨이. 사진/이미지 중심 |
| 🎬 **History / Making Film** | `_notebook/` | 🏗️ **기록 보관소** — 메이킹 필름 + 로고 + 구축 과정 히스토리. GitHub에 저장됨 |
| 📹 **YouTube 공통** | `@HelenaPark-e7c` | 루트 채널. 5개 서브채널로 분화 예정 |

## 레포 현황 및 필요량

```
현재:  helena_phone + helana_log = 2개
필요:  helena-faith + helena-piano + helena-metalcare = 3개 추가
합계:  5개 (티스토리 5종과 1:1 매칭)
```

## 전체 구조도

```
                    🌐 네이버 (관저탑/그림첩)
                    대중 홍보용 이미지 게이트웨이
                          ↑
    ┌──────────┬──────────┬┴──────────┬──────────┬──────────┐
    │          │          │           │          │          │
 S21 테크   기술노트    신앙       피아노     금속케어
    │          │          │           │          │
    ├ YouTube  ├ YouTube  ├ YouTube   ├ YouTube  ├ YouTube  ─┐
    ├ GitHub   ├ GitHub   ├ GitHub    ├ GitHub   ├ GitHub   ─┤
    └ Tistory  └ Tistory  └ Tistory   └ Tistory  └ Tistory  ─┤
         │          │          │           │          │       │
         └──────────┴──────────┴───────────┴──────────┘       │
                              │                               │
                      🎬 _notebook/                        로고
                     (History/Making film)                아카이브
```

## YouTube 채널 — 티스토리 1:1 매칭

| 티스토리 블로그 | YouTube 채널 (예상명) | GitHub 레포 | 콘텐츠 타입 |
|----------------|---------------------|------------|------------|
| `galaxys21-pwuser` | **S21 Phone** | `helena_phone` | 폰 셋업 / 코딩 / 워크스테이션 |
| `mynote11605` | **Helena Tech Log** | `helana_log` | 개발 / 기술 튜토리얼 |
| `helana-christianity` | **Helana Faith** | _(helana-faith)_ | 말씀 / 신앙 / 묵상 |
| `helena-piano` | **Helena Piano** | _(helena-piano)_ | 연주 커버 / 피아노 레슨 / 음악 |
| `helena-metalcare` | **Helena Metal Craft** | _(helena-metalcare)_ | 금속 공예 / 메이킹 필름 / 제작 |

## 플랫폼별 성격 요약

| 플랫폼 | 성격 |
|--------|------|
| **GitHub 레포** | 각 채널의 소스 코드 + 설정 + 컨텐츠 저장소 |
| **GitHub Pages** | 랜딩 페이지 + Giscus 게시판 |
| **YouTube** | 영상 콘텐츠 발행 — 티스토리와 연동 |
| **티스토리** | 글/이미지 위주 블로그 — YouTube와 1:1 매칭 |
| **네이버** | 🏛️ **관저탑** — 대중 대상 그림첩. 모든 결과물의 교차 홍보 |
| **_notebook/** | 🏗️ **구축 History** — Making film + 로고 기록
