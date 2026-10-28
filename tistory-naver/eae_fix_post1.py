#!/usr/bin/env python3
"""eae-kr /1 (프랑스 BD 샘플, JS기반이라 빈페이지 확인됨)을 JS-free 방식으로 수정."""
import asyncio, json, re, sys
from pathlib import Path
from playwright.async_api import async_playwright

BASE = Path("/root/work/tistory-naver")
sys.path.insert(0, str(BASE))
from post import ensure_logged_in, _fill_and_save  # noqa: E402

# 원본 /1 글의 base64 이미지 2장 재사용
old = json.load(open(BASE / "posts" / "eae-kr-french-bd-sample.json", encoding="utf-8"))
old_content = old["content"]
images = re.findall(r'"(data:image/jpeg;base64,[^"]+)"', old_content)
print("found images:", len(images))

captions = ["Bonjour !", "C'est la vie !"]
panels = []
for i, (img, cap) in enumerate(zip(images, captions), start=1):
    panels.append(f'''
  <figure class="pk-panel">
    <img src="{img}" alt="컷 {i}" loading="lazy">
    <figcaption class="pk-cap">{cap}</figcaption>
  </figure>''')

content = f'''<!-- JS-free 재발행 (2026-08-30) — 원본 wt-viewer 템플릿은 티스토리 script 필터에 전부 제거되어 빈페이지였음 -->
<div class="pk-webtoon">
  <header class="pk-head">
    <div class="pk-eyebrow">EPISODE 4 · 프랑스 만화 테스트</div>
    <h2 class="pk-title">파리에서 온 편지</h2>
  </header>
{"".join(panels)}
  <div class="pk-end">— 끝 —</div>
</div>

<style>
  .pk-webtoon{{max-width:640px;margin:0 auto;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans KR","Malgun Gothic",sans-serif;background:#111;color:#f2f2f2;padding:24px 0;border-radius:12px}}
  .pk-head{{text-align:center;padding:8px 20px 20px}}
  .pk-eyebrow{{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:#ff4d4d;margin-bottom:6px}}
  .pk-title{{font-size:26px;margin:0;font-weight:800;color:#f2f2f2}}
  .pk-panel{{margin:0 0 28px;padding:0 16px}}
  .pk-panel img{{display:block;width:100%;height:auto;border-radius:10px;border:2px solid #ff4d4d}}
  .pk-cap{{margin-top:10px;padding:10px 14px;background:#1c1c1c;border-left:3px solid #ff4d4d;border-radius:4px;font-size:15px;line-height:1.5;color:#f2f2f2}}
  .pk-end{{text-align:center;padding:12px 0 4px;color:#999;font-size:13px;letter-spacing:.08em}}
</style>'''

async def main():
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            str(BASE / "cookies" / "eae-kr"), headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        await ensure_logged_in(page, "eae_kr@kakao.com", "eae-kr")
        ok = await _fill_and_save(
            page, "eae-kr", 1,
            "프랑스 BD 스타일 웹툰 샘플 (JS-free 재발행)",
            content,
            ["웹툰", "프랑스만화", "샘플"],
            "웹툰",
            "public",
        )
        print("fixed:", ok)
        await ctx.close()

asyncio.run(main())
