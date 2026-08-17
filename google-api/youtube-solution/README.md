# 🎬 YouTube 자동화 솔루션 (자체완결 패키지)

계정정보 + 토큰 + 환경변수만 넣으면 **설치 → 설정 → 유튜브 통제**까지 한 방에 되는
패키지. 기존 `tools/youtube/`의 노하우(로그인 자동화·쿼터 6만 증산·업로드 상태머신)를
**이식/압축해서 어디서든 재설치 가능하게** 만든 버전.

---

## 1. 뭐가 필요한가 (3개)

| 입력 | 값 | 필수 |
|------|-----|------|
| 계정 이메일 | `YT_ACCOUNT_EMAIL` | ✅ |
| 채널 목록 | `YT_CHANNELS` (`@핸들|채널ID|레포`) | ✅ |
| GCP 클라이언트 | `YT_CLIENT_ID` / `YT_CLIENT_SECRET` | ✅ |
| 리프레시 토큰 | `YT_REFRESH_TOKEN` | 🟡 있으면 브라우저 생략 |
| 구글 비번 | `YT_PASSWORD` | 🟡 브라우저 자동 로그인할 때만 |

> **핵심**: `YT_REFRESH_TOKEN`만 있으면 브라우저/2FA 없이 **곧바로 API 통제**.
> 토큰이 없으면 `auth` 명령 1회로 브라우저(폰 2FA) 인증.

---

## 2. 설치 (3단계)

```bash
cd tools/youtube/solution

# 1) 환경변수 파일 생성 후 값 채우기
cp .env.example .env
nano .env

# 2) 원클릭 설치 (의존성 + 설정파일 자동 생성)
bash install.sh

# 3) 상태 확인
python3 youtube_ctl.py status
```

`.env` 예시:

```bash
YT_ACCOUNT_EMAIL="REDACTED"
YT_ACCOUNT_ID="a"
YT_CHANNELS="@musician-parksy|UCun6b2HD3ekp35PhqbTfOlg|parksy-audio;@blogger-parksy|UC5H8CnRGDxvx4v3HWrktuSg|parksy.kr"
YT_CLIENT_ID="390585643473-....apps.googleusercontent.com"
YT_CLIENT_SECRET="GOCSPX-...."
YT_GCP_PROJECT="parksy-youtube"
YT_REFRESH_TOKEN="1//0... (있으면 바로 통제)"
```

---

## 3. 통제 명령 (토큰만 있으면 전부)

```bash
python3 youtube_ctl.py status                # 계정/채널/토큰 상태
python3 youtube_ctl.py auth                  # 토큰 발급 (없을 때 1회)
python3 youtube_ctl.py channels              # 채널 정보+구독자
python3 youtube_ctl.py upload video.mp4 "제목" # 동영상 업로드
python3 youtube_ctl.py playlist list         # 플레이리스트 목록
python3 youtube_ctl.py playlist create "CDN"
python3 youtube_ctl.py playlist add <플리ID> <영상ID>
python3 youtube_ctl.py branding "새 설명"
python3 youtube_ctl.py analytics 28          # 28일 조회/구독 통계
```

---

## 4. 토큰 없이 브라우저 자동 로그인 (기존 GUI 솔루션 그대로)

이 패키지는 refresh token이 있으면 브라우저 없이 동작. 브라우저 로그인이 필요한
경우 기존 GUI 자동화(`tools/youtube/yt_oauth_channel.cjs`)를 그대로 씀:

```bash
pkill -9 -f "yt_oauth_channel.cjs"; pkill -9 -f "chromium-1228"
cd tools/youtube
DISPLAY=:0 PASSWORD='<비번>' timeout 150 node yt_oauth_channel.cjs @핸들
```

얻은 refresh_token을 `.env`의 `YT_REFRESH_TOKEN`에 넣으면 끝.

---

## 5. 쿼터 (이미 증산 완료)

- 기본 10,000 → **60,000 units/day** (GCP `parksy-youtube`)
- 업로드 1회 = 1,600 units → 하루 약 37개 가능
- 증산 이력: `docs/dev-logs/022-...-quota-expansion-2026-03-19.md`

---

## 6. 알아두면 안 막히는 것들

1. **2FA는 폰에서 사람이 눌러야 함** — 자동화 불가 구간. 인증 직전 "폰 확인" 안내.
2. `auth`가 headless 서버면 URL을 출력해주니 폰으로 열어 코드 붙여넣기.
3. 토큰 파일은 `solution/runtime/` 아래 자동 생성 — 절대 커밋하지 말 것 (.gitignore 처리).
