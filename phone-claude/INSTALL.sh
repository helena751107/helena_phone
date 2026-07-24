#!/bin/bash
# ============================================
# 📱 Phone Claude — 갤럭시 AI 서버 설치 스크립트
# ============================================
# 출처: dtslib-papyrus gift/helena (본사 SSOT)

set -e
echo "🚀 Phone Claude 설치 시작"

# 1. Termux 기본 설정
pkg update -y && pkg upgrade -y
pkg install -y git curl wget python nodejs openssh

# 2. proot-distro Ubuntu
pkg install -y proot-distro
proot-distro install ubuntu
proot-distro login ubuntu -- apt update && apt install -y python3 nodejs git curl

# 3. Claude Code 설치 (npm)
npm install -g @anthropic-ai/claude-code

# 4. 기본 설정
git config --global user.name "helena751107"
git config --global user.email "helena751107@gmail.com"

echo "✅ 설치 완료! Claude Code 실행: claude"
echo "📋 다음 단계: GitHub 레포 clone → CLAUDE.md 확인"
