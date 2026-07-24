"""
티스토리 자동 포스팅 v1.0
- 저장된 세션(cookies/{id}_state.json) 사용
- posts/*.json 파일을 읽어 순서대로 발행
- 세션 만료 시 자동 재로그인

posts/ 디렉토리 구조:
  posts/
  └── 001_blogger-parksy.json   ← 파일명 형식 자유
      {
        "account": "dtslib",          ← accounts.json의 id
        "blog":    "blogger-parksy",  ← 블로그 슬러그
        "title":   "제목",
        "content": "<p>본문 HTML</p>",
        "tags":    ["태그1", "태그2"],
        "category": "",               ← 빈 문자열이면 미분류
        "visibility": "public"        ← public | private
      }

실행:
  python3 D:/1_GITHUB/dtslib-papyrus/tools/tistory/post.py
  python3 ... --post posts/001.json   ← 단일 파일
"""

import asyncio, argparse, json, re, time, sys
from pathlib import Path
from playwright.async_api import async_playwright

BASE          = Path(__file__).parent
ACCOUNTS_FILE = BASE / "accounts.json"
COOKIES_DIR   = BASE / "cookies"
POSTS_DIR     = BASE / "posts"
LOG_FILE      = BASE / "output" / f"post_{time.strftime('%Y%m%d_%H%M%S')}.log"

COOKIES_DIR.mkdir(exist_ok=True)
POSTS_DIR.mkdir(exist_ok=True)
LOG_FILE.parent.mkdir(exist_ok=True)

LOG_LINES = []
RESULTS   = {"success": [], "fail": []}

def log(msg):
    ts   = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    LOG_LINES.append(line)

def save_log():
    LOG_FILE.write_text("\n".join(LOG_LINES), encoding="utf-8")
    log(f"로그 저장: {LOG_FILE}")


# ── 카카오 재로그인 (세션 만료 시) ─────────────────────────
async def kakao_login(page, email, pw):
    log(f"  재로그인: {email}")
    await page.goto("https://www.tistory.com/auth/login",
                    wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(2000)

    try:
        btn = page.locator("a.btn_login.link_kakao_id, a[href*='kakao']").first
        await btn.wait_for(state="visible", timeout=8000)
        await btn.click()
        await page.wait_for_timeout(4000)
    except Exception as e:
        log(f"  카카오 버튼 없음: {e}")
        return False

    if "kakao.com" in page.url:
        try:
            other = page.locator(
                "a:has-text('다른 계정'), button:has-text('다른 계정'), a:has-text('계정 추가')"
            ).first
            if await other.is_visible(timeout=3000):
                await other.click()
                await page.wait_for_timeout(2000)
        except:
            pass

    try:
        await page.wait_for_selector(
            "#loginId--1, input[name='loginId'], input[autocomplete='username']",
            timeout=15000
        )
        await page.fill("#loginId--1, input[name='loginId'], input[autocomplete='username']", email)
        await page.wait_for_timeout(300)
        await page.fill("#password--2, input[name='password'], input[type='password']", pw)
        await page.wait_for_timeout(300)
        await page.click("button[type='submit'], .btn_g.btn_confirm, button.submit")
        await page.wait_for_timeout(5000)
    except Exception as e:
        log(f"  폼 입력 실패: {e}")

    for _ in range(10):
        url = page.url
        if "tistory.com" in url and "login" not in url and "kakao.com" not in url:
            log("  ✅ 재로그인 성공")
            return True
        await page.wait_for_timeout(1000)

    log(f"  ⚠ 자동 재로그인 실패 — 수동 60초 대기")
    for i in range(60):
        await page.wait_for_timeout(1000)
        url = page.url
        if "tistory.com" in url and "login" not in url and "kakao.com" not in url:
            log(f"  ✅ 수동 재로그인 성공 ({i+1}초)")
            return True

    return False


# ── 로그인 상태 확인 ────────────────────────────────────────
async def ensure_logged_in(page, email, pw):
    await page.goto("https://www.tistory.com/manage",
                    wait_until="domcontentloaded", timeout=20000)
    await page.wait_for_timeout(2000)
    url = page.url
    if "login" in url or "kakao.com" in url:
        return await kakao_login(page, email, pw)
    return True


# ── 포스트 발행 ─────────────────────────────────────────────
async def publish_post(page, post: dict):
    slug    = post["blog"]
    title   = post.get("title", "")
    content = post.get("content", "")
    tags    = post.get("tags", [])
    cat     = post.get("category", "")
    vis     = post.get("visibility", "public")

    write_url = f"https://{slug}.tistory.com/manage/newpost/?type=post"
    log(f"  [{slug}] 에디터 접근: {write_url}")
    await page.goto(write_url, wait_until="networkidle", timeout=30000)
    await page.wait_for_timeout(8000)

    # ── 제목 입력 (evaluate 직접 — visible 우회) ──
    title_filled = False
    try:
        # textarea#post-title-inp가 display:none일 수도 있으니 fill 강제
        title_ok = await page.evaluate(f"""(t) => {{
            const e = document.querySelector('#post-title-inp') || document.querySelector('textarea.textarea_tit');
            if (!e) return false;
            e.value = t;
            e.dispatchEvent(new Event('input', {{bubbles:true}}));
            e.dispatchEvent(new Event('change', {{bubbles:true}}));
            return true;
        }}""", title)
        if title_ok:
            title_filled = True
            log(f"  [{slug}] 제목 입력 OK (evaluate)")
    except Exception as e:
        log(f"  [{slug}] 제목 evaluate 실패: {e}")

    if not title_filled:
        log(f"  [{slug}] 제목 입력 실패")

    await page.wait_for_timeout(500)

    # ── 본문 입력 (블록 에디터 / iframe / textarea) ──
    content_filled = False

    # 0) TinyMCE iframe#editor-tistory_ifr 직접 (티스토리 진짜 에디터)
    try:
        # tinymce 전역 함수 사용 시도
        tin_ok = await page.evaluate(f"""(html) => {{
            try {{
                if (window.tinymce && tinymce.activeEditor) {{
                    tinymce.activeEditor.setContent(html);
                    return 'tinymce';
                }}
                const ifr = document.querySelector('iframe#editor-tistory_ifr');
                if (ifr && ifr.contentDocument) {{
                    const b = ifr.contentDocument.querySelector('body#tinymce, body');
                    if (b) {{ b.innerHTML = html; return 'iframe-body'; }}
                }}
                return false;
            }} catch(e) {{ return 'err:' + e.message; }}
        }}""", content)
        if tin_ok and tin_ok is not False and not str(tin_ok).startswith('err'):
            content_filled = True
            log(f"  [{slug}] 본문 입력 OK ({tin_ok})")
    except Exception as e:
        log(f"  [{slug}] TinyMCE 직접 실패: {e}")

    # 1) 블록 에디터 (contenteditable)
    for sel in [
        ".ProseMirror",
        "[contenteditable='true'].editor",
        "#editor-content [contenteditable='true']",
        ".editor_body [contenteditable='true']",
    ]:
        try:
            el = page.locator(sel).first
            if await el.is_visible(timeout=3000):
                await el.click()
                await page.keyboard.press("Control+a")
                await el.evaluate(f"el => el.innerHTML = {json.dumps(content)}")
                content_filled = True
                log(f"  [{slug}] 블록 에디터 본문 입력 OK")
                break
        except:
            pass

    # 2) iframe 에디터 (구형)
    if not content_filled:
        try:
            frame = page.frame_locator("iframe#editor-tistory_ifr, iframe[id*='editor']").first
            body  = frame.locator("body#tinymce, body")
            if await body.is_visible(timeout=3000):
                await body.evaluate(f"el => el.innerHTML = {json.dumps(content)}")
                content_filled = True
                log(f"  [{slug}] iframe 에디터 본문 입력 OK")
        except:
            pass

    # 3) HTML 직접 모드 textarea
    if not content_filled:
        for sel in ["textarea#content", "textarea.editor_content", "textarea"]:
            try:
                ta = page.locator(sel).first
                if await ta.is_visible(timeout=2000):
                    await ta.fill(content)
                    content_filled = True
                    log(f"  [{slug}] textarea 본문 입력 OK")
                    break
            except:
                pass

    if not content_filled:
        log(f"  [{slug}] 본문 입력 실패 — 스킵")
        RESULTS["fail"].append(f"{slug}:{title[:20]}")
        return False

    await page.wait_for_timeout(500)

    # ── 태그 입력 ──
    if tags:
        for sel in [
            "#tagText",
            "input[name='tag']",
            "input[placeholder*='태그']",
            ".tag_area input",
        ]:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=5000):
                    await el.click()
                    for tag in tags:
                        await el.fill(tag)
                        await page.keyboard.press("Enter")
                        await page.wait_for_timeout(300)
                    log(f"  [{slug}] 태그 입력 OK: {tags}")
                    break
            except:
                pass

    # ── 카테고리 선택 ──
    if cat:
        try:
            sel_el = page.locator("select#categoryId, select[name='categoryId']").first
            if await sel_el.is_visible(timeout=2000):
                await sel_el.select_option(label=cat)
                log(f"  [{slug}] 카테고리 선택 OK: {cat}")
        except:
            pass

    # ── 공개/비공개 설정 ──
    if vis == "private":
        try:
            priv = page.locator(
                "input[value='3'], label:has-text('비공개'), button:has-text('비공개')"
            ).first
            if await priv.is_visible(timeout=2000):
                await priv.click()
                log(f"  [{slug}] 비공개 설정 OK")
        except:
            pass

    await page.wait_for_timeout(500)

    # ── 발행 버튼 ──
    published = False
    for sel in [
        "button:has-text('발행')",
        "button:has-text('공개 발행')",
        "button:has-text('저장')",
        "#publish-btn",
        "input[type='submit'][value*='발행']",
    ]:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=3000):
                await btn.click()
                await page.wait_for_timeout(3000)
                # 최종 발행 확인 팝업이 뜰 수 있음
                for confirm_sel in ["button:has-text('확인')", "button:has-text('발행')"]:
                    try:
                        cf = page.locator(confirm_sel).first
                        if await cf.is_visible(timeout=2000):
                            await cf.click()
                            await page.wait_for_timeout(2000)
                    except:
                        pass
                published = True
                log(f"  [{slug}] ✅ 발행 완료: {title[:30]}")
                RESULTS["success"].append(f"{slug}:{title[:20]}")
                break
        except:
            pass

    if not published:
        log(f"  [{slug}] 발행 버튼 없음")
        RESULTS["fail"].append(f"{slug}:{title[:20]}")

    return published


# ── 계정별 처리 ─────────────────────────────────────────────
async def process_account(playwright, acc_id: str, acc_info: dict, posts: list):
    email = acc_info["email"]
    pw    = acc_info["password"]
    log(f"\n{'='*50}\n계정: {email} ({len(posts)}개 포스트)")

    state_path = COOKIES_DIR / f"{acc_id}_state.json"
    ctx_kwargs = dict(
        channel   = "chrome",
        headless  = False,
        viewport  = {"width": 1280, "height": 900},
        locale    = "ko-KR",
        args      = ["--no-first-run", "--no-default-browser-check"],
    )

    if state_path.exists():
        ctx = await playwright.chromium.launch_persistent_context(
            str(COOKIES_DIR / acc_id),
            **ctx_kwargs,
        )
    else:
        ctx = await playwright.chromium.launch_persistent_context(
            str(COOKIES_DIR / acc_id),
            **ctx_kwargs,
        )

    page = ctx.pages[0] if ctx.pages else await ctx.new_page()

    try:
        ok = await ensure_logged_in(page, email, pw)
        if not ok:
            log(f"  로그인 실패 — 계정 스킵")
            return

        await ctx.storage_state(path=str(state_path))

        for post in posts:
            try:
                await publish_post(page, post)
            except Exception as e:
                slug = post.get("blog", "?")
                title = post.get("title", "?")[:20]
                log(f"  [{slug}] 포스트 오류: {e}")
                RESULTS["fail"].append(f"{slug}:{title}")
            await page.wait_for_timeout(2000)

    except Exception as e:
        log(f"  계정 처리 오류: {e}")
    finally:
        await ctx.close()


# ── 메인 ────────────────────────────────────────────────────
async def main():
    parser = argparse.ArgumentParser(description="티스토리 자동 포스팅")
    parser.add_argument("--post", type=str, help="단일 포스트 JSON 파일 경로")
    args = parser.parse_args()

    log("=== 티스토리 자동 포스팅 v1.0 ===")

    data     = json.loads(ACCOUNTS_FILE.read_text(encoding="utf-8"))
    pw       = data["password"]
    acc_map  = {a["id"]: {**a, "password": pw} for a in data["accounts"]}

    # 포스트 파일 수집
    if args.post:
        post_files = [Path(args.post)]
    else:
        post_files = sorted(POSTS_DIR.glob("*.json"))

    if not post_files:
        log(f"❌ 포스트 파일 없음: {POSTS_DIR}")
        sys.exit(1)

    log(f"포스트 파일: {len(post_files)}개")

    # 계정별로 포스트 그룹화
    acc_posts: dict[str, list] = {}
    for pf in post_files:
        post = json.loads(pf.read_text(encoding="utf-8"))
        acc_id = post.get("account")
        if not acc_id:
            log(f"⚠ 'account' 필드 없음: {pf.name} — 스킵")
            continue
        if acc_id not in acc_map:
            log(f"⚠ 알 수 없는 계정: {acc_id} — 스킵")
            continue
        acc_posts.setdefault(acc_id, []).append(post)

    async with async_playwright() as pw_:
        for acc_id, posts in acc_posts.items():
            await process_account(pw_, acc_id, acc_map[acc_id], posts)
            await asyncio.sleep(3)

    log(f"\n{'='*50}")
    log(f"성공: {len(RESULTS['success'])}개 → {RESULTS['success']}")
    log(f"실패: {len(RESULTS['fail'])}개 → {RESULTS['fail']}")
    save_log()


if __name__ == "__main__":
    asyncio.run(main())
