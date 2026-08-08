#!/usr/bin/env python3
"""P0 URL Content Parser — Playwright DOM 파싱 → shot_bible 자동 생성

페이지를 로드하고 섹션(heading + 본문)을 추출해 beat 구성을 자동 생성합니다.
각 beat에는 스크롤 캡처를 위한 CSS selector(scroll_sel)가 포함됩니다.

V10: Generic page support — Tistory, GitHub Pages, Velog, Naver Blog 등.

Usage:
  python3 scripts/_parse_url.py <URL> <OUTDIR>
  python3 scripts/_parse_url.py "https://mynote11605.tistory.com/m/2" /root/work/out/pd_tistory_v2
"""
from __future__ import annotations

import json, os, re, sys, time
from pathlib import Path
from urllib.parse import urlparse


def url_to_ep(url: str) -> str:
    """Generate episode ID from URL."""
    parsed = urlparse(url)
    domain = parsed.hostname or "unknown"
    domain_short = domain.split(".")[0]  # e.g., "mynote11605" from mynote11605.tistory.com
    path = parsed.path.strip("/").replace("/", "-") or "index"
    # Sanitize: keep only alphanumeric, dash, underscore
    raw = f"pd_{domain_short}_{path}"[:40]
    return re.sub(r"[^a-zA-Z0-9_-]", "", raw)


def extract_sections(page) -> list[dict]:
    """Extract content sections from the page DOM.

    Strategy:
    1. Find the main content container
    2. Collect all h1-h3 headings within it
    3. For each heading, find the following paragraph text
    4. Build CSS selector path for scroll targeting
    """
    result = page.evaluate("""() => {
        // Find main content container (priority order for common blog platforms)
        const containers = [
            '.contents_style',           // Tistory
            '.tt_article_useless_p_margin', // Tistory v2
            'article',                    // Generic
            '.blog-content',              // Naver
            '.post-content',              // Various
            '.entry-content',             // WordPress
            '.markdown-body',             // GitHub Pages
            '#content',                   // Generic
            'main',                       // HTML5
            '.main-content',
            'body',
        ];

        let container = null;
        for (const sel of containers) {
            const el = document.querySelector(sel);
            if (el && el.textContent.trim().length > 200) {
                container = el;
                break;
            }
        }
        if (!container) container = document.body;

        // Find all headings within the container
        const headings = container.querySelectorAll('h1, h2, h3, h4');
        const sections = [];

        for (const h of headings) {
            const tag = h.tagName.toLowerCase();
            const text = h.textContent.trim();
            if (!text || text.length < 2) continue;

            // Collect text from sibling elements until next heading
            let contextText = '';
            let next = h.nextElementSibling;
            const maxSiblings = 8;
            let count = 0;
            while (next && count < maxSiblings) {
                if (['H1','H2','H3','H4'].includes(next.tagName)) break;
                const t = next.textContent.trim();
                if (t && t.length > 5) {
                    contextText += t + ' ';
                }
                next = next.nextElementSibling;
                count++;
            }
            contextText = contextText.trim().substring(0, 200);

            // Build CSS selector — use nth-of-type counting within container
            const containerTag = container.tagName.toLowerCase();
            const sameTagHeadings = container.querySelectorAll(tag);
            let nth = 1;
            for (let i = 0; i < sameTagHeadings.length; i++) {
                if (sameTagHeadings[i] === h) {
                    nth = i + 1;
                    break;
                }
            }

            // Build a Playwright-safe selector
            // V10.1: Use text-based selectors (more reliable than nth-of-type)
            // Also store the heading text for fallback matching
            let scrollSel;
            if (h.id) {
                scrollSel = '#' + h.id;
            } else {
                // Use partial text match — Playwright locator supports :has-text()
                const shortText = text.substring(0, 20).replace(/["'\\]/g, '');
                scrollSel = tag + ':has-text("' + shortText + '")';
            }

            sections.push({
                level: parseInt(tag[1]),
                heading: text,
                context: contextText,
                scroll_sel: scrollSel,
            });
        }

        return {
            sections: sections,
            containerTag: container.tagName.toLowerCase(),
            containerClass: container.className || '',
        };
    }""")

    return result


def main() -> int:
    from playwright.sync_api import sync_playwright

    if len(sys.argv) < 3:
        print("Usage: python3 _parse_url.py <URL> <OUTDIR>")
        print("Example: python3 _parse_url.py https://mynote11605.tistory.com/m/2 /root/work/out/pd_tistory_v2")
        return 1

    url = sys.argv[1]
    outdir = Path(sys.argv[2])
    ep = url_to_ep(url)

    print(f"🔍 P0 URL Parser — {url}")
    print(f"  EP={ep}  OUTDIR={outdir}")

    outdir.mkdir(parents=True, exist_ok=True)
    stills = outdir / "stills"
    stills.mkdir(exist_ok=True)
    (outdir / "voice").mkdir(exist_ok=True)
    (outdir / "work").mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--disable-dev-shm-usage"])
        page = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=3)
        page.goto(url, wait_until="networkidle", timeout=120000)
        page.wait_for_timeout(1500)

        # ── Extract metadata ──
        page_title = page.title() or url
        # Get page background color
        bg_color = page.evaluate("""() => {
            const bg = getComputedStyle(document.body).backgroundColor;
            return bg || '#ffffff';
        }""")
        print(f"  📄 Title: {page_title[:80]}")
        print(f"  🎨 bg: {bg_color[:30]}")

        # ── Extract sections ──
        extract_result = extract_sections(page)
        sections = extract_result.get("sections", [])
        container_info = f"{extract_result.get('containerTag','?')}.{extract_result.get('containerClass','')[:30]}"

        print(f"  📦 Container: {container_info}")
        print(f"  📑 Sections: {len(sections)}")

        if not sections:
            print("  ⚠️  No headings found — creating single-beat fallback")
            sections = [{
                "level": 1,
                "heading": page_title[:40],
                "context": page_title,
                "scroll_sel": "body",
            }]

        # ── Build beats ──
        n = len(sections)
        # Role distribution: hook / build* / climax / resolve
        role_map = {}
        role_tags = ["warm", "gold", "teal", "cool", "warm", "gold"]
        zoom_defaults = {
            0: {"type": "out", "pan": "none"},       # hook: zoom out (show overall)
            -2: {"type": "pan_right", "pan": "none"}, # climax: pan right
            -1: {"type": "out", "pan": "none"},       # resolve: zoom out
        }

        for i, sec in enumerate(sections):
            if n == 1:
                role = "hook"
            elif i == 0:
                role = "hook"
            elif i == n - 1:
                role = "resolve"
            elif i == n - 2:
                role = "climax"
            else:
                role = "build"

            # Emotion mapping
            emotion_map = {
                "hook": "hook", "build": "trust",
                "climax": "rise", "resolve": "handoff",
            }

            # Zoom: use defaults or "in" for build
            if i == 0:
                zoom = {"type": "out", "pan": "none"}
            elif i == n - 2 and n >= 3:
                zoom = {"type": "pan_right", "pan": "none"}
            elif i == n - 1:
                zoom = {"type": "out", "pan": "none"}
            else:
                zoom = {"type": "in", "pan": "none"}

            # Pause by role
            pause_map = {"hook": 0.8, "build": 0.5, "climax": 0.7, "resolve": 1.0}

            beat_id = f"{i+1:02d}_{re.sub(r'[^a-zA-Z0-9가-힣]','',sec['heading'][:15])}"
            if not beat_id.split("_", 1)[1]:
                beat_id = f"{i+1:02d}_section{i+1}"

            color_tag = role_tags[i % len(role_tags)]

            vo_draft = sec.get("context", "") or sec["heading"]
            # Trim to reasonable VO length
            if len(vo_draft) > 120:
                vo_draft = vo_draft[:117] + "..."

            sections[i]["beat"] = {
                "id": beat_id,
                "kind": "page",
                "role": role,
                "emotion": emotion_map.get(role, "trust"),
                "zoom": zoom,
                "color_tag": color_tag,
                "pause": pause_map.get(role, 0.6),
                "caption": sec["heading"][:40],
                "vo": vo_draft,
                "scroll_sel": sec["scroll_sel"],
            }

        beats = [s["beat"] for s in sections]

        # ── Build shot_bible ──
        bible = {
            "id": ep,
            "url": url,
            "title": page_title,
            "standard": "video_pd_pipeline_v2",
            "bgm_volume": 0.025,
            "resolution": "1080:1920",
            "version": "v10",
            "channel_stinger": {"enabled": True, "duration": 0.5, "text": "S21 Phone"},
            "pattern_interrupt": {"enabled": True, "duration": 0.4},
            "loop_match": {"enabled": True, "open_color": "gold", "close_color": "gold"},
            "role_pacing": {"hook": 2.5, "build": 3.5, "climax": 4.5, "resolve": 3.0},
            "page_bg_color": bg_color,
            "beats": beats,
            "bridges": [],
        }

        bible_path = outdir / "shot_bible.json"
        bible_path.write_text(
            json.dumps(bible, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        browser.close()

    # ── Summary ──
    print(f"\n{'='*50}")
    print(f"shot_bible → {bible_path}")
    print(f"Beats: {len(beats)}")
    for b in beats:
        sel_short = (b.get("scroll_sel") or "NONE")[:55]
        print(f"  {b['id']:25s} | {b['role']:7s} | {b['caption'][:25]:25s} | sel={sel_short}")
    print(f"{'='*50}")
    print(f"  Next: python3 scripts/_generate_vo.py {outdir}")
    print(f"  Then:  python3 scripts/_direct_map.py {outdir}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
