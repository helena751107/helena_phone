#!/bin/bash
# 📄 phone-mcp.sh — MCP 서버 실행 스크립트
# 📍 저장 위치: /root/work/phone-mcp.sh
# 🚀 실행: bash phone-mcp.sh --port 3456
#
# Termux 환경에서 phone-mcp-server를 실행한다.
# 핵심: PATH에 Termux 바이너리 경로를 꼭 포함시켜야 함
# (안 그러면 termux-battery-status 등이 ENOENT)

export PATH="/data/data/com.termux/files/usr/bin:$PATH"
cd /tmp/phone-mcp-server
node server.js "$@"
