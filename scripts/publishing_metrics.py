#!/usr/bin/env python3
"""Publishing metrics — agent mark _Claude (Publisher).

Scans all 6 repos for md→HTML translation coverage, page quality tiers,
registration rates, and broken internal links. Zero dependencies — stdlib only.

Output: assets/publishing-metrics.json + human-readable summary on stdout.
Always exits 0 — CI gates on JSON data fields, not exit code.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ── satellite repo definitions ──────────────────────────────────────────
SATELLITES = {
    "helana_log": {
        "dir": ROOT / "helana_log",
        "pages_url": "https://helena751107.github.io/helana_log/",
        "accent": "#3db8a8",
    },
    "helena-piano": {
        "dir": ROOT / "helena-piano",
        "pages_url": "https://helena751107.github.io/helena-piano/",
        "accent": "#8b7cf0",
    },
    "helena-faith": {
        "dir": ROOT / "helena-faith",
        "pages_url": "https://helena751107.github.io/helena-faith/",
        "accent": "#d4a84b",
    },
    "helena-psycare": {
        "dir": ROOT / "helena-psycare",
        "pages_url": "https://helena751107.github.io/helena-psycare/",
        "accent": "#e85d4c",
    },
    "helena-programming": {
        "dir": ROOT / "helena-programming",
        "pages_url": "https://helena751107.github.io/helena-programming/",
        "accent": "#d4a84b",
    },
}

SKIP_NAMES = {"_TEST_CONNECTION.md"}
ORPHAN_ALLOWLIST = {"webpage-coverage", "apps-index", "index", "pages", "docs"}


# ── quality scoring ─────────────────────────────────────────────────────

def score_page(md_text: str) -> tuple[int, str]:
    """Score a page 0-5 and return (score, tier)."""
    score = 0
    lines = md_text.splitlines()

    has_h1 = False
    has_deck = False
    h2_count = 0
    has_table = False
    has_code_or_checklist = False
    past_h1 = False

    for line in lines:
        # H1
        if line.startswith("# ") and not has_h1:
            has_h1 = True
            score += 1
            past_h1 = True
            continue

        # Deck: first blockquote after H1
        if past_h1 and not has_deck and line.startswith(">") and line.strip() != ">":
            has_deck = True
            score += 1
            continue

        # H2
        if line.startswith("## "):
            h2_count += 1
            continue

        # Table: pipe with at least one more pipe on the same line
        if line.count("|") >= 2 and "|---" not in line:
            has_table = True
            continue

        # Code block or checklist
        if line.startswith("```") or line.startswith("- [ ]") or line.startswith("- [x]"):
            has_code_or_checklist = True
            continue

    if h2_count >= 2:
        score += 1
    if has_table:
        score += 1
    if has_code_or_checklist:
        score += 1

    if score >= 5:
        tier = "premium"
    elif score >= 3:
        tier = "standard"
    else:
        tier = "minimal"

    return score, tier


# ── link checking ────────────────────────────────────────────────────────

def check_internal_links(md_text: str, md_dir: Path, all_md_stems: set) -> list[str]:
    """Find broken internal .md links. Returns list of broken link descriptions."""
    broken = []
    # match [text](./path.md) or [text](path.md)
    pattern = re.compile(r'\[([^\]]*)\]\(([^)]+\.md)\)')
    for m in pattern.finditer(md_text):
        target = m.group(2)
        # resolve relative
        resolved = (md_dir / target).resolve()
        stem = resolved.stem
        if stem not in all_md_stems:
            # check if the full path resolves
            if not resolved.exists():
                broken.append(f"{target} → not found")
    return broken


# ── repo scanners ────────────────────────────────────────────────────────

def scan_main_hub() -> dict:
    """Scan helena_phone _notebook/ vs notebook/."""
    nb_dir = ROOT / "_notebook"
    html_dir = ROOT / "notebook"

    mds = sorted(nb_dir.glob("*.md")) if nb_dir.exists() else []
    htmls = {p.stem: p for p in html_dir.glob("*.html")} if html_dir.exists() else {}

    # Load NOTEBOOK_TITLES for manual registration check
    manual_titles = set()
    try:
        # Import the CATALOG — fragile but works because build_webzine imports cleanly
        import importlib.util
        spec = importlib.util.spec_from_file_location("build_webzine", ROOT / "scripts" / "build_webzine.py")
        bmod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bmod)
        for item in bmod.CATALOG:
            if item.get("section") == "Notebook" and item["src"].startswith("_notebook/"):
                stem = Path(item["src"]).stem
                manual_titles.add(stem)
    except Exception:
        # Fallback: scan source for NOTEBOOK_TITLES keys
        try:
            src = (ROOT / "scripts" / "build_webzine.py").read_text(encoding="utf-8")
            for line in src.splitlines():
                if '"_notebook/' in line and ":" in line:
                    key = line.strip().split('"')[1].split("/")[-1].replace(".md", "")
                    if key:
                        manual_titles.add(key)
        except Exception:
            pass

    md_count = len(mds)
    html_count = len(htmls)

    # Quality scan
    quality = {"premium": 0, "standard": 0, "minimal": 0}
    all_md_stems = {m.stem for m in mds}
    all_broken_links = []

    for md_path in mds:
        try:
            text = md_path.read_text(encoding="utf-8", errors="replace")
            _, tier = score_page(text)
            quality[tier] += 1
            broken = check_internal_links(text, nb_dir, all_md_stems)
            for b in broken:
                all_broken_links.append(f"_notebook/{md_path.name}: {b}")
        except Exception:
            quality["minimal"] += 1

    # Gaps
    missing_html = [f"_notebook/{m.name}" for m in mds if m.stem not in htmls]
    orphan_html = [
        f"notebook/{p.name}" for stem, p in sorted(htmls.items())
        if stem not in all_md_stems and stem not in ORPHAN_ALLOWLIST
    ]

    auto_titled = md_count - len([s for s in all_md_stems if s in manual_titles])
    manual_rate = len([s for s in all_md_stems if s in manual_titles]) / max(md_count, 1)

    return {
        "source_md": md_count,
        "output_html": html_count,
        "coverage": html_count / max(md_count, 1),
        "gap_count": len(missing_html),
        "missing_html": missing_html,
        "orphan_html": orphan_html,
        "manual_title_rate": round(manual_rate, 3),
        "auto_titled": auto_titled,
        "quality": quality,
        "broken_links": all_broken_links[:20],  # cap at 20 for readability
    }


def scan_satellite(name: str, cfg: dict) -> dict | None:
    """Scan a single satellite repo for md→HTML coverage and quality."""
    root = cfg["dir"]
    if not root.exists():
        return {"source_md": 0, "output_html": 0, "coverage": 0, "gap_count": 0,
                "missing_html": [], "orphan_html": [], "quality": {"premium": 0, "standard": 0, "minimal": 0},
                "broken_links": [], "status": "not_checked_out"}

    # Collect all md files
    mds = []
    for p in root.rglob("*.md"):
        if any(x in p.parts for x in [".git", "__pycache__", "node_modules"]):
            continue
        if p.name in SKIP_NAMES:
            continue
        mds.append(p)

    # Collect all html files
    htmls_by_stem = {}
    for p in root.rglob("*.html"):
        if any(x in p.parts for x in [".git", "__pycache__", "node_modules"]):
            continue
        # Index by relative stem within repo
        rel = p.relative_to(root)
        htmls_by_stem[str(rel.with_suffix(""))] = p

    # Build md stem set using relative paths
    md_stems = set()
    for md_path in mds:
        rel = md_path.relative_to(root)
        md_stems.add(str(rel.with_suffix("")))

    # Quality + gaps
    quality = {"premium": 0, "standard": 0, "minimal": 0}
    missing_html = []
    all_broken_links = []

    for md_path in sorted(mds):
        rel = md_path.relative_to(root)
        stem_key = str(rel.with_suffix(""))
        try:
            text = md_path.read_text(encoding="utf-8", errors="replace")
            _, tier = score_page(text)
            quality[tier] += 1
        except Exception:
            quality["minimal"] += 1

        if stem_key not in htmls_by_stem:
            missing_html.append(str(rel))

    # Orphans
    orphan_html = []
    for stem_key in sorted(htmls_by_stem):
        if stem_key not in md_stems:
            parts = Path(stem_key)
            if parts.stem not in ORPHAN_ALLOWLIST and parts.name not in ORPHAN_ALLOWLIST:
                orphan_html.append(str(htmls_by_stem[stem_key].relative_to(root)))

    md_count = len(mds)
    html_count = len(htmls_by_stem)

    return {
        "source_md": md_count,
        "output_html": html_count,
        "coverage": html_count / max(md_count, 1),
        "gap_count": len(missing_html),
        "missing_html": missing_html[:15],
        "orphan_html": orphan_html[:10],
        "quality": quality,
        "broken_links": all_broken_links[:10],
        "status": "ok",
    }


# ── main ─────────────────────────────────────────────────────────────────

def main() -> int:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    print("=" * 60)
    print(f"📊 Publishing Metrics — {now}")
    print("=" * 60)

    # Main hub
    print("\n── helena_phone (main hub) ──")
    main_hub = scan_main_hub()
    _print_repo_report("helena_phone", main_hub)

    # Satellites
    repos = {"helena_phone": main_hub}
    total_md = main_hub["source_md"]
    total_html = main_hub["output_html"]
    total_gaps = main_hub["gap_count"]

    for name, cfg in SATELLITES.items():
        print(f"\n── {name} ──")
        result = scan_satellite(name, cfg)
        repos[name] = result
        if result.get("status") == "not_checked_out":
            print(f"  ⚠ Not checked out at {cfg['dir']}")
            continue
        _print_repo_report(name, result)
        total_md += result["source_md"]
        total_html += result["output_html"]
        total_gaps += result["gap_count"]

    ecosystem_coverage = total_html / max(total_md, 1)

    # Aggregate quality
    agg_quality = {"premium": 0, "standard": 0, "minimal": 0}
    for r in repos.values():
        for tier in agg_quality:
            agg_quality[tier] += r.get("quality", {}).get(tier, 0)

    report = {
        "generated": now,
        "agent": "_Claude",
        "role": "publisher",
        "repos": repos,
        "ecosystem_coverage": round(ecosystem_coverage, 3),
        "total_md": total_md,
        "total_html": total_html,
        "total_gaps": total_gaps,
        "aggregate_quality": agg_quality,
    }

    # Write JSON
    out_path = ROOT / "assets" / "publishing-metrics.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Summary
    print(f"\n{'=' * 60}")
    print(f"🌐 Ecosystem coverage: {ecosystem_coverage:.1%} ({total_html}/{total_md})")
    print(f"   Gaps: {total_gaps}")
    print(f"   Quality: {agg_quality}")
    print(f"   Report: {out_path.relative_to(ROOT)}")
    print(f"{'=' * 60}")

    return 0


def _print_repo_report(name: str, r: dict) -> None:
    cov = r.get("coverage", 0)
    emoji = "✅" if cov >= 1.0 else ("⚠" if cov >= 0.8 else "🔴")
    print(f"  {emoji} md={r['source_md']} html={r['output_html']} coverage={cov:.1%} gaps={r['gap_count']}")
    print(f"  Quality: {r.get('quality', {})}")
    if r.get("missing_html"):
        for m in r["missing_html"][:5]:
            print(f"    MISSING: {m}")
        if len(r["missing_html"]) > 5:
            print(f"    ... +{len(r['missing_html']) - 5} more")
    if r.get("broken_links"):
        for bl in r["broken_links"][:3]:
            print(f"    BROKEN LINK: {bl}")


if __name__ == "__main__":
    sys.exit(main())
