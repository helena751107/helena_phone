#!/usr/bin/env python3
"""
youtube_ctl — YouTube 자동화 솔루션 (자체완결형)
=================================================
계정정보 + 토큰 + 환경변수(.env)만 있으면 전부 자동 구성되어
아래 명령 한 줄로 유튜브를 통제한다.

  python3 youtube_ctl.py init                # env → 설정파일 생성
  python3 youtube_ctl.py status              # 계정/채널/토큰 상태
  python3 youtube_ctl.py auth                # 토큰 없으면 1회 브라우저 인증
  python3 youtube_ctl.py channels            # 채널 목록
  python3 youtube_ctl.py upload <mp4> [제목] # 동영상 업로드
  python3 youtube_ctl.py playlist list       # 플레이리스트 목록
  python3 youtube_ctl.py playlist create <제목>
  python3 youtube_ctl.py branding <설명>     # 채널 설명/키워드 갱신
  python3 youtube_ctl.py analytics [일수]    # 조회/구독자 통계
"""
import json, os, sys, re
from pathlib import Path

SOL_DIR = Path(__file__).resolve().parent
ROOT_DIR = SOL_DIR.parent                        # tools/youtube
CONF_DIR = SOL_DIR / "runtime"                   # 자동 생성된 설정 저장소
CONF_DIR.mkdir(exist_ok=True)

CLIENT_SECRET = CONF_DIR / "client_secret.json"
CHANNELS_FILE = CONF_DIR / "channels.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]
TOKEN_URI = "https://oauth2.googleapis.com/token"


# ──────────────────────────────────────────────────────────────
def _env():
    """.env 파일 + 실제 환경변수에서 값을 읽는다 (환경변수 우선)."""
    env = {}
    envfile = SOL_DIR / ".env"
    if envfile.exists():
        for line in envfile.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    env.update({k: v for k, v in os.environ.items() if k.startswith("YT_")})
    return env


def _slug(handle: str) -> str:
    return handle.replace("@", "").strip()


def _parse_channels(raw: str):
    """'@핸들|채널ID|레포' (; 구분) → list[dict]"""
    out = []
    for part in raw.split(";"):
        part = part.strip()
        if not part:
            continue
        bits = [b.strip() for b in part.split("|")]
        if len(bits) < 2:
            continue
        handle, cid = bits[0], bits[1]
        repo = bits[2] if len(bits) > 2 else "?"
        out.append({"handle": handle, "channel_id": cid, "repo": repo})
    return out


# ──────────────────────────────────────────────────────────────
def cmd_init():
    env = _env()
    email = env.get("YT_ACCOUNT_EMAIL", "")
    acc_id = env.get("YT_ACCOUNT_ID", "a")
    raw_ch = env.get("YT_CHANNELS", "")
    client_id = env.get("YT_CLIENT_ID", "")
    client_secret = env.get("YT_CLIENT_SECRET", "")
    project = env.get("YT_GCP_PROJECT", "parksy-youtube")
    refresh = env.get("YT_REFRESH_TOKEN", "")

    if not email or not raw_ch or not client_id or not client_secret:
        print("✖ .env 값 부족 — YT_ACCOUNT_EMAIL / YT_CHANNELS / YT_CLIENT_ID / YT_CLIENT_SECRET 필요")
        sys.exit(1)

    channels = _parse_channels(raw_ch)
    if not channels:
        print("✖ YT_CHANNELS 파싱 실패 — 형식: @핸들|채널ID|레포 (여러개는 ; 구분)")
        sys.exit(1)

    # 1) client_secret.json
    CLIENT_SECRET.write_text(json.dumps({
        "installed": {
            "client_id": client_id,
            "project_id": project,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": TOKEN_URI,
            "redirect_uris": ["http://localhost"],
        }
    }, indent=2, ensure_ascii=False))

    # 2) channels.json
    acc = {
        "id": acc_id,
        "email": email,
        "token_file": f"{CONF_DIR}/token_{acc_id}.json",
        "channels": channels,
    }
    CHANNELS_FILE.write_text(json.dumps({"accounts": [acc]}, indent=2, ensure_ascii=False))

    # 3) 토큰 (refresh_token 있으면 브라우저 인증 생략, 없으면 auth 1회)
    if refresh:
        for ch in channels:
            tok = {
                "token": "",
                "refresh_token": refresh,
                "token_uri": TOKEN_URI,
                "client_id": client_id,
                "client_secret": client_secret,
                "scopes": [SCOPES[0]],
            }
            tfile = CONF_DIR / f"token_{acc_id}__{_slug(ch['handle'])}.json"
            tfile.write_text(json.dumps(tok, indent=2))
            # 계정 단위 fallback 토큰도 동일하게
            if ch is channels[0]:
                (CONF_DIR / f"token_{acc_id}.json").write_text(json.dumps(tok, indent=2))
    else:
        for ch in channels:
            tfile = CONF_DIR / f"token_{acc_id}__{_slug(ch['handle'])}.json"
            if tfile.exists():
                tfile.unlink()

    print(f"✔ 설정 생성 완료 — 계정 {email} / 채널 {len(channels)}개")
    print(f"  client_secret : {CLIENT_SECRET}")
    print(f"  channels      : {CHANNELS_FILE}")
    print(f"  토큰          : {'🟢 refresh_token 있음(즉시 사용)' if refresh else '🟡 없음 → youtube_ctl.py auth 1회 필요'}")


def _load_channels():
    if not CHANNELS_FILE.exists():
        print("✖ 설정 없음 — 먼저: python3 youtube_ctl.py init")
        sys.exit(1)
    return json.loads(CHANNELS_FILE.read_text())["accounts"]


def _token_for(handle: str):
    accounts = _load_channels()
    acc = accounts[0]
    for ch in acc["channels"]:
        if ch["handle"] == handle:
            path = CONF_DIR / f"token_{acc['id']}__{_slug(handle)}.json"
            if path.exists():
                return path, ch, acc
    # fallback 계정 토큰
    path = CONF_DIR / f"token_{acc['id']}.json"
    return path, acc["channels"][0], acc


def _creds(handle: str):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    path, ch, acc = _token_for(handle)
    if not path.exists():
        print(f"✖ 토큰 없음 ({ch['handle']}) — python3 youtube_ctl.py auth")
        sys.exit(1)
    creds = Credentials.from_authorized_user_file(str(path), SCOPES)
    if not creds.valid and creds.refresh_token:
        creds.refresh(Request())
    return creds, ch, acc


def _youtube(handle: str):
    from googleapiclient.discovery import build
    creds, ch, acc = _creds(handle)
    return build("youtube", "v3", credentials=creds, cache_discovery=False), ch, acc


# ──────────────────────────────────────────────────────────────
def cmd_status():
    accounts = _load_channels()
    for acc in accounts:
        print(f"계정: {acc['email']}  (id={acc['id']})")
        for ch in acc["channels"]:
            tok = CONF_DIR / f"token_{acc['id']}__{_slug(ch['handle'])}.json"
            r = json.loads(tok.read_text()) if tok.exists() else {}
            has_refresh = bool(r.get("refresh_token"))
            state = "🟢 사용가능(refresh)" if has_refresh else "🔴 토큰없음 → auth 필요"
            print(f"  {ch['handle']:24} {ch['channel_id']:26} {state}")
    print("\n명령: init / auth / status / channels / upload / playlist / branding / analytics")


def cmd_auth():
    """토큰 발급 (브라우저 1회). headless면 URL 출력 → 폰에서 열어 코드 붙여넣기."""
    env = _env()
    client_id = env.get("YT_CLIENT_ID", "")
    client_secret = env.get("YT_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        print("✖ .env 에 YT_CLIENT_ID / YT_CLIENT_SECRET 필요")
        sys.exit(1)

    from google_auth_oauthlib.flow import InstalledAppFlow
    flow = InstalledAppFlow.from_client_secrets_file(
        str(CLIENT_SECRET), scopes=SCOPES
    )
    try:
        creds = flow.run_local_server(port=0, prompt="consent")
    except Exception:
        # headless 환경: URL 수동 복사 방식
        auth_url, _ = flow.authorization_url(prompt="consent")
        print("브라우저 없음 — 아래 URL을 폰/PC에서 열고 코드를 붙여넣으세요:\n")
        print(auth_url)
        print()
        code = input("인증코드: ").strip()
        flow.fetch_token(code=code)
        creds = flow.credentials

    accounts = _load_channels()
    acc = accounts[0]
    for ch in acc["channels"]:
        tok = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": TOKEN_URI,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes,
        }
        (CONF_DIR / f"token_{acc['id']}__{_slug(ch['handle'])}.json").write_text(json.dumps(tok, indent=2))
        if ch is acc["channels"][0]:
            (CONF_DIR / f"token_{acc['id']}.json").write_text(json.dumps(tok, indent=2))
    print("✔ 토큰 발급 완료. 이제 status / upload 등 전부 사용 가능.")


def cmd_channels():
    handle = sys.argv[3] if len(sys.argv) > 3 else None
    accounts = _load_channels()
    acc = accounts[0]
    target = handle or acc["channels"][0]["handle"]
    yt, ch, _ = _youtube(target)
    if ch["channel_id"]:
        r = yt.channels().list(part="snippet,statistics", id=ch["channel_id"]).execute()
        for it in r.get("items", []):
            s = it["snippet"]; st = it["statistics"]
            print(f"채널: {s['title']}")
            print(f"  구독자: {st.get('subscriberCount','?')} / 영상: {st.get('videoCount','?')} / 조회: {st.get('viewCount','?')}")
            print(f"  설명: {s.get('description','')[:80]}")
    else:
        r = yt.channels().list(part="snippet", mine=True).execute()
        for it in r.get("items", []):
            print(f"  {it['id']}  {it['snippet']['title']}")


def cmd_upload():
    if len(sys.argv) < 4:
        print("사용법: youtube_ctl.py upload <mp4경로> [제목]")
        sys.exit(1)
    from googleapiclient.http import MediaFileUpload
    env = _env()
    file_path = sys.argv[3]
    title = sys.argv[4] if len(sys.argv) > 4 else Path(file_path).stem
    handle = env.get("YT_UPLOAD_HANDLE", None)
    yt, ch, acc = _youtube(handle or acc_channel_first())
    privacy = env.get("YT_PRIVACY", "public")

    body = {
        "snippet": {
            "title": title,
            "description": title,
            "categoryId": "22",
            "defaultLanguage": env.get("YT_LANGUAGE", "ko"),
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(file_path, chunksize=1024 * 1024 * 8, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    print(f"→ 업로드 시작: {title} ({ch['handle']})")
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"   진행: {int(status.progress() * 100)}%")
    print(f"✔ 완료: https://youtu.be/{resp['id']}")


def acc_channel_first():
    accounts = _load_channels()
    return accounts[0]["channels"][0]["handle"]


def cmd_playlist():
    if len(sys.argv) < 4:
        print("사용법: playlist list | create <제목> | add <플리ID> <videoID>")
        sys.exit(1)
    sub = sys.argv[3]
    env = _env()
    handle = env.get("YT_UPLOAD_HANDLE", acc_channel_first())
    yt, ch, acc = _youtube(handle)
    cid = ch["channel_id"]

    if sub == "list":
        r = yt.playlists().list(part="snippet", channelId=cid, maxResults=50).execute()
        for it in r.get("items", []):
            print(f"  {it['id']}  {it['snippet']['title']}")
    elif sub == "create":
        title = sys.argv[4] if len(sys.argv) > 4 else "새 플레이리스트"
        r = yt.playlists().insert(part="snippet,status", body={
            "snippet": {"title": title, "description": title},
            "status": {"privacyStatus": "public"},
        }).execute()
        print(f"✔ 생성: {r['id']}  {r['snippet']['title']}")
    elif sub == "add":
        pid, vid = sys.argv[4], sys.argv[5]
        yt.playlistItems().insert(part="snippet", body={
            "snippet": {"playlistId": pid, "resourceId": {"kind": "youtube#video", "videoId": vid}},
        }).execute()
        print(f"✔ 추가: {vid} → {pid}")
    else:
        print("알 수 없는 하위명령")


def cmd_branding():
    if len(sys.argv) < 4:
        print("사용법: branding <새 설명 텍스트>")
        sys.exit(1)
    env = _env()
    desc = " ".join(sys.argv[3:])
    handle = env.get("YT_UPLOAD_HANDLE", acc_channel_first())
    yt, ch, acc = _youtube(handle)
    yt.channels().update(part="brandingSettings", body={
        "id": ch["channel_id"],
        "brandingSettings": {"channel": {"description": desc, "keywords": desc.replace("\n", " ")}},
    }).execute()
    print(f"✔ 브랜딩 갱신: {ch['handle']}")


def cmd_analytics():
    from googleapiclient.discovery import build
    days = int(sys.argv[3]) if len(sys.argv) > 3 else 28
    env = _env()
    handle = env.get("YT_UPLOAD_HANDLE", acc_channel_first())
    creds, ch, acc = _creds(handle)
    yta = build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)
    r = yta.reports().query(
        ids=f"channel=={ch['channel_id']}",
        startDate=f"{(__import__('datetime').date.today() - __import__('datetime').timedelta(days=days)).isoformat()}",
        endDate=__import__('datetime').date.today().isoformat(),
        metrics="views,estimatedMinutesWatched,subscribersGained",
        dimensions="day",
    ).execute()
    print(f"최근 {days}일 통계 ({ch['handle']}):")
    for row in r.get("rows", []):
        print(f"  {row[0]}  조회 {row[1]:>6}  시청분 {row[2]:>8}  구독+{row[3]}")


# ──────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    cmd = sys.argv[1]
    fns = {
        "init": cmd_init, "status": cmd_status, "auth": cmd_auth,
        "channels": cmd_channels, "upload": cmd_upload, "playlist": cmd_playlist,
        "branding": cmd_branding, "analytics": cmd_analytics,
    }
    if cmd not in fns:
        print(f"✖ 알 수 없는 명령: {cmd}\n")
        print(__doc__)
        sys.exit(1)
    fns[cmd]()


if __name__ == "__main__":
    main()
