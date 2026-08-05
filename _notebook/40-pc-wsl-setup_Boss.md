# 🖥️ PC-WSL 부트스트랩 — Boss 2026-08-05

## 핵심 원칙: Boss는 자판을 치지 않는다

```
Boss가 직접 할 일:  Python 설치 + Aider 설치 (2줄, 5분)
그 이후 전부:        Aider에게 시킨다
```

---

## 0단계: Boss — Windows 10에 Aider 설치 (직접)

PowerShell 열고 딱 이거만:

```powershell
# 1. Python 설치 (없으면)
winget install Python.Python.3.12

# 2. Aider 설치
pip install aider-chat
```

끝. 이제부터 Aider한테 말로 시키면 된다.

---

## 1단계: Aider 프롬프트 — 전체 셋업 위임

아래 전문을 **복사해서 Aider에 붙여넣기**:

```
너는 Windows 10 + WSL2 Ubuntu 개발환경을 셋업하는 작업반장이다.
지금부터 내가 시키는 모든 것을 순서대로 실행해라.
필요한 명령어는 직접 실행하고, 안 되는 건 대안을 찾아서 해결해라.

--- 작업 목록 ---

[1] Tailscale 설치 + 로그인
- https://tailscale.com/download/windows 에서 Windows용 다운로드 + 설치
- 설치 후 tailscale up 실행, 로그인 URL 출력
- 나한테 "여기 로그인해" 하고 URL 던져줘

[2] Tailscale 상태 확인
- tailscale status 로 PC의 Tailscale IP 확인
- 이 IP를 PC_IP 변수로 기록해둬

[3] WSL2 설치 + Ubuntu
- PowerShell(관리자): wsl --install -d Ubuntu
- 재부팅 필요하면 말해줘
- Ubuntu 초기 사용자/비번 설정

[4] WSL 기본 셋업
- WSL Ubuntu 진입해서:
  sudo apt update && sudo apt upgrade -y
  sudo apt install -y build-essential git curl wget python3 python3-pip pipx openssh-server
  pipx ensurepath

[5] WSL에 Aider 설치
- pipx install aider-chat
- 테스트: aider --version

[6] DeepSeek API 키 설정
- Windows 환경변수 + WSL ~/.bashrc 양쪽에:
  OPENROUTER_API_KEY=sk-or-v1-XXXX  (← 내가 키 줄 거야)
  DEEPSEEK_MODEL=deepseek/deepseek-chat

[7] WSL SSH 서버
- sudo service ssh start
- Windows 방화벽: Tailscale 인터페이스 22번 허용

[8] Phone SSH 키 등록
- WSL의 ~/.ssh/authorized_keys에 다음 키 추가:
  ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIG5ohGtm3SbeKQzFe2glSRlIAwLurJJsiiHRhYn0R9L5 s21-phone-20260805
- 권한: chmod 600 ~/.ssh/authorized_keys

[9] Git 레포 클론 (WSL)
- cd ~/work
- git clone --recurse-submodules https://github.com/helena751107/helena_phone.git

[10] ds 래퍼 설치 (WSL + Windows 양쪽)
- WSL: ~/bin/ds 생성
  #!/bin/bash
  REPO="${REPO:-$HOME/work/helena_phone}"
  MODEL="${DEEPSEEK_MODEL:-deepseek/deepseek-chat}"
  cd "$REPO" || exit 1
  aider --model "openrouter/${MODEL}" --no-auto-commits --no-gitignore "$@"

- Windows: C:\Users\<사용자>\bin\ds.ps1 생성 (동일 기능 PowerShell 버전)

[11] 전체 연결 테스트
- Phone → WSL SSH: ssh <user>@<PC_IP> "echo 연결OK"
- WSL에서 ds "이 레포 구조 설명해줘" 테스트
- Windows에서 ds "현재 디렉토리 파일 목록" 테스트

--- 규칙 ---
- 각 단계 완료할 때마다 "[N]/11 완료: 뭘 했는지" 형식으로 보고
- 안 되는 건 원인 분석해서 대안 제시
- 나한테 물어봐야 할 건 명확하게 질문 (API 키 등)
- 절대 대충 넘어가지 마
```

---

## 2단계: Phone ↔ PC 연동 확인

Aider가 셋업 다 끝내면, Phone에서:

```bash
source ~/work/scripts/phone-pc-aliases.sh
export PC_IP=<PC_Tailscale_IP>

pc-check   # PC 환경 확인
pc         # SSH 접속
```

---

## 아키텍처 (최종)

```
Boss → Aider (Windows 10) → "셋업해"
     → Aider가 WSL 설치
     → Aider가 Tailscale 설치
     → Aider가 SSH 구성
     → Aider가 Git 클론
     → Aider가 ds 래퍼 설치

Phone(Claude Code) ←→ SSH/Tailscale ←→ PC(Aider×2: Win+WSL)
```

---

## 현재 상태

| 항목 | S21 Phone | Windows 10 PC |
|------|-----------|---------------|
| SSH 키 | ✅ | ❌ Aider가 할 거 |
| Tailscale | ⏳ Termux pkg 필요 | ❌ Aider가 할 거 |
| Aider | ❌ (Claude Code 사용 중) | ❌ Boss가 pip install |
| Git | ✅ | ❌ Aider가 클론 |
| 가이드 | ✅ | ✅ 이 문서 |

**Boss 액션:** PowerShell에서 `pip install aider-chat` → 위 프롬프트 붙여넣기 → 끝.
