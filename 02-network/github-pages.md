# 2.1 GitHub Pages + Giscus 댓글

> 무료 웹사이트 호스팅 + GitHub 기반 댓글 시스템

## GitHub Pages 활성화

```bash
# API로 Pages 켜기 (레포당 1번)
TOKEN="ghp_xxx"
curl -X POST -H "Authorization: token $TOKEN" \
  https://api.github.com/repos/사용자명/레포명/pages \
  -d '{"source":{"branch":"main","path":"/"}}'
```

또는 GitHub 웹 UI: Settings → Pages → Source → Deploy from branch → main

## index.html 만들기

저장소 루트에 `index.html`을 만들면 자동으로 웹사이트가 된다.

```html
<!DOCTYPE html>
<html>
<head><title>내 사이트</title></head>
<body><h1>Hello, World!</h1></body>
</html>
```

## Giscus 댓글 시스템

Giscus는 GitHub Discussions를 댓글판으로 쓰는 무료 시스템.

### 1. GitHub App 설치
https://github.com/apps/giscus → Install → 저장소 선택

### 2. Discussions 활성화
```bash
curl -X PATCH -H "Authorization: token $TOKEN" \
  https://api.github.com/repos/사용자명/레포명 \
  -d '{"has_discussions":true}'
```

### 3. Giscus 스크립트 추가
https://giscus.app/ 에서 설정 후 스크립트 복사 → index.html에 삽입

## 전체 흐름

```
git push → GitHub Pages 자동 배포 (보통 1~2분)
         → Giscus 댓글 로드
         → Discord 채팅 위젯 (WidgetBot)
```

## 비용

**0원.** GitHub Free 플랜으로 충분함.
