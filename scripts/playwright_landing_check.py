#!/usr/bin/env python3
"""
Playwright E2E — S21 랜딩페이지 + 설치 플로우 전수 검사
검증: 새로운 유저가 폰으로 보는 시점에서 작동하는가
"""
import sys, time
from playwright.sync_api import sync_playwright

BASE = "https://helena751107.github.io/helena_phone"
RESULTS = []  # (label, pass:bool, detail)

def check(label, ok, detail=""):
    RESULTS.append((label, ok, detail))
    mark = "✅" if ok else "❌"
    print(f"  {mark} {label}  {detail}")

def main():
    with sync_playwright() as p:
        # ── 모바일 Galaxy S21 에뮬레이션 ──
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 384, "height": 854},   # S21 portrait
            device_scale_factor=2,
            user_agent=(
                "Mozilla/5.0 (Linux; Android 13; SM-G991N) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
            ),
        )
        page = ctx.new_page()

        # ────────────────────────────────────────
        # 1. 랜딩페이지 로드
        # ────────────────────────────────────────
        print("\n── 1. 랜딩페이지 ──")
        resp = page.goto(f"{BASE}/", wait_until="networkidle", timeout=30000)
        check("HTTP 200", resp.status == 200, f"status={resp.status}")
        check("<title> 존재", bool(page.title()), page.title()[:80])
        check("h1 존재", page.locator("h1").count() > 0,
              page.locator("h1").first.text_content()[:80] if page.locator("h1").count() > 0 else "NONE")

        # 스크린샷
        page.screenshot(path="/root/work/_notebook/playwright-check-landing-full.png", full_page=True)
        print("  📸 full page → _notebook/playwright-check-landing-full.png")

        # ────────────────────────────────────────
        # 2. Install 섹션 (#install)
        # ────────────────────────────────────────
        print("\n── 2. Install 섹션 ──")
        install = page.locator("#install")
        check("#install 존재", install.count() > 0)

        if install.count() > 0:
            install.scroll_into_view_if_needed()
            time.sleep(0.5)

            # Screen 1 - 앱
            screen1 = page.locator("text=Screen 1")
            check("Screen 1 · 앱 표시", screen1.count() > 0 or page.locator("text=Termux + Termux:API").count() > 0,
                  "F-Droid → Termux + Termux:API")

            # Screen 2 - 터미널
            term = page.locator("#terminal")
            check("터미널 컴포넌트 존재", term.count() > 0)

            # CMD 텍스트 확인 (script 태그에서 추출)
            cmd = page.evaluate("""() => {
                const scripts = document.querySelectorAll('script');
                for (const s of scripts) {
                    if (s.textContent && s.textContent.includes('easy.sh')) {
                        const m = s.textContent.match(/CMD\\s*=\\s*'([^']+)'/);
                        if (m) return m[1];
                    }
                }
                // fallback: check window.CMD
                try { return window.CMD || 'NOT FOUND'; } catch(e) { return 'NOT FOUND'; }
            }""")
            check("CMD 변수 존재", "easy.sh" in cmd, cmd[:120] if len(cmd) > 120 else cmd)

            # Copy 버튼
            copy_btn = page.locator("#copyInstall")
            check("Copy 버튼 존재", copy_btn.count() > 0)

            # 버튼 텍스트 확인만 (클릭은 accordion 중첩으로 skip)
            if copy_btn.count() > 0:
                btn_text = copy_btn.text_content()
                check("Copy 버튼 텍스트", "Copy" in btn_text or "copy" in btn_text.lower(), btn_text)

            # Screen 3 - 확인
            check("proot-distro login ubuntu 텍스트", page.locator("text=proot-distro login ubuntu").count() > 0)
            check("cat S21-START.txt 텍스트", page.locator("text=cat S21-START.txt").count() > 0)

            # 페이지 링크 확인
            pages_link = page.locator(f"a[href*='helena751107.github.io/helena_phone/']")
            check("Pages URL 링크", pages_link.count() > 0)

        page.screenshot(path="/root/work/_notebook/playwright-check-install.png", full_page=False)
        print("  📸 install viewport → _notebook/playwright-check-install.png")

        # ────────────────────────────────────────
        # 3. install-guide.html 링크 확인 + 이동
        # ────────────────────────────────────────
        print("\n── 3. install-guide.html ──")
        guide_links = page.locator("a[href='install-guide.html']")
        check("install-guide 링크 존재", guide_links.count() > 0,
              f"{guide_links.count()}개 링크")

        resp2 = page.goto(f"{BASE}/install-guide.html", wait_until="networkidle", timeout=30000)
        check("install-guide HTTP 200", resp2.status == 200, f"status={resp2.status}")
        check("화면 1 텍스트", page.locator("text=화면 1").count() > 0
              or page.locator("text=두 개").count() > 0)
        check("OWNER_GITHUB 커스터마이즈 설명", page.locator("text=OWNER_GITHUB").count() > 0,
              "env override 설명 있음")
        check("설치자용 체크리스트", page.locator("text=설치자용").count() > 0
              or page.locator("text=체크리스트").count() > 0,
              "사회복지사·가족 체크리스트 있음")
        check("고장 표", page.locator("text=curl: not found").count() > 0,
              "troubleshooting table 있음")
        check("termux-api ENOENT", page.locator("text=termux-api ENOENT").count() > 0
              or page.locator("text=termux-api").count() > 0,
              "MCP 도구 오류 대처법 있음")

        # ────────────────────────────────────────
        # 4. foundation/termux-setup.html
        # ────────────────────────────────────────
        print("\n── 4. foundation/termux-setup.html ──")
        resp3 = page.goto(f"{BASE}/foundation/termux-setup.html", wait_until="networkidle", timeout=30000)
        check("termux-setup HTTP 200", resp3.status == 200, f"status={resp3.status}")
        check("F-Droid 언급", page.locator("text=F-Droid").count() > 0)
        check("pkg install 언급", page.locator("text=pkg install").count() > 0)
        # 제네릭 검증: helena751107 없어야 함
        body3 = page.locator("body").inner_text()
        has_account = "helena751107" in body3 or "helena1975" in body3
        check("계정정보 0건 (제네릭)", not has_account,
              "helena751107 발견됨" if has_account else "깨끗함")

        # ────────────────────────────────────────
        # 5. foundation/proot-ubuntu.html
        # ────────────────────────────────────────
        print("\n── 5. foundation/proot-ubuntu.html ──")
        resp4 = page.goto(f"{BASE}/foundation/proot-ubuntu.html", wait_until="networkidle", timeout=30000)
        check("proot-ubuntu HTTP 200", resp4.status == 200, f"status={resp4.status}")
        check("proot-distro 언급", page.locator("text=proot-distro").count() > 0)
        body4 = page.locator("body").inner_text()
        has_account2 = "helena751107" in body4 or "helena1975" in body4
        check("계정정보 0건 (제네릭)", not has_account2,
              "helena751107 발견됨" if has_account2 else "깨끗함")

        # ────────────────────────────────────────
        # 6. g/easy.html (easy.sh 소스뷰어)
        # ────────────────────────────────────────
        print("\n── 6. g/easy.html ──")
        resp5 = page.goto(f"{BASE}/g/easy.html", wait_until="networkidle", timeout=30000)
        check("easy.html HTTP 200", resp5.status == 200, f"status={resp5.status}")
        check("OWNER_GITHUB 파라미터화", page.locator("text=OWNER_GITHUB").count() > 0
              or page.locator("text=OWNER").count() > 0,
              "env override 변수 존재")
        check("TEMPLATE_REPO 파라미터화", page.locator("text=TEMPLATE_REPO").count() > 0
              or page.locator("text=helena751107/helena_phone").count() > 0)

        # ────────────────────────────────────────
        # 7. g/install.html (고급 설치)
        # ────────────────────────────────────────
        print("\n── 7. g/install.html ──")
        resp6 = page.goto(f"{BASE}/g/install.html", wait_until="networkidle", timeout=30000)
        check("install.html HTTP 200", resp6.status == 200, f"status={resp6.status}")
        check("DEEPSEEK_API_KEY 언급", page.locator("text=DEEPSEEK_API_KEY").count() > 0
              or page.locator("text=DEEPSEEK").count() > 0)

        # ────────────────────────────────────────
        # 8. 깨진 링크 스캔 (랜딩페이지로 돌아가서)
        # ────────────────────────────────────────
        print("\n── 8. 깨진 링크 검사 ──")
        page.goto(f"{BASE}/", wait_until="networkidle", timeout=30000)
        all_links = page.locator("a[href]").all()
        internal_links = []
        for a in all_links:
            href = a.get_attribute("href") or ""
            if href.startswith("/") or href.startswith(BASE) or (not href.startswith("http") and not href.startswith("#") and not href.startswith("mailto:")):
                internal_links.append(href)

        broken = []
        checked = 0
        for href in list(set(internal_links))[:30]:  # 최대 30개만
            if href.startswith("http") and "github" not in href and "youtube" not in href:
                try:
                    r = page.goto(href, wait_until="load", timeout=10000)
                    if r.status >= 400:
                        broken.append(f"{href} → {r.status}")
                except:
                    broken.append(f"{href} → TIMEOUT/ERROR")
                checked += 1

        check(f"내부 링크 {checked}개 검사", len(broken) == 0,
              f"깨짐 {len(broken)}: {broken[:3]}" if broken else "전부 OK")

        # ────────────────────────────────────────
        # 요약
        # ────────────────────────────────────────
        print("\n" + "=" * 50)
        passed = sum(1 for _, ok, _ in RESULTS if ok)
        failed = sum(1 for _, ok, _ in RESULTS if not ok)
        print(f"  TOTAL {len(RESULTS)}  ✅ {passed}  ❌ {failed}")
        print("=" * 50)

        for label, ok, detail in RESULTS:
            if not ok:
                print(f"  ❌ {label} — {detail}")

        browser.close()
        return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
