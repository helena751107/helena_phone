#!/usr/bin/env python3
"""
Phase 1 — galaxys21-pwuser 티스토리 쿠키 저장 스크립트
=====================================================
방법 A (자동): 카카오 ID/PW로 직접 로그인 시도 → 쿠키 저장
방법 B (수동): 이미 로그인된 폰 브라우저에서 쿠키 복사 → 파일로 저장
=====================================================

사용법:
  방법 A: python3 scripts/save_tistory_cookie.py auto [카카오이메일] [비번]
  방법 B: python3 scripts/save_tistory_cookie.py manual  (쿠키 문자열을 stdin으로)

결과물: .tistory_session_galaxys21.json (Playwright storage_state 형식)
"""

import sys, os, json, asyncio
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
COOKIE_FILE = BASE / ".tistory_session_galaxys21.json"
BLOG = "galaxys21-pwuser"
TISTORY_LOGIN = "https://www.tistory.com/auth/login"
TISTORY_WRITE = f"https://{BLOG}.tistory.com/manage/newpost/"

async def method_auto(email, password):
    """Playwright로 카카오 로그인 자동화 → 쿠키 저장"""
    from playwright.async_api import async_playwright

    print(f"🔐 티스토리 자동 로그인 시도: {email}")
    print(f"   대상: {BLOG}.tistory.com")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=[
            '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
        ])
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Linux; Android 13; SM-G991N) AppleWebKit/537.36'
        )
        page = await context.new_page()

        # 1. 티스토리 로그인 페이지
        print("   ① 로그인 페이지 이동...")
        await page.goto(TISTORY_LOGIN, timeout=15000)
        await page.wait_for_timeout(2000)

        # 2. 카카오 로그인 버튼 클릭
        print("   ② 카카오 로그인 버튼 클릭...")
        try:
            kakao_btn = page.locator('button:has-text("카카오"), a:has-text("카카오"), .btn_kakao, [class*="kakao"]').first
            await kakao_btn.click(timeout=5000)
            await page.wait_for_timeout(3000)
        except:
            print("   ⚠️  카카오 버튼 없음. 직접 로그인 폼 시도...")
            # 이메일 로그인 fallback
            await page.goto(TISTORY_LOGIN, timeout=10000)

        # 3. 로그인 정보 입력 (카카오 로그인 페이지)
        print("   ③ 로그인 정보 입력...")
        try:
            # 카카오 이메일 필드
            email_input = page.locator('input[name="email"], input[name="id"], input[type="email"]').first
            await email_input.fill(email, timeout=5000)

            # 비밀번호 필드
            pw_input = page.locator('input[name="password"], input[name="pw"], input[type="password"]').first
            await pw_input.fill(password, timeout=5000)

            # 로그인 버튼
            submit = page.locator('button[type="submit"], button:has-text("로그인"), .btn_login').first
            await submit.click(timeout=5000)
            await page.wait_for_timeout(5000)
        except Exception as e:
            print(f"   ⚠️  로그인 폼 입력 실패: {e}")
            screenshot = await page.screenshot()
            (BASE / "_login_error.png").write_bytes(screenshot)
            print("   📸 스크린샷 저장: _login_error.png")
            await browser.close()
            return False

        # 4. 로그인 성공 확인
        print("   ④ 로그인 확인...")
        current_url = page.url

        if 'login' in current_url.lower() or 'auth' in current_url.lower():
            print("   ⚠️  로그인 실패 — CAPTCHA 또는 2FA 가능성")
            screenshot = await page.screenshot()
            (BASE / "_login_error.png").write_bytes(screenshot)
            print("   📸 스크린샷: _login_error.png")
            await browser.close()
            return False

        # 5. 쿠키 저장
        print("   ⑤ 쿠키 저장...")
        await context.storage_state(path=str(COOKIE_FILE))
        print(f"   ✅ 쿠키 저장 완료: {COOKIE_FILE}")

        # 6. 글쓰기 페이지 접근 테스트
        print("   ⑥ 글쓰기 페이지 접근 확인...")
        await page.goto(TISTORY_WRITE, timeout=15000)
        await page.wait_for_timeout(2000)

        if 'manage' in page.url or 'newpost' in page.url:
            print("   ✅ 글쓰기 페이지 접근 성공!")
        else:
            print(f"   ⚠️  글쓰기 페이지 접근 실패. 현재 URL: {page.url[:80]}")

        await browser.close()
        return True

async def method_manual(cookie_json_str=None):
    """수동으로 쿠키 JSON 입력받아 저장"""
    print("📋 티스토리 쿠키 수동 저장")
    print()
    print("   폰 브라우저(크롬)에서 galaxys21-pwuser.tistory.com 에 이미 로그인한 상태에서:")
    print("   1. 주소창에 javascript:document.cookie 입력 → 값 전체 복사")
    print("   2. 또는 개발자도구 → Application → Cookies → 값 복사")
    print()

    if not cookie_json_str:
        print("   쿠키 JSON 문자열을 입력하세요 (한 줄):")
        cookie_json_str = sys.stdin.readline().strip()

    if not cookie_json_str:
        print("❌ 쿠키 없음")
        return False

    try:
        # JSON 배열 또는 단순 문자열 처리
        if cookie_json_str.startswith('['):
            cookies = json.loads(cookie_json_str)
        else:
            # "name1=val1; name2=val2" 형식 처리
            cookies = []
            for pair in cookie_json_str.split(';'):
                pair = pair.strip()
                if '=' in pair:
                    name, value = pair.split('=', 1)
                    cookies.append({
                        'name': name.strip(),
                        'value': value.strip(),
                        'domain': '.tistory.com',
                        'path': '/',
                        'httpOnly': False,
                        'secure': True,
                        'sameSite': 'Lax',
                    })

        # Playwright storage_state 형식으로 저장
        state = {'cookies': cookies, 'origins': []}
        COOKIE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))
        print(f"✅ 쿠키 저장 완료: {COOKIE_FILE} ({len(cookies)}개)")
        return True

    except Exception as e:
        print(f"❌ 쿠키 파싱 실패: {e}")
        return False

async def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    method = sys.argv[1]

    if method == "auto":
        email = sys.argv[2] if len(sys.argv) > 2 else os.environ.get('TISTORY_EMAIL', '')
        password = sys.argv[3] if len(sys.argv) > 3 else os.environ.get('TISTORY_PW', '')

        if not email or not password:
            print("❌ 이메일/비밀번호 필요")
            print("   사용법: python3 save_tistory_cookie.py auto [이메일] [비밀번호]")
            print("   또는 환경변수: TISTORY_EMAIL, TISTORY_PW")
            sys.exit(1)

        ok = await method_auto(email, password)
        sys.exit(0 if ok else 1)

    elif method == "manual":
        cookie_str = sys.argv[2] if len(sys.argv) > 2 else None
        ok = await method_manual(cookie_str)
        sys.exit(0 if ok else 1)

    else:
        print(f"❌ 알 수 없는 방식: {method}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
