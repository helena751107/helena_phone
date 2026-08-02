# Director PRO v8 — 프로급 소원 풀이 (_Grok)

> 2026-08-02 · Boss: 진짜 프로급, 이전 TG보다 훨씬 잘  
> 산출: `out/helena_phone_pro_v8.mp4`

---

## 커뮤니티에서 가져온 솔루션

| 기법 | 출처 | 구현 |
|------|------|------|
| approachMs 커서 홀드 후 클릭 | playwright-recast | `demoClick` → glide → 520ms hold → ripple |
| 안정 줌 (재락 시 지터 없음) | recast / Screen Studio | zoom key reuse |
| Ken Burns 미세 드리프트 | Screen Studio 언어 | CSS `hd-ken` animation |
| 시네마 비네팅·레터박스 | 제품 데모 관례 | `#hd-vignette` · letter bars |
| 광분 배속 금지 | 시청 품질 상식 | setpts ≥ 0.72 + audio atempo |
| 짧은 편집 대본 | 투어 호흡 | `helena_phone_pro.json` |

---

## v8 SHIP

- overlay **v5** · clicks **8/0** · proof **16/16** · VQA **100** · perfect_ship **SHIP**
- 인코드 CRF **17** · 보이스 InJoon + humanize

## 남은 한계 (정직)

- 폰 shoot이 VO보다 김 → **최대 1.39×** 압축 잔존 (0.4×는 제거)
- ElevenLabs / 실 crop-zoom 미도입
- 시네마 최종본 = **V3 ComfyUI**

---

_Grok 2026-08-02
