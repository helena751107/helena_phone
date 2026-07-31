#!/usr/bin/env bash
# ==============================================================================
# wsl-agent-setup.sh — PC WSL에 S21 Agent 워크스페이스 + Tailscale + Mosh 설치
# ==============================================================================
# 용도: 집 PC WSL Ubuntu → 핸드폰(S21)에서 Mosh로 원격 접속 가능하게
# 사용: bash <(curl -sL https://raw.githubusercontent.com/helena751107/helena_phone/main/scripts/wsl-agent-setup.sh)
#
# 선행 조건:
#   Windows에 Tailscale 설치 + 로그인 완료 (https://tailscale.com/download)
#   WSL Ubuntu 20.04+ 설치 완료 (wsl --install)
#
# 설치 후:
#   핸드폰 Termux: pkg install mosh && mosh user@<pc-tailscale-ip>
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'
BOLD='\033[1m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✅${NC} $*"; }
warn() { echo -e "${YELLOW}⚠️${NC}  $*"; }
fail() { echo -e "${RED}❌${NC} $*"; }
info() { echo -e "${BLUE}📌${NC} $*"; }

# ── 설정 변수 ────────────────────────────────────────────────────────────────
OWNER_GITHUB="${OWNER_GITHUB:-helena751107}"
GITHUB_REPO="${GITHUB_REPO:-helena_phone}"
WORK_DIR="${WORK_DIR:-/root/work}"
DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-}"
SSH_PORT="${SSH_PORT:-2222}"           # WSL SSH 포트 (Windows와 충돌 방지)

banner() {
  echo ""
  echo -e "${BOLD}═══════════════════════════════════════════════════${NC}"
  echo -e "${BOLD}  🖥️  PC WSL → S21 Agent 워크스페이스 설치기${NC}"
  echo -e "${BOLD}  Tailscale + Mosh + DeepSeek + Aider${NC}"
  echo -e "${BOLD}═══════════════════════════════════════════════════${NC}"
  echo ""
}

# ── 1단계: WSL 환경 체크 ─────────────────────────────────────────────────────
check_wsl() {
  echo "─── 1단계: WSL 환경 체크 ───"

  if ! grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null; then
    warn "WSL 환경이 아닌 것 같습니다. 계속 진행할까요? (Enter=진행, Ctrl+C=중단)"
    read -r || true
  else
    ok "WSL 환경 감지됨"
  fi

  if [ "$(id -u)" != "0" ]; then
    fail "root로 실행하세요: sudo bash $0"
    exit 1
  fi
  ok "root 권한"
}

# ── 2단계: Tailscale 설치 ────────────────────────────────────────────────────
install_tailscale() {
  echo ""
  echo "─── 2단계: Tailscale ───"

  if command -v tailscale >/dev/null 2>&1; then
    ok "Tailscale 이미 설치됨 ($(tailscale version 2>/dev/null | head -1))"
    tailscale status >/dev/null 2>&1 && ok "Tailscale 연결됨" || warn "tailscale up 필요할 수 있음"
    return 0
  fi

  info "Tailscale 설치 중..."
  curl -fsSL https://tailscale.com/install.sh | sh >/dev/null 2>&1 && ok "Tailscale 설치 완료" || {
    fail "Tailscale 설치 실패"; return 1
  }

  echo ""
  echo -e "  ${YELLOW}👉 이제 2가지 방법 중 하나로 연결:${NC}"
  echo ""
  echo "  [방법 A · 권장] WSL에서 Windows Tailscale 공유:"
  echo "    Windows에 Tailscale 이미 설치돼 있으면, WSL은 자동으로"
  echo "    Windows의 Tailscale 네트워크를 따라갑니다."
  echo "    (Windows Tailscale이 켜져 있으면 WSL도 같은 네트워크)"
  echo ""
  echo "  [방법 B] WSL 독립 Tailscale:"
  echo "    sudo tailscale up"
  echo ""
}

# ── 3단계: SSH + Mosh 서버 ───────────────────────────────────────────────────
install_ssh_mosh() {
  echo ""
  echo "─── 3단계: SSH + Mosh 서버 ───"

  apt-get update -qq >/dev/null 2>&1

  # SSH
  if command -v sshd >/dev/null 2>&1; then
    ok "SSH 서버 이미 있음"
  else
    info "openssh-server 설치..."
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq openssh-server >/dev/null 2>&1 \
      && ok "SSH 서버 설치" || warn "SSH 설치 실패"
  fi

  # SSH 설정: 보안 + 포트 변경
  SSHD_CONFIG="/etc/ssh/sshd_config"
  if [ -f "$SSHD_CONFIG" ]; then
    cp "$SSHD_CONFIG" "${SSHD_CONFIG}.bak.$(date +%Y%m%d%H%M%S)" 2>/dev/null || true

    # 포트 변경 (Windows RDP와 충돌 방지)
    sed -i "s/^#\?Port .*/Port ${SSH_PORT}/" "$SSHD_CONFIG"
    # root 로그인 허용 (키 인증 권장)
    sed -i 's/^#\?PermitRootLogin .*/PermitRootLogin prohibit-password/' "$SSHD_CONFIG"
    # 비밀번호 인증 허용 (Tailscale 안에서는 안전)
    sed -i 's/^#\?PasswordAuthentication .*/PasswordAuthentication yes/' "$SSHD_CONFIG"
    ok "SSH 설정 업데이트 (Port ${SSH_PORT})"
  fi

  # Mosh
  if command -v mosh-server >/dev/null 2>&1; then
    ok "Mosh 서버 이미 있음"
  else
    info "mosh 설치..."
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq mosh >/dev/null 2>&1 \
      && ok "Mosh 서버 설치" || warn "Mosh 설치 실패"
  fi

  # SSH 재시작
  service ssh restart 2>/dev/null && ok "SSH 서비스 재시작" || warn "SSH 재시작 실패 (수동: sudo service ssh start)"

  # UFW 포트 열기 (있다면)
  if command -v ufw >/dev/null 2>&1; then
    ufw allow "${SSH_PORT}/tcp" 2>/dev/null || true
    ufw allow 60000:61000/udp 2>/dev/null || true   # Mosh UDP 포트
    ok "방화벽 포트 오픈"
  fi
}

# ── 4단계: S21 워크스페이스 클론 ──────────────────────────────────────────────
setup_workspace() {
  echo ""
  echo "─── 4단계: S21 워크스페이스 ───"

  # 필수 패키지
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq git curl python3 python3-pip nodejs npm ca-certificates >/dev/null 2>&1 \
    && ok "기본 패키지" || warn "패키지 일부 실패"

  # 레포 클론
  if [ -d "$WORK_DIR/.git" ]; then
    ok "워크스페이스 이미 있음: $WORK_DIR"
    git -C "$WORK_DIR" pull --ff-only 2>/dev/null && ok "git pull 완료" || warn "pull 스킵"
  else
    info "클론 중: https://github.com/${OWNER_GITHUB}/${GITHUB_REPO}.git"
    mkdir -p "$(dirname "$WORK_DIR")"
    git clone "https://github.com/${OWNER_GITHUB}/${GITHUB_REPO}.git" "$WORK_DIR" \
      && ok "워크스페이스 클론 완료" || { fail "클론 실패"; return 1; }
  fi

  cd "$WORK_DIR"
}

# ── 5단계: Claude Code + DeepSeek ─────────────────────────────────────────────
setup_claude() {
  echo ""
  echo "─── 5단계: Claude Code + DeepSeek ───"

  # DeepSeek 환경 설정
  mkdir -p "$WORK_DIR/configs"
  cat > "$WORK_DIR/configs/deepseek.env" << 'DSEOF'
# source this before running claude or ds.sh
export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
export ANTHROPIC_MODEL=deepseek-chat
DSEOF

  if [ -n "$DEEPSEEK_API_KEY" ]; then
    {
      echo "export ANTHROPIC_API_KEY=${DEEPSEEK_API_KEY}"
      echo "export DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}"
    } >> "$WORK_DIR/configs/deepseek.env"
    ok "DeepSeek 키 설정됨"
  else
    warn "DEEPSEEK_API_KEY 없음 — configs/deepseek.env 에 나중에 추가"
    echo "# export DEEPSEEK_API_KEY=sk-..." >> "$WORK_DIR/configs/deepseek.env"
  fi

  # Claude Code (npm)
  if command -v claude >/dev/null 2>&1; then
    ok "Claude Code 이미 있음"
  else
    info "npm install -g @anthropic-ai/claude-code ..."
    npm install -g @anthropic-ai/claude-code >/dev/null 2>&1 \
      && ok "Claude Code 설치 완료" || warn "Claude Code 설치 실패"
  fi

  # .bashrc 연결
  if [ -f "$HOME/.bashrc" ]; then
    grep -q "deepseek.env" "$HOME/.bashrc" 2>/dev/null \
      || echo "source ${WORK_DIR}/configs/deepseek.env 2>/dev/null" >> "$HOME/.bashrc"
    ok ".bashrc 에 deepseek.env 연결"
  fi
}

# ── 6단계: Aider + DeepSeek ──────────────────────────────────────────────────
setup_aider() {
  echo ""
  echo "─── 6단계: Aider + DeepSeek ───"

  # uv 설치 (없으면)
  if ! command -v uv >/dev/null 2>&1; then
    info "uv 설치 중..."
    curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1 \
      && ok "uv 설치 완료" || warn "uv 설치 실패"
    export PATH="$HOME/.local/bin:${PATH:-}"
  fi

  # Aider 설치
  if command -v aider >/dev/null 2>&1; then
    ok "Aider 이미 있음 ($(aider --version 2>/dev/null || echo ok))"
  elif command -v uv >/dev/null 2>&1; then
    info "uv tool install aider-chat ..."
    uv tool install aider-chat >/dev/null 2>&1 \
      && ok "Aider 설치 완료" || warn "Aider 설치 실패"
  else
    info "pip install aider-chat ..."
    pip3 install aider-chat >/dev/null 2>&1 \
      && ok "Aider 설치 완료" || warn "Aider 설치 실패"
  fi

  # Aider 모델 설정 파일
  cat > "$HOME/.aider.model.settings.yml" << 'YMEOF'
# Aider model settings for DeepSeek
- name: deepseek/deepseek-v4-pro
  edit_format: diff
  extra_params:
    max_tokens: 65536
  weak_model_name: deepseek/deepseek-v4-flash
YMEOF
  ok "Aider 모델 설정 → ~/.aider.model.settings.yml"

  # ds.sh 심링크
  if [ -x "$WORK_DIR/scripts/ds.sh" ]; then
    chmod +x "$WORK_DIR/scripts/ds.sh"
    ln -sf "$WORK_DIR/scripts/ds.sh" /usr/local/bin/ds 2>/dev/null || true
    ok "ds 명령어 → /usr/local/bin/ds"
  fi
}

# ── 7단계: health + tg 테스트 ──────────────────────────────────────────────────
smoke_test() {
  echo ""
  echo "─── 7단계: 연기 테스트 ───"

  if [ -f "$WORK_DIR/phone-health.sh" ]; then
    bash "$WORK_DIR/phone-health.sh" 2>&1 | tail -6 || warn "health 경고"
    ok "phone-health 실행"
  fi

  # WSL 환경 표시
  echo ""
  info " 머신 정보:"
  echo "   호스트: $(hostname 2>/dev/null || echo unknown)"
  echo "   커널:  $(uname -r 2>/dev/null || echo unknown)"
  echo "   CPU:   $(nproc 2>/dev/null || echo unknown) cores"
  echo "   RAM:   $(free -h 2>/dev/null | awk '/Mem/{print $2}' || echo unknown)"
}

# ── 최종 요약 ─────────────────────────────────────────────────────────────────
summary() {
  echo ""
  echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
  echo -e "${GREEN}  ✅ PC WSL Agent 설치 완료${NC}"
  echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"

  # Tailscale IP 확인
  TS_IP=$(tailscale ip -4 2>/dev/null || echo "?.?.?.?")
  HOSTNAME=$(hostname 2>/dev/null || echo "unknown")

  cat << EOF

  📡 접속 정보:
     Tailscale IP: ${TS_IP}
     SSH 포트:     ${SSH_PORT}
     호스트명:     ${HOSTNAME}

  📱 핸드폰(Termux)에서 접속:
     # 1. Termux에 Mosh 설치 (한 번만)
     pkg install mosh

     # 2. 접속!
     mosh root@${TS_IP} --ssh="ssh -p ${SSH_PORT}"

     # 또는 호스트명으로 (Tailscale MagicDNS 켜져 있으면):
     mosh root@${HOSTNAME} --ssh="ssh -p ${SSH_PORT}"

  🖥️  접속 후:
     cd ${WORK_DIR}
     source configs/deepseek.env
     claude          # Claude Code 시작
     ds              # Aider + DeepSeek 시작
     bash tg.sh '📡 PC WSL 접속 완료'

  🔧 Windows 부팅 시 자동 시작:
     # WSL 부팅 시 SSH 자동 시작하려면:
     # /etc/wsl.conf 만들기 (이미 해둠)
     sudo service ssh start

  📋 상태 확인:
     tailscale status    # 네트워크 연결
     service ssh status  # SSH 서버
     mosh-server --help  # Mosh 버전
EOF
}

# ── WSL 자동 시작 설정 ──────────────────────────────────────────────────────────
setup_wsl_autostart() {
  echo ""
  echo "─── WSL 자동 시작 설정 ───"

  cat > /etc/wsl.conf << 'WEOF'
[boot]
systemd=true
command="service ssh start"

[network]
hostname=helena-pc
generateResolvConf=true
WEOF
  ok "/etc/wsl.conf 작성 (SSH 자동 시작)"
}

# ── Windows Tailscale 연동 안내 ────────────────────────────────────────────────
show_tailscale_guide() {
  echo ""
  echo "─── Windows ↔ WSL Tailscale 연동 ───"
  echo ""
  echo "  💡 WSL2는 기본적으로 Windows의 네트워크 스택을 공유합니다."
  echo "     Windows에 Tailscale이 설치돼 있으면, WSL에서도"
  echo "     tailscale IP로 자동 접근 가능합니다."
  echo ""
  echo "  🔍 확인 방법:"
  echo "     Windows PowerShell:  tailscale status"
  echo "     WSL:                  tailscale status"
  echo ""
  echo "  📱 핸드폰에서도 Tailscale 설치 → 같은 계정 로그인 →"
  echo "     세 기기(Windows + WSL + Phone)가 모두 같은 Tailnet."
  echo ""
}

# ── 메인 ──────────────────────────────────────────────────────────────────────
main() {
  banner
  check_wsl
  show_tailscale_guide
  install_tailscale
  install_ssh_mosh
  setup_workspace
  setup_claude
  setup_aider
  setup_wsl_autostart
  smoke_test
  summary
}

main "$@"
