# Director PRO v3 — Visual Proof 강제 (_Grok)

> 2026-08-01 · 목적: **가짜 SHIP PASS 종식** — 클릭 카운트만 통과하는 산출 차단  
> 산출: `helena-programming/director/out/helena_phone_pro_v3.mp4`

---

## 1. Boss 지적 (정당한 실패)

PRO v2 텔레그램 보고: `클릭 8/0 · SHIP PASS · ~79s`

실제 프레임 감사 결과:

| 증상 | 사실 |
|------|------|
| 클릭이 안 보임 | Playwright `force=True` 로그만 성공. 아코디언은 **expand-all 이후** 토글이라 상태 변화 약함 |
| 효과가 안 보임 | 클릭 직후 `clearFocus()` → gold ring **~1초**만 존재. 118s 중 거의 무 |
| 합성 없음 | Screen Studio급 후처리 없이 CSS 오버레이만. 게이트가 픽셀 검증 안 함 |
| 가짜 PASS | G3가 `black_ratio 0.92` 도 통과. PNG 필터 미해제로 gold/teal 카운트 **0** |

**한 줄:** 메트릭 PASS ≠ 시청 가능. 게이트가 눈을 속였다.

---

## 2. Root Cause (v2 → v3)

| ID | 원인 | v3 대책 |
|----|------|---------|
| R1 | `clearFocus()` after every click | **holdFocus** for full beat hold |
| R2 | expand-all before tour | **collapse-all** → open per beat (visible state change) |
| R3 | Overlay dim 0.58 + tiny cursor | Overlay **v3**: dim 0.36, 44px cursor, triple ripple, pulse ring |
| R4 | Quality gate = file size only | **G7** mid-video gold/teal samples ≥2/5 |
| R5 | actions_log has no pixel proof | **visual_proof** PNG per click + gold≥80 teal≥20 |
| R6 | PNG filter not unfiltered | `png_decode_rgb` filter types 0–4 |
| R7 | Scout merge duplicate clicks | head/acc detect + selector dedupe |
| R8 | CTA navigates away | init_script preventDefault on external links |

---

## 3. Pipeline (강제 본체)

```
Scout (Planner)
  → Scenario stamp + policy enforce (pre_shoot)
  → Voice (edge-tts)
  → Intro HTML/CJK
  → Shoot v3 (overlay + demoClick + proof frames)
  → enforce post_shoot (clicks + visual_proof_pass)
  → Edit (ffmpeg 30fps + intro concat)
  → Quality G1–G7
  → enforce pre_ship
  → SHIP
```

MCP는 여전히 **입구만**. 본체 = `policy/tutorial_v1.json` + `enforce.py` + proof PNG.

---

## 4. Overlay v3 스펙

- Hole spotlight (box-shadow cutout, dim 36%)
- Gold focus ring 3px + live pulse
- Teal outline on hole
- Cursor SVG 44px + gold stroke, park center
- Multi-ripple ×3 (teal / gold / white)
- CLICK badge
- STEP caption + PRODUCT TOUR chip + progress bar
- `demoClick`: focus → moveCursor(580ms) → ripple → **holdFocus** (no clear)

---

## 5. 이번 산출 (pro_v3)

| 항목 | 값 |
|------|-----|
| 파일 | `out/helena_phone_pro_v3.mp4` |
| 길이 | **56.0s** · ~3.5MB |
| 클릭 | **8 OK / 0 FAIL** |
| Proof | **16/16 PASS** (gold 782–5678, teal 1078–1667) |
| G7 accents | **5/5** samples hit |
| overlay_version | **3** |
| policy | tutorial_v1 |
| 렌더 시간 | ~317s |

Proof 샘플 (사람 눈 확인):

- CTA: gold ring + callout `CTA` + cursor on INSTALL
- Tracks: gold ring on accordion + callout + STEP 2/6
- Diagram node: spotlight on S21 DEV node

---

## 6. 정책 변경 (tutorial_v1)

```json
"min_overlay_version": 3,
"require_visual_proof": true,
"min_visual_proof_pass": 4,
"collapse_before_tour": true,
"expand_all_before_tour": false
```

`enforce_actions`가 `visual_proof_pass` 없으면 **post_shoot FAIL (exit 4)**.

---

## 7. 아직 남은 갭 (초1급 다음)

1. **A/V 싱크 정밀화** — 클릭 애니메이션 시간만큼 hold 보정은 0.85 계수 근사. beat-level timeline 테이블 필요  
2. **Ken Burns / soft zoom** — 후처리 compositor (ffmpeg zoompan) 미구현  
3. **커서 궤적 스플라인** — CSS transition만. 베지어 경로 녹화는 다음  
4. **에이전트 카드 클릭** — 레이더 전환 비트를 시나리오에 명시 클릭으로  
5. **네이버/유튜브 업로드 파이프** — 렌더 ≠ 발행

---

## 8. 관련 파일

- `helena-programming/director/overlays.js` (v3)
- `helena-programming/director/run_director.py` (shoot + proof)
- `helena-programming/director/quality.py` (G7 + PNG unfilter)
- `helena-programming/director/enforce.py`
- `helena-programming/director/policy/tutorial_v1.json`
- `helena-programming/director/scenarios/helena_phone.json`
- 리서치: `_notebook/49-director-community-research_Grok.md`
- 재발: `_notebook/48-director-video-recurrence_Grok.md`

---

## 9. 서명

- 분석·수정·재렌더·문서: **_Grok** (2026-08-01)
- Boss 검수: _대기_
