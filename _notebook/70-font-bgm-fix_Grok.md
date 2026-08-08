# 70 · 자막 폰트 깨짐 + BGM whisper 전구간 (_Grok)

## 원인
1. **폰트**: `_render_video.py`가 없는 `NotoSansKR-Regular.ttf` → **DejaVu** 폴백 → 한글 □□□
2. **캡션 미연결**: `shot_bible.caption`이 `SLIDE_TITLES`로 안 넘어감
3. **BGM**: 브릿지 북엔드 조립 후 **재믹스 없음** → open/close 무음, 또는 weights 과감쇄

## 수정
- fontconfig `Noto Sans CJK KR` / `Noto Serif CJK KR`
- `produce_pd.sh` → bible captions export
- `_pd_assemble.py`: VO-only body + bridges → **full-timeline BGM vol=0.025**
- BGM 우선: `bgm_shorts.m4a` (Boss YouTube Shorts 렌더)

## 검증
- open 구간 mean ≈ -57dB (순무음 -91 아님)
- body mean ≈ -26dB (VO 우선)
- TG msg 315

— _Grok · 2026-08-06
