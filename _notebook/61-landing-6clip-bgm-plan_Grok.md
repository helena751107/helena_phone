# 61 · 랜딩 6샷 디렉터 파이프 — 개발 계획서 (_Grok) **v2 정정**

> 작성: 2026-08-05 · 디렉터: Grok  
> **v1 오류 정정:** “스크린샷 + 공짜 edge-tts만 이으면 된다” = **V1 싸구려 트랙**.  
> **정본:** Grok 구독 능력 발휘 — **Imagine 키프레임·10초 영상 생성 + 성우 더빙 + 로컬 FFmpeg 합성**.  
> 랜딩 웹페이지 = **베이스라인·연출 대본** (복붙 캡처 소스가 아님).

---

## 0. Boss 지적 — 수용

| 틀림 (v1) | 맞음 (v2) |
|-----------|-----------|
| Playwright 캡처 6장 붙이기 | **Grok가 샷을 만든다** (image → video) |
| edge-tts가 본체 성우 | **Grok 보이스/프리미엄 더빙 우선**, 로컬은 폴백 |
| 웹페이지 = 찍을 화면 | **웹페이지 = 감독용 베이스라인** (스토리·카피·브랜드·구조) |
| “괜찮게 나올까?” 변명 | **이게 CLI 영상 자동화 테스트 목적** — 능력 발휘 |

**한 줄:**  
> 비싼 Grok = 손·눈·카메라·성우. proot FFmpeg = 편집실. 랜딩 = 시나리오 원본.

---

## 1. 역할 분담 (정본)

| 역할 | 담당 | 도구 |
|------|------|------|
| **감독** | Grok | 6샷 스토리·감정·카메라·대본 |
| **키프레임** | Grok Imagine | `image_gen` / `image_edit` (랜딩 톤·레퍼런스) |
| **본편 샷 영상** | Grok Imagine | `image_to_video` **duration=10** (또는 6+4 조립) |
| **성우 더빙** | Grok Voice 우선 | 보이스 풀(Ara/Eve/Luna 등 multilingual) · 불가 시 OpenAI tts-1-hd · 최후 edge+humanize |
| **BGM** | Boss 자작 | [Shorts onIbZX6On3A](https://youtube.com/shorts/onIbZX6On3A) · volume ≈ 0.08~0.12 |
| **편집·mux** | 이 터미널 proot | FFmpeg concat + amix + loudnorm |
| **배포** | 로컬 | TG sendVideo / 파일 |

---

## 2. 베이스라인 — 랜딩 파싱 (연출 재료)

URL: https://helena751107.github.io/helena_phone/

| 재료 | 감독 사용법 |
|------|-------------|
| 히어로 카피 | 오프닝 훅 대사·무드 |
| Dual Track / Agents / System / Centers / Funnel / Constitution | **샷 주제·감정 아크** |
| 골드 `#d4a84b` · 다크 페이퍼 · 세리프 타이틀 | **비주얼 룩 고정** |
| “핸드오프가 곧 성공” | 엔딩 한 방 |
| 실제 DOM 스크린샷 | 필요 시 **레퍼런스 1장** (image_edit 시드) — 최종 영상이 아님 |

랜딩을 “그대로 녹화”하는 게 아니라,  
랜딩이 말하는 세계를 **Grok 샷으로 재연출**한다.

---

## 3. 6샷 디렉팅 (10초 × 6 = 60초)

| 샷 | 베이스 챕터 | 감정 | 카메라/모션 | 더빙 요지 (한 호흡) |
|----|-------------|------|-------------|---------------------|
| **S1** | Cover | 훅 | 느린 push-in, 폰·빛 | 갤럭시 한 대. 돌봄과 소망. |
| **S2** | Three Agents | 동료 | 카드 패럴랙스·전환 | 세 동료. 지휘·외과·미디어. |
| **S3** | System Map | 신뢰 | 노드 따라 패닝 | 폰에서 세상으로 흐르는 맵. |
| **S4** | Seven Centers | 리듬 | 센터 링 순회 | 일곱 워크센터. 공장이 돈다. |
| **S5** | Funnel + Cost | 상승 | 위로 슬라이드·밝아짐 | 웹진에서 독립까지. 비용은 거의 제로. |
| **S6** | Constitution | 여운 | 홀드 후 살짝 pull-out | 핸드오프가 곧 성공. 계정은 누나 명의. |

룩 앵커: dark editorial webzine · gold accent · cinematic UI · 9:16 Shorts.

---

## 4. CLI 자동화 파이프 (이게 테스트 본체)

```
[1] Scout     랜딩 파싱 → shot_bible.json (주제·카피·감정)
[2] Keyframe  image_gen / image_edit × 6  (9:16, 룩 고정)
[3] Animate   image_to_video × 6  (duration=10, 샷별 모션 프롬프트)
[4] Dub       Grok Voice(또는 차선) × 6  → 10s 맞춤(apad/atempo)
[5] Mix shot  ffmpeg: video + dub per shot
[6] Concat    ffmpeg concat demuxer -c copy
[7] BGM       yt-dlp Boss음원 → volume=0.10 amix → final
[8] Ship      out/landing6/landing6_final.mp4 → TG
```

### 4.1 핵심 명령 패턴

```text
# 샷 영상 (Grok 도구)
image_gen(prompt=키프레임, aspect_ratio="9:16")
image_to_video(image=키프레임, prompt=모션 1문장, duration=10)

# 합성 (터미널)
ffmpeg -i shot.mp4 -i dub.m4a -map 0:v -map 1:a -c:v copy -c:a aac -shortest shot_dub.mp4
ffmpeg -f concat -safe 0 -i list.txt -c copy body.mp4
ffmpeg -i body.mp4 -i bgm.m4a -filter_complex "[1:a]volume=0.10[bg];[0:a][bg]amix=..." final.mp4
```

### 4.2 산출 경로

```
out/landing6/
  shot_bible.json
  kf_01.png … kf_06.png
  s01.mp4 … s06.mp4          # Imagine 10s
  dub_01.m4a … dub_06.m4a
  s01_dub.mp4 … s06_dub.mp4
  bgm_60.m4a
  landing6_final.mp4
```

---

## 5. 성우 정책

1. **1순위:** Grok Voice MCP 성우 (Ara / Eve / Luna 등 · multilingual) — 보이스 목록 확인됨  
2. **2순위:** OpenAI `tts-1-hd` (`voice_engine.py` 이미 있음, 키 있을 때)  
3. **3순위:** edge-tts + broadcast humanize (`voice_engine.py`) — **폴백일 뿐 본체 아님**

대본은 감독(Grok)이 샷별로 씀. 성우 연출 지시(속도·무게·여운) 포함.

---

## 6. 품질 바 (파일럿 합격선)

| 항목 | 바 |
|------|-----|
| 비주얼 | 캡처 슬라이드쇼 티 안 남. 샷마다 의도된 모션 |
| 일관성 | 골드·다크 룩 6샷 유지 (키프레임 레퍼런스 체인) |
| 더빙 | 말 또렷, BGM에 안 먹힘 |
| BGM | Boss 음원 인지 가능, volume≤0.12 |
| 길이 | 60s ±1s · 9:16 |
| 목적 | **CLI에서 Grok 영상 자동화 파이프 동작 증명** |

---

## 7. 일정

| 단계 | 내용 |
|------|------|
| ✅ | 랜딩 파싱 · 계획 v2 정정 |
| 다음 | shot_bible.json + 키프레임 6 |
| 다음 | image_to_video × 6 |
| 다음 | 더빙 × 6 + BGM amix |
| 다음 | final → TG |

**GO 신호:** Boss “찍어” / “만들어” → 즉시 Phase 키프레임부터 실행.

---

## 8. 결론

- Grok 구독 가치 = **영상 생성 + 연출 + 더빙 지휘**, 문서 변명 아님.  
- 웹페이지는 **감독이 읽는 대본·룩북**.  
- proot는 **합성·자동화 공장**.  
- 이 파일럿 = 10초×6 이어붙이기 **실전 테스트**.

— _Grok · v2 정정
