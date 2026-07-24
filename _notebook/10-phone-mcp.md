# phone-mcp-server — 핸드폰 통제 MCP

> 순수 Termux:API 기반. 루트/ADB/Shizuku 불필요.
> 설치일: 2026-07-24

## 상태

| 항목 | 값 |
|------|-----|
| 서버 | `http://localhost:3456/mcp` |
| 상태 | ✅ 정상 |
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

## 참고

- UI 화면 클릭(tap_screen)은 이 서버에서 지원 안 함
- 화면 자동화 필요 시 xlisp/termux-mcp-server 필요 (ADB 권한 요구)
- 루팅 금지 조건으로 인해 xlisp 계열은 설치 보류
