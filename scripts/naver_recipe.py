#!/usr/bin/env python3
"""
네이버 블로그 '요리 레시피' 형식 포스트 생성기
=============================================
파싱한 원본: helena1975/224357386157
형식: 요리 레시피를 빌려 기술/개발 내용을 소개하는 "메타포 포스트"

사용법:
  python3 scripts/naver_recipe.py > 네이버_포스트.txt
  → 복사해서 네이버 블로그 글쓰기에 붙여넣기

스타일:
  - 카테고리 + 제목
  - 대표 이미지 + 한 줄 소개
  - "재료" 섹션 (기술 스택/도구 나열)
  - 1~8단계 요리 과정 (설치/설정 과정)
  - 마무리 + 링크
"""

import sys, datetime

def recipe(meta):
    """메타데이터로 레시피 포스트 생성"""

    today = datetime.date.today().strftime("%Y-%m-%d")

    post = f"""카테고리: {meta.get('category', '1.갤럭시21 w/ AI')}

---

# {meta.get('title', '제목')}

{meta.get('subtitle', '')}

---

## 📱 이렇게 만듭니다

{meta.get('intro', '')}

---

## 🛒 재료 준비

{chr(10).join('- ' + item for item in meta.get('ingredients', []))}

---

## 👨‍🍳 만들기

{chr(10).join(f'''
**{i+1}.** {step}
''' for i, step in enumerate(meta.get('steps', [])))}

---

## ✨ 완성!

{meta.get('result', '')}

---

## 🔗 더 보기

{chr(10).join('- ' + link for link in meta.get('links', []))}

---

{meta.get('footer', f'© {today} Helena Park — helena751107.github.io/helena_phone')}
"""
    return post


# ============================================================
# 예제: S21 AI 워크스테이션 소개글
# ============================================================

EXAMPLE = {
    "category": "1.갤럭시21 w/ AI",
    "title": "구형 갤럭시 S21, AI 워크스테이션으로 다시 태어나다",
    "subtitle": "5년 된 폰 하나로 풀스택 개발·방송·출판 스튜디오를 만드는 레시피",

    "intro": """삼성 구형 핸드폰 Galaxy S21.
2021년에 출시된 이 폰이 2026년, AI 개발 워크스테이션으로 다시 태어났습니다.

Termux + proot Ubuntu + Claude Code + DeepSeek Radar.
모든 비용 0원. 모든 작업 100% 음성입력.

이 레시피는 "폰을 AI 서버로 만드는"全过程을 요리하듯 안내합니다.""",

    "ingredients": [
        "📱 삼성 갤럭시 S21 (또는 아무 안드로이드 폰)",
        "🛠️ Termux (F-Droid에서 설치)",
        "🐧 proot-distro Ubuntu 26.04",
        "🤖 Claude Code + DeepSeek Radar (무료 LLM)",
        "📺 YouTube 채널 (@helena_phone)",
        "📝 GitHub 계정 (helena751107)",
        "💬 Discord 서버 + Telegram 봇",
        "🎤 STT 음성입력 (키보드 없이 말로만!)"
    ],

    "steps": [
        "Termux 설치하기 — F-Droid에서 다운로드. Play Store 버전은 업데이트 중단됐으니 F-Droid만 사용하세요.",
        "proot Ubuntu 올리기 — `proot-distro install ubuntu` 한 줄이면 끝. 5분 소요.",
        "Claude Code 얹기 — npm으로 Claude Code 설치. DeepSeek Radar로 API 비용 우회 (0원!).",
        "GitHub 연결하기 — 레포 5개 생성. Pages + Giscus + WidgetBot 자동 활성화.",
        "폰 통제 MCP 올리기 — phone-mcp-server로 SMS·배터리·GPS·카메라 원격 제어. 루트 없이 18개 도구.",
        "건강 검진 자동화 — phone-health.sh로 27개 항목 진단. 배터리·WiFi·센서·카메라 전부 체크.",
        "YouTube·Discord·Telegram 연결 — 통신망 3종 완비. AI가 작업 완료를 텔레그램으로 보고합니다.",
        "1줄 설치기로 마무리 — g/install.sh. 이제 이 모든 과정이 curl 한 줄로 끝납니다."
    ],

    "result": """5년 된 구형 폰이 풀스택 AI 개발 서버가 됐습니다.
39커밋·102파일·15,874줄의 코드와 문서.
모든 작업은 STT 음성입력으로, 키보드 0회.

이 레시피의 진짜 주인공은 누나입니다.
대필작가-간병인의 손길로 언젠가 누나가 직접 이 시스템을 운영하는 날까지.""",

    "links": [
        "📱 GitHub: github.com/helena751107/helena_phone",
        "🌐 영문판: helena751107.github.io/helena_phone/index-en.html",
        "📺 YouTube: youtube.com/@helena_phone",
        "💬 Discord: discord.gg/JTYSZv2WQE",
        "📝 업무일지: galaxys21-pwuser.tistory.com"
    ],

    "footer": "© 2026 Helena Park — S21 Phone 프로젝트 | helena751107.github.io/helena_phone"
}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--example":
        print(recipe(EXAMPLE))
    else:
        print("사용법:")
        print("  python3 scripts/naver_recipe.py --example    ← 예제 출력")
        print("  python3 scripts/naver_recipe.py --template   ← 빈 템플릿 출력")

        if len(sys.argv) > 1 and sys.argv[1] == "--template":
            print("\n" + recipe({
                "category": "카테고리명",
                "title": "제목을 입력하세요",
                "subtitle": "한 줄 설명",
                "intro": "소개 문단...",
                "ingredients": ["재료1", "재료2", "..."],
                "steps": ["1단계 설명", "2단계 설명", "..."],
                "result": "완성 소감...",
                "links": ["링크1", "링크2"],
                "footer": "서명"
            }))
