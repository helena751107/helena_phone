#!/usr/bin/env bash
# ==============================================================================
# care-daemon.sh — 트랙 1 돌봄 데몬 (Termux 네이티브, proot 위에서 실행 금지)
# ==============================================================================
# 실행: crontab */15 * * * * bash ~/care/care-daemon.sh
# 의존성: termux-api, curl
# AI 의존성: 제로 — Claude Code 세션과 완전히 독립적
# ==============================================================================

set -euo pipefail

# ── 경로 ───────────────────────────────────────────────────────────────────
CARE_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_FILE="${CARE_DIR}/care-state.json"
LOG_FILE="${CARE_DIR}/care.log"
CONF_FILE="${CARE_DIR}/care.conf"
NOW=$(date '+%Y-%m-%d %H:%M:%S')
NOW_EPOCH=$(date +%s)

# Termux PATH
export PATH="/data/data/com.termux/files/usr/bin:$PATH"

# ── 설정 로드 ──────────────────────────────────────────────────────────────
if [ -f "$CONF_FILE" ]; then
  source "$CONF_FILE"
fi

TG_TOKEN="${TG_TOKEN:-}"
TG_CHAT_HELENA="${TG_CHAT_HELENA:-}"
TG_CHAT_PASTOR="${TG_CHAT_PASTOR:-}"

# 임계값 (conf에서 override 가능)
BATTERY_LOW="${BATTERY_LOW:-15}"
BATTERY_DROP_PCT="${BATTERY_DROP_PCT:-30}"
BATTERY_DROP_MIN="${BATTERY_DROP_MIN:-60}"
TEMP_HIGH="${TEMP_HIGH:-45}"
GPS_SILENT_HOURS="${GPS_SILENT_HOURS:-2}"
NO_MOVE_HOURS="${NO_MOVE_HOURS:-6}"
LOCATION_RADIUS_M="${LOCATION_RADIUS_M:-500}"

# ── 유틸리티 ────────────────────────────────────────────────────────────────
log() { echo "[$NOW] $*" >> "$LOG_FILE"; }

save_state() {
  python3 -c "
import json, sys, os
state = {}
if os.path.exists('$STATE_FILE'):
    try: state = json.load(open('$STATE_FILE'))
    except: pass
state.update(json.load(sys.stdin))
json.dump(state, open('$STATE_FILE','w'), indent=2)
"
}

load_state() {
  [ -f "$STATE_FILE" ] && python3 -c "
import json
state = json.load(open('$STATE_FILE'))
for k,v in state.items():
    print(f'{k}={v}')
" || true
}

send_alert() {
  local level="$1" msg="$2" target="${3:-$TG_CHAT_HELENA}"

  if [ -z "${TG_TOKEN:-}" ] || [ -z "${target:-}" ]; then
    log "WARN: TG_TOKEN 또는 chat_id 미설정 → 알림 전송 스킵"
    return 1
  fi

  local icon
  case "$level" in
    urgent) icon="🔴" ;;
    warning) icon="🟡" ;;
    info) icon="🟢" ;;
    *) icon="📢" ;;
  esac

  local text="${icon} [${level^^}] ${NOW}
${msg}"

  curl -s -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" \
    -d "chat_id=${target}" \
    -d "text=${text}" \
    -d "disable_notification=${DISABLE_NOTIFY:-false}" >/dev/null 2>&1 || {
    log "ERROR: 텔레그램 전송 실패"
    return 1
  }

  log "ALERT → ${target}: ${msg}"
}

# ── 수집 ────────────────────────────────────────────────────────────────────

collect_battery() {
  local batt_json
  batt_json=$(termux-battery-status 2>/dev/null || echo '{}')

  local pct; pct=$(echo "$batt_json" | grep -o '"percentage":[0-9]*' | grep -o '[0-9]*' || echo "0")
  local temp; temp=$(echo "$batt_json" | grep -o '"temperature":[0-9.]*' | grep -o '[0-9.]*' || echo "0")
  local status; status=$(echo "$batt_json" | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo "UNKNOWN")
  local health; health=$(echo "$batt_json" | grep -o '"health":"[^"]*"' | cut -d'"' -f4 || echo "UNKNOWN")
  local plugged; plugged=$(echo "$batt_json" | grep -o '"plugged":"[^"]*"' | cut -d'"' -f4 || echo "UNKNOWN")

  echo "BATTERY_PCT=$pct"
  echo "BATTERY_TEMP=$temp"
  echo "BATTERY_STATUS=$status"
  echo "BATTERY_HEALTH=$health"
  echo "BATTERY_PLUGGED=$plugged"
}

collect_location() {
  local loc_json
  loc_json=$(termux-location -p gps -r last 2>/dev/null || termux-location -p network -r last 2>/dev/null || echo '{}')

  local lat; lat=$(echo "$loc_json" | grep -o '"latitude":[0-9.]*' | grep -o '[0-9.]*' || echo "")
  local lon; lon=$(echo "$loc_json" | grep -o '"longitude":[0-9.]*' | grep -o '[0-9.]*' || echo "")
  local provider; provider=$(echo "$loc_json" | grep -o '"provider":"[^"]*"' | cut -d'"' -f4 || echo "none")

  echo "LOC_LAT=$lat"
  echo "LOC_LON=$lon"
  echo "LOC_PROVIDER=$provider"
}

collect_connectivity() {
  local wifi_json
  wifi_json=$(termux-wifi-scaninfo 2>/dev/null || termux-wifi-connectioninfo 2>/dev/null || echo '{}')

  local ssid; ssid=$(echo "$wifi_json" | grep -o '"ssid":"[^"]*"' | cut -d'"' -f4 || echo "UNKNOWN")
  local rssi; rssi=$(echo "$wifi_json" | grep -o '"rssi":-\?[0-9]*' | grep -o -- '-\?[0-9]*' | head -1 || echo "0")
  local ip; ip=$(echo "$wifi_json" | grep -o '"ip":"[^"]*"' | cut -d'"' -f4 || echo "0.0.0.0")

  echo "WIFI_SSID=$ssid"
  echo "WIFI_RSSI=$rssi"
  echo "WIFI_IP=$ip"
}

collect_telephony() {
  local tel_json
  tel_json=$(termux-telephony-deviceinfo 2>/dev/null || echo '{}')

  local net_type; net_type=$(echo "$tel_json" | grep -o '"network_type":"[^"]*"' | cut -d'"' -f4 || echo "UNKNOWN")
  local signal_str; signal_str=$(echo "$tel_json" | grep -o '"signal_strength":[0-9]*' | grep -o '[0-9]*' || echo "0")

  echo "CELL_NET=$net_type"
  echo "CELL_SIGNAL=$signal_str"
}

# ── 분석 ────────────────────────────────────────────────────────────────────

analyze() {
  local batt_pct="$1" batt_temp="$2" batt_status="$3" batt_plugged="$4"
  local loc_lat="$5" loc_lon="$6" loc_provider="$7"
  local wifi_ssid="$8" wifi_rssi="$9" cell_signal="${10}"

  local alerts=""
  local level="info"

  # ── 배터리 검사 ──
  if [ "$batt_pct" -lt "$BATTERY_LOW" ] && [ "$batt_plugged" != "PLUGGED_AC" ]; then
    level="urgent"
    alerts="${alerts}
⚠️ 배터리 ${batt_pct}% (방전 위험)"
  fi

  if [ "${batt_temp%.*}" -gt "$TEMP_HIGH" ] 2>/dev/null; then
    [ "$level" = "info" ] && level="warning"
    alerts="${alerts}
🔥 온도 ${batt_temp}°C (과열)"
  fi

  # 이전 대비 급감 감지
  local prev_batt
  prev_batt=$(echo "$PREV_STATE" | grep "BATTERY_PCT=" | cut -d= -f2 || echo "100")
  if [ -n "$prev_batt" ] && [ "$prev_batt" != "0" ]; then
    local drop=$((prev_batt - batt_pct))
    if [ "$drop" -gt "$BATTERY_DROP_PCT" ]; then
      level="urgent"
      alerts="${alerts}
📉 배터리 급감: ${prev_batt}% → ${batt_pct}% (${drop}% 하락)"
    fi
  fi

  # ── GPS 검사 ──
  if [ -z "$loc_lat" ] || [ "$loc_provider" = "none" ]; then
    local prev_gps_time
    prev_gps_time=$(echo "$PREV_STATE" | grep "LAST_GPS_TIME=" | cut -d= -f2 || echo "$NOW_EPOCH")
    local gps_gap=$(( (NOW_EPOCH - prev_gps_time) / 3600 ))
    if [ "$gps_gap" -gt "$GPS_SILENT_HOURS" ]; then
      [ "$level" = "info" ] && level="warning"
      alerts="${alerts}
📍 GPS ${gps_gap}시간째 무응답"
    fi
  fi

  # ── 활동 패턴 ──
  local prev_loc
  prev_loc=$(echo "$PREV_STATE" | grep "LOC_LAT=" | cut -d= -f2 || echo "")
  if [ -n "$prev_loc" ] && [ -n "$loc_lat" ] && [ "$prev_loc" = "$loc_lat" ]; then
    local prev_move_time
    prev_move_time=$(echo "$PREV_STATE" | grep "LAST_MOVE_TIME=" | cut -d= -f2 || echo "$NOW_EPOCH")
    local still_hours=$(( (NOW_EPOCH - prev_move_time) / 3600 ))
    if [ "$still_hours" -gt "$NO_MOVE_HOURS" ]; then
      level="urgent"
      alerts="${alerts}
🛑 ${still_hours}시간째 위치 변동 없음 (웰니스 체크 필요)"
    fi
  fi

  # ── 연결성 ──
  if [ "${wifi_rssi#-}" -gt 80 ] 2>/dev/null; then
    [ "$level" = "info" ] && level="warning"
    alerts="${alerts}
📶 WiFi 약함 (RSSI ${wifi_rssi}dBm)"
  fi

  echo "ALERT_LEVEL=$level"
  echo "ALERTS=$alerts"
}

# ── 메인 ────────────────────────────────────────────────────────────────────

main() {
  log "─── 데몬 체크 시작 ───"

  # 이전 상태 로드
  PREV_STATE=$(load_state)

  # 수집
  eval "$(collect_battery)"
  eval "$(collect_location)"
  eval "$(collect_connectivity)"
  eval "$(collect_telephony)"

  # 분석
  eval "$(analyze "$BATTERY_PCT" "$BATTERY_TEMP" "$BATTERY_STATUS" "$BATTERY_PLUGGED" \
    "$LOC_LAT" "$LOC_LON" "$LOC_PROVIDER" \
    "$WIFI_SSID" "$WIFI_RSSI" "$CELL_SIGNAL")"

  # 상태 저장
  echo "{
    \"timestamp\": \"$NOW\",
    \"epoch\": $NOW_EPOCH,
    \"battery_pct\": $BATTERY_PCT,
    \"battery_temp\": $BATTERY_TEMP,
    \"battery_status\": \"$BATTERY_STATUS\",
    \"battery_plugged\": \"$BATTERY_PLUGGED\",
    \"loc_lat\": \"$LOC_LAT\",
    \"loc_lon\": \"$LOC_LON\",
    \"loc_provider\": \"$LOC_PROVIDER\",
    \"wifi_ssid\": \"$WIFI_SSID\",
    \"wifi_rssi\": $WIFI_RSSI,
    \"cell_signal\": $CELL_SIGNAL,
    \"alert_level\": \"$ALERT_LEVEL\",
    \"last_gps_time\": $([ -n "$LOC_LAT" ] && echo "$NOW_EPOCH" || echo "$(echo "$PREV_STATE" | grep "LAST_GPS_TIME=" | cut -d= -f2 || echo "$NOW_EPOCH")"),
    \"last_move_time\": $([ "$LOC_LAT" != "$(echo "$PREV_STATE" | grep "LOC_LAT=" | cut -d= -f2 || echo '')" ] && echo "$NOW_EPOCH" || echo "$(echo "$PREV_STATE" | grep "LAST_MOVE_TIME=" | cut -d= -f2 || echo "$NOW_EPOCH")")
  }" | save_state

  # ── 보고 ──
  if [ "$ALERT_LEVEL" = "urgent" ] || [ "$ALERT_LEVEL" = "warning" ]; then
    # 이상 보고 — 즉시 발송
    local report="${alerts}
📍 위치: ${LOC_LAT}, ${LOC_LON} (${LOC_PROVIDER})
🔋 배터리: ${BATTERY_PCT}% / ${BATTERY_TEMP}°C / ${BATTERY_STATUS}
📶 WiFi: ${WIFI_SSID} (${WIFI_RSSI}dBm) | 셀룰러: ${CELL_SIGNAL}"

    send_alert "$ALERT_LEVEL" "$report" "$TG_CHAT_HELENA"

    # 긴급 시 목사님에게도
    if [ "$ALERT_LEVEL" = "urgent" ] && [ -n "${TG_CHAT_PASTOR:-}" ]; then
      send_alert "urgent" "[에스컬레이션] $report" "$TG_CHAT_PASTOR"
    fi
  fi

  # ── Tailscale 상태 ──
  local ts_ip=""; ts_status="offline"
  if command -v tailscale >/dev/null 2>&1; then
    ts_ip=$(tailscale ip -4 2>/dev/null || echo "")
    [ -n "$ts_ip" ] && ts_status="online"
  fi

  # 정기 보고 (매 시간 정각 ±5분)
  local min
  min=$(date +%M | sed 's/^0//')
  if [ "$min" -le 5 ]; then
    local report="🟢 [정기] $(date +%H:%M)
🔋 ${BATTERY_PCT}% / ${BATTERY_TEMP}°C / ${BATTERY_STATUS}
📍 ${LOC_LAT}, ${LOC_LON} (${LOC_PROVIDER})
📶 ${WIFI_SSID} (${WIFI_RSSI}dBm)
🔗 Tailscale: ${ts_status} ${ts_ip}
상태: 정상"
    send_alert "info" "$report" "$TG_CHAT_HELENA"
  fi

  log "체크 완료: battery=${BATTERY_PCT}%, level=${ALERT_LEVEL}"
}

main "$@"
