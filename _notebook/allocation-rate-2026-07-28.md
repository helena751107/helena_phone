# Allocation Rate — 2026-07-28

> S21 Phone 전체 자산 배분율 + 저장소 메커니즘 분석  
> 작성: _Claude (2026-07-28)

---

## 1. 폰 상태

| 항목 | 값 |
|------|-----|
| 모델 | Samsung Galaxy S21 (aarch64) |
| OS | Android + Termux + proot Ubuntu 26.04 |
| 배터리 | 60%, 34.3°C, DISCHARGING |
| 디스크 | 169GB free / 225G total (75% 사용가능) |
| 건강등급 | **B** — WiFi 약함, 마이크 권한, 클립보드 |
| GitHub Pages | 6/6 정상 (HTTP 200) |
| parksy-audio | private, 986MB, 접근 가능 |

---

## 2. 문서 자산

| 위치 | 파일 수 | 용량 | 유형 |
|------|---------|------|------|
| `_notebook/` | 69 | 1.7MB | 업무수첩 (Markdown 원본) |
| `notebook/` | 62 | 992KB | 웹진 (HTML 변환본) |
| `_textbook/` | - | 32KB | 완결판 교재 |
| 합계 | ~131 | ~2.7MB | — |

### 파일 타입 분포

| 타입 | 개수 | 비율 |
|------|------|------|
| HTML | 115 | 37% |
| Markdown | 106 | 34% |
| PNG (아이콘·스크린샷) | 30 | 10% |
| Python | 23 | 7% |
| JSON (설정·맵) | 18 | 6% |
| Shell | 17 | 5% |
| JS (Node) | 10 | 3% |

**문서가 전체의 71%** — 코딩보다 문서화·기록 비중이 높다.

---

## 3. 저장소 메커니즘

```
helena_phone/ (메인 레포)
├── 📁 _notebook/    1.7MB  업무수첩 원본 (69 md)
├── 📁 notebook/     992KB  웹진 HTML (62개)
├── 📁 assets/       5.1MB  정적 리소스
├── 📁 scripts/      263KB  자동화 스크립트
├── 📁 mcp-servers/  156KB  phone-mcp-server (18도구)
├── 📁 care/         64KB   트랙1 돌봄 데몬
├── 📁 configs/      68KB   설정·템플릿
├── 📁 g/            64KB   install.sh
├── 📁 icons/        388KB  PWA 아이콘
├── 📁 naver/        115KB  네이버 파이프
├── 📁 tistory-naver/84KB   티스토리·네이버
├── 📁 ecosystem/    85KB   생태계 맵
├── 📁 google-api/   64KB   Google OAuth
├── 📁 01~05/        124KB  GUIDE.md 챕터
├── 📁 broadcast/    36KB   방송
├── 📁 network/      36KB   네트워크
├── 📁 phone-control/36KB   폰 제어
├── 📁 optimization/ 36KB   최적화
├── 📁 foundation/   44KB   기초
└── 📁 helana_log/   1.3MB  로그 서브모듈

helena-piano/ (별도 레포)
├── 📁 bgm/          BGM Studio (MIDI + 렌더 파이프)
├── 📁 fridge/       parksy-audio 전수조사
├── 📁 pages/        문서 브릿지
├── 📁 icons/        PWA 아이콘
├── 📁 youtube/      YT 자동화 스크립트
└── 📄 index.html    55KB  메인 웹진

dtslib1979/parksy-audio/ (외부, 콜라보 접근)
├── 986MB, 39개 YT 영상 실적
├── steal.py (YouTube→MIDI)
├── pipeline/ (작곡·편곡·인간화)
├── local-agent/ (S21 TG 봇)
└── docs/ (27종 건축 문서)
```

---

## 4. 할당률 (Allocation Rate)

### 저장공간 할당

| 영역 | 용량 | 비율 | 설명 |
|------|------|------|------|
| 🎨 **문서·웹진** | 2.1MB | 7% | md+html, 업무수첩+웹진 |
| 🎵 **오디오·BGM** | 18KB | 0% | parksy-audio는 외부, 헬레나 내엔 없음 |
| 🖼️ **에셋·아이콘** | 5.5MB | 18% | PNG·SVG·정적 리소스 |
| ⚙️ **스크립트·자동화** | 5.3MB | 18% | Python·Shell·MCP·CI |
| 📦 **외부 의존성** | 18MB | 60% | node_modules |
| 합계 (순수) | ~13MB | — | node_modules 제외 |

### 노력·집중도 할당

| 영역 | 집중도 | 증거 |
|------|--------|------|
| 📝 **기록·문서화** | ████████ 40% | 131개 md+html, 일지·수첩·웹진 |
| 🎬 **출판·방송** | ██████ 30% | YouTube·네이버·티스토리·랜딩 |
| 🔧 **인프라·자동화** | ████ 20% | MCP·CI·스크립트·TG 봇 |
| 🎵 **오디오·음원** | ██ 10% | parksy-audio (외부), BGM Studio (초기) |

### GitHub Pages 배분

| 페이지 | 상태 | 역할 |
|--------|------|------|
| `helena_phone` | 🟢 | 메인 허브 — 모든 것의 관문 |
| `helana_log` | 🟢 | 업무일지 — 시간축 기록 |
| `helana-faith` | 🟢 | 신앙사 — 가족·비교종교 |
| `helena-piano` | 🟢 | 피아노 스튜디오 — 웹진·BGM |
| `helena-psycare` | 🟢 | 심리 케어 |
| `parksy-audio` | 🔒 | 오디오 엔진 — 외부(private) |

---

## 5. 병목·제약

| 제약 | 영향 | 대응 |
|------|------|------|
| proot Ubuntu 휘발성 | 재설치 시 패키지 증발 | 복구 스크립트 (`bgm/scripts/render.sh`) |
| GitHub Actions 냉시동 | 첫 실행 5분+ | actions/cache@v4 (v6 검증) |
| Internet Archive 장애 | Salamander SF2 다운로드 불가 | MuseScore General 대체, IA 복구 대기 |
| 206MB SoundFont git 불가 | bgm/salamander.sf2 추적 불가 | .gitignore + CI 캐시 |
| S21 배터리 60% | 장시간 렌더링 제한 | GitHub Actions로 오프로드 |

---

## 6. 권장: 출판·방송 우선

**음원 렌더링은 기술적으로 증명됐지만, 콘텐츠가 먼저다.**

| 순서 | 액션 | 의존성 |
|------|------|--------|
| 1 | YouTube 채널 콘텐츠 기획 (@HelenaPark-e7c) | 없음 |
| 2 | 웹진에 실제 세션 로그 채우기 | 없음 |
| 3 | MIDI 라이브러리 구축 (Public Domain) | bitmidi·Mutopia |
| 4 | GitHub Actions BGM 자동화 실사용 | 3 완료 후 |
| 5 | Salamander SF2 입수 + 적용 | IA 복구 또는 수동 빌드 |
