# 🆓 GitHub 공짜 생태계 끝까지 쥐어짜기 — Boss 2026-08-05

## 결정: PC 확장은 없다

| 항목 | S21 Phone | 누나 PC | 승자 |
|------|-----------|---------|------|
| CPU | Exynos 2100 8코어 2.9GHz | Celeron 3855U 2코어 1.6GHz | **폰** (3-4배) |
| RAM | 8GB LPDDR5 | 4GB DDR3 | **폰** (2배+속도) |
| WSL2 | 불필요 (이미 리눅스) | 4GB로 불가능 | **폰** |
| 이동성 | 주머니 | 책상 | **폰** |

**결론: 폰이 메인 워크스테이션. PC는 필요 없음.**

---

## 대신 공짜로 돌릴 수 있는 것들

### GitHub Actions — 무료 2000분/월 Linux 러너

```
┌─────────────────────────────────────────┐
│          GitHub Actions (공짜)            │
│                                          │
│  ✓ cron 스케줄 (RSS 수집, 빌드)           │
│  ✓ Markdown → HTML 자동 변환              │
│  ✓ 링크 검사, 건강 체크                    │
│  ✓ 멀티레포 동기화                         │
│  ✓ TG 알림 발송                           │
│  ✓ PR 자동화·레이블·이슈 관리              │
│                                          │
│  한도: 2000분/월, 6시간/실행               │
│  현실: 이 프로젝트로는 절대 못 씀           │
└─────────────────────────────────────────┘
```

### GitHub Pages — 공짜 무제한 정적 호스팅

```
이미 쓰는 것:
  ✓ helena_phone 메인 (webzine)
  ✓ helana_log (학습 로그)
  ✓ helena-psycare (돌봄 허브)
  ✓ helana-faith (신앙 허브)
  ✓ helena-piano (연주 스튜디오)

더 쥐어짤 것:
  ✓ 모든 _notebook/*.md → HTML 자동 빌드 (Actions로)
  ✓ RSS 피드 생성 → 다른 플랫폼 연동
  ✓ JSON API 엔드포인트 (정적 .json 파일)
  ✓ 검색 인덱스 (lunr.js 정적 검색)
```

### GitHub API — 공짜 5000 req/hr

```
  ✓ 이슈·PR 자동화
  ✓ 멀티레포 상태 대시보드
  ✓ 커밋 통계·기여 그래프
  ✓ Giscus 댓글 (이미 사용 중)
```

---

## 실행 로드맵

### 1단계: GitHub Actions로 자동 빌드 파이프 (지금 당장)

```yaml
# .github/workflows/build-webzine.yml
# push할 때마다 모든 MD → HTML 자동 변환
# cron으로 매일 새벽에도 한 번
```

### 2단계: RSS → helana_log 자동 동기화 (Actions cron)

```yaml
# .github/workflows/rss-sync.yml
# 매 6시간마다 티스토리 5채널 RSS → helana_log/기자/
# 지금은 tistory_sync.sh 수동 실행 → Actions로 자동화
```

### 3단계: 상태 대시보드 (정적 JSON + Pages)

```
모든 레포 상태 한눈에:
  - 마지막 커밋
  - Pages 배포 상태
  - Actions 성공/실패
  - RSS 동기화 상태
```

### 4단계: PC = Thin Client (옵션, 정 필요하면)

```
PC는 Tailscale + SSH만.
폰이 모든 작업 수행.
PC는 큰 화면 + 키보드로 폰에 SSH 접속.
WSL 절대 금지. Python Native도 굳이 필요 없음.
```

---

## 안 되는 것 (공짜 한계 인정)

| 안 되는 것 | 이유 | 대안 |
|-----------|------|------|
| 백엔드 서버 | Pages = 정적 only | Firebase, Supabase 무료 티어 |
| 데이터베이스 |同上 | JSON 파일 + GitHub API |
| 사용자 인증 |同上 | Giscus OAuth, Firebase Auth |
| 실시간 처리 | Actions 최소 5분 간격 | 폰에서 직접 |
| 대용량 저장 | 1GB 권장 | YouTube, Tistory로 분산 |
| GPU 작업 | 당연히 | 폰이 더 나음 (ISP) |

---

## 현재 인프라 재평가

```
✅ 공짜로 잘 돌아가는 것:
  GitHub Pages 5종 — 무제한 정적 호스팅
  Telegram Bot — 무제한 메시지
  Discord — 무제한 커뮤니티
  YouTube — 무제한 동영상
  Tistory — 무제한 블로그
  Giscus — 무료 댓글
  WidgetBot — 무료 디스코드 임베드

⏳ Actions로 자동화할 것:
  MD → HTML 빌드
  RSS 동기화
  상태 체크

❌ 포기:
  PC WSL2 확장
  로컬 서버
  Docker
```

---

## 핵심 원칙

1. **폰이 메인 컴퓨터다.** PC보다 3-4배 빠르다.
2. **GitHub가 유일한 서버다.** Actions + Pages = 공짜 풀스택.
3. **정적 파일이 데이터베이스다.** JSON + Markdown = 모든 것.
4. **PC는 필요할 때만 Thin Client.** Tailscale + SSH로 폰에 붙는다.
