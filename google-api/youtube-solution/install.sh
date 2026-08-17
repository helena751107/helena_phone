#!/usr/bin/env bash
# ============================================================
#  YouTube 자동화 솔루션 — 원클릭 설치/설정
#  계정정보 + 토큰 + 환경변수(.env)만 있으면 전부 자동 구성.
#  사용법:
#    1) cp .env.example .env  → 값 채우기
#    2) bash install.sh
#    3) python3 youtube_ctl.py status   (동작 확인)
# ============================================================
set -euo pipefail

SOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SOL_DIR/.." && pwd)"     # tools/youtube
cd "$SOL_DIR"

echo "════════════════════════════════════════════"
echo "  YouTube 자동화 솔루션 — 설치 시작"
echo "════════════════════════════════════════════"

# 0) .env 로드
if [ -f "$SOL_DIR/.env" ]; then
  set -a; . "$SOL_DIR/.env"; set +a
  echo "✔ .env 로드 완료"
else
  echo "✖ .env 없음 — cp .env.example .env 후 값을 채우세요"
  exit 1
fi

# 1) 필수값 검증
: "${YT_ACCOUNT_EMAIL:?YT_ACCOUNT_EMAIL 필수}"
: "${YT_CHANNELS:?YT_CHANNELS 필수}"
: "${YT_CLIENT_ID:?YT_CLIENT_ID 필수 (GCP OAuth 클라이언트)}"
: "${YT_CLIENT_SECRET:?YT_CLIENT_SECRET 필수}"
echo "✔ 필수값 검증 통과: $YT_ACCOUNT_EMAIL"

# 2) Python 의존성 설치
echo "→ Python 의존성 설치 중..."
if command -v pip3 >/dev/null 2>&1; then
  PIP=pip3
elif command -v pip >/dev/null 2>&1; then
  PIP=pip
else
  echo "✖ pip 없음 — python3 + pip 설치 후 재실행"
  exit 1
fi
$PIP install --quiet --disable-pip-version-check \
  google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2 \
  python-dotenv 2>&1 | tail -3 || true
echo "✔ 의존성 설치 완료"

# 3) 설정 파일 생성 (계정/채널/토큰/클라이언트시크릿)
echo "→ 설정 파일 생성 중..."
python3 "$SOL_DIR/youtube_ctl.py" init || { echo "✖ 설정 생성 실패"; exit 1; }

# 4) 스모크 테스트 (refresh token 있으면 API 검증, 없으면 auth 안내)
echo "→ 스모크 테스트..."
python3 "$SOL_DIR/youtube_ctl.py" status || true

echo ""
echo "════════════════════════════════════════════"
echo "  설치 완료. 실행 방법:"
echo "   python3 $SOL_DIR/youtube_ctl.py status      # 상태"
echo "   python3 $SOL_DIR/youtube_ctl.py auth        # 브라우저 토큰 발급(토큰 없을 때)"
echo "   python3 $SOL_DIR/youtube_ctl.py upload <mp4> # 업로드"
echo "════════════════════════════════════════════"
