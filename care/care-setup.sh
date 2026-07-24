#!/usr/bin/env bash
# ==============================================================================
# care-setup.sh — 트랙 1 돌봄 데몬 설치 스크립트
# ==============================================================================
# 실행: bash ~/care/care-setup.sh
# 이 스크립트는 Termux 네이티브 환경에서 실행 (proot Ubuntu 안에서 실행 금지)
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok() { echo -e "${GREEN}✅${NC} $*"; }
warn() { echo -e "${YELLOW}⚠️${NC}  $*"; }
fail() { echo -e "${RED}❌${NC} $*"; }

CARE_DIR="/data/data/com.termux/files/home/care"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "════════════════════════════════════════════"
echo "  🛡️  트랙 1 돌봄 데몬 — 설치"
echo "  위치: $CARE_DIR"
echo "  ⚠️  Termux 네이티브에서 실행 중인가?"
echo "════════════════════════════════════════════"

# ── 환경 체크 ──
if [ "$(uname -o 2>/dev/null)" != "Android" ]; then
  fail "Android/Termux 환경에서만 실행 가능합니다"
  exit 1
fi

if [ -z "${TERMUX_VERSION:-}" ]; then
  fail "Termux에서 실행해주세요"
  exit 1
fi
ok "Termux 환경 확인"

# ── 의존성 체크 ──
for cmd in termux-battery-status termux-location termux-wifi-connectioninfo curl python3 crontab; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    warn "$cmd 없음 — pkg install termux-api 진행..."
    pkg install -y termux-api >/dev/null 2>&1 || fail "$cmd 설치 실패"
  fi
done
ok "의존성 확인"

# ── 파일 복사 ──
mkdir -p "$CARE_DIR"

for f in care-daemon.sh care.conf; do
  if [ -f "${SCRIPT_DIR}/$f" ]; then
    cp "${SCRIPT_DIR}/$f" "$CARE_DIR/$f"
    chmod +x "$CARE_DIR/$f"
    ok "$f → $CARE_DIR/$f"
  else
    warn "$f 없음 (스킵)"
  fi
done

# ── 토큰 확인 ──
if ! grep -q "TG_TOKEN=" "$CARE_DIR/care.conf" 2>/dev/null || \
   grep -q "TG_TOKEN=\"\"" "$CARE_DIR/care.conf" 2>/dev/null; then
  echo ""
  warn "care.conf에 TG_TOKEN이 설정되지 않았습니다."
  echo "  편집: nano $CARE_DIR/care.conf"
  echo "  TG_TOKEN=봇토큰"
  echo "  TG_CHAT_HELENA=챗ID"
fi

# ── crontab 등록 ──
CRON_LINE="*/15 * * * * bash ${CARE_DIR}/care-daemon.sh >> ${CARE_DIR}/cron.log 2>&1"

if crontab -l 2>/dev/null | grep -q "care-daemon"; then
  ok "crontab 이미 등록됨"
else
  (crontab -l 2>/dev/null || true; echo "$CRON_LINE") | crontab -
  ok "crontab 등록 완료 (매 15분)"
fi

# ── 첫 실행 ──
echo ""
echo "─── 첫 실행 테스트 ───"
if bash "${CARE_DIR}/care-daemon.sh" 2>&1; then
  ok "첫 실행 완료"
else
  warn "첫 실행에 경고가 있습니다. 로그 확인: $CARE_DIR/care.log"
fi

# ── 상태 파일 ──
ls -la "$CARE_DIR/care-state.json" 2>/dev/null && ok "care-state.json 생성됨" || warn "state 파일 없음"

echo ""
echo "════════════════════════════════════════════"
echo "  ✅ 트랙 1 돌봄 데몬 설치 완료"
echo ""
echo "  작동 확인:"
echo "    crontab -l              ← 등록 확인"
echo "    cat ~/care/care-state.json  ← 최신 상태"
echo "    cat ~/care/care.log     ← 로그"
echo ""
echo "  ⚠️  이 데몬은 AI 의존성 제로."
echo "     Claude Code가 죽어도 독립 실행됩니다."
echo "════════════════════════════════════════════"
