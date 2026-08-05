#!/bin/bash
# 🖥️ pc-setup-wsl.sh — WSL2 Ubuntu 개발환경 자동 셋업
# 사용법: bash pc-setup-wsl.sh
# Boss 2026-08-05

set -e

echo "🖥️  WSL2 개발환경 셋업 시작..."
echo "========================================"

# 1. 기본 패키지
echo ""
echo "📦 [1/6] 기본 패키지 설치..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential git curl wget python3 python3-pip pipx openssh-server
pipx ensurepath

# 2. Tailscale
echo ""
echo "🔗 [2/6] Tailscale 설치..."
if ! command -v tailscale &>/dev/null; then
    curl -fsSL https://tailscale.com/install.sh | sh
    echo "👉 'sudo tailscale up' 실행 후 브라우저에서 로그인하세요."
else
    echo "✅ Tailscale 이미 설치됨"
fi

# 3. SSH 서버
echo ""
echo "🔑 [3/6] SSH 서버 설정..."
sudo systemctl enable ssh 2>/dev/null || echo "  (WSL — systemctl 불가, service로 대체)"
sudo service ssh start 2>/dev/null || echo "  SSH 서비스 수동 시작 필요"

# 4. DeepSeek API 키 확인
echo ""
echo "🤖 [4/6] API 키 확인..."
if [ -z "$DEEPSEEK_API_KEY" ] && [ -z "$OPENROUTER_API_KEY" ]; then
    echo "⚠️  DEEPSEEK_API_KEY 또는 OPENROUTER_API_KEY가 설정되지 않았습니다."
    echo "   ~/.bashrc에 추가:"
    echo "   export OPENROUTER_API_KEY='sk-or-v1-XXXX'"
    echo "   export DEEPSEEK_MODEL='deepseek/deepseek-chat'"
else
    echo "✅ API 키 설정됨"
fi

# 5. Aider + ds 래퍼
echo ""
echo "🛠️ [5/6] Aider 설치 + ds 래퍼..."
pipx install aider-chat || pip install aider-chat

mkdir -p ~/bin
cat > ~/bin/ds << 'DSEOF'
#!/bin/bash
# ds — Aider + DeepSeek 작업반장 래퍼
# 사용법: ds "작업 지시"
#         ds --apply "코드 수정 지시"
#         ds --repo ~/other-repo "지시"

REPO="${REPO:-$HOME/work/helena_phone}"
MODEL="${DEEPSEEK_MODEL:-deepseek/deepseek-chat}"

cd "$REPO" || { echo "❌ $REPO 없음. 먼저 git clone 하세요."; exit 1; }

echo "🔧 ds — Aider + DeepSeek (${MODEL})"
echo "📂 $REPO"
echo ""

aider \
  --model "openrouter/${MODEL}" \
  --no-auto-commits \
  --no-gitignore \
  "$@"
DSEOF
chmod +x ~/bin/ds
echo "✅ ds 래퍼 설치됨: ~/bin/ds"

# 6. Git 레포 클론
echo ""
echo "📥 [6/6] Git 레포 클론..."
mkdir -p ~/work
cd ~/work
if [ -d helena_phone ]; then
    echo "✅ helena_phone 이미 존재 — pull"
    cd helena_phone && git pull --recurse-submodules
else
    git clone --recurse-submodules https://github.com/helena751107/helena_phone.git
    echo "✅ helena_phone 클론 완료"
fi

echo ""
echo "========================================"
echo "🎉 셋업 완료!"
echo ""
echo "✨ 다음 수동 작업:"
echo "   1. tailscale up → 브라우저 로그인"
echo "   2. Phone에서: ssh-keygen + ssh-copy-id <user>@<pc-tailscale-ip>"
echo "   3. Tailscale 콘솔에서 양쪽 기기 'Disable expiry'"
echo "   4. Phone ~/.bashrc에 alias 등록"
echo ""
echo "🧪 테스트:"
echo "   ssh <user>@<pc-tailscale-ip> 'echo 연결OK'"
echo "   ds '이 레포 설명해줘'"
