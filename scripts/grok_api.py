#!/usr/bin/env python3
"""
Grok API 클라이언트 — OpenAI 호환 (xAI)
========================================
인증 방법 (우선순위):
  1. OAuth 토큰: configs/grok_token.json (SuperGrok 구독 → bash grok_oauth_setup.sh)
  2. API 키: .secrets.env 의 XAI_API_KEY (console.x.ai → $25 무료 크레딧)

사용법:
  python3 scripts/grok_api.py chat "질문"
  python3 scripts/grok_api.py parse "https://m.blog.naver.com/..."
  python3 scripts/grok_api.py image "프롬프트 설명"

모델:
  grok-4-1-fast — 업무용 (가장 저렴, $0.20/$0.50 per 1M)
  grok-4.3     — 범용 플래그십 ($1.25/$2.50)
  grok-code-fast-1 — 코딩 에이전트 ($0.20/$1.50)
"""

import os, sys, json, subprocess, time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SECRETS = BASE / ".secrets.env"
TOKEN_FILE = BASE / "configs" / "grok_token.json"

# ── 인증 ────────────────────────────────────────────────────
def get_access_token():
    """OAuth 토큰 or API 키 로드. OAuth 우선."""
    # 1. OAuth 토큰 (SuperGrok 구독)
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE) as f:
            data = json.load(f)
            access_token = data.get("access_token", "")
            if access_token:
                return access_token

    # 2. API 키 (console.x.ai)
    if SECRETS.exists():
        with open(SECRETS) as f:
            for line in f:
                if line.startswith("XAI_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"\'')
                    if key:
                        return key

    return os.environ.get("XAI_API_KEY", "")

def load_auth():
    """인증 정보 로드. API 키면 api_key=, OAuth 토큰이면 base_url만 설정"""
    token = get_access_token()
    if not token:
        print("❌ 인증 정보 없음")
        print("   방법 1: bash scripts/grok_oauth_setup.sh (SuperGrok 구독)")
        print("   방법 2: .secrets.env 에 XAI_API_KEY=\"xai-...\" 추가")
        return None, None

    # OAuth 토큰이면 Bearer, API 키(xai-...)면 그대로
    return token, "https://api.x.ai/v1"
                if line.startswith("XAI_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"\'')
    return os.environ.get("XAI_API_KEY", "")

# ── Grok API 호출 ────────────────────────────────────────────
def grok_chat(prompt, model="grok-4-1-fast", system=None):
    """OpenAI 호환 API로 Grok 호출 (OAuth or API Key)"""
    token, base_url = load_auth()
    if not token:
        return None

    try:
        from openai import OpenAI
    except ImportError:
        print("❌ openai 패키지 필요: ~/browser-env/bin/pip install openai")
        return None

    client = OpenAI(
        api_key=token,
        base_url=base_url,
    )

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
    )

    return response.choices[0].message.content

# ── 네이버 파싱 + 요약 ─────────────────────────────────────────
def parse_naver_and_summarize(url):
    """proot curl로 네이버 파싱 → Grok이 요약"""
    # 1. 직접 파싱 (우리 폰에서)
    html = subprocess.run([
        "curl", "-sL", url,
        "-H", "User-Agent: Mozilla/5.0 (Linux; Android 13; SM-G991N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
        "-H", "Accept-Language: ko-KR,ko;q=0.9",
    ], capture_output=True, text=True, timeout=15).stdout

    # 2. 텍스트 추출
    import re
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '\n', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&[a-z]+;', '', text)
    lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 3]
    content = '\n'.join(lines[:100])  # 앞 100줄만

    # 3. Grok에게 요약 요청
    system = "너는 네이버 블로그 글을 읽고 핵심을 요약하는 AI다. 글의 주요 내용, 구조, 톤을 파악해서 한국어로 답변해라."
    prompt = f"다음은 네이버 블로그 글의 텍스트 추출본이다. 이 글을 읽고:\n1. 글의 주제와 핵심 메시지\n2. 주요 섹션/구조\n3. 글의 톤과 스타일\n4. 이 글에서 이미지/영상이 있으면 좋을 위치 제안\n\n---\n{content[:4000]}\n---"

    return grok_chat(prompt, system=system)

# ── 이미지 생성 프롬프트 ───────────────────────────────────────
def image_prompt(description, style="다크 테마, 터미널·코드·기술 미학"):
    """Grok에게 이미지 생성을 위한 상세 프롬프트 작성 요청"""
    system = "너는 AI 이미지 생성용 프롬프트를 작성하는 전문가다. 주어진 설명을 바탕으로 상세한 이미지 생성 프롬프트를 영어로 작성해라."
    prompt = f"다음 설명에 맞는 이미지 생성 프롬프트를 작성해줘:\n설명: {description}\n스타일: {style}\n\n영어로 상세하게 작성하고, 구도·색감·조명·분위기를 포함해라."

    return grok_chat(prompt, system=system)

# ── CLI ──────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        print("명령: chat | parse | image")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "chat":
        prompt = " ".join(sys.argv[2:])
        result = grok_chat(prompt)
        if result:
            print(result)

    elif cmd == "parse":
        url = sys.argv[2] if len(sys.argv) > 2 else input("Naver URL: ")
        result = parse_naver_and_summarize(url)
        if result:
            print(result)

    elif cmd == "image":
        desc = " ".join(sys.argv[2:])
        result = image_prompt(desc)
        if result:
            print(result)

    elif cmd == "setup":
        print("""
═══ Grok API 설정 방법 ═══

1. console.x.ai 접속 → 회원가입 (이메일/Google/X 계정)
2. 좌측 "API Keys" → "Create API Key"
3. 키 복사 (xai-... 형식, 한 번만 표시)
4. .secrets.env 에 추가:
   XAI_API_KEY="xai-..."

5. openai 패키지 설치:
   ~/browser-env/bin/pip install openai

6. 테스트:
   python3 scripts/grok_api.py chat "안녕"

※ 신규 계정 $25 무료 크레딧 (30일)
※ API와 SuperGrok 구독은 별도
""")
