#!/usr/bin/env python3
"""
S21 Phone — 블로그 자동 포스팅 실행기
post.py(티스토리) + session_post.py(네이버) 래퍼

사용법:
  ~/browser-env/bin/python3 scripts/publish.py tistory [계정] [제목]
  ~/browser-env/bin/python3 scripts/publish.py naver [계정] [제목]
  ~/browser-env/bin/python3 scripts/publish.py batch

환경: proot Ubuntu + Playwright headless Chromium
"""

import subprocess, sys, os, json, datetime

BASE     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS    = os.path.join(BASE, "tistory-naver")
PYTHON   = os.path.expanduser("~/browser-env/bin/python3")
TG_SCRIPT = os.path.join(BASE, "tg.sh")

ACCOUNTS = {
    "galaxys21":  {"blog": "galaxys21-pwuser",   "domain": "S21 폰 최적화"},
    "mynote":     {"blog": "mynote11605",         "domain": "기술노트"},
    "faith":      {"blog": "helana-christianity", "domain": "신앙사"},
    "piano":      {"blog": "helena-piano",        "domain": "피아노"},
    "psycare":    {"blog": "helena-psycare",      "domain": "정신분석"},
}

def notify_tg(msg):
    subprocess.run(["bash", TG_SCRIPT, msg], check=False)

def run_tistory(account, title_hint=""):
    """티스토리 자동 포스팅 (post.py)"""
    if account not in ACCOUNTS:
        print(f"❌ 없는 계정: {account}. 가능: {list(ACCOUNTS.keys())}")
        return False

    info = ACCOUNTS[account]
    now  = datetime.datetime.now()
    title = title_hint or f"[{info['domain']}] {now.strftime('%Y-%m-%d')} 작업일지"

    print(f"📝 티스토리 포스팅: {info['blog']}")
    print(f"   제목: {title}")

    # post.py 직접 호출
    cmd = [
        PYTHON, os.path.join(TOOLS, "post.py"),
        "--account", account,
        "--title", title,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=TOOLS, timeout=120)
    print(r.stdout[-500:] if r.stdout else r.stderr[:500])

    if r.returncode == 0:
        notify_tg(f"✅ 티스토리 발행 완료 — {info['blog']}\n제목: {title}")
        return True
    else:
        notify_tg(f"⚠️ 티스토리 발행 실패 — {info['blog']}")
        return False

def run_naver(account, title_hint=""):
    """네이버 블로그 자동 포스팅 (session_post.py)"""
    now  = datetime.datetime.now()
    title = title_hint or f"[관저탑] {now.strftime('%Y-%m-%d')} 기록"

    print(f"📝 네이버 포스팅: helena1975")
    print(f"   제목: {title}")

    cmd = [
        PYTHON, os.path.join(TOOLS, "session_post.py"),
        account,
        title,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=TOOLS, timeout=120)
    print(r.stdout[-500:] if r.stdout else r.stderr[:500])

    if r.returncode == 0:
        notify_tg(f"✅ 네이버 발행 완료 — helena1975\n제목: {title}")
        return True
    else:
        notify_tg(f"⚠️ 네이버 발행 실패 — helena1975")
        return False

def run_batch():
    """5개 티스토리 + 네이버 일괄 포스팅"""
    results = {}
    for account in ACCOUNTS:
        print(f"\n{'='*50}")
        ok = run_tistory(account)
        results[account] = "✅" if ok else "❌"

    # 네이버도
    ok = run_naver("eae_kr")
    results["naver"] = "✅" if ok else "❌"

    summary = "\n".join([f"  {k}: {v}" for k, v in results.items()])
    notify_tg(f"📋 일괄 발행 완료\n{summary}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "tistory":
        run_tistory(sys.argv[2] if len(sys.argv) > 2 else "galaxys21",
                    " ".join(sys.argv[3:]) if len(sys.argv) > 3 else "")
    elif cmd == "naver":
        run_naver(sys.argv[2] if len(sys.argv) > 2 else "helena1975",
                  " ".join(sys.argv[3:]) if len(sys.argv) > 3 else "")
    elif cmd == "batch":
        run_batch()
    else:
        print(f"❌ 알 수 없는 명령: {cmd}")
