# 3단계: 방송/발행 — 폰으로 콘텐츠 만들기

> 유튜브 방송, 블로그 포스팅을 폰에서 자동화

## 상태

| 채널 | 상태 | 도구 |
|------|------|------|
| YouTube 5채널 | 🔧 설계 완료 / OAuth 대기 | YouTube Data API |
| 티스토리 5종 | 🔧 설계 완료 | Playwright Headless |
| 네이버 블로그 | 🔧 설계 완료 | Playwright + 쿠키 세션 |

## 핵심 문제

**티스토리와 네이버는 공식 API가 없다.**
- 티스토리 Open API: 2024년 2월 완전 종료
- 네이버 포스팅 API: 원래 없음

→ 유일한 방법: **Playwright Headless Chromium** 브라우저 자동화

## 문서

| # | 내용 | 바로가기 |
|---|------|---------|
| 3.1 | YouTube 채널 5종 아키텍처 | [youtube.md](./youtube.md) |
| 3.2 | 티스토리 자동 포스팅 전략 | [tistory-auto.md](./tistory-auto.md) |
| 3.3 | 네이버 자동 포스팅 전략 | [naver-auto.md](./naver-auto.md) |
