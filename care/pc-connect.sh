#!/usr/bin/env bash
# ==============================================================================
# pc-connect.sh — PC에서 S21로 Tailscale SSH 접속 (WSL/Mac/Linux)
# ==============================================================================
# 사용법: bash pc-connect.sh [command]
#   (인자 없음) → 대화형 SSH 접속
#   "health"     → care-state.json 읽기
#   "log"        → care.log 보기
#   "restart"    → care-daemon 재시작
#   "ping"       → 연결 테스트
#   "cmd <cmd>"  → 임의 명령 실행
# ==============================================================================
set -euo pipefail

# Tailscale S21 호스트명 (tailscale status로 확인한 이름)
S21_HOST="${S21_TS_HOST:-helena-s21}"
S21_PORT="${S21_PORT:-8022}"

# SSH 옵션
SSH_OPTS="-p ${S21_PORT} -o ConnectTimeout=5 -o StrictHostKeyChecking=no"

# ── Tailscale 연결 확인 ──
if ! command -v tailscale >/dev/null 2>&1; then
  echo "❌ tailscale CLI 없음 — https://tailscale.com/download"
  exit 1
fi

# S21 IP 찾기
S21_IP=$(tailscale status 2>/dev/null | grep "$S21_HOST" | grep -oP '100\.\d+\.\d+\.\d+' | head -1 || echo "")

if [ -z "$S21_IP" ]; then
  echo "❌ Tailscale에서 '$S21_HOST'를 찾을 수 없습니다."
  echo "   tailscale status 로 호스트명 확인 후 S21_TS_HOST= 설정"
  tailscale status 2>/dev/null | head -10
  exit 1
fi

echo "🔗 S21: $S21_IP (Tailscale)"

case "${1:-}" in
  ""|shell|ssh)
    echo "접속 중..."
    ssh $SSH_OPTS "$S21_IP"
    ;;
  health)
    ssh $SSH_OPTS "$S21_IP" "cat ~/care/care-state.json 2>/dev/null || echo 'state 없음'"
    ;;
  log)
    ssh $SSH_OPTS "$S21_IP" "tail -50 ~/care/care.log"
    ;;
  restart)
    ssh $SSH_OPTS "$S21_IP" "bash ~/care/care-daemon.sh"
    ;;
  ping)
    ssh $SSH_OPTS "$S21_IP" "echo ✅ S21 alive; uptime; termux-battery-status | head -3"
    ;;
  cmd)
    shift
    ssh $SSH_OPTS "$S21_IP" "$@"
    ;;
  *)
    echo "사용법: bash pc-connect.sh [health|log|restart|ping|cmd <명령>]"
    exit 1
    ;;
esac
