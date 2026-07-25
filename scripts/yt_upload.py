#!/usr/bin/env python3
"""
S21 Phone — YouTube 업로드 스크립트 v1
OAuth Device Code Flow → Data API v3 → 영상 업로드

사용법:
  ~/browser-env/bin/python3 scripts/yt_upload.py --title "제목" --file video.mp4
  ~/browser-env/bin/python3 scripts/yt_upload.py --channel @HelenaPark-e7c --list

환경: proot Ubuntu
의존성: google-auth-oauthlib, google-api-python-client
전제: OAuth 토큰이 .secrets.env 또는 yt_tokens.json에 존재할 것
"""

import os, sys, json, subprocess, argparse, datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SECRETS = BASE / ".secrets.env"
TOKEN_FILE = BASE / "configs" / "yt_tokens.json"

# ── 설정 ────────────────────────────────────────────────────────────────────

CLIENT_ID = os.environ.get("YT_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET", "")
PROJECT_ID = "911931724403"  # S21 YouTube

CHANNELS = {
    "main":     {"id": "UCRUuiKCCwIbyvqlxTNpDfKw", "handle": "@HelenaPark-e7c",   "topic": "루트 채널"},
    "phone":    {"id": "", "handle": "@S21Phone",           "topic": "S21 폰 최적화"},
    "tech":     {"id": "", "handle": "@HelenaTechLog",      "topic": "기술 튜토리얼"},
    "faith":    {"id": "", "handle": "@HelanaFaith",        "topic": "신앙 콘텐츠"},
    "piano":    {"id": "", "handle": "@HelenaPiano",        "topic": "피아노 연주"},
    "psycare":  {"id": "", "handle": "@HelenaPsycare",      "topic": "정신분석"},
}

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

# ── 인증 ────────────────────────────────────────────────────────────────────

def get_authenticated_service():
    """Device Code Flow로 인증 → YouTube API 클라이언트 반환"""
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        import pickle
    except ImportError:
        print("❌ 필요 패키지 설치:")
        print("   ~/browser-env/bin/pip install google-auth-oauthlib google-api-python-client")
        sys.exit(1)

    credentials = None

    # 토큰 로드
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, 'r') as f:
            data = json.load(f)
            from google.oauth2.credentials import Credentials
            credentials = Credentials(
                token=data.get('access_token'),
                refresh_token=data.get('refresh_token'),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                scopes=SCOPES,
            )

    # 만료 시 리프레시
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        _save_tokens(credentials)
        print("🔄 토큰 리프레시 완료")

    if not credentials or not credentials.valid:
        print("❌ 유효한 토큰 없음. OAuth 재인증 필요:")
        print("   bash scripts/yt_oauth_setup.sh")
        sys.exit(1)

    return build('youtube', 'v3', credentials=credentials)

def _save_tokens(credentials):
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        'access_token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes,
    }
    with open(TOKEN_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    os.chmod(TOKEN_FILE, 0o600)

# ── 업로드 ───────────────────────────────────────────────────────────────────

def upload_video(youtube, file_path, title, description, tags, category_id, privacy_status):
    """YouTube Data API v3 — videos.insert (1,600유닛)"""

    from googleapiclient.http import MediaFileUpload

    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags or [],
            'categoryId': category_id or '22',  # 22=People & Blogs
        },
        'status': {
            'privacyStatus': privacy_status or 'private',  # private/unlisted/public
            'selfDeclaredMadeForKids': False,
        },
    }

    media = MediaFileUpload(file_path, mimetype='video/*', resumable=True)

    print(f"📤 업로드 시작: {title}")
    print(f"   파일: {file_path}")
    print(f"   상태: {privacy_status or 'private'}")

    request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)
    response = None

    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"   진행률: {int(status.progress() * 100)}%")

    video_id = response['id']
    url = f"https://youtu.be/{video_id}"
    print(f"✅ 업로드 완료: {url}")
    return video_id, url

# ── 채널 정보 ────────────────────────────────────────────────────────────────

def list_channel_videos(youtube, channel_id, max_results=10):
    """채널 동영상 목록 (playlistItems.list = 1유닛) ⚡️"""
    # 채널의 uploads 플레이리스트 ID 조회
    resp = youtube.channels().list(part='contentDetails', id=channel_id).execute()
    uploads_id = resp['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    # playlistItems.list 사용 (search.list 대비 100배 저렴)
    results = youtube.playlistItems().list(
        part='snippet',
        playlistId=uploads_id,
        maxResults=min(max_results, 50),
    ).execute()

    print(f"\n📺 채널 동영상 ({len(results.get('items', []))}개):")
    for item in results.get('items', []):
        title = item['snippet']['title']
        video_id = item['snippet']['resourceId']['videoId']
        published = item['snippet']['publishedAt'][:10]
        print(f"   [{published}] {title}")
        print(f"   https://youtu.be/{video_id}")

    return results

def get_channel_stats(youtube, channel_id):
    """채널 통계 (Analytics API 없이 기본 통계)"""
    resp = youtube.channels().list(
        part='statistics,snippet',
        id=channel_id,
    ).execute()

    if not resp.get('items'):
        print("❌ 채널 없음")
        return None

    item = resp['items'][0]
    stats = item['statistics']
    print(f"\n📊 채널 통계:")
    print(f"   이름: {item['snippet']['title']}")
    print(f"   구독자: {stats.get('subscriberCount', '?')}")
    print(f"   동영상: {stats.get('videoCount', '?')}")
    print(f"   조회수: {stats.get('viewCount', '?')}")
    return resp

# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='S21 YouTube 업로더 v1')
    parser.add_argument('--title', help='영상 제목')
    parser.add_argument('--description', help='영상 설명', default='')
    parser.add_argument('--file', help='영상 파일 경로')
    parser.add_argument('--tags', nargs='*', help='태그 (공백 구분)')
    parser.add_argument('--category', default='22', help='카테고리 ID (기본: 22=People)')
    parser.add_argument('--privacy', default='private', choices=['private', 'unlisted', 'public'])
    parser.add_argument('--channel', default='main', help=f'채널 키: {", ".join(CHANNELS.keys())}')
    parser.add_argument('--list', action='store_true', help='채널 동영상 목록')
    parser.add_argument('--stats', action='store_true', help='채널 통계')
    args = parser.parse_args()

    # OAuth 토큰 로드
    _load_secrets()

    youtube = get_authenticated_service()
    channel = CHANNELS.get(args.channel, CHANNELS['main'])

    if not channel['id']:
        print(f"❌ 채널 '{args.channel}'의 ID가 설정되지 않았습니다.")
        print("   configs/yt_tokens.json 또는 yt_upload.py의 CHANNELS 딕셔너리 확인")
        sys.exit(1)

    if args.list:
        list_channel_videos(youtube, channel['id'])
        return

    if args.stats:
        get_channel_stats(youtube, channel['id'])
        return

    if not args.title or not args.file:
        parser.error("--title과 --file은 필수입니다")
        return

    if not os.path.exists(args.file):
        print(f"❌ 파일 없음: {args.file}")
        sys.exit(1)

    desc = args.description or f"{channel['topic']}\n\n🤖 @S21Phone_Bot 자동 업로드"

    video_id, url = upload_video(
        youtube, args.file, args.title, desc,
        args.tags, args.category, args.privacy,
    )

    # tg.sh로 보고
    tg = BASE / "tg.sh"
    if tg.exists():
        msg = f"📺 YouTube 업로드 완료\n제목: {args.title}\n{url}"
        subprocess.run(["bash", str(tg), msg], check=False)

def _load_secrets():
    """환경변수에서 OAuth 정보 로드"""
    global CLIENT_ID, CLIENT_SECRET

    if SECRETS.exists():
        with open(SECRETS) as f:
            for line in f:
                line = line.strip()
                if line.startswith('YT_CLIENT_ID='):
                    CLIENT_ID = line.split('=', 1)[1].strip('"\'')
                elif line.startswith('YT_CLIENT_SECRET='):
                    CLIENT_SECRET = line.split('=', 1)[1].strip('"\'')

    CLIENT_ID = os.environ.get('YT_CLIENT_ID', CLIENT_ID)
    CLIENT_SECRET = os.environ.get('YT_CLIENT_SECRET', CLIENT_SECRET)

if __name__ == '__main__':
    main()
