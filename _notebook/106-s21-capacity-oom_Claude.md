# 106 · S21 연산 캐파 — 메모리 한계와 "하나씩" 규칙 (2026-09-29)

> 작성 `_Claude` (랩탑 에이전트, ADB·SSH 로 S21 실측) · 대상: S21 에이전트 · 박씨
> 박씨: "이거 헬레나 폰 레포지토리에다가 저장해. 나중에 이거 캐파도 확인해 줘야 될 것 같아."
> 상태: **사고 2건 확정 · 캐파 실측은 미착수 (§5 계획)**

---

## 1. 결론

- S21 은 **RVC 헬레나 더빙을 혼자서는 해낸다.** (실측 성공 3건)
- **무거운 작업을 동시에 돌리면 Termux 째로 죽는다.** (실측 사고 2건, 둘 다 `LOW_MEMORY`)
- 튜토리얼 MCP 주력 프로세스(칠판 → 헬레나 RVC → YouTube)는 **순서대로 하나씩**이면 가능성이 높다. 단 **캡처+합성까지 끝까지 돈 기록은 아직 없다.**

## 2. 기기 사양 (09-29 실측)

| 항목 | 값 |
|---|---|
| 모델 | Galaxy S21 (SM-G991N) · Tailscale `thomas-gall21` 100.99.4.125 |
| SoC | Exynos 2100 (8코어) · GPU 가속 없음 (ffmpeg `h264_nvenc` 불가 → `libx264` CPU 폴백) |
| RAM | 7.2 GB (MemTotal 7,373,752 kB) |
| 스왑 | 4.0 GB (평상시 이미 절반가량 사용) |
| 여유 메모리 관측 | 1.7 ~ 3.0 GB (Claude 세션 + 우분투 떠 있는 상태) |
| 실행 환경 | Termux → proot-distro Ubuntu 26.04 · Python 3.14 · Claude Code(DeepSeek v4-flash) · ubuntu 유저 |

## 3. 사고 기록 — 2건 모두 같은 원인

`adb shell dumpsys activity exit-info com.termux` (PC 쪽에서 확인):

```
2026-09-29 06:25:46  com.termux  reason=3 (LOW_MEMORY)
2026-09-29 06:42:57  com.termux  reason=3 (LOW_MEMORY)
```

| 사고 | 동시에 돌던 것 | 결과 |
|---|---|---|
| 06:25 | 헬레나 RVC 나레이션 + Playwright 크롬 캡처(preview) | Termux·우분투·Claude 세션·작업 전부 소멸, 산출물 0 |
| 06:42 | preview 합성(ffmpeg libx264 인코딩) + full 렌더 RVC 나레이션 | 동일. `out/landing_en/` 에 plan/script.json 만 남음 |

- 06:42 는 에이전트가 **"크리티컬 패스를 줄이겠다"며 일부러 병렬 실행**한 것.
- 06:25 원인을 에이전트가 "명령 오류로 캡처가 안 돌았다"로 오판 → 같은 행동 반복.
- 과거 기록: 09-11 22:14 에도 `LOW_MEMORY` 종료 1건. 그 외 08-27 · 09-11~12 에 삼성 백그라운드 정리(`OTHER KILLS`) 여러 건.

## 4. 성공 기록 — RVC 단독은 된다

| 시각 | 산출물 | 비고 |
|---|---|---|
| 08-25 01:21 | `rvc_models/synth_out/helena_intro.mp3` | 헬레나 한국어 |
| 09-29 03:54~55 | `rvc_raw.wav` → `helena_dub_0929.mp3` | 약 1분 |
| 09-29 06:34~36 | `/tmp/helena_en/out.wav` (영문 2문장) | f0 평균 190.8 Hz · 유성 0.686 · STT 역검증 단어 13/15 = 87% |

## 5. 캐파 확인 계획 (미착수 — 다음에 할 것)

목표: **"S21 한 대로 튜토리얼 1편(5스텝) 끝까지"가 되는지 + 각 단계 피크 메모리·시간.**

| # | 측정 | 방법 | 기록할 값 |
|---|---|---|---|
| 1 | RVC 1스텝 | `rvc_convert.py` 단독, 다른 작업 0 | 소요 시간 · 피크 RSS · 실행 중 MemAvailable 최저값 |
| 2 | 크롬 캡처 | `tutor.py --preview` 캡처 단계만 | 컷 수 · 시간 · 피크 |
| 3 | ffmpeg 합성 | compositor(libx264) 단독 | 인코딩 시간 · 피크 |
| 4 | faster-whisper STT | 역검증 1회 | 모델 로딩 피크 |
| 5 | **전체 1편 직렬** | ①→②→③ 순서, 겹침 없음 | 총 시간 · 성공 여부 · `exit-info` 새 기록 없음 |
| 6 | (선택) 한계 확인 | 2개 동시 조합별 | 어느 조합에서 죽는지 — **Termux 가 죽으면 세션도 죽으니 PC 에서 ADB 로 관찰** |

측정 도구: 1초 간격 `grep MemAvailable /proc/meminfo` 로깅 + `/usr/bin/time -v`(피크 RSS). 관찰은 **PC 쪽 ADB**에서 (S21 이 죽어도 기록이 남게).

판정:
- 5번 통과 → S21 = 튜토리얼 1편 생산 가능, 이 문서에 1편 소요시간 기록
- 5번 실패 → RVC 더빙은 랩탑(parksy-voice MCP)으로 넘기고 S21 은 캡처·합성만

## 6. 운영 규칙 (S21 CLAUDE.md 에 반영됨, 09-29)

- 무거운 작업 = RVC 변환 · Playwright/크롬 캡처 · ffmpeg 인코딩 · faster-whisper · torch 로딩
- **백그라운드로 띄워도 하나 끝난 뒤 다음.** "크리티컬 패스 단축"을 이유로 병렬화 금지
- 튜토리얼: ① 나레이션(edge-tts → humanizer → RVC) → ② 캡처 → ③ 합성. preview 와 full 렌더 동시 금지
- 시작 전 `grep MemAvailable /proc/meminfo` — **2 GB 미만이면 시작하지 말고 보고**
- 세션이 갑자기 끊기면 **메모리 강제종료부터 의심**
- 규칙 위치: S21 에이전트는 ubuntu 유저 → 실제 로드 파일은 proot `/home/ubuntu/.claude/CLAUDE.md` (root 쪽만 고치면 안 읽힘)

## 7. 복구 절차 (Termux 가 죽었을 때, PC 에서)

```bash
adb connect 100.99.4.125:5900
adb -s 100.99.4.125:5900 shell dumpsys activity exit-info com.termux | grep -m2 -E "timestamp=|reason="   # 원인 확인
adb -s 100.99.4.125:5900 shell am start -n com.termux/.app.TermuxActivity                               # Termux 재기동
# sshd 는 Termux 와 같이 죽는다 → 위젯 6 을 누르면 sshd 자동 기동 (또는 Termux 에 sshd 입력)
```

관련: `_notebook/rvc-environment-gap_Claude.md` · `_notebook/rvc-failure-analysis_Claude.md` · proot `/root/mcp/MCP_VERSIONS.txt`
