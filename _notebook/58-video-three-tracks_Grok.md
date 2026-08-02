# 영상 3트랙 — PPT → Grok 파이프 → ComfyUI 프로 마감 (_Grok)

> 선언: Boss 2026-07-31 (§103) · 정리·현행화: 2026-08-02 (_Grok)  
> 헌법: 트랙1 돌봄 / 트랙2 소망 과 **별개**. 여기는 **영상 생산 품질·비용 3단**.  
> 관계: `33-hybrid-image-video-whitepaper.md` · `57-director-community-a-bar_Grok.md` · `56-director-perfect-ship-process_Grok.md`

---

## 1. 한 줄

```
돈이 없으면 PPT 수준
Grok 구독이면 제품 투어 파이프 (Director / perfect_ship)
PC + ComfyUI(GPU) 있으면 프로 마감
```

**2트랙이 아니다. 영상은 3트랙이다.**

---

## 2. 3트랙 표 (정본)

| 트랙 | 이름 | 엔진 | 품질 감각 | 비용 | 언제 쓰나 |
|------|------|------|-----------|------|-----------|
| **V1** | PPT·리포트 | Claude(DeepSeek) + Edge TTS + Playwright 단순 파이프 | 문서 영상화 · 개발일지 · “대충 보여주기” | **0원** (DeepSeek 등 기존) | 빠른 기록, 내부 공유 |
| **V2** | 제품 투어 · 튜토리얼 | **Grok 구독 + Director / `perfect_ship`** | 커서·줌·5막·게이트 · 커뮤니티 자동화 A− | **Grok 구독** (월 고정) | 랜딩 투어, TG 데모, 외부에 보여줄 “수준” |
| **V3** | 프로 마감 | **ComfyUI + 로컬 GPU(WSL) / RunPod** | 시네마틱 · AI VFX · 일관성 최종본 | GPU 있으면 0원 추가 / 없으면 종량제 | 출시 필름, 히어로 영상, 브랜딩 컷 |

Boss 원문 감각:

1. **그냥 PPT 수준**으로 만드는 거  
2. **Grok 구독**하면 이 파이프 안으로 들어와 수기·제품 영상을 조금 수준 있게  
3. **PC + ComfyUI** 돌리면 프로 마감  

---

## 3. 각 트랙 실물 (지금 레포)

### V1 — PPT 수준 (0원 쪽)

| 경로 | 역할 |
|------|------|
| `helena-programming/scripts/webpage_to_video.py` | 스크린샷 + TTS + 붙이기 |
| `make_video.py` · `record_demo.py` · `demo_director.py` | 초기 데모 파이프 (품질 게이트 약함) |

- 목표: **나오게 한다.**  
- 검수: 사람 눈 / 메트릭 최소.  
- Grok 구독 **필수는 아님.**

### V2 — Grok 파이프 (구독 시)

| 경로 | 역할 |
|------|------|
| `helena-programming/director/perfect_ship.py` | **유일한 진입점** |
| `process/perfect_ship_v1.json` | L0–L9 사다리 |
| `directing/product_tour_v1.json` | 5막 연출 |
| `overlays.js` · `vision_qa.py` · `voice_engine.py` | 커서·줌·TTS-first |

```bash
cd helena-programming/director
python3 perfect_ship.py \
  --scenario scenarios/helena_phone.json \
  --out out/helena_phone.mp4 \
  --format shorts_1080 \
  --subs
```

- 목표: **재현 가능한 제품 투어.**  
- Grok 역할: 파이프 **설계·패치·비전 검수 루프** (에이전트).  
- 렌더 본체: 폰 로컬 Playwright + ffmpeg + edge-tts (Grok 서버 ≠ 영상 인코더).  
- 구독이 주는 것: **비전 있는 에이전트로 품질 루프를 돌릴 수 있음** + 이 파이프를 유지·확장하는 손.

### V3 — ComfyUI 프로 마감

| 경로 / 인프라 | 역할 |
|---------------|------|
| ComfyUI 워크플로우 | 오프닝·엔딩·AI 모션·스타일 고정 |
| 집 PC WSL GPU 또는 RunPod | 실행 |
| (예비) parksy-image / papyrus runpod | 과거 실험 자산 |

- 목표: **출시·브랜딩 최종본.**  
- V2 mp4를 재료로 넘기거나, 별도 시퀀스 생성 후 concat.  
- S21 → Tailscale → WSL / RunPod API 로 방아쇠 (설계만 있음, 상시 ON 아님).

---

## 4. 돈·진입 조건

```
V1  ──(항상)──►  0원에 가깝게 굴림
         │
         │  Grok 구독 있음
         ▼
V2  ──(구독)──►  Director / perfect_ship 로 “수준 있는” 투어
         │
         │  PC GPU 또는 RunPod 있음
         ▼
V3  ──(GPU)──►  ComfyUI 프로 마감
```

| 사용자 | 권장 트랙 | 한 달 감각 |
|--------|-----------|------------|
| 구독 없음 · 폰만 | **V1** | 사실상 0 |
| Grok 구독 · 폰 | **V1 + V2** | 구독료 (이미 쓰는 돈) |
| 구독 + PC GPU | **V1 + V2 + V3** | 구독 + (로컬이면 전기) |
| 구독 + GPU 없음 · 마감만 | **V2 + V3(RunPod)** | 구독 + 그날 종량 |

**원칙 (Boss):**  
팔 건 “구독 강요”가 아니라 **0원으로도 V1이 되고, 구독하면 V2, GPU 있으면 V3** 라는 층이다.

---

## 5. 헷갈리면 안 되는 것

| 구분 | 내용 |
|------|------|
| 헌법 투트랙 | **돌봄(트랙1) / 소망(트랙2)** — 사람·목적 |
| 영상 3트랙 | **V1 PPT / V2 Grok 파이프 / V3 Comfy** — 품질·비용 |
| 하이브리드 백서(33) | 이미지·영상 **드래프트(Grok Imagine) vs 마감(Comfy)** — V2 안의 “생성” 감각과 V3 연결 |
| Grok 서버 | V2 **에이전트 손**. 렌더는 로컬. “Grok이 영상을 서버에서 인코딩”이 아님 |

---

## 6. 운영 규칙

1. **V1으로  sufficiency 되면 V2를 돌리지 않는다.** (시간 낭비)  
2. **V2 SHIP 없이 V3에 넣지 않는다.** (재료가 가짜면 마감도 가짜)  
3. **V3는 방향 확정 후에만.** (33 백서·헌법 스캐폴드 원칙과 동일)  
4. 에이전트 영상 작업 기본 진입점:  
   - 싸게·빠르게 → V1 스크립트  
   - 보여줄 품질 → `perfect_ship.py` (V2)  
   - 출시 컷 → V3 핸드오프 체크리스트 (추후 문서화)

---

## 7. 현재 상태 (2026-08-02)

| 트랙 | 상태 |
|------|------|
| V1 | ✅ 스크립트 존재 · 품질 제각각 |
| V2 | ✅ Director + perfect_ship · pro_v7 SHIP 이력 |
| V3 | ⏳ 인프라·워크플로 설계·dtslib 자산 있음 · 상시 가동 전 |

---

## 8. 서명

- 구조 선언: Boss 2026-07-31  
- 업무 수첩 정본 정리: **_Grok** 2026-08-02  
- Boss 검수: _대기_
