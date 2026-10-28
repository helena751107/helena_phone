#!/usr/bin/env python3
"""
strip_widget.py — 스킨에 박아넣은 PARKSY-PLAYER 위젯 마커 블록 제거 (범용판).

2026-09-13 확정: 웹툰 신규 발행 = 그냥 블로그 글 하나 추가하는 것(제목+이미지)
이지, 스킨에 고정 플레이어 위젯을 박아넣는 방식이 아니다. 그 위젯은
position:fixed 레이아웃 스킨과 충돌해 헤더/카테고리를 덮어버리는 버그의
원인이었다(kr-merit-aggro/midmath 등 실측 확인).

이 스크립트는 폰이 kr-merit-aggro 전용으로 만든 1회성 스크립트
(tistory-naver/_revert_skin.py)를 계정/슬러그를 인자로 받는 범용판으로
정리한 것 — 어느 블로그든 이 마커가 박혀있으면 동일하게 제거한다.

사용법:
  python3 strip_widget.py --profile cookies/<account> --slug <slug>
"""
import argparse
import re
import time

from playwright.sync_api import sync_playwright

MARKER_START = "<!-- PARKSY-PLAYER-START -->"
MARKER_END = "<!-- PARKSY-PLAYER-END -->"


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def strip_widget(profile_dir: str, slug: str) -> bool:
    with sync_playwright() as p:
        try:
            ctx = p.chromium.launch_persistent_context(profile_dir, channel="chrome", headless=True, args=["--no-sandbox"])
        except Exception:
            ctx = p.chromium.launch_persistent_context(profile_dir, headless=True, args=["--no-sandbox"])
        ctx.on("dialog", lambda d: d.accept())
        pg = ctx.new_page()

        pg.goto(f"https://{slug}.tistory.com/manage/design/skin/edit#/source/html", wait_until="domcontentloaded", timeout=30000)
        pg.wait_for_timeout(3000)
        if "#/source/html" not in pg.url:
            el = pg.query_selector("text=html 편집")
            if el:
                el.click(force=True)
                pg.wait_for_timeout(2500)

        has_monaco = pg.evaluate("() => typeof window.monaco !== 'undefined'")
        if not has_monaco:
            log(f"{slug}: monaco 없음/로그인 실패")
            ctx.close()
            return False

        cur = pg.evaluate("() => window.monaco.editor.getModels()[0].getValue()")
        if MARKER_START not in cur:
            log(f"{slug}: 마커 없음 — 이미 깨끗함")
            ctx.close()
            return True

        new_val = re.sub(re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END), "", cur, flags=re.S)
        new_val = re.sub(r"\n{3,}", "\n\n", new_val)
        pg.evaluate("(v) => window.monaco.editor.getModels()[0].setValue(v)", new_val)
        pg.wait_for_timeout(800)

        removed = MARKER_START not in pg.evaluate("() => window.monaco.editor.getModels()[0].getValue()")
        if not removed:
            log(f"{slug}: 마커 제거 실패")
            ctx.close()
            return False

        for sel in ["button:has-text('적용')", "button:has-text('저장')"]:
            btn = pg.locator(sel).first
            try:
                if btn.is_visible(timeout=3000):
                    btn.click(force=True)
                    pg.wait_for_timeout(2500)
                    log(f"{slug}: 위젯 제거 + 저장 완료")
                    ctx.close()
                    return True
            except Exception:
                pass
        log(f"{slug}: 저장 버튼 못 찾음")
        ctx.close()
        return False


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", required=True, help="Playwright 영속 프로필 경로 (예: cookies/dtslib2k)")
    ap.add_argument("--slug", required=True, help="티스토리 블로그 슬러그")
    args = ap.parse_args()
    ok = strip_widget(args.profile, args.slug)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
