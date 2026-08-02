# 연출 설정 — Director Plan First (_Grok)

> 2026-08-01 · Boss: “빛이 따로 놀아. 플랜 자체가 없어. 연출 설정부터 만들어.”

---

## 1. 문제 (왜 영상이 미쳤는가)

지금까지 파이프:

```
scenario(대사·셀렉터) + policy(게이트) + shoot(매직넘버)
```

빠진 층:

```
DIRECTING PLAN = 한 프레임에 무엇을 보게 할 것인가의 문법
```

| 증상 | 원인 |
|------|------|
| 빛·커서 따로 놈 | 오버레이가 “클릭할 때만” 반짝, VO와 무관 |
| STEP vs 화면 불일치 | 비트 경계 없이 카메라/클릭 남발 |
| CTA 후 화면 날아감 | 연출 규칙 없이 실클릭 |
| hold 중 링 증발 / 거대 링 | clearFocus·섹션 전체 focus 임의 |

**결론:** 품질 게이트를 올려도, **연출 악보가 없으면** 연주가 매번 다르다.

---

## 2. 권위 순서 (Authority)

```
1) directing/product_tour_v1.json   ← 연출 성경 (이 문서의 본체)
2) policy/tutorial_v1.json           ← ship 금지 조건
3) scenarios/*.json                  ← 대사·목적지
4) run_director.shoot                ← 악보 연주
5) vision_qa                         ← 연주 녹음 검수
```

**시나리오는 대본이다. 디렉팅은 카메라·조명·큐 시트다.**  
대본만 있으면 연극이 안 된다.

---

## 3. 한 줄 철학

> **한 프레임 = 한 의도.**  
> VO가 시계를 잡고, 화면(빛·커서·카메라)이 따른다. 반대 금지.

---

## 4. 비트 5막 (모든 beat 동일)

| 막 | frac | 하는 일 |
|----|------|---------|
| **establish** | 12% | 카메라 도착 · chip/caption · 빛 ON (클릭 전) |
| **focus** | 15% | 커서 이동 · 콜아웃 |
| **act** | 22% | demoClick · (비-nav만) 실클릭 · proof |
| **hold** | 43% | 결과 유지 · VO 의미 전달 · 추가 난사 금지 |
| **release** | 8% | clearFocus · 다음 비트 준비 |

시계: `phase_budget_ms(audio_sec + pad)` — **hold가 나머지 흡수**.  
예전의 “클릭 애니 다 돌린 뒤 audio 전체를 또 hold” 금지.

---

## 5. 빛 (Light language)

- dim **0.36** · gold ring **3px** · max height **55vh / 420px**
- primary = 첫 클릭 타깃, 없으면 섹션 헤딩
- **hold 중 끄지 말 것** (release 막에서만 OFF)
- 섹션 전체 링 금지 → 내부 h1/button으로 축소

---

## 6. 커서

- 이동 580ms · 리플 700ms · 클릭 후 freeze 350ms
- 항상 primary 위에서 끝남
- 메트릭 그리드에 방치 금지
- `#` / http 링크 = **visual only**

---

## 7. 크롬 (HUD)

- chip: `{i}/{n} · PRODUCT TOUR` — **비트 경계에서만** 변경
- caption: STEP kicker + 현재 섹션 이름
- progress: i/n

---

## 8. 파일

| 경로 | 역할 |
|------|------|
| `director/directing/product_tour_v1.json` | 연출 설정 (canonical) |
| `director/directing.py` | load · phase budget · chrome · primary |
| `director/policy/tutorial_v1.json` | ship 게이트 (directing id 필수 예정) |
| `director/scenarios/helena_phone.json` | 대본 |

---

## 9. 다음 구현 순서

1. ✅ 연출 설정 JSON + loader (이번 커밋)
2. ⬜ `shoot()` 가 5막을 그대로 연주 (매직넘버 제거)
3. ⬜ actions_log에 `phases_played[]` 기록 → enforce
4. ⬜ 재렌더 pro_v5 (연출 악보 준수) + Vision QA

---

## 10. 서명

- 연출 설정 설계: **_Grok** (2026-08-01)  
- Boss 검수: _대기_
