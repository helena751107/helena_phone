#!/usr/bin/env bash
# ==============================================================================
# yt_oauth_setup.sh — YouTube OAuth Device Code Flow 최초 인증
# ==============================================================================
# 사용법: bash scripts/yt_oauth_setup.sh
# 전제: Google Cloud Console에서 OAuth 클라이언트 ID 발급 완료
#       → .secrets.env에 YT_CLIENT_ID, YT_CLIENT_SECRET 저장
# ==============================================================================

set -euo pipefail

BASE="$(cd "$(dirname "$0")/.." && pwd)"
SECRETS="$BASE/.secrets.env"
TOKEN_FILE="$BASE/configs/yt_tokens.json"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok() { echo -e "${GREEN}✅${NC} $*"; }
warn() { echo -e "${YELLOW}⚠️${NC}  $*"; }

echo "════════════════════════════════════════════"
echo "  📺 YouTube OAuth — Device Code Flow"
echo "════════════════════════════════════════════"

# ── 시크릿 로드 ──
if [ -f "$SECRETS" ]; then
  source "$SECRETS" 2>/dev/null || true
fi

CLIENT_ID="${YT_CLIENT_ID:-}"
CLIENT_SECRET="${YT_CLIENT_SECRET:-}"

if [ -z "$CLIENT_ID" ] || [ -z "$CLIENT_SECRET" ]; then
  echo "❌ YT_CLIENT_ID 또는 YT_CLIENT_SECRET이 설정되지 않았습니다."
  echo ""
  echo "   발급 방법:"
  echo "   1. console.cloud.google.com → S21 YouTube 프로젝트"
  echo "   2. API 및 서비스 → 사용자 인증 정보"
  echo "   3. OAuth 클라이언트 ID → TV 및 제한된 입력 장치"
  echo "   4. 클라이언트 ID + 시크릿 → .secrets.env에 저장:"
  echo ""
  echo "      YT_CLIENT_ID=xxxxxxxx.apps.googleusercontent.com"
  echo "      YT_CLIENT_SECRET=GOCSPX-xxxxxxxx"
  exit 1
fi
ok "클라이언트 ID 확인"

# ── Device Code 요청 ──
echo ""
echo "📡 Google에 device code 요청..."

RESP=$(curl -s -X POST "https://oauth2.googleapis.com/device/code" \
  -d "client_id=${CLIENT_ID}" \
  -d "scope=https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube https://www.googleapis.com/auth/yt-analytics.readonly")

DEVICE_CODE=$(echo "$RESP" | python3 -c "import json,sys; print(json.load(sys.stdin)['device_code'])" 2>/dev/null || echo "")
USER_CODE=$(echo "$RESP" | python3 -c "import json,sys; print(json.load(sys.stdin)['user_code'])" 2>/dev/null || echo "")
VERIFY_URL=$(echo "$RESP" | python3 -c "import json,sys; print(json.load(sys.stdin)['verification_url'])" 2>/dev/null || echo "")
INTERVAL=$(echo "$RESP" | python3 -c "import json,sys; print(json.load(sys.stdin).get('interval',5))" 2>/dev/null || echo "5")
EXPIRES=$(echo "$RESP" | python3 -c "import json,sys; print(json.load(sys.stdin).get('expires_in',600))" 2>/dev/null || echo "600")

if [ -z "$DEVICE_CODE" ]; then
  echo "❌ Device code 요청 실패"
  echo "$RESP"
  exit 1
fi

echo ""
echo "════════════════════════════════════════════"
echo "  📱 폰에서 이 URL로 접속하세요:"
echo ""
echo -e "  ${GREEN}${VERIFY_URL}${NC}"
echo ""
echo -e "  코드 입력: ${GREEN}${USER_CODE}${NC}"
echo ""
echo "  ⏱  ${EXPIRES}초 안에 완료해야 합니다"
echo "════════════════════════════════════════════"

# ── 토큰 폴링 ──
echo ""
echo "⏳ 인증 대기 중..."

for i in $(seq 1 $((EXPIRES / INTERVAL))); do
  sleep "$INTERVAL"

  TOKEN_RESP=$(curl -s -X POST "https://oauth2.googleapis.com/token" \
    -d "client_id=${CLIENT_ID}" \
    -d "client_secret=${CLIENT_SECRET}" \
    -d "device_code=${DEVICE_CODE}" \
    -d "grant_type=urn:ietf:params:oauth:grant-type:device_code")

  ACCESS_TOKEN=$(echo "$TOKEN_RESP" | python3 -c "import json,sys; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || echo "")

  if [ -n "$ACCESS_TOKEN" ]; then
    ok "인증 성공!"

    # 토큰 저장
    mkdir -p "$(dirname "$TOKEN_FILE")"
    echo "$TOKEN_RESP" | python3 -c "
import json, sys
data = json.load(sys.stdin)
with open('$TOKEN_FILE', 'w') as f:
    json.dump({
        'access_token': data['access_token'],
        'refresh_token': data.get('refresh_token', ''),
        'expires_in': data.get('expires_in', 3600),
        'scope': data.get('scope', ''),
        'token_type': data.get('token_type', 'Bearer'),
    }, f, indent=2)
" && ok "토큰 저장: $TOKEN_FILE"

    chmod 600 "$TOKEN_FILE" 2>/dev/null || true

    echo ""
    echo "✅ YouTube OAuth 설정 완료!"
    echo "   이제 업로드 가능:"
    echo "   ~/browser-env/bin/python3 scripts/yt_upload.py --title '제목' --file video.mp4"
    exit 0
  fi

  ERROR=$(echo "$TOKEN_RESP" | python3 -c "import json,sys; print(json.load(sys.stdin).get('error','pending'))" 2>/dev/null || echo "pending")

  if [ "$ERROR" != "authorization_pending" ] && [ "$ERROR" != "pending" ]; then
    echo "❌ 오류: $ERROR"
    echo "$TOKEN_RESP"
    exit 1
  fi

  echo "   ... 대기 중 (${i}/${INTERVAL}회, 오류: $ERROR)"
done

echo "❌ 시간 초과. 다시 시도하세요."
exit 1
