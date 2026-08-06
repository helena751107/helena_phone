#!/bin/bash
# activate.sh — ParkSyTTS v1 환경 활성화
VENV="$HOME/GPT-SoVITS/.venv"

if [ ! -d "$VENV" ]; then
    echo "❌ 가상환경 없음. 먼저: bash install.sh"
    return 1 2>/dev/null || exit 1
fi

source "$VENV/bin/activate"
export PARKSY_MODEL_DIR="$HOME/parksy-tts-v1/models"
export GPT_SOVITS_DIR="$HOME/GPT-SoVITS"

echo "✅ ParkSyTTS v1 활성화"
echo "   사용법: python3 $(dirname "${BASH_SOURCE[0]}")/say.py '텍스트'"
