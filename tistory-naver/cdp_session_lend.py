#!/usr/bin/env python3
"""
cdp_session_lend.py — 폰 브라우저(삼성인터넷/크롬)의 로그인된 티스토리 세션을 CDP로 빌려온다.

캡차 없이 "콜드 스타트"를 푸는 방법 (폰 단독 실행 가능, WSL 불필요):
  - 삼성인터넷(@Terrace_devtools_remote) / 크롬(@chrome_devtools_remote)은
    안드로이드가 이미 CDP 원격디버깅 소켓을 열어둔다.
  - ADB wireless debugging(127.0.0.1:5900)으로 그 소켓에 forward만 하면,
    이미 로그인된 세션(TSSESSION 등)을 그대로 뽑아 Playwright 프로파일에 주입할 수 있다.
  - renew_sessions.py 의 kakao_login(캡차) 단계를 이 방식으로 대체한다.

사용법:
  python3 cdp_session_lend.py              # 브라우저에서 빌려 커버되는 계정만 시드 + probe
  python3 cdp_session_lend.py --dry-run    # 빌리지 않고 CDP 탭/세션 상태만 보기
  python3 cdp_session_lend.py --seed-only  # probe 없이 추출+시드만 (빠른 발행 직전용)

주의 (핵심):
  - 토큰은 "빌린 직후 즉시 사용"이 원칙. 미리 캐싱해두면 재검증 실패할 수 있다.
    → make_pair.sh --tistory 에서 renew_sessions 대신 이 스크립트를 먼저 돌리고,
      바로 이어 history_batch.py --run 을 실행한다.
  - 본사그룹(dtslib1k@kakao.com)은 지금 어느 브라우저에도 로그인돼 있지 않다.
    커버 안 되는 계정은 결과로 명확히 보고되며, 그 계정만 renew_sessions.py(캡차)로 보완한다.
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))

ACCOUNTS_FILE = BASE / "accounts.json"
COOKIES_DIR = BASE / "cookies"

# renew_sessions.py 와 동일한 쿠키 도메인 필터 (검증된 최소 세트)
USABLE_DOMAINS = {".tistory.com", ".www.tistory.com", "www.tistory.com", ".daum.net"}

# 브라우저 → (로컬 forward 포트, devtools 유닉스 소켓 이름, 표시명)
BROWSERS = [
    {"port": 9222, "socket": "Terrace_devtools_remote", "label": "삼성인터넷(Terrace)"},
    {"port": 9223, "socket": "chrome_devtools_remote", "label": "크롬"},
]

ADB_SERIAL = "127.0.0.1:5900"


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def adb_forward(port: int, socket: str) -> bool:
    """devtools 유닉스 소켓 → 로컬 TCP forward."""
    r = subprocess.run(
        ["adb", "-s", ADB_SERIAL, "forward", f"tcp:{port}", f"localabstract:{socket}"],
        capture_output=True, text=True,
    )
    return r.returncode == 0


def list_tabs(port: int):
    """CDP /json/list 로 탭 목록 조회. 실패 시 None."""
    import urllib.request
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=4) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def extract_cookies(port: int) -> list:
    """connect_over_cdp 로 해당 브라우저의 모든 컨텍스트 쿠키 수집 → USABLE 필터 → 세션쿠키 영속화."""
    def norm_samesite(v):
        return {"NoRestriction": "None", "Lax": "Lax", "Strict": "Strict", "None": "None"}.get(v, "Lax")

    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        raw, seen = [], set()
        for ctx in b.contexts:
            for c in ctx.cookies():
                k = (c["domain"], c["name"], c["value"])
                if k not in seen:
                    seen.add(k)
                    raw.append(c)
        b.close()

    now = int(time.time())
    out = []
    for c in raw:
        if c["domain"] not in USABLE_DOMAINS:
            continue
        out.append({
            "name": c["name"],
            "value": c["value"],
            "domain": c["domain"],
            "path": c.get("path", "/"),
            "expires": c["expires"] if c.get("expires", -1) != -1 else now + 86400 * 7,
            "httpOnly": c.get("httpOnly", False),
            "secure": c.get("secure", False),
            "sameSite": norm_samesite(c.get("sameSite", "Lax")),
        })
    return out


def has_session(cookies: list) -> bool:
    return any(c["name"] == "TSSESSION" for c in cookies)


def probe_coverage(cookies: list, accounts: list) -> set:
    """쿠키를 임시 컨텍스트에 주입해 각 블로그 /manage 진입을 실측 → 커버되는 blog 집합 반환."""
    covered = set()
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            "/tmp/_cdp_probe_prof",
            headless=True, viewport={"width": 1280, "height": 900}, locale="ko-KR",
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
        )
        ctx.add_cookies(cookies)
        pg = ctx.new_page()
        for a in accounts:
            slug = a["blog"]
            try:
                pg.goto(f"https://{slug}.tistory.com/manage", wait_until="domcontentloaded", timeout=20000)
                pg.wait_for_timeout(800)
                if "/auth/login" not in pg.url and f"{slug}.tistory.com/manage" in pg.url:
                    covered.add(slug)
            except Exception:
                pass
        ctx.close()
    return covered


def seed_accounts(cookies: list, accounts: list) -> None:
    """커버되는 계정의 persistent profile + state.json 에 쿠키 시드 (renew_sessions.py 와 동일 패턴)."""
    ctx_kwargs = dict(
        headless=True,
        viewport={"width": 1280, "height": 900},
        locale="ko-KR",
        args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
    )
    with sync_playwright() as p:
        for a in accounts:
            acc_id = a["id"]
            ctx = p.chromium.launch_persistent_context(str(COOKIES_DIR / acc_id), **ctx_kwargs)
            if cookies:
                ctx.add_cookies(cookies)
            ctx.storage_state(path=str(COOKIES_DIR / f"{acc_id}_state.json"))
            ctx.close()
            log(f"  ✅ {acc_id:10s} 시드 완료")


def main() -> int:
    ap = argparse.ArgumentParser(description="폰 브라우저 CDP로 티스토리 세션 빌려오기")
    ap.add_argument("--dry-run", action="store_true", help="빌리지 않고 CDP 탭/세션 상태만 보기")
    ap.add_argument("--seed-only", action="store_true", help="probe 없이 추출+시드만 (빠른 발행 직전용)")
    args = ap.parse_args()

    data = json.loads(ACCOUNTS_FILE.read_text(encoding="utf-8"))
    accounts = data["accounts"]
    log(f"=== 티스토리 CDP 세션 빌리기 ({len(accounts)}개 블로그 / 카카오 2계정) ===")

    if args.dry_run:
        for br in BROWSERS:
            tabs = list_tabs(br["port"]) if adb_forward(br["port"], br["socket"]) else None
            if tabs is None:
                print(f"  ⚠️ {br['label']:16s} — devtools 소켓 없음(브라우저 미실행?)")
                continue
            tist = [t for t in tabs if t.get("type") == "page" and "tistory" in t.get("url", "")]
            print(f"  {br['label']:16s} — 탭 {len(tabs)}개 / 티스토리 탭 {len(tist)}개")
            for t in tist:
                print(f"      · {t.get('url','')[:70]}")
        return 0

    # 1) 브라우저별로 세션 추출 → 커버되는 계정만 시드
    total_covered: set = set()
    for br in BROWSERS:
        if not adb_forward(br["port"], br["socket"]):
            log(f"⚠️ {br['label']} forward 실패 — 건너뜀")
            continue
        cookies = extract_cookies(br["port"])
        if not has_session(cookies):
            log(f"ℹ {br['label']} — TSSESSION 없음(로그인 안 됨) → 건너뜀")
            continue
        log(f"{br['label']} — TSSESSION 포함 {len(cookies)}개 쿠키 추출")

        covered = probe_coverage(cookies, accounts)
        log(f"  커버 블로그: {len(covered)}개 {sorted(covered)}")

        seed_targets = [a for a in accounts if a["blog"] in covered]
        if seed_targets:
            seed_accounts(cookies, seed_targets)
        total_covered |= covered

    # 2) 결과 요약
    uncovered = [a for a in accounts if a["blog"] not in total_covered]
    print()
    if uncovered:
        log(f"❌ 커버 안 된 계정 {len(uncovered)}개 — 브라우저 로그인 필요(renew_sessions.py --headed 캡차 보완):")
        for a in uncovered:
            log(f"   · {a['id']:12s} ({a['blog']}.tistory.com, {a['email']})")
        return 1
    log(f"✅ 전 계정 세션 시드 완료 ({len(accounts)}개 블로그)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
