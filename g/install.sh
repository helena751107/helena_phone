#!/usr/bin/env bash
# ==============================================================================
# g/install.sh — S21 Phone 1줄 설치기 v2 (사용자 변수화)
# ==============================================================================
# 사용법:
#   curl -sL https://raw.github.com/helena751107/helena_phone/main/g/install.sh | bash
#
#   또는 변수 지정:
#   GITHUB_USER="내아이디" GITHUB_TOKEN="ghp_..." bash install.sh
#
# 이 스크립트는:
#   갤럭시 폰 1대를 AI 워크스테이션 + 블로그/유튜브 발행기 + 돌봄 데몬으로
#   변환한다. 필요한 건 안드로이드 폰 + WiFi + GitHub 계정 뿐. 비용 0원.
# ==============================================================================

set -euo pipefail

# ── 사용자 변수 (환경변수 or 기본값) ──────────────────────────────────────
GITHUB_USER="${GITHUB_USER:-}"           # GitHub 사용자명 (예: helena751107)
GITHUB_TOKEN="${GITHUB_TOKEN:-}"         # GitHub Personal Access Token
GITHUB_REPO="${GITHUB_REPO:-s21-work}"   # 레포 이름 (기본값)
DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-}" # DeepSeek API 키 (없으면 나중에)
TG_TOKEN="${TG_TOKEN:-}"                 # Telegram 봇 토큰
TG_CHAT="${TG_CHAT:-}"                   # Telegram chat ID

# ── 색상 ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'
BOLD='\033[1m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✅${NC} $*"; }
warn() { echo -e "${YELLOW}⚠️${NC}  $*"; }
fail() { echo -e "${RED}❌${NC} $*"; }
info() { echo -e "${BLUE}📌${NC} $*"; }

# ── 배너 ──────────────────────────────────────────────────────────────────
banner() {
  echo ""
  echo -e "${BOLD}═══════════════════════════════════════════════════${NC}"
  echo -e "${BOLD}  📱 S21 Phone — 1줄 설치기 v2${NC}"
  echo -e "${BOLD}  폰 → AI 워크스테이션 → 블로그/유튜브/돌봄데몬${NC}"
  echo -e "${BOLD}  비용: 0원 | 입력: 100% 음성 | 준비물: 폰+WiFi+GitHub${NC}"
  echo -e "${BOLD}═══════════════════════════════════════════════════${NC}"
  echo ""
}

# ── 0단계: 변수 확인 ──────────────────────────────────────────────────────
check_vars() {
  echo "─── 0단계: 사용자 설정 확인 ───"

  if [ -z "$GITHUB_USER" ]; then
    echo ""
    info "GitHub 사용자명이 없습니다."
    echo -n "  GitHub 사용자명을 입력하세요: "
    read -r GITHUB_USER
  fi
  ok "GitHub 사용자: ${GITHUB_USER}"

  if [ -z "$GITHUB_TOKEN" ]; then
    echo ""
    warn "GITHUB_TOKEN이 없습니다."
    echo "  발급 방법: GitHub → Settings → Developer settings → Personal access tokens"
    echo "  권한: repo, workflow"
    echo "  (나중에 설정하려면 지금은 Enter)"
    echo -n "  GitHub 토큰 (선택): "
    read -r GITHUB_TOKEN
  fi
  [ -n "$GITHUB_TOKEN" ] && ok "GitHub 토큰 설정됨" || warn "토큰 없음 — git push 수동 필요"

  if [ -z "$DEEPSEEK_API_KEY" ]; then
    warn "DEEPSEEK_API_KEY 없음 — Claude Code 구동 시 필요"
    echo "  발급: platform.deepseek.com → API Keys"
  else
    ok "DeepSeek API 키 설정됨"
  fi
}

# ── 1단계: 환경 체크 ──────────────────────────────────────────────────────
check_env() {
  echo ""
  echo "─── 1단계: 환경 체크 ───"

  [ "$(uname -o 2>/dev/null)" = "Android" ] || { fail "Android/Termux에서만 실행"; exit 1; }
  ok "Android 환경"

  [ -n "${TERMUX_VERSION:-}" ] || { fail "Termux 필요 (F-Droid: termux.com)"; exit 1; }
  ok "Termux ${TERMUX_VERSION}"

  local free_mb=$(df /data 2>/dev/null | awk 'NR==2{print int($4/1024)}' || echo 0)
  [ "$free_mb" -lt 5120 ] && warn "저장공간 ${free_mb}MB (5GB 권장)" || ok "저장공간 ${free_mb}MB"

  ping -c1 -W3 8.8.8.8 >/dev/null 2>&1 || { fail "인터넷 연결 필요"; exit 1; }
  ok "인터넷 연결"
}

# ── 2단계: Termux 패키지 ──────────────────────────────────────────────────
install_pkgs() {
  echo ""
  echo "─── 2단계: Termux 패키지 ───"
  pkg update -y >/dev/null 2>&1 && ok "pkg update"

  for p in proot-distro termux-api git curl; do
    command -v "$p" >/dev/null 2>&1 && ok "$p" || { info "$p 설치..."; pkg install -y "$p" >/dev/null 2>&1; }
  done

  command -v termux-battery-status >/dev/null 2>&1 || { info "termux-api CLI 설치..."; pkg install -y termux-api >/dev/null 2>&1; }
  ok "termux-api CLI"
}

# ── 3단계: proot Ubuntu ───────────────────────────────────────────────────
install_proot() {
  echo ""
  echo "─── 3단계: proot Ubuntu ───"
  if proot-distro list 2>/dev/null | grep -q ubuntu; then
    ok "proot Ubuntu 이미 존재"
  else
    info "proot-distro ubuntu 설치 (수 분)..."
    proot-distro install ubuntu && ok "Ubuntu 설치 완료" || { fail "실패"; exit 1; }
  fi
}

# ── 4단계: GitHub 레포 클론 또는 생성 ─────────────────────────────────────
setup_repo() {
  echo ""
  echo "─── 4단계: GitHub 레포 ───"
  local target="/root/work"

  if [ -d "$target/.git" ]; then
    ok "이미 클론됨: $target"
    git -C "$target" pull --ff-only 2>/dev/null && ok "pull 완료" || warn "pull 스킵"
    return
  fi

  # helena_phone을 템플릿으로 클론하거나 새 레포 생성
  if [ -n "$GITHUB_TOKEN" ]; then
    info "helena_phone 템플릿 클론 → 사용자 레포로 설정..."
    git clone "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/helena751107/helena_phone.git" "$target" 2>/dev/null && {
      ok "helena_phone 클론 완료"
      # remote를 사용자 레포로 변경
      git -C "$target" remote set-url origin "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${GITHUB_REPO}.git"
      ok "remote → github.com/${GITHUB_USER}/${GITHUB_REPO}"
      return
    }
  fi

  # 토큰 없으면 템플릿만 클론
  git clone "https://github.com/helena751107/helena_phone.git" "$target" 2>/dev/null && {
    warn "토큰 없이 클론. GitHub에 push하려면 토큰 설정 필요"
    ok "helena_phone 클론 완료 (읽기 전용)"
  } || fail "클론 실패"
}

# ── 5단계: Claude Code + DeepSeek ─────────────────────────────────────────
setup_claude() {
  echo ""
  echo "─── 5단계: Claude Code + DeepSeek Radar ───"

  if ! command -v claude >/dev/null 2>&1; then
    info "npm install -g @anthropic-ai/claude-code..."
    npm install -g @anthropic-ai/claude-code >/dev/null 2>&1 && ok "Claude Code 설치" || warn "설치 실패"
  else
    ok "Claude Code 설치됨"
  fi

  # DeepSeek 환경변수
  cat > /root/work/configs/deepseek.env << 'DSEOF'
export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
export ANTHROPIC_MODEL=deepseek-v4-pro
DSEOF

  if [ -n "$DEEPSEEK_API_KEY" ]; then
    echo "export DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}" >> /root/work/configs/deepseek.env
    ok "DeepSeek 키 설정"
  fi

  grep -q "deepseek.env" ~/.bashrc 2>/dev/null || echo "source /root/work/configs/deepseek.env" >> ~/.bashrc
  ok ".bashrc 등록"
}

# ── 6단계: phone-mcp-server ───────────────────────────────────────────────
setup_mcp() {
  echo ""
  echo "─── 6단계: phone-mcp-server (18개 폰 통제 도구) ───"
  local mcp_dir="/tmp/phone-mcp-server"

  [ -f "$mcp_dir/server.py" ] || git clone https://github.com/htekdev/phone-mcp-server "$mcp_dir" >/dev/null 2>&1
  ok "phone-mcp-server 준비"

  # MCP 설정
  mkdir -p ~/.claude
  cp /root/work/configs/settings.json ~/.claude/settings.json 2>/dev/null && ok "MCP 설정 복사"
}

# ── 7단계: Telegram (선택) ────────────────────────────────────────────────
setup_telegram() {
  echo ""
  echo "─── 7단계: Telegram 봇 (선택) ───"

  if [ -n "$TG_TOKEN" ] && [ -n "$TG_CHAT" ]; then
    ok "TG_TOKEN, TG_CHAT 설정됨"
    return
  fi

  warn "Telegram 봇 없음. 작업 보고는 생략됩니다."
  echo "  설정하려면:"
  echo "  1. @BotFather → /newbot → 토큰"
  echo "  2. 봇에게 메시지 1회 전송"
  echo "  3. curl https://api.telegram.org/bot<TOKEN>/getUpdates → chat_id"
  echo "  4. ~/.bashrc: export TG_TOKEN=... TG_CHAT=..."
}

# ── 8단계: 건강 검진 ──────────────────────────────────────────────────────
run_healthcheck() {
  echo ""
  echo "─── 8단계: 첫 건강 검진 ───"
  chmod +x /root/work/phone-health.sh 2>/dev/null
  bash /root/work/phone-health.sh 2>&1 | tail -5 && ok "건강 검진 완료" || warn "phone-health.sh 없음"
}

# ── 요약 ──────────────────────────────────────────────────────────────────
summary() {
  echo ""
  echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
  echo -e "${GREEN}  ✅ 설치 완료!${NC}"
  echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
  echo ""
  echo "  진입: proot-distro login ubuntu → cd /root/work → claude"
  echo "  검진: bash phone-health.sh"
  echo "  보고: bash tg.sh '메시지' (TG 설정 시)"
  echo "  설치: bash care/care-setup.sh (돌봄 데몬)"
  echo ""
  echo "  GitHub: github.com/${GITHUB_USER}/${GITHUB_REPO}"
  echo "  Pages:  ${GITHUB_USER}.github.io/${GITHUB_REPO}/"
  echo ""
  echo "  도움말: cat README.md"
  echo "  헌법:   cat CONSTITUTION.md"
  echo ""
}

# ── MAIN ───────────────────────────────────────────────────────────────────
main() {
  banner
  check_vars
  check_env
  install_pkgs
  install_proot
  setup_repo
  setup_claude
  setup_mcp
  setup_telegram
  run_healthcheck
  summary
}

main "$@"
