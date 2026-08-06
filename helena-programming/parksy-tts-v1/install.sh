#!/bin/bash
# ParkSyTTS v1 설치 스크립트 — Galaxy S21 proot-Ubuntu (ARM64)
# 실행: bash install.sh

set -e
ARCH=$(uname -m)
echo "======================================"
echo "  ParkSyTTS v1 설치 시작"
echo "  아키텍처: $ARCH"
echo "======================================"

echo ""
echo "[1/5] 시스템 패키지 설치..."
apt-get update -qq
apt-get install -y -qq \
    python3 python3-pip python3-venv \
    git git-lfs \
    ffmpeg \
    mecab libmecab-dev mecab-ipadic-utf8 \
    build-essential \
    libsndfile1 \
    wget curl

echo ""
echo "[2/5] GPT-SoVITS 설치..."
if [ ! -d "$HOME/GPT-SoVITS" ]; then
    git clone https://github.com/RVC-Boss/GPT-SoVITS "$HOME/GPT-SoVITS"
else
    echo "  → 이미 존재, 건너뜀"
fi

echo ""
echo "[3/5] Python 가상환경 생성..."
if [ ! -d "$HOME/GPT-SoVITS/.venv" ]; then
    python3 -m venv "$HOME/GPT-SoVITS/.venv"
fi
source "$HOME/GPT-SoVITS/.venv/bin/activate"
pip install --upgrade pip -q

echo ""
echo "[4/5] PyTorch CPU 설치... (5~15분 소요)"
if [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
    echo "  → ARM64: pip 기본 채널"
    pip install torch torchaudio -q
else
    echo "  → x86_64: CPU-only wheel"
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu -q
fi

echo ""
echo "[5/5] 추론 의존성 설치..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
pip install -r "$SCRIPT_DIR/requirements.txt" -q

echo ""
echo "======================================"
echo "  ✅ 설치 완료!"
echo ""
echo "  다음 단계:"
echo "  1. 오빠한테 모델 보내달라고 하기 (send_models.sh)"
echo "  2. source activate.sh"
echo "  3. python3 say.py '안녕 헬레나!'"
echo "======================================"
