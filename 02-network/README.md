# 2단계: 통신망 구축 — 폰을 세상과 연결

> 폰 안에서만 돌아가던 서비스를 외부와 연결하는 채널 3종

## 3종 세트

| 채널 | 용도 | 방식 | 비용 |
|------|------|------|------|
| **GitHub Pages** | 정적 웹사이트 호스팅 | git push 자동 발행 | 무료 |
| **Discord** | 실시간 채팅 + 위젯 | WidgetBot 임베드 | 무료 |
| **Telegram** | AI 보고 + 알림 | Bot API | 무료 |

## 전체 흐름

```
GitHub 저장소 push
    → GitHub Pages 자동 배포 (웹사이트)
        → Giscus 댓글 (GitHub Discussions 기반)
            → WidgetBot 채팅 (Discord 위젯)
                → Telegram 봇 알림
```

## 문서

| # | 내용 | 바로가기 |
|---|------|---------|
| 2.1 | GitHub Pages + Giscus + WidgetBot | [github-pages.md](./github-pages.md) |
| 2.2 | Discord 서버 생성/관리 | [discord.md](./discord.md) |
| 2.3 | Telegram 봇 + 자동 보고 | [telegram.md](./telegram.md) |
