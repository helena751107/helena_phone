#!/bin/bash
# ─── Helena TG-TTS Bridge ──────────────────────────────
# 텔레그램 메시지를 받아서 음성으로 읽어주는 브릿지
#
# 동작:
#   TG 봇이 메시지 수신 → tts-speak.py로 음성 변환 → 재생
#   사용 후 깔끔하게 종료 (램 상주 없음)
#
# 사용법:
#   bash tg-tts-bridge.sh start          # 브릿지 시작 (백그라운드)
#   bash tg-tts-bridge.sh stop           # 브릿지 중지
#   bash tg-tts-bridge.sh speak "텍스트"  # 직접 읽기
#   bash tg-tts-bridge.sh status         # 상태 확인
#
# 필요:
#   pip install edge-tts
#   apt install ffmpeg jq
# ───────────────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TTS_SCRIPT="$SCRIPT_DIR/tts-speak.py"
PID_FILE="/tmp/tg-tts-bridge.pid"
LAST_UPDATE="/tmp/tg-tts-last-update.txt"

# ── TG 설정 (.secrets.env에서) ──────────────────────
source /root/work/.secrets.env 2>/dev/null || true
TG_TOKEN="${HELENA_PIANO_TG_TOKEN}"
TG_CHAT="${HELENA_PIANO_TG_CHAT:-8579179811}"

TG_API="https://api.telegram.org/bot${TG_TOKEN}"

# ── 온디맨드 읽기 ──────────────────────────────────
do_speak() {
    local text="$1"
    if [ -z "$text" ]; then
        echo "❌ 읽을 텍스트 없음"
        return 1
    fi
    echo "🔊 읽는 중: ${text:0:60}..."
    python3 "$TTS_SCRIPT" "$text" --native 2>/dev/null || \
    python3 "$TTS_SCRIPT" "$text" 2>/dev/null
}

# ── TG 폴링 (필요할 때만) ──────────────────────────
do_poll_once() {
    # 마지막 업데이트 이후 새 메시지만 가져오기
    local offset=""
    [ -f "$LAST_UPDATE" ] && offset=$(( $(cat "$LAST_UPDATE") + 1 ))

    local updates
    updates=$(curl -s "${TG_API}/getUpdates?offset=${offset}&limit=1&timeout=5" 2>/dev/null)

    local update_id
    update_id=$(echo "$updates" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result'][0]['update_id']) if d.get('result') else None" 2>/dev/null)

    if [ -n "$update_id" ]; then
        echo "$update_id" > "$LAST_UPDATE"

        local msg
        msg=$(echo "$updates" | python3 -c "
import sys, json
d = json.load(sys.stdin)
r = d.get('result', [])
if r:
    m = r[0].get('message', {}).get('text', '')
    print(m[:500])
" 2>/dev/null)

        if [ -n "$msg" ] && [ "$msg" != "None" ]; then
            do_speak "$msg"
        fi
    fi
}

# ── 백그라운드 루프 ───────────────────────────────
do_start() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "⚠️ 이미 실행 중 (PID: $(cat "$PID_FILE"))"
        return 1
    fi

    echo "▶️ TG-TTS 브릿지 시작..."
    (
        echo $$ > "$PID_FILE"
        echo "0" > "$LAST_UPDATE"
        while true; do
            do_poll_once
            sleep 10  # 10초 간격 폴링 (CPU 거의 안 씀)
        done
    ) &
    echo "✅ 백그라운드 시작 (PID: $!)"
}

do_stop() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        kill "$pid" 2>/dev/null && echo "⏹️ 중지됨 (PID: $pid)"
        rm -f "$PID_FILE"
    else
        echo "⚠️ 실행 중인 브릿지 없음"
    fi
}

do_status() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "🟢 실행 중 (PID: $(cat "$PID_FILE"))"
        echo "   마지막 업데이트: $(cat "$LAST_UPDATE" 2>/dev/null || echo '없음')"
    else
        echo "🔴 중지됨"
    fi
}

# ── CLI ───────────────────────────────────────────
case "${1:-}" in
    start)   do_start ;;
    stop)    do_stop ;;
    status)  do_status ;;
    speak)   do_speak "${*:2}" ;;
    poll)    do_poll_once ;;
    *)
        echo "사용법:"
        echo "  bash tg-tts-bridge.sh start     # 브릿지 시작"
        echo "  bash tg-tts-bridge.sh stop      # 브릿지 중지"
        echo "  bash tg-tts-bridge.sh status    # 상태 확인"
        echo "  bash tg-tts-bridge.sh speak '...' # 직접 읽기"
        echo "  bash tg-tts-bridge.sh poll      # 1회 폴링"
        ;;
esac
