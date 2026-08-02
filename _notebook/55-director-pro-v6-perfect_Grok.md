# Director PRO v6 — 만점 솔루션 (_Grok)

> 2026-08-02 · Boss: 초A급 올려라. 솔루션.  
> URL: https://helena751107.github.io/helena_phone/  
> 산출: `helena-programming/director/out/helena_phone_pro_v6.mp4`

---

## 1. v5 감사에서 죽인 버그

| 버그 | 원인 | v6 수정 |
|------|------|---------|
| 커서가 FILES 메트릭 위 | `focus`/`holdFocus`가 커서를 안 옮김. park=화면 55%=메트릭 밴드 | **cursor always tracks primary** |
| 2차 클릭 증발 | 시간 예산에 `break` | multi-click 보장 + 비트 pad 확장 |
| 클릭 결과 안 보임 | act 직후 다음으로 점프 | result hold 280–700ms |
| 기계 TTS | edge-tts raw | ffmpeg broadcast humanize |
| lead black 8s | 부트 과다 | trim 1.8s · boot 단축 |

---

## 2. 구현

### overlays.js v4
- `focus` / `holdFocus` → `moveCursorTo(primary)` 필수
- `_resolveTarget` — stats/metric 금지, CTA·acc-head·node 우선
- soft zoom `body scale(1.06)` origin=target
- parkCursor y=38% (메트릭 밴드 회피)
- `version: 4`

### shoot
- multi-click 전부 실행 (arch node · workcenter)
- hold 중 1.1s마다 primary re-lock
- demoClick `await` Promise

### voice
- multi-click 비트 pad += 1.65s × (n-1)
- loudnorm + presence EQ humanize

---

## 3. SHIP 성적

| 항목 | v5 | **v6** |
|------|----|--------|
| clicks | 6 | **8/0** |
| proof | 12/12 | **16/16** |
| overlay | 3 | **4** |
| cursor_on_primary | — | **True** |
| VQA | 100 S | **100 S** |
| lead trim | ~8s | **1.8s** |
| 사람 프레임 | 커서 메트릭 | **CTA·아코디언 링** |

---

## 4. 사람 비전 (프레임)

- t10: 커서 **INSTALL IN ONE LINE** + CTA 콜아웃 + 골드링 ✅  
- t26: 아코디언 **돌봄과 소망** 오픈 연출 ✅  
- t42: System Map 펼침 + 다이어그램 노드 노출 ✅  

---

## 5. 서명

- 솔루션·렌더·TG: **_Grok** (2026-08-02)
