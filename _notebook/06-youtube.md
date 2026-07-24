# YouTube 채널 아키텍처

## 채널 구성 (티스토리 1:1 매칭)

| 채널명 | 매칭 티스토리 | 콘텐츠 |
|--------|-------------|--------|
| _(미정)_ | `galaxys21-pwuser` | S21 폰 워크스테이션 셋업/코딩 |
| _(미정)_ | `mynote11605` | 기술 튜토리얼 / 개발 vlog |
| _(미정)_ | `helana-christianity` | 말씀 / 신앙 콘텐츠 |
| _(미정)_ | `helena-piano` | 연주 커버 / 피아노 레슨 |
| _(미정)_ | `helena-psycare` | 금속 공예 / 메이킹 필름 |

## 채널 구조

- 각 티스토리 블로그 = 1개의 YouTube 채널과 1:1 매칭
- YouTube 채널명은 티스토리와 동일하거나 유사하게 구성
- 네이버 블로그(관저탑)는 모든 채널의 교차 홍보 게이트웨이

## 루트 채널

```
https://www.youtube.com/@HelenaPark-e7c
```

## 구축 상태

| 단계 | 상태 |
|------|------|
| GCP 프로젝트 생성 | 📌 준비 완료 (gcloud CLI 설치됨) |
| YouTube Data API v3 활성화 | 📌 준비 완료 |
| OAuth 동의 화면 | ⏳ 수동 필요 (console.cloud.google.com) |
| TV 클라이언트 ID 생성 | ⏳ 수동 필요 |
| Device code 인증 | 📌 자동화 준비 |
| 업로드 스크립트 | ⏳ 미작성 |
| 쿼터 보호(playlistItems) | 📌 설계 반영 예정 |

## 수동 작업 (폰 브라우저)

```md
1. console.cloud.google.com → 새 프로젝트 "S21 YouTube"
2. OAuth 동의 화면 → 외부 → 앱이름 "S21 Phone" → 테스트 사용자 추가
3. 사용자 인증 정보 → OAuth 클라이언트 ID → "TV 및 제한된 입력 장치"
4. 클라이언트 ID + 시크릿 복사
```

## 쿼터 참고

| 작업 | 유닛 | 비고 |
|------|------|------|
| 업로드 (videos.insert) | 1,600 | 하루 약 6개 가능 |
| 메타데이터 수정 | 50 | |
| 목록 조회 (search.list) | 100 | ❌ 사용 금지 |
| playlistItems.list | 1 | ✅ 이걸로 대체 |
| 채널 정보 | 1 | |

**절대 `search.list`를 루프에 넣지 말 것. playlistItems.list (1유닛) 사용.**
