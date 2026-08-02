# 재발일지 — Director 소개 영상 품질 사고 (_Grok)

> 작성: 2026-07-31 · 에이전트: Grok 디자이너  
> 대상: `helena-programming/director` · 샘플 URL `helena_phone`  
> 등급: **P1 (시청 불가 구간 발생)** → 수정 후 **재발 금지 게이트** 적용

---

## 1. 증상 (사용자 보고)

1. **영상 앞부분 텍스트 깨짐** (□□□ 토푸)
2. **처음 화면이 안 나오는 것처럼 보임** (검정/빈 화면)

---

## 2. 재현

- 파이프: Scout → edge-tts → Playwright record → FFmpeg intro concat
- 산출: `helena_phone_scout_intro.mp4` (~121s)
- 프레임 추출:
  - `intro_card` 첫 프레임: 영문만 정상, **한글 자막 전부 □**
  - `page.mp4` 0–3s: **완전 검정** (PNG ~5.5KB)
  - `page.mp4` ~8s 이후: 실제 웹 UI 정상 (한글 포함)

---

## 3. 원인 분석 (Root Cause)

| ID | 증상 | 원인 | 계층 |
|----|------|------|------|
| **R1** | 텍스트 깨짐 | 인트로를 FFmpeg `drawtext`로 그림. 폰트 후보에 Noto KR 없음 → **DejaVuSans 폴백(라틴 only)** | Intro |
| **R2** | 앞 검정 | Playwright `record_video`가 **about:blank / 첫 페인트 전**부터 타임라인 시작. `domcontentloaded`+2s만으로는 부족 | Shoot |
| **R3** | 체감 악화 | 사이트 배경 `#0a0908` + 긴 커버 나레이션(~19s) → 검정 구간이 “영원히” 느껴짐 | Direct/Write |
| **R4** | 품질 관리 부재 | 렌더 후 **첫 프레임·토푸·블랙 검출 게이트 없음**. 삽질 산출물을 그대로 TG 전송 | QA |

**한 줄:** 웹진이 깨진 게 아니라 **(1) 인트로 폰트 경로 실패 + (2) 녹화 헤드 블랙 프레임 + (3) 무검증 배포**다.

---

## 4. 왜 재발했는가 (프로세스)

- “일단 나오게” MVP를 TG까지 밀어붙임
- Intro를 웹 렌더가 아닌 **drawtext 숏컷**으로 처리
- Shoot을 **로드 완료 계약** 없이 녹화
- **품질 게이트(만점 체크리스트)** 없이 배달

---

## 5. 재발 방지 대책 (구현 의무)

| ID | 대책 | 검증 |
|----|------|------|
| C1 | Intro = **HTML → Playwright 스크린샷 → mp4** (시스템 CJK 폰트 / Noto) | 인트로 PNG에 한글 글리프 존재 |
| C2 | Shoot: `load` + `document.fonts.ready` + 커버 셀렉터 visible 후 **준비 완료 플래그** | 블랙 검출 길이 < 0.4s 또는 트리밍 |
| C3 | Edit: `blackdetect`로 **선두 검정 자동 트림** | 최종 첫 프레임 평균 휘도 게이트 |
| C4 | Writer: beat 나레이션 **글자/초 상한** (커버 과장 금지) | beat audio ≤ 12s 권장 |
| C5 | `quality_gate.py` 실패 시 **TG 전송 금지·exit 2** | CI/로컬 동일 |
| C6 | 재발일지 + `director/QUALITY.md` 체크리스트 상시 | 문서 |

---

## 6. 완료 정의 (DoD · 만점)

- [ ] 인트로 한글 깨짐 0
- [ ] 최종 mp4 첫 0.5s 검정 비율 < 5% (또는 의미 있는 픽셀 존재)
- [ ] Scout 셀렉터로 아코디언/섹션 클릭 최소 1회 이상 성공 로그
- [ ] TTS·화면 길이 싱크 (shortest 전 audio/video 차이 리포트)
- [ ] TG 전송 전 quality_gate PASS 로그

---

## 7. 관련 파일

- `helena-programming/director/run_director.py`
- `helena-programming/director/scout.py`
- `helena-programming/director/intro.py` (신설)
- `helena-programming/director/quality.py` (신설)
- `helena-programming/director/QUALITY.md`

---

## 8. 2차 — 자체 파싱 단점 (PRO 산출 재감사)

게이트 PASS여도 하이테크 튜토리얼 기준으로는 부족했던 점:

| 단점 | 보완 (tutorial_v1) |
|------|-------------------|
| 클릭이 눈에 안 띔 | `overlays.js` 커서 이동+펄스 |
| optional 클릭 스킵 | optional 금지 + min 4 성공 클릭 |
| 멘트 템플릿 반복 | forbid_phrases |
| LLM 자유 연출 | `policy` + `enforce` 단계 게이트 |
| ship 전 증거 없음 | `actions_log.json` 필수 |

**MCP:** 강제 수단의 필수는 아님. 결정론 정책 파일이 본체. MCP는 툴 래퍼 단계.

## 9. 3차 — PRO v2 가짜 SHIP PASS (2026-08-01)

| 단점 | 보완 (pro_v3) |
|------|----------------|
| 클릭 후 링 즉시 소멸 | holdFocus for full beat |
| expand-all로 클릭 무효과 | collapse-first |
| gold/teal 게이트 없음 | visual_proof + G7 |
| PNG 필터 미해독 | png_decode_rgb |

상세: `_notebook/50-director-pro-v3-visual-proof_Grok.md`

## 10. 서명

- 분석·대책·구현: **_Grok** (2026-07-31)
- v3 visual proof: **_Grok** (2026-08-01)
- Boss 검수: _대기_
