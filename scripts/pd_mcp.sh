#!/usr/bin/env bash
# pd_mcp.sh — PD Pipeline MCP 서버 시작/중지/생산 래퍼
#
# 사용:
#   bash scripts/pd_mcp.sh start       # HTTP 서버 백그라운드 시작 (port 8765)
#   bash scripts/pd_mcp.sh stop        # 서버 중지
#   bash scripts/pd_mcp.sh status      # 서버 상태 확인
#   bash scripts/pd_mcp.sh list        # 사용 가능한 에피소드 목록
#   bash scripts/pd_mcp.sh produce EP  # EP 생산 시작 (예: pd_magic)
#   bash scripts/pd_mcp.sh job JOBID   # 작업 상태 확인
#   bash scripts/pd_mcp.sh output      # 최근 완료 작업 출력 파일 확인

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MCP="$ROOT/helena-programming/mcp/pd_pipeline_mcp.py"
PORT=8765
URL="http://localhost:$PORT"

cmd="${1:-status}"

_api() {
  curl -s -X POST "$URL/" -H "Content-Type: application/json" -d "$1"
}

case "$cmd" in
  start)
    if pgrep -f "pd_pipeline_mcp.py --http" >/dev/null 2>&1; then
      echo "🟢 MCP server already running on port $PORT"
    else
      python3 "$MCP" --http --port "$PORT" &
      sleep 1
      if curl -s "$URL/health" >/dev/null 2>&1; then
        echo "🟢 MCP server started on http://0.0.0.0:$PORT"
        echo "   Tools: pd_produce · pd_status · pd_list · pd_stop · pd_output"
      else
        echo "🔴 Failed to start MCP server"
        exit 1
      fi
    fi
    ;;
  stop)
    if pgrep -f "pd_pipeline_mcp.py --http" >/dev/null 2>&1; then
      kill $(pgrep -f "pd_pipeline_mcp.py --http") 2>/dev/null
      sleep 0.5
      echo "🔴 MCP server stopped"
    else
      echo "⚪ MCP server not running"
    fi
    ;;
  status)
    if pgrep -f "pd_pipeline_mcp.py --http" >/dev/null 2>&1; then
      echo "🟢 MCP server running on port $PORT"
      curl -s "$URL/health"
      echo ""
    else
      echo "⚪ MCP server not running"
      echo "   Start: bash scripts/pd_mcp.sh start"
    fi
    ;;
  list)
    python3 "$MCP" --list
    ;;
  produce)
    ep="${2:-pd_intro}"
    echo "🎬 Producing: $ep"
    result=$(_api "{\"method\":\"tools/call\",\"params\":{\"name\":\"pd_produce\",\"arguments\":{\"ep_id\":\"$ep\",\"force\":true}}}")
    echo "$result" | python3 -c "
import sys, json
d = json.load(sys.stdin)
c = json.loads(d['content'][0]['text'])
j = json.loads(c)
if j.get('ok'):
    print(f\"✅ Job started: {j['job_id']}\")
    print(f\"   PID: {j['pid']}  |  Log: {j['log']}\")
    print(f\"   {j['hint']}\")
else:
    print(f\"❌ {j.get('error','unknown')}\")
"
    ;;
  job)
    jid="${2}"
    if [ -z "$jid" ]; then
      _api '{"method":"tools/call","params":{"name":"pd_status"}}' | python3 -c "
import sys, json
d = json.load(sys.stdin)
c = json.loads(d['content'][0]['text'])
j = json.loads(c)
if j.get('ok') and j.get('jobs'):
    print(f\"Total jobs: {j['total']}\")
    for job in j['jobs']:
        icon = '🟢' if job['status']=='running' else '✅' if job['status']=='complete' else '🔴'
        print(f\"  {icon} {job['job_id']} | {job['ep_id']} | {job['status']} | {job.get('started','?')}\")
else:
    print('No jobs found')
"
    else
      _api "{\"method\":\"tools/call\",\"params\":{\"name\":\"pd_status\",\"arguments\":{\"job_id\":\"$jid\"}}}" | python3 -c "
import sys, json
d = json.load(sys.stdin)
c = json.loads(d['content'][0]['text'])
j = json.loads(c)
print(f\"Status: {j.get('status')}  |  EP: {j.get('ep_id')}  |  Started: {j.get('started')}\")
if j.get('log_tail'):
    print(f\"--- LOG ---\n{j['log_tail']}\")
"
    fi
    ;;
  output)
    _api '{"method":"tools/call","params":{"name":"pd_output"}}' | python3 -c "
import sys, json
d = json.load(sys.stdin)
c = json.loads(d['content'][0]['text'])
j = json.loads(c)
if j.get('ok'):
    print(f\"Job: {j['job_id']}  |  EP: {j['ep_id']}  |  Status: {j['status']}\")
    for label, info in j.get('files', {}).items():
        print(f\"  📁 {label}: {info['path']} ({info['size_mb']}MB)\")
else:
    print(f\"No completed jobs\")
"
    ;;
  *)
    echo "Usage: pd_mcp.sh {start|stop|status|list|produce EP|job [JOBID]|output}"
    ;;
esac
