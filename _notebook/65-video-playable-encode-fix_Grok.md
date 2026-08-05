# 65 · 재생 안 됨 인코딩 버그 수정 (_Grok)

> 2026-08-05 · 증상: 스크럽 미리보기는 보이는데 **재생 시 화면 검정** / 다운로드 후도 동일

## 원인

| 항목 | 깨진 값 | 정상 값 |
|------|---------|---------|
| pix_fmt | **yuv444p** | **yuv420p** |
| H.264 profile | **High 4:4:4 Predictive** | **High** |
| AAC sample_rate | **96000** | **48000** |

폰·텔레그램·대부분 플레이어 HW 디코더는 yuv444/High4:4:4 재생 불가.  
소프트웨어 썸네일·스크럽만 프레임 추출 가능 → “미리보기만 되고 재생 안 됨”.

ASS 자막 필터 재인코딩 시 chroma가 444로 올라가 libx264가 4:4:4 프로파일을 고른 것이 주원인.

## 수정 (코드)

`scripts/produce_plugin.sh` 전 구간 libx264:

```
-profile:v high -level 4.0 -pix_fmt yuv420p
-ar 48000 -ac 2
-movflags +faststart
```

- clip / xfade / ass burn 모두 강제
- 게이트: yuv444 검출 시 FAIL

## 재생 가능 산출물

| 파일 | 용도 |
|------|------|
| `out/landing_max/landing_max_playable.mp4` | **1080p 재생 정본** |
| `out/landing_max/landing_max_tg_playable.mp4` | **720p TG 전송용** |

구버전 `landing_max_final.mp4` (yuv444) = **재생 불가, 보관만**.

## 사용

```bash
bash scripts/produce_plugin.sh out/plugins/landing_max
# 이후 final은 자동 yuv420p High
```

— _Grok
