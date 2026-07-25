#!/usr/bin/env bash
# ==============================================================================
# g/install.sh — S21 Phone 1줄 설치기 v1
# ==============================================================================
# 사용법:
#   curl -sL https://raw.github.com/helena751107/helena_phone/main/g/install.sh | bash
#   또는:
#   git clone https://github.com/helena751107/helena_phone && bash helena_phone/g/install.sh
#
# 이 스크립트는:
#   갤럭시 폰 1대를 AI 워크스테이션 + 블로그/유튜브 발행기 + 돌봄 데몬으로
#   변환한다. 필요한 건 안드로이드 폰 + WiFi + GitHub 계정 뿐. 비용 0원.
# ==============================================================================

set -euo pipefail

# ── 색상 ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'
BOLD='\033[1m'; NC='\033[0m'

ok()   { echo -e "${GREEN}✅${NC} $*"; }
warn() { echo -e "${YELLOW}⚠️${NC}  $*"; }
fail() { echo -e "${RED}❌${NC} $*"; }
info() { echo -e "${BLUE}📌${NC} $*"; }
ask()  { echo -ne "${BOLD}❓${NC} $* "; }

# ── 배너 ──────────────────────────────────────────────────────────────────
banner() {
  echo ""
  echo -e "${BOLD}═══════════════════════════════════════════════════${NC}"
  echo -e "${BOLD}  📱 S21 Phone — 1줄 설치기 v1${NC}"
  echo -e "${BOLD}  폰 → AI 워크스테이션 → 블로그/유튜브/돌봄데몬${NC}"
  echo -e "${BOLD}  helena751107.github.io/helena_phone${NC}"
  echo -e "${BOLD}═══════════════════════════════════════════════════${NC}"
  echo ""
}

# ── 체크: 실행 환경 ──────────────────────────────────────────────────────
check_env() {
  echo "─── 0단계: 환경 체크 ───"

  # 안드로이드인가
  if [ "$(uname -o 2>/dev/null)" != "Android" ]; then
    fail "이 스크립트는 Android/Termux에서만 실행됩니다."
    exit 1
  fi
  ok "Android 환경 확인"

  # Termux인가
  if [ -z "${TERMUX_VERSION:-}" ]; then
    fail "Termux에서 실행해주세요. (F-Droid에서 설치: termux.com)"
    exit 1
  fi
  ok "Termux ${TERMUX_VERSION}"

  # 저장공간 (최소 5GB)
  local free_mb
  free_mb=$(df /data 2>/dev/null | awk 'NR==2{print int($4/1024)}' || echo 0)
  if [ "$free_mb" -lt 5120 ]; then
    warn "저장공간 ${free_mb}MB (권장 5GB 이상). 계속 진행합니다."
  else
    ok "저장공간 ${free_mb}MB"
  fi

  # 인터넷
  if ! ping -c1 -W3 8.8.8.8 >/dev/null 2>&1; then
    fail "인터넷 연결 필요"
    exit 1
  fi
  ok "인터넷 연결"
}

# ── 1단계: Termux 패키지 ──────────────────────────────────────────────────
install_termux_pkgs() {
  echo ""
  echo "─── 1단계: Termux 기반 패키지 ───"

  pkg update -y >/dev/null 2>&1 && ok "pkg update 완료" || warn "pkg update 스킵"

  local pkgs="proot-distro termux-api git curl openssh wget python"
  for p in $pkgs; do
    if command -v "$p" >/dev/null 2>&1 || dpkg -s "$p" >/dev/null 2>&1; then
      ok "$p — 이미 설치됨"
    else
      info "$p 설치 중..."
      pkg install -y "$p" >/dev/null 2>&1 && ok "$p 설치 완료" || warn "$p 설치 실패"
    fi
  done

  # termux-api 특별 취급 (CLI 바이너리)
  if ! command -v termux-battery-status >/dev/null 2>&1; then
    info "termux-api CLI 설치 중 (이게 없으면 MCP 18개 도구 전부 ENOENT)..."
    pkg install -y termux-api >/dev/null 2>&1 && ok "termux-api 설치 완료" || warn "설치 실패 — 수동: pkg install termux-api"
  else
    ok "termux-api CLI 준비됨"
  fi
}

# ── 2단계: proot Ubuntu ──────────────────────────────────────────────────
install_proot() {
  echo ""
  echo "─── 2단계: proot Ubuntu 컨테이너 ───"

  if proot-distro list 2>/dev/null | grep -q ubuntu; then
    ok "proot Ubuntu 이미 존재"
  else
    info "proot-distro ubuntu 설치 (수 분 소요)..."
    proot-distro install ubuntu && ok "Ubuntu 설치 완료" || {
      fail "proot 설치 실패"
      exit 1
    }
  fi

  # proot 안에서 기본 패키지
  info "Ubuntu 컨테이너 패키지 설치..."
  proot-distro login ubuntu -- bash -c '
    apt update -y >/dev/null 2>&1
    apt install -y git curl nodejs npm python3 python3-pip python3-venv \
      jq wget ca-certificates build-essential >/dev/null 2>&1
  ' && ok "Ubuntu 기본 패키지 완료" || warn "일부 패키지 실패"
}

# ── 3단계: GitHub 클론 ────────────────────────────────────────────────────
clone_repo() {
  echo ""
  echo "─── 3단계: S21 Phone 레포 클론 ───"

  local repo_url="https://github.com/helena751107/helena_phone.git"
  local target="/root/work"

  if [ -d "$target/.git" ]; then
    ok "이미 클론됨: $target"
    info "git pull로 최신화..."
    git -C "$target" pull --ff-only 2>/dev/null && ok "pull 완료" || warn "pull 스킵"
  else
    info "클론 중: $repo_url → $target"
    mkdir -p "$(dirname "$target")"
    git clone "$repo_url" "$target" && ok "클론 완료" || {
      fail "클론 실패. GitHub 연결을 확인하세요."
      exit 1
    }
  fi
}

# ── 4단계: Claude Code + DeepSeek 설정 ────────────────────────────────────
setup_claude() {
  echo ""
  echo "─── 4단계: Claude Code + DeepSeek Radar ───"

  local target="/root/work"

  # Claude Code 설치 (npm)
  info "Claude Code 설치 확인..."
  if command -v claude >/dev/null 2>&1; then
    ok "Claude Code $(claude --version 2>/dev/null || echo '설치됨')"
  else
    info "npm install -g @anthropic-ai/claude-code..."
    npm install -g @anthropic-ai/claude-code >/dev/null 2>&1 && ok "설치 완료" || warn "설치 실패"
  fi

  # DeepSeek 환경변수
  info "DeepSeek Radar 설정 (Anthropic 과금 우회)..."
  cat > "${target}/configs/deepseek.env" << 'DSEOF'
# DeepSeek Radar — Anthropic API 과금 우회
# ANTHROPIC_BASE_URL만 DeepSeek 엔드포인트로, Claude Code UI/도구는 그대로
export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
export ANTHROPIC_MODEL=deepseek-v4-pro
# ↑ deepseek-chat → deepseek-v4-pro (2026-07-24 변경)
# deepseek-chat이 폐기되면 이 줄만 수정
DSEOF

  # .bashrc에 소스 라인 추가
  if ! grep -q "deepseek.env" ~/.bashrc 2>/dev/null; then
    echo "source ${target}/configs/deepseek.env" >> ~/.bashrc
    ok ".bashrc에 DeepSeek 환경변수 추가"
  fi

  if [ -n "${DEEPSEEK_API_KEY:-}" ]; then
    echo "export DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}" >> "${target}/configs/deepseek.env"
  else
    warn "DEEPSEEK_API_KEY 없음. 수동 설정: export DEEPSEEK_API_KEY=sk-..."
  fi

  # Claude Code 설정
  mkdir -p ~/.claude
  if [ -f "${target}/configs/settings.json" ]; then
    cp "${target}/configs/settings.json" ~/.claude/settings.json
    ok "Claude Code MCP 설정 복사"
  fi
}

# ── 5단계: phone-mcp-server ───────────────────────────────────────────────
setup_mcp() {
  echo ""
  echo "─── 5단계: phone-mcp-server (18개 폰 통제 도구) ───"

  local mcp_dir="/tmp/phone-mcp-server"

  if [ -f "${mcp_dir}/server.py" ]; then
    ok "phone-mcp-server 이미 클론됨"
  else
    info "클론 중..."
    git clone https://github.com/htekdev/phone-mcp-server "$mcp_dir" >/dev/null 2>&1 \
      && ok "클론 완료" || warn "클론 실패"
  fi

  # MCP 설정에 등록
  if [ -f ~/.claude/settings.json ]; then
    info "settings.json에 MCP 등록 확인..."
    if grep -q "3456" ~/.claude/settings.json 2>/dev/null; then
      ok "MCP port 3456 등록됨"
    else
      warn "MCP 등록 필요 — ${target}/configs/settings.json 참조"
    fi
  fi

  # .bashrc 자동시작
  local autostart="bash ${target}/phone-mcp.sh --port 3456"
  if ! grep -q "phone-mcp.sh" ~/.bashrc 2>/dev/null; then
    echo "# phone-mcp-server 자동시작" >> ~/.bashrc
    echo "$autostart" >> ~/.bashrc
    ok "MCP 자동시작 등록"
  fi
}

# ── 6단계: Telegram 봇 설정 ───────────────────────────────────────────────
setup_telegram() {
  echo ""
  echo "─── 6단계: Telegram 보고 봇 ───"

  local target="/root/work"

  if [ -n "${TG_TOKEN:-}" ] && [ -n "${TG_CHAT:-}" ]; then
    ok "TG_TOKEN, TG_CHAT 이미 설정됨"
  else
    echo ""
    warn "Telegram 봇 설정 필요:"
    echo "  1. @BotFather → /newbot → 토큰 복사"
    echo "  2. 봇에게 아무 말이나 1회 전송"
    echo "  3. curl https://api.telegram.org/bot<TOKEN>/getUpdates → chat_id 확인"
    echo ""

    if [ -f "${target}/configs/secrets-template.env" ]; then
      info "secrets-template.env 복사 → .secrets.env"
      cp "${target}/configs/secrets-template.env" "${target}/.secrets.env"
    fi

    info "이후 .secrets.env 에 TG_TOKEN, TG_CHAT 입력"
  fi

  # tg.sh 실행 권한
  chmod +x "${target}/tg.sh" 2>/dev/null && ok "tg.sh 실행 권한 설정"
}

# ── 7단계: 건강 검진 ──────────────────────────────────────────────────────
run_healthcheck() {
  echo ""
  echo "─── 7단계: 첫 건강 검진 ───"

  local target="/root/work"

  if [ -f "${target}/phone-health.sh" ]; then
    chmod +x "${target}/phone-health.sh"
    info "27개 항목 검진 실행..."
    bash "${target}/phone-health.sh" 2>&1 | tail -5
    ok "건강 검진 완료 → _notebook/health/ 에 JSON 저장됨"
  else
    warn "phone-health.sh 없음"
  fi
}

# ── 8단계: CONSTITUTION 출력 ──────────────────────────────────────────────
print_constitution() {
  echo ""
  echo "═══════════════════════════════════════════════════"
  echo -e "${BOLD}  📜 CONSTITUTION.md — 핵심 조항${NC}"
  echo "═══════════════════════════════════════════════════"
  echo ""
  echo "  제0장: 👑 HELENA = Boss (최종 의사결정권자)"
  echo "  제1조:  루팅/Shizuku 전면 금지"
  echo "  제2조:  코드는 선물 — 저작권 무의미"
  echo "  제3조:  스캐폴드 우선 — 일단 작동, 나중에 개선"
  echo "  제5조:  AI 출력은 전부 1차 가설"
  echo "  제7조:  핸드오프가 곧 성공 — 대필작가는 영원하지 않다"
  echo "  제8조:  Layer A(인간) / Layer B(STT+에이전트)"
  echo ""
  echo "  전체 헌법: ${target}/CONSTITUTION.md"
  echo ""
  echo -e "${BOLD}  이 시스템의 주인은 큰누나입니다.${NC}"
  echo -e "${BOLD}  사용자는 대필작가이자 간병인입니다.${NC}"
  echo "═══════════════════════════════════════════════════"
}

# ── 최종 요약 ──────────────────────────────────────────────────────────────
summary() {
  local target="/root/work"

  echo ""
  echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
  echo -e "${GREEN}  ✅ S21 Phone 설치 완료!${NC}"
  echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
  echo ""
  echo "  진입 방법:"
  echo "    proot-distro login ubuntu   ← Ubuntu 컨테이너"
  echo "    cd ${target}"
  echo "    claude                       ← Claude Code 실행"
  echo ""
  echo "  상태 확인:"
  echo "    bash ${target}/phone-health.sh           ← 건강 검진"
  echo "    bash ${target}/phone-health.sh --telegram ← TG 보고"
  echo "    bash ${target}/tg.sh '테스트'             ← TG 메시지"
  echo ""
  echo "  통신망:"
  echo "    GitHub:  github.com/helena751107/helena_phone"
  echo "    Discord: discord.gg/JTYSZv2WQE"
  echo "    TG 봇:   @S21Phone_Bot"
  echo ""
  echo "  다음 할 일:"
  echo "    1. .secrets.env 에 토큰 입력"
  echo "    2. CONSTITUTION.md 전문 읽기"
  echo "    3. _notebook/99-devlog.md 로 컨텍스트 복원"
  echo ""
  echo -e "${YELLOW}  이 설치기는 proot Ubuntu 위에서 구동됩니다.${NC}"
  echo -e "${YELLOW}  트랙1(돌봄) 데몬은 Termux 네이티브로 분리 설치됩니다.${NC}"
  echo ""
}

# ── MAIN ───────────────────────────────────────────────────────────────────
main() {
  banner

  check_env
  install_termux_pkgs
  install_proot

  # 여기서부터는 proot 안에서 실행
  # 이미 proot 안이면 그냥 진행
  if [ -f /.dockerenv ] || grep -q Ubuntu /etc/os-release 2>/dev/null; then
    info "proot Ubuntu 내부 — 직접 실행"
    clone_repo
    setup_claude
    setup_mcp
    setup_telegram
    run_healthcheck
  else
    info "proot Ubuntu 진입 → 내부에서 계속..."
    proot-distro login ubuntu -- bash -c "
      export TERMUX_VERSION='${TERMUX_VERSION:-}'
      $(declare -f clone_repo setup_claude setup_mcp setup_telegram run_healthcheck ok warn fail info)
      clone_repo
      setup_claude
      setup_mcp
      setup_telegram
      run_healthcheck
    "
  fi

  print_constitution
  summary
}

# ── 실행 ───────────────────────────────────────────────────────────────────
TARGET="/root/work"
main "$@"
