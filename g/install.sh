#!/usr/bin/env bash
# ==============================================================================
# g/install.sh — S21 Phone 1줄 설치기 v3 (누나 명의 · 변수화 · 초심자)
# ==============================================================================
# 에이전트 마크 문서: _notebook/41-beginner-install-manual_Grok.md
#
# 한 줄 (템플릿 클론 · 읽기 위주):
#   bash <(curl -sL https://raw.githubusercontent.com/helena751107/helena_phone/main/g/install.sh)
#
# 권장 (변수 넣고 실행 · 누나 폰 / Boss 작업 폰 공통):
#   export OWNER_GITHUB="helena751107"          # 명의(큰누나) 계정
#   export WORK_GITHUB="dtslib1979"             # 실제 push 하는 작업 계정(선택)
#   export GITHUB_TOKEN="ghp_...."              # WORK 또는 OWNER 토큰
#   export GITHUB_REPO="helena_phone"           # 워크스페이스 레포 이름
#   export DEEPSEEK_API_KEY="sk-...."           # 선택
#   export TG_TOKEN="..." TG_CHAT="..."         # 선택
#   bash <(curl -sL https://raw.githubusercontent.com/helena751107/helena_phone/main/g/install.sh)
#
# 철학: 모든 공개 표면의 명의는 OWNER. Boss는 콜라보/방문 설치로 핸드오프.
# ==============================================================================

set -euo pipefail

# ── 생태계 변수 (환경변수로 덮어쓰기) ───────────────────────────────────────
OWNER_GITHUB="${OWNER_GITHUB:-helena751107}"           # 명의 · 템플릿 소유자
OWNER_NAME="${OWNER_NAME:-큰누나}"                     # 표시용 이름
WORK_GITHUB="${WORK_GITHUB:-${GITHUB_USER:-}}"         # 작업 push 계정 (비우면 OWNER)
GITHUB_USER="${GITHUB_USER:-${WORK_GITHUB:-$OWNER_GITHUB}}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
GITHUB_REPO="${GITHUB_REPO:-helena_phone}"
TEMPLATE_REPO="${TEMPLATE_REPO:-helena751107/helena_phone}"
WORK_DIR="${WORK_DIR:-/root/work}"
DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-}"
TG_TOKEN="${TG_TOKEN:-}"
TG_CHAT="${TG_CHAT:-}"
INSTALL_GROK="${INSTALL_GROK:-0}"                      # 1이면 grok 안내만 (수동 로그인)
SKIP_CLAUDE="${SKIP_CLAUDE:-0}"
SKIP_MCP="${SKIP_MCP:-0}"
CLONE_SATELLITES="${CLONE_SATELLITES:-0}"               # 1이면 위성 4레포 안내

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'
BOLD='\033[1m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✅${NC} $*"; }
warn() { echo -e "${YELLOW}⚠️${NC}  $*"; }
fail() { echo -e "${RED}❌${NC} $*"; }
info() { echo -e "${BLUE}📌${NC} $*"; }

banner() {
  echo ""
  echo -e "${BOLD}═══════════════════════════════════════════════════${NC}"
  echo -e "${BOLD}  📱 S21 Phone — 1줄 설치기 v3${NC}"
  echo -e "${BOLD}  낡은 폰 → Termux → Ubuntu → 워크스페이스${NC}"
  echo -e "${BOLD}  명의(OWNER)=${OWNER_GITHUB}  작업(USER)=${GITHUB_USER}${NC}"
  echo -e "${BOLD}  비용: 런타임 \$0 축 | 준비: 폰+WiFi+GitHub${NC}"
  echo -e "${BOLD}═══════════════════════════════════════════════════${NC}"
  echo ""
}

check_vars() {
  echo "─── 0단계: 변수 확인 ───"
  info "OWNER_GITHUB(명의)=${OWNER_GITHUB}"
  info "GITHUB_USER(작업)=${GITHUB_USER}"
  info "GITHUB_REPO=${GITHUB_REPO}"
  info "TEMPLATE_REPO=${TEMPLATE_REPO}"
  info "WORK_DIR=${WORK_DIR}"

  if [ -z "$GITHUB_USER" ]; then
    echo -n "  작업용 GitHub 사용자명: "
    read -r GITHUB_USER
  fi
  ok "작업 계정: ${GITHUB_USER}"

  if [ -z "$GITHUB_TOKEN" ]; then
    warn "GITHUB_TOKEN 없음 — clone은 가능, push는 나중에"
    echo "  발급: GitHub → Settings → Developer settings → PAT (repo)"
    echo -n "  토큰 (Enter=스킵): "
    read -r GITHUB_TOKEN || true
  fi
  [ -n "$GITHUB_TOKEN" ] && ok "토큰 설정됨" || warn "토큰 없음"

  [ -n "$DEEPSEEK_API_KEY" ] && ok "DeepSeek 키 있음" || warn "DEEPSEEK_API_KEY 없음 (cc 구동 시 필요)"
  [ -n "$TG_TOKEN" ] && [ -n "$TG_CHAT" ] && ok "Telegram 설정됨" || warn "TG 선택 사항"
}

check_env() {
  echo ""
  echo "─── 1단계: 환경 체크 ───"
  # Termux often reports Android; some builds differ
  if [ "$(uname -o 2>/dev/null)" != "Android" ] && [ -z "${TERMUX_VERSION:-}" ] && [ ! -d /data/data/com.termux ]; then
    fail "Android/Termux에서 실행하세요 (F-Droid Termux 권장)"
    exit 1
  fi
  ok "Android/Termux 환경"

  if [ -z "${TERMUX_VERSION:-}" ]; then
    warn "TERMUX_VERSION 비어 있음 — Termux 앱 안에서 실행 중인지 확인"
  else
    ok "Termux ${TERMUX_VERSION}"
  fi

  local free_mb
  free_mb=$(df /data 2>/dev/null | awk 'NR==2{print int($4/1024)}' || echo 0)
  if [ "$free_mb" -gt 0 ] && [ "$free_mb" -lt 5120 ]; then
    warn "저장공간 ${free_mb}MB (5GB 권장)"
  else
    ok "저장공간 확인 (${free_mb}MB)"
  fi

  if ping -c1 -W3 8.8.8.8 >/dev/null 2>&1 || ping -c1 -W3 github.com >/dev/null 2>&1; then
    ok "인터넷 연결"
  else
    fail "인터넷 필요"; exit 1
  fi
}

install_pkgs() {
  echo ""
  echo "─── 2단계: Termux 패키지 ───"
  if command -v pkg >/dev/null 2>&1; then
    pkg update -y >/dev/null 2>&1 && ok "pkg update" || warn "pkg update 경고"
    for p in proot-distro git curl; do
      if command -v "$p" >/dev/null 2>&1; then ok "$p"
      else info "$p 설치..."; pkg install -y "$p" >/dev/null 2>&1 && ok "$p" || warn "$p 실패"
      fi
    done
    pkg install -y termux-api >/dev/null 2>&1 && ok "termux-api" || warn "termux-api (앱도 설치 권장)"
  else
    warn "pkg 없음 — 이미 proot 안이거나 PC 환경"
  fi
}

install_proot() {
  echo ""
  echo "─── 3단계: proot Ubuntu ───"
  if ! command -v proot-distro >/dev/null 2>&1; then
    warn "proot-distro 없음 — Termux에서 pkg install proot-distro"
    return 0
  fi
  if proot-distro list 2>/dev/null | grep -qi ubuntu; then
    ok "proot Ubuntu 이미 있음"
  else
    info "ubuntu 설치 중 (수 분)..."
    proot-distro install ubuntu && ok "Ubuntu 설치" || { fail "Ubuntu 설치 실패"; exit 1; }
  fi
}

# 실제 작업은 proot 안에서. Termux 호스트면 login 후 재실행 안내
in_proot() {
  # rough: not android path for home
  [ -f /etc/os-release ] && grep -qi ubuntu /etc/os-release 2>/dev/null
}

setup_repo() {
  echo ""
  echo "─── 4단계: 워크스페이스 클론 ───"
  mkdir -p "$(dirname "$WORK_DIR")"

  if [ -d "$WORK_DIR/.git" ]; then
    ok "이미 있음: $WORK_DIR"
    git -C "$WORK_DIR" pull --ff-only 2>/dev/null && ok "git pull" || warn "pull 스킵"
  else
    local url
    if [ -n "$GITHUB_TOKEN" ]; then
      url="https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/${TEMPLATE_REPO}.git"
    else
      url="https://github.com/${TEMPLATE_REPO}.git"
    fi
    info "clone ${TEMPLATE_REPO} → ${WORK_DIR}"
    git clone "$url" "$WORK_DIR" && ok "클론 완료" || { fail "클론 실패"; exit 1; }
  fi

  # remote: 작업 계정의 포크/동일 레포로 맞출 때
  if [ -n "$GITHUB_TOKEN" ] && [ -n "$GITHUB_USER" ]; then
    git -C "$WORK_DIR" remote set-url origin \
      "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${GITHUB_REPO}.git" 2>/dev/null \
      && ok "origin → ${GITHUB_USER}/${GITHUB_REPO}" \
      || warn "remote 유지 (템플릿 origin)"
  fi

  # 환경 스니펫 기록 (토큰은 파일에 넣지 않음)
  mkdir -p "$WORK_DIR/configs"
  cat > "$WORK_DIR/configs/helena-env.example.sh" << EOF
# 복사: cp configs/helena-env.example.sh configs/helena-env.sh && nano configs/helena-env.sh
# source configs/helena-env.sh
export OWNER_GITHUB="${OWNER_GITHUB}"
export OWNER_NAME="${OWNER_NAME}"
export WORK_GITHUB="${GITHUB_USER}"
export GITHUB_USER="${GITHUB_USER}"
export GITHUB_REPO="${GITHUB_REPO}"
export TEMPLATE_REPO="${TEMPLATE_REPO}"
export WORK_DIR="${WORK_DIR}"
# export GITHUB_TOKEN="ghp_..."          # 파일에 넣지 말고 세션 export 권장
# export DEEPSEEK_API_KEY="sk-..."
# export TG_TOKEN="..." TG_CHAT="..."
EOF
  ok "configs/helena-env.example.sh 작성"
}

setup_ubuntu_pkgs() {
  echo ""
  echo "─── 5단계: Ubuntu 패키지 (proot 안) ───"
  if ! in_proot; then
    warn "지금 Termux 호스트일 수 있음. Ubuntu 안에서는:"
    echo "  proot-distro login ubuntu"
    echo "  apt update && apt install -y git curl nodejs npm python3 python3-pip"
    return 0
  fi
  apt-get update -qq >/dev/null 2>&1 || true
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq git curl ca-certificates python3 python3-pip >/dev/null 2>&1 \
    && ok "git curl python3" || warn "apt 일부 실패"
  if ! command -v node >/dev/null 2>&1; then
    info "nodejs 설치 시도..."
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq nodejs npm >/dev/null 2>&1 \
      && ok "nodejs" || warn "nodejs 수동 설치 필요"
  else
    ok "node $(node -v 2>/dev/null || echo ok)"
  fi
}

setup_claude() {
  echo ""
  echo "─── 6단계: Claude Code + DeepSeek ───"
  if [ "$SKIP_CLAUDE" = "1" ]; then warn "SKIP_CLAUDE=1"; return 0; fi

  mkdir -p "$WORK_DIR/configs"
  cat > "$WORK_DIR/configs/deepseek.env" << 'DSEOF'
# source this file inside proot Ubuntu
export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
export ANTHROPIC_MODEL=deepseek-chat
DSEOF
  if [ -n "$DEEPSEEK_API_KEY" ]; then
    echo "export ANTHROPIC_API_KEY=${DEEPSEEK_API_KEY}" >> "$WORK_DIR/configs/deepseek.env"
    echo "export DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}" >> "$WORK_DIR/configs/deepseek.env"
    ok "DeepSeek 키를 deepseek.env에 기록"
  else
    warn "키 없음 — configs/deepseek.env 에 나중에 추가"
  fi

  if command -v npm >/dev/null 2>&1; then
    if command -v claude >/dev/null 2>&1; then ok "claude 이미 있음"
    else
      info "npm i -g @anthropic-ai/claude-code ..."
      npm install -g @anthropic-ai/claude-code >/dev/null 2>&1 && ok "Claude Code" || warn "Claude Code 설치 실패 — 수동"
    fi
  else
    warn "npm 없음 — Ubuntu 안 패키지 후 재실행"
  fi

  if [ -f "$HOME/.bashrc" ]; then
    grep -q "deepseek.env" "$HOME/.bashrc" 2>/dev/null \
      || echo "source ${WORK_DIR}/configs/deepseek.env 2>/dev/null" >> "$HOME/.bashrc"
    ok ".bashrc 에 deepseek.env 연결"
  fi
}

setup_mcp() {
  echo ""
  echo "─── 7단계: phone-mcp (선택) ───"
  if [ "$SKIP_MCP" = "1" ]; then warn "SKIP_MCP=1"; return 0; fi
  local mcp_dir="/tmp/phone-mcp-server"
  if [ ! -f "$mcp_dir/server.py" ]; then
    git clone --depth 1 https://github.com/htekdev/phone-mcp-server "$mcp_dir" >/dev/null 2>&1 \
      && ok "phone-mcp-server 클론" || warn "mcp 클론 실패"
  else
    ok "phone-mcp 이미 있음"
  fi
  mkdir -p "$HOME/.claude"
  if [ -f "$WORK_DIR/configs/settings.json" ]; then
    cp "$WORK_DIR/configs/settings.json" "$HOME/.claude/settings.json" 2>/dev/null && ok "MCP settings 복사"
  fi
}

setup_telegram() {
  echo ""
  echo "─── 8단계: Telegram ───"
  if [ -n "$TG_TOKEN" ] && [ -n "$TG_CHAT" ]; then
    ok "TG_TOKEN / TG_CHAT 설정됨"
    if [ -x "$WORK_DIR/tg.sh" ] || [ -f "$WORK_DIR/tg.sh" ]; then
      chmod +x "$WORK_DIR/tg.sh" 2>/dev/null || true
      (cd "$WORK_DIR" && TG_TOKEN="$TG_TOKEN" TG_CHAT="$TG_CHAT" bash tg.sh "✅ S21 install v3 완료 · OWNER=${OWNER_GITHUB} USER=${GITHUB_USER}") 2>/dev/null \
        && ok "테스트 메시지 전송" || warn "tg 테스트 스킵"
    fi
  else
    warn "TG 없음 — @BotFather 후 export TG_TOKEN TG_CHAT"
  fi
}

run_health() {
  echo ""
  echo "─── 9단계: 건강 검진 ───"
  if [ -f "$WORK_DIR/phone-health.sh" ]; then
    chmod +x "$WORK_DIR/phone-health.sh"
    bash "$WORK_DIR/phone-health.sh" 2>&1 | tail -8 || warn "검진 경고"
    ok "phone-health 실행"
  else
    warn "phone-health.sh 없음"
  fi
}

show_satellites() {
  echo ""
  echo "─── 위성 레포 (참고) ───"
  cat << EOF
  명의 계정 아래 공개 표면:
    https://github.com/${OWNER_GITHUB}/helena_phone
    https://github.com/${OWNER_GITHUB}/helana_log
    https://github.com/${OWNER_GITHUB}/helana-faith
    https://github.com/${OWNER_GITHUB}/helena-piano
    https://github.com/${OWNER_GITHUB}/helena-psycare

  Pages:
    https://${OWNER_GITHUB}.github.io/helena_phone/
    https://${OWNER_GITHUB}.github.io/helana_log/
    ...
EOF
  if [ "$CLONE_SATELLITES" = "1" ]; then
    info "CLONE_SATELLITES=1 — /root/sites 에 클론 시도"
    mkdir -p /root/sites
    for r in helana_log helana-faith helena-piano helena-psycare; do
      [ -d "/root/sites/$r/.git" ] && continue
      git clone "https://github.com/${OWNER_GITHUB}/${r}.git" "/root/sites/$r" 2>/dev/null \
        && ok "$r" || warn "$r 클론 실패"
    done
  fi
}

summary() {
  echo ""
  echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
  echo -e "${GREEN}  ✅ 설치 플로우 완료 (v3)${NC}"
  echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
  cat << EOF

  명의(OWNER):  ${OWNER_GITHUB} (${OWNER_NAME})
  작업(USER):   ${GITHUB_USER}
  워크스페이스: ${WORK_DIR}
  템플릿:       ${TEMPLATE_REPO}

  다음 명령 (Termux):
    proot-distro login ubuntu
    cd ${WORK_DIR}
    source configs/deepseek.env   # 키 넣었다면
    source configs/helena-env.example.sh
    claude                        # 또는 grok / bash scripts/ds.sh

  검진:  bash phone-health.sh
  보고:  bash tg.sh '메시지'
  돌봄:  bash care/care-setup.sh
  매뉴얼: cat _notebook/41-beginner-install-manual_Grok.md
          또는 https://${OWNER_GITHUB}.github.io/helena_phone/install-guide.html

  Pages: https://${OWNER_GITHUB}.github.io/${GITHUB_REPO}/

EOF
}

main() {
  banner
  check_vars
  check_env
  install_pkgs
  install_proot

  if ! in_proot; then
    echo ""
    warn "지금은 Termux 호스트 단계까지 완료했을 수 있습니다."
    echo "  아래를 실행한 뒤, Ubuntu 안에서 이 스크립트를 다시 돌리세요:"
    echo ""
    echo "  proot-distro login ubuntu"
    echo "  apt update && apt install -y git curl nodejs npm python3"
    echo "  export OWNER_GITHUB=${OWNER_GITHUB} GITHUB_USER=${GITHUB_USER} GITHUB_REPO=${GITHUB_REPO}"
    echo "  export GITHUB_TOKEN=... DEEPSEEK_API_KEY=..."
    echo "  bash <(curl -sL https://raw.githubusercontent.com/${TEMPLATE_REPO}/main/g/install.sh)"
    echo ""
  fi

  setup_ubuntu_pkgs
  setup_repo
  setup_claude
  setup_mcp
  setup_telegram
  run_health
  show_satellites
  summary
}

main "$@"
