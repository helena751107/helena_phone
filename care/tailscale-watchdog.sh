#!/usr/bin/env bash
# ==============================================================================
# tailscale-watchdog.sh — Tailscale 터널 생존 감시 (cron 매 10분)
# ==============================================================================
# Tailscale 데몬이 죽으면 재시작, 연결 끊기면 보고
# ==============================================================================
set -euo pipefail

CARE_DIR="/data/data/com.termux/files/home/care"
STATE_FILE="${CARE_DIR}/tailscale-state.json"
LOG_FILE="${CARE_DIR}/tailscale.log"
CONF_FILE="${CARE_DIR}/care.conf"
NOW=$(date '+%Y-%m-%d %H:%M:%S')
NOW_EPOCH=$(date +%s)

export PATH="/data/data/com.termux/files/usr/bin:$PATH"

[ -f "$CONF_FILE" ] && source "$CONF_FILE"

log() { echo "[$NOW] $*" >> "$LOG_FILE"; }

# ── 1. 데몬 생존 체크 ──
if ! pgrep -f "tailscaled" >/dev/null 2>&1; then
  log "WARN: tailscaled 죽음 → 재시작"
  tailscaled --tun=userspace-networking --socks5-server=localhost:1055 \
    --state="$HOME/.tailscale/tailscaled.state" &
  sleep 3
fi

# ── 2. 연결 상태 체크 ──
TS_STATUS=$(tailscale status 2>/dev/null || echo "OFFLINE")
TS_IP=$(tailscale ip -4 2>/dev/null || echo "0.0.0.0")

if echo "$TS_STATUS" | grep -q "100."; then
  # 연결 정상
  echo "{\"timestamp\":\"$NOW\",\"epoch\":$NOW_EPOCH,\"status\":\"online\",\"ip\":\"$TS_IP\"}" > "$STATE_FILE"
  log "OK: online $TS_IP"
else
  log "WARN: tailscale 오프라인 → 재연결 시도"
  tailscale up --accept-routes --ssh 2>/dev/null || true
  sleep 5

  TS_IP2=$(tailscale ip -4 2>/dev/null || echo "0.0.0.0")
  if [ "$TS_IP2" != "0.0.0.0" ]; then
    log "OK: 재연결 성공 $TS_IP2"
  else
    log "ERROR: tailscale 재연결 실패"

    # 텔레그램 알림
    if [ -n "${TG_TOKEN:-}" ] && [ -n "${TG_CHAT_HELENA:-}" ]; then
      curl -s -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" \
        -d "chat_id=${TG_CHAT_HELENA}" \
        -d "text=🔗 Tailscale 오프라인 — S21 연결 끊김" \
        >/dev/null 2>&1 || true
    fi
  fi

  echo "{\"timestamp\":\"$NOW\",\"epoch\":$NOW_EPOCH,\"status\":\"offline\",\"ip\":\"$TS_IP2\"}" > "$STATE_FILE"
fi
