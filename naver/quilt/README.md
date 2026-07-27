# Marine Quilt — 네이버 스킨·서식 패키지

**해병대(구조) + 수공예 퀼트(표면)**  
YouTube 조교 · Naver 장인 · Paste Pipeline 손바느질.

## 빠른 시작

| 순서 | 파일 | 행동 |
|------|------|------|
| 1 | [BOSS-CARD.md](./BOSS-CARD.md) | 3분 설치 카드 |
| 2 | [skin-custom.css](./skin-custom.css) | 스킨 CSS 1회 붙여넣기 |
| 3 | [weekly-seosik-preview.html](./weekly-seosik-preview.html) | 서식 시각 기준 |
| 4 | [weekly-seosik-paste.txt](./weekly-seosik-paste.txt) | 서식 1회 저장용 텍스트 |
| 5 | [tg-package-template.md](./tg-package-template.md) | 매주 TG 배달 포맷 |

## 파이프

```
Claude → TG 주간 패키지
    → Boss: 서식 불러오기
    → 【슬롯】 한 땀 붙여넣기
    → YouTube·이미지 삽입
    → 발행 = 한 주의 퀼트
```

## 디자인 근거

[design-system.md](./design-system.md) — 커뮤니티 리서치 요약 + 토큰 + 버릴 것.

## 부품

[blocks/](./blocks/) — mast · oneline · demo · follow · drill · judgment · links · foot

## 레거시

`scripts/naver_template.html` 은 HTML 모드 전제 참고용.  
실전은 **이 폴더(Marine Quilt)** 가 정본.
