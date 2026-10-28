#!/usr/bin/env python3
"""
self_cdp_session_lend.py — 이 기기(폰 또는 태블릿) 자기 자신의 삼성인터넷/크롬
세션을 캡차 없이 빌려온다. WSL 없이 기기 혼자서 돌아간다.
================================================================================
2026-09-13, phone(S25 Ultra)+tablet(Tab S9) 양쪽에 배포.

전제조건 (기기별로 다르니 먼저 확인할 것):
  - 폰: proot의 ~/.android/adbkey(.pub)를 Termux의 승인된 키로 교체해야
    자기참조(127.0.0.1:5900)가 unauthorized 안 뜬다.
      cp /data/data/com.termux/files/home/.android/adbkey* ~/.android/
  - 태블릿: Shizuku가 떠 있으면 별도 키 교체 없이 자기참조가 바로 된다
    (2026-09-13 실측 확인, Shizuku "1개 앱 인증됨" 상태).
  - 대상 브라우저(삼성인터넷 등)에 로그인하려는 사이트의 탭이 열려 있어야 한다.
    로그인 안 돼 있으면(TSSESSION 등 세션쿠키 없음) 뽑을 게 없다 — 그럴 땐
    사람이 그 브라우저로 한 번 로그인해줘야 한다(이후엔 계속 이 스크립트로 재사용).

사용법:
  adb connect 127.0.0.1:5900   # 먼저 자기참조 연결 확인 (device 떠야 함)
  python3 self_cdp_session_lend.py --domain-filter tistory \
      --profile /root/work/tistory-naver/cookies/dtslib2k --check-url https://kr-merit-aggro.tistory.com/manage
"""
import argparse
import json
import subprocess
import sys

import websocket
from playwright.sync_api import sync_playwright

CDP_SOCKET_CANDIDATES = ["Terrace_devtools_remote", "chrome_devtools_remote"]


def adb_self_connect(adb_target: str = "127.0.0.1:5900"):
    r = subprocess.run(["adb", "connect", adb_target], capture_output=True, text=True)
    print(r.stdout.strip())
    if "unauthorized" in r.stdout.lower():
        print("자기참조 unauthorized — proot adbkey를 Termux 승인된 키로 교체 필요 (상단 docstring 참고)")
        sys.exit(1)


def forward_first_working_socket(local_port: int) -> str:
    last_err = None
    for sock in CDP_SOCKET_CANDIDATES:
        try:
            subprocess.run(
                ["adb", "forward", f"tcp:{local_port}", f"localabstract:{sock}"],
                check=True, capture_output=True, text=True,
            )
            return sock
        except subprocess.CalledProcessError as e:
            last_err = e
    raise RuntimeError(f"열린 devtools 소켓을 못 찾음: {last_err}")


def find_page(local_port: int, domain_filter: str) -> dict | None:
    import urllib.request
    with urllib.request.urlopen(f"http://localhost:{local_port}/json", timeout=5) as r:
        pages = json.loads(r.read())
    for p in pages:
        if p.get("type") == "page" and domain_filter in p.get("url", ""):
            return p
    return None


def extract_session_values(page: dict, domain_filter: str) -> list[dict]:
    ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=10, suppress_origin=True)
    try:
        ws.send(json.dumps({"id": 1, "method": "Network.getAllCookies"}))
        data = json.loads(ws.recv())
    finally:
        ws.close()
    entries = data.get("result", {}).get("cookies", [])
    return [c for c in entries if domain_filter in c.get("domain", "")]


def to_playwright_cookies(entries: list[dict]) -> list[dict]:
    out = []
    for c in entries:
        pc = {
            "name": c["name"], "value": c["value"], "domain": c["domain"],
            "path": c.get("path", "/"), "httpOnly": c.get("httpOnly", False),
            "secure": c.get("secure", False),
        }
        if not c.get("session", False) and c.get("expires", 0) > 0:
            pc["expires"] = c["expires"]
        if c.get("sameSite") in ("Strict", "Lax", "None"):
            pc["sameSite"] = c["sameSite"]
        out.append(pc)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--adb-target", default="127.0.0.1:5900")
    ap.add_argument("--domain-filter", required=True, help="예: tistory")
    ap.add_argument("--profile", help="주입할 Playwright 영속 프로필 경로")
    ap.add_argument("--check-url")
    ap.add_argument("--export-only", action="store_true")
    ap.add_argument("-o", "--output", default="/tmp/session_values.json")
    ap.add_argument("--local-port", type=int, default=9333)
    args = ap.parse_args()

    adb_self_connect(args.adb_target)
    forward_first_working_socket(args.local_port)
    page = find_page(args.local_port, args.domain_filter)
    if not page:
        print(f"'{args.domain_filter}' 포함된 탭이 브라우저에 안 열려있음 — 먼저 그 사이트 탭 열어둘 것")
        sys.exit(1)
    entries = extract_session_values(page, args.domain_filter)
    if not entries:
        print("세션 값을 못 뽑음 (로그인 안 된 상태일 수 있음)")
        sys.exit(1)
    print(f"{len(entries)}개 값 확보")

    if args.export_only:
        with open(args.output, "w") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        print(f"저장: {args.output}")
        sys.exit(0)

    if not args.profile:
        print("--profile 필요 (또는 --export-only)")
        sys.exit(1)

    pw_cookies = to_playwright_cookies(entries)
    with sync_playwright() as p:
        try:
            ctx = p.chromium.launch_persistent_context(args.profile, headless=True, args=["--no-sandbox"])
        except Exception as e:
            print(f"프로필 열기 실패: {e}")
            sys.exit(1)
        ctx.add_cookies(pw_cookies)
        if args.check_url:
            pg = ctx.new_page()
            pg.goto(args.check_url, wait_until="domcontentloaded", timeout=20000)
            pg.wait_for_timeout(1500)
            ok = "auth/login" not in pg.url
            print(f"검증 URL: {pg.url} -> {'성공' if ok else '실패'}")
        ctx.close()


if __name__ == "__main__":
    main()
