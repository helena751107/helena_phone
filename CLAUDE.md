# S21 Phone — 로봇 친구들 사용 설명서

> ⚠️ **일 시작하기 전에 꼭 `CONSTITUTION.md` (규칙책) 먼저 읽기!**
> 규칙책에는 "우리가 왜 이 일을 하는지"가 적혀 있어. 이 설명서는 "어떻게 하는지"를 알려주는 거야.
> 목적·불변 원칙·신원 규칙은 CONSTITUTION.md에, 작업 방법은 여기에.

---

## 🚨 ParksyTTS on S21 — 일 시작할 때 꼭 읽기! (2026-08-07~)

### 우리 컴퓨터(환경)
- **실행 위치:** proot Ubuntu on Galaxy S21 (aarch64), WSL 아님
- **텔레그램:** `.secrets.env`에 TG_TOKEN/TG_CHAT 있음, 5개 봇 활성
- **모델:** parksy_v2 checkpoints 314MB 전부 로컬에 있음 (`/root/work/helena-programming/tools/voice/`)
- **TTS_ENGINE 기본값 = `local`** (grok은 폴백, 현재 403 상태라 무의미)
- **추론 현실:** GPT-SoVITS semantic token prediction on CPU → 1500 iters, ~3s/it, 총 471초(7분51초) for 3.5초 음성. 실시간 대비 135배 느림.

> 쉽게 말하면: 우리 폰에서 목소리 만드는 작업은 엄청 느려. 3.5초짜리 목소리 하나 만드는 데 7분 51초나 걸려!

### 지금 하고 있는 일 — NPU/GPU 가속 (2026-08-11 갱신)
- **CPU-only 한계 확인됨.** ParksyTTS 추론 471초는 실사용 불가.
- **GPU (Mali-G78 MP14):** `/dev/mali0` 존재, OpenCL lib 있음. proot(glibc) → bionic ABI 불일치로 직통 불가.
- **NPU (Exynos 2100, 26 TOPS):** ENPU 런타임 전체 존재. NNAPI HAL 1.3 + EDEN 드라이버 정의됨.
- **핵심 발견 — Termux가 열쇠 (2026-08-11 정정):**
  - 이전 기록 "sysfs permission 문제" → **틀림**. 실제 원인은 **glibc/bionic ABI 불일치**.
  - proot(glibc)에서는 `libneuralnetworks.so`(bionic)를 dlopen할 수 없음. 권한이 아니라 링킹 문제.
  - Termux는 `untrusted_app` SELinux 도메인으로 실행 → 일반 앱과 동일한 NDK API(NNAPI 포함) 접근 가능. **루팅 불필요.**
  - sherpa-onnx NNAPI: **STT 근거 충분** (Pixel 6 벤치마크 RTF 0.035, sherpa-onnx 공식) — ⚠️ **S21 실측은 아직 안 함**. **TTS는 모델별 실패 사례** 있음 (Piper 텐서 차원 불일치 이슈).
- **단기 전략 (2026-08-11 재정정):**
  - ❌ ~~`pip install sherpa-onnx` → NNAPI~~ — **불가능**. PyPI wheel은 `manylinux2014_aarch64`(glibc) 전용, NNAPI 프로바이더 미포함.
  - ✅ **실제 경로:** Termux에 Android NDK 설치 → `build-android-arm64-v8a.sh`로 크로스컴파일 (`-DANDROID_PLATFORM=android-27` → NNAPI 활성화)
  - 결과물: `install/bin/sherpa-onnx` CLI 바이너리 + `libonnxruntime.so`(NNAPI 포함) + `libsherpa-onnx-jni.so`
  - VoxSherpa(TTS 앱) 선례: Kokoro=CPU/NNAPI, Piper/VITS=CPU only — TTS 모델별 NNAPI 호환성 차이 확인됨
  - proot → localhost HTTP 브릿지로 CLI 바이너리 호출
- **TTS 리스크:** ParksyTTS가 쓰는 구체적 TTS 아키텍처가 NNAPI에서 실제로 돌아가는지는 실기기 테스트로만 확인 가능. **STT도 S21 실측은 아직 — Pixel 6 벤치마크 근거만 있음.** TTS는 미확정.

> 우리 폰 안에는 AI 계산기(NPU, 26 TOPS)와 그림 그리는 부품(GPU, Mali-G78)이 모두 있어!
> 근데 proot은 glibc 언어를 쓰고 안드로이드는 bionic 언어를 써서 서로 말이 안 통해.
> Termux는 bionic 언어를 네이티브로 쓰니까 안드로이드랑 바로 대화할 수 있어.
> 그래서 "Termux에서 NDK로 AI 두뇌(sherpa-onnx)를 직접 컴파일하고, NNAPI 가속 넣어서 CLI로 실행" 전략!
> pip install로는 안 돼 — PyPI에 올라온 건 glibc용이라 Termux(bionic)랑 안 맞고 NNAPI도 없어.
> NDK로 직접 빌드해야 진짜 NNAPI가 붙은 바이너리가 나와.

### 이미 해결된 것 — 다시 건드리지 말 것
- 한국어는 BERT 불필요 → 0-vector 처리, 코드 반영 완료
- numba/librosa ARM64 크래시 → soundfile로 의존성 자체 제거
- torchcodec 누락 → 설치 완료 (`0.15.0+cu130`, `--break-system-packages`)
- Grok TTS API 403 → SuperGrok 구독에 TTS 미포함, local 전용으로 전환 완료

> 이 네 가지는 이미 고친 문제들이야. 다시 파헤치지 마!

### 오늘 세션 이슈 (2026-08-07)
- **세션 2회 이상 끊김.** 장시간 추론(ParksyTTS 7분+) 중 타임아웃 가능성.
- 장시간 CPU 작업 시 중간 체크포인트 저장하거나 watchdog ping 유지할 것.
- PD Pipeline v2 마이그레이션 코드는 완성 → uncommitted 상태 (아래 "이번 세션 TODO" 참고).

> 오늘 컴퓨터가 두 번이나 꺼졌어. 오래 걸리는 작업 할 때는 중간중간 저장해두자!

---

## 작업 원칙 — 우리가 일하는 방법

- **커밋 자주, 작게**: 기능 단위로 쪼개서 커밋
- **설명 남겨라**: "왜"를 커밋 메시지에 포함
- **깨져도 괜찮다**: 트랙 2(소망)에 한함. 트랙 1(돌봄)은 절대 안 깨지는 게 유일한 기준.
- **스캐폴드 우선**: 일단 작동, 나중에 개선. Grok 80% 드래프트 → Claude Code 100% 완성.

> 알기 쉽게:
> - **커밋은 작게, 자주!** 레고 블록 하나하나 쌓듯이. 한 번에 왕창 쌓으면 무너져.
> - **왜 바꿨는지 메모 남기기!** 나중에 "이거 왜 했더라?" 하고 헷갈리지 않게.
> - **놀이(소망)는 망가져도 괜찮아.** 하지만 엄마 심부름(돌봄)은 절대 망가지면 안 돼!
> - **대충 뼈대 먼저 만들기!** 그림 로봇(Grok)이 80% 그리고 → 글짓기 로봇(Claude Code)이 100% 완성.

## Git 작업 — 무료 전시장(GitHub)에 작품 올리는 법

- 작업 전 `git pull`로 최신 상태 확인
- 커밋 메시지는 한글/영문 혼용 가능, 간결하게
- `git push --force`는 원격이 로컬보다 뒤처진 게 확실할 때만. 함부로 쓰지 말 것.
- 완료 후 `git push` 자동 실행

> **무료 전시장(GitHub)**에 우리 작품을 올리는 방법이야:
> - 작업 시작할 땐 `git pull`로 "혹시 다른 로봇이 먼저 올린 거 있어?" 확인부터.
> - 커밋 메시지는 짧고 명확하게. 한국말+영어 섞어도 OK.
> - `git push --force`는 **벽돌로 내리치는 거랑 똑같아!** 정말 내 작업이 최신인 게 확실할 때만 써.

## AI 에이전트 4종 — 우리 팀 로봇 친구들! (Boss 2026-07-26, 확장 2026-08-08, 기점 2026-08-14)

> **가치 = 돌봄 (누나 S21).** **일 = 출판·미디어 인프라.**  
> Grok은 플러그 두 칸만 — 기점 `_notebook/83-momentum-2026-08-14_Grok.md`.

| 호출 | 마크 | 직함 | 영역 | 비용 | 설치 |
|------|------|------|------|------|------|
| `grok` / `gr` | **`_Grok`** | **잡지 구도 디자이너 · 다큐 PD** | ① 사진+잡지 구도→웹 디자인+이미지 ② 딥페이크급 10초 PD 다큐 | $30/월 | ✅ |
| `ds` / `dsflash` | **`_Aider`** | **작업 반장** | 패치 큐·디프·반복 시공·실행 감독 | DeepSeek 포함 | ✅ |
| `cc` (출판부) | **`_Claude`** | **출판부 · 번역 수호자** | md→html 변환·커버리지·품질 게이트·CI 검증 | 정책에 따름 | ✅ |
| `cc` (감사) | **`_Claude`** | **감사** | 거리 둔 검증·보안·헌법·통과/보류/반려 | 정책에 따름 | ⏳ 미설치 |

**파이프:** Boss 방향 → `_Grok` 칸① 웹 / 칸② 다큐 → `_Aider` 시공 → `_Claude`(출판부) 변환·게이트 → `_Claude`(감사) 검증(있을 때) → Boss 최종.  
**상세:** `_notebook/83-momentum-2026-08-14_Grok.md` · `_notebook/31-agent-roles_Grok.md` · 출판부: `_notebook/75-translation-logic-management_Claude.md` · 마크 규약: `30-agent-file-marks.md`

> Termux: `grok` / `groklogin` / `grokc` / `agent` · `ds`는 `scripts/ds.sh` 래퍼.  
> 예전 `gr`/`grlogin`/`grc` 호환 유지.

> 우리 팀엔 네 명의 로봇 친구가 있어! 마치 축구팀 같아:
> - **그림·PD 로봇 (Grok, `gr`):** 비싼 요금제가 프로처럼 잘하는 건 둘뿐. 사진에 잡지 구도를 주면 웹 디자인하고 그 이미지를 만들거나, 딥페이크 같은 PD 영상을 만들어. 월 $30.
> - **고치기 로봇 (Aider, `ds`):** 고장 수리 전문가! 코드 깨진 거 고치고, 반복 작업 척척 해내.
> - **글짓기 로봇 (Claude Code, `cc` 출판부):** 번역 지킴이! 우리가 쓴 글을 웹페이지(HTML)로 예쁘게 바꿔줘. 검사도 하고.
> - **심판 로봇 (Claude Code, `cc` 감사):** 규칙 잘 지켰는지 확인하는 심판! 아직 오진 않았어(⏳).
>
> **일하는 순서:** Boss가 방향 정하기 → 그림·PD 로봇이 칸에 맞는 일만 → 고치기 로봇이 뚝딱 → 글짓기 로봇이 예쁘게 변환·검사 → (심판 로봇 확인) → Boss 최종!

## AI 에이전트 규칙 — 로봇 친구들 지키기 약속

- 세션 시작 시 CONSTITUTION.md → CLAUDE.md → 기점 `83-momentum-2026-08-14_Grok.md` → (역할) `31-agent-roles_Grok.md` 순
- AI 출력은 전부 1차 가설 — 검증 없이 수용하지 말 것
- **AI 출력 = 기술적 관성.** 보고서·코드는 학습한 표준 패턴을 따라 그럴싸하게 자동생성한 것. "전부/완료/검증됨"은 내가 다시 세어서 확인(오늘 63→실제 67/68 사건). 통제권·의구심은 Boss 손에 — AI는 귀찮은 작업 대행용 일꾼일 뿐
- **Grok은 잡지 구도 이미지·딥페이크 PD 두 칸만, 반장은 패치, 출판부는 전시장 게이트, 감사는 「아니다」** — 직함 침범 최소화
- Claude가 아직 없으면 감사 간이 게이트는 **Boss**
- 모든 설정 변경 전후로 기록을 남길 것 (`*_Grok` / `*_Aider` / `*_Claude`)

> 로봇 친구들과 일할 때 지킬 약속:
> - 일 시작할 땐 **규칙책(CONSTITUTION.md) 먼저!** 그다음 이 설명서, 그다음 각자 맡은 역할 설명서.
> - 로봇이 하는 말은 **100% 정답이 아니야.** 꼭 내가 다시 확인하기!
> - **그림·PD 로봇은 잡지 구도 이미지와 딥페이크 다큐 두 칸만, 고치기 로봇은 수리, 심판은 "안 돼!"** — 서로 자기 일만 하기.
> - 심판 로봇이 아직 없으면 **Boss가 대신 심판 본다.**
> - 설정 바꾸면 **꼭 메모 남기기!** 누가 했는지 파일 이름에 표시 (`_Grok` / `_Aider` / `_Claude`).

## 텔레그램 보고 의무 — 무전기로 상황 알리기

작업 완료 후 보고가 필요하면:
```bash
bash ~/work/tg.sh '✅ 작업명 — 결과'
```

> 일이 끝나면 **무전기(Telegram)**로 짧게 상황 보고! 위 명령어를 그대로 따라 치면 돼.

## 건강 검진 의무 — 우리 폰 건강 검사

- 세션 시작 시 또는 하드웨어 관련 작업 전후 `bash ~/work/phone-health.sh` 실행
- 결과는 자동으로 `_notebook/health/`에 타임스탬프 저장
- --telegram 플래그로 채팅 보고 가능
- 등급 A 이하(Grade B/C)면 점검 항목 확인 후 조치

> 아침에 일어나면 건강 검진 받듯이, 우리 폰도 **일 시작할 때 건강 검사** 받아야 해!
> `bash ~/work/phone-health.sh` 한 줄이면 끝.
> - 결과는 `_notebook/health/` 폴더에 자동 저장.
> - 등급이 A가 아니면? 어디가 아픈지 확인하고 고쳐야 해.

## 업무일지 — 오늘 있었던 일 기록

- 주요 작업, 판단, 전환점은 `_notebook/99-devlog.md`에 바텀업으로 기록
- AI와의 주요 대화 중 결정적 전환이 있었으면 요지 함께 기록
- 추후 `g/zero.sh`로 압축·정제 예정

> 마치 **일기장**처럼! 오늘 무슨 일 했는지, 중요한 결정은 뭐였는지 `_notebook/99-devlog.md`에 차곡차곡 쌓아. 나중에 `g/zero.sh`로 깔끔하게 정리할 거야.

## 에이전트 파일 마크 (필수 · 2026-07-26~) — 누가 쓴 글인지 표시하기

- 업무 수첩·세션 메모·단독 로그를 **새로 쓸 때** 파일명 접미 마크:
  - Grok → **`_Grok`** (예: `session-2026-07-26_Grok.md`)
  - Claude Code (`cc`) → **`_Claude`**
  - Aider (`ds`) → **`_Aider`**
  - 사람 → `_Boss` / 공용 규약 → `_Shared` 또는 번호 문서 유지
- 규약 전문: `_notebook/30-agent-file-marks.md`
- 공용 `99-devlog.md` 섹션을 추가할 때는 제목 끝에 `(_Grok)` / `(_Claude)` / `(_Aider)` 표기
- **다른 에이전트 마크 파일은 덮어쓰지 말 것** — 이어서 할 거면 자기 마크 신규 파일 + handoff 체크리스트

> 마치 **필통에 이름 쓰기**랑 똑같아! 누가 쓴 파일인지 파일 이름 뒤에 꼬리표를 붙여:
> - 그림 로봇이 쓴 글 → `_Grok`
> - 글짓기 로봇이 쓴 글 → `_Claude`
> - 고치기 로봇이 쓴 글 → `_Aider`
> - 보스가 쓴 글 → `_Boss`
>
> **절대 남의 파일에 낙서하지 마!** 이어서 쓰고 싶으면 내 이름으로 새 파일 만들어.

## 웹페이지 커버리지 (출판부 게이트 · 디자이너는 자기 페이지 · 2026-08-14~)

- **`_notebook/*.md` 는 반드시 `notebook/*.html` 웹페이지**가 있어야 한다.
- **게이트 소유는 출판부 `_Claude`.** Grok 칸 ①은 사진+잡지 구도 이미지다. 수첩을 새로 쓰면 그 페이지만:
  ```bash
  python3 scripts/check_webpages_Grok.py   # gap_count
  python3 scripts/build_webzine.py         # 전체 생성 + coverage JSON
  ```
- 인터랙티브 앱: `notebook/webpage-coverage.html`
- 역할 문서: `_notebook/33-webpage-coverage_Grok.md` · 기점: `_notebook/83-momentum-2026-08-14_Grok.md`
- 문서 페이지는 공통 **웹앱 UI**(검색·접기·펼치기·본문 복사) — `assets/webzine.js`

> 우리가 수첩(`_notebook/`)에 쓴 글은 모두 **무료 전시장(GitHub)에도 걸려야** 해!
> 전시장 문은 출판부가 잠근다(`gap_count > 0`이면 배포 금지).
> 그림·PD 로봇이 새 수첩을 쓰면 그 페이지만 직접 만들어. 명령어는 위 두 줄.
> 전시된 페이지는 검색도 되고 접고 펼 수도 있어!

## 출판부 (Publishing Department) — 번역 수호자 (2026-08-08~)

- **역할:** 모든 6개 레포의 md→HTML 변환 파이프라인 소유·관리
- **측정:** `python3 scripts/publishing_metrics.py` → `assets/publishing-metrics.json`
- **표준:** 페이지 작법 표준 `_notebook/76-page-writing-standard_Claude.md`
- **규칙:** 출판부 7규칙 `_notebook/75-translation-logic-management_Claude.md`
- **CI 게이트:** `gap_count > 0` → deploy 차단 (`.github/workflows/deploy-pages.yml`)
- **커밋 규약:** 빌드 결과 커밋 시 `translation:` 접두어

> **출판부**는 우리 글을 전시용 웹페이지로 바꿔주는 **번역팀**이야.
> - 원고(md)가 전시용(html)으로 제대로 바뀌었는지 항상 확인해.
> - 한 개라도 빠진 페이지가 있으면(`gap_count > 0`) 전시 금지! 문 잠겨!
> - 빌드 결과 저장할 땐 꼭 `translation:` 이라고 태그 붙이기.

## Paste Pipeline (네이버·티스토리 수동 발행) — 사람 손으로 옮겨 붙이기

- API 없는 플랫폼은 Paste Pipeline으로 대응:
  `Claude Code → TG 원고 배달 → 사람 복사붙여넣기 → 발행 (5분)`
- 티스토리 = 업무일지 (TG리포트 + git log + 스크린샷)
- 네이버 = 웹진·미끼 (Grok 80% 드래프트 → 주간 발행)

> 어떤 전시장(네이버, 티스토리)은 로봇이 직접 못 올려. 그래서 우리는 **복사해서 붙여넣기** 작전을 써!
> 1. 글짓기 로봇이 글 완성 → 2. 무전기(Telegram)로 보내줌 → 3. 사람이 복사+붙여넣기 → 4. 끝! (5분이면 돼)

## PD Pipeline (웹페이지 → 숏폼 영상) — V10 공짜 공장 (2026-08-08~)

> **2026-08-14 기점:** 이 공장은 **페이지 소개 레인**이다. Grok 플러그 칸 ②(누나 사진 1장 → 10초 딥페이크+더빙 → 다큐)와 **다른 일**이다.  
> 플러그 역할 원장: `_notebook/83-momentum-2026-08-14_Grok.md`

**목적:** URL 하나로 웹페이지를 "이해하고 소개하는" 숏폼 영상 자동 제작.
일반 숏폼 도구(템플릿 끼워맞추기)와 달리, **실제 페이지를 읽고 섹션별로 다른 화면을 캡처**한다.

**파이프라인 단계:**
| 단계 | 스크립트 | 하는 일 |
|------|----------|---------|
| **P0** | `_parse_url.py` | URL 로드 → DOM 파싱 → 제목/섹션/본문 추출 → beat 생성 + scroll_sel 부여 |
| **P0.5** | `_generate_vo.py` | beat별 caption+context → 한국어 내레이션 VO 초안 생성 |
| **P0.6** | `_direct_map.py` | VO 길이·역할 기반 zoom/color_tag/pause 연출 자동 결정 |
| **P1** | `produce_pd.sh` P1 | Playwright로 페이지 로드 → beat별 `scroll_sel`로 다른 섹션 스크롤 → viewport 캡처 |
| **P2** | `produce_pd.sh` P2 | Edge TTS (YuJinNeural)로 VO 음성 합성 |
| **P3** | `_bridge_pickup.sh` | Android 갤러리에서 bridge 영상 감지 |
| **P4** | `_render_video.py` | Ken Burns (zoom/pan) + color grade + soft overlay → xfade concat |
| **P4b** | `_make_ass.py` | CNN Breaking News 스타일 ASS 자막 (per-word scale pop) |
| **P4c** | ffmpeg | ASS 자막을 VO body에 burn-in |
| **P5** | `_pd_assemble.py` | Bridge 연결 + full-timeline BGM (sidechain ducking) |
| **P5b** | `_make_srt.py` | YouTube caption용 SRT 생성 (xfade timing 보정) |
| **P6** | ffmpeg + curl | 720p TG 인코딩 + @S21Phone_Bot 전송 |

**V10 시각 스타일:**
- 검은 막대(drawbox) 제거 → 하단 그라데이션 오버레이 (텍스트 가독성)
- 텍스트 박스 제거 → 그림자(shadow) + 테두리(border)로 교체
- 비네트 PI/5 → PI/8 (더 가볍게)
- color_tag `teal` 추가 (warm/gold/cool/cinematic/natural과 함께 6종)

**사용법:**
```bash
# MCP (권장):
# pd_parse_url(url="https://...") → pd_produce(ep_id="pd_xxx")

# CLI:
URL="https://페이지주소" EP=에피소드ID bash scripts/produce_pd.sh "$EP" "$URL"

# shot_bible 수동 작성 후 캡처만:
# shot_bible에 scroll_sel 필드 포함 → P1이 각 beat마다 다른 섹션 캡처
```

**핵심 차별점:**
- 일반 숏폼 도구 = 템플릿에 콘텐츠 끼워맞추기
- PD Pipeline V10 = **콘텐츠를 읽고 이해해서, 그 이해에 맞는 연출을 스스로 결정**
- P0가 채워지기 전까지는 "이해 없는 소개"였음 → V10부터 진짜 "독해와 편집 판단" 기반

> URL 하나만 주면 로봇이 알아서 페이지를 "읽고" 섹션별로 다른 화면을 찍어서 멋진 숏폼 영상을 만들어줘! P0 → P0.5 → P0.6 단계가 페이지 내용을 이해하고 연출을 결정하는 똑똑한 부분이야.

## 파일 구조 — 우리 집 지도

```
helena_phone/
├── CONSTITUTION.md  ← 헌법 (무엇을, 왜)
├── CLAUDE.md        ← 실무 규칙 (어떻게)
├── index.html       ← 랜딩 포털
├── _notebook/       ← 업무 수첩 (34종)
├── _textbook/       ← 완결판 교재
├── g/               ← install.sh
├── care/            ← 트랙1 돌봄 데몬
├── scripts/         ← 자동화 스크립트
├── configs/         ← 설정 파일
├── 01~05/           ← GUIDE.md 챕터
├── mcp-servers/     ← dtslib MCP
└── tistory-naver/   ← dtslib 블로그코드(보존)
```

> 이게 우리 집 구조야. 마치 집 안에 방마다 이름 붙이듯이:
> - **CONSTITUTION.md** = 규칙책 (왜 이 일을 하는지)
> - **CLAUDE.md** = 이 설명서 (어떻게 하는지)
> - **`_notebook/`** = 업무 수첩 보관함
> - **`scripts/`** = 자동으로 일하는 마법 주문 창고
> - **`care/`** = 엄마 심부름(돌봄) 감시 카메라
> - **`configs/`** = 설정 메모 보관함

## 현재 인프라 — 우리가 가진 도구들

```
📱 S21 (Android + Termux + proot Ubuntu)
├── Claude Code (DeepSeek) — 메인 코딩
├── Grok CLI (xAI SuperGrok) — 시각·Naver
├── Aider (DeepSeek) — 보조 코딩
├── phone-mcp-server (18 도구, 포트 3456)
├── 5개 GitHub 레포 → Pages + Giscus + WidgetBot
├── Discord S21 Phone 서버 (#로비, #ai-보고)
├── Telegram @S21Phone_Bot (tg.sh 보고)
├── 티스토리 5종 (수동 업무일지)
├── YouTube @helena_phone (OAuth 완료)
└── 네이버 helena1975 (웹진·미끼)
```

> 한눈에 보는 우리 작업실!
> - **S21 폰**: 우리 메인 컴퓨터. Termux+proot으로 우분투를 돌리고 있어.
> - **로봇 세 마리**: Claude Code(글짓기), Grok(그림), Aider(고치기)가 DeepSeek 두뇌로 일해.
> - **무료 전시장 5곳(GitHub)**: Pages로 웹페이지 보여주고, Giscus로 댓글도 달 수 있어.
> - **무전기(Telegram)**: @S21Phone_Bot으로 작업 보고.
> - **유튜브, 네이버, 티스토리**: 우리 작품 전시하는 여러 곳!
> - **Discord**: 로비랑 AI 보고방 있음.
> - **phone-mcp-server**: 18가지 도구, 포트 3456으로 연결.

## dtslib-papyrus 허브 — 뇌 (Boss·Claude Code·누나 3자 연결 · 2026-08-18~)

- **뭐:** `dtslib1979/dtslib-papyrus` (private) = **그룹 뇌**. 28레포(1 hub + 27 위성)의 SSOT.
- **연결 3자:** 나(Boss·운영) ↔ 너(Claude Code·실행) ↔ 누나(돌봄·read-only).
- **흐름 3줄:**
  1. 누나 → 허브: 돌봄 하트비트(health·JOURNAL) — **읽기 전용, 제어 금지**(헌법 트랙1)
  2. Boss → 허브 → 나: 방향·팬딩(`PENDING-ISSUES.md`) — 세션 시작 때 pull
  3. 나 → 허브: 작업 일지·빌드 상태 — 세션 끝에 push
- **원칙:** 미러(랩) → 재수정(뇌) → 선물(양산) 한 방향. 시크릿은 `.secrets.env`(gitignored)만, 레포엔 template만. 상주 데몬 없이(on-demand + cron).
- **SSOT:** `configs/ecosystem.json.template` + `scripts/load_ecosystem.py` — 계정·디바이스·레포 매핑(4계정4세계)은 여기서 읽음.

> **허브**는 우리 셋을 잇는 **뇌**야. Boss가 방향을 정하고, Claude Code가 S21에서 일하고, 누나의 돌봄 상태가 허브로 흘러 들어와. 누나한테는 아무것도 내려보내지 않아 — 누나는 지켜보기만 해.

## GEO 원조 스탬프 — 정체 인식 출판 파이프라인 (헌법 제17조 · 2026-08-17~)

- **본질:** 사람 눈(텍스트)과 기계 눈(JSON-LD/canonical/sitemap) **둘 다**에 "원조 = GitHub" 좌표를 새기는 것. 사람이 검색 안 하고 AI한테 묻는 시대 → 크롤링 미끼를 전역에 뿌려두고 "원조가 GitHub"라고 답하게.
- **파운드리 스탬프(핵심):** `scripts/build_webzine.py`가 나오는 **모든 페이지** `<head>`에 canonical + JSON-LD 정체 그래프(`Person @id→GitHub #person` + `WebPage publisher/author→Person`)를 **자동 주입**. 유지비 0, 반복 작업 0.
- **정체는 변수:** `configs/ecosystem.json` → `identity` 블록(person_name·github_user·hub_repo·tagline·sameAs). 포크한 사람은 이거만 채우면 **자기 정체**로 자동 상속. 하드코딩 금지.
- **플랫폼별 위치(루트 소유권에 따라):**
  - GitHub Pages(루트 소유) = llms.txt / robots.txt / sitemap / JSON-LD / canonical 전부.
  - 티스토리·YouTube(남의 루트) = JSON-LD 정체 그래프 + "원조 · Origin" 텍스트 라인. (`apply_geold.py` / `yt_geo_origin.py`)
  - 네이버(남의 루트 + `<script>` 제거) = **텍스트 한정** 푸터 라인.
- **⚠️ 한계(정직 — 과장 금지):** JSON-LD는 **블록체인/등기 아님**(암호화·위변조방지·분산원장 없음). 법적 저작권도, 실시간 원조 판정도 아님. **정본 화살표 = 확률적 우위.** 진짜 해자는 퍼포먼스·진정성. "노출이 빨라진다"는 지금까지 가설 — **측정 루프**(Bing WMT AI 성과·GSC·AI 질의 스팟체크)로 증명할 것.
- **상세:** `_notebook/99-devlog.md` GEO 항목 · 메모리 `geo-llm-origin-protection`

## 2026-09-19 미니PC 핸드오프 (딥페이크 클라우드)

- 미니PC 쪽 딥페이크 MCP GitHub Actions 이식 개발 완료, 실제 성공 검증됨.
- 상세: /root/work/HANDOFF_DEEPFAKE_MCP_CLOUD_2026-09-19.md 참고.
