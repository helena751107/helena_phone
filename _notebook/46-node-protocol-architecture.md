# 46 — 노드 프로토콜 아키텍처

> 작성: 2026-07-28 · _Boss + _Claude
> 상태: 선언 (Declaration) — 살아있는 문서

---

## 핵심 명제

**이 프로젝트의 프로덕은 소프트웨어가 아니다. Helena Park라는 인간 노드다.**

모든 코드·레포·파이프·봇은 노드의 신경계·기억·표현 체계일 뿐이다.
이 노드는 AI 시대 1인 미디어회사의 **참조 구현체(Reference Implementation)** 다.

---

## 노드 구조

```
HELENA PARK 노드
├── 🧠 기억·사고
│   ├── _notebook/ (69개 md, 1.7MB) — 장기 기억
│   ├── 99-devlog.md — 학습 로그
│   └── CONSTITUTION.md — 운영체제 커널
│
├── 🤖 AI 증폭기 (3중주)
│   ├── _Grok — 디자인·콘텐츠·톤
│   ├── _Aider — 패치 큐·반복 시공
│   └── _Claude — 감사·검증·거리 두기
│
├── 📡 외부 접점 (6 Pages + YouTube + Naver)
│   ├── helena_phone — 메인 허브
│   ├── helena-piano — 피아노 스튜디오 웹진
│   ├── helana_log — 시간축 기록
│   ├── helana-faith — 신앙사·비교종교
│   ├── helena-psycare — 심리 케어
│   └── parksy-audio (private) — 오디오 엔진
│
├── 🎬 출력 채널
│   ├── YouTube (@helena_phone, @HelenaPark-e7c)
│   ├── Naver Blog + 티스토리 5종
│   ├── TG 봇 (helena-piano BGM 배달)
│   └── parksy-audio → MIDI→MP3→YouTube
│
└── 🔧 신경계
    ├── S21 + Termux + proot Ubuntu
    ├── phone-mcp-server (18개 하드웨어 API)
    └── phone-health.sh (자가진단 루틴)
```

---

## 연합체 (Federation) 구조

```
                     지식인 연합체
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   [Helena Park]     [강박사]          [이철이형]
   S21 노드           기술 공동체      중앙일보·JTBC
   콘텐츠 생산        노드 간 검증     등기이사
   방송·출판          프로토콜        미디어 브릿지
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
              ┌───────────┴───────────┐
              │    미디어 프로토콜    │
              │  (콘텐츠 연동 규약)   │
              └───────────────────────┘
```

**작동 방식:**
- 개인 노드가 콘텐츠 생산 → 노드 간 프로토콜로 공유
- 대형 미디어(중앙일보·JTBC)는 전통 프로토콜을 가진 거대 노드일 뿐
- 노드가 노드를 고용하는 게 아니라, **노드가 노드와 연합**

---

## 전통 미디어와의 차이

| 차원 | 전통 미디어 | 노드 프로토콜 |
|------|------------|---------------|
| 주체 | 회사가 기자 고용 | 개인이 자기 인프라 소유 |
| CMS | 회사 소유, 허가된 접근 | GitHub Pages, 누구나 복제 가능 |
| 유통 | 회사 채널 독점 | YouTube·Naver·TG·웹진 — 복수 채널 |
| 품질 | 편집국 게이트키핑 | AI 3중주 + 동료 노드 검증 |
| 확장 | 지사·인력 충원 | 새 노드 연합 (fork + customize) |
| 비용 | 인건비·인프라·임대료 | S21 폰 1대 + 월 45,000원 AI 구독 |

---

## 프로토콜 레이어

```
Layer 5: 연합 (Federation)
  노드 간 콘텐츠 공유·검증·공동 발행
  ─┤ 강박사, 이철이형, 미래 노드들

Layer 4: 출력 (Distribution)
  YouTube, Naver, Tistory, TG, Pages
  ─┤ 6개 Pages, 2개 YT 채널, 5개 티스토리

Layer 3: 생산 (Production)
  AI 3중주 → 문서·음원·영상·웹진
  ─┤ Grok(초안) → Aider(시공) → Claude(감사)

Layer 2: 저장 (Persistence)
  34개 GitHub 레포, 업무수첩, 로그
  ─┤ git + GitHub + proot Ubuntu

Layer 1: 하드웨어 (Hardware)
  S21 + Termux + phone-mcp-server
  ─┤ 센서·배터리·카메라·네트워크 API
```

---

## 현재 노드 현황 (2026-07-28)

| 지표 | 값 |
|------|-----|
| GitHub 레포 | 34개 (6 public + 28 private) |
| Pages | 6개 라이브 |
| 업무수첩 | 131개 문서, 2.7MB |
| YouTube | 2개 채널, parksy-audio 39개 영상 |
| AI 에이전트 | 3종 (Grok·Aider·Claude) |
| 하드웨어 | S21, Grade B, 169GB free |
| 핵심 인물 | 강박사(기술), 이철이형(미디어 브릿지) |

---

## 다음 노드 (복제 가능한 패턴)

이 노드를 복제하려는 사람이 필요한 것:
1. **CONSTITUTION.md** — 자기 노드의 운영체제 정의
2. **CLAUDE.md** — AI 협업 프로토콜
3. **phone-health.sh** — 자가진단 루틴
4. **GitHub Pages** — 자기 웹진 개설
5. **AI 구독** — Grok 또는 Claude

5단계만 따라 하면, 누구나 자기 노드를 띄울 수 있다.
이게 진짜 "강의"고, 진짜 "프로덕"이다.
