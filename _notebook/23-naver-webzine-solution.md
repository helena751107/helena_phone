# 🎨 네이버 웹진 — 최종 솔루션 (2026-07-25)

> 리서치 결론: 스마트에디터 ONE은 HTML 모드 미지원.
> 코드 템플릿 ❌, 시각 서식 ✅, YouTube CDN ✅.

---

## 1. 기술 제약 정리

| 시도 | 결과 | 이유 |
|------|------|------|
| HTML 복사붙여넣기 | ❌ | 스마트에디터 ONE이 raw HTML 입력 차단 |
| 스킨 편집 | ✅ | 전체 블로그 디자인. HTML/CSS 직접 작성 가능. **1회 작업** |
| 서식 (스냅샷) | ✅ | 에디터 내 블록 구성 저장 → 새 글에서 불러오기 |
| YouTube 링크 | ✅ | URL 붙여넣기 → 미리보기 카드 자동 생성 |
| 이미지 URL 삽입 | ✅ | GitHub Pages를 CDN으로 사용 |

---

## 2. 콘텐츠 전략 — "이미지 대신 짧은 클립"

### 원칙
- ❌ AI 이미지 생성 안 함 (비용·품질·진정성 문제)
- ❌ Cloudinary 등 유료 CDN 안 씀
- ✅ YouTube를 무료 영상 CDN으로 사용
- ✅ 폰 화면 녹화 → 짧은 설명 클립 → YouTube 업로드 → 네이버 임베드

### YouTube = 무제한 무료 CDN

```
폰 화면 녹화 (1~3분)
    │
    ▼
YouTube @helena_phone 업로드
    │
    ▼
네이버 에디터에서 URL 붙여넣기 → 자동 임베드
```

**장점:**
- 무료·무제한·영구 보존
- 네이버 에디터에서 자동 미리보기 카드 생성
- 영상이 이미지보다 설명력이 훨씬 높음
- 실제 작업 화면이라 신뢰감 있음

---

## 3. 주간 발행 워크플로우

### Claude Code → Telegram 배달

```
매주 일요일, TG로 발행 패키지 전송:

📋 [주간 워크센터 리포트] 2026-07-25

🏭 이번 주 GitHub:
  (git log --oneline --since="7일전")

📱 디바이스:
  배터리: XX% · 저장: XXGB · 온도: XX°C

📺 이번 주 클립:
  https://youtu.be/XXXXX — (영상 제목)
  https://youtu.be/YYYYY — (영상 제목)

🧠 판단:
  "이번 주 핵심 결정 한 줄"

🔗:
  GitHub: github.com/helena751107/helena_phone
  영문: helena751107.github.io/helena_phone/index-en.html
  YouTube: youtube.com/@helena_phone
```

### 사람 → 네이버 발행 (5분)

1. TG 메시지 복사
2. 네이버 글쓰기 → 제목 붙여넣기
3. 본문 붙여넣기 (에디터가 자동 서식)
4. YouTube 링크 → 자동 임베드 카드
5. GitHub 이미지 URL → 이미지 삽입
6. 서식에서 미리 만들어둔 푸터·헤더 불러오기
7. 발행

---

## 4. 1회 설정 작업

### A. 블로그 스킨 (내가 CSS 파일 제공)
- 관리자 → 스킨 편집 → HTML/CSS 붙여넣기
- 웹진 스타일: 깔끔한 타이포그래피, 강조 색상, 링크 카드 스타일

### B. 서식 등록 (네가 에디터에서)
- 네이버 글쓰기 → 헤더·푸터·링크 박스 배치 → "서식으로 저장"
- 매주 새 글 쓸 때 "서식 불러오기"로 재사용

### C. YouTube 재생목록
- "웹진 클립" 플레이리스트 생성
- 짧은 설명 클립 전용 보관

---

## 5. 생산된 파일

| 파일 | 용도 |
|------|------|
| **`naver/quilt/`** | **정본 · Marine Quilt 스킨+서식+TG 패키지 (2026-07-27)** |
| `naver/quilt/BOSS-CARD.md` | Boss 3분 설치 카드 |
| `naver/quilt/skin-custom.css` | 스킨 CSS 1회 |
| `naver/quilt/weekly-seosik-preview.html` | 서식 시각 기준 |
| `naver/quilt/weekly-seosik-paste.txt` | 서식 저장용 텍스트 |
| `naver/quilt/tg-package-template.md` | Claude→TG 배달 포맷 |
| `scripts/naver_template.html` | (레거시 참고) HTML — 스마트에디터 직접 사용 불가 |
| `scripts/naver_recipe.py` | (참고용) 요리레시피 메타포 생성기 |
| `_notebook/23-naver-webzine-solution.md` | 이 문서 — 솔루션 원칙 |
| `_notebook/42-marine-quilt-naver-design_Grok.md` | 디자인 패키지 노트 |

---

## 6. 교훈

> **"플랫폼이 허용한 방식으로만 하라.**
> HTML 모드가 없으면 없는 대로, YouTube 임베드가 되면 되는 대로.
> 제약 안에서 가장 효율적인 파이프를 만드는 게 진짜 설계다."

---

> 📱 helena751107.github.io/helena_phone
> 📺 youtube.com/@helena_phone
> 🌐 m.blog.naver.com/helena1975
