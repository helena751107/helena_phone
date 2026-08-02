# 백서: Grok으로 제품 투어 영상 만들기

> **S21 Phone · Helena Director / Perfect Ship**  
> 버전: 1.0 · 2026-08-02 · 작성: _Grok  
> 대상: Boss · 설치자 · “구독하면 뭐가 달라지나” 묻는 사람

---

## 0. 한 장 요약

```
URL 하나 (또는 시나리오 JSON)
        │
        ▼
┌───────────────────────────────────────┐
│  Grok 구독 = 손·눈 (에이전트)          │
│  perfect_ship = 카메라·편집실 (로컬)   │
└───────────────────────────────────────┘
        │
        ├─ Scout (페이지 구조)
        ├─ 연출 5막 (directing)
        ├─ TTS-first 나레이션
        ├─ Playwright 촬영 + 커서·줌
        ├─ FFmpeg 합성
        ├─ Vision QA + process 사다리
        ▼
     mp4 SHIP → 텔레그램 / YouTube
```

| 오해 | 진실 |
|------|------|
| “Grok 서버가 영상을 렌더한다” | **아님.** 렌더는 폰(로컬) Playwright + ffmpeg |
| “Grok 없으면 영상 자체가 안 된다” | **V1(PPT)은 된다.** Grok은 **V2 품질 루프·파이프 유지** |
| “한 번에 시네마틱 런칭 필름” | **아님.** 그건 V3 ComfyUI. Grok 파이프는 **제품 투어 A−** |

---

## 1. 영상은 3트랙이다

헌법의 돌봄/소망 **투트랙**과 별개. **품질·비용 3단.**

| 트랙 | 이름 | 도구 | 품질 | 비용 |
|------|------|------|------|------|
| **V1** | PPT·리포트 | DeepSeek + Edge TTS + 단순 Playwright | 개발일지·내부용 | ~0원 |
| **V2** | 제품 투어 | **Grok + Director / perfect_ship** | 커서·줌·게이트 | Grok 구독 |
| **V3** | 프로 마감 | ComfyUI + PC GPU / RunPod | 시네마틱 최종본 | GPU·종량제 |

**이 백서의 범위 = V2.**  
“Grok 써서 영상 만드는 프로세스”의 정본.

상세: `_notebook/58-video-three-tracks_Grok.md`

---

## 2. Grok이 하는 일 / 안 하는 일

### 2.1 Grok이 하는 일 (손·눈)

| 역할 | 내용 |
|------|------|
| 디자이너·시공 | 파이프 설계, 버그 패치, 연출 JSON, 오버레이 |
| 비전 검수 | 프레임 보고 “커서가 메트릭에 있다” 같은 **사람급 지적** |
| 프로세스 고정 | perfect_ship 사다리·정책·remediation 문서화 |
| 커뮤니티 리서치 | recast / Purple Owl 등과 비교해 바 맞추기 |

### 2.2 로컬이 하는 일 (카메라·편집실)

| 역할 | 도구 |
|------|------|
| 페이지 조작·녹화 | Playwright (Chromium) |
| 나레이션 | edge-tts (또는 OPENAI_API_KEY 시 tts-1-hd) |
| 합성·배속·자막 | ffmpeg |
| 픽셀 게이트 | vision_qa.py (로컬 휴리스틱) |
| 결정론 거부 | enforce.py · perfect_ship.py |

### 2.3 한 줄

> **Grok = 파이프를 깎는 사람. perfect_ship = 파이프가 찍는 기계.**  
> 구독료는 “기계 가동비”가 아니라 “깎는 사람 + 비전 루프”에 가깝다.

---

## 3. 프로세스 (고정 순서)

**마음대로 순서를 바꾸지 않는다.**  
실패하면 remediation 키만 고치고 **같은 사다리를 다시** 탄다.

### 3.1 유일한 진입점

```bash
cd ~/work/helena-programming/director   # 또는 워크스페이스 경로

python3 perfect_ship.py \
  --scenario scenarios/helena_phone.json \
  --out out/helena_phone.mp4 \
  --format shorts_1080 \
  --subs \
  --tts auto
```

| 플래그 | 의미 |
|--------|------|
| `--scenario` | 대본(대사·클릭·카메라). 없으면 `--url`로 Scout 생성 |
| `--format shorts_1080` | 1080×1920 (기본 A-bar 숏츠) |
| `--subs` | SRT 번인 + `.srt` 파일 |
| `--tts auto` | OpenAI 키 있으면 고품질 TTS, 없으면 edge+humanize |

### 3.2 사다리 L0–L9

| Stage | 이름 | 하는 일 | 실패 exit |
|-------|------|---------|-----------|
| L0 | Scout | URL 페이지 구조·인터랙티브 파악 | 3 |
| L1 | Directing | 5막 연출·정책 스탬프 | 3 |
| L2 | Voice | **TTS 먼저** · 길이 측정 · multi-click pad | 3 |
| L3 | Shoot | 5막 연주 · 커서 락 · auto-zoom · 전체 클릭 | 4 |
| L4 | Proof | 클릭 전후 PNG gold/teal | 4 |
| L5 | Edit | 리드 블랙 트림 · VO 길면 freeze · 영상 길면 배속 압축 | 2 |
| L6 | Quality | G1–G7 | 2 |
| L7 | Vision QA | 점수 ≥100 · 검정/링 hard gate | 5 |
| L8 | Process | perfect_ship 전체 검증 | 6 |
| L9 | **SHIP** | TG/배포 **허용** | 0 |

정의 파일: `director/process/perfect_ship_v1.json`  
구현: `director/perfect_ship.py`

### 3.3 SHIP 없이 텔레그램에 영상 올리지 말 것

```
SHIP 배지 없음 → 전송 금지
*.process.json 의 ship: true 확인
```

---

## 4. 한 비트(장면) 안에서 일어나는 일

연출 성경: `directing/product_tour_v1.json`

매 비트 = **5막** (VO 길이가 시계):

| 막 | 비율 감각 | 화면 |
|----|-----------|------|
| establish | ~12% | 카메라 도착 · chip/STEP · 빛 ON |
| focus | ~15% | 커서 → primary · 줌 인 |
| act | ~22% | demoClick · 실클릭 · proof |
| hold | ~43% | 결과 유지 · 나레이션 |
| release | ~8% | 빛 끄기 · 다음 준비 |

**금지 (anti-pattern):**

- 커서가 FILES/COMMITS 메트릭에 주차  
- 클릭 숫자만 통과하고 링/리플 없음  
- 시간 없다고 2번째 클릭 스킵  
- 클릭 직후 바로 다음 장면 (결과 안 보임)  
- 세션마다 다른 순서로 품질 땜빵  

---

## 5. 산출물 목록

한 번 SHIP 하면 보통 옆에 붙는다:

```
out/NAME.mp4              ← 본편
out/NAME.actions.json     ← 클릭·phase·zoom 로그
out/NAME.vision_qa.json   ← 비전 점수
out/NAME.process.json     ← 사다리 PASS/FAIL
out/NAME.process.md       ← 사람이 읽는 리포트
out/NAME.quality.json
out/NAME.srt              ← 자막 (옵션)
out/NAME.audit.json
```

실패 시: `process.md` 의 **Remediation** 만 보고 해당 코드 고친 뒤  
`perfect_ship.py` **재실행**. 새 임시 스크립트 만들지 말 것.

---

## 6. 실제 명령 치트시트

### 6.1 기본 (helena_phone 랜딩 투어)

```bash
cd helena-programming/director
python3 perfect_ship.py \
  --scenario scenarios/helena_phone.json \
  --out out/helena_phone.mp4 \
  --format shorts_1080 \
  --subs
```

### 6.2 URL만 주고 Scout부터

```bash
python3 perfect_ship.py \
  --url https://helena751107.github.io/helena_phone/ \
  --out out/demo.mp4 \
  --format shorts_1080
```

### 6.3 이미 찍힌 것만 재검증

```bash
python3 perfect_ship.py --verify-only \
  --scenario scenarios/helena_phone.json \
  --out out/helena_phone_pro_v7.mp4 \
  --work out/work_helena_phone
```

### 6.4 텔레그램 (SHIP 후)

```bash
# 텍스트 보고
bash ~/work/tg.sh '✅ Director SHIP — out/xxx.mp4'

# 영상 첨부
curl -s -X POST "https://api.telegram.org/bot$TG_TOKEN/sendVideo" \
  -F chat_id="$TG_CHAT" \
  -F video=@"out/xxx.mp4" \
  -F caption="🎬 Product Tour SHIP"
```

---

## 7. 파일 지도 (V2)

| 경로 | 역할 |
|------|------|
| `perfect_ship.py` | **유일한 진입점** |
| `process/perfect_ship_v1.json` | 사다리 · remediation |
| `run_director.py` | Scout→Shoot→Edit 연주 |
| `directing/product_tour_v1.json` | 5막 연출 |
| `policy/tutorial_v1.json` | ship 금지 조건 |
| `enforce.py` | 결정론 게이트 |
| `overlays.js` | 커서·링·autoZoom |
| `voice_engine.py` | TTS-first |
| `vision_qa.py` | 프레임 점수 |
| `subtitles.py` | SRT |
| `scenarios/*.json` | 대본 |

---

## 8. 커뮤니티에서의 위치 (과장 없이)

| 비교 | 평가 |
|------|------|
| Purple Owl / DIY 블로그 | 우리는 **게이트·사다리**가 더 두꺼움 |
| playwright-recast | 줌·ElevenLabs·패키징은 그쪽이 앞설 수 있음 |
| Screen Studio | **마케팅 시네마틱** — 우리 V2 목표가 아님 (V3) |

**정직한 라벨:**  
「폰에서 도는 **재현 가능한 제품 투어 자동화 (커뮤니티 A−, 프로세스 A)**」

---

## 9. 비용 감각

| 항목 | V2에서 |
|------|--------|
| Grok 구독 | 파이프 유지·비전 루프 (이미 쓰는 돈이면 추가 체감 적음) |
| edge-tts | 사실상 0 |
| OpenAI TTS | 키 있을 때만 종량 (옵션) |
| 폰 전기·시간 | 1편 렌더 수 분~십수 분 (해상도·비트 수) |

**팔 메시지 (Boss 감각):**  
구독을 강요하지 않는다.  
**0원이면 V1, 구독이면 V2, GPU 있으면 V3.**

---

## 10. 실패했을 때

1. `out/*.process.md` 연다  
2. ✗ 난 Stage 확인  
3. `remediation_ids` → `process/perfect_ship_v1.json` 의 remediation_map  
4. **그 코드만** 패치  
5. `perfect_ship.py` 다시  

예:

| ID | 증상 | 어디 손대나 |
|----|------|-------------|
| AP1 | 커서 메트릭 주차 | overlays.js cursor lock |
| AP3 | 2클릭 드롭 | multi_click_pad / shoot |
| AP7 | 줌 없음 | autoZoom |
| AP8 | TTS-first 아님 | voice_engine |

---

## 11. 관련 문서

| 문서 | 내용 |
|------|------|
| `58-video-three-tracks_Grok.md` | V1·V2·V3 정본 |
| `56-director-perfect-ship-process_Grok.md` | 사다리 코드화 |
| `57-director-community-a-bar_Grok.md` | 줌·1080·커뮤니티 바 |
| `33-hybrid-image-video-whitepaper.md` | Grok Imagine 드래프트 ↔ Comfy 마감 (이미지·V3 감각) |
| `helena-programming/director/README.md` | 엔지니어용 진입 |

---

## 12. 결론

1. **Grok 영상 = V2 제품 투어 파이프**이지, 서버 렌더 서비스가 아니다.  
2. **프로세스는 perfect_ship 한 줄**로 고정한다. 즉흥 금지.  
3. **SHIP 게이트를 통과한 뒤에만** 텔레그램·배포.  
4. 더 올리고 싶으면 V3(ComfyUI)로 넘긴다. V2에서 시네마틱을 강요하지 않는다.

---

## 서명

- 백서 작성: **_Grok** (2026-08-02)  
- 근거 파이프: helena-programming/director · pro_v7 SHIP 이력  
- Boss 검수: _대기_

---

*EOF · S21 Phone · 코드는 선물 · 판단력만 희소*
