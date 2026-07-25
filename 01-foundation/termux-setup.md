# 1.1 Termux 설치

> 안드로이드에서 리눅스 네이티브 환경을 실행하는 앱

## 설치 방법

### 1. F-Droid 설치
Termux는 **Play Store 버전 말고 F-Droid 버전**을 써야 한다.
Play Store 버전은 업데이트가 중단됨.

1. [F-Droid](https://f-droid.org/) 다운로드 & 설치
2. F-Droid 검색 → `Termux` 설치
3. F-Droid 검색 → `Termux:API` 설치 (별도 앱! 하드웨어 제어용)

### 2. 기본 패키지 설치

```bash
pkg update && pkg upgrade -y
pkg install git curl nodejs-lts python -y
```

### 3. Termux:API 패키지 설치

```bash
pkg install termux-api -y
```

> ⚠️ 이거 안 깔면 phone-mcp-server가 termux-battery-status 등 모든 명령어를 **ENOENT**로 실패한다.
> 반드시 설치할 것.

### 4. 저장소 접근 권한

```bash
termux-setup-storage
# → 폰에서 권한 허용 팝업 → Allow
```

### 5. 설치 확인

```bash
termux-battery-status
# → {"percentage": 64, "temperature": 34.1, ...}  ← JSON 떠야 정상
```

## 다음 단계

→ [proot Ubuntu 설치](./proot-ubuntu.md)로 리눅스 컨테이너 만들기
