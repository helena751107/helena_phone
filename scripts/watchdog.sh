#!/usr/bin/env bash
# ==============================================================================
# watchdog.sh — 빠른 세션 상태 체크 (메모리·스왑·고아·이중세션)
# ==============================================================================
# 사용: hc  (alias)  또는  bash ~/work/scripts/watchdog.sh
# ==============================================================================

# ── 설정 ──────────────────────────────────────────────────────────────────────
MEM_AVAIL_CRIT=300
MEM_AVAIL_WARN=800
SWAP_PCT_CRIT=85
SWAP_PCT_WARN=65

# ── 수집 ──────────────────────────────────────────────────────────────────────

# 메모리 정보
while IFS=: read -r key val; do
  case "$key" in
    MemAvailable) MEM_AVAIL=$(( ${val% kB} / 1024 )) ;;
    MemTotal)     MEM_TOTAL=$(( ${val% kB} / 1024 )) ;;
    SwapTotal)    SWAP_TOTAL=$(( ${val% kB} / 1024 )) ;;
    SwapFree)     SWAP_FREE=$(( ${val% kB} / 1024 )) ;;
  esac
done < /proc/meminfo

[ -z "$SWAP_TOTAL" ] && SWAP_TOTAL=0
[ -z "$SWAP_FREE" ] && SWAP_FREE=0
SWAP_USED=$(( SWAP_TOTAL - SWAP_FREE ))
SWAP_PCT=0
[ "$SWAP_TOTAL" -gt 0 ] && SWAP_PCT=$(( SWAP_USED * 100 / SWAP_TOTAL ))

# 프로세스 정보
CLAUDE_COUNT=0
ORPHAN_COUNT=0
while IFS= read -r line; do
  pid=$(echo "$line" | awk '{print $2}')
  cpu=$(echo "$line" | awk '{print $3}')
  comm=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')

  case "$comm" in
    *"claude --dangerously-skip-permissions"*)
      # proot 래퍼는 제외 (proot 명령줄에 claude가 포함되므로)
      echo "$comm" | grep -qv 'proot' && CLAUDE_COUNT=$((CLAUDE_COUNT + 1))
      ;;
  esac

  case "$comm" in
    *"bfs -S dfs"*|*"find /"*)
      ORPHAN_COUNT=$((ORPHAN_COUNT + 1))
      ;;
  esac
done < <(ps aux 2>/dev/null | tail -n +2)

# Load
read -r LOAD1 _ _ < /proc/loadavg 2>/dev/null || LOAD1="0"

# ── 판정 ──────────────────────────────────────────────────────────────────────

LEVEL="ok"
ICON=""
MSG=""

if [ "$MEM_AVAIL" -lt "$MEM_AVAIL_CRIT" ] 2>/dev/null; then
  LEVEL="critical"
  MSG="$MSG
  MEM  CRIT: ${MEM_AVAIL}MB available  (< ${MEM_AVAIL_CRIT}MB)"
elif [ "$MEM_AVAIL" -lt "$MEM_AVAIL_WARN" ] 2>/dev/null; then
  [ "$LEVEL" = "ok" ] && LEVEL="warning"
  MSG="$MSG
  MEM  WARN: ${MEM_AVAIL}MB available  (< ${MEM_AVAIL_WARN}MB)"
fi

if [ "$SWAP_PCT" -gt "$SWAP_PCT_CRIT" ] 2>/dev/null; then
  LEVEL="critical"
  MSG="$MSG
  SWAP CRIT: ${SWAP_PCT}%  (> ${SWAP_PCT_CRIT}%)"
elif [ "$SWAP_PCT" -gt "$SWAP_PCT_WARN" ] 2>/dev/null; then
  [ "$LEVEL" = "ok" ] && LEVEL="warning"
  MSG="$MSG
  SWAP WARN: ${SWAP_PCT}%  (> ${SWAP_PCT_WARN}%)"
fi

if [ "$ORPHAN_COUNT" -gt 0 ] 2>/dev/null; then
  [ "$LEVEL" = "ok" ] && LEVEL="warning"
  MSG="$MSG
  ORPHAN: ${ORPHAN_COUNT} scanner(s) — kill -9 them"
fi

if [ "$CLAUDE_COUNT" -gt 1 ] 2>/dev/null; then
  LEVEL="critical"
  MSG="$MSG
  CLAUDE: ${CLAUDE_COUNT} sessions — should be 1"
fi

case "$LEVEL" in
  critical) ICON="🔴"; COLOR="\033[0;31m" ;;
  warning)  ICON="🟡"; COLOR="\033[0;33m" ;;
  ok)       ICON="🟢"; COLOR="\033[0;32m" ;;
esac
NC="\033[0m"

# ── 출력 ──────────────────────────────────────────────────────────────────────

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
printf "${COLOR}  ${ICON}  %-28s${NC}\n" "${LEVEL}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
printf "  MEM   %sMB avail / %sMB total\n" "$MEM_AVAIL" "$MEM_TOTAL"
printf "  SWAP  %sMB used / %sMB total  (%s%%)\n" "$SWAP_USED" "$SWAP_TOTAL" "$SWAP_PCT"
printf "  LOAD  %s\n" "$LOAD1"
printf "  CLAUDE %s session(s)\n" "$CLAUDE_COUNT"
printf "  ORPHAN %s scanner(s)\n" "$ORPHAN_COUNT"
if [ -n "$MSG" ]; then
  echo "  ──────────────────────────────"
  echo "$MSG"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
