# 🖥️ PC-WSL 개발환경 셋업 — Boss 2026-08-05

## 아키텍처

```
┌──────────────────────────────────────────────────────────┐
│                    Tailscale Mesh                         │
│                                                          │
│  ┌──────────────────┐       ┌─────────────────────────┐  │
│  │   S21 Phone       │       │   Windows PC             │  │
│  │   (Termux+proot)  │ SSH   │                          │  │
│  │                   │──────►│  ┌────────────────────┐ │  │
│  │  Claude Code(cc)  │       │  │ Windows Native      │ │  │
│  │  감사·기획         │       │  │  Aider(ds)          │ │  │
│  │                   │       │  │  DeepSeek API       │ │  │
│  │  Git (push/pull)  │       │  └────────────────────┘ │  │
│  └──────────────────┘       │                          │  │
│                              │  ┌────────────────────┐ │  │
│                              │  │ WSL2 Ubuntu         │ │  │
│                              │  │  Aider(ds)          │ │  │
│                              │  │  DeepSeek API       │ │  │
│                              │  │  SSH server ←───────┤─┼──│── Phone SSH Target
│                              │  │  Git repos          │ │  │
│                              │  └────────────────────┘ │  │
│                              └─────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

**3중 에이전트 체제:**
| 머신 | 쉘 | 호출 | 역할 | LLM |
|------|----|------|------|-----|
| S21 Phone | Termux/proot | `cc` | 감사·기획·Claude Code | DeepSeek |
| Windows Native | PowerShell/CMD | `ds` | 작업반장 (윈도우 파일 조작) | DeepSeek (Aider) |
| WSL2 Ubuntu | bash | `ds` | 작업반장 (리눅스·Git·서버) | DeepSeek (Aider) |

**왜 양쪽인가:**
- **Windows ds**: 윈도우 전용 도구·파일 작업, GUI 연동, PowerShell 자동화
- **WSL ds**: Git 레포, 리눅스 서버, Phone과 SSH 통합, Docker·빌드

**연결:**
- Tailscale mesh VPN → Phone ↔ PC 같은 네트워크
- SSH: Phone → WSL (Tailscale IP), key auth only
- Git: WSL에서 주로 관리, Windows ds는 WSL 경로 접근 가능 (`\\wsl$\Ubuntu\...`)

---

## 1단계: Windows + WSL2 기초 셋업

### 1-A: WSL2 설치
```powershell
# PowerShell (관리자)
wsl --install -d Ubuntu
# 재부팅 후 Ubuntu 사용자/비번 설정
```

### 1-B: WSL 기본 패키지
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential git curl wget python3 python3-pip pipx openssh-server
pipx ensurepath
```

### 1-C: Windows에 Python 설치
```powershell
# PowerShell
winget install Python.Python.3.12
# 또는 https://python.org 에서 다운로드
```

---

## 2단계: Tailscale 설치 (Windows)

```powershell
# https://tailscale.com/download/windows 에서 설치
# 설치 후 tray에서 로그인
# WSL은 Windows 호스트의 Tailscale IP 공유 (WSL2 네트워킹 기본)
```

### S21 Phone
```bash
# Termux에서 (proot 밖, 일반 사용자로)
pkg install tailscale
tailscale up
# 인증 URL → 브라우저 로그인
```

**확인:**
```bash
tailscale status
# PC (Windows): 100.x.x.x
# Phone: 100.x.x.x
```

> 📌 **Tailscale은 Windows에만 설치.** WSL2는 기본적으로 Windows의 네트워크를 미러링하므로 Windows Tailscale IP로 WSL에도 접근 가능.

---

## 3단계: DeepSeek API 키 (양쪽 공통)

### WSL
```bash
cat >> ~/.bashrc << 'EOF'
export DEEPSEEK_API_KEY="sk-XXXX"
export OPENROUTER_API_KEY="sk-or-v1-XXXX"
export DEEPSEEK_MODEL="deepseek/deepseek-chat"
EOF
source ~/.bashrc
```

### Windows
```powershell
# PowerShell 프로필에 추가
notepad $PROFILE
# 또는 GUI: 시스템 환경 변수 → DEEPSEEK_API_KEY, OPENROUTER_API_KEY
[Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", "sk-XXXX", "User")
[Environment]::SetEnvironmentVariable("OPENROUTER_API_KEY", "sk-or-v1-XXXX", "User")
```

---

## 4단계: Aider + ds 래퍼 — Windows Native

### 설치
```powershell
pip install aider-chat
# 또는 pipx
pipx install aider-chat
```

### `ds.ps1` (PowerShell 래퍼)
```powershell
# C:\Users\<사용자>\bin\ds.ps1
param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Args
)

$env:REPO = if ($env:REPO) { $env:REPO } else { "\\wsl$\Ubuntu\home\$env:USERNAME\work\helena_phone" }
$env:MODEL = if ($env:DEEPSEEK_MODEL) { $env:DEEPSEEK_MODEL } else { "deepseek/deepseek-chat" }

Set-Location $env:REPO

Write-Host "🔧 ds (Windows) — Aider + DeepSeek ($env:MODEL)" -ForegroundColor Cyan
Write-Host "📂 $env:REPO" -ForegroundColor Cyan
Write-Host ""

aider --model "openrouter/$env:MODEL" --no-auto-commits --no-gitignore @Args
```

### `ds.bat` (CMD 래퍼, 간단 버전)
```batch
@echo off
REM C:\Users\<사용자>\bin\ds.bat
set REPO=%REPO%==C:\Users\%USERNAME%\work\helena_phone
set MODEL=%DEEPSEEK_MODEL%==deepseek/deepseek-chat
cd /d %REPO%
echo 🔧 ds (Windows CMD) — Aider + DeepSeek (%MODEL%)
echo 📂 %REPO%
aider --model openrouter/%MODEL% --no-auto-commits --no-gitignore %*
```

```powershell
# PATH에 추가
mkdir C:\Users\$env:USERNAME\bin
$path = [Environment]::GetEnvironmentVariable("PATH", "User")
[Environment]::SetEnvironmentVariable("PATH", "$path;C:\Users\$env:USERNAME\bin", "User")
```

---

## 5단계: Aider + ds 래퍼 — WSL Ubuntu

```bash
# 설치
pipx install aider-chat
```

### `~/bin/ds` (bash 래퍼)
```bash
#!/bin/bash
# ds — Aider + DeepSeek 작업반장 (WSL)
REPO="${REPO:-$HOME/work/helena_phone}"
MODEL="${DEEPSEEK_MODEL:-deepseek/deepseek-chat}"
cd "$REPO" || { echo "❌ $REPO 없음"; exit 1; }

echo "🔧 ds (WSL) — Aider + DeepSeek (${MODEL})"
echo "📂 $REPO"
echo ""

aider \
  --model "openrouter/${MODEL}" \
  --no-auto-commits \
  --no-gitignore \
  "$@"
```

```bash
chmod +x ~/bin/ds
```

---

## 6단계: SSH 서버 + Phone 키 교환

### WSL에서
```bash
sudo apt install -y openssh-server
sudo service ssh start
# WSL2에서 systemctl 안 될 경우:
sudo sshd -D &  # 또는 /etc/init.d/ssh start
```

### Phone → WSL 키 배포

Phone의 SSH 공개키 (`~/.ssh/id_ed25519.pub`)를 WSL의 `~/.ssh/authorized_keys`에 추가.

```bash
# WSL에서
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIG5ohGtm3SbeKQzFe2glSRlIAwLurJJsiiHRhYn0R9L5 s21-phone-20260805" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

```bash
# Phone에서 테스트
ssh <WSL사용자>@<PC_Tailscale_IP> "echo '✅ 연결 OK'"
```

> ⚠️ WSL2 SSH는 Windows 방화벽에서 Tailscale 인터페이스의 22번 포트를 허용해야 할 수 있음.
> 또는 SSH를 2222 같은 대체 포트로 띄우는 것도 방법.

---

## 7단계: Git 레포 + 서브모듈 클론

```bash
# WSL에서
mkdir -p ~/work && cd ~/work
git clone --recurse-submodules https://github.com/helena751107/helena_phone.git
# 또는 SSH
git clone --recurse-submodules git@github.com:helena751107/helena_phone.git
```

---

## 8단계: Phone ↔ PC 워크플로우

### 일일 작업 흐름
```bash
# 1. Phone → WSL 접속
ssh boss@100.x.x.x

# 2. 최신 코드 pull
cd ~/work/helena_phone && git pull --recurse-submodules

# 3. Aider 작업 (WSL ds)
ds "이 기능 구현해줘"

# 4. 결과 push
git push

# 5. Phone에서 pull
git pull --recurse-submodules
```

### Phone aliases (`scripts/phone-pc-aliases.sh`)
```bash
source ~/work/scripts/phone-pc-aliases.sh
export PC_IP=100.x.x.x  # PC Tailscale IP로 변경

pc          # SSH 접속
pc-status   # PC git 상태
pc-ds       # PC에서 Aider 실행
pc-push     # push + PC pull
```

---

## 🆚 양쪽 ds 사용 판단 기준

| 상황 | 어디서 `ds` 호출 |
|------|-----------------|
| Git 레포 작업, 서버 셋업, 빌드 | WSL |
| 윈도우 파일 편집, PowerShell 자동화 | Windows Native |
| Phone에서 원격 작업 | SSH → WSL |
| GUI 도구 연동 (VS Code 등) | Windows Native |
| Docker, Linux 전용 도구 | WSL |

---

## 점검 목록

- [ ] WSL2 Ubuntu 설치 + `wsl -l -v` 확인
- [ ] Windows Python 설치 (`python --version`)
- [ ] Tailscale Windows 설치 + Phone과 같은 tailnet
- [ ] Phone SSH 키 → WSL authorized_keys 등록
- [ ] Phone → WSL SSH 접속 성공
- [ ] DeepSeek API 키 (Windows 환경변수 + WSL .bashrc)
- [ ] Windows: `aider --version`
- [ ] WSL: `aider --version`
- [ ] `ds` 래퍼 Windows (ds.ps1) + WSL (~/bin/ds) 양쪽 테스트
- [ ] Git clone WSL에 완료
- [ ] 전체 사이클 1회: Phone SSH → WSL ds → git push → Phone pull

---

## 현재 상태 (2026-08-05)

| 항목 | S21 Phone | Windows PC |
|------|-----------|------------|
| OS | Ubuntu 26.04 (proot) | ❌ |
| Tailscale | ❌ (Termux 미설치) | ❌ |
| SSH 키 | ✅ `id_ed25519` 생성됨 | ❌ |
| DeepSeek API | Claude Code 내장 | ❌ |
| Aider | ❌ | ❌ |
| Git | ✅ | ❌ |

**Phone 준비 완료:** SSH 키 있음, aliases 스크립트 있음, 셋업 가이드 있음.  
**다음 액션:** PC에서 1단계부터 시작.
