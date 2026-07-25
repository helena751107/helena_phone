# 4단계: 폰 원격 제어 — PC에서 폰 조종

> Claude Code가 폰의 배터리를 읽고, 플래시를 켜고, 문자를 보낸다

## 시스템 구조

```
Claude Code (AI 에이전트)
    ↓ MCP 프로토콜 (Streamable HTTP)
phone-mcp-server (localhost:3456)
    ↓ termux-* 명령어
Termux:API (80여개 하드웨어 API)
    ↓
📱 실제 폰 하드웨어
```

## 가능한 것 (Domain ✅)

```
📡 센서:    배터리, WiFi, GPS, 볼륨, 디바이스 정보
📨 통신:    SMS 발송/수신, 연락처, 통화기록, 전화걸기
🛠️ 제어:   플래시, 진동, 볼륨조절, 알림, 클립보드
📸 미디어:  사진촬영, 음성녹음
```

## 불가능한 것 (Codomain ❌)

```
✗ 화면 터치 주입 (input tap) — Android OS가 원천 차단
✗ 앱 내부 탐색/조작
✗ 시스템 설정 변경
```

> **이유:** `input tap`은 root/ADB 권한이 필요함. 루팅하면 삼성페이/뱅킹앱 깨짐.
> **대안:** Accessibility Service (별도 APK 제작 필요, 지금 단계에선 오버)

## 문서

| # | 내용 | 바로가기 |
|---|------|---------|
| 4.1 | phone-mcp-server 설치/운영 | [phone-mcp.md](./phone-mcp.md) |
| 4.2 | 건강 검진 시스템 | [health-check.md](./health-check.md) |
