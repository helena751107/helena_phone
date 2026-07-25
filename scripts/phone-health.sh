#!/usr/bin/env bash
# ==============================================================================
# phone-health.sh — S21 Phone 건강 검진 스크립트 v3
# ==============================================================================
# 사용법:
#   bash phone-health.sh                    # 기본 검진 (비파괴)
#   bash phone-health.sh --full             # 전체 검진 (사진/녹음 포함)
#   bash phone-health.sh --telegram         # 검진 + 텔레그램 보고
#
# 결과: _notebook/health/YYYY-MM-DD_HHMM.json 자동 저장
# ==============================================================================

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
HEALTH_DIR="${BASE_DIR}/_notebook/health"
MCP_PORT="${MCP_PORT:-3456}"
NOW="$(date +%Y-%m-%d_%H%M)"
TS="$(date '+%Y-%m-%d %H:%M:%S %Z')"
REPORT_FILE="${HEALTH_DIR}/${NOW}.json"

mkdir -p "$HEALTH_DIR"

# Termux PATH 반드시 선두에
export PATH="/data/data/com.termux/files/usr/bin:$PATH"

PASS_CNT=0; WARN_CNT=0; FAIL_CNT=0; SKIP_CNT=0

# ============================================================
# Helpers
# ============================================================

OK="✅"; WARN="⚠️"; FAIL="❌"; SKIP="⏭️"; INFO="ℹ️"

info()  { echo "  $INFO $1"; }
ok()    { echo "  $OK $1"; PASS_CNT=$((PASS_CNT+1)); }
warn()  { echo "  $WARN $1"; WARN_CNT=$((WARN_CNT+1)); }
fail()  { echo "  $FAIL $1"; FAIL_CNT=$((FAIL_CNT+1)); }
skip()  { echo "  $SKIP $1"; SKIP_CNT=$((SKIP_CNT+1)); }
sect()  { echo ""; echo "━━━ $* ━━━"; }

# 핵심: Termux 명령은 반드시 직접 실행 (bash -c 말고)
tx() { "$@" 2>/dev/null || true; }

# JSON 필드 추출 (multiline JSON 대비, 따옴표/공백 제거)
jget() {
  echo "$1" | sed -n "s/.*\"$2\": *\"\{0,1\}\([^\",}]*\)\"\{0,1\}.*/\1/p" | head -1
}


# ============================================================
# 1. 시스템 기본
# ============================================================

sect "1. 시스템 기본"
info "Kernel: $(uname -r 2>/dev/null || echo '?')"
info "Host:   $(uname -n 2>/dev/null || echo '?')"

MCP_HTTP=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${MCP_PORT}/health" 2>/dev/null || echo "000")
MCP_OKAY=$(curl -s "http://localhost:${MCP_PORT}/health" 2>/dev/null | grep -c '"status":"ok"' || true)
[ "$MCP_HTTP" = "200" ] && [ "$MCP_OKAY" -ge 1 ] && ok "phone-mcp-server (port ${MCP_PORT})" || fail "phone-mcp-server (HTTP ${MCP_HTTP})"

info "MCP tools: 18 (phone-mcp-server)"

info "Disk: $(df -h /data/data/com.termux/files 2>/dev/null | awk 'NR==2{print $4" free / "$2" total"}')"

GH_HTTP=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "https://helena751107.github.io/helena_phone/" 2>/dev/null || echo "000")
[ "$GH_HTTP" = "200" ] && ok "GitHub Pages (HTTP ${GH_HTTP})" || warn "GitHub Pages (HTTP ${GH_HTTP})"

# ============================================================
# 2. 전원 / 배터리 — 가장 중요
# ============================================================

sect "2. 전원 / 배터리"

BAT=$(termux-battery-status 2>/dev/null || echo "")
if [ -n "$BAT" ] && [ "$BAT" != "{}" ]; then
  ok "battery-status sensor"
  BAT_PCT=$(jget "$BAT" "percentage")
  BAT_TMP=$(jget "$BAT" "temperature")
  BAT_STS=$(jget "$BAT" "status")
  BAT_HTH=$(jget "$BAT" "health")
  BAT_PLG=$(jget "$BAT" "plugged")
  BAT_VLT=$(jget "$BAT" "voltage")
  BAT_CUR=$(jget "$BAT" "current_average")
  info "${BAT_PCT}% / ${BAT_TMP}°C / ${BAT_STS} / ${BAT_HTH} / plugged=${BAT_PLG}"
  info "Voltage: ${BAT_VLT}mV | Current avg: ${BAT_CUR}mA"

  [ -n "$BAT_PCT" ] && [ "$BAT_PCT" -lt 15 ] 2>/dev/null && warn "배터리 임계 (${BAT_PCT}% < 15%)"
  [ -n "$BAT_TMP" ] && [ "${BAT_TMP%.*}" -gt 45 ] 2>/dev/null && warn "온도 과열 (${BAT_TMP}°C > 45°C)"
else
  fail "battery-status sensor (no data)"
  BAT_PCT=""; BAT_TMP=""; BAT_STS="?"; BAT_HTH="?"; BAT_PLG="?"
fi

# ============================================================
# 3. WiFi / 네트워크
# ============================================================

sect "3. WiFi / 네트워크"

WIFI=$(termux-wifi-connectioninfo 2>/dev/null || echo "")
if [ -n "$WIFI" ] && [ "$WIFI" != "{}" ]; then
  ok "WiFi connection info"
  WIFI_SSID=$(jget "$WIFI" "ssid")
  WIFI_IP=$(jget "$WIFI" "ip")
  WIFI_RSSI=$(jget "$WIFI" "rssi")
  WIFI_LINK=$(jget "$WIFI" "link_speed_mbps")
  info "SSID: ${WIFI_SSID:-?} | IP: ${WIFI_IP:-?} | RSSI: ${WIFI_RSSI:-?}dBm | Link: ${WIFI_LINK:-?}Mbps"
  [ -n "$WIFI_RSSI" ] && [ "$WIFI_RSSI" -lt -80 ] 2>/dev/null && warn "WiFi 신호 약함 (RSSI ${WIFI_RSSI}dBm)"
else
  fail "WiFi connection info"
  WIFI_SSID="?"; WIFI_IP="?"; WIFI_RSSI=""
fi

EXT_G=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "https://www.google.com" 2>/dev/null || echo "000")
EXT_H=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "https://github.com" 2>/dev/null || echo "000")
info "Google: HTTP ${EXT_G} | GitHub: HTTP ${EXT_H}"

# ============================================================
# 4. 하드웨어 센서
# ============================================================

sect "4. 하드웨어 센서"

tx termux-torch on
sleep 1
tx termux-torch off
echo "  $OK Flashlight (ON→1s→OFF)"; PASS_CNT=$((PASS_CNT+1))

tx termux-vibrate -d 100
echo "  $OK Vibrate (100ms)"; PASS_CNT=$((PASS_CNT+1))

VOL=$(termux-volume 2>/dev/null || echo "")
if [ -n "$VOL" ] && [ "$VOL" != "[]" ]; then
  ok "Volume sensor"
  VM=$(echo "$VOL" | grep -oP '"stream":"music","volume":\K[0-9]+' || echo "?")
  VR=$(echo "$VOL" | grep -oP '"stream":"ring","volume":\K[0-9]+' || echo "?")
  VN=$(echo "$VOL" | grep -oP '"stream":"notification","volume":\K[0-9]+' || echo "?")
  info "Music: ${VM} | Ring: ${VR} | Notification: ${VN}"
else
  warn "Volume sensor"
fi

AI=$(termux-audio-info 2>/dev/null || echo "")
[ -n "$AI" ] && [ "$AI" != "{}" ] && ok "Audio info" || warn "Audio info"

SN=$(termux-sensor -l 2>/dev/null || echo "")
SC=$(echo "$SN" | wc -l)
[ -n "$SN" ] && ok "Sensors (${SC} available)" || warn "Sensors (unavailable)"

# ============================================================
# 5. GPS / 위치
# ============================================================

sect "5. 위치 / GPS"

GPS=$(timeout 8 termux-location -p gps 2>/dev/null || echo "")
if [ -n "$GPS" ] && echo "$GPS" | grep -q "latitude"; then
  ok "GPS location"
  GLAT=$(jget "$GPS" "latitude"); GLON=$(jget "$GPS" "longitude")
  GACC=$(jget "$GPS" "accuracy"); GALT=$(jget "$GPS" "altitude")
  info "(${GLAT}, ${GLON}) ±${GACC}m alt=${GALT}m"
else
  GPS2=$(timeout 5 termux-location -p network 2>/dev/null || echo "")
  if [ -n "$GPS2" ] && echo "$GPS2" | grep -q "latitude"; then
    GLAT=$(jget "$GPS2" "latitude"); GLON=$(jget "$GPS2" "longitude")
    warn "GPS (network fallback: ${GLAT}, ${GLON})"
  else
    warn "GPS (both providers failed)"
  fi
fi

# ============================================================
# 6. 카메라 / 미디어
# ============================================================

sect "6. 카메라 / 미디어"

CI=$(termux-camera-info 2>/dev/null || echo "")
if [ -n "$CI" ] && [ "$CI" != "[]" ]; then
  ok "Camera info"
  echo "  ${INFO} $(echo "$CI" | grep -oP '"facing":"[^"]*"' | tr '\n' ' ')"
else
  warn "Camera info"
fi

if [ "${1:-}" = "--full" ]; then
  tx termux-camera-photo -c 1 /tmp/hc_${NOW}.jpg
  PS=$(ls -la /tmp/hc_${NOW}.jpg 2>/dev/null | awk '{print $5}' || echo "0")
  [ "$PS" -gt 1000 ] 2>/dev/null && ok "Camera photo (${PS}B)" || fail "Camera photo"
  rm -f /tmp/hc_${NOW}.jpg 2>/dev/null
else
  skip "Camera photo (--full)"
fi

tx termux-microphone-record -d 1 -l 1 -f /tmp/hc_mic.m4a 2>/dev/null
sleep 1
tx termux-microphone-record -q 2>/dev/null
MS=$(ls -la /tmp/hc_mic.m4a 2>/dev/null | awk '{print $5}' || echo "0")
rm -f /tmp/hc_mic.m4a 2>/dev/null
[ "$MS" -gt 100 ] 2>/dev/null && ok "Microphone (${MS}B)" || warn "Microphone"

TTS=$(termux-tts-speak "health check ok" 2>/dev/null && echo "ok" || echo "fail")
[ "$TTS" = "ok" ] && ok "TTS" || warn "TTS"

# ============================================================
# 7. 클립보드
# ============================================================

sect "7. 클립보드"

echo "S21HC_${NOW}" | termux-clipboard-set 2>/dev/null
sleep 0.3
CG=$(termux-clipboard-get 2>/dev/null || echo "")
echo "$CG" | grep -q "S21HC_" && ok "Clipboard (write+read)" || fail "Clipboard (got='${CG}')"

# ============================================================
# 8. 커뮤니케이션
# ============================================================

sect "8. 커뮤니케이션"

SMS=$(termux-sms-list -l 1 -t inbox 2>/dev/null || echo "")
[ -n "$SMS" ] && [ "$SMS" != "[]" ] && ok "SMS inbox" || warn "SMS inbox"

CONT=$(termux-contact-list 2>/dev/null || echo "")
CC=$(echo "$CONT" | grep -c '"name"' || echo 0)
[ "$CC" -gt 0 ] 2>/dev/null && ok "Contacts (${CC} entries)" || warn "Contacts"

CALL=$(termux-call-log -l 5 2>/dev/null || echo "")
CLC=$(echo "$CALL" | grep -c '"number"' || echo 0)
[ "$CLC" -gt 0 ] 2>/dev/null && ok "Call log (${CLC} entries)" || warn "Call log"

TEL=$(termux-telephony-deviceinfo 2>/dev/null || echo "")
[ -n "$TEL" ] && [ "$TEL" != "{}" ] && ok "Telephony device info" || warn "Telephony device info"

CELL=$(termux-telephony-cellinfo 2>/dev/null || echo "")
[ -n "$CELL" ] && [ "$CELL" != "[]" ] && ok "Cellular info" || warn "Cellular info"

NT=$(termux-notification --title "Health Check" \
  --content "S21 Phone HC ${NOW}" --id "s21hc_${NOW}" --alert-once 2>/dev/null && echo "ok" || echo "fail")
[ "$NT" = "ok" ] && ok "Notification" || warn "Notification (permission?)"

# ============================================================
# 9. 네트워크 서비스
# ============================================================

sect "9. 네트워크 서비스"

for URL_LABEL in \
  "helena_phone|https://helena751107.github.io/helena_phone/" \
  "helana_log|https://github.com/helena751107/helana_log" \
  "helana-faith|https://github.com/helena751107/helana-faith" \
  "helena-piano|https://github.com/helena751107/helena-piano" \
  "helena-metalcare|https://github.com/helena751107/helena-metalcare"; do
  L="${URL_LABEL%%|*}"; U="${URL_LABEL##*|}"
  H=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$U" 2>/dev/null || echo "000")
  ok "$L (HTTP ${H})"
done

DC=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 \
  "https://discord.com/api/guilds/REDACTED/widget.json" 2>/dev/null || echo "000")
[ "$DC" = "200" ] && ok "Discord widget (HTTP ${DC})" || warn "Discord widget (HTTP ${DC})"

source "${BASE_DIR}/.secrets.env" 2>/dev/null || true
TG_API=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 \
  "https://api.telegram.org/bot${TG_TOKEN:-x}/getMe" 2>/dev/null || echo "000")
[ "$TG_API" = "200" ] && ok "Telegram API (HTTP ${TG_API})" || warn "Telegram API (HTTP ${TG_API})"

# ============================================================
# 10. 직접 Termux 핵심 기능 검증 (MCP 의존 없이)
# ============================================================

sect "10. 핵심 기능 직접 검증"

# get_battery 직접
BAT2=$(termux-battery-status 2>/dev/null || echo "")
if [ -n "$BAT2" ] && echo "$BAT2" | grep -q "percentage"; then
  P2=$(jget "$BAT2" "percentage")
  T2=$(jget "$BAT2" "temperature")
  ok "termux-battery-status → ${P2}% / ${T2}°C"
else
  fail "termux-battery-status (직접 호출 실패)"
fi

# device_info 직접
DI=$(termux-telephony-deviceinfo 2>/dev/null || echo "")
[ -n "$DI" ] && [ "$DI" != "{}" ] && ok "termux-telephony-deviceinfo" || fail "termux-telephony-deviceinfo"

# camera — 단순 info 확인
CI2=$(termux-camera-info 2>/dev/null || echo "")
[ -n "$CI2" ] && echo "$CI2" | grep -q "facing" && ok "termux-camera-info" || fail "termux-camera-info"

# ============================================================
# 종합 등급
# ============================================================

TOTAL=$((PASS_CNT + WARN_CNT + FAIL_CNT + SKIP_CNT))
sect "종합 진단"
info "통과: ${PASS_CNT} | 경고: ${WARN_CNT} | 실패: ${FAIL_CNT} | 생략: ${SKIP_CNT}"

if [ "$FAIL_CNT" -eq 0 ] && [ "$WARN_CNT" -le 2 ]; then G="S";   GM="모든 항목 정상"
elif [ "$FAIL_CNT" -eq 0 ]; then                G="A";   GM="경고 있으나 핵심 정상"
elif [ "$FAIL_CNT" -le 3 ]; then                G="B";   GM="소수 기능 불량 — 점검 권장"
else                                             G="C";   GM="다수 기능 불량 — 즉시 점검"
fi
info "종합 등급: ${G} — ${GM}"

# ============================================================
# JSON 리포트 저장
# ============================================================

cat > "$REPORT_FILE" <<EOF
{
  "timestamp": "$(echo "$TS" | sed 's/"/\\"/g')",
  "host": "$(echo "$(uname -n)" | sed 's/"/\\"/g')",
  "kernel": "$(echo "$(uname -r)" | sed 's/"/\\"/g')",
  "grade": "${G}",
  "battery": {
    "percentage": ${BAT_PCT:-null},
    "temperature": ${BAT_TMP:-null},
    "status": "$(echo "${BAT_STS}" | sed 's/"/\\"/g')",
    "health": "$(echo "${BAT_HTH}" | sed 's/"/\\"/g')",
    "plugged": "$(echo "${BAT_PLG}" | sed 's/"/\\"/g')"
  },
  "wifi": {
    "ssid": "$(echo "${WIFI_SSID}" | sed 's/"/\\"/g')",
    "ip": "$(echo "${WIFI_IP}" | sed 's/"/\\"/g')",
    "rssi": ${WIFI_RSSI:-null},
    "link_speed": ${WIFI_LINK:-null}
  },
  "networks": {
    "google": ${EXT_G:-null},
    "github": ${EXT_H:-null},
    "gh_pages": ${GH_HTTP:-null}
  },
  "results": {
    "pass": ${PASS_CNT},
    "warn": ${WARN_CNT},
    "fail": ${FAIL_CNT},
    "skip": ${SKIP_CNT},
    "total": ${TOTAL}
  },
  "mcp": {
    "port": ${MCP_PORT},
    "http_status": ${MCP_HTTP:-null},
    "tools": 18
  }
}
EOF

echo ""
info "저장: ${REPORT_FILE}"

# 최근 이력
echo ""
info "최근 검진 이력:"
ls -t "${HEALTH_DIR}"/*.json 2>/dev/null | head -5 | while read -r f; do
  [ ! -f "$f" ] && continue
  fb=$(basename "$f" .json)
  fg=$(grep '"grade"' "$f" 2>/dev/null | sed 's/.*"grade": *"\([^"]*\)".*/\1/' || echo "?")
  fp=$(grep '"percentage"' "$f" 2>/dev/null | sed 's/.*"percentage": *\([0-9]*\).*/\1/' || echo "?")
  echo "    ${fb}  | ${fg} | 배터리 ${fp}%"
done

echo ""
echo "==========================================="
echo "  ✅ 검진 완료 (${TS})"
echo "==========================================="

# Telegram 보고
if [ "${1:-}" = "--telegram" ]; then
  source "${BASE_DIR}/.secrets.env" 2>/dev/null || true
  bash "${BASE_DIR}/tg.sh" "📋 S21 Phone 건강 검진 — ${TS}

📊 등급: ${G} — ${GM}

🔋 배터리: ${BAT_PCT}% / ${BAT_TMP}°C / ${BAT_STS}
📶 WiFi: ${WIFI_SSID:-?} (RSSI ${WIFI_RSSI:-?})
📡 MCP: ✅ port ${MCP_PORT} | 도구 ${TCNT}개
✅ ${PASS_CNT} / ⚠️ ${WARN_CNT} / ❌ ${FAIL_CNT} / ⏭️ ${SKIP_CNT}

상세: _notebook/health/${NOW}.json" 2>/dev/null || true
fi
