# 66 · Grok 역할 정정 — PD · 성우 · 브릿지 (페이지 재래스터 금지) (_Grok)

> Boss 2026-08-05  
> 「예쁜 웹페이지 이미 있다. 공짜 프로세스보다 못하면 실패.  
> Grok은 이어 붙일 때 브릿지 이미지/영상 + 성우 + PD에 토큰 써라. 조립은 FFmpeg.」

---

## 1. 틀린 사용 (지금까지 자주 한 것)

```
웹페이지 있음
  → Grok이 페이지를 다시 그림 / 전 구간 I2V
  → 공짜 Playwright 슬라이드보다 못하거나 재생 깨짐
  → 토큰 낭비
```

**결과:** 구독 가치가 안 나오고, free pipe보다 못한 영상.

---

## 2. 맞는 역할 분담 (정본 v3)

| 담당 | 도구 | 하는 일 | 안 하는 일 |
|------|------|---------|------------|
| **공장 (공짜)** | Playwright · produce_intro · episode · **FFmpeg** | 페이지 캡처, 클립, concat, xfade, BGM, 자막, TG | Grok 호출 |
| **PD (Grok)** | 대화 · shot_bible | 스토리·감정·순서·대본·어느 컷이 브릿지인지 | 픽셀 조립 |
| **성우 (Grok)** | `grok_tts.py` / xAI TTS | 전 구간 나레이션 | edge 기본 사용 |
| **브릿지 (Grok)** | image_gen / I2V **소수** | 오프닝·전환·엔딩 등 **이어 붙일 때만** | 전 편 웹 재연출 |
| **조립** | **FFmpeg only** | 타임라인 합성 | 토큰 |

---

## 3. 런타임 비중 가이드

```
[ 라이브 페이지 캡처 ≥ 70% ]  +  [ Grok 브릿지 0~30% ]  +  [ Grok VO 100% ]
              ↑ FFmpeg 조립
```

- 본편 비주얼 본체 = **이미 만든 웹페이지**  
- Grok 비주얼 = **가교** (없으면 안 되는 자리만)

---

## 4. 토큰 우선순위

1. PD 샷 바이블 + 대본  
2. Grok TTS 전 구간  
3. 브릿지 키프레임/짧은 I2V (필요할 때만)  
4. 프레임 QA  
5. ❌ 페이지 전체 재이미지화 금지

---

## 5. 성공 기준 (한 줄)

> **같은 URL에 대해 free produce_intro 결과보다 못하면 SHIP 금지.**  
> Grok이 붙는 가치 = **성우 품질 + PD 구성 + 브릿지 감동**. 페이지 예쁨은 페이지가 이미 담당.

---

## 6. 엔트리

```bash
# 페이지 본체 (공짜 공장) + Grok 성우
TTS_ENGINE=grok bash scripts/produce_intro.sh

# 플러그인: manifest에 live stills 위주, bridge만 Grok 경로
bash scripts/produce_plugin.sh out/plugins/<id>
```

스펙: `configs/video_plugin_standard_v3.json`  
인코딩: yuv420p High (65번 문서)

— _Grok · 역할 정정
