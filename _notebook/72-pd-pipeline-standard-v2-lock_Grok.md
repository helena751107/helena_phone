# 72 · PD 영상 표준 v2 확정 (LOCK) (_Grok)

> Boss 2026-08-06: 「여기로 버전 확정. 이게 표준. 매번 동일하게 작업되게 저장.」

---

## 정본

| 항목 | 값 |
|------|-----|
| **CURRENT** | `configs/video_pd_pipeline_CURRENT.json` → **v2** |
| **스펙** | `configs/video_pd_pipeline_v2.json` |
| **엔트리** | `bash scripts/produce_pd.sh [ep] [url]` |
| **v1** | `superseded` — 신규 작업 금지 |

---

## 매번 같은가? → **예 (엔트리 1개 + 상수 핀)**

한 줄만 치면 동일 파이프:

```bash
bash scripts/produce_pd.sh pd_intro
# 또는
BGM_VOLUME=0.025 TTS_ENGINE=grok bash scripts/produce_pd.sh <ep> <url>
```

### 고정 상수 (세션마다 바꾸지 말 것)

| 상수 | 값 | 어디에 박혀 있나 |
|------|-----|------------------|
| BGM 볼륨 | **0.025** | `produce_pd.sh` · `_render_video.py` · `_pd_assemble.py` · v2 JSON |
| 성우 | **grok / ara** | `produce_pd.sh` 기본값 |
| 해상도 | 1080×1920 yuv420p High | `_render_video` · assemble |
| 조립 | **concat demuxer** (xfade 오프셋 금지) | `_render_video.py` v2 |
| 폰트 | Noto Sans/Serif **CJK KR** | `_render_video.py` |
| BGM 소스 | Boss 렌더 `bgm_shorts` → helena-piano | 우선순위 리스트 |
| 브릿지 | 앞·뒤 소수만 · 페이지 재래스터 금지 | 역할 표 |
| **SHIP 전** | `_qa_video_slides.py` 통과 필수 | `_pd_assemble.py` |

### 단계 (항상 동일)

```
P0 bible → P1 Playwright stills → P2 Grok TTS
  → P3 bridge(있으면) → P4 render+concat → P5 assemble+BGM
  → P5b QA gate → P6 TG
```

---

## 스크립트 맵 (손대지 말 것 / 여기만 타라)

| 역할 | 파일 |
|------|------|
| 엔트리 | `scripts/produce_pd.sh` |
| 클립+concat | `scripts/_render_video.py` |
| 북엔드+BGM | `scripts/_pd_assemble.py` |
| QA | `scripts/_qa_video_slides.py` |
| 브릿지 FX | `scripts/bridge_fx.sh` |
| 프롬프트 브릿지 | `configs/imagine_prompt_standard_v1.json` |

---

## 규칙

1. **새 세션에서 파이프를 다시 발명하지 말 것.** CURRENT → v2 만.
2. QA 실패면 TG 보내지 말 것.
3. 상수 바꾸려면 v2 → **v3** 로 올리고 CURRENT를 갱신 (슬쩍 수정 금지).
4. 페이지 본편은 공짜 공장. Grok 토큰은 성우·PD·브릿지.

— _Grok · LOCK
