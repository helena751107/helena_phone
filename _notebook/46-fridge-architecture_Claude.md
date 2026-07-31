# 냉장고(Fridge) 아키텍처 — dtslib1979 ⇄ helena751107 자산 공유 체계

> 선언: 2026-07-31 (_Claude, Boss 승인)  
> 헌법 근거: CONSTITUTION.md 제2조(코드는 선물) · 제6조(판단력=희소자산)  
> 관계 문서: `99-devlog.md` §97–98

---

## 1. 정의

**냉장고(Fridge)** 란, dtslib1979(창작자)가 구축한 모든 코드·에셋·실험·템플릿을
helena751107(수혜자·누나·대필작가)에게 **GitHub 콜라보레이터 권한으로 즉시 공유**하는
자산 전달 체계다.

포크도, PR도, 서브모듈도 아니다. **공동 소유(shared ownership)** 다.

---

## 2. 냉장고에 들어 있는 것

### dtslib1979 소유 — 28종 (27🔒 + 1🌐)

#### 🧊 dtslib 코어 (5종)
| 레포 | 내용 | 핵심 자산 |
|------|------|-----------|
| `dtslib-papyrus` | 디지털 명함·선물 패키지 원산지 | 33파일·9,240줄 — CONSTITUTION 제2조의 실물 증거 |
| `dtslib-branch` | 보일러플레이트 + 실물 모델 | 브랜치 전략·템플릿 |
| `dtslib-cloud-appstore` | 클라우드 앱 배포 실험 (Python) | 배포 파이프라인 |
| `dtslib-localpc` | 로컬PC 실행 노드 (Python) | WSL·로컬 자동화·오프라인 워크플로우 |
| `dtslib-apk-lab` | APK 빌드 실험실 (Dart) 🌐 | 안드로이드 패키징 |

#### 🎙️ 방송·콘텐츠 (6종)
| 레포 | 내용 |
|------|------|
| `gohsy` | gohsy comes true — 브랜드 루트 |
| `gohsy-fashion` | DONGSEON Studio — 비즈니스 디지털 스튜디오 |
| `gohsy-production` | 3-Lane 방송 스튜디오 프로토콜 (News/Recording/Stage) |
| `espiritu-tango` | Tango Magenta — 콘텐츠 방송 아키텍처 |
| `artrew` | KOOSY 자매 사이트 |
| `koosy` | 셀럽 스토리 편집 방송 ⭐2 |

#### 🛠️ parksy 에셋 파이프 (4종)
| 레포 | 내용 | 규모/특징 |
|------|------|-----------|
| `parksy-audio` | 오디오·내레이션·MIDI 추출·렌더링 | ~986MB, steal.py→demucs→basic-pitch 파이프, TG 봇(36KB) |
| `parksy-image` | 썸네일·AI 비디오 시드 | WH 연동 |
| `parksy-logs` | Android Share Intent → 자동 텍스트 캡처 | Python, 개인 아카이브 |
| `parksy.kr` | EduArt 엔지니어 마도서 — 디지털 지식 아카이브 | |

#### 📡 인프라·툴 (4종)
| 레포 | 내용 |
|------|------|
| `termux-bridge` | **PC↔Termux 간극 메우기** — QA·CDP 스크린샷·모바일 개발 |
| `OrbitPrompt` | 다중 쿼리 생성 엔진 → AI 파이프 |
| `eae-univ` | AI 시대 온라인 학습 플랫폼 — YouTube + PWA |
| `eae.kr` | EAE PWA Books — React + Vite + MDX + Pages ⭐1 |

#### 🏢 비즈니스·실험 (9종)
| 레포 | 내용 |
|------|------|
| `abraham` | 에이브럼 — 족발집 실운영자 + YouTube 크리에이터 |
| `papafly` | 파파플라이 인큐베이션 |
| `buckleychang.com` | Buckley Chang CPA — AI 경제 리얼리티 인터페이스 |
| `buddies.kr` | 실물 유통·지역 비즈니스 |
| `namoneygoal` | 길드형 부동산·로컬 비즈니스 실험 |
| `phoneparis` | 폰 유통·현장 판매 실험 |
| `hoyadang.com` | 레스토랑 프로토콜 (espiritu-tango fork) |
| `alexandria-sanctuary` | 팔공산 글로벌 스피리추얼 케어 커뮤니티 |
| `dtslib.kr` | DTSLIB 경제방송 허브 — 코드·사업·현장 연결 |

### helena751107 소유 — 6종 (전부 🌐)

| 레포 | 내용 |
|------|------|
| `helena_phone` | **메인 워크스페이스** — S21 폰·Termux·AI 에이전트·문서 |
| `helana_log` | 기술 로그 — APK 리버싱·MCP·LLM |
| `helena-faith` | 가족 신앙사 — 신학·묵상·찬양 아카이브 |
| `helena-piano` | 피아노 종합 — MIDI·REAPER·AI 음원·BGM Studio |
| `helena-psycare` | 멘탈케어 — 정신분석·MCP 모델·치료 기록 |
| `helana-faith` | (중복 가능성 — ecosystem-map 미등록) |

---

## 3. 냉장고 vs 기존 협업 모델

| | Fork | PR | Submodule | **냉장고 (콜라보)** |
|---|---|---|---|---|
| 방향 | 단방향 복사 | 단방향 제안 | 읽기전용 참조 | **쌍방향 RW** |
| 원본 접근 | 내 사본만 | merge 후 | 고정 커밋 | **실시간 최신** |
| AI가 쓰려면 | fork 따로 clone | PR 따로 생성 | submodule init | **바로 `gh repo clone`** |
| 자산 철학 | "빌려 씀" | "기여함" | "참조함" | **"내 것도 네 것"** |
| 갱신 | upstream pull | merge 기다림 | 수동 업데이트 | **즉시 반영** |

---

## 4. AI 에이전트가 냉장고를 쓰는 패턴

### 4.1 재고 확인
```bash
# 전체 28종 인벤토리
gh api /user/repos \
  --jq '[.[] | select(.owner.login == "dtslib1979")] | .[] | "\(.name) | \(.description)"'
```

### 4.2 특정 자산 즉시 복제
```bash
# termux-bridge 필요하면:
gh repo clone dtslib1979/termux-bridge /root/fridge/termux-bridge

# parksy-audio 파이프 필요하면:
gh repo clone dtslib1979/parksy-audio /root/fridge/parksy-audio
```

### 4.3 파일 단위 참조 (clone 없이)
```bash
# README만 읽기
gh api repos/dtslib1979/parksy-audio/contents/README.md --jq '.content' | base64 -d

# 특정 디렉토리 구조 파악
gh api repos/dtslib1979/termux-bridge/contents/app/ --jq '.[].name'
```

### 4.4 전체 싱크 (최초 1회)
```bash
mkdir -p /root/fridge
for r in $(gh api /user/repos --jq '[.[]|select(.owner.login=="dtslib1979")].name[]'); do
  [ -d "/root/fridge/$r" ] && git -C "/root/fridge/$r" pull --ff-only \
    || gh repo clone "dtslib1979/$r" "/root/fridge/$r"
done
```

---

## 5. 헌법적 의미

### CONSTITUTION.md 제2조 — 코드는 선물
> "이 프로젝트에서 생산된 모든 코드는 선물(gift)이다.  
> 저작권, 소유권, 라이선스 논의는 이 프로젝트의 목적과 무관하다."

냉장고는 이 선언을 **기술적 메커니즘**으로 구현한 것이다.
"코드는 선물"이라는 철학이 GitHub Collaborator라는 구체적 인프라로 실물화됨.

### CONSTITUTION.md 제6조 — 판단력만이 희소 자산
> "코드는 인스턴스, 사고 서식이 자산."

냉장고에 저장된 모든 코드는 **인스턴스(산출물)** 이다.
진짜 자산은 그 코드를 생산한 **사고 서식**이며,
냉장고는 그 사고 서식의 실물을 **공유하는 창구**다.

---

## 6. 운영 원칙

1. **dtslib1979가 만들면, helena751107 콜라보는 기본값.** 새 레포 생성 시 자동으로 초대.
2. **AI 에이전트는 양쪽 레포를 균등하게 취급.** `helena_phone/scripts/`와 `dtslib1979/termux-bridge/`는 같은 냉장고의 다른 선반.
3. **자산 출처는 기록하되, 재사용을 막지 않는다.** "어디서 왔는지"는 밝히고, "써도 되는지"는 묻지 않는다.
4. **냉장고는 계속 채워진다.** dtslib1979의 새 실험·템플릿·파이프가 생기면 자동으로 helena751107의 자산 풀에 추가.

---

## 7. Boss 선언 (2026-07-31)

> "내가 만든 자산을 공유하는 거야.  
> 필요한 거 갖고 와서 써."

냉장고는 **창작자(dtslib1979)와 수혜자(helena751107)가
같은 문을 열고, 같은 선반에서, 같은 식재료로 각자의 요리를 하는 공간**이다.

이것이 이 프로젝트의 자산 철학이다.
코드를 쌓는 게 아니라, 코드를 **나누는** 것.
