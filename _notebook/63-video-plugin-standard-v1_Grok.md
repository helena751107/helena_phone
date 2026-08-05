# 63 · Video Plugin Standard v1 — 커뮤니티 A-bar 코드 고정 (_Grok)

> 2026-08-05 · Boss: 파이프 스탠다드 맞냐? 품질 더 올려. 커뮤니티 리서치.

## 0. 솔직 상태 (이전)

| 질문 | 답 |
|------|-----|
| 코드로 다 설정됐나? | **부분.** `grok_tts.py` + `produce_plugin.sh` 초안만 있음 |
| 스탠다드였나? | **아니오.** 원샷 파일럿. A-bar 게이트 없음 |
| 품질 | 정지 슬라이드 + 짧은 VO + 침묵 패딩 = **C+~B−** |

## 1. 커뮤니티에서 가져온 A 규칙

| 규칙 | 출처 | 코드 반영 |
|------|------|-----------|
| **TTS-first** (VO가 시계) | Purple Owl / recast · Vivideo 2026 | L1 Grok TTS → 그다음 비주얼 |
| 랜딩 **60–90s**, 훅 3–10s | Vidico / Demopolish 2026 | clip 6×10 + xfade ≈ 58s |
| **9:16 · 1080** | recast · LTX short-form | default `1080:1920` |
| **Captions** | short-form 2026 트렌드 | ASS 번인 · safe zone |
| **xfade** | FFmpeg 커뮤니티 | `xfade` + `acrossfade` |
| **loudnorm + duck** | broadcast / Mux FFmpeg | weights 1 : 0.28 |
| **Grok TTS** punctuation · tags | xAI TTS docs | `ara` storytelling, speed 0.94 |
| stills need motion | AI video workflow | **Ken Burns** zoompan |
| edge 금지 | Boss / SuperGrok 가치 | `allow_edge_fallback: false` |

## 2. 스탠다드 산출물 (코드)

| 경로 | 역할 |
|------|------|
| `configs/video_plugin_standard_v1.json` | **정본 스펙** |
| `scripts/produce_plugin.sh` | A-bar 엔트리 (게이트·자막·xfade·KenBurns) |
| `scripts/grok_tts.py` | xAI TTS |
| `director/voice_engine.py` | grok → openai → edge |
| `out/plugins/<id>/manifest.json` | 에피소드 플러그인 |

```bash
bash scripts/produce_plugin.sh /root/work/out/plugins/landing6
# → out/landing6_a/landing6_a_final.mp4
# → out/landing6_a/ship_report.json
```

## 3. 파이프 사다리 (고정 순서)

```
L0 manifest
L1 Grok TTS-first + loudnorm
L2 pad to clip_sec (gap 측정)
L3 still|motion resolve
L4 Ken Burns or motion normalize
L5 ASS 자막
L6 xfade + acrossfade
L7 BGM duck + final loudnorm
L8 gate → ship_report.json
L9 TG
```

## 4. 게이트

- Grok TTS 아니면 경고
- VO gap > 1.0s → 경고 (대본 밀도 올리기)
- subs 필수
- duration / resolution 검사
- `strict_gate: true` 면 fail exit 2

## 5. 아직 A 풀스택 아닌 것 (다음)

- 실 랜딩 Playwright 2샷 강제 슬롯
- Imagine `image_to_video` motion/ 자동 채움
- sidechaincompress 진짜 덕킹
- xfade 타임라인에 ASS 정확 재매핑
- Vision QA 자동 루프

## 6. 서명

구현·리서치: **_Grok** · standard v1
