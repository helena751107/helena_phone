# 69 · 성우 플러그인 최종 — Grok 정식 vs Edge 함정 (_Grok)

> 2026-08-06 · Boss 판단: 비수익화여도 Edge 쓰지 않는다. 채널이 날아가면 억울하다.
> 연관: [[67-grok-subscribe-voice-bgm-hurdle_Grok]]

---

## 0. 한 줄

수익화를 포기해도 **Edge TTS는 채널 스트라이크 리스크**가 있다.
열심히 만든 쇼츠가 라이선스 이슈로 삭제되면 억울하다.
**Grok 정식 성우(Ara)로 통일. Edge는 오프라인 시연·비상 폴백 전용.**

---

## 1. 최종 판단

| 조건 | Edge TTS | Grok Ara |
|------|----------|----------|
| 비수익화 개인 채널 | 🟡 약관 위반 자체는 성립 | 🟢 정식 라이선스 |
| 저작권 신고 시 | 경고 → 3회 시 채널 폐쇄 | 문제 없음 |
| 나중에 수익화 전환 | 불가 (자산 재제작 필요) | 그대로 전환 가능 |
| 한줄 | "돈 안 버니까 괜찮겠지" ≠ 안전 | 마음 놓고 업로드 |

---

## 2. 구현 — 성우 플러그인

`director/voice_engine.py` — 통합 TTS 엔진:

```python
from director.voice_engine import synthesize

dur, provider = synthesize("안녕하세요", Path("/tmp/out.mp3"))
# → grok/ara 🟢  or  openai/nova 🟢  or  edge/SunHi 🟡 (폴백 only)
```

**우선순위:** `grok → openai → edge`

- Grok: xAI TTS API · SuperGrok 구독 · 상업 가능 🟢
- OpenAI: tts-1-hd · API 키 필요 · 상업 가능 🟢
- Edge: edge-tts + humanize · **비상업 전용** 🟡

**엔진 강제:**
```bash
TTS_ENGINE=grok bash scripts/produce_pd.sh
TTS_ENGINE=edge bash scripts/produce_intro.sh  # 비상업 시연용
```

---

## 3. 파이프 규칙 (실무)

| 규칙 | 값 |
|------|-----|
| 기본 엔진 | **grok** |
| Grok 성우 | ara (warm narration) |
| Edge 사용 조건 | `allow_edge_fallback=true` + 비수익화 확인 |
| 수익화 영상 | Edge 절대 금지 · Grok only |
| AI 라벨 | YouTube Studio → 합성/AI 생성 콘텐츠 체크 |

---

## 4. 파일

| 경로 | 용도 |
|------|------|
| `director/voice_engine.py` | 통합 성우 플러그인 |
| `scripts/grok_tts.py` | Grok TTS 저수준 호출 |
| `configs/video_plugin_standard_v3.json` | `allow_edge_fallback: false` 기본 |

---

— _Grok · 2026-08-06
