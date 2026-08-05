# 62 · Grok 플러그인 영상 파이프 (_Grok)

> 2026-08-05 · Boss 지시: **이미 돌아가는 솔루션 위에** Grok 예쁜 이미지 + Grok 성우만 꽂아라.

## 구조

```
기존 공장 (건드리지 않고 확장)
  produce_intro.sh / episode_produce.sh / FFmpeg concat
        ▲
        │  플러그인 슬롯
        ├─ stills/     ← Grok Imagine 다이어그램·키프레임
        └─ grok_tts.py ← xAI TTS (ara/eve/…)  성우 본체
```

| 파일 | 역할 |
|------|------|
| `scripts/grok_tts.py` | `POST https://api.x.ai/v1/tts` · 세션 JWT 또는 `XAI_API_KEY` |
| `scripts/produce_plugin.sh` | manifest + stills + Grok TTS + FFmpeg + TG |
| `scripts/produce_intro.sh` | `TTS_ENGINE=grok` 기본 · `PLUGIN_STILLS=` 있으면 캡처 스킵 |
| `helena-programming/director/voice_engine.py` | 우선순위: **grok → openai → edge** |

## 플러그인 디렉터리

```
out/plugins/landing6/
  manifest.json
  stills/01.jpg … 06.jpg   # Grok이 만든 것만
  bgm.m4a                    # 선택 (Boss 음원)
```

```bash
bash scripts/produce_plugin.sh /root/work/out/plugins/landing6
# → out/landing6_grok/landing6_grok_final.mp4 + TG
```

## 성우

- **본체:** Grok Voice (`ara` 기본, `eve`/`altair`/… 선택)
- **금지 기본값 아님:** edge-tts (폴백 only)
- 한국어: `language=ko` 지원 확인됨

## 한 줄

> 웹페이지·에피소드 파이프는 공장. Grok은 **예쁜 컷 + 비싼 성우** 플러그인.
