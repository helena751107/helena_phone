# 🏠 누나 PC — 최종 (WSL 없음, Windows Native) — Boss 2026-08-05

## 결정: WSL 포기, Windows만

Celeron 3855U + 4GB. WSL2는 RAM 부족으로 불가.
**Windows Native 앱 4개만 깐다.** 연결 허브 + 빌드 캐시 용도.

## PC 역할: 연결 허브

```
Celeron PC (Windows 10, WSL X)
├── Tailscale       → VPN (Phone ↔ PC ↔ 어디서나)
├── OpenSSH Server  → Phone에서 PC 원격 제어
├── ADB             → USB/WiFi로 폰 디버깅 (상시 연결)
├── Git             → 레포 싱크, 빌드 캐시 보관
└── 끝.
```

RAM 사용: Windows 2GB + 앱들 500MB = 2.5GB. **남는 거 1.5GB.**

## 무거운 건 전부 Actions로

| 작업 | 어디서 | 비용 |
|------|--------|------|
| APK 빌드 | GitHub Actions (7GB) | 0원 |
| 오디오 렌더링 | GitHub Actions | 0원 |
| CAD | GitHub Actions | 0원 |
| AI 코딩·기획 | S21 + DeepSeek | 0원 |
| GPU·영상 | Grok + RunPod | 있음 |

## 설치 (PowerShell 관리자, 딱 4줄)

```powershell
# 1. Tailscale
winget install tailscale.tailscale
tailscale up

# 2. SSH Server
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd
Set-Service -Name sshd -StartupType 'Automatic'

# 3. ADB
winget install Google.PlatformTools

# 4. Git
winget install Git.Git

# 확인
tailscale ip -4
```

## Phone → PC 연결

```bash
# Tailscale IP 확인 후
ssh [사용자명]@100.x.x.x
# 붙으면 PowerShell/CMD
adb devices   # 폰 디버깅
```

---

## 전체 아키텍처 최종

```
┌──────────────┐   ┌─────────────────┐   ┌──────────────────┐
│   S21 Phone   │   │  Celeron PC      │   │  GitHub Actions   │
│   (메인)      │   │  (연결 허브)     │   │  (CPU 공장)       │
├──────────────┤   ├─────────────────┤   ├──────────────────┤
│ Claude Code  │◄──│ ADB·디버깅      │   │ APK 빌드 (7GB)    │
│ DeepSeek API │   │ Tailscale       │   │ 오디오 렌더링     │
│ AI·센서·이동 │   │ SSH·Git·캐시    │   │ CAD·FFmpeg       │
│              │   │                 │   │ 공짜 무제한       │
└──────────────┘   └─────────────────┘   └──────────────────┘
      ↑                   ↑                      ↑
  Exynos 8GB          Celeron 4GB          2코어 7GB
  항상 주머니          책상 고정              휘발성
```

## 이 PC가 못 하는 것 (인정)

- Docker → 필요 없음 (Actions로 충분)
- WSL2 → RAM 부족으로 불가
- GPU → Grok + RunPod
- 무거운 빌드 → Actions가 함

## 이 PC가 하는 것

- **늘 켜져 있음** → ADB로 폰 상시 연결
- **공인 IP 없이 접근** → Tailscale
- **Git 캐시** → Gradle·Flutter SDK 매번 다운 안 함
- **원격 터미널** → Phone에서 SSH로 PC 제어
