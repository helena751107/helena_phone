#!/usr/bin/env python3
"""오늘 만든 Method1(JS기반, 빈페이지 확인됨) 중복 글 2개만 삭제 — eae-kr /2, /3."""
import asyncio, sys, time
from pathlib import Path
from playwright.async_api import async_playwright

BASE = Path("/root/work/tistory-naver")
sys.path.insert(0, str(BASE))
from post import ensure_logged_in  # noqa: E402

TARGET_IDS = [2, 3]  # 오늘 발행한 빈페이지 Method1 시도 2건 (재시도 전/후)

async def main():
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            str(BASE / "cookies" / "eae-kr"), headless=True,
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        await ensure_logged_in(page, "eae-kr", "eae-kr")
        for pid in TARGET_IDS:
            r = await page.request.delete(f"https://eae-kr.tistory.com/manage/post/{pid}.json")
            print(pid, r.status, (await r.text())[:200])
        await ctx.close()

asyncio.run(main())
