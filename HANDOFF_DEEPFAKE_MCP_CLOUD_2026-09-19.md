# 핸드오프 — 딥페이크 MCP 클라우드(GitHub Actions) 이식 (2026-09-19)

> 작성: dev-batch 미니PC 쪽 Claude 세션(별도 대화, 이 proot과 컨텍스트 공유 안 됨).
> 박씨 지시로 남김 — 이 세션(폰/proot)이 이어서 검증·마무리를 맡음.
> **2026-09-19 갱신: 미니PC 쪽 개발 완료 + 실사용 가능 상태 확인됨. 아래 §6 참고.**

## 1. 목표

PC(미니PC/랩탑) 없는 지인도 **자기 폰만으로** 딥페이크 MCP(사진+대사 →
Grok 영상생성 → RVC 더빙 → 완성본) 파이프라인을 쓸 수 있게 만드는 것.
결론: 폰이 직접 연산하는 게 아니라, **폰은 트리거만 쏘고 GitHub Actions가
대신 무거운 연산을 하는 구조**로 간다.

## 2. 실측으로 확인한 것 — 전부 실제 테스트, 추측 아님

| 항목 | 결과 |
|---|---|
| 폰/태블릿(안드로이드, proot)이 직접 Docker를 돌릴 수 있는가 | ❌ **불가능, 커널 레벨 차단**. tab-s9와 이 S25 둘 다 `dockerd` 구동 시도 → `iptables/ip_forward permission denied`. 루팅 없인 방법 없음 |
| GitHub Actions 러너가 Docker를 실행할 수 있는가 | ✅ 확인됨. 러너 사양: 2 vCPU / RAM 7.8GB(가용 6.9GB) / 디스크 여유 14GB |
| 폰에서 GitHub Actions를 실제로 트리거할 수 있는가 | ✅ 이 폰(S25)에서 직접 테스트 완료 |
| Grok 로그인 세션이 클라우드(데이터센터) IP에서 막히는가 | ✅ 안 막힘(로그인 로드까진 확인) |
| Grok "영상 생성" 버튼이 클라우드 헤드리스에서 실제로 눌리는가 | ❌ **여전히 미검증, 우회 결정함** — 대신 §6처럼 "영상 생성은 폰에서 실제 브라우저로", 클라우드는 더빙/조립만 맡는 구조로 확정 |
| RVC 더빙 + ffmpeg 조립·렌더링 (순수 CPU 연산) | ✅ **2026-09-19 실제 GitHub Actions 러너에서 end-to-end 성공** — 아래 §6 |

## 3. 역할 분담 (박씨 확정, 유지)

- **미니PC/랩탑 쪽(개발) — 완료.** `po-deepfake-cell` 이미지 GHCR 푸시 완료,
  `.github/workflows/cloud-dub-render.yml` 작성+실제 성공 검증까지 끝남.
- **이 세션(폰) — 다음 담당:**
  1. §6 트리거 방법으로 **이 폰에서 직접** 실제 Grok 생성 클립을 넣어 재검증
  2. 완성본을 이 폰 생태계 인프라(YouTube OAuth, 텔레그램 `@Proot_25ultra_bot`)로 연결
  3. 문제 발견 시 박씨 경유로 피드백

## 4. 참고 문서

`dtslib1979/termux-bridge`(private) `docs/12-deepfake-mcp/`:
`MANUAL-INSTALL.md` / `EASY-EXPLANATION.md` / `CLOUD-ARCHITECTURE-STUDY-2026-09-19.md`

## 5. 이 폰 환경 이슈 (2026-09-19 기준, 재조사 불필요)

- `/root/work/parksy-image` 클론이 깨져있었음 — 정식 재클론 필요.
- `/root/work/voice_models/`, 얼굴사진 폴더 비어있음 — RVC 모델·얼굴사진은
  미니PC 쪽(`parksy-faces`, `~/rvc_models`)에 있음. **클라우드 워크플로우는
  이 문제를 이미 우회함**(§6 — GitHub Release로 모델/사진을 실어나름, 폰에
  로컬로 있을 필요 없음).
- RAM 여유 없음, torch/playwright는 이미 네이티브 설치돼있음(도커 없이).
- **별개 사안(미니PC 쪽 무관)**: `/root/work/.secrets.env`의 `GITHUB_TOKEN`
  노출건 — 이 세션이 알아서 판단.

## 6. ✅ 미니PC 쪽 개발 완료 — 실제 동작 방식 및 트리거 방법

### 파이프라인 구조 (확정)
1. **영상 생성은 폰에서** — 실제 Grok 웹앱/브라우저로 평소처럼 클립 생성
   (헤드리스 클라우드 생성은 버튼 렌더링 문제로 미검증 상태라 우회함).
2. **더빙+조립+렌더링은 클라우드가** — GitHub Actions가 RVC 더빙 → ffmpeg
   조립 → 텔레그램 QA 게이트 → (승인 시) 완성.

### 실제 증명된 실행 결과 (2026-09-19)
`dtslib1979/parksy-image` 레포 `.github/workflows/cloud-dub-render.yml`을
`workflow_dispatch`로 트리거 → G0(모델확인)→G1(플랜)→G2(기존 클립 유지)→
G3(RVC 더빙, ~3분/CPU)→G4(ffmpeg 조립)까지 전부 성공, 완성본을 텔레그램으로
전송까지 확인(사람이 300초 내 OK 안 눌러서 최종 게이트만 타임아웃 — 파이프
라인 자체는 완전히 살아있음이 실증됨).

### 트리거 방법 (이 세션이 실제로 쓸 절차)
1. **에셋 업로드** — 아래 3가지를 하나의 GitHub Release로 `parksy-image`
   레포에 올림(private repo라 `gh release create`/API 사용):
   - `assets.tar.gz` — `rvc_models/<name>/<name>.pth,.index` + `faces/<character>.png`
     + 목소리 QA 참조 wav
   - `clips.zip` — 폰에서 생성한 실제 Grok 클립, `S01.mp4`(멀티 숏이면
     `S02.mp4`...) 이름으로
   - Release 태그 이름을 기억해둘 것 (`release_tag` 입력값으로 씀)
2. **workflow_dispatch 호출**:
   ```
   POST https://api.github.com/repos/dtslib1979/parksy-image/actions/workflows/cloud-dub-render.yml/dispatches
   Authorization: Bearer <PAT, repo 권한>
   {
     "ref": "main",
     "inputs": {
       "title": "<제목, 폴더명으로도 씀>",
       "character": "<faces/ 안의 파일명, 확장자 제외>",
       "voice": "<rvc_models/ 안의 실제 폴더명, 별칭 아님. 예: parksy_rvc_v3>",
       "script_b64": "<대사 텍스트를 base64로>",
       "release_tag": "<1단계 Release 태그>",
       "shot_ids": "unused"
     }
   }
   ```
3. 실행 상태는 `GET .../actions/workflows/cloud-dub-render.yml/runs?per_page=1`로 폴링.
4. 완성본이 **텔레그램으로 자동 전송됨** — 5분 내에 OK/NG 눌러야 최종
   완료 처리됨(안 누르면 타임아웃 실패로 찍히지만, 그 전까지 실제 산출물은
   이미 완성돼서 Actions 아티팩트로도 남아있음).

### 알아둘 함정 2가지 (디버깅하며 발견, 재발 방지용)
- **`voice` 입력엔 친근한 별칭(`"parksy"`) 쓰면 안 됨** — 별칭→실제 모델명
  변환은 `mcp_server.py` 안에서만 일어나고, 이 클라우드 워크플로우는
  `one_shot.sh`를 MCP 안 거치고 직접 호출하므로 **반드시 실제 폴더명**
  (`parksy_rvc_v3` 같은)을 넣어야 함.
- **`--resume-cuts`는 "이 컷 유지"가 아니라 "이 컷만 재생성"이라는 뜻**
  (반대 개념!). 클라우드에선 항상 사전 업로드한 클립을 그대로 써야 하므로
  워크플로우가 내부적으로 `__NONE__`(존재 안 하는 센티널)을 고정으로 넣어서
  모든 컷이 "유지" 분기를 타게 만들어둠 — `shot_ids` 입력은 현재 미사용
  (호환용으로만 남겨둠).

## 7. 다음 행동 제안

이 세션은 §6 절차로 실제 폰에서 생성한 클립을 넣어 재검증하고, 성공하면
YouTube/텔레그램 연결 단계로 넘어가면 됨. 클라우드 워크플로우 자체는
더 손댈 필요 없음(완성 상태).
