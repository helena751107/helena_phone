#!/usr/bin/env bash
# ==============================================================================
# g/easy.sh — 초심자 전용 · 리버스 엔지니어링 최단 경로
# ==============================================================================
# 목표: 결정 최소화. 앱 2개 설치 후, Termux에 이 한 줄만.
#
#   bash <(curl -sL https://raw.githubusercontent.com/helena751107/helena_phone/main/g/easy.sh)
#
# 기본 동작 (질문 거의 없음):
#   1) Termux 패키지
#   2) Ubuntu proot (없으면 설치)
#   3) Ubuntu 안에서 /root/work 에 helena_phone 클론
#   4) 시작 치트시트 출력 + 저장
#
# 명의 기본값 = 큰누나 계정 (변수로 변경 가능)
#   OWNER_GITHUB  WORK_DIR  TEMPLATE_REPO
# ==============================================================================

set -euo pipefail

OWNER_GITHUB="${OWNER_GITHUB:-helena751107}"
TEMPLATE_REPO="${TEMPLATE_REPO:-helena751107/helena_phone}"
WORK_DIR="${WORK_DIR:-/root/work}"
# 초심자: 토큰 없이 public clone (나중에 push 할 때만 토큰)

G() { printf '\033[0;32m✅ %s\033[0m\n' "$*"; }
Y() { printf '\033[1;33m⚠️  %s\033[0m\n' "$*"; }
B() { printf '\033[0;34m📌 %s\033[0m\n' "$*"; }
R() { printf '\033[0;31m❌ %s\033[0m\n' "$*"; }

banner() {
  cat << EOF

══════════════════════════════════════
  📱 S21 쉬운 설치 (easy)
  앱 2개 깐 뒤 → 이 스크립트 1번
  명의 템플릿: ${TEMPLATE_REPO}
══════════════════════════════════════

EOF
}

need_termux() {
  if [ -z "${PREFIX:-}" ] && [ ! -d /data/data/com.termux ]; then
    R "Termux 앱 안에서 실행하세요."
    echo "  1) F-Droid 설치: https://f-droid.org/"
    echo "  2) Termux 검색 → 설치"
    echo "  3) Termux:API 도 설치"
    echo "  4) Termux 열고 아래 한 줄 다시:"
    echo "     bash <(curl -sL https://raw.githubusercontent.com/helena751107/helena_phone/main/g/easy.sh)"
    exit 1
  fi
}

step_termux_host() {
  B "Termux 패키지…"
  pkg update -y 2>/dev/null || true
  pkg install -y proot-distro git curl termux-api 2>/dev/null || pkg install -y proot-distro git curl
  G "패키지 OK"

  if command -v termux-setup-storage >/dev/null 2>&1; then
    termux-setup-storage 2>/dev/null || true
    G "저장소 권한 (팝업 뜨면 허용)"
  fi

  if proot-distro list 2>/dev/null | grep -qi ubuntu; then
    G "Ubuntu 이미 있음"
  else
    B "Ubuntu 설치 중 (몇 분, 화면 가만히)…"
    proot-distro install ubuntu
    G "Ubuntu OK"
  fi
}

# runs inside ubuntu via proot-distro login
ubuntu_bootstrap() {
  set -e
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y -qq git curl ca-certificates python3 2>/dev/null || apt-get install -y git curl ca-certificates python3

  WORK_DIR="${WORK_DIR:-/root/work}"
  TEMPLATE_REPO="${TEMPLATE_REPO:-helena751107/helena_phone}"
  OWNER_GITHUB="${OWNER_GITHUB:-helena751107}"

  if [ -d "$WORK_DIR/.git" ]; then
    echo "✅ 이미 워크스페이스 있음: $WORK_DIR"
    git -C "$WORK_DIR" pull --ff-only 2>/dev/null || true
  else
    echo "📌 클론 ${TEMPLATE_REPO} → ${WORK_DIR}"
    git clone --depth 1 "https://github.com/${TEMPLATE_REPO}.git" "$WORK_DIR"
  fi

  mkdir -p "$WORK_DIR/configs"
  cat > "$WORK_DIR/S21-START.txt" << EOF
════════════════════════════════════
S21 시작 쪽지 (초심자)
════════════════════════════════════
명의(OWNER) 템플릿: ${OWNER_GITHUB}
폴더: ${WORK_DIR}

매일 하는 일:
  1) Termux 실행
  2) 입력:  proot-distro login ubuntu
  3) 입력:  cd /root/work
  4) 웹 보기(폰 브라우저):
     https://${OWNER_GITHUB}.github.io/helena_phone/

나중에 필요할 때만 (필수로 안 함):
  · GitHub 토큰, DeepSeek 키
  · bash g/install.sh   ← 고급 설치
  · claude / grok

도움말:
  cat /root/work/install-guide.html   (웹)
  cat /root/work/S21-START.txt
════════════════════════════════════
EOF

  # tiny env example without secrets
  cat > "$WORK_DIR/configs/easy-env.sh" << EOF
# 초심자용 — 나중에 키 넣을 때만 수정
export OWNER_GITHUB="${OWNER_GITHUB}"
export TEMPLATE_REPO="${TEMPLATE_REPO}"
export WORK_DIR="${WORK_DIR}"
# export GITHUB_USER="작업계정"
# export GITHUB_TOKEN="ghp_..."
# export DEEPSEEK_API_KEY="sk-..."
EOF

  echo ""
  echo "══════════════════════════════════════"
  echo "  ✅ 쉬운 설치 끝"
  echo "══════════════════════════════════════"
  echo ""
  cat "$WORK_DIR/S21-START.txt"
  echo ""
  echo "지금 바로:"
  echo "  cd ${WORK_DIR} && ls"
  echo "브라우저:"
  echo "  https://${OWNER_GITHUB}.github.io/helena_phone/"
  echo ""
}

# ── MAIN ───────────────────────────────────────────────────────────────────
banner

# Already inside Ubuntu proot?
if [ -f /etc/os-release ] && grep -qi ubuntu /etc/os-release && [ ! -d /data/data/com.termux ]; then
  B "Ubuntu 안에서 실행 중 → 워크스페이스만 준비"
  ubuntu_bootstrap
  exit 0
fi

need_termux
step_termux_host

B "Ubuntu 들어가서 레포 준비…"
# export vars into ubuntu
proot-distro login ubuntu -- bash -lc "
  export WORK_DIR='${WORK_DIR}'
  export TEMPLATE_REPO='${TEMPLATE_REPO}'
  export OWNER_GITHUB='${OWNER_GITHUB}'
  $(declare -f ubuntu_bootstrap)
  ubuntu_bootstrap
"

cat << EOF

▶ 다음 한 줄만 기억하세요 (매일):

   proot-distro login ubuntu
   cd /root/work
   cat S21-START.txt

▶ 웹 (성공 확인):

   https://${OWNER_GITHUB}.github.io/helena_phone/

▶ 키·푸시·에이전트는 나중에:
   매뉴얼 install-guide.html 또는 g/install.sh

EOF
