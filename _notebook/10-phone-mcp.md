# phone-mcp-server — 핸드폰 통제 MCP

> 순수 Termux:API 기반. 루트/ADB/Shizuku 불필요.
> 설치일: 2026-07-24

## 상태

| 항목 | 값 |
|------|-----|
| 서버 | `http://localhost:3456/mcp` |
| 상태 | ✅ **검증 완료** (2026-07-24) |
| 도구 | 18개 |
| 소스 | `github.com/htekdev/phone-mcp-server` |

## 설치 위치

| 파일 | 설명 |
|------|------|
| `/tmp/phone-mcp-server/` | 소스 코드 (clone) |
| `/root/work/phone-mcp.sh` | 실행 스크립트 |
| `/root/.claude/settings.json` | MCP 등록 (Streamable HTTP) |
| `~/.bashrc` | 세션 자동 시작 |

## 사용 가능한 도구

| 도구 | 설명 | 권한 필요 |
|------|------|----------|
| `send_sms` | SMS 발송 | SMS |
| `read_sms` | SMS 수신함 조회 | SMS |
| `get_contacts` | 연락처 목록 | 연락처 |
| `get_location` | GPS 위치 | 위치 |
| `get_battery` | 배터리 잔량/온도 | - |
| `get_clipboard` | 클립보드 읽기 | - |
| `set_clipboard` | 클립보드 쓰기 | - |
| `take_photo` | 사진 촬영 | 카메라 |
| `get_call_log` | 통화 기록 | 통화기록 |
| `make_call` | 전화 걸기 | 전화 |
| `get_wifi_info` | WiFi 정보 | - |
| `flashlight` | 플래시 ON/OFF | - |
| `vibrate` | 진동 | - |
| `send_notification` | 알림 표시 | - |
| `get_volume` | 볼륨 확인 | - |
| `set_volume` | 볼륨 조절 | - |
| `record_audio` | 음성 녹음 | 마이크 |
| `device_info` | 종합 디바이스 정보 | - |
| `shell` | 셸 명령 (보안 필터) | - |

## 시작 방법

```bash
# 수동 시작
bash ~/work/phone-mcp.sh --port 3456

# 자동 시작 (.bashrc에 등록됨)
# proot Ubuntu 로그인 시 자동 실행
```

## 주의사항

- 최초 각 API 사용 시 폰에서 권한 팝업 허용 필요
- SMS/RCS는 읽을 수 없음 (SMS/MMS만)
- 같은 WiFi 네트워크 필요
- settings.json 수정 후 cc 재시작해야 MCP 도구 활성화됨
- **⭐ 필수: `termux-api` 패키지 설치** — `pkg install termux-api`를 Termux에서 실행해야 termux-battery-status 등 CLI 도구가 설치됨
- MCP 서버는 `phone-mcp.sh` wrapper로 실행해야 PATH에 Termux 바이너리가 포함됨
- Termux:API 안드로이드 앱 (APK)은 F-Droid 또는 GitHub Releases에서 별도 설치 필요

## 참고

- UI 화면 클릭(tap_screen)은 이 서버에서 지원 안 함
- 화면 자동화 필요 시 xlisp/termux-mcp-server 필요 (ADB 권한 요구)
- 루팅 금지 조건으로 인해 xlisp 계열은 설치 보류

## Domain vs Codomain — 폰 통제 경계선 분석

> 분석일: 2026-07-24 | 근거: 실제 도구 목록 + Android SELinux 권한 모델

### Domain ✅ (가능 — Termux:API가 공식 허용)
```
백그라운드 API 통제 (18개 도구)

📡 Read-only 센서
  • 배터리(잔량/온도)  • WiFi 정보
  • GPS 위치            • 디바이스 정보
  • 볼륨 상태

📨 메시징
  • SMS 발송/수신함 조회  • 연락처 목록
  • 통화 기록 조회         • 전화 걸기

🛠️ 단순 시스템 액션
  • 플래시 ON/OFF     • 진동 울리기
  • 볼륨 조절          • 알림 표시
  • 클립보드 읽기/쓰기  • 사진 촬영 / 음성 녹음
  • 셸 명령 (필터링됨)
```

### Codomain ❌ (절대 불가능 — OS가 차단)
```
GUI 조작 = 완전히 닫힘 (0%)

✗ 화면 터치 주입 (input tap)
✗ 앱 내부 탐색/조작
✗ 스크린샷 획득 + 분석 → 행동
✗ 시스템 설정 변경

원인: Android SELinux + 권한 모델
→ input tap = root/ADB only
→ root = 삼성페이/뱅킹앱 보안 깨짐
```

### 경계선의 본질

```
백그라운드 API (Termux:API)
    ─── 완전 통제 가능 ───
    SMS · 센서 · 클립보드 · 알림 · 촬영
    ↑ 앱 수준에서 OS가 공개한 API
    ↑ 뱅킹앱과 충돌 없음

        ⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
            ▲ 이 선은 절대 못 넘음 ▲
        ⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

GUI 조작 (터치 주입)
    ─── 완전히 닫힘 ───
    tap_screen · swipe · 앱 내 탐색
    ↑ root 또는 ADB 필요
    ↑ 또는 Accessibility Service (앱 제작 필요)
    ↑ 뱅킹앱 안전과 공존 불가 (root)
```

### 유일한 합법 경로: Accessibility Service

| 항목 | 현재(root/ADB) | Accessibility Service |
|------|---------------|---------------------|
| 삼성페이 안전 | ❌ (root) | ✅ (이론상) |
| tap/swipe 가능 | ✅ (ADB) | ✅ |
| 별도 APK 필요 | ❌ | ✅ (앱 제작 필요) |
| 공사 규모 | 0줄 | 수천 줄 + 플레이스토어 배포 |
| 지금 단계 적합성 | ❌ (루팅=금지) | ❌ (오버엔지니어링) |

### 현재 결론

> **지금 폰 = 완벽한 "센서+메신저 노드"**
> 백그라운드 API 통제는 거의 100% 열렸고,
> GUI 화면 조작은 0%로 완전히 닫혀 있다.
> GUI 통제가 진짜 필요해지면 그때 Accessibility Service 트랙 별도 검토.
