# 📋 PD Grok · 업무 수첩 종합 리포트 (1장)

> **일시:** 2026-08-06 · 에이전트: **_Grok (PD · GPU 대용 · 80% 프로 마감)**  
> **환경:** S21 → Termux → proot Ubuntu · helena_phone  
> **대상:** Boss (헬레나)  
> **헬스:** Grade **B** · 배터리 ~64% · 통과 26 / 경고 3 / 실패 1  
> **정본 파이프:** `configs/video_pd_pipeline_CURRENT.json` → **v2 LOCK**

---

## 0. 한 줄 정체성 (지금 나)

| 항목 | 값 |
|------|-----|
| **직함** | 디자이너 + **PD** (프로듀서·디렉터) |
| **역할** | 성우(Ara) · 브릿지 소수 · 샷 바이블 · 톤 · 웹진 · 커버리지 |
| **안 하는 것** | 페이지 전편 재래스터 · 무한 패치 루프 · 트랙1 돌봄 최종 판단 |
| **품질 목표** | **80% 프로 마감** (V2 Grok 구독 레인 = GPU 대용) |
| **엔트리** | `bash scripts/produce_pd.sh [ep] [url]` |

**정본 분담 (66·72 LOCK)**  
공장(공짜) = Playwright + FFmpeg · Grok = PD + 성우 + 브릿지 소수 · Edge TTS 금지(수익화·채널 안전).

---

## 1. 수첩 전체 지도 (`*_Grok` 40종 · ~4.9k lines)

### A. 조직·역할·커버리지 (기반)

| # | 파일 | 요지 |
|---|------|------|
| 31 | agent-roles | 디자이너 / 반장 / 감사 직함 |
| 33 | webpage-coverage | md↔html 갭 가디언 (상시) |
| 36 | project-planning-vs-helena | 일반 PM vs 헬레나 비교 |
| 37 | free-runtime-planner 백서 | 공짜 런타임 풀스택 플래너 |
| 38 | web-designer-workpad | 5레포 디자이너 현황판 |
| — | session-2026-07-26 | 웹진·아이콘·행정 톤 세션 |

### B. 콘텐츠·네이버·교육 (소망 트랙)

| # | 파일 | 요지 |
|---|------|------|
| 39 | naver-lecture-s21-voice-intro | 강의 시리즈 예고 + 프롬프트 |
| 40 | lecture-draft Vol.0 | 칠판+대본 12–15분 초안 |
| 41 | beginner-install-manual | 초심자 3화면 설치 |
| 42 | marine-quilt-naver-design | 해병대+퀼트 네이버 톤 패키지 |
| 44 | naver-admin-automation-review | 자동화 가능/쓰레기 분리 |
| 45 | naver-admin-playwright-feasibility | 폰 Playwright 1회 시드 YES |

### C. Director 전쟁 · 영상 사다리 (48→61)

| # | 파일 | 요지 |
|---|------|------|
| 48 | director-video-recurrence | 토푸·검정 재발 → QA 게이트 필요 |
| 49 | community-research | 프로 제품 수준 리서치 |
| 50 | pro-v3 visual-proof | Visual Proof 강제 |
| 51 | scout-v2 | ARIA Planner급 Scout |
| 52 | vision-qa-loop | Vision QA 만점 루프 |
| 53 | plan-settings | Plan First 연출 설정 |
| 54 | pro-v5 five-act | 5막 shoot |
| 55 | pro-v6 perfect | 만점 솔루션 |
| 56 | perfect-ship-process | L0–L9 사다리 코드화 |
| 57 | community-a-bar | A− 바 구현 |
| 58 | **video-three-tracks** | **V1 PPT / V2 Grok / V3 ComfyUI** |
| 59 | grok-video-process 백서 | 제품 투어 프로세스 정본 |
| 60 | pro-v8 wish | 프로급 소원 풀이 |
| 61 | landing-6clip-bgm | 랜딩 6샷 + BGM 계획 |
| 61b | session-deepseek-cc | CC 세션 복구 메모 |

### D. 플러그인 → PD 표준 → LOCK (62→72) ★현재 전선

| # | 파일 | 요지 | 상태 |
|---|------|------|------|
| 62 | plugin-video-pipe | 공장 위 Grok stills+TTS 슬롯 | 기반 |
| 63 | video-plugin-standard-v1 | TTS-first·1080·xfade·KenBurns | v1 |
| 64 | process-80-squeeze | **80% 목표표** (I2V·live UI·ship_report) | 목표 |
| 65 | playable-encode-fix | moov/재생 깨짐 수정 | 수정 |
| 66 | **pd-voice-bridge** | **역할 정정: 재래스터 금지** | 정본 |
| 67 | subscribe-voice-bgm-hurdle | 구독 이유 = Ara 성우+자작 BGM | 정본 |
| 68 | imagine-prompt-standard-v1 | 브릿지 스틸 산문 프롬프트 | v1 |
| 69a | session-resume-pd-bridge | bridge open/close WIN · TG 313 | 완료 |
| 69b | voice-engine-plugin-final | Edge 금지 · grok→openai→edge | 정본 |
| 70a | ai-voice-core-gift | 로컬 성우 선물/학습 로드맵 | (_Claude 협업) |
| 70b | font-bgm-fix | CJK 폰트 + BGM 0.025 전구간 | 수정 |
| 71 | pd-intro-v2-slide-black-fix | xfade 붕괴→**concat demuxer** | QA PASS |
| **72** | **pd-pipeline-standard-v2-lock** | **CURRENT=v2 · 매번 동일** | **LOCK** |

---

## 2. 지금 LOCK된 표준 (매번 이것만)

```bash
bash scripts/produce_pd.sh pd_intro
# 또는
BGM_VOLUME=0.025 TTS_ENGINE=grok bash scripts/produce_pd.sh <ep> <url>
```

| 상수 | 값 |
|------|-----|
| BGM 볼륨 | **0.025** (은은 · 자작/helena-piano) |
| 성우 | **grok / ara** |
| 해상도 | 1080×1920 yuv420p High |
| 조립 | **concat demuxer** (깨진 xfade 체인 금지) |
| 폰트 | Noto Sans/Serif **CJK KR** |
| 브릿지 | 앞·뒤 소수만 · 페이지 재래스터 금지 |
| SHIP 전 | `_qa_video_slides.py` **필수** (실패 시 TG 금지) |

**단계:** P0 bible → P1 stills → P2 Grok TTS → P3 bridge → P4 render+concat → P5 assemble+BGM → P5b QA → P6 TG

**스크립트 맵:** `produce_pd.sh` · `_render_video.py` · `_pd_assemble.py` · `_qa_video_slides.py` · `bridge_fx.sh`

---

## 3. 영상 3트랙 안에서의 위치 (58)

| 트랙 | 이름 | 엔진 | 지금 |
|------|------|------|------|
| V1 | PPT·리포트 | 공짜 공장 | 내부 기록용 |
| **V2** | **제품 투어·PD** | **Grok 구독 (GPU 대용)** | **← 여기 (80% 마감)** |
| V3 | 프로 시네마틱 | ComfyUI + GPU | PC 확장 포기 → 나중 |

→ Boss 설정: **나는 V2 전담 · 80%까지 쥐어짜기.**  
→ 90%+ 는 Vision QA 재생성 루프 · perfect_ship 커서 투어 병합 (64 아이디어 뱅크).

---

## 4. 최근 사고 → 교훈 (재발 금지)

1. **토푸 자막** — CJK 폰트 없으면 DejaVu → □□□ (48·70b)  
2. **블랙 테일** — xfade offset 붕괴 → 영상 끊기고 오디오만 (71) → concat demuxer  
3. **moov missing** — 파손 playable (65·69) → High 정규화 후 재조립  
4. **페이지 재래스터** — 토큰 낭비·품질 하락 (66) → 금지  
5. **Edge TTS** — 채널 리스크 (67·69b) → Ara 통일  
6. **BGM 구간 무음** — 북엔드 재믹스 누락 (70b) → full-timeline 0.025  

**게이트 없으면 TG로 쓰레기 나간다.** QA 필수.

---

## 5. 커버리지·인프라 스냅샷

| 항목 | 값 |
|------|-----|
| md / html | 94 / 93 (catalog 133) |
| **갭 (missing HTML)** | **4** — #70a #70b #71 #72 |
| orphan HTML | 2 (lecture-chalkboard, self-eval) |
| 위성 레포 HTTP | helena_phone·log·faith·piano 200 · metalcare 301 |
| TG / Discord | API 200 |
| 헬스 등급 | **B** (소수 기능 불량 — 점검 권장) |

---

## 6. 투트랙 헌법 정렬 (잊지 말 것)

- **트랙1 돌봄:** 절대 안 깨짐 · 비공개 · 지금 미착수 데몬 예정  
- **트랙2 소망:** 누나 명의 분신 콘텐츠 · 스캐폴드 우선 · **여기가 PD 레인**  
- **금지:** 돌봄 데이터 → 공개 채널 누수  
- **수익:** 누나 경제적 독립 기반 (대필작가-간병인)

---

## 7. 다음 액션 (PD Grok 큐)

- [ ] 갭 4건 HTML 빌드 (`build_webzine.py` / 개별 페이지)  
- [ ] 인덱스 `00-INDEX.md`에 62–73 반영  
- [ ] `pd_intro` v2 QA PASS본 기준 **다음 에피소드 동일 엔트리**로 반복  
- [ ] 80% 잔여: Imagine I2V 브릿지 비중↑ · live UI shot ≥2 · ship_report.json  
- [ ] Edge 경로 실사용 차단 재확인 (폴백만)  
- [ ] 헬스 Grade B 경고/실패 항목 점검  

---

## 8. Boss에게 한 줄

> 폰 안 `_notebook/*_Grok` **40장**을 훑었다.  
> 전선은 **#72 PD 표준 v2 LOCK** 이다.  
> 나는 **GPU 없는 V2 레인에서 성우·PD·브릿지로 80% 프로 마감** 한다.  
> 새 파이프 발명 금지 · `produce_pd.sh` 한 줄 · QA 통과 전 TG 금지.

— **_Grok · PD · 2026-08-06**
