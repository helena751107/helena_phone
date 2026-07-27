---
date: 2026-07-27
agent: Grok
mark: _Grok
type: naver-lecture-intro
source:
  - 38-s21-voice-driven-analysis.md
  - 34-stt-zero-cost-justification.md
  - 37-free-runtime-planner-whitepaper_Grok.md
  - 33-hybrid-image-video-whitepaper.md
  - 36-project-planning-vs-helena_Grok.md
status: draft-for-naver
---

# [강의 시리즈 예고] 5년 된 갤럭시로 AI 플랫폼을 돌린다 — S21 Voice-Driven 입문

> 네이버 블로그용 **강의 소개글 + 강의 스크립트 골격**  
> 기초 문서: S21 Voice-Driven 실측 분석 · STT 0원 정당화 · 공짜 런타임 플래너 백서 · 이미지·영상 하이브리드  
> 형식: 강의 톤 · 중간 **이미지 프롬프트** · **영상 프롬프트** 삽입 (Grok Imagine / 쇼츠용)

---

## 메타 (발행 시 복붙)

| 항목 | 값 |
|------|-----|
| 제목 | 5년 된 S21로 AI를 돌린다 — 보이스 드리븐 플랫폼 강의 예고 |
| 카테고리 | IT·인터넷 / 생활 팁 / 자기계발 (택1) |
| 태그 | #S21 #Termux #STT #보이스드리븐 #중고폰AI #헬레나 #GitHubPages #Claude #Grok |
| 시리즈명 | **S21 Voice OS 입문** (가제) Vol.0 예고 |
| CTA | 댓글에 “1강 알림” / 저장해두기 / 유튜브·Pages 링크 |

**원문·인터랙티브 분석 (강의 교재):**  
https://helena751107.github.io/helena_phone/notebook/38-s21-voice-driven-analysis.html

---

## 네이버 본문 (강의 소개 + 스크립트)

### 🎬 오프닝 멘트 (15초 쇼츠 / 블로그 도입)

안녕하세요.  
오늘은 “최신 폰이 있어야 AI를 한다”는 말을 **실측으로 깨는** 이야기입니다.

2021년 갤럭시 S21, 중고 약 20만 원.  
RAM 8GB, 배터리 4,000mAh, 무게 169g.  
**NPU 없어요.** 로컬 거대 모델도 못 돌립니다.

그런데 이 폰으로  
**말 한마디 → 코드 → 문서 → 웹페이지 → 블로그·유튜브 파이프**  
까지 잇는 플랫폼을 굴리고 있습니다.

질문 하나만 남길게요.

> API가 일을 하는 세상에서도, 정말 최신 플래그십이 필요할까요?

---

### 🖼 이미지 프롬프트 01 — 썸네일 / 표지

```
Prompt (KO/EN mix OK for Grok Imagine):
Dark cinematic flat-lay of a worn Galaxy S21 on a black desk,
Termux green terminal glow reflecting on the glass screen,
small sticky note "20만 원", soft gold rim light, teal accent UI particles,
editorial product photo, 16:9, high detail, no watermark, no logo text clutter
Negative: cartoon, blurry, multiple phones, Apple device
```

**영상 프롬프트 01 — 오프닝 3초**
```
Slow push-in on Galaxy S21 screen lighting up Termux,
cursor blinking, ambient dark room, subtle dust motes,
soft whoosh SFX later, 9:16 vertical, 3 seconds, realistic
```

---

### 📚 이 강의 시리즈가 다루는 것 (커리큘럼 예고)

| 회차 | 제목 (가제) | 기초 문서 |
|------|-------------|-----------|
| **0 (오늘)** | 왜 S21인가 — 보이스 드리븐 적합성 | 38 Voice-Driven 분석 |
| 1 | 말 하나로 미디어를 짓는다 — STT 0원 스택 | 34 STT 정당화 |
| 2 | 공짜 런타임으로 플래너 돌리기 | 37 플래너 백서 |
| 3 | 프로젝트·콘텐츠·비즈니스 플랜이 한 레포에 | 36 비교표 |
| 4 | 이미지·영상은 드래프트(Grok)→마감(Comfy) | 33 하이브리드 백서 |
| 5 | 5개 레포 생태계 · 핸드오프(누나 명의) | 생태계 백서·헌법 |

오늘 글은 **0강 예고 + 핵심 논리**입니다.  
교재는 이미 웹에 올려 두었습니다. (위 링크)

---

### 🎓 강의 본론 ① — 실측 숫자로 말하기

(스크립트)

“스펙 자랑 말고 표부터 보시죠.  
이건 2026년 7월, SM-G991N 실측입니다.”

| 항목 | S21 실측 | 최신 플래그십 대비 감각 |
|------|----------|------------------------|
| CPU | Exynos 2100 | 느림 |
| RAM | 8GB | 절반 수준 |
| NPU | 없음 | 최신은 수십 TOPS |
| 무게 | **169g** | 플래그십은 더 무거움 |
| 중고가 | **~20만** | 최신 ~180만 (약 1/9) |
| 남는 저장 | 172GB | 실사용 충분 |

**강의 포인트:**  
보이스 드리븐의 주력은 **STT·LLM·API**입니다.  
로컬에서 무거운 모델을 안 돌리면, **네트워크·배터리·무게·가격**이 더 중요합니다.

---

### 🖼 이미지 프롬프트 02 — 비교 인포그래픽

```
Clean dark infographic split screen:
LEFT teal "S21" with icons: light weight 169g, 20만원, WiFi, battery,
RIGHT red "S26 Ultra" with icons: NPU chip, heavier phone, 180만원,
center bold Korean text "API가 같으면?", minimal Swiss editorial style,
4K, sharp, blog header 1200x630
```

**영상 프롬프트 02 — 비교 슬라이드 5초**
```
Animated bar chart S21 vs flagship:
bars for portability and cost grow for S21,
NPU bar empty on S21, full on flagship,
smooth motion graphics, dark UI, 5 seconds, 16:9
```

---

### 🎓 강의 본론 ② — 보이스 드리븐의 역설

(스크립트)

“여기가 핵심입니다. 메모해 두세요.”

> **역설:** API 호출이 주력이면, 로컬 성능보다  
> **네트워크 · 배터리 · 휴대성**이 엔진이다.

| 항목 | S21 | 최신폰 | Voice에 중요한가 |
|------|-----|--------|------------------|
| API 속도 | 동일(클라우드) | 동일 | 무관 |
| STT 정확도 | 동일(클라우드) | 동일 | 무관 |
| 휴대성 169g | 우위 | 무거움 | **중요** |
| 비용 | 압도적 우위 | 고가 | **중요** |
| 수리 | 쉬움 | 어려움 | **중요** |
| 온디바이스 LLM | 불가 | 가능 | API로 대체 가능 |

**결론 한 줄 (칠판에 쓸 문장):**  
**「중고 플래그십 + 클라우드 에이전트 = 보이스 OS 엔진」**

---

### 🖼 이미지 프롬프트 03 — 역설 칠판

```
Chalkboard style dark classroom,
Korean chalk text: "보이스 드리븐의 역설"
and "네트워크 · 배터리 · 휴대성",
small S21 sketch in corner, warm tungsten light,
cinematic still, 3:2
```

**영상 프롬프트 03 — 손 필기 느낌 4초**
```
Top-down hand writing Korean on black tablet with stylus,
text appears: "API 주력이면 구형도 엔진",
soft desk lamp, ASMR-like quiet, 4 seconds, 9:16
```

---

### 🎓 강의 본론 ③ — 입·뇌·손 스택 (0원 런타임)

(스크립트)

“장비가 아니라 **흐름**입니다.”

```
입  STT 음성 → 클립보드 → Termux
뇌  Claude Code · Grok · Aider  (분업)
손  GitHub · Pages · YouTube · Naver · TG · Discord
```

- 코딩·문서·git → 코드 레인  
- 이미지·네이버 드래프트 → Grok 레인  
- 반복 패치 → Aider 레인  
- 호스팅 대부분 **$0**  
- 유료는 보통 **구독 1개 수준** (토큰 지옥 대신 월정액 설계)

이건 강의 2강·3강에서 플래너 백서로 깊게 갑니다.  
오늘은 “가능하냐?”에 **예, 증거 있다**만 심으면 됩니다.

---

### 🖼 이미지 프롬프트 04 — 스택 다이어그램

```
Vertical flowchart infographic dark mode:
Mouth icon → Android STT → Termux terminal →
three agent cards (code / vision / patch) →
platform row GitHub Pages YouTube Naver Telegram,
teal and gold accents, clean Korean labels, 1080x1920 story size
```

**영상 프롬프트 04 — 흐름 애니메이션 6초**
```
Motion graphics: glowing particle travels mouth → phone → cloud agents →
websites lighting up one by one, futuristic but warm, 6s, 9:16
```

---

### 🎓 강의 본론 ④ — 다른 디바이스와 비교 (왜 폰인가)

| 디바이스 | 말하기 | 풀스택 운영 | 평결 |
|----------|--------|-------------|------|
| S21+Termux | ✅ | ✅ | **올인원** |
| 라즈베리파이 | 마이크 추가 | 서버 쪽 | 서버 전용 |
| 스마트 스피커 | ✅ | ❌ | 입력만 |
| 저가 노트북 | ✅ | ✅ | 무겁고 비쌈 |

**멘트:**  
“스피커처럼 말하고, 노트북처럼 배포하는 폼팩터.  
그게 이 시리즈가 폰을 붙잡는 이유입니다.”

---

### 🖼 이미지 프롬프트 05 — 폼팩터 비교

```
Five devices silhouette line-up on dark gradient:
S21 highlighted in gold glow, Pi, smart speaker, laptop, tablet,
label under S21 in Korean "올인원", others muted gray, minimal poster
```

**영상 프롬프트 05 — 디바이스 탭 3초**
```
Quick cuts: hand holding light phone speaking,
vs heavy laptop on desk,
caption pop "169g", upbeat but calm, 3s, 9:16
```

---

### 🎓 강의 본론 ⑤ — 한계도 정직하게 (신뢰)

(스크립트)

“광고 아닙니다. 한계도 말합니다.”

- NPU 없음 → 로컬 LLM 대신 **API**  
- 배터리 노화 → 교체 5~8만, 화면 장시간 녹화는 부담  
- 발열 → Playwright 장시간 시 쓰로틀  
- 6.2" → 코드 리뷰는 덱스·외부 모니터  
- WiFi 6 → 4K 장시간 업로드는 체감 차이  

**멘트:**  
“완벽한 폰이 아니라, **이 제약 안에서의 최적 엔진**입니다.”

---

### 🖼 이미지 프롬프트 06 — 한계 카드

```
Dark UI cards layout titled "한계와 우회",
four cards: No NPU→API, Battery→replace, Heat→throttle note,
Small screen→DeX, flat design, coral warning accents, Korean text clear
```

---

### 🎓 클로징 — 시리즈 약속 · CTA

(스크립트)

“다음 강의에서는  
말 한마디로 미디어를 짓는 **STT 풀스택**을 깔아 보겠습니다.  
설치 한 줄, 에이전트 셋, 공짜 런타임.

오늘은 이 문장만 가져가세요.”

> **보이스 드리븐에는, 구형 플래그십이 오히려 맞을 수 있다.**  
> 증거는 스펙표가 아니라 **돌아가는 플랫폼**이다.

**CTA**
1. 이 글 저장  
2. 교재 페이지 열어보기 (링크)  
3. 댓글: `1강` 이라고 남겨 주시면 시리즈 알림 기준으로 씁니다  

교재(인터랙티브):  
https://helena751107.github.io/helena_phone/notebook/38-s21-voice-driven-analysis.html  

허브:  
https://helena751107.github.io/helena_phone/

---

### 🖼 이미지 프롬프트 07 — 엔딩 카드

```
End card dark gradient, Korean text:
"5년 된 폰으로 AI 플랫폼을 돌린다"
subtitle "S21 Voice OS 입문 · Vol.0",
small S21 outline, gold and teal, clean YouTube end-screen safe margins
```

**영상 프롬프트 07 — 엔드 5초**
```
Logo-style text fade in, soft ambient music bed,
URL appears at bottom, hold 5 seconds, 16:9 and 9:16 versions
```

---

## 강의 촬영용 원테이크 스크립트 (3분 요약)

1. (0:00) 썸네일 질문 — 최신폰 필수?  
2. (0:20) S21 실측 숫자 3개: 20만, 169g, NPU 없음  
3. (0:50) 역설 칠판: 네트워크·배터리·휴대성  
4. (1:30) 입·뇌·손 스택 한 장  
5. (2:10) 한계 정직 고지 15초  
6. (2:30) 시리즈 예고 + 교재 URL  
7. (2:50) CTA 댓글 `1강`

---

## 제작 체크리스트 (Paste Pipeline)

- [ ] 이미지 01~07 Grok Imagine 생성 → 네이버 본문 배치  
- [ ] 쇼츠용 01,03,04,05 세로 렌더  
- [ ] 본문 복붙 (이 md § 네이버 본문)  
- [ ] 링크 2개 확인  
- [ ] 발행 후 TG로 URL 보고  

---

*강의 시리즈 예고 원고 · 기초: 38 Voice 분석 + 34 STT + 37 플래너 + 33 하이브리드 + 36 비교*  
*agent: **_Grok** · 2026-07-27*
