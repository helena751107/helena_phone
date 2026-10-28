#!/usr/bin/env python3
"""Method 1: wt-viewer(French BD) 템플릿에 오늘 아르누보 3컷 주입 → eae-kr 발행 JSON."""
import base64, json, re, pathlib

def b64(path):
    return "data:image/jpeg;base64," + base64.b64encode(open(path, "rb").read()).decode()

ROOT = pathlib.Path("/root/work/tistory-naver")
images = [
    b64("/root/work/DCIM_pull/wtcut1_sm.jpg"),
    b64("/root/work/DCIM_pull/wtcut2_sm.jpg"),
    b64("/root/work/DCIM_pull/wtcut3_sm.jpg"),
]

tpl = open("/root/gifts/webtoon-viewer/wt-viewer-post.html", encoding="utf-8").read()
cfg = {
    "images": images,
    "title": "박씨의 하루",
    "episode": 1,
    "series": "아르누보 워크스테이션",
    "ctaText": "다음 편 보기",
    "ctaUrl": "",
}
tpl = re.sub(
    r"(var CONFIG = )\{.*?\n  \};",
    lambda m: m.group(1) + json.dumps(cfg, ensure_ascii=False, indent=4) + ";",
    tpl, flags=re.DOTALL,
)

post = {
    "account": "eae-kr",
    "blog": "eae-kr",
    "title": "박씨의 하루 — 아르누보 (Method 1: wt-viewer 프랑스BD 템플릿)",
    "content": tpl,
    "tags": ["웹툰", "아르누보", "박씨", "parksy-gallery-mcp"],
    "category": "웹툰",
    "visibility": "public",
}

out = ROOT / "posts" / "eae-kr-parksy-arnouveau-method1.json"
out.parent.mkdir(exist_ok=True)
json.dump(post, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("method1 post json:", out, "size:", len(post["content"]), "cuts:", len(images))
