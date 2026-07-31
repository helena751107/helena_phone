# Director 수준 상향 — 커뮤니티·프로 제품 리서치 (_Grok)

> 2026-07-31 · 목적: 하이테크 제품 튜토리얼 / 에이전트급 데모 영상 기준 정립

---

## 1. 업계·커뮤니티에서 반복되는 패턴

### A. Playwright + 데모 영상 (r/Playwright 등)

- **스크립트 먼저 → 녹화** (즉흥 클릭 금지)
- Playwright로 **결정론 데모 영상** 생성 후 AI 보이스 오버
- 에이전트 3단 (공식 Playwright Test Agents 사상과 유사):
  - **Planner** = 앱 탐색·플랜
  - **Generator** = 실행 스크립트
  - **Healer** = 실패 셀렉터 수정

→ 우리 맵핑: Scout=Planner, scenario+shoot=Generator, enforce 실패 시 재시도=Healer 자리

### B. 프로 제품 데모 툴 (Screen Studio / 유사 계열)

- **커서 궤적 + 클릭 리플**
- **포커스 링 / 스포트라이트(주변 딤)**
- 의도적 **느린 페이스**
- 하단 캡션 · 상단 스텝 칩
- 부드러운 줌/팬 (Ken Burns) — 선택

### C. Arcade / Storylane / Navattic (인터랙티브 데모)

- 스텝마다 **하이라이트 한 요소만**
- “지금 어디를 보라”가 프레임마다 명확
- 클릭 가능한 UI = 스토리 비트

### D. Playwright Agents / MCP (Microsoft 문서 축)

- 탐색 → 플랜 MD → 실행 코드
- **환각 셀렉터 방지 = 라이브 검증**
- MCP는 도구 입구; **품질은 검증 루프**

---

## 2. 우리가 빠져 있던 것 (이전 산출)

| 프로 기준 | 이전 Director |
|-----------|----------------|
| 스포트라이트 포커스 | 없음 (스크롤만) |
| 클릭 시각 언어 | 약함 |
| Planner→Execute→Heal | Scout만 약함 |
| 고정 fps / 안정 타임라인 | 불안정 |
| 강제 계약 | optional 남발 |

---

## 3. 적용 스펙 (pro_v2)

1. Overlay v2: hole spotlight + gold ring + cursor SVG + ripple  
2. `demoClick(el)` 시퀀스: focus → move → ripple → click  
3. policy `tutorial_v1` + enforce (이미) + spotlight 필수 플래그  
4. 30fps 인코드  
5. Healer 1회: 클릭 실패 시 CSS path 완화 재시도  

---

## 4. MCP?

- **강제 본체 = policy + enforce + actions_log** (이미)
- MCP = 외부 에이전트에게 `director.run(url, policy=tutorial_v1)` 만 열어 주는 **입구**
- 리서치 결론: MCP 먼저 만들면 안 됨. **파이프 품질 먼저.**

---

## 5. 출처 축 (요지)

- Playwright Test Agents (planner/generator/healer) — playwright.dev  
- r/Playwright: Playwright → polished product demo + voiceover  
- 제품 데모 UX: Screen Studio 계열 커서/줌 관습  
- 인터랙티브 데모: Arcade/Storylane 스텝 하이라이트
