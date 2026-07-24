# 5단계: 최적화 — 오래된 폰 최대한 오래 쓰기

> 갤럭시 S21을 24/7 서버로 돌리기 위한 꿀팁

## 배터리 관리

- **충전 제한:** 80%까지만 충전 (Settings > Battery > Protect battery)
- **발열 관리:** 폰을 세워서 공기 순환 (뒤집어 놓거나 거치대)
- **WiFi 고정:** 절전 모드에서 WiFi 끊김 방지
- **화면 꺼짐:** SSH로 접속 중이면 화면 꺼도 작업 계속됨

## proot 성능 팁

- 메모리 제한: 기본적으로 proot은 호스트 메모리를 그대로 씀 (S21 기준 8GB 충분)
- CPU: big.LITTLE 코어 할당은 커널이 알아서 함
- 실행 시간: 배터리 방전 막으려면 12시간 이상 작업은 AC 충전 권장

## 저장공간

| 대상 | 명령어 | 예상 확보 |
|------|--------|----------|
| npm cache | `npm cache clean --force` | ~500MB |
| apt cache | `apt clean` | ~300MB |
| Termux cache | `pkg clean` | ~200MB |
| Docker (안 씀) | (proot에선 도커 불가) | N/A |

## 문서

| # | 내용 | 바로가기 |
|---|------|---------|
| 5.1 | 배터리 최적화 | [battery-saving.md](./battery-saving.md) |
| 5.2 | 성능 튜닝 | [performance.md](./performance.md) |
| 5.3 | 저장공간 관리 | [storage.md](./storage.md) |
