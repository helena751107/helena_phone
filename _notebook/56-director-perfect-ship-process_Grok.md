# Director Perfect Ship — 만점 프로세스 코드화 (_Grok)

> 2026-08-02 · Boss: 만점 올릴 때 쓰던 프로세스 자체를 솔루션·코드로 고정. 매번 마음대로 하지 마라.

---

## 1. 문제

에이전트가 세션마다:

- 다른 순서로 품질 패치
- 메트릭만 통과시키고 SHIP
- 문서만 쓰고 강제 없음

→ **프로세스가 사람/LLM 머리에만 있음 = 재발.**

---

## 2. 솔루션

**만점 사다리를 JSON + enforce + 단일 CLI로 고정.**

| 파일 | 역할 |
|------|------|
| `director/process/perfect_ship_v1.json` | L0–L9 사다리 · anti-pattern · remediation_map · agent_rules |
| `director/perfect_ship.py` | **유일한 진입점** · 렌더 + 검증 · `.process.json` |
| `director/policy/tutorial_v1.json` v2 | require_all_declared_clicks · cursor_on_primary · tts_humanize · VQA≥100 · process_id |
| `director/enforce.py` | 위 require 결정론 거부 |
| `director/run_director.py --process` | process stamp · L8 verify 내장 |

---

## 3. 사용법 (에이전트 필수)

```bash
cd helena-programming/director
python3 perfect_ship.py \
  --scenario scenarios/helena_phone.json \
  --out out/helena_phone.mp4
```

실패 시:

1. `out/*.process.json` 의 `remediation_ids` 확인  
2. `remediation_map` 이 가리키는 코드만 수정  
3. **같은 사다리 재실행**  
4. SHIP 배지 나오기 전 TG 금지  

---

## 4. 사다리 요약

L0 Scout → L1 Directing → L2 Voice humanize → L3 5-act+cursor+all clicks →  
L4 Proof → L5 Edit → L6 Quality → L7 VQA 100 → L8 Process verify → L9 SHIP

---

## 5. 검증

`perfect_ship.py --verify-only` on pro_v6 → **SHIP · 10/10 stages PASS**

---

## 6. 서명

- 프로세스 코드화: **_Grok** (2026-08-02)  
- Boss 검수: _대기_
