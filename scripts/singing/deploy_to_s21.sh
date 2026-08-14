#!/bin/bash
# deploy_to_s21.sh — 가창 AI 파이프라인을 S21 proot로 전송
# 실행: bash deploy_to_s21.sh

set -e

# helena-proot Tailscale IP
HELENA_IP="100.87.229.125"
HELENA_USER="user"
SSH_PORT="22"

# 또는 helena-android IP 사용
# HELENA_IP="100.97.231.3"

SCP="scp -P ${SSH_PORT} -o StrictHostKeyChecking=no"
SSH="ssh -p ${SSH_PORT} -o StrictHostKeyChecking=no ${HELENA_USER}@${HELENA_IP}"

echo "[1] S21 Tailscale 연결 확인"
if ! ping -c 1 -W 3 "$HELENA_IP" > /dev/null 2>&1; then
    echo "  ❌ $HELENA_IP 응답 없음. S21이 온라인인지 확인하세요."
    exit 1
fi
echo "  ✅ $HELENA_IP 응답"

echo "[2] 디렉토리 생성"
$SSH "mkdir -p ~/helena_phone/scripts/singing ~/rvc_models/helena_rvc"

echo "[3] 가창 파이프라인 전송"
DIR="$(dirname "$0")"
$SCP "${DIR}/s21_singing.py" "${HELENA_USER}@${HELENA_IP}:~/helena_phone/scripts/singing/"
$SCP "${DIR}/check_npu.sh"   "${HELENA_USER}@${HELENA_IP}:~/helena_phone/scripts/singing/"
echo "  ✅ 파이프라인 전송 완료"

echo "[4] helena RVC 모델 전송 (55MB + 112MB)"
RVC_DIR="${HOME}/rvc_models/helena_rvc"
if [ -f "${RVC_DIR}/helena_rvc.pth" ]; then
    $SCP "${RVC_DIR}/helena_rvc.pth"   "${HELENA_USER}@${HELENA_IP}:~/rvc_models/helena_rvc/"
    $SCP "${RVC_DIR}/helena_rvc.index" "${HELENA_USER}@${HELENA_IP}:~/rvc_models/helena_rvc/"
    echo "  ✅ helena RVC 모델 전송 완료"
else
    echo "  ⚠️  helena RVC 모델 없음: ${RVC_DIR}"
fi

echo "[5] S21에서 NPU 진단 실행"
$SSH "bash ~/helena_phone/scripts/singing/check_npu.sh" || true

echo ""
echo "========================================"
echo " 전송 완료! S21에서 실행 방법:"
echo ""
echo " # 테스트 (주기도문 일부)"
echo " python3 ~/helena_phone/scripts/singing/s21_singing.py \\"
echo "   --lyrics '하늘에 계신 우리 아버지' \\"
echo "   --notes 'C4,D4,E4,F4,G4,A4,G4,C5' \\"
echo "   --durs '0.5,0.5,0.5,0.5,0.5,0.5,0.5,1.0' \\"
echo "   --steps 10 --rvc"
echo ""
echo " # .ustx 파일로 실행"
echo " python3 ~/helena_phone/scripts/singing/s21_singing.py \\"
echo "   --ustx ~/amazing_grace_parksy.ustx"
echo "========================================"
