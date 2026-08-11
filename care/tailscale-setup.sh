#!/usr/bin/env bash
# ==============================================================================
# tailscale-setup.sh — S21 Tailscale 돌봄 터널 설치 (Termux 네이티브)
# ==============================================================================
# 실행: bash ~/care/tailscale-setup.sh
# 전제: Termux 네이티브 (proot X), F-Droid Tailscale APK 설치되어 있어야 함
# 결과: PC↔S21 항시 SSH 터널 (돌봄 케어 백본)
# ==============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok() { echo -e "${GREEN}✅${NC} $*"; }
warn() { echo -e "${YELLOW}⚠️${NC}  $*"; }
fail() { echo -e "${RED}❌${NC} $*"; }

CARE_DIR="/data/data/com.termux/files/home/care"

echo "════════════════════════════════════════════"
echo "  🔗 Tailscale 돌봄 터널 — 설치"
echo "  PC ↔ S21 항시 연결 백본"
echo "════════════════════════════════════════════"

# ── 1. Tailscale 바이너리 체크 ──
if command -v tailscale >/dev/null 2>&1; then
  ok "tailscale 바이너리 있음 ($(tailscale version 2>/dev/null | head -1))"
else
  warn "tailscale CLI 없음 — Termux에 설치"
  pkg install -y tailscale 2>/dev/null || {
    fail "tailscale 설치 실패. F-Droid에서 Tailscale APK 설치 후 재시도"
    echo "  https://f-droid.org/packages/com.tailscale.ipn/"
    exit 1
  }
  ok "tailscale 설치 완료"
fi

# ── 2. Tailscale 데몬 시작 ──
if tailscale status >/dev/null 2>&1; then
  ok "tailscaled 이미 실행 중"
else
  warn "tailscaled 시작..."
  tailscaled --tun=userspace-networking --socks5-server=localhost:1055 \
    --state="$HOME/.tailscale/tailscaled.state" &
  sleep 3
  ok "tailscaled 시작됨 (userspace 모드)"
fi

# ── 3. 인증 상태 체크 ──
if tailscale status 2>/dev/null | grep -q "100."; then
  ok "Tailscale 이미 인증됨 → $(tailscale status | head -1)"
else
  echo ""
  warn "Tailscale 인증 필요"
  echo "  아래 URL을 PC 브라우저에서 열어서 인증하세요:"
  echo ""
  tailscale up --accept-routes --ssh 2>&1 | grep "https://" || true
  echo ""
  echo "  ⏳ 인증 후 Enter..."
  read -r
fi

# ── 4. 상태 확인 ──
echo ""
if tailscale status 2>/dev/null | head -3; then
  ok "Tailscale 연결 완료"
else
  fail "Tailscale 상태 확인 실패"
  exit 1
fi

# ── 5. SSH 서버 확인 (선택) ──
if command -v sshd >/dev/null 2>&1; then
  ok "SSH 서버 있음 — Tailscale IP로 접속 가능"
  tailscale ip -4 2>/dev/null | xargs -I{} echo "  PC에서: ssh {} -p 8022"
else
  warn "sshd 없음 — 필요시: pkg install openssh && sshd"
fi

# ── 6. watchdog 등록 ──
cp "$(dirname "$0")/tailscale-watchdog.sh" "$CARE_DIR/tailscale-watchdog.sh" 2>/dev/null || true
chmod +x "$CARE_DIR/tailscale-watchdog.sh"

CRON_LINE="*/10 * * * * bash ${CARE_DIR}/tailscale-watchdog.sh"
if crontab -l 2>/dev/null | grep -q "tailscale-watchdog"; then
  ok "tailscale watchdog crontab 이미 등록됨"
else
  (crontab -l 2>/dev/null || true; echo "$CRON_LINE") | crontab -
  ok "tailscale watchdog crontab 등록 (매 10분)"
fi

echo ""
echo "════════════════════════════════════════════"
echo "  ✅ Tailscale 돌봄 터널 설치 완료"
echo ""
echo "  S21 Tailscale IP: $(tailscale ip -4 2>/dev/null || echo '?')"
echo "  PC에서 접속: ssh $(tailscale ip -4 2>/dev/null || echo 'S21_IP') -p 8022"
echo ""
echo "  ⚠️  userspace-networking 모드 = 루트 불필요"
echo "     APK가 설치되어 있어야 백그라운드 지속됨"
echo "════════════════════════════════════════════"
