#!/usr/bin/env python3
"""Method 2: JS 없이 그냥 이어붙이는 방식 (순수 HTML/CSS, 세로 스크롤 스택).
티스토리 글쓰기 HTML모드는 <script> 전부 제거하므로, 캐러셀/애니메이션 없이
img+figcaption만 세로로 쌓는 가장 단순하고 확실하게 렌더되는 방식."""
import base64, pathlib

def b64(path):
    return "data:image/jpeg;base64," + base64.b64encode(open(path, "rb").read()).decode()

ROOT = pathlib.Path("/root/work/tistory-naver")
CUTS = [
    ("/root/work/DCIM_pull/wtcut1_sm.jpg", "오늘도 새벽부터 시작한다."),
    ("/root/work/DCIM_pull/wtcut2_sm.jpg", "이걸 어떻게 이어붙일까, 그게 진짜 일이다."),
    ("/root/work/DCIM_pull/wtcut3_sm.jpg", "오늘 하루도, 폰 하나로 다 만들었다."),
]

panels = []
for i, (path, dialogue) in enumerate(CUTS, start=1):
    panels.append(f'''
  <figure class="pk-panel">
    <img src="{b64(path)}" alt="컷 {i}" loading="lazy">
    <figcaption class="pk-cap">{dialogue}</figcaption>
  </figure>''')

content = f'''<!-- Method 2: 순수 HTML/CSS 이어붙이기(JS 없음) — 티스토리 script 필터 회피 -->
<div class="pk-webtoon">
  <header class="pk-head">
    <div class="pk-eyebrow">EPISODE 1 · 아르누보</div>
    <h2 class="pk-title">박씨의 하루</h2>
  </header>
{"".join(panels)}
  <div class="pk-end">— 끝 —</div>
</div>

<style>
  .pk-webtoon{{max-width:640px;margin:0 auto;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans KR","Malgun Gothic",sans-serif;background:#181410;color:#f2ead9;padding:24px 0;border-radius:12px}}
  .pk-head{{text-align:center;padding:8px 20px 20px}}
  .pk-eyebrow{{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:#d4a84b;margin-bottom:6px}}
  .pk-title{{font-size:26px;margin:0;font-weight:800;color:#f2ead9}}
  .pk-panel{{margin:0 0 28px;padding:0 16px}}
  .pk-panel img{{display:block;width:100%;height:auto;border-radius:10px;border:2px solid #d4a84b}}
  .pk-cap{{margin-top:10px;padding:10px 14px;background:#241d15;border-left:3px solid #d4a84b;border-radius:4px;font-size:15px;line-height:1.5;color:#f2ead9}}
  .pk-end{{text-align:center;padding:12px 0 4px;color:#a8987a;font-size:13px;letter-spacing:.08em}}
</style>'''

post = {
    "account": "eae-kr",
    "blog": "eae-kr",
    "title": "박씨의 하루 — 아르누보 (Method 2: 순수 HTML 이어붙이기)",
    "content": content,
    "tags": ["웹툰", "아르누보", "박씨", "parksy-gallery-mcp"],
    "category": "웹툰",
    "visibility": "public",
}

import json
out = ROOT / "posts" / "eae-kr-parksy-arnouveau-method2.json"
json.dump(post, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("method2 post json:", out, "size:", len(post["content"]))
