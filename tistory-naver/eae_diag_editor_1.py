#!/usr/bin/env python3
import asyncio, sys
from pathlib import Path
from playwright.async_api import async_playwright

BASE = Path("/root/work/tistory-naver")
sys.path.insert(0, str(BASE))
from post import ensure_logged_in  # noqa: E402

async def main():
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            str(BASE / "cookies" / "eae-kr"), headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        await ensure_logged_in(page, "eae_kr@kakao.com", "eae-kr")
        await page.goto("https://eae-kr.tistory.com/manage/newpost/1?type=post", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        print("URL:", page.url)
        await page.screenshot(path="/tmp/edit_page.png", full_page=False)
        html = await page.content()
        Path("/tmp/edit_page.html").write_text(html, encoding="utf-8")
        print("saved screenshot+html, len=", len(html))
        await ctx.close()

asyncio.run(main())
