#!/bin/bash
# phone-mcp-server — proot Ubuntu에서 실행 (Termux:API 우회)
export PATH="/data/data/com.termux/files/usr/bin:$PATH"
cd /tmp/phone-mcp-server
node server.js "$@"
