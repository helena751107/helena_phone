#!/usr/bin/env python3
"""Webpage coverage checker — agent mark _Grok.

Compares _notebook/*.md ↔ notebook/*.html and reports gaps.
Writes assets/webpage-coverage.json. Exit 1 if gaps (for CI/hooks).
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_manual_titles() -> set[str]:
    """Parse NOTEBOOK_TITLES keys from build_webzine.py for manual registration check."""
    manual = set()
    try:
        src = (ROOT / "scripts" / "build_webzine.py").read_text(encoding="utf-8")
        in_dict = False
        for line in src.splitlines():
            if "NOTEBOOK_TITLES" in line and "{" in line:
                in_dict = True
                continue
            if in_dict:
                if line.strip().startswith("}"):
                    break
                # Match "key.md": "title" pattern
                m = re.match(r'\s*"([^"]+\.md)"\s*:', line)
                if m:
                    manual.add(m.group(1).replace(".md", ""))
    except Exception:
        pass
    return manual


def main() -> int:
    nb = ROOT / "_notebook"
    html_dir = ROOT / "notebook"
    mds = sorted(nb.glob("*.md")) if nb.exists() else []
    htmls = {p.stem: p for p in html_dir.glob("*.html")} if html_dir.exists() else {}

    manual_titles = _load_manual_titles()
    auto_titled = [m for m in mds if m.stem not in manual_titles]

    missing_html = [f"_notebook/{m.name}" for m in mds if m.stem not in htmls]
    orphan_html = []
    for stem, path in sorted(htmls.items()):
        if not (nb / f"{stem}.md").exists():
            if stem in {"webpage-coverage", "apps-index"}:
                continue
            orphan_html.append(f"notebook/{path.name}")

    # catalog cross-check if present
    catalog_path = ROOT / "assets" / "catalog.json"
    catalog_missing = []
    catalog_count = 0
    if catalog_path.exists():
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        catalog_count = len(catalog)
        for item in catalog:
            if not (ROOT / item["out"]).exists():
                catalog_missing.append(item["out"])

    report = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "agent": "_Grok",
        "notebook_md_count": len(mds),
        "notebook_html_count": len(htmls),
        "catalog_count": catalog_count,
        "manual_titles": len(manual_titles),
        "auto_titled": len(auto_titled),
        "missing_html": missing_html,
        "orphan_html": orphan_html,
        "catalog_missing_on_disk": catalog_missing,
        "gap_count": len(missing_html) + len(catalog_missing),
        "ok": len(missing_html) + len(catalog_missing) == 0,
        "policy": (
            "Every _notebook/*.md must have notebook/<same-stem>.html. "
            "Run: python3 scripts/build_webzine.py"
        ),
        "live_app": "https://helena751107.github.io/helena_phone/notebook/webpage-coverage.html",
    }

    out = ROOT / "assets" / "webpage-coverage.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("=== Webpage coverage (_Grok) ===")
    print(f"md={report['notebook_md_count']} html={report['notebook_html_count']} catalog={catalog_count}")
    print(f"manual_titles={len(manual_titles)} auto_titled={len(auto_titled)}")
    print(f"missing_html={len(missing_html)} catalog_missing={len(catalog_missing)} orphans={len(orphan_html)}")
    for m in missing_html:
        stem = Path(m).stem
        prefix = "⚠ AUTO_TITLE" if stem not in manual_titles else "  "
        print(f"  MISSING {prefix} {m}")
    for m in catalog_missing:
        print("  CATALOG_MISSING", m)
    for o in orphan_html[:12]:
        print("  ORPHAN", o)
    # auto-title warning summary
    auto_missing = [m for m in missing_html if Path(m).stem not in manual_titles]
    if auto_missing:
        print(f"⚠ {len(auto_missing)} missing page(s) are auto-titled (no NOTEBOOK_TITLES entry)")
        print("  → Add to NOTEBOOK_TITLES in build_webzine.py for proper Korean title")
    if auto_titled:
        print(f"ℹ {len(auto_titled)} existing md(s) are auto-titled — consider manual registration")
    print(f"gap_count={report['gap_count']} → {out.relative_to(ROOT)}")
    print("ok" if report["ok"] else "GAPS")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
