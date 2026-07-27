# 🔰 초심자 설치 매뉴얼 — 낡은 폰에서 헬레나 생태계까지

> **대상:** 처음 보는 사람 · 누나 폰에 깔아 주는 Boss · 핸드오프 받는 사람  
> **기기:** Galaxy S21급 중고 안드로이드 (다른 기종도 가능)  
> **시간:** 첫 세팅 2~4시간 (한 번에 안 해도 됨)  
> **비용:** 런타임 대부분 $0 · (선택) DeepSeek/Grok 구독  
> **관련:** `g/install.sh` v3 · 랜딩 `#install` · `GUIDE.md` · Voice 분석 · 플래너 백서  

**에이전트:** `_Grok` 디자이너 레인에서 동선 정리 · 2026-07-27

---

## 0. 한 장으로 보는 전체 동선

```
[낡은 폰]
    │  F-Droid → Termux + Termux:API
    ▼
[Termux] pkg: proot-distro git curl
    │  proot-distro install ubuntu
    ▼
[proot Ubuntu] /root/work = helena_phone
    │  git clone · deepseek.env · claude/grok/ds
    ▼
[에이전트 3레인] 코드 · 시각 · 패치
    │  push · Pages
    ▼
[공개 표면] helena_phone + 위성 4 (log/faith/piano/psycare)
    │
    ▼
[운영] tg 보고 · phone-health · care 데몬 · 문서 웹진
```

**명의 규칙 (중요)**  
- 공개 GitHub·Pages의 **OWNER(명의)** = 큰누나 계정 (기본 `helena751107`)  
- 평소 개발 push 는 **WORK** 계정(콜라보)일 수 있음  
- 변수로 분리해 두었음 → 아래 §2

---

## 1. 준비물 체크리스트

| # | 준비 | 완료 |
|---|------|------|
| 1 | 안드로이드 폰 + 충전기 | ☐ |
| 2 | 안정 Wi-Fi | ☐ |
| 3 | 저장 여유 **5GB+** | ☐ |
| 4 | GitHub 계정 (OWNER 또는 WORK) | ☐ |
| 5 | (권장) PAT 토큰 `repo` 권한 | ☐ |
| 6 | (권장) DeepSeek API 키 | ☐ |
| 7 | (선택) Telegram 봇 토큰·chat_id | ☐ |
| 8 | F-Droid 설치 가능 (플레이 스토어 Termux 비권장) | ☐ |

---

## 2. 변수표 — 누나 계정 변수화

복사해서 메모장에 값을 채우세요. **토큰은 채팅에 올리지 마세요.**

```bash
# ═══ 헬레나 생태계 변수 (예시) ═══
export OWNER_GITHUB="helena751107"     # 명의 · 공개 레포 주인 (큰누나)
export OWNER_NAME="큰누나"               # 표시용
export WORK_GITHUB="dtslib1979"        # 실제 작업·push 계정 (Boss 등)
export GITHUB_USER="$WORK_GITHUB"      # install.sh 가 쓰는 작업 유저
export GITHUB_REPO="helena_phone"      # 워크스페이스 레포 이름
export TEMPLATE_REPO="helena751107/helena_phone"  # 클론 원본
export WORK_DIR="/root/work"           # proot 안 작업 경로

export GITHUB_TOKEN="ghp_여기에넣지말고_로컬만"   # PAT
export DEEPSEEK_API_KEY="sk-..."       # 선택
export TG_TOKEN=""                     # 선택
export TG_CHAT=""                      # 선택

# 옵션
export SKIP_CLAUDE=0                   # 1=클로드 설치 스킵
export SKIP_MCP=0
export CLONE_SATELLITES=0              # 1=위성 4레포 /root/sites 클론
```

| 변수 | 의미 | 초심자 기본 |
|------|------|-------------|
| `OWNER_GITHUB` | 명의·Pages 주인 | `helena751107` |
| `WORK_GITHUB` / `GITHUB_USER` | push 하는 손 | 본인 또는 콜라보 |
| `TEMPLATE_REPO` | 배울 원본 레포 | `helena751107/helena_phone` |
| `GITHUB_REPO` | 내 포크/워크 이름 | `helena_phone` |
| `WORK_DIR` | 디스크 위치 | `/root/work` |

---

## 3. 단계별 설치 (복사 붙여넣기)

### 3-A. 폰에 Termux

1. **F-Droid** 설치 → **Termux** + **Termux:API** 설치  
2. Termux 실행 → 아래 붙여넣기

```bash
pkg update -y && pkg install -y proot-distro git curl termux-api
termux-setup-storage
```

### 3-B. Ubuntu 컨테이너

```bash
proot-distro install ubuntu
proot-distro login ubuntu
```

Ubuntu 안에서:

```bash
apt update && apt install -y git curl ca-certificates python3 python3-pip nodejs npm
```

### 3-C. 변수 넣고 1줄 설치기

Ubuntu 셸에서 (값은 본인 것으로):

```bash
export OWNER_GITHUB="helena751107"
export GITHUB_USER="YOUR_WORK_USER"
export GITHUB_REPO="helena_phone"
export GITHUB_TOKEN="ghp_xxx"
export DEEPSEEK_API_KEY="sk-xxx"   # 없으면 생략
export TG_TOKEN="" TG_CHAT=""      # 없으면 생략

bash <(curl -sL https://raw.githubusercontent.com/helena751107/helena_phone/main/g/install.sh)
```

토큰 없이 **읽기 전용 클론**만:

```bash
export OWNER_GITHUB="helena751107"
export GITHUB_USER="helena751107"
bash <(curl -sL https://raw.githubusercontent.com/helena751107/helena_phone/main/g/install.sh)
```

### 3-D. 매일 출근 루틴

```bash
# Termux
proot-distro login ubuntu
cd /root/work
source configs/deepseek.env 2>/dev/null
source configs/helena-env.example.sh 2>/dev/null

# 에이전트 (있는 것부터)
claude          # 코드 레인
# grok          # 디자이너 레인 (설치 후)
# bash scripts/ds.sh   # 반장 레인

bash phone-health.sh
bash tg.sh '✅ 세션 시작'
```

### 3-E. 웹 표면 확인

브라우저에서:

```
https://OWNER_GITHUB.github.io/helena_phone/
https://OWNER_GITHUB.github.io/helana_log/
https://OWNER_GITHUB.github.io/helana-faith/
https://OWNER_GITHUB.github.io/helena-piano/
https://OWNER_GITHUB.github.io/helena-psycare/
```

`OWNER_GITHUB` 를 실제 아이디로 바꿔서 엽니다.

### 3-F. 문서 → 웹 다시 빌드 (작업 폰에서)

```bash
cd /root/work
python3 scripts/build_webzine.py
python3 scripts/check_webpages_Grok.py
python3 scripts/build_satellite_docs_Grok.py   # 위성 문서 html
```

---

## 4. 핸드오프 시나리오 (누나 폰에 깔 때)

| 단계 | 누가 | 무엇을 |
|------|------|--------|
| 1 | Boss | 누나 폰에 Termux 설치 |
| 2 | Boss | `OWNER_GITHUB=helena751107` 고정 |
| 3 | Boss | WORK 토큰은 **Boss 세션에만**, 누나 폰에는 최소 권한 |
| 4 | Boss | `install.sh` 실행 · health 확인 |
| 5 | 둘 | 랜딩·Pages 같이 열어 “내 명의 사이트” 확인 |
| 6 | Boss | 막힌 지점 → 교재/일지에 기록 |

**성공 정의 (헌법):** 누나가 “이 폰·이 계정” 위에서 나중에 혼자 열 수 있을 것.

---

## 5. 고장 났을 때

| 증상 | 확인 |
|------|------|
| `proot-distro: not found` | Termux에서 `pkg install proot-distro` |
| clone 403 | 토큰·USER·REPO 이름 |
| claude 안 됨 | `source configs/deepseek.env` · API 키 |
| Pages 404 | GitHub repo Settings → Pages → main / root |
| 저장공간 | `df -h` · 5GB 비우기 |
| 배터리 | 충전 · `phone-health.sh` |

```bash
# 재설치 없이 레포만 갱신
cd /root/work && git pull --ff-only
```

---

## 6. 동선 ↔ 문서 지도 (파싱 요약)

| 단계 | 산출 | 문서/URL |
|------|------|----------|
| 왜 구형 폰 | 하드웨어 근거 | `38-s21-voice-driven-analysis` |
| 왜 STT·0원 | 스택 정당화 | `34-stt-zero-cost-justification` |
| 왜 레포 체계 | 플래너 백서 | `37-free-runtime-planner-whitepaper_Grok` |
| 단계 로드맵 | GUIDE 5단계 | `GUIDE.md` / `guide.html` |
| 1줄 설치 | 스크립트 | `g/install.sh` |
| 헌법·실무 | 규칙 | `CONSTITUTION.md` · `CLAUDE.md` |
| 위성 표면 | 4 웹진 | log/faith/piano/psycare |
| 디자이너 현황 | 브릿지 | `38-web-designer-workpad_Grok` |

---

## 7. 랜딩 `#install` 과 관계

랜딩 터미널에 보이는 한 줄은 **요약 진입점**이다.  
초심자는 **이 매뉴얼(계정·변수·순서)** 을 먼저 보고,  
익숙해지면 한 줄 설치기만 돌린다.

권장 한 줄 (복사):

```bash
export OWNER_GITHUB="helena751107" GITHUB_USER="YOUR_USER" GITHUB_TOKEN="ghp_xxx"
bash <(curl -sL https://raw.githubusercontent.com/helena751107/helena_phone/main/g/install.sh)
```

---

## 8. 체크리스트 — “여기까지 왔다”

| # | 상태 |
|---|------|
| Termux + Ubuntu 진입 | ☐ |
| `/root/work` 에 helena_phone | ☐ |
| `git remote -v` 확인 | ☐ |
| deepseek.env 또는 키 | ☐ |
| 에이전트 1종 이상 실행 | ☐ |
| Pages 허브 200 | ☐ |
| (선택) tg 테스트 메시지 | ☐ |
| (선택) 위성 pages 열림 | ☐ |

---

*초심자 설치 매뉴얼 · install-guide · agent **_Grok** · 2026-07-27*
