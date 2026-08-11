#!/usr/bin/env bash
# ==============================================================================
# proot-gateway.sh — Termux → proot Ubuntu 게이트웨이 (돌봄 터널 백본)
# ==============================================================================
# 문제: proot Ubuntu(glibc)는 Tailscale VPN 인터페이스를 직접 탈 수 없음.
#       Android 프레임워크가 VPN 라우팅을 독점 → proot 프로세스 격리.
# 해결: Termux(bionic)가 Tailscale 받고, proot은 localhost 경유.
#
# 터널 구조:
#   PC ──Tailscale──→ Termux(SSH:8022) ──localhost──→ proot Ubuntu
#
# 실행: bash ~/care/proot-gateway.sh [start|stop|status]
# ==============================================================================
set -euo pipefail

CARE_DIR="/data/data/com.termux/files/home/care"
PROOT_NAME="${PROOT_NAME:-ubuntu}"
PROOT_PORT_START="${PROOT_PORT_START:-9000}"

export PATH="/data/data/com.termux/files/usr/bin:$PATH"

start_gateway() {
  echo "🔗 proot-gateway 시작..."

  # ── 1. proot Ubuntu 실행 중인지 확인 ──
  if ! pgrep -f "proot.*${PROOT_NAME}" >/dev/null 2>&1; then
    echo "  proot Ubuntu 로그인..."
    proot-distro login "$PROOT_NAME" -- bash -c "echo proot-ready" &
    sleep 3
  fi
  echo "  ✅ proot Ubuntu 활성"

  # ── 2. proot 내 SSH 서버 시작 ──
  proot-distro login "$PROOT_NAME" -- bash -c "
    if ! pgrep sshd >/dev/null 2>&1; then
      mkdir -p /run/sshd
      /usr/sbin/sshd -p 2222 -o PermitRootLogin=yes -o PasswordAuthentication=yes &
      echo 'sshd started on proot:2222'
    else
      echo 'sshd already running'
    fi
  " 2>/dev/null || echo "  ⚠️  proot sshd 시작 실패 (openssh-server 설치 필요)"

  # ── 3. Termux → proot 포트포워드 (socat) ──
  # Tailscale로 들어오는 요청을 proot Ubuntu로 전달
  if command -v socat >/dev/null 2>&1; then
    # 기존 socat 정리
    pkill -f "socat.*${PROOT_PORT_START}" 2>/dev/null || true

    # proot SSH: Termux:8022 → proot:2222
    socat TCP-LISTEN:8022,fork,reuseaddr TCP:127.0.0.1:2222 &
    echo "  ✅ 포트포워드: Termux:8022 → proot:2222 (SSH)"

    # proot HTTP: Termux:8080 → proot:8080 (웹진 등)
    socat TCP-LISTEN:8080,fork,reuseaddr TCP:127.0.0.1:8080 &
    echo "  ✅ 포트포워드: Termux:8080 → proot:8080 (HTTP)"
  else
    echo "  ⚠️  socat 없음 → pkg install socat"
    pkg install -y socat 2>/dev/null || true
  fi

  # ── 4. Tailscale 연결 확인 ──
  TS_IP=$(tailscale ip -4 2>/dev/null || echo "")
  if [ -n "$TS_IP" ]; then
    echo "  ✅ Tailscale IP: $TS_IP"
    echo ""
    echo "  PC에서 접속:"
    echo "    ssh root@${TS_IP} -p 8022        # proot Ubuntu 직접 SSH"
    echo "    curl http://${TS_IP}:8080          # proot 웹 서비스"
  else
    echo "  ⚠️  Tailscale 오프라인 — PC에서 접속 불가"
    echo "     bash ~/care/tailscale-setup.sh 먼저 실행"
  fi
}

stop_gateway() {
  echo "🛑 proot-gateway 정지..."
  pkill -f "socat.*8022" 2>/dev/null && echo "  socat:8022 정지" || true
  pkill -f "socat.*8080" 2>/dev/null && echo "  socat:8080 정지" || true
  echo "  완료"
}

status_gateway() {
  echo "📊 proot-gateway 상태"
  echo ""

  # Tailscale
  TS_IP=$(tailscale ip -4 2>/dev/null || echo "offline")
  echo "  Tailscale: $TS_IP"

  # proot
  if pgrep -f "proot.*${PROOT_NAME}" >/dev/null 2>&1; then
    echo "  proot:     ✅ running"
  else
    echo "  proot:     ❌ stopped"
  fi

  # socat forwards
  for port in 8022 8080; do
    if pgrep -f "socat.*${port}" >/dev/null 2>&1; then
      echo "  forward:${port}: ✅ active"
    else
      echo "  forward:${port}: ❌ inactive"
    fi
  done
}

case "${1:-start}" in
  start) start_gateway ;;
  stop)  stop_gateway ;;
  status) status_gateway ;;
  *) echo "사용법: bash proot-gateway.sh [start|stop|status]" ;;
esac
