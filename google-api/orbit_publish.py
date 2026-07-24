#!/usr/bin/env python3
"""
orbit_publish.py — OrbitPrompt → YouTube 발행 파이프라인

사용법:
  python3 orbit_publish.py list                        # 아이템 목록 출력
  python3 orbit_publish.py status                      # 각 아이템 업로드 상태
  python3 orbit_publish.py queue <item_id> <video.mp4> # pending 큐에 추가
  python3 orbit_publish.py run [item_id]               # 업로드 실행 (없으면 전체)
  python3 orbit_publish.py playlist-add <video_id> <item_id>  # 플레이리스트에 추가

흐름:
  orbit-youtube-map.json 읽기
  → 아이템 → 채널 + 플레이리스트 찾기
  → tools/youtube/uploads/pending/ 에 스펙 JSON 생성
  → node upload.cjs [account] 실행
  → playlist_items.insert 로 플레이리스트 추가
  → 완료 후 텔레그램 보고
"""

import json, sys, os, subprocess, urllib.request, urllib.parse, urllib.error
from pathlib import Path
from datetime import datetime

# ── 경로 ──
PAPYRUS   = Path(__file__).parent.parent.parent
MAP_FILE  = Path.home() / 'OrbitPrompt/tools/orbit-youtube-map.json'
SECRET    = PAPYRUS / 'tools/youtube/client_secret.json'
PENDING   = PAPYRUS / 'tools/youtube/uploads/pending'
DONE      = PAPYRUS / 'tools/youtube/uploads/done'
UPLOAD_JS = PAPYRUS / 'tools/youtube/upload.cjs'

PENDING.mkdir(parents=True, exist_ok=True)
DONE.mkdir(parents=True, exist_ok=True)

# ── 텔레그램 ──
_TG_ENV = Path.home() / 'dtslib-papyrus' / 'config' / 'tg.env'
def _load_tg_config():
    token, chat = '', ''
    if _TG_ENV.exists():
        for line in _TG_ENV.read_text().splitlines():
            line = line.strip()
            if line.startswith('TG_TOKEN_PARKSY_BRIDGE='):
                token = line.split('=', 1)[1].strip()
            elif line.startswith('TG_CHAT_ID='):
                chat = line.split('=', 1)[1].strip()
    return token or os.environ.get('TG_TOKEN_PARKSY_BRIDGE', ''), \
           chat or os.environ.get('TG_CHAT_ID', '6858098283')

TG_TOKEN, TG_CHAT = _load_tg_config()

def tg(msg):
    try:
        data = json.dumps({'chat_id': TG_CHAT, 'text': msg, 'parse_mode':'HTML'}).encode()
        req = urllib.request.Request(
            f'https://api.telegram.org/bot{TG_TOKEN}/sendMessage',
            data=data, headers={'Content-Type':'application/json'})
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"[TG 실패] {e}")

def load_map():
    with open(MAP_FILE) as f:
        return json.load(f)

def refresh_token(acc_id):
    with open(SECRET) as f:
        cs = json.load(f)
    tok_path = PAPYRUS / f'tools/youtube/accounts/token_{acc_id}.json'
    with open(tok_path) as f:
        tok = json.load(f)
    data = urllib.parse.urlencode({
        'client_id':     cs['installed']['client_id'],
        'client_secret': cs['installed']['client_secret'],
        'refresh_token': tok['refresh_token'],
        'grant_type':    'refresh_token'
    }).encode()
    req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data)
    with urllib.request.urlopen(req) as resp:
        new = json.loads(resp.read())
    # 저장
    tok['access_token'] = new['access_token']
    with open(tok_path, 'w') as f:
        json.dump(tok, f, indent=2)
    return new['access_token']

def playlist_add(access_token, playlist_id, video_id):
    """video_id를 playlist_id에 추가"""
    url = "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet"
    body = json.dumps({
        "snippet": {
            "playlistId": playlist_id,
            "resourceId": {"kind": "youtube#video", "videoId": video_id}
        }
    }).encode()
    req = urllib.request.Request(url, data=body, method='POST', headers={
        'Authorization': f'Bearer {access_token}',
        'Content-Type':  'application/json'
    })
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), None
    except urllib.error.HTTPError as e:
        return None, f"{e.code}: {e.read().decode()[:120]}"

def get_item(data, item_id):
    for it in data['items']:
        if '_section' in it:
            continue
        if it['id'] == item_id:
            return it
    return None

def real_items(data):
    return [it for it in data['items'] if '_section' not in it]

def get_channel(data, ch_key):
    return data['channels'].get(ch_key)

# ── 명령 ──

def cmd_list(data):
    print(f"\n{'ID':<25} {'Φ7':<12} {'채널':<25} {'언어':<5} {'상태'}")
    print('─'*80)
    for it in real_items(data):
        ch = get_channel(data, it['primary']['channel'])
        lang = it.get('lang', '?')
        st = it.get('status', '?')
        vid = f" ({it['video_id']})" if it.get('video_id') else ''
        print(f"{it['id']:<25} {it['phi7_axis']:<12} {ch['handle']:<25} {lang:<5} {st}{vid}")
    print()

def cmd_status(data):
    done_files = list(DONE.glob('*.json'))
    done_ids = set()
    for f in done_files:
        try:
            spec = json.load(open(f))
            if spec.get('_orbit_item'):
                done_ids.add(spec['_orbit_item'])
        except:
            pass
    pending_files = list(PENDING.glob('*.json'))
    pending_ids = set()
    for f in pending_files:
        try:
            spec = json.load(open(f))
            if spec.get('_orbit_item'):
                pending_ids.add(spec['_orbit_item'])
        except:
            pass

    print(f"\n{'ID':<25} {'언어':<5} {'상태':<12} {'플레이리스트'}")
    print('─'*80)
    for it in real_items(data):
        if it.get('status') == 'uploaded':
            st = f"✅ uploaded ({it.get('video_id','')})"
        elif it['id'] in done_ids:
            st = '✅ done'
        elif it['id'] in pending_ids:
            st = '⏳ queued'
        else:
            st = '⬜ pending'
        lang = it.get('lang', '?')
        pl_name = it['primary']['playlist_name'][:28]
        print(f"{it['id']:<25} {lang:<5} {st:<12} {pl_name}")
    print()

def cmd_queue(data, item_id, video_path):
    """pending 큐에 아이템 추가"""
    it = get_item(data, item_id)
    if not it:
        print(f"❌ 아이템 없음: {item_id}")
        print(f"   사용 가능: {', '.join(i['id'] for i in data['items'])}")
        sys.exit(1)

    video_path = Path(video_path).resolve()
    if not video_path.exists():
        print(f"❌ 비디오 파일 없음: {video_path}")
        sys.exit(1)

    ch     = get_channel(data, it['primary']['channel'])
    pl     = it['primary']
    ts     = datetime.now().strftime('%Y%m%d_%H%M%S')
    fname  = f"orbit_{item_id}_{ts}.json"

    spec = {
        "account":       ch['token_acc'],
        "title":         it['title'],
        "description":   f"{it['title']}\n\n플레이리스트: {pl['playlist_name']}\n\n#OrbitPrompt #{it['phi7_axis']}",
        "tags":          it['tags'],
        "category_id":   it.get('category_id', '27'),
        "privacy":       "public",
        "file":          str(video_path),
        "_orbit_item":   item_id,
        "_playlist_id":  pl['playlist_id'],
        "_channel":      ch['handle'],
        "_crosspost_pl": it['crosspost']['playlist_id'] if it['crosspost'] else None,
        "_crosspost_acc": get_channel(data, it['crosspost']['channel'])['token_acc'] if it['crosspost'] else None,
    }

    out = PENDING / fname
    with open(out, 'w') as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)

    print(f"✅ 큐 추가: {fname}")
    print(f"   채널:     {ch['handle']}")
    print(f"   플레이리스트: {pl['playlist_name']}")
    print(f"   파일:     {video_path.name}")
    print(f"\n실행: python3 orbit_publish.py run {item_id}")

def cmd_run(data, item_id=None):
    """pending 큐 실행 → node upload.cjs → 플레이리스트 추가"""
    pending = list(PENDING.glob(f'orbit_{item_id}_*.json' if item_id else 'orbit_*.json'))
    if not pending:
        print("⚠ 큐에 아이템 없음. 먼저: python3 orbit_publish.py queue <item_id> <video.mp4>")
        return

    # 계정별 그룹
    by_acc = {}
    for pf in pending:
        spec = json.load(open(pf))
        acc = spec['account']
        by_acc.setdefault(acc, []).append(pf)

    for acc, files in by_acc.items():
        print(f"\n▶ node upload.cjs {acc} ({len(files)}개)")
        ret = subprocess.run(
            ['node', str(UPLOAD_JS), acc],
            capture_output=False
        )
        if ret.returncode != 0:
            print(f"  ❌ upload.cjs 실패")
            continue

    # 완료된 파일에서 video_id 추출 → 플레이리스트 추가
    print("\n플레이리스트 추가 중...")
    done_files = sorted(DONE.glob('orbit_*.json'), key=lambda f: f.stat().st_mtime, reverse=True)
    for df in done_files[:20]:
        spec = json.load(open(df))
        vid  = spec.get('_video_id')
        pl   = spec.get('_playlist_id')
        acc  = spec.get('account')
        item_name = spec.get('_orbit_item','?')
        if not vid or not pl:
            continue
        if spec.get('_playlist_added'):
            continue

        print(f"  {item_name}: video={vid} → playlist={pl[:20]}...")
        try:
            at = refresh_token(acc)
            _, err = playlist_add(at, pl, vid)
            if err:
                print(f"  ❌ playlist_add 실패: {err}")
            else:
                print(f"  ✅ 추가 완료")
                spec['_playlist_added'] = True
                with open(df, 'w') as f:
                    json.dump(spec, f, indent=2, ensure_ascii=False)

            # 크로스포스트
            xpl  = spec.get('_crosspost_pl')
            xacc = spec.get('_crosspost_acc')
            if xpl and xacc:
                xat = refresh_token(xacc)
                _, xerr = playlist_add(xat, xpl, vid)
                if xerr:
                    print(f"  ⚠ 크로스포스트 실패: {xerr}")
                else:
                    print(f"  ✅ 크로스포스트 완료 → {xpl[:20]}...")
        except Exception as e:
            print(f"  ❌ {e}")

    tg(f"🎬 OrbitPrompt 업로드 완료\n완료: {len(done_files)}개")
    print("\n완료!")

def cmd_playlist_add(data, video_id, item_id):
    """수동으로 특정 video_id를 item의 플레이리스트에 추가"""
    it = get_item(data, item_id)
    if not it:
        print(f"❌ 아이템 없음: {item_id}"); sys.exit(1)

    acc = get_channel(data, it['primary']['channel'])['token_acc']
    pl  = it['primary']['playlist_id']

    print(f"토큰 갱신 ({acc})...")
    at = refresh_token(acc)

    print(f"플레이리스트 추가: {video_id} → {pl}")
    result, err = playlist_add(at, pl, video_id)
    if err:
        print(f"❌ 실패: {err}")
    else:
        print(f"✅ 완료: {result.get('id','?')}")
        # crosspost
        cp = it.get('crosspost')
        if cp:
            xacc = get_channel(data, cp['channel'])['token_acc']
            xat  = refresh_token(xacc)
            xr, xe = playlist_add(xat, cp['playlist_id'], video_id)
            if xe:
                print(f"⚠ 크로스포스트 실패: {xe}")
            else:
                print(f"✅ 크로스포스트 완료: {cp['playlist_name']}")

# ── 엔트리포인트 ──
if __name__ == '__main__':
    data = load_map()
    cmd  = sys.argv[1] if len(sys.argv) > 1 else 'list'

    if cmd == 'list':
        cmd_list(data)
    elif cmd == 'status':
        cmd_status(data)
    elif cmd == 'queue':
        if len(sys.argv) < 4:
            print("사용법: python3 orbit_publish.py queue <item_id> <video.mp4>")
            print(f"아이템: {', '.join(it['id'] for it in real_items(data) if it.get('status') != 'uploaded')}")
            sys.exit(1)
        cmd_queue(data, sys.argv[2], sys.argv[3])
    elif cmd == 'run':
        item_id = sys.argv[2] if len(sys.argv) > 2 else None
        cmd_run(data, item_id)
    elif cmd == 'playlist-add':
        if len(sys.argv) < 4:
            print("사용법: python3 orbit_publish.py playlist-add <video_id> <item_id>")
            sys.exit(1)
        cmd_playlist_add(data, sys.argv[2], sys.argv[3])
    else:
        print(f"알 수 없는 명령: {cmd}")
        print("명령: list | status | queue | run | playlist-add")
