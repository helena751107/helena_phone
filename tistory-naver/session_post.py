#!/usr/bin/env python3
"""
session_post.py — 터미널 작업 → 네이버 블로그 자동 포스팅

사용법:
  python3 session_post.py [account] [제목힌트]
  python3 session_post.py eae_kr "오늘 MCP 작업"
  python3 session_post.py dtslib

account 기본값: eae_kr
"""

import subprocess, json, datetime, os, sys, re

NAVER_TOOLS = os.path.expanduser("~/dtslib-papyrus/tools/naver")
POSTS_DIR   = os.path.join(NAVER_TOOLS, "posts")
WIN_SHOT    = r"C:\Temp\session_screenshot.png"
WSL_SHOT    = "/tmp/session_screenshot.png"

DOMAIN_MAP = {
    "eae_kr":   "교육방송국",
    "dtslib":   "비즈니스방송국",
    "parksy_kr": "박씨로그",
}

BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
CHAT_ID   = os.environ.get("TG_CHAT_ID", "")


def capture_terminal(session=None):
    cmd = ["tmux", "capture-pane", "-p", "-S", "-100"]
    if session:
        cmd += ["-t", session]
    r = subprocess.run(cmd, capture_output=True, text=True)
    lines = [l for l in r.stdout.splitlines() if l.strip()]
    return "\n".join(lines[-40:])  # 최근 40줄


def capture_screenshot():
    """PowerShell로 Windows 전체화면 캡처 → WSL /tmp/로 복사"""
    ps = (
        "Add-Type -AssemblyName System.Windows.Forms,System.Drawing; "
        "$b=[System.Drawing.Bitmap]::new([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width,"
        "[System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height); "
        "$g=[System.Drawing.Graphics]::FromImage($b); "
        "$g.CopyFromScreen([System.Drawing.Point]::Empty,[System.Drawing.Point]::Empty,$b.Size); "
        f"$b.Save('{WIN_SHOT}'); $g.Dispose(); $b.Dispose(); Write-Output 'OK'"
    )
    r = subprocess.run(["powershell.exe", "-Command", ps], capture_output=True, text=True, timeout=15)
    if "OK" in r.stdout:
        subprocess.run(["cp", f"/mnt/c/Temp/session_screenshot.png", WSL_SHOT], check=False)
        if os.path.exists(WSL_SHOT):
            print(f"  스크린샷 저장: {WSL_SHOT}")
            return WIN_SHOT  # post.cjs는 Windows 경로 사용
    print(f"  스크린샷 실패: {r.stderr[:100]}")
    return None


def get_recent_tg_images(count=3):
    """텔레그램 최근 이미지 파일 다운로드 → Windows 경로 반환"""
    import urllib.request, urllib.parse
    images = []
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?limit=20&allowed_updates=message"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())

        msgs = data.get("result", [])
        msgs.reverse()
        for msg in msgs:
            m = msg.get("message", {})
            photos = m.get("photo", [])
            if photos:
                file_id = max(photos, key=lambda p: p.get("file_size", 0))["file_id"]
                # file_path 조회
                fp_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
                with urllib.request.urlopen(fp_url, timeout=5) as fr:
                    fp_data = json.loads(fr.read())
                fp = fp_data["result"]["file_path"]
                dl_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{fp}"
                fname = os.path.basename(fp)
                wsl_path = f"/tmp/{fname}"
                win_path = f"C:\\Temp\\{fname}"
                urllib.request.urlretrieve(dl_url, wsl_path)
                # WSL → Windows Temp 복사
                subprocess.run(["cp", wsl_path, f"/mnt/c/Temp/{fname}"], check=False)
                images.append(win_path)
                if len(images) >= count:
                    break
    except Exception as e:
        print(f"  텔레그램 이미지 수집 실패: {e}")
    return images


def build_content(terminal_text, summary_hint=""):
    """터미널 내용 → HTML 본문"""
    # 제목/명령어/결과 중 유의미한 줄만 추출
    lines = terminal_text.splitlines()
    meaningful = []
    for l in lines:
        l = l.strip()
        if not l or l.startswith("│") or l.startswith("└") or l.startswith("┌"):
            continue
        meaningful.append(l)

    summary = summary_hint or " | ".join(meaningful[:3]) if meaningful else "AI 에이전트 작업 기록"
    body = "\n".join(meaningful[:20])

    html = f"<p><b>📋 작업 요약</b></p>"
    html += f"<p>{summary}</p>"
    html += f"<p><b>🖥 터미널 로그</b></p>"
    html += f"<pre>{body[:800]}</pre>" if body else ""
    return html


def create_post_json(account, title, content, images):
    os.makedirs(POSTS_DIR, exist_ok=True)
    now = datetime.datetime.now()
    fname = f"post_{now.strftime('%Y%m%d_%H%M%S')}.json"
    data = {
        "account": account,
        "title": title,
        "content": content,
        "images": images,
        "tags": ["AI작업", "회의록", "Claude", "에이전트"],
        "visibility": "public",
    }
    fpath = os.path.join(POSTS_DIR, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return fpath, fname


def publish(account, fname):
    r = subprocess.run(
        ["node", os.path.join(NAVER_TOOLS, "post.cjs"), account, fname],
        capture_output=True, text=True, cwd=NAVER_TOOLS, timeout=120
    )
    return r.stdout + r.stderr


def notify_tg(msg):
    import urllib.request, urllib.parse
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": msg}).encode()
    urllib.request.urlopen(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data=data, timeout=5
    )


if __name__ == "__main__":
    account     = sys.argv[1] if len(sys.argv) > 1 else "eae_kr"
    title_hint  = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
    include_tg  = "--tg" in sys.argv  # 텔레그램 이미지 포함 여부

    now    = datetime.datetime.now()
    domain = DOMAIN_MAP.get(account, account)

    print(f"=== 세션 포스팅 시작 [{account}] ===")

    # 1. 터미널 캡처
    print("[1] 터미널 캡처...")
    term = capture_terminal()

    # 2. 스크린샷
    print("[2] 스크린샷...")
    shot = capture_screenshot()
    images = [shot] if shot else []

    # 3. 텔레그램 이미지 (선택)
    if include_tg:
        print("[3] 텔레그램 최근 이미지...")
        tg_imgs = get_recent_tg_images(3)
        images += tg_imgs
        print(f"  텔레그램 이미지 {len(tg_imgs)}장")

    # 4. 제목
    title = title_hint or f"[{domain}] {now.strftime('%Y-%m-%d')} AI 에이전트 작업 회의록"
    print(f"[4] 제목: {title}")

    # 5. 본문
    content = build_content(term, title_hint)

    # 6. JSON 생성
    print("[5] 포스트 JSON 생성...")
    fpath, fname = create_post_json(account, title, content, images)
    print(f"  → {fpath}")

    # 7. 발행
    print("[6] 네이버 발행...")
    output = publish(account, fname)
    print(output[-500:])

    # 8. 텔레그램 보고
    success = "발행 완료" in output or "✅" in output
    status  = "✅ 발행 완료" if success else "⚠ 발행 결과 확인 필요"
    notify_tg(f"{status}\n계정: {account}\n제목: {title}\n이미지: {len(images)}장")
    print(f"\n{status}")
