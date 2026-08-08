# 71 · pd_intro v2 — 슬라이드 블랙 꼬리 수정 (_Grok)

> 2026-08-06 · Boss: 화면 안 바뀜 / 중간부터 안 나옴 → 검증 후 재전송

## 원인 (검증으로 확정)

| 증상 | 측정 |
|------|------|
| 중간부터 검은 화면 | t≥16s mean_lum=16 · unique=1 (순흑) |
| 슬라이드 안 바뀜 | video stream **8.67s** (clip0 only) · audio 36~50s |
| playable nb_frames | 426 (≈14s) vs 필요 ~1500 |

**루트 원인:** `_render_video.py` xfade offset  
`offset = i * (clip_durations[i-1] - xfade)` → 2번째 전환부터 오프셋 붕괴  
→ 영상 트랙이 첫 슬라이드에서 끊김, 오디오만 계속 → **블랙 테일**

(개별 `kb_*.mp4` 6장은 정상이었음. 조립만 죽음.)

## v2 수정

1. **concat demuxer** 재인코딩 (깨진 xfade 체인 폐기)
2. **zoompan `d=nframes`** (옛 `d=1/fps` 금지)
3. **CJK 폰트** + bible 캡션
4. **BGM** Boss Shorts · vol=0.025 전 구간
5. **QA gate** `_qa_video_slides.py` — unique frames + non-black + A/V 길이  
   → 실패 시 TG 전송 안 함

## 검증 (SHIP 전)

```
QA PASS · dur=50.2s · unique=10/10 · black=0
video 1504f @30fps · audio 50.18s 일치
```

## 산출

| 경로 | |
|------|--|
| playable | `out/pd_intro/pd_intro_playable.mp4` |
| TG | msg **317** |
| 표준 | `configs/video_pd_pipeline_v2.json` |
| 아카이브 | `out/pd_intro/v2/` |

— _Grok
