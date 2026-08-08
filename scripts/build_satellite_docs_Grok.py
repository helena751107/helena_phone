#!/usr/bin/env python3
"""Build unified webzine-style HTML for Helena satellite repo markdown.

Agent: _Grok · bridges docs ↔ webpages across ecosystem satellites.
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

try:
    import markdown
    from markdown.extensions.toc import TocExtension
except ImportError:
    print("need markdown package", file=sys.stderr)
    sys.exit(1)

MD = markdown.Markdown(
    extensions=["tables", "fenced_code", "sane_lists", "smarty", "nl2br", "attr_list",
                TocExtension(permalink=False, toc_depth="2-3")],
    output_format="html5",
)

BRANDS = {
    "helana_log": {
        "name": "Helana Log",
        "accent": "#3db8a8",
        "home": "https://helena751107.github.io/helana_log/",
        "hub": "https://helena751107.github.io/helena_phone/",
        "kicker": "행정 대화록 · Docs",
    },
    "helana-faith": {
        "name": "Helana Faith",
        "accent": "#d4a84b",
        "home": "https://helena751107.github.io/helana-faith/",
        "hub": "https://helena751107.github.io/helena_phone/",
        "kicker": "Faith · Docs",
    },
    "helena-piano": {
        "name": "Helena Piano",
        "accent": "#8b7cf0",
        "home": "https://helena751107.github.io/helena-piano/",
        "hub": "https://helena751107.github.io/helena_phone/",
        "kicker": "Studio · Docs",
    },
    "helena-psycare": {
        "name": "Helena PsyCare",
        "accent": "#e85d4c",
        "home": "https://helena751107.github.io/helena-psycare/",
        "hub": "https://helena751107.github.io/helena_phone/",
        "kicker": "Care · Docs",
    },
    "helena-programming": {
        "name": "Helena Programming",
        "accent": "#3db8a8",
        "home": "https://helena751107.github.io/helena-programming/",
        "hub": "https://helena751107.github.io/helena_phone/",
        "kicker": "Engineering · Docs",
    },
}

SKIP_NAMES = {"_TEST_CONNECTION.md"}


def shell(brand: dict, title: str, deck: str, body: str, src: str, rel_home: str = "../") -> str:
    acc = brand["accent"]
    # depth for icons
    return f"""<!DOCTYPE html>
<html lang="ko" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="{html.escape(deck or title)}">
<meta name="theme-color" content="#0a0908">
<title>{html.escape(title)} — {html.escape(brand['name'])}</title>
<link rel="icon" href="{rel_home}icons/favicon-32.png" type="image/png">
<link rel="manifest" href="{rel_home}site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,600;1,400&family=DM+Sans:opsz,wght@9..40,400;9..40,600&family=JetBrains+Mono:wght@400&family=Noto+Sans+KR:wght@400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://helena751107.github.io/helena_phone/assets/webzine.css">
<style>
:root {{
  --ink:#f4efe6; --ink-dim:#b5a999; --ink-mute:#7a7064;
  --paper:#0a0908; --paper-2:#12100e; --paper-3:#1a1714;
  --rule:rgba(244,239,230,.1); --rule2:rgba(244,239,230,.18);
  --accent:{acc}; --gold:#d4a84b;
  --serif:'Cormorant Garamond',serif; --sans:'DM Sans','Noto Sans KR',system-ui,sans-serif;
  --mono:'JetBrains Mono',monospace;
  --gutter:max(22px, calc(env(safe-area-inset-left,0px) + 16px));
  --gutter-r:max(22px, calc(env(safe-area-inset-right,0px) + 16px));
}}
[data-theme="light"] {{
  --ink:#1a1510; --ink-dim:#5c5348; --ink-mute:#8a8074;
  --paper:#f7f1e6; --paper-2:#efe8db; --paper-3:#fffdf8;
  --rule:rgba(26,21,16,.1); --rule2:rgba(26,21,16,.18);
}}
*{{box-sizing:border-box;margin:0;padding:0}}
html{{scroll-behavior:smooth}}
body{{font-family:var(--sans);background:var(--paper);color:var(--ink);line-height:1.7;min-height:100vh}}
a{{color:var(--accent);text-decoration:none}}
a:hover{{filter:brightness(1.15)}}
.spine{{position:fixed;left:0;top:0;bottom:0;width:2px;background:var(--rule);z-index:50}}
.spine-fill{{width:100%;height:0;background:var(--accent)}}
.mast{{position:sticky;top:0;z-index:40;display:flex;justify-content:space-between;align-items:center;gap:12px;
  padding:12px var(--gutter-r) 12px var(--gutter);padding-top:max(12px,env(safe-area-inset-top));
  background:color-mix(in srgb,var(--paper) 90%,transparent);backdrop-filter:blur(12px);border-bottom:1px solid var(--rule)}}
.brand{{font-family:var(--serif);font-weight:700;letter-spacing:.06em;text-transform:uppercase;font-size:1rem;color:var(--ink)}}
.brand em{{font-style:italic;color:var(--accent);font-weight:400}}
.mast nav{{display:flex;flex-wrap:wrap;gap:6px}}
.mast a,.mast button{{font-size:.72rem;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-dim);
  min-height:40px;padding:8px 10px;background:none;border:none;cursor:pointer;font-family:inherit}}
.wrap{{max-width:720px;margin:0 auto;padding:28px var(--gutter-r) 80px var(--gutter)}}
.kicker{{font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-weight:600;margin-bottom:10px}}
h1{{font-family:var(--serif);font-size:clamp(1.7rem,6vw,2.4rem);font-weight:600;margin-bottom:10px;padding-inline:2px}}
.deck{{color:var(--ink-dim);font-weight:300;border-left:2px solid var(--accent);padding-left:12px;margin-bottom:18px}}
.meta{{font-size:.75rem;color:var(--ink-mute);margin-bottom:22px;font-family:var(--mono)}}
.prose h2{{font-family:var(--serif);font-size:1.35rem;margin:1.6em 0 .6em;color:var(--ink)}}
.prose h3{{font-size:1.05rem;margin:1.2em 0 .5em}}
.prose p,.prose li{{color:var(--ink-dim);font-weight:300;margin-bottom:.7em}}
.prose ul,.prose ol{{margin:0 0 1em 1.2em}}
.prose code{{font-family:var(--mono);font-size:.85em;color:var(--accent)}}
.prose pre{{background:var(--paper-2);border:1px solid var(--rule);padding:14px;overflow-x:auto;margin:1em 0;font-size:.82rem}}
.prose table{{width:100%;border-collapse:collapse;font-size:.88rem;margin:1em 0}}
.prose th,.prose td{{border:1px solid var(--rule);padding:8px 10px;text-align:left;vertical-align:top}}
.prose th{{background:var(--paper-3);color:var(--ink-mute);font-size:.72rem;letter-spacing:.06em;text-transform:uppercase}}
.prose blockquote{{border-left:2px solid var(--accent);padding:8px 14px;color:var(--ink-dim);margin:1em 0;background:var(--paper-2)}}
.appbar{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:18px;padding:10px;background:var(--paper-2);border:1px solid var(--rule);position:sticky;top:56px;z-index:30}}
.appbar input{{flex:1 1 140px;min-height:40px;padding:8px 10px;border:1px solid var(--rule2);background:var(--paper);color:var(--ink);font:inherit}}
.appbar button{{min-height:40px;padding:8px 12px;border:1px solid var(--rule2);background:var(--paper-3);color:var(--ink-dim);font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;cursor:pointer;font-family:inherit}}
.foot{{margin-top:40px;padding-top:18px;border-top:1px solid var(--rule);text-align:center;color:var(--ink-mute);font-size:.8rem}}
.foot .a{{color:var(--accent);margin-top:8px}}
.sec{{border:1px solid var(--rule);background:var(--paper-2);margin:1em 0;border-radius:2px;overflow:hidden}}
.sec > .sec-h{{width:100%;display:flex;justify-content:space-between;align-items:center;gap:10px;padding:12px 14px;background:none;border:none;color:inherit;font:inherit;cursor:pointer;text-align:left;min-height:48px}}
.sec > .sec-h h2{{margin:0;font-size:1.15rem;font-family:var(--serif)}}
.sec .ico{{width:28px;height:28px;border:1px solid var(--rule2);display:grid;place-items:center;color:var(--accent)}}
.sec.open .ico{{transform:rotate(45deg)}}
.sec .sec-b{{display:grid;grid-template-rows:0fr;transition:grid-template-rows .3s}}
.sec.open .sec-b{{grid-template-rows:1fr}}
.sec .sec-i{{overflow:hidden;min-height:0;opacity:0;padding:0 14px;transition:opacity .25s}}
.sec.open .sec-i{{opacity:1;padding:0 14px 14px}}
mark.hit{{background:color-mix(in srgb,var(--accent) 35%,transparent)}}
</style>
</head>
<body>
<div class="spine" aria-hidden="true"><div class="spine-fill" id="spineFill"></div></div>
<header class="mast">
  <a class="brand" href="{rel_home}">{html.escape(brand['name'].split()[0])} <em>{html.escape(brand['name'].split()[-1] if len(brand['name'].split())>1 else 'Docs')}</em></a>
  <nav>
    <a href="{rel_home}">Home</a>
    <a href="{rel_home}docs/">Docs</a>
    <a href="{html.escape(brand['hub'])}">Hub</a>
    <button type="button" id="themeBtn">Theme</button>
  </nav>
</header>
<main class="wrap">
  <div class="kicker">{html.escape(brand['kicker'])}</div>
  <h1>{html.escape(title)}</h1>
  {f'<p class="deck">{html.escape(deck)}</p>' if deck else ''}
  <div class="meta">source · {html.escape(src)} · bridge docs↔web · _Grok</div>
  <div class="appbar">
    <input type="search" id="q" placeholder="페이지 내 검색…" autocomplete="off">
    <button type="button" id="fold">접기</button>
    <button type="button" id="expand">펼치기</button>
  </div>
  <article class="prose" id="prose">{body}</article>
  <footer class="foot">
    <div>{html.escape(brand['name'])} · Docs Webzine</div>
    <div class="a">모든 계정은 큰누나 명의입니다.</div>
    <p style="margin-top:12px"><a href="{rel_home}">← Landing</a> · <a href="{html.escape(brand['hub'])}">S21 Hub</a></p>
  </footer>
</main>
<script>
(() => {{
  const root = document.documentElement;
  const saved = localStorage.getItem('helena-doc-theme');
  if (saved) root.setAttribute('data-theme', saved);
  document.getElementById('themeBtn')?.addEventListener('click', () => {{
    const n = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', n);
    localStorage.setItem('helena-doc-theme', n);
  }});
  const spine = document.getElementById('spineFill');
  addEventListener('scroll', () => {{
    const max = document.documentElement.scrollHeight - innerHeight;
    if (spine) spine.style.height = (max > 0 ? (scrollY / max) * 100 : 0) + '%';
  }}, {{ passive: true }});
  const prose = document.getElementById('prose');
  if (prose) {{
    [...prose.querySelectorAll(':scope > h2')].forEach((h2) => {{
      const sec = document.createElement('div');
      sec.className = 'sec open';
      const btn = document.createElement('button');
      btn.type = 'button'; btn.className = 'sec-h';
      const tw = document.createElement('div'); tw.appendChild(h2.cloneNode(true));
      const ico = document.createElement('span'); ico.className = 'ico'; ico.textContent = '+';
      btn.appendChild(tw); btn.appendChild(ico);
      const body = document.createElement('div'); body.className = 'sec-b';
      const inner = document.createElement('div'); inner.className = 'sec-i';
      let n = h2.nextSibling; const move = [];
      while (n && !(n.nodeType === 1 && n.tagName === 'H2')) {{ move.push(n); n = n.nextSibling; }}
      move.forEach(x => inner.appendChild(x));
      body.appendChild(inner); sec.appendChild(btn); sec.appendChild(body);
      h2.replaceWith(sec);
      btn.addEventListener('click', () => {{
        const on = !sec.classList.contains('open');
        sec.classList.toggle('open', on);
      }});
    }});
    const setAll = (open) => prose.querySelectorAll('.sec').forEach(s => s.classList.toggle('open', open));
    document.getElementById('fold')?.addEventListener('click', () => setAll(false));
    document.getElementById('expand')?.addEventListener('click', () => setAll(true));
    document.getElementById('q')?.addEventListener('input', (e) => {{
      const q = e.target.value.trim().toLowerCase();
      prose.querySelectorAll('.sec').forEach(sec => {{
        const hit = !q || sec.innerText.toLowerCase().includes(q);
        sec.style.display = hit ? '' : 'none';
        if (hit && q) sec.classList.add('open');
      }});
    }});
  }}
}})();
</script>
</body>
</html>
"""


def title_deck(md: str, fallback: str) -> tuple[str, str]:
    title, deck = fallback, ""
    for line in md.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break
    for line in md.splitlines():
        s = line.strip()
        if s.startswith(">") and len(s) > 2:
            deck = s.lstrip("> ").strip()
            break
    return title, deck


def build_repo(root: Path, brand_key: str) -> list[str]:
    brand = BRANDS[brand_key]
    built = []
    mds = []
    for p in root.rglob("*.md"):
        if any(x in p.parts for x in [".git"]):
            continue
        if p.name in SKIP_NAMES:
            continue
        # skip huge noise parksylog optional - include all non-test
        mds.append(p)

    for md_path in sorted(mds):
        rel = md_path.relative_to(root)
        raw = md_path.read_text(encoding="utf-8", errors="replace")
        title, deck = title_deck(raw, md_path.stem)
        MD.reset()
        body = MD.convert(raw)
        body = re.sub(r"^<h1[^>]*>.*?</h1>\s*", "", body, count=1, flags=re.I | re.S)
        # relative home depth
        depth = len(rel.parts) - 1
        rel_home = "../" * depth if depth > 0 else "./"
        if depth == 0:
            rel_home = "./"
        out = md_path.with_suffix(".html")
        # rewrite .md links in body to .html roughly
        body = re.sub(r'href="([^"]+)\.md"', r'href="\1.html"', body)
        page = shell(brand, title, deck, body, str(rel).replace("\\", "/"), rel_home=rel_home)
        out.write_text(page, encoding="utf-8")
        built.append(str(rel.with_suffix(".html")))

    # docs hub if docs/
    docs = root / "docs"
    if docs.is_dir():
        links = []
        for p in sorted(docs.rglob("*.html")):
            rel = p.relative_to(docs)
            links.append(f'<li><a href="{rel.as_posix()}">{html.escape(p.stem)}</a></li>')
        hub_body = "<p>문서 ↔ 웹페이지 브릿지. 검색·접기 지원.</p><ul>" + "".join(links) + "</ul>"
        hub = shell(brand, "Docs Hub", "문서 목록", hub_body, "docs/", rel_home="../")
        (docs / "index.html").write_text(hub, encoding="utf-8")
        built.append("docs/index.html")

    # root docs index listing all html from md
    all_links = []
    for p in sorted(root.rglob("*.html")):
        if p.name == "index.html" and p.parent == root:
            continue
        if p.name == "index.html" and p.parent.name == "docs":
            continue
        # only those paired with md or docs hub
        rel = p.relative_to(root)
        all_links.append(f'<li><a href="{rel.as_posix()}">{html.escape(str(rel))}</a></li>')
    if all_links:
        idx_body = "<p>이 레포의 문서 웹페이지 목록 (통일 템플릿 · _Grok).</p><ul>" + "".join(all_links) + "</ul>"
        # write pages/index or docs-bridge
        bridge_dir = root / "pages"
        bridge_dir.mkdir(exist_ok=True)
        page = shell(brand, f"{brand['name']} · Pages Bridge", "md→html 목록", idx_body, "pages/", rel_home="../")
        (bridge_dir / "index.html").write_text(page, encoding="utf-8")
        built.append("pages/index.html")

    return built


def main() -> int:
    base = Path(__file__).resolve().parents[1]  # /root/work/ (helena_phone root)
    mapping = {
        "helana_log": base / "helana_log",
        "helana-faith": base / "helena-faith",
        "helena-piano": base / "helena-piano",
        "helena-psycare": base / "helena-psycare",
        "helena-programming": base / "helena-programming",
    }
    total = 0
    for key, path in mapping.items():
        if not path.exists():
            print("skip missing", path)
            continue
        built = build_repo(path, key)
        total += len(built)
        print(f"OK {key}: {len(built)} pages")
        for b in built[:12]:
            print(" ", b)
        if len(built) > 12:
            print(f"  ... +{len(built)-12}")
    print(f"TOTAL {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
