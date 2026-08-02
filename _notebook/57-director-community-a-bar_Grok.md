# Director Community A-bar — 구현 (_Grok)

> 2026-08-02 · 커뮤니티 리서치(recast / Purple Owl / Screencast) → 코드 고정  
> 산출: `out/helena_phone_pro_v7.mp4` (1080×1920)

---

## 1. 커뮤니티가 A라고 부르는 것 (자동화 데모)

| 기능 | 출처 | 우리 구현 |
|------|------|-----------|
| TTS-first → 영상 시계 | Purple Owl, recast | `voice_engine` + shoot deadline + edit freeze/compress |
| auto-zoom | recast / Screen Studio | `overlays.js autoZoom` scale~1.14 |
| 커서·클릭 리플 | recast, Screencast showActions | overlay v4 |
| 고품질 TTS | ElevenLabs/OpenAI | `OPENAI_API_KEY` → tts-1-hd, else edge+humanize |
| 1080p | recast default | `--format shorts_1080` |
| 자막 | recast burn | `--subs` + `.srt` sidecar |
| 결정론 ship | (거의 없음) | **perfect_ship 사다리** |

---

## 2. 진입점

```bash
cd helena-programming/director
python3 perfect_ship.py \
  --scenario scenarios/helena_phone.json \
  --out out/helena_phone.mp4 \
  --format shorts_1080 \
  --subs \
  --tts auto
```

| 플래그 | 의미 |
|--------|------|
| `--format shorts_1080` | 1080×1920 (기본 A-bar) |
| `--subs` | SRT 번인 + `.srt` 파일 |
| `--tts auto` | OpenAI 키 있으면 tts-1-hd, 없으면 edge+humanize |

---

## 3. 신규 모듈

| 파일 | 역할 |
|------|------|
| `voice_engine.py` | TTS-first · OpenAI/edge · multi_click_pad |
| `subtitles.py` | SRT 생성 · ffmpeg burn |
| `overlays.js` | `autoZoom` + zoom log |
| `edit()` | freeze if VO longer · **setpts compress if video longer** |

---

## 4. v7 SHIP

| 항목 | 값 |
|------|-----|
| 해상도 | **1080×1920** |
| 클릭 | **8/0** |
| zoom_events | **63** · auto_zoom True |
| VQA | **100 S** |
| perfect_ship | **10/10 SHIP** |
| 파일 | ~11MB · ~63s |

---

## 5. 서명

- 구현: **_Grok** (2026-08-02)
