"""
티스토리 전계정 스킨 자동화 v3.0
- headless=False (카카오 봇탐지 우회)
- 계정별 독립 컨텍스트 (쿠키 오염 없음)
- 자동 로그인 실패 시 수동 대기 (60초)
- 실제 Chrome 사용 (channel='chrome')
- 블로그 슬러그 자동 발견 + accounts.json 업데이트

실행: python3 D:/1_GITHUB/dtslib-papyrus/tools/tistory/skin.py
"""

import asyncio, argparse, json, os, re, time, sys
from pathlib import Path
from playwright.async_api import async_playwright

# ── 경로 설정 ──────────────────────────────────────────────
BASE          = Path(__file__).parent
ACCOUNTS_FILE = BASE / "accounts.json"
COOKIES_DIR   = BASE / "cookies"
LOG_FILE      = BASE / "output" / f"skin_{time.strftime('%Y%m%d_%H%M%S')}.log"

# player.html 경로 우선순위:
#   1. --player CLI 인자
#   2. TISTORY_PLAYER_HTML 환경변수
#   3. 기본 경로 후보 순서대로
_PLAYER_FALLBACKS = [
    Path(r"D:\parksy-image\tools\tistory\player.html"),
    Path(r"D:\1_GITHUB\parksy-image\tools\tistory\player.html"),
    BASE.parent.parent.parent / "parksy-image" / "tools" / "tistory" / "player.html",
    BASE / "player.html",
]

COOKIES_DIR.mkdir(exist_ok=True)
LOG_FILE.parent.mkdir(exist_ok=True)

MARKER_START = "<!-- PARKSY-PLAYER-START -->"
MARKER_END   = "<!-- PARKSY-PLAYER-END -->"

# ── 로그 ──────────────────────────────────────────────────
LOG_LINES = []
RESULTS   = {"success": [], "skip": [], "fail": []}

def log(msg):
    ts   = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    LOG_LINES.append(line)

def save_log():
    LOG_FILE.write_text("\n".join(LOG_LINES), encoding="utf-8")
    log(f"로그 저장: {LOG_FILE}")

# ── 카카오 로그인 ──────────────────────────────────────────
async def kakao_login(page, email, pw):
    log(f"  로그인 시작: {email}")

    await page.goto("https://www.tistory.com/auth/login",
                    wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(2000)

    # 1. 카카오 로그인 버튼 클릭
    try:
        btn = page.locator("a.btn_login.link_kakao_id, a[href*='kakao']").first
        await btn.wait_for(state="visible", timeout=8000)
        await btn.click()
        await page.wait_for_timeout(4000)
        log("  카카오 버튼 클릭 OK")
    except Exception as e:
        log(f"  카카오 버튼 없음: {e}")
        return False

    url = page.url
    log(f"  리다이렉트 URL: {url[:80]}")

    # 2. 이미 다른 계정으로 로그인된 경우 — "다른 계정으로 로그인" 클릭
    if "kakao.com" in url:
        try:
            # "다른 계정으로 로그인" 또는 "계정 추가" 링크
            other = page.locator("a:has-text('다른 계정'), button:has-text('다른 계정'), a:has-text('계정 추가')").first
            if await other.is_visible(timeout=3000):
                await other.click()
                await page.wait_for_timeout(2000)
                log("  '다른 계정으로 로그인' 클릭")
        except:
            pass

    # 3. 카카오 로그인 폼 입력
    try:
        await page.wait_for_selector(
            "#loginId--1, input[name='loginId'], input[autocomplete='username']",
            timeout=15000
        )
        # ID
        id_sel = "#loginId--1, input[name='loginId'], input[autocomplete='username']"
        await page.fill(id_sel, email)
        await page.wait_for_timeout(300)
        # PW
        pw_sel = "#password--2, input[name='password'], input[type='password']"
        await page.fill(pw_sel, pw)
        await page.wait_for_timeout(300)
        # Submit
        await page.click("button[type='submit'], .btn_g.btn_confirm, button.submit")
        await page.wait_for_timeout(5000)
        log("  폼 제출 완료")
    except Exception as e:
        log(f"  폼 입력 실패: {e}")

    # 4. 결과 확인 (최대 10초 대기)
    for _ in range(10):
        url = page.url
        if "tistory.com" in url and "login" not in url and "kakao.com" not in url:
            log("  ✅ 자동 로그인 성공")
            return True
        await page.wait_for_timeout(1000)

    # 5. 자동 실패 → 수동 대기 (60초)
    log(f"  ⚠ 자동 로그인 실패. URL: {page.url[:80]}")
    log(f"  ⏳ 브라우저에서 수동 로그인 60초 대기 중... ({email})")
    for i in range(60):
        await page.wait_for_timeout(1000)
        url = page.url
        if "tistory.com" in url and "login" not in url and "kakao.com" not in url:
            log(f"  ✅ 수동 로그인 성공 ({i+1}초)")
            return True

    log(f"  ❌ 로그인 최종 실패: {email}")
    return False


# ── 블로그 슬러그 발견 ──────────────────────────────────────
async def get_blog_slugs(page):
    await page.goto("https://www.tistory.com/manage",
                    wait_until="domcontentloaded", timeout=20000)
    await page.wait_for_timeout(3000)

    links = await page.eval_on_selector_all("a", "els => els.map(e => e.href)")
    slugs = []
    seen  = set()
    for link in links:
        m = re.search(r"https?://([a-z0-9][a-z0-9\-]+)\.tistory\.com", link)
        if m:
            s = m.group(1)
            if s not in seen and s not in ("www", "admin", "api"):
                seen.add(s)
                slugs.append(s)
    return slugs


# ── 스킨 HTML 삽입 ─────────────────────────────────────────
async def inject_skin(page, slug, player_html):
    skin_url = f"https://{slug}.tistory.com/manage/skin/edit"
    log(f"    [{slug}] 스킨 편집 접근")
    await page.goto(skin_url, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(3000)

    # HTML 탭 클릭
    for sel in ["button:has-text('HTML')", "a:has-text('HTML')", ".tab_html", "[data-type='html']"]:
        try:
            el = page.locator(sel).first
            if await el.is_visible(timeout=2000):
                await el.click()
                await page.wait_for_timeout(1500)
                break
        except:
            pass

    inject_block = f"\n{MARKER_START}\n{player_html}\n{MARKER_END}\n"

    # CodeMirror 에디터
    try:
        cm_el = page.locator(".CodeMirror").first
        if await cm_el.is_visible(timeout=5000):
            # 현재 내용 읽기
            cur = await page.evaluate("""
                () => {
                    const cm = document.querySelector('.CodeMirror')?.CodeMirror;
                    return cm ? cm.getValue() : null;
                }
            """)
            if cur is None:
                log(f"    [{slug}] CodeMirror.getValue() 실패")
            elif MARKER_START in cur:
                log(f"    [{slug}] 이미 삽입됨 — 스킵")
                RESULTS["skip"].append(slug)
                return True
            else:
                new_val = inject_block + cur
                await page.evaluate(f"""
                    () => {{
                        const cm = document.querySelector('.CodeMirror')?.CodeMirror;
                        if (cm) cm.setValue({json.dumps(new_val)});
                    }}
                """)
                log(f"    [{slug}] CodeMirror 삽입 완료")
                return await _save(page, slug)
    except Exception as e:
        log(f"    [{slug}] CodeMirror 오류: {e}")

    # Textarea 폴백
    try:
        ta = page.locator("textarea[name='skinHtml'], textarea.code, textarea").first
        if await ta.is_visible(timeout=3000):
            cur = await ta.input_value()
            if MARKER_START in cur:
                log(f"    [{slug}] 이미 삽입됨 — 스킵")
                RESULTS["skip"].append(slug)
                return True
            await ta.fill(inject_block + cur)
            log(f"    [{slug}] Textarea 삽입 완료")
            return await _save(page, slug)
    except Exception as e:
        log(f"    [{slug}] Textarea 오류: {e}")

    log(f"    [{slug}] 에디터 없음 — 실패")
    RESULTS["fail"].append(slug)
    return False


async def _save(page, slug):
    for sel in ["button:has-text('저장')", "button:has-text('적용')", "input[type='submit'][value*='저장']"]:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=3000):
                await btn.click()
                await page.wait_for_timeout(2000)
                log(f"    [{slug}] ✅ 저장 완료")
                RESULTS["success"].append(slug)
                return True
        except:
            pass
    log(f"    [{slug}] 저장 버튼 없음")
    RESULTS["fail"].append(slug)
    return False


# ── 계정별 처리 ────────────────────────────────────────────
async def process_account(playwright, acc, player_html):
    email = acc["email"]
    log(f"\n{'='*50}\n계정: {email}")

    ctx = await playwright.chromium.launch_persistent_context(
        str(COOKIES_DIR / acc["id"]),
        channel        = "chrome",
        headless       = False,
        viewport       = {"width": 1280, "height": 900},
        locale         = "ko-KR",
        args           = ["--no-first-run", "--no-default-browser-check"],
    )
    page = ctx.pages[0] if ctx.pages else await ctx.new_page()

    try:
        ok = await kakao_login(page, email, acc["password"])
        if not ok:
            log(f"  로그인 실패 — 계정 스킵")
            return

        # 세션 저장
        await ctx.storage_state(path=str(COOKIES_DIR / f"{acc['id']}_state.json"))
        log(f"  세션 저장: {acc['id']}_state.json")

        # 블로그 슬러그 발견
        slugs = await get_blog_slugs(page)
        log(f"  발견 블로그: {slugs}")

        if not slugs:
            log("  블로그 없음 — 스킵")
            return

        # accounts.json 슬러그 업데이트
        acc["blogs"] = slugs

        # 스킨 삽입
        for slug in slugs:
            try:
                await inject_skin(page, slug, player_html)
            except Exception as e:
                log(f"    [{slug}] 오류: {e}")
                RESULTS["fail"].append(slug)
            await page.wait_for_timeout(1000)

    except Exception as e:
        log(f"  계정 처리 오류: {e}")
    finally:
        await ctx.close()


# ── 메인 ──────────────────────────────────────────────────
async def main():
    parser = argparse.ArgumentParser(description="티스토리 전계정 스킨 자동화")
    parser.add_argument("--player", type=str, help="player.html 경로 (기본: 자동 탐색)")
    args = parser.parse_args()

    log("=== 티스토리 전계정 스킨 자동화 v3.0 ===")

    # player.html 경로 결정
    player_path = None
    if args.player:
        player_path = Path(args.player)
    elif os.environ.get("TISTORY_PLAYER_HTML"):
        player_path = Path(os.environ["TISTORY_PLAYER_HTML"])
    else:
        for p in _PLAYER_FALLBACKS:
            if p.exists():
                player_path = p
                break

    if not player_path or not player_path.exists():
        searched = "\n  ".join(str(p) for p in _PLAYER_FALLBACKS)
        log(f"❌ player.html 없음. 아래 위치 탐색 실패:\n  {searched}")
        log("해결 방법:")
        log("  1. python3 skin.py --player D:/path/to/player.html")
        log("  2. set TISTORY_PLAYER_HTML=D:/path/to/player.html")
        log("  3. tools/tistory/player.html 에 직접 복사")
        sys.exit(1)

    player_html = player_path.read_text(encoding="utf-8")
    log(f"player.html 로드: {player_path} ({len(player_html)}자)")

    # accounts.json 로드
    data = json.loads(ACCOUNTS_FILE.read_text(encoding="utf-8"))
    accounts = []
    pw = data["password"]
    for a in data["accounts"]:
        accounts.append({**a, "password": pw})

    async with async_playwright() as pw_:
        for acc in accounts:
            await process_account(pw_, acc, player_html)
            await asyncio.sleep(3)

    # accounts.json에 발견된 슬러그 저장
    for a_out, a_in in zip(accounts, data["accounts"]):
        a_in["blogs"] = a_out.get("blogs", a_in.get("blogs", []))
    ACCOUNTS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    log("accounts.json 슬러그 업데이트 완료")

    # 결과 요약
    log(f"\n{'='*50}")
    log(f"성공: {len(RESULTS['success'])}개 → {RESULTS['success']}")
    log(f"스킵: {len(RESULTS['skip'])}개 → {RESULTS['skip']}")
    log(f"실패: {len(RESULTS['fail'])}개 → {RESULTS['fail']}")
    save_log()


if __name__ == "__main__":
    asyncio.run(main())
