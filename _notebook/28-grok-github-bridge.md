# 🌉 Grok — GitHub↔Naver 인터프리터

> 발견: 2026-07-25 | Grok이 GitHub Pages도 완벽 파싱

---

## 1. Grok 파싱 검증

| 대상 | Claude WebFetch | Grok | proot curl |
|------|----------------|------|-----------|
| Naver (m.blog) | ❌ | ✅ | ✅ |
| GitHub Pages | ❌ | ✅ | ✅ |
| GitHub Raw | ❌ | ✅ | ✅ |

**Grok은 우리 인프라(GitHub)와 배포처(Naver) 양쪽을 모두 읽을 수 있다.**

---

## 2. Grok = 인터프리터

```
GitHub (원본·공장)              Naver (배포·웹진)
─────────────────              ─────────────────
CONSTITUTION.md                 프로젝트 소개글
_notebook/99-devlog.md          워크센터 리포트
5x5 ecosystem-map.json         생태계 맵
g/install.sh                   설치 가이드 요약
phone-health.sh 결과            디바이스 스탯

        └──────────┬──────────┘
                   │
              Grok (인터프리터)
              ┌─────┴─────┐
              │ GitHub 읽기 │ → 이해 → 요약
              │ Naver 읽기  │ → 파싱 → 피드백
              │ 이미지 생성 │ → 삽화·표지
              │ 클립 생성   │ → 숏폼 요약
              └───────────┘
```

---

## 3. 월간 웹진 파이프 (Grok 포함)

```
매주 일요일:

1. Claude Code → 주간 GitHub 요약 (git log + devlog)
2. Claude Code → TG로 텍스트 초안 배달
3. 사람 → 네이버에 초안 발행
4. 발행된 네이버 링크 → Grok에게 전달
5. Grok → 네이버 글 + GitHub 원본 동시 파싱
6. Grok → 이미지·클립 생성 (양쪽 맥락 이해)
7. 사람 → 이미지·클립 글에 추가
```

---

## 4. Grok이 특별한 이유

Grok은 다른 AI와 달리 **두 플랫폼을 동시에 이해**할 수 있다:

- Claude Code: GitHub은 완벽, Naver는 못 읽음
- ChatGPT: 둘 다 제한적
- Gemini: 둘 다 제한적
- **Grok: GitHub ✅ + Naver ✅**

이 "양쪽 다 가능"이라는 특성이 Grok을 단순한 이미지 생성기가 아니라
**인프라-배포 간 인터프리터**로 만든다.

---

## 5. 비용 포지셔닝

| 도구 | 비용 | 역할 |
|------|------|------|
| Claude Code | $0 | 텍스트·코드·인프라 |
| Grok | 45,000원/월 | GitHub↔Naver 인터프리터 + 시각 생성 |
| 사람 | — | 발행·편집·방향 |

**45,000원 = GitHub 원본을 이해하고 Naver 독자에게 전달하는 전담 번역가.**

---

> Grok은 "Naver용 Claude Code"가 아니라
> "GitHub와 Naver 사이를 잇는 다리"다.
> 이 다리가 없으면 Claude Code의 산출물이 Naver 독자에게 닿지 않는다.
