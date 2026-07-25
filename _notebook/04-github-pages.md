# GitHub Pages + Giscus + WidgetBot

## 레포지토리

| 레포 | URL | Pages |
|------|-----|-------|
| helena_phone | `github.com/helena751107/helena_phone` | `helena751107.github.io/helena_phone/` |
| helana_log | `github.com/helena751107/helana_log` | `helena751107.github.io/helana_log/` |

## GitHub Pages 활성화 (API)

```bash
TOKEN="ghp_...여기에_토큰"
curl -X POST -H "Authorization: token $TOKEN" \
  https://api.github.com/repos/helena751107/helena_phone/pages \
  -d '{"source":{"branch":"main","path":"/"}}'
```

## Giscus (댓글/게시판)

### helena_phone
- repo: `helena751107/helena_phone`
- repo-id: `R_kgDOTg3jPQ`
- category: `Announcements`
- category-id: `DIC_kwDOTg3jPc4DByff`

### helana_log
- repo: `helena751107/helana_log`
- repo-id: `R_kgDOTg3TCg`
- category: `Announcements`
- category-id: `DIC_kwDOTg3TCs4DByif`

## Discussions 활성화 (API)

```bash
curl -X PATCH -H "Authorization: token $TOKEN" \
  https://api.github.com/repos/helena751107/helena_phone \
  -d '{"has_discussions":true}'
```

## Giscus GraphQL (카테고리 ID 조회)

```graphql
{
  repository(owner:"helena751107",name:"helena_phone") {
    discussionCategories(first:10) {
      nodes { id name slug }
    }
  }
}
```

---

## 현재 상태 (2026-07-25)

| 레포 | Pages URL | Giscus | WidgetBot |
|------|----------|--------|-----------|
| helena_phone | ✅ Live | ✅ | ✅ |
| helana_log | ✅ Live | ✅ | ✅ |
| helena-faith | ✅ Live | ✅ | ✅ |
| helena-piano | ✅ Live | ✅ | ✅ |
| helena-psycare | ✅ Live | ✅ | ✅ |

**참고:** GitHub Pages 빌드가 stuck 상태가 되면 Settings → Pages → None → Save → Deploy from branch로 리셋.
