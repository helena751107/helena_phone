#!/usr/bin/env bash
# ds.sh — Aider + DeepSeek 안전 실행 래퍼
# Termux: alias ds 가 proot 안에서 이 스크립트를 실행
# 사용: bash ~/work/scripts/ds.sh [추가 aider 인자...]
#
# 환경변수:
#   AIDER_MODEL=deepseek/deepseek-v4-pro|deepseek/deepseek-v4-flash
#   DS_KEEP_HISTORY=1  → 오염 히스토리 자동 백업 안 함

set -euo pipefail

WORK="${WORK_DIR:-$HOME/work}"
[ -d "$WORK" ] || WORK="/root/work"
cd "$WORK"

# 키 로드
if [ -f "$WORK/.secrets.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$WORK/.secrets.env"
  set +a
fi
# bashrc에 DEEPSEEK_API_KEY 있는 경우
if [ -z "${DEEPSEEK_API_KEY:-}" ] && [ -f "$HOME/.bashrc" ]; then
  # shellcheck disable=SC1091
  eval "$(grep -E '^export DEEPSEEK_API_KEY=' "$HOME/.bashrc" 2>/dev/null || true)"
fi

export PATH="$HOME/.local/bin:${PATH:-}"
export AIDER_MODEL_SETTINGS_FILE="${AIDER_MODEL_SETTINGS_FILE:-$HOME/.aider.model.settings.yml}"

if [ -z "${DEEPSEEK_API_KEY:-}" ]; then
  echo "❌ DEEPSEEK_API_KEY 없음" >&2
  echo "   $WORK/.secrets.env 또는 ~/.bashrc 에 export DEEPSEEK_API_KEY=... 추가" >&2
  exit 1
fi

if ! command -v aider >/dev/null 2>&1; then
  echo "❌ aider 없음. 설치: uv tool install aider-chat  또는  pip install aider-chat" >&2
  exit 1
fi

MODEL="${AIDER_MODEL:-deepseek/deepseek-v4-pro}"

# 오염 히스토리 정리 (Claude 행세 / greeting 환각 세션)
HIST="$WORK/.aider.chat.history.md"
if [ -f "$HIST" ] && [ "${DS_KEEP_HISTORY:-0}" != "1" ]; then
  if grep -qE 'Anthropic의 Claude|Change the greeting|저는 Anthropic|Claude \(Sonnet\)' "$HIST" 2>/dev/null; then
    bak="$HIST.bad.$(date +%Y%m%d%H%M%S)"
    mv "$HIST" "$bak"
    echo "⚠️  오염된 Aider 히스토리 → $bak"
  fi
fi

echo "▶ ds = Aider + DeepSeek"
echo "  model: $MODEL"
echo "  cwd:   $WORK"
echo "  종료:  /exit 또는 Ctrl+C"
echo ""

exec aider \
  --model "$MODEL" \
  --model-settings-file "$AIDER_MODEL_SETTINGS_FILE" \
  --edit-format diff \
  --chat-language Korean \
  --no-auto-commits \
  --no-attribute-author \
  --no-attribute-committer \
  --no-restore-chat-history \
  --dark-mode \
  --pretty \
  --assistant-output-color "#FFD700" \
  --tool-error-color "#22CC66" \
  --tool-warning-color "#E6B800" \
  --user-input-color "#66FF66" \
  --code-theme gruvbox-dark \
  "$@"
