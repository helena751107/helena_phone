#!/bin/bash
# send_models.sh — 박씨 WSL에서 실행: 모델을 헬레나 S21로 전송
#
# 사용법:
#   bash send_models.sh 192.168.1.xxx      (헬레나 폰 IP)
#   bash send_models.sh 192.168.1.xxx 8022 (포트 지정)

PHONE_IP="${1:?사용법: bash send_models.sh <헬레나폰IP> [포트]}"
PHONE_PORT="${2:-8022}"

MODEL_SRC="$HOME/parksy-audio/voice_models/matched_v2"
MODEL_DST="~/parksy-tts-v1/models"

echo "======================================"
echo "  ParkSyTTS v1 모델 전송"
echo "  대상: ${PHONE_IP}:${PHONE_PORT}"
echo "======================================"

ssh -p "$PHONE_PORT" "${PHONE_IP}" \
    "mkdir -p ~/parksy-tts-v1/models/gpt ~/parksy-tts-v1/models/sovits ~/parksy-tts-v1/models/ref"

echo ""
echo "[1/3] GPT 모델 (149MB)..."
scp -P "$PHONE_PORT" \
    "$MODEL_SRC/gpt/parksy_v2-e15.ckpt" \
    "${PHONE_IP}:${MODEL_DST}/gpt/"

echo ""
echo "[2/3] SoVITS 모델 (165MB)..."
scp -P "$PHONE_PORT" \
    "$MODEL_SRC/sovits/parksy_v2_e8_s256.pth" \
    "${PHONE_IP}:${MODEL_DST}/sovits/"

echo ""
echo "[3/3] 레퍼런스 오디오..."
scp -P "$PHONE_PORT" \
    "$MODEL_SRC/ref/seg004.wav" \
    "${PHONE_IP}:${MODEL_DST}/ref/"

echo ""
echo "======================================"
echo "  ✅ 전송 완료! 헬레나 폰에서:"
echo "  source activate.sh"
echo "  python3 say.py '안녕!'"
echo "======================================"
