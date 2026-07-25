#!/usr/bin/env bash
# ==============================================================================
# grok_oauth_setup.sh — SuperGrok OAuth Device Code Flow (YouTube와 동일 패턴)
# ==============================================================================
# 사용법: bash scripts/grok_oauth_setup.sh
# 전제: grok.com 또는 X Premium+ 구독 상태
# 결과: configs/grok_token.json 에 토큰 저장
# ==============================================================================

set -euo pipefail

BASE="$(cd "$(dirname "$0")/.." && pwd)"
TOKEN_FILE="$BASE/configs/grok_token.json"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok() { echo -e "${GREEN}✅${NC} $*"; }
warn() { echo -e "${YELLOW}⚠️${NC}  $*"; }

echo "════════════════════════════════════════════"
echo "  🤖 Grok OAuth — Device Code Flow"
echo "  SuperGrok 구독 → API 사용"
echo "════════════════════════════════════════════"

# ── Device Code 요청 ──
echo ""
echo "📡 xAI에 device code 요청..."

RESP=$(curl -s -X POST "https://accounts.x.ai/oauth2/device/code" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=grok" \
  -d "scope=openid profile email offline_access" 2>/dev/null)

DEVICE_CODE=$(echo "$RESP" | python3 -c "import json,sys; print(json.load(sys.stdin).get('device_code',''))" 2>/dev/null || echo "")
USER_CODE=$(echo "$RESP" | python3 -c "import json,sys; print(json.load(sys.stdin).get('user_code',''))" 2>/dev/null || echo "")
VERIFY_URL=$(echo "$RESP" | python3 -c "import json,sys; print(json.load(sys.stdin).get('verification_uri',''))" 2>/dev/null || echo "")
INTERVAL=$(echo "$RESP" | python3 -c "import json,sys; print(json.load(sys.stdin).get('interval',5))" 2>/dev/null || echo "5")
EXPIRES=$(echo "$RESP" | python3 -c "import json,sys; print(json.load(sys.stdin).get('expires_in',600))" 2>/dev/null || echo "600")

if [ -z "$DEVICE_CODE" ]; then
  echo "❌ Device code 요청 실패"
  echo "$RESP"
  echo ""
  echo "💡 대안: console.x.ai 에서 API 키 발급 (무료 $25 크레딧)"
  echo "   발급 후 .secrets.env 에 추가: XAI_API_KEY=\"xai-...\""
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
echo "  ⏱  ${EXPIRES}초 안에 완료"
echo "  💡 SuperGrok 계정으로 로그인하세요"
echo "════════════════════════════════════════════"

# ── 토큰 폴링 ──
echo ""
echo "⏳ 인증 대기 중..."

for i in $(seq 1 $((EXPIRES / INTERVAL))); do
  sleep "$INTERVAL"

  TOKEN_RESP=$(curl -s -X POST "https://accounts.x.ai/oauth2/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=urn:ietf:params:oauth:grant-type:device_code" \
    -d "client_id=grok" \
    -d "device_code=${DEVICE_CODE}" 2>/dev/null)

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
        'token_type': data.get('token_type', 'Bearer'),
    }, f, indent=2)
" && ok "토큰 저장: $TOKEN_FILE"

    chmod 600 "$TOKEN_FILE" 2>/dev/null || true

    # 토큰 검증
    echo ""
    echo "═══ 토큰 검증 ═══"
    curl -s -H "Authorization: Bearer ${ACCESS_TOKEN}" \
      "https://api.x.ai/v1/models" 2>/dev/null | python3 -c "
import json,sys
d = json.load(sys.stdin)
if 'data' in d:
    models = [m['id'] for m in d['data']]
    print(f'사용 가능 모델: {len(models)}개')
    for m in models[:10]:
        print(f'  - {m}')
elif 'error' in d:
    print(f'오류: {d[\"error\"].get(\"message\",\"?\")}')
else:
    print(json.dumps(d, indent=2, ensure_ascii=False)[:300])
" 2>/dev/null

    echo ""
    echo "✅ Grok OAuth 설정 완료!"
    echo "   이제 사용 가능:"
    echo "   python3 scripts/grok_api.py chat '질문'"
    exit 0
  fi

  ERROR=$(echo "$TOKEN_RESP" | python3 -c "import json,sys; print(json.load(sys.stdin).get('error','pending'))" 2>/dev/null || echo "pending")

  if [ "$ERROR" != "authorization_pending" ] && [ "$ERROR" != "pending" ]; then
    echo "❌ 오류: $ERROR"
    echo "$TOKEN_RESP"
    echo ""
    echo "💡 OAuth가 안 되면 API 키 방식으로:"
    echo "   1. console.x.ai → API Keys → Create"
    echo "   2. .secrets.env 에 XAI_API_KEY=\"xai-...\""
    exit 1
  fi

  echo "   ... 대기 중 (${i}회)"
done

echo "❌ 시간 초과"
exit 1
