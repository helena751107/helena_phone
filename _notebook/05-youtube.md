# YouTube Data API (구축 예정)

## 상태

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

## GCP 프로젝트 생성 (API)

```bash
export PATH="/tmp/google-cloud-sdk/bin:$PATH"
gcloud auth login
gcloud projects create s21-youtube --name="S21 YouTube"
gcloud config set project s21-youtube
gcloud services enable youtube.googleapis.com
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

## 채널 정보

```
https://www.youtube.com/@HelenaPark-e7c
```
