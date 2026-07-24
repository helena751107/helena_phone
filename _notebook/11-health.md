# S21 Phone 건강 검진 시스템

> 역할: 주기적인 하드웨어/소프트웨어 헬스체크
> 최초 구축: 2026-07-24
> 스크립트: `~/work/phone-health.sh`

## 개요

phone-health.sh는 S21 Phone의 모든 하드웨어와 소프트웨어 상태를 진단하는 자동화 스크립트다.
MCP 서버(phone-mcp-server)에 의존하지 않고 Termux:API를 직접 호출하여 각 센서와 기능을 검증한다.

## 검사 항목 (10개 카테고리)

| # | 카테고리 | 검사 내용 |
|---|---------|----------|
| 1 | 시스템 기본 | Kernel, hostname, MCP 서버 상태, 디스크, GitHub Pages |
| 2 | 전원/배터리 | 잔량(%), 온도(°C), 충전상태, 건강도, 전압, 전류 |
| 3 | WiFi/네트워크 | SSID, IP, RSSI(dBm), 링크속도, 외부 연결성 |
| 4 | 하드웨어 센서 | Flashlight, Vibrate, Volume, Audio info, Sensor list |
| 5 | 위치/GPS | GPS fix (GPS + Network fallback) |
| 6 | 카메라/미디어 | Camera info, Microphone, TTS |
| 7 | 클립보드 | Write + Read 검증 |
| 8 | 커뮤니케이션 | SMS, Contacts, Call log, Telephony, Cellular, Notification |
| 9 | 네트워크 서비스 | GitHub Pages 5개, Discord widget, Telegram API |
| 10 | 핵심 직접 검증 | termux-battery-status, device_info, camera_info 재확인 |

## 사용법

```bash
# 기본 검진 (27개 항목, 비파괴)
bash ~/work/phone-health.sh

# 전체 검진 (사진 촬영 포함)
bash ~/work/phone-health.sh --full

# 검진 + 텔레그램 보고
bash ~/work/phone-health.sh --telegram
```

## 보고서 보관

모든 검진 결과는 타임스탬프 JSON으로 `_notebook/health/`에 저장된다.

```
_notebook/health/
├── 2026-07-24_1212.json    ← 첫 검진
├── 2026-07-24_1217.json    ← 두 번째
├── 2026-07-24_1223.json    ← 현재 최신
└── ...
```

## JSON 보고서 구조

```json
{
  "timestamp": "2026-07-24 12:23:10 UTC",
  "grade": "A",
  "battery": {
    "percentage": 63,
    "temperature": 37.2,
    "status": "CHARGING",
    "health": "GOOD",
    "plugged": "PLUGGED_AC"
  },
  "wifi": {
    "ssid": "U+NetFA1B",
    "ip": "192.168.219.131",
    "rssi": -43,
    "link_speed": 130
  },
  "results": {
    "pass": 27, "warn": 3, "fail": 0,
    "total": 31
  },
  "mcp": {
    "port": 3456,
    "http_status": 200,
    "tools": 18
  }
}
```

## 종합 등급 기준

| 등급 | 조건 | 의미 |
|------|------|------|
| **S** | fail=0, warn≤2 | 모든 항목 완벽 정상 |
| **A** | fail=0 | 경고 있으나 핵심 기능 정상 |
| **B** | fail≤3 | 소수 기능 불량 — 점검 권장 |
| **C** | fail>3 | 다수 기능 불량 — 즉시 점검 |

## 시계열 비교

같은 디렉토리의 JSON 파일들을 비교하여 시점별 건강 추이를 볼 수 있다:

```bash
# 최근 5개 요약
ls -t _notebook/health/*.json | head -5 | while read f; do
  echo "$(basename $f .json): $(sed -n 's/.*"grade":"\{0,1\}\([^",]*\)"\{0,1\}.*/\1/p' $f)"
done
```

## 경고 신호 (자동 감지)

| 조건 | 조치 |
|------|------|
| 배터리 < 15% | 충전 필요 |
| 온도 > 45°C | 사용 중지, 냉각 |
| RSSI < -80dBm | WiFi 근처로 이동 |
| MCP HTTP ≠ 200 | 서버 재시작: `bash ~/work/phone-mcp.sh --port 3456` |
| GPS fail 지속 | 위치 권한 확인, 실외에서 재시도 |

## 설계 원칙

1. **MCP 불필요** — MCP 서버는 단일 session만 허용하므로(cc 사용 중이면 curl session 불가), 모든 검사는 Termux:API를 직접 호출
2. **비파괴** — SMS 발송, 전화걸기, 파일삭제 등 변경을 가하는 도구는 테스트하지 않음
3. **타임스탬프 보관** — 모든 검진은 JSON 파일로 남겨 시계열 비교 가능
4. **텔레그램 보고** — `--telegram` 플래그로 채팅방에 자동 보고
