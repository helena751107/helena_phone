# 🖥️ PC 개발환경 셋업 — Boss 2026-08-05

## 핵심: 폰(Termux) = PC(Windows) 동일 환경

```
폰:  pip install aider-chat  →  ds.sh  →  deepseek-v4-pro
PC:  pip install aider-chat  →  ds.bat →  deepseek-v4-pro
              ↑                              ↑
         똑같은 DeepSeek API, 똑같은 모델, 똑같은 설정
```

---

## 1단계: Boss — PC에 DeepSeek + Aider 설치 (1회)

```cmd
REM GitHub에서 레포 클론 또는 scripts만 다운로드 후:
pc-install-ds.bat
```

이게 하는 일:
1. Python 확인 (없으면 winget 설치)
2. `pip install aider-chat`
3. DeepSeek API 키 입력받아 환경변수 등록
4. `ds.bat` + `ds.ps1` → `~/bin/` + PATH 등록
5. `aider.model.settings.yml` → `~/` (Claude 행세 방지 설정)
6. `ANTHROPIC_BASE_URL` → `https://api.deepseek.com/anthropic`
7. 테스트 실행

**API 키:** https://platform.deepseek.com/api_keys 에서 발급 (폰이랑 같은 키 쓰면 됨)

---

## 2단계: ds 실행 테스트

```cmd
ds
```

폰에서 `ds` 칠 때랑 똑같은 게 뜬다:
```
▶ ds = Aider + DeepSeek
  model: deepseek/deepseek-v4-pro
  cwd:   C:\Users\...
  종료:  /exit 또는 Ctrl+C
```

---

## 3단계: 나머지는 ds한테 시킨다

```
ds "WSL2 Ubuntu 설치하고 Tailscale 깔고 SSH 서버 구성해줘.
    Phone SSH 공개키 등록하고 Git 레포 클론하고
    WSL에도 똑같이 Aider 설치해줘.
    끝나면 연결 테스트까지."
```

---

## 파일 구조 (폰 ↔ PC 매핑)

| 폰 (Termux) | PC (Windows) | 설명 |
|-------------|-------------|------|
| `~/.local/bin/aider` | `pip install aider-chat` | Aider |
| `DEEPSEEK_API_KEY` in `.bashrc` | `DEEPSEEK_API_KEY` 시스템 환경변수 | API 키 |
| `ANTHROPIC_BASE_URL=api.deepseek.com/anthropic` | 동일 | 엔드포인트 |
| `~/.aider.model.settings.yml` | `%USERPROFILE%\.aider.model.settings.yml` | Claude 행세 방지 |
| `~/work/scripts/ds.sh` | `%USERPROFILE%\bin\ds.bat` / `ds.ps1` | 실행 래퍼 |
| `~/work/.secrets.env` | `%USERPROFILE%\.deepseek.env` (API키만) | 시크릿 |

---

## 현재 상태

| 항목 | S21 Phone | Windows 10 PC |
|------|-----------|---------------|
| Aider | ✅ v0.86.2 | ❌ → `pc-install-ds.bat` |
| DeepSeek API | ✅ `sk-c400...` | ❌ → 같은 키 입력 |
| Model | `deepseek-v4-pro` | 동일 |
| ds 래퍼 | ✅ `ds.sh` | ✅ `ds.bat` / `ds.ps1` 준비됨 |
| Model settings | ✅ | ✅ 복사 준비됨 (configs/) |
| WSL / Tailscale / SSH | ❌ | ❌ → ds가 할 거 |

**Boss 액션:** PC에서 `pc-install-ds.bat` 실행. 그 담부턴 ds한테 말로 시키면 된다.
