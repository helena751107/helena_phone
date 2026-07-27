# Marine Quilt — 네이버 디자인 패키지 (리서치→템플릿)

> agent _Grok · 2026-07-27  
> 확정 톤: **해병대 조교(YouTube) + 수공예 퀼트(Naver)**

---

## 1. 왜 이걸 만들었나

Boss 지시: 커뮤니티·쓰레기통을 뒤져 솔루션을 모으고,  
**최고의 디자인 요소로 템플릿을 만들어라.**

이전 상태:
- `scripts/naver_template.html` — 예쁨, 그러나 **스마트에디터 ONE HTML 모드 없음** → 실전 불가
- 홈페이지형 스킨 커뮤니티 — 투명 위젯 5개 + 이미지맵 → **초심자·주간 운영에 쓰레기**
- Paste Pipeline 문서는 있음 → **시각 시스템·서식 골격이 약함**

---

## 2. 쓰레기통에서 건진 것 / 버린 것

| 건짐 | 버림 |
|------|------|
| 스킨 CSS 1회 주입 | 풀 홈페이지형 이미지맵 스킨 |
| 서식(스냅샷) 재사용 | raw HTML 포스트 |
| YouTube URL → 카드 | 유료 CDN·AI 삽화 남발 |
| TG 배달 + 손 붙여넣기 | 매크로·Playwright 발행 집착 |
| 1단·여백·타이포 중심 | 위젯 광고 밀집 레이아웃 |
| 시범→따라→실전 교범 구조 | 옵션·변수 폭주 문서 |

---

## 3. 디자인 핵심 (디자이너 결정)

**구조 = 해병대, 표면 = 퀼트.**

- Deep olive / crimson badge / khaki thread / cream linen
- 점선 = 바느질 선 (섹션 경계)
- 패치 블록 = 한 줄·판단·링크
- 따라하기 **3단계 고정** (4+ 는 다음 주)
- 슬롯 문법 `【 】` = 손바느질 자리

상세 토큰: `naver/quilt/design-system.md`

---

## 4. 납품 파일

```
naver/quilt/
  README.md
  BOSS-CARD.md
  design-system.md
  skin-custom.css
  skin-widgets.html
  weekly-seosik-preview.html
  weekly-seosik-paste.txt
  tg-package-template.md
  blocks/ 01~08
```

Pages 배포 후 미리보기 예:
`https://helena751107.github.io/helena_phone/naver/quilt/weekly-seosik-preview.html`

---

## 5. 퀼트 제작 파이프 (확정)

```
① Claude Code → TG 주간 콘텐츠 패키지
② Boss → Naver 서식 「Marine Quilt 주간」 불러오기
③ TG 내용 → 서식 슬롯 한 땀 붙여넣기
④ YouTube 링크 · 이미지 삽입
⑤ 발행 → 한 주의 퀼트 완성
```

---

## 6. 성공 기준

- [ ] 스킨 CSS 적용 후 본문 톤이 린넨·스티치로 읽힘
- [ ] 서식 1회 저장 완료
- [ ] 샘플 1편 손바느질 발행 < 10분
- [ ] HTML/매크로 시도 0

---

## 7. 다음 (선택)

- TG 봇이 `tg-package-template` 형식으로 자동 발송
- 주간 VOL 번호 카운터 (레포 파일 한 줄)
- 미리보기 PNG를 Pages에 스냅샷

*한 땀 한 땀 · 장비 탓 하지 마라*
