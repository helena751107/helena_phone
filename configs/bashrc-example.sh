# 📄 .bashrc 예시 — proot Ubuntu 자동 설정
# 📍 저장 위치: /root/.bashrc (proot Ubuntu 내부)
#
# phone-mcp-server 자동 시작 + PATH 설정 포함

# ---- 기본 PATH ----
export PATH="$HOME/.local/bin:$PATH"

# ---- Termux 바이너리 PATH (필수!) ----
# phone-mcp-server가 termux-* 명령어를 찾을 수 있게 해줌
export PATH="/data/data/com.termux/files/usr/bin:$PATH"

# ---- phone-mcp-server 자동 시작 ----
# proot Ubuntu 로그인 시 자동 실행 (이미 떠 있으면 생략)
pgrep -f "phone-mcp-server" > /dev/null 2>&1 || \
  nohup bash /root/work/phone-mcp.sh --port 3456 > /tmp/phone-mcp.log 2>&1 &

# ---- 편의 Aliases ----
alias hc='bash /root/work/phone-health.sh'
alias hcf='bash /root/work/phone-health.sh --full'
alias hct='bash /root/work/phone-health.sh --telegram'
alias tg='bash /root/work/tg.sh'
alias mcp-restart='pkill -f "node server" 2>/dev/null; sleep 1; bash /root/work/phone-mcp.sh --port 3456 &'

# ── DeepSeek Aider (래퍼: 오염 히스토리 정리 + diff + 정체성 프롬프트) ──
alias ds='proot-distro login ubuntu -- bash -lc "bash /root/work/scripts/ds.sh"'
alias dsflash='proot-distro login ubuntu -- bash -lc "AIDER_MODEL=deepseek/deepseek-v4-flash bash /root/work/scripts/ds.sh"'

# ── Grok CLI (Termux → proot Ubuntu) — 직관적 이름 ──
alias grok='proot-distro login ubuntu -- bash -lc "export PATH=\$HOME/.grok/bin:\$PATH; cd ~/work; grok"'
alias groklogin='proot-distro login ubuntu -- bash -lc "export PATH=\$HOME/.grok/bin:\$PATH; grok login --device-auth"'
alias grokc='proot-distro login ubuntu -- bash -lc "export PATH=\$HOME/.grok/bin:\$PATH; cd ~/work; grok -c"'
alias agent='proot-distro login ubuntu -- bash -lc "export PATH=\$HOME/.grok/bin:\$PATH; agent"'
# 예전 이름 호환
alias gr='grok'
alias grlogin='groklogin'
alias grc='grokc'
