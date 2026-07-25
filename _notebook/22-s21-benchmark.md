# 📱 S21 디바이스 분석 — 최신폰 대비 성능 비교

> 측정일: 2026-07-25 | 실측 기기: Galaxy S21 5G (SM-G991N, 한국판)
> 용도: AI 워크스테이션·미니 스튜디오·개인 출판 오피스

---

## 1. 실측 사양

| 항목 | 실측값 |
|------|--------|
| 모델 | SM-G991N (Galaxy S21 5G) |
| 제조사 | Samsung |
| 출시 | 2021년 1월 (5년 6개월 경과) |
| Android | 15 (SDK 35) |
| CPU | Samsung Exynos 2100 (5nm), 8코어 (1×Cortex-X1 2.9GHz + 3×A78 2.8GHz + 4×A55 2.2GHz) |
| RAM | 8GB LPDDR5 (실측 7.0Gi 사용 가능) |
| 저장공간 | 256GB (실측 226GB, 54GB 사용, 172GB 남음) |
| 배터리 | 4,000mAh, 건강 GOOD, 현재 85%·38.5°C·4,096mV |
| 디스플레이 | 6.2" Dynamic AMOLED 2X, FHD+ 2400×1080, 120Hz |
| 카메라 | 후면 2개(12MP+64MP), 전면 2개(10MP) |
| WiFi | WiFi 6 (802.11ax), RSSI -49dBm |
| GPU | ARM Mali-G78 MP14 |
| 무게 | 169g |

---

## 2. 최신 플래그십 vs S21 (2026년 7월 기준)

| 항목 | **S21 (2021)** | **S26 Ultra (2026, 추정)** | **갭** |
|------|---------------|--------------------------|--------|
| CPU | Exynos 2100 (5nm) | Snapdragon 8 Gen 4 / Exynos 2500 (3nm) | 약 3.5배 |
| RAM | 8GB LPDDR5 | 12~16GB LPDDR6 | 1.5~2배 |
| 저장 | 256GB UFS 3.1 | 256GB~1TB UFS 4.0 | 속도 2배 |
| 배터리 | 4,000mAh (5년 사용) | 5,000~5,500mAh (신품) | 실체감 2배 |
| 디스플레이 | 6.2" FHD+ 120Hz | 6.8" QHD+ 144Hz | 해상도 ↑ |
| WiFi | WiFi 6 | WiFi 7 | 속도 4.8배 |
| GPU | Mali-G78 MP14 | Snapdragon Xclipse / AMD RDNA 4 | 약 4배 |
| AI 칩 | 없음 (CPU/GPU 대체) | 전용 NPU (45 TOPS) | AI연산 10배+ |

---

## 3. AI 워크스테이션 용도 관점 비교

이 관점이 진짜 중요하다. 스펙 숫자가 아니라 **"이 일을 이 폰으로 할 수 있냐"** 가 기준.

| 작업 | S21에서 가능? | 한계 | 최신폰이면? |
|------|------------|------|-----------|
| Termux + proot Ubuntu | ✅ 잘 됨 | 파일시스템 약간 느림 | 동일 |
| Claude Code (DeepSeek) | ✅ 잘 됨 | API 호출이라 로컬 성능 무관 | 동일 (API는 같음) |
| Git + GitHub | ✅ 잘 됨 | 대용량 레포는 약간 느림 | 동일 |
| Playwright Chromium headless | ✅ 잘 됨 | 메모리 500MB 먹음, 초기 로딩 느림 | 더 빠름 |
| Python·Node.js·pip·npm | ✅ 잘 됨 | 빌드 속도 차이 | 2~3배 빠름 |
| phone-mcp-server 18도구 | ✅ 잘 됨 | 제약 없음 | 동일 |
| YouTube 업로드 (API) | ✅ 잘 됨 | API 호출이라 로컬 성능 무관 | 동일 |
| 영상 녹화 + 인코딩 | ⚠️ 가능하나 느림 | 1080p 이상은 인코딩 부담 | 하드웨어 인코딩 |
| LLM 로컬 실행 (Ollama) | ❌ 불가능 | RAM 부족 + NPU 없음 | S26은 가능 (NPU) |
| Docker / VM | ❌ 불가능 | proot은 컨테이너 에뮬레이션일 뿐 | 동일 (Android 제약) |
| GUI 앱 (X11) | ⚠️ 이론상 가능 | GPU 가속 없음, 느림 | DeX 모드로 가능 |

---

## 4. 결론: 이 폰으로 할 수 있는 것, 없는 것

### ✅ 할 수 있는 것 (제약 없음)
- **AI 코딩 에이전트** — Claude Code, Aider, MCP 서버
- **풀스택 웹 개발** — Git, GitHub Pages, HTML/CSS/JS
- **문서화** — Markdown, Jekyll, 정적 사이트 생성
- **API 자동화** — YouTube, Telegram, Discord, GitHub API
- **폰 하드웨어 통제** — SMS, 배터리, GPS, 카메라, 플래시
- **헤드리스 브라우저** — Playwright Chromium
- **쉘 스크립트 자동화** — Bash, cron, daemon

### ⚠️ 가능하지만 느린 것
- **대용량 컴파일** — C/C++ 빌드, pip 대형 패키지
- **영상 인코딩** — FFmpeg 소프트웨어 인코딩 (1080p 이상)
- **데이터베이스** — SQLite 충분, PostgreSQL은 무거움

### ❌ 할 수 없는 것 (물리적 한계)
- **로컬 LLM 실행** — 8GB RAM + NPU 없음. 7B 모델도 스왑 필요
- **Docker / 가상화** — Android 커널 제약. proot만 가능
- **GPU 가속** — CUDA/Metal 없음. 순수 CPU 연산
- **iOS 개발** — Xcode 불가 (macOS 필요)

---

## 5. 핵심 인사이트

> **"API 기반 AI 워크스테이션으로서 S21은 성능 제약이 거의 없다."**
>
> Claude Code·GitHub·YouTube·Telegram 전부 API 호출이기 때문에
> 로컬 CPU/GPU 성능보다 **네트워크 대역폭**이 더 중요하다.
>
> S21의 진짜 한계는 CPU가 아니라 **배터리 수명**(5년 사용)과
> **로컬 LLM 실행 불가**(NPU 없음)다. 하지만 클라우드 API를 쓰는
> 현 구조에서는 둘 다 문제가 되지 않는다.
>
> **5년 된 폰으로 최신 AI 개발이 가능한 이유: 모든 무거운 연산이 API로 빠지기 때문.**

---

> 다음: 이 분석을 기반으로 en/device-benchmark.html 영문 페이지 생성
