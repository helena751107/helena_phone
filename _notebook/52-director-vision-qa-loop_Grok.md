# Director Vision QA 루프 — 만점까지 (_Grok)

> 2026-08-01 · Boss: 비전 셀프 QA 넣고 클로드급 튜토리얼 바까지 올려라. 중간 TG 보고.

---

## 1. 목표

| 바 | 의미 |
|----|------|
| Screen Studio | 커서 경로 · 클릭 리플 · 느린 페이스 |
| Arcade / Storylane | 스텝당 스포트라이트 1개 |
| Playwright Generator | 검증된 role 클릭 · dead nav 금지 |
| Claude Code 데모 톤 | STEP 캡션 ↔ 화면 내용 동기 |

**SHIP = policy + visual_proof + Vision QA ≥ 85/100** (v4: **100/100 S**)

---

## 2. Vision QA 모듈

`helena-programming/director/vision_qa.py`

| ID | 가중 | 검사 |
|----|------|------|
| V1 | 15 | early not pure black · 1.5–3s void 금지 |
| V2 | 12 | teal chip / PRODUCT TOUR |
| V3 | 12 | STEP caption 계열 |
| V4 | 18 | gold ring ≥40% body samples |
| V5 | 12 | teal chrome |
| V6 | 12 | mean_y readable band |
| V7 | 12 | visual_proof pass rate ≥70% |
| V8 | 7 | mid-video blackdetect void 없음 |

+ **사람 비전 체크리스트** (`*.agent_vision.json`) — Grok 프레임 리딩

---

## 3. pro_v3 → pro_v4 루프

### 기준선 (pro_v3 · 사람 비전)

- t=2s **순수 검정** (concat seam)
- CTA 실클릭 → `#install` 이탈 · STEP 1/6 고착
- 거대 링이 화면 삼킴
- 자동 VQA는 픽셀만 보고 만점 줄 수 있음 → **V1 mid-void hard fail** 추가

### 수정

1. **nav-lock** — `#` / http 링크는 visual-only demoClick
2. **concat re-encode** — `-c copy` 금지, filter concat (seam 검정 제거)
3. **ring cap** 55vh / 420px · callout clamp under chip
4. **cover re-anchor** after CTA
5. **role-first click** (Scout v2)
6. ship gate: `vision_qa_required` + pass_score 85

### 결과 (pro_v4)

| 항목 | 값 |
|------|-----|
| 파일 | `out/helena_phone_pro_v4.mp4` |
| Auto VQA | **100/100 · S · PASS** |
| 사람 비전 | **A+** (H1–H8 all pass) |
| 클릭 | 8/0 · proof 16/16 · role accordion |
| 길이 | ~55s |

TG 보고: 기준선 실패 원인 → 조치 중 → SHIP 100/100 (전송 성공)

---

## 4. 파이프라인 단계

```
Scout v2 → enforce pre → Voice → Intro → Shoot v3
  → enforce post → Edit (seamless concat)
  → Quality G1–G7 → enforce pre_ship
  → Vision QA (V1–V8)  ← NEW hard gate exit 5
  → Self-audit + agent_vision notes → SHIP
```

---

## 5. 남은 갭 (S+ / 클로드 영상팀)

1. Ken Burns soft zoom  
2. SVG 노드 호버 상태 강조  
3. beat 단위 A/V 타임라인 테이블  
4. OCR 기반 STEP↔섹션 동기 검사  

---

## 6. 서명

- Vision QA · 수정 · 재렌더 · TG: **_Grok** (2026-08-01)
