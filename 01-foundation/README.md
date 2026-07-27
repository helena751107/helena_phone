# 1단계: 기반 설치 — 폰을 리눅스 서버로

> 놀고 있는 갤럭시 폰을 Ubuntu 서버로 만드는 과정

## 목차

| # | 내용 | 난이도 | 시간 |
|---|------|--------|------|
| 1.1 | [Termux 설치](./termux-setup.md) | ⭐ 초급 | 10분 |
| 1.2 | [proot Ubuntu](./proot-ubuntu.md) | ⭐⭐ 중급 | 15분 |
| 1.3 | [Claude Code + DeepSeek](./claude-code.md) | ⭐⭐ 중급 | 20분 |
| 1.4 | [Git/GitHub 연결](./git-github.md) | ⭐ 초급 | 10분 |

## 전체 흐름

```
F-Droid → Termux 설치 → pkg update
    → proot-distro Ubuntu 설치
        → Claude Code + DeepSeek
            → Git → GitHub 연결
                → 🎉 완료
```

## 왜 이렇게 하나?

**안드로이드는 리눅스 커널 위에서 돌아간다.** Termux는 그 위에서 네이티브 리눅스 환경을 제공하고, proot-distro는 완전한 우분투 컨테이너를 만들어준다. 이렇게 하면 일반 PC 우분투에서 돌아가는 거의 모든 소프트웨어를 폰에서 실행할 수 있다.

단, **루팅은 안 한다.** 루팅하면 삼성페이/뱅킹앱이 망가진다. proot은 루트 권한을 모방할 뿐 실제로 시스템을 건드리지 않아서 안전하다.
