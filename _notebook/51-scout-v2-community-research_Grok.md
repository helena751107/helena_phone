# Scout v2 — 커뮤니티 리서치 → ARIA Planner급 (_Grok)

> 2026-08-01 · Boss: “Claude Chrome보다 스카우트가 더 나을 수 있다. 커뮤니티 방법 있다.”

---

## 1. 결론 (한 줄)

**맞다.** Claude-in-Chrome / 순수 CSS DOM 훑기보다  
**Playwright 공식 Agents·MCP 스택(ARIA snapshot + getByRole + live verify)** 이 Scout에 정답에 가깝다.

---

## 2. 커뮤니티·공식 축

| 출처 | 패턴 | 우리 맵핑 |
|------|------|-----------|
| [Playwright Test Agents](https://playwright.dev/docs/test-agents) | Planner → Generator → Healer | Scout → Shoot → enforce/healer |
| [Playwright MCP Snapshots](https://playwright.dev/mcp/snapshots) | **refs / a11y tree**, CSS 말고 스냅샷 | `page.aria_snapshot()` |
| [ARIA Snapshots docs](https://playwright.dev/docs/aria-snapshots) | YAML accessibility tree | `scout.aria.yml` |
| [Locators guide](https://playwright.dev/docs/locators) | **getByRole(+name) 1순위** | `locator: {by:role, role, name}` |
| Generator 산출물 관습 | 라이브로 셀렉터 검증하며 코드 생성 | `live_verify_role()` |
| Healer | 실패 시 동등 요소 재탐색 | CSS variants + role fallback in shoot |
| Arcade/Storylane | 스텝당 한 포커스 | `demo_score` 랭킹 |

### Playwright Agents (공식)

1. **Planner** — 앱 탐색 → Markdown 테스트 플랜 (`specs/…md`)
2. **Generator** — 플랜 → `getByRole` 테스트, **실행하며 검증**
3. **Healer** — 실패 재현 → 동등 로케이터 패치

### MCP / Agent CLI 베스트 프랙티스

1. Use **refs / a11y**, not brittle CSS  
2. Re-snapshot after navigation  
3. Limit depth / scope to section  
4. Combine snapshot + screenshot when visual needed  

---

## 3. 이전 Scout v1 한계 (Claude급 휴리스틱)

```
DOM querySelectorAll('button.acc-head, .pillar, .node, …')
  → cssPath()
  → sections[]
```

| 약점 | 결과 |
|------|------|
| 사이트 전용 클래스 의존 | 다른 랜딩에서 붕괴 |
| 접근 이름 무시 | “01 Dual Track…” 시맨틱 유실 |
| 검증 없음 | 깨진 셀렉터를 시나리오에 실어 보냄 |
| 랭킹 없음 | 메뉴/테마 버튼 = CTA 동급 |
| 플랜 산출 없음 | Planner MD 없음 |

Chrome 비전 모델이 화면을 “보고” 클릭 후보를 고르는 것과 비교하면,  
v1은 **CSS 수프**에 가깝고 에이전트급이 아니었다.

---

## 4. Scout v2 설계

```
load + fonts-ready
  │
  ├─① DOM pass (cssPath, section geometry)     ← 카메라 스크롤용
  ├─② page.aria_snapshot() YAML                ← Planner 시야
  ├─③ parse roles/names → demo_score rank
  ├─④ live_verify getByRole(role, name)        ← Generator 계약
  ├─⑤ merge DOM↔ARIA (strict text match)
  └─⑥ artifacts: scout.json + scout.aria.yml + scout_plan.md
```

### 산출 필드 (신규)

```json
{
  "scout_version": 2,
  "scout_engine": "aria+dom+live_verify",
  "aria_snapshot_chars": 7345,
  "verified_count": 36,
  "interactives": [{
    "selector": "#tracks-head",
    "role": "button",
    "name": "01 Dual Track 돌봄과 소망을 동시에",
    "locator": {"by": "role", "role": "button", "name": "…"},
    "demo_score": 137,
    "verified": true,
    "source": "dom+aria"
  }]
}
```

### Shoot 연동

`run_director.do_clicks` 후보 순서:

1. `getByRole(role, name)` (Scout 검증 로케이터)
2. CSS healer variants (`#id`, 말단 조각)

오버레이 `demoClick`은 **element handle** 기준 → role locator도 링/커서 가능.

---

## 5. helena_phone 실측 (2026-08-01)

| 메트릭 | Scout v2 |
|--------|----------|
| ARIA snapshot | **7345 chars** |
| live-verify roles | **28/28** |
| sections | 10 |
| interactives | 40 |
| verified (merged) | **36** |
| plan | `out/scout_plan.md` |

Top demo_score 예:

1. Install accordion / CTA (~160)
2. Dual Track accordion (137)
3. Centers / System / Agents heads (122+)
4. Workcenter listbox buttons (①공장 …)

---

## 6. Claude Chrome vs Scout v2

| | Claude-in-Chrome (비전) | Scout v2 (이 구현) |
|--|------------------------|---------------------|
| 입력 | 스크린샷 + DOM 일부 | **a11y tree + DOM + live API** |
| 재현성 | 세션/모델 의존 | **결정론 JSON** |
| 셀렉터 | 환각 가능 | **count()>0 검증 후 채택** |
| 비용 | 토큰·비전 비쌈 | Playwright 로컬 1회 |
| 플랜 | 대화형 | `scout_plan.md` 고정 산출 |
| 데모 적합성 | 사람 지시 의존 | `demo_score` 자동 랭크 |

**비전 없이도** 튜토리얼 후보를 더 안정적으로 뽑는다.  
비전은 “애매한 아이콘/차트 노드” 보강용으로 남기면 된다 (다음 단계).

---

## 7. 파일

- `helena-programming/director/scout.py` — v2 본체  
- `helena-programming/director/run_director.py` — role-first click  
- 산출 예: `director/out/scout_v2.json`, `scout.aria.yml`, `scout_plan.md`  
- 선행: `_notebook/49-director-community-research_Grok.md`, `50-…visual-proof…`

---

## 8. 다음 (초1급 Scout)

1. Section-scoped `locator.aria_snapshot()` (depth limit)  
2. SVG diagram nodes: aria 없는 경우 geometry+label 휴리스틱  
3. Multi-page crawl (nav href 따라 1-hop)  
4. Scout diff (aria.yml git) = 회귀 감지  
5. 선택: 비전 1컷으로 diagram-only 보강  

---

## 9. 서명

- 리서치·구현·실측: **_Grok** (2026-08-01)  
- Boss 검수: _대기_
