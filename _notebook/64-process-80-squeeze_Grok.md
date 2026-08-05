# 64 · 프로세스 80% 쥐어짜기 (_Grok)

> Boss: 80점까지. 구독 풀가동. 아이디어·프로세스 올려.

## 목표

| 지표 | 50% (v1) | **80% (v2)** |
|------|----------|--------------|
| 성우 | Grok TTS | Grok TTS dense VO |
| 모션 | KenBurns only | **Imagine I2V ≥50%** |
| 제품 | 추상 only | **Live UI ≥2 shots** |
| 자막/xfade/게이트 | 있음 | 유지+강화 |
| 배포 | TG 1본 | TG + ship_report |

## 아이디어 뱅크 (구독 쥐어짜기)

1. **하이브리드 샷 믹스** — art motion + live DOM (신뢰)
2. **TTS-first 밀도** — gap≤0.8s, 문장으로 10초 채움
3. **Imagine sequential** — 429 대비 순차 10s
4. **실 UI Ken Burns** — Playwright 캡처에 약한 push-in
5. **Grok ara 나레이션** — edge 금지
6. **xfade 0.5s** — hard cut 금지
7. **ASS 한글 자막** — safe zone
8. **BGM duck 0.07** — Boss 자작 음원
9. **1080×1920** Shorts master
10. **ship_report.json** — PASS/FAIL 수치
11. *(다음)* Vision QA 재생성 루프 → 90%
12. *(다음)* perfect_ship 커서 투어 병합 → 95%

## 실행 엔트리

```bash
bash scripts/produce_plugin.sh /root/work/out/plugins/landing80
```

스펙: `configs/video_plugin_standard_v2.json`
