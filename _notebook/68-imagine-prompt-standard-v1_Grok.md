# 68 · Imagine 프롬프트 표준 v1 — 초A 브릿지 스틸 (_Grok)

> 2026-08-06 · Boss: 대충 프롬프트 금지. 포토그래퍼·예술 작품 수준. 버전 올리며 실험.

## 왜 v1이 필요한가

이전 브릿지는 **짧은 키워드 프롬프트** → 평범한 “AI 무드 이미지”.  
페이지 캡처 공장과 대비되면 **구독 가치가 안 보인다.**

**원칙:** 페이지 본편은 Playwright. Grok 이미지는 **앞·뒤 브릿지 = 전시용 한 장** 만 최고 퀄.

## 프롬프트 규칙 (v1)

1. **주어 먼저** · 장면 **하나**  
2. **산문 3–5문장** (키워드 나열 금지)  
3. 순서: 피사체 → 자세 → 공간 → 스타일 → 구도 → 빛/무드 → 재질 1–2  
4. **긍정 서술만**  
5. Shorts → **9:16**  
6. **글자·가짜 UI 금지** (감정은 빛으로)  
7. 렌즈·빛·심도 언어 사용 (`masterpiece 8k` 스팸 금지)  
8. 이후 I2V 대비: 히어로 1개, 배경 단순

## 브랜드 락

| | hex |
|--|-----|
| paper | `#0a0908` |
| gold | `#d4a84b` |
| teal | `#3db8a8` |

느낌: dark luxury editorial · quiet hope · care + aspiration

## 캐논 프롬프트 (v1)

전문: `configs/imagine_prompt_standard_v1.json` → `canon_prompts_v1`

- **b_open_hook** — 암전 속 폰 · 금테 빛 · 초대장  
- **b_close_handoff** — 금빛 인 · 손·폰 · 핸드오프 여운  

## 파일

| 경로 | 용도 |
|------|------|
| `configs/imagine_prompt_standard_v1.json` | 기계 판독 표준 |
| `out/pd_intro/bridge/v1/` | v1 생성본 보관 |
| `out/pd_intro/bridge/b_open.jpg` | 파이프 활성 오픈 |
| `out/pd_intro/bridge/b_close.jpg` | 파이프 활성 클로즈 |

## 버전 업 방법

Boss 점수 → `v1.1` 프롬프트 수정 → 같은 앵커에서 `image_edit` 우선 → 이기면 active 교체.

— _Grok
