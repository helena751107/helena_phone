# 1.2 proot Ubuntu 설치

> Termux 위에 Ubuntu 컨테이너를 올리는 방법

## 왜 proot인가?

- **루팅 필요 없음** — 일반 앱 권한으로 동작
- **삼성페이/뱅킹앱 안전** — 시스템을 건드리지 않음
- **완전한 Ubuntu** — apt로 패키지 설치 가능

## 설치

```bash
# proot-distro 설치
pkg install proot-distro -y

# Ubuntu 설치
proot-distro install ubuntu

# Ubuntu 로그인
proot-distro login ubuntu

# (이제부터 Ubuntu 셸)
apt update && apt upgrade -y
apt install git curl nodejs -y
```

## 자주 쓰는 명령어

```bash
# 로그인
proot-distro login ubuntu

# root 권한으로 명령 실행
proot-distro login ubuntu -- bash -c "apt install nginx"

# 제거
proot-distro remove ubuntu
```

## 주의사항

- proot은 **진짜 root가 아님** — `systemd` 안 됨 (서비스는 직접 실행)
- Docker 안 됨 (호환성 문제)
- 모든 네트워크는 기본적으로 호스트(Termux)와 공유

## 트러블슈팅

| 증상 | 해결 |
|------|------|
| `proot-distro install` 실패 | `pkg update` 후 재시도 |
| DNS 안 잡힘 | `echo "nameserver 8.8.8.8" > /etc/resolv.conf` |
| "Cannot run 'pkg' command as root" | proot 안에선 이 에러 안 남 (Termux에서만 발생) |

## 다음 단계

→ [Claude Code + DeepSeek Radar 설치](./claude-code.md)
