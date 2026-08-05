# 🏠 집PC ↔ 누나 폰 연동 — Boss 2026-08-05

## 핵심: Tailscale Windows 네이티브 + Windows SSH + wsl

```
누나 폰 ──ssh──▶ Windows (Tailscale IP) ──wsl──▶ Ubuntu (Aider)
```

**Tailscale은 무조건 Windows에.** WSL 안에 깔면 네트워크 꼬임.
**SSH도 Windows OpenSSH.** WSL SSH 필요 없음.

---

## ① PC: Tailscale 설치
```powershell
# PowerShell 관리자
winget install tailscale.tailscale
tailscale up
# 브라우저 로그인 (폰이랑 같은 계정)
```

## ② PC: Windows SSH 서버 켜기
```powershell
# PowerShell 관리자
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd
Set-Service -Name sshd -StartupType 'Automatic'
```

## ③ PC: Tailscale IP 확인 (적어두기)
```powershell
tailscale ip -4
```
→ `100.x.x.x` 이거 적어둔다.

## ④ 폰: Tailscale + SSH 설치
```bash
# Termux 겉 (~ $) proot 안 아님
pkg install -y tailscale openssh
tailscale up
# 같은 계정으로 브라우저 인증
```

## ⑤ 폰 → PC SSH 접속 테스트
```bash
ssh [윈도우_사용자명]@[③에서_적은_IP]
```
윈도우 로그인 비번 입력. PowerShell/CMD 화면 뜨면 성공.

## ⑥ WSL + Aider 진입
```
wsl
cd ~/work
aider --model deepseek/deepseek-v4-pro
```

---

## PC 최초 1회: WSL + Aider 설치

```powershell
# PowerShell 관리자
wsl --install -d Ubuntu
# 재부팅, Ubuntu 사용자/비번 설정
```

```bash
# WSL Ubuntu
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential git curl wget python3 python3-pip pipx
pipx ensurepath
pipx install aider-chat

# API 키
cat >> ~/.bashrc << 'EOF'
export DEEPSEEK_API_KEY="sk-XXXX"
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export AIDER_MODEL="deepseek/deepseek-v4-pro"
EOF

# Git 클론
mkdir -p ~/work && cd ~/work
git clone --recurse-submodules https://github.com/helena751107/helena_phone.git

# 모델 설정
curl -o ~/.aider.model.settings.yml \
  https://raw.githubusercontent.com/helena751107/helena_phone/main/configs/aider.model.settings.yml
```

---

## Phone aliases (~/.bashrc)
```bash
export PC_IP=100.x.x.x
export PC_USER=사용자명

alias pc="ssh ${PC_USER}@${PC_IP}"
alias pc-wsl="ssh ${PC_USER}@${PC_IP} -t wsl"
alias pc-ds="ssh ${PC_USER}@${PC_IP} -t 'wsl ~/bin/ds'"
```

---

## ✅ 통과 기준
- `ssh 사용자@100.x.x.x` → PowerShell/CMD 뜸
- `wsl` → `aider` → DeepSeek 응답 옴
