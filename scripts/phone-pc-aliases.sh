#!/bin/bash
# 📱 phone-pc-aliases.sh — S21 Phone → PC 연결 편의 aliases
# 사용법: source phone-pc-aliases.sh  (또는 ~/.bashrc에 추가)
# Boss 2026-08-05

# ⚠️ PC 설정 후 PC_IP를 실제 Tailscale IP로 변경할 것
PC_IP="${PC_IP:-100.0.0.0}"      # PC WSL Tailscale IP
PC_USER="${PC_USER:-boss}"        # WSL 사용자명
PC_WORK="${PC_WORK:-~/work/helena_phone}"

# SSH 접속
alias pc="ssh ${PC_USER}@${PC_IP}"

# PC에서 명령 실행
alias pc-run='ssh ${PC_USER}@${PC_IP}'

# PC 작업 디렉토리로 바로 이동
alias pc-work="ssh ${PC_USER}@${PC_IP} -t 'cd ${PC_WORK} && exec \$SHELL -l'"

# Git: Phone → PC 양방향 동기화
alias pc-push='git push && ssh ${PC_USER}@${PC_IP} "cd ${PC_WORK} && git pull --recurse-submodules"'
alias pc-pull='git pull --recurse-submodules'
alias pc-status='ssh ${PC_USER}@${PC_IP} "cd ${PC_WORK} && git status --short"'

# ds 실행 (PC에서 Aider 호출)
alias pc-ds='ssh ${PC_USER}@${PC_IP} -t "cd ${PC_WORK} && ds"'

# Tailscale 상태
alias pc-net='ssh ${PC_USER}@${PC_IP} "tailscale status"'

# 설정 확인
alias pc-check='echo "PC: ${PC_USER}@${PC_IP}" && ssh ${PC_USER}@${PC_IP} "echo -n \"OS: \" && cat /etc/os-release | head -1 && echo -n \"Aider: \" && which aider && echo -n \"ds: \" && which ds && echo -n \"Git: \" && cd ${PC_WORK} && git log --oneline -1"'

echo "📱 Phone↔PC aliases 로드됨"
echo "   pc         — SSH 접속"
echo "   pc-work    — 작업 디렉토리로 바로 이동"
echo "   pc-push    — push + PC pull"
echo "   pc-status  — PC git 상태"
echo "   pc-ds      — PC에서 Aider 실행"
echo "   pc-net     — Tailscale 상태"
echo "   pc-check   — PC 환경 확인"
echo ""
echo "   ⚠️  PC Tailscale IP를 설정하세요: export PC_IP=100.x.x.x"
