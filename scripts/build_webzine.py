#!/usr/bin/env python3
"""
Build all S21 Phone webzine HTML pages from markdown + code sources.
Matches landing-page editorial design via assets/webzine.css.
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
from pathlib import Path

import markdown
from markdown.extensions.toc import TocExtension

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)

MD = markdown.Markdown(
    extensions=[
        "tables",
        "fenced_code",
        "sane_lists",
        "smarty",
        "nl2br",
        "attr_list",
        TocExtension(permalink=False, toc_depth="2-3"),
    ],
    output_format="html5",
)

# ── catalog: source → output html, title, section ──────────────
# section used for nav grouping / related pages

CATALOG: list[dict] = []


def add(src: str, out: str, title: str, section: str, kind: str = "md", deck: str = ""):
    CATALOG.append(
        {
            "src": src,
            "out": out,
            "title": title,
            "section": section,
            "kind": kind,
            "deck": deck,
        }
    )


# Core
add("CONSTITUTION.md", "constitution.html", "헌법 CONSTITUTION", "Core", deck="불변 원칙 · Chain of Command")
add("CLAUDE.md", "claude.html", "실무 규칙 CLAUDE.md", "Core", deck="AI 3종 · Paste Pipeline · 인프라")
add("README.md", "readme.html", "README · 프로젝트 소개", "Core", deck="숫자 · 구조 · 빠른 링크")
add("GUIDE.md", "guide.html", "5단계 GUIDE", "Core", deck="Termux부터 방송까지")
add("CHRONICLE.md", "chronicle.html", "CHRONICLE · 연대기", "Core", deck="DAY 1–2 개발 기록")
add("GIFT.md", "gift.html", "GIFT · dtslib 선물", "Core", deck="선물 패키지 분석")
add("_textbook/index.md", "textbook.html", "완결판 교재", "Core", deck="판단층 + 실행층")
add("install-guide.md", "install-guide.html", "초심자 설치 매뉴얼", "Core", deck="낡은 폰→헬레나 전체 동선 · 변수화")

# Foundation
for name, title in [
    ("termux-setup.md", "Termux 설치"),
    ("proot-ubuntu.md", "proot Ubuntu"),
    ("claude-code.md", "Claude Code"),
    ("git-github.md", "Git · GitHub"),
]:
    p = f"01-foundation/{name}"
    if (ROOT / p).exists():
        add(p, f"foundation/{name.replace('.md', '.html')}", title, "Foundation")

# Network guides
for name, title in [
    ("discord.md", "Discord"),
    ("telegram.md", "Telegram"),
    ("github-pages.md", "GitHub Pages"),
]:
    p = f"02-network/{name}"
    if (ROOT / p).exists():
        add(p, f"network/{name.replace('.md', '.html')}", title, "Network")


# Auto stubs — broadcast / phone-control / optimization
for name, title, sec, outdir in [
    ("03-broadcast/youtube.md", "YouTube 채널", "Broadcast", "broadcast"),
    ("03-broadcast/tistory-auto.md", "티스토리 자동화", "Broadcast", "broadcast"),
    ("03-broadcast/naver-auto.md", "네이버 자동화", "Broadcast", "broadcast"),
    ("04-phone-control/termux-api.md", "Termux:API", "Phone Control", "phone-control"),
    ("04-phone-control/phone-mcp.md", "phone-mcp-server", "Phone Control", "phone-control"),
    ("04-phone-control/health-check.md", "건강 검진", "Phone Control", "phone-control"),
    ("05-optimization/battery-saving.md", "배터리 최적화", "Optimization", "optimization"),
    ("05-optimization/performance.md", "성능 튜닝", "Optimization", "optimization"),
    ("05-optimization/storage.md", "저장공간 관리", "Optimization", "optimization"),
]:
    if (ROOT / name).exists():
        add(name, f"{outdir}/{Path(name).name.replace('.md','.html')}", title, sec)

# Notebook (from _notebook)
NOTEBOOK_TITLES = {
    "00-INDEX.md": "업무 수첩 목차",
    "01-arch.md": "시스템 아키텍처",
    "02-discord.md": "Discord",
    "03-telegram.md": "Telegram",
    "04-github-pages.md": "Pages · Giscus",
    "05-tistory.md": "티스토리",
    "06-youtube.md": "YouTube",
    "07-cli-reference.md": "CLI 레퍼런스",
    "08-secrets.md": "비밀 관리",
    "09-ecosystem.md": "생태계 브릿지",
    "10-phone-mcp.md": "phone-MCP 18도구",
    "11-health.md": "건강 검진",
    "12-dtslib-gift.md": "dtslib 선물 분석",
    "13-midterm-eval.md": "중간평가 v1",
    "13-midterm-eval-v2.md": "중간평가 v2",
    "14-daemon-design.md": "돌봄 데몬 설계",
    "15-proot-report.md": "proot 종합 보고서",
    "16-textbook-methodology.md": "교재 합성 지침",
    "17-merged-chronicle.md": "병합 연대기",
    "18-workcenters.md": "워크센터 초안",
    "19-final-strategy.md": "최종 전략",
    "20-workcenters-final.md": "워크센터 최종",
    "21-integrated-dev-plan.md": "통합 개발 계획서",
    "22-s21-benchmark.md": "S21 벤치마크",
    "23-naver-webzine-solution.md": "네이버 웹진 솔루션",
    "24-paste-pipeline.md": "Paste Pipeline",
    "25-multi-ai-strategy.md": "멀티 AI 전략",
    "26-naver-parsing-solution.md": "Naver 파싱 해결",
    "27-claude-grok-pipeline.md": "Claude+Grok 파이프",
    "28-grok-github-bridge.md": "Grok 인터프리터",
    "29-grok-cli-installed.md": "Grok CLI 설치",
    "30-agent-file-marks.md": "에이전트 파일 마크 _Grok",
    "31-agent-roles_Grok.md": "직함 디자이너·반장·감사",
    "32-ecosystem-whitepaper.md": "생태계 백서",
    "33-webpage-coverage_Grok.md": "웹페이지 커버리지 체크 (_Grok)",
    "33-hybrid-image-video-whitepaper.md": "이미지·영상 하이브리드 워크플로우",
    "34-stt-zero-cost-justification.md": "STT 0원 풀스택 정당화",
    "35-ecosystem-whitepaper-v1.1.md": "생태계 백서 v1.1",
    "session-2026-07-26_Grok.md": "세션 2026-07-26 _Grok",
    "99-devlog.md": "개발일지",
    "ai-agents-cc-ds-grok-comparison-2026-07-25.md": "cc vs ds vs grok",
    "supergrok-community-research-2026-07-25.md": "SuperGrok 리서치",
    "naver-intro-article.md": "네이버 소개 아티클",
}

# Auto-discover every _notebook/*.md (overrides in NOTEBOOK_TITLES)
_nb_seen = set()
for md_name, title in NOTEBOOK_TITLES.items():
    src = f"_notebook/{md_name}"
    if (ROOT / src).exists():
        out = f"notebook/{md_name.replace('.md', '.html')}"
        add(src, out, title, "Notebook")
        _nb_seen.add(md_name)
for md_path in sorted((ROOT / "_notebook").glob("*.md")):
    if md_path.name in _nb_seen:
        continue
    # skip private drafts if any
    if md_path.name.startswith("."):
        continue
    title = md_path.stem.replace("_", " ").replace("-", " ")
    # try first H1 later at build; placeholder title
    add(f"_notebook/{md_path.name}", f"notebook/{md_path.stem}.html", title, "Notebook")

# Code / config viewers
CODE_PAGES = [
    ("g/install.sh", "g/install.html", "install.sh · 1줄 설치기", "Scripts"),
    ("care/care-daemon.sh", "care/care-daemon.html", "care-daemon.sh", "Scripts"),
    ("care/care-setup.sh", "care/care-setup.html", "care-setup.sh", "Scripts"),
    ("care/care.conf", "care/care-conf.html", "care.conf", "Scripts"),
    ("phone-health.sh", "phone-health.html", "phone-health.sh", "Scripts"),
    ("scripts/tg.sh", "scripts/tg.html", "tg.sh · Telegram", "Scripts"),
    ("scripts/ds.sh", "scripts/ds.html", "ds.sh · Aider wrapper", "Scripts"),
    ("scripts/yt_upload.py", "scripts/yt-upload.html", "yt_upload.py", "Scripts"),
    ("scripts/grok_api.py", "scripts/grok-api.html", "grok_api.py", "Scripts"),
    ("configs/bashrc-example.sh", "configs/bashrc-example.html", "bashrc-example.sh", "Scripts"),
    ("configs/settings.json", "configs/settings.html", "settings.json", "Scripts"),
    ("configs/ecosystem-map.json", "configs/ecosystem-map.html", "ecosystem-map.json", "Scripts"),
    ("site.webmanifest", "site-webmanifest.html", "site.webmanifest", "Scripts"),
]
for src, out, title, sec in CODE_PAGES:
    if (ROOT / src).exists():
        add(src, out, title, sec, kind="code")

# README sections for empty folders
for p, title in [
    ("01-foundation/README.md", "Foundation README"),
    ("02-network/README.md", "Network README"),
    ("03-broadcast/README.md", "Broadcast README"),
    ("04-phone-control/README.md", "Phone Control README"),
    ("05-optimization/README.md", "Optimization README"),
]:
    if (ROOT / p).exists():
        add(p, p.replace(".md", ".html").replace("01-foundation/", "foundation/").replace("02-network/", "network/").replace("03-broadcast/", "broadcast/").replace("04-phone-control/", "phone-control/").replace("05-optimization/", "optimization/"), title, "Guides")


def rewrite_md_links(text: str, current_out: str) -> str:
    """Rewrite internal .md / raw paths to generated .html paths."""

    def map_target(target: str) -> str:
        t = target.strip()
        if t.startswith(("http://", "https://", "mailto:", "#")):
            return t
        # strip anchors
        path, anc = (t.split("#", 1) + [""])[:2]
        anc = f"#{anc}" if anc else ""
        # normalize
        path = path.lstrip("./")
        # direct catalog lookup
        for item in CATALOG:
            if item["src"] == path or item["src"].endswith("/" + path) or item["out"] == path:
                return rel_between(current_out, item["out"]) + anc
        # _notebook/foo.md → notebook/foo.html
        if path.startswith("_notebook/") and path.endswith(".md"):
            return rel_between(current_out, "notebook/" + Path(path).name.replace(".md", ".html")) + anc
        if path.startswith("notebook/") and path.endswith(".md"):
            return rel_between(current_out, path.replace(".md", ".html")) + anc
        if path.endswith(".md"):
            # try basename match
            base = Path(path).name
            for item in CATALOG:
                if Path(item["src"]).name == base:
                    return rel_between(current_out, item["out"]) + anc
            # fallback sibling html
            return path[:-3] + ".html" + anc
        # code files linked
        for item in CATALOG:
            if item["src"] == path:
                return rel_between(current_out, item["out"]) + anc
        return t

    # [text](url)
    def repl(m):
        label, url = m.group(1), m.group(2)
        return f"[{label}]({map_target(url)})"

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", repl, text)
    return text


def rel_between(from_out: str, to_out: str) -> str:
    from_dir = Path(from_out).parent
    rel = os.path.relpath(to_out, from_dir if str(from_dir) != "." else ".")
    return rel.replace(os.sep, "/")


def extract_title_deck(md_text: str, fallback: str, deck: str) -> tuple[str, str]:
    title = fallback
    for line in md_text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break
    if not deck:
        for line in md_text.splitlines():
            s = line.strip()
            if s.startswith(">") and len(s) > 3:
                deck = s.lstrip("> ").strip()
                break
    return title, deck


def render_md(md_text: str) -> tuple[str, str]:
    MD.reset()
    body = MD.convert(md_text)
    toc = getattr(MD, "toc", "") or ""
    return body, toc


def page_shell(
    *,
    title: str,
    deck: str,
    section: str,
    body_html: str,
    toc_html: str,
    out_path: str,
    src: str,
    kind: str = "md",
) -> str:
    # depth for assets
    depth = len(Path(out_path).parts) - 1
    prefix = "../" * depth if depth > 0 else ""
    home = prefix + "index.html"
    assets = prefix + "assets/"

    # prev/next within same section
    section_items = [c for c in CATALOG if c["section"] == section]
    idx = next((i for i, c in enumerate(section_items) if c["out"] == out_path), -1)
    prev = section_items[idx - 1] if idx > 0 else None
    nxt = section_items[idx + 1] if 0 <= idx < len(section_items) - 1 else None

    def pager_link(item, direction):
        if not item:
            return "<div></div>"
        href = rel_between(out_path, item["out"])
        label = "Previous" if direction == "prev" else "Next"
        cls = "" if direction == "prev" else " next"
        return f'''<a class="{cls.strip()}" href="{href}">
          <span class="dir">{label}</span>
          <span class="title">{html.escape(item["title"])}</span>
        </a>'''

    # related: up to 4 other in section
    related = [c for c in section_items if c["out"] != out_path][:6]
    related_html = ""
    if related:
        cards = []
        for c in related:
            href = rel_between(out_path, c["out"])
            cards.append(
                f'<a href="{href}"><strong>{html.escape(c["title"])}</strong>{html.escape(c.get("deck") or c["section"])}</a>'
            )
        related_html = f'''<div class="wz-related">
          <h2>같은 섹션</h2>
          <div class="grid">{"".join(cards)}</div>
        </div>'''

    toc_block = ""
    if toc_html and "li" in toc_html:
        toc_block = f'<nav class="wz-toc" aria-label="목차"><div class="label">Contents</div>{toc_html}</nav>'

    crumb_section = html.escape(section)
    return f"""<!DOCTYPE html>
<html lang="ko" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="{html.escape(deck or title)} — S21 Phone Webzine">
<meta name="theme-color" content="#0a0908">
<meta name="application-name" content="S21 Phone">
<title>{html.escape(title)} — S21 Phone Webzine</title>
<link rel="icon" href="{prefix}icons/favicon-32.png" type="image/png" sizes="32x32">
<link rel="icon" href="{prefix}icons/icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{prefix}icons/apple-touch-icon.png">
<link rel="manifest" href="{prefix}site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&family=JetBrains+Mono:wght@400;500&family=Noto+Sans+KR:wght@300;400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{assets}webzine.css">
</head>
<body>
<div class="spine" aria-hidden="true"><div class="spine-fill" id="spineFill"></div></div>
<header class="wz-mast">
  <a class="brand" href="{home}">S21 <em>Phone</em></a>
  <div class="wz-mast-actions">
    <button type="button" class="wz-burger" data-nav-toggle aria-label="메뉴" aria-expanded="false">☰</button>
    <nav class="wz-nav">
      <a href="{home}">Home</a>
      <a href="{prefix}archive.html">Archive</a>
      <a href="{home}#library">Library</a>
      <a href="{home}#agents">Agents</a>
      <button type="button" data-theme-toggle>Theme</button>
      <a class="pill gold" href="{home}#install">Install</a>
    </nav>
  </div>
</header>
<main class="wz-shell">
  <div class="wz-crumb">
    <a href="{home}">Webzine</a><span class="sep">/</span>
    <span>{crumb_section}</span><span class="sep">/</span>
    <span>{html.escape(title)}</span>
  </div>
  <header class="wz-hero">
    <div class="wz-kicker">{html.escape(section)} · Vol.01</div>
    <h1>{html.escape(title)}</h1>
    {f'<p class="deck">{html.escape(deck)}</p>' if deck else ''}
    <div class="wz-meta">
      <span>Source · {html.escape(src)}</span>
      <span>Kind · {html.escape(kind)}</span>
      <span>S21 Phone Editorial</span>
    </div>
  </header>
  {toc_block}
  <div class="wz-appbar" role="toolbar" aria-label="Document tools">
    <input type="search" id="wzSearch" class="wz-search" placeholder="페이지 내 검색…" autocomplete="off">
    <button type="button" id="wzFoldAll" data-cursor>접기</button>
    <button type="button" id="wzExpandAll" data-cursor>펼치기</button>
    <button type="button" id="wzCopy" data-cursor>본문 복사</button>
  </div>
  <article class="wz-prose" id="wzProse" data-app="doc">
    {body_html}
  </article>
  <nav class="wz-pager">
    {pager_link(prev, 'prev')}
    {pager_link(nxt, 'next')}
  </nav>
  {related_html}
  <footer class="wz-foot">
    <div>S21 PHONE · Webzine Vol.01</div>
    <div class="gold">모든 계정은 누나 명의입니다.</div>
    <p style="margin-top:12px"><a href="{home}">← Back to landing</a></p>
  </footer>
</main>
<div class="wz-float">
  <button type="button" id="wzTop" aria-label="Top">↑</button>
  <button type="button" data-theme-toggle aria-label="Theme">◐</button>
</div>
<script src="{assets}webzine.js"></script>
</body>
</html>
"""


def build_md(item: dict) -> None:
    src_path = ROOT / item["src"]
    raw = src_path.read_text(encoding="utf-8", errors="replace")
    title, deck = extract_title_deck(raw, item["title"], item.get("deck") or "")
    item["title"] = title
    if deck:
        item["deck"] = deck
    rewritten = rewrite_md_links(raw, item["out"])
    body, toc = render_md(rewritten)
    # drop duplicate h1 if present as first heading matching title
    body = re.sub(r"^<h1[^>]*>.*?</h1>\s*", "", body, count=1, flags=re.I | re.S)
    html_out = page_shell(
        title=item["title"],
        deck=item.get("deck") or "",
        section=item["section"],
        body_html=body,
        toc_html=toc,
        out_path=item["out"],
        src=item["src"],
        kind="markdown",
    )
    out = ROOT / item["out"]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html_out, encoding="utf-8")


def build_code(item: dict) -> None:
    src_path = ROOT / item["src"]
    raw = src_path.read_text(encoding="utf-8", errors="replace")
    lang = Path(item["src"]).suffix.lstrip(".") or "text"
    escaped = html.escape(raw)
    body = f"""
<div class="wz-code-head">
  <span class="path">{html.escape(item["src"])}</span>
  <button type="button" data-copy="#codeBody">Copy</button>
</div>
<pre id="codeBody"><code class="language-{html.escape(lang)}">{escaped}</code></pre>
<p style="margin-top:1.5em;color:var(--ink-mute);font-size:.9rem">원본 파일: <code>{html.escape(item["src"])}</code> · Webzine code viewer (no execution)</p>
"""
    html_out = page_shell(
        title=item["title"],
        deck=item.get("deck") or f"Source viewer · {item['src']}",
        section=item["section"],
        body_html=body,
        toc_html="",
        out_path=item["out"],
        src=item["src"],
        kind="code",
    )
    out = ROOT / item["out"]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html_out, encoding="utf-8")


def build_archive_index() -> None:
    """notebook/00-INDEX.html already from md; also create archive.html hub."""
    by_sec: dict[str, list] = {}
    for c in CATALOG:
        by_sec.setdefault(c["section"], []).append(c)
    parts = ['<p>랜딩 페이지와 연결된 모든 Webzine 문서 · 스크립트 뷰어 허브.</p>']
    for sec, items in by_sec.items():
        parts.append(f"<h2>{html.escape(sec)}</h2><ul>")
        for it in items:
            href = rel_between("archive.html", it["out"])
            parts.append(f'<li><a href="{href}">{html.escape(it["title"])}</a> <code style="opacity:.6">{html.escape(it["out"])}</code></li>')
        parts.append("</ul>")
    body = "\n".join(parts)
    page = page_shell(
        title="Archive Hub",
        deck="모든 웹진 페이지 인덱스",
        section="Core",
        body_html=body,
        toc_html="",
        out_path="archive.html",
        src="scripts/build_webzine.py",
        kind="index",
    )
    (ROOT / "archive.html").write_text(page, encoding="utf-8")


def patch_landing_links() -> int:
    """Rewrite index.html internal targets to html pages where catalog maps."""
    index = ROOT / "index.html"
    text = index.read_text(encoding="utf-8")
    count = 0
    # map src path and common variants → out
    mapping = {}
    for c in CATALOG:
        mapping[c["src"]] = c["out"]
        mapping["./" + c["src"]] = c["out"]
        if c["src"].startswith("_notebook/"):
            # old notebook html already correct sometimes
            mapping["notebook/" + Path(c["src"]).name.replace(".md", ".html")] = c["out"]
            mapping["_notebook/" + Path(c["src"]).name] = c["out"]

    def repl_href(m):
        nonlocal count
        full, url = m.group(0), m.group(1)
        if url.startswith(("http://", "https://", "mailto:", "#", "icons/", "assets/", "site.webmanifest")):
            return full
        key = url.split("#")[0].split("?")[0].lstrip("./")
        # try direct
        for k, v in mapping.items():
            if k.lstrip("./") == key or k == url or k == key:
                count += 1
                anc = ""
                if "#" in url:
                    anc = "#" + url.split("#", 1)[1]
                return f'href="{v}{anc}"'
        # md → guess
        if key.endswith(".md"):
            # foundation etc already in mapping
            guess = key[:-3] + ".html"
            # known root files
            root_map = {
                "CONSTITUTION.md": "constitution.html",
                "CLAUDE.md": "claude.html",
                "README.md": "readme.html",
                "GUIDE.md": "guide.html",
                "CHRONICLE.md": "chronicle.html",
                "GIFT.md": "gift.html",
                "_textbook/index.md": "textbook.html",
            }
            if key in root_map:
                count += 1
                return f'href="{root_map[key]}"'
        return full

    new = re.sub(r'href=["\']([^"\']+)["\']', repl_href, text)
    # add archive link in mast if missing
    if "archive.html" not in new:
        new = new.replace(
            '<a class="hide-m" href="#library">Library</a>',
            '<a class="hide-m" href="#library">Library</a>\n    <a class="hide-m" href="archive.html">All pages</a>',
        )
    index.write_text(new, encoding="utf-8")
    return count


def write_sitemap() -> None:
    urls = ["https://helena751107.github.io/helena_phone/"]
    urls.append("https://helena751107.github.io/helena_phone/archive.html")
    for c in CATALOG:
        urls.append("https://helena751107.github.io/helena_phone/" + c["out"])
    body = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        body.append(f"  <url><loc>{html.escape(u)}</loc></url>")
    body.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(body) + "\n", encoding="utf-8")


def write_webpage_coverage() -> dict:
    """Compare docs ↔ HTML; Grok coverage duty source of truth."""
    notebook_mds = sorted((ROOT / "_notebook").glob("*.md"))
    notebook_html = {p.stem for p in (ROOT / "notebook").glob("*.html")}
    missing_html = []
    for m in notebook_mds:
        if m.stem not in notebook_html:
            missing_html.append(f"_notebook/{m.name}")
    orphan_html = []
    for h in sorted((ROOT / "notebook").glob("*.html")):
        if not (ROOT / "_notebook" / f"{h.stem}.md").exists():
            # allow generated apps without md
            if h.stem in {"webpage-coverage", "apps-index"}:
                continue
            orphan_html.append(f"notebook/{h.name}")
    catalog_missing = []
    for item in CATALOG:
        out = ROOT / item["out"]
        if not out.exists():
            catalog_missing.append(item["out"])
    report = {
        "generated": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "notebook_md_count": len(notebook_mds),
        "notebook_html_count": len(list((ROOT / "notebook").glob("*.html"))),
        "catalog_count": len(CATALOG),
        "missing_html": missing_html,
        "orphan_html": orphan_html,
        "catalog_missing_on_disk": catalog_missing,
        "gap_count": len(missing_html) + len(catalog_missing),
        "policy": "Every _notebook/*.md must have notebook/*.html. Build via scripts/build_webzine.py. Agent: _Grok checks every session.",
    }
    outp = ROOT / "assets" / "webpage-coverage.json"
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report



def main() -> int:
    built = 0
    for item in CATALOG:
        src = ROOT / item["src"]
        if not src.exists():
            print("SKIP missing", item["src"])
            continue
        if item["kind"] == "code":
            build_code(item)
        else:
            build_md(item)
        built += 1
        print("OK", item["out"])
    build_archive_index()
    print("OK archive.html")
    n = patch_landing_links()
    print(f"Patched landing hrefs: {n}")
    write_sitemap()
    print("OK sitemap.xml")
    # catalog json for debugging
    (ROOT / "assets" / "catalog.json").write_text(
        json.dumps(CATALOG, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    cov = write_webpage_coverage()
    print(f"Coverage gaps: {cov.get('gap_count', 0)} → assets/webpage-coverage.json")
    print(f"Built {built} pages + archive")
    return 0 if cov.get("gap_count", 0) == 0 else 0  # build always succeeds; gaps reported


if __name__ == "__main__":
    sys.exit(main())
