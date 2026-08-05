#!/usr/bin/env bash
# 🎬 produce_pd.sh — PD Pipeline v1
# Baseline: Aider produce_intro + _render_video (Ken Burns 1080p BGM)
# Upgrade:  Grok PD bible · Grok TTS · optional bridge clips · playable encode
#
# 역할:
#   Factory(공짜) = Playwright 페이지 캡처 + FFmpeg 조립
#   Grok(유료)   = PD 대본 · 성우 · bridge/ 에 미리 둔 이미지·I2V 만
#
# 사용:
#   bash scripts/produce_pd.sh [ep_id] [page_url]
#   EP=pd_intro BGM_VOLUME=0.06 bash scripts/produce_pd.sh
#
# 스펙: configs/video_pd_pipeline_v1.json

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EP="${1:-pd_intro}"
URL="${2:-https://helena751107.github.io/helena_phone/}"
OUTDIR="${OUTDIR:-$ROOT/out/$EP}"
export OUTDIR EP URL ROOT
export BGM_VOLUME="${BGM_VOLUME:-0.025}"  # Golden whisper — 들릴락 말락 은은
export TTS_ENGINE="${TTS_ENGINE:-grok}"
export GROK_TTS_VOICE="${GROK_TTS_VOICE:-ara}"
export VOICE="${VOICE:-ko-KR-InJoonNeural}"
export PYTHONIOENCODING=utf-8

if [[ -f "$ROOT/.secrets.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.secrets.env"
  set +a
fi

mkdir -p "$OUTDIR"/{stills,voice,bridge,work}
echo "=== 🎬 produce_pd · $EP ==="
echo "  URL=$URL"
echo "  BGM_VOLUME=$BGM_VOLUME (golden)  TTS=$TTS_ENGINE/$GROK_TTS_VOICE"

# ── P0 shot bible (create default if missing) ──
BIBLE="$OUTDIR/shot_bible.json"
if [[ ! -f "$BIBLE" ]]; then
  python3 - <<'PY'
import json, os
from pathlib import Path
out = Path(os.environ["OUTDIR"])
bible = {
  "id": os.environ.get("EP", "pd_intro"),
  "url": os.environ.get("URL"),
  "standard": "video_pd_pipeline_v1",
  "bgm_volume": float(os.environ.get("BGM_VOLUME", "0.06")),
  "resolution": "1080:1920",
  "beats": [
    {"id": "01_hero", "kind": "page", "emotion": "hook",
     "caption": "한 대의 폰",
     "vo": "갤럭시 한 대. 돌봄은 깨지지 않게, 소망은 세상에 닿게. 스마트폰으로 돌리는 AI 워크스테이션, S21 Phone입니다."},
    {"id": "02_agents", "kind": "page", "emotion": "trust",
     "caption": "세 동료",
     "vo": "역할이 다른 세 동료. 지휘 클로드, 외과 에이더, 미디어 그록. 분업이 강합니다."},
    {"id": "03_system", "kind": "page", "emotion": "map",
     "caption": "시스템 맵",
     "vo": "시스템 맵. 데이터가 폰에서 세상으로 흐릅니다. 실제 페이지 위 아키텍처입니다."},
    {"id": "04_centers", "kind": "page", "emotion": "rhythm",
     "caption": "워크센터",
     "vo": "일곱 워크센터. 공장부터 인터컴까지, 자동화와 수동이 리듬처럼 맞춰집니다."},
    {"id": "05_funnel", "kind": "page", "emotion": "rise",
     "caption": "콘텐츠 흐름",
     "vo": "웹진 미끼에서 유튜브 강의로, 누나의 독립까지. 월 비용은 거의 제로입니다."},
    {"id": "06_constitution", "kind": "page", "emotion": "handoff",
     "caption": "핸드오프",
     "vo": "원칙은 하나. 핸드오프가 곧 성공이다. 모든 계정은 누나 명의. S21 Phone."},
  ],
  "bridges": [
    {"id": "b_open", "after": None, "before": "01_hero", "file": "bridge/b_open.mp4",
     "note": "Grok bridge optional · skip if missing"},
    {"id": "b_close", "after": "06_constitution", "before": None, "file": "bridge/b_close.mp4",
     "note": "Grok bridge optional · skip if missing"},
  ],
}
(out / "shot_bible.json").write_text(json.dumps(bible, ensure_ascii=False, indent=2), encoding="utf-8")
print("  wrote shot_bible.json default")
PY
fi

# ── P1 Factory: Playwright page captures ──
echo "[P1] Playwright page captures..."
python3 - <<'PY'
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

outdir = Path(os.environ["OUTDIR"])
stills = outdir / "stills"
stills.mkdir(exist_ok=True)
url = os.environ["URL"]
# map beat ids to scroll anchors when possible
anchors = {
    "01_hero": None,
    "02_agents": "#agents",
    "03_system": "#system",
    "04_centers": "#centers",
    "05_funnel": "#funnel",
    "06_constitution": "#install",
}
import json
beats = json.loads((outdir / "shot_bible.json").read_text(encoding="utf-8"))["beats"]

with sync_playwright() as p:
    b = p.chromium.launch(args=["--disable-dev-shm-usage"])
    page = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=3)
    page.goto(url, wait_until="networkidle", timeout=120000)
    page.wait_for_timeout(2000)
    page.evaluate("""() => {
      document.querySelectorAll('.cursor,.cursor-dot').forEach(e => e.remove());
    }""")
    for beat in beats:
        if beat.get("kind") != "page":
            continue
        bid = beat["id"]
        sel = anchors.get(bid)
        if sel:
            try:
                page.goto(url + sel, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(1000)
                page.evaluate("document.querySelectorAll('.cursor,.cursor-dot').forEach(e=>e.remove())")
                page.locator(sel).first.scroll_into_view_if_needed(timeout=8000)
                page.wait_for_timeout(500)
            except Exception as e:
                print("  ! scroll", bid, e)
                page.evaluate("window.scrollBy(0, window.innerHeight)")
                page.wait_for_timeout(500)
        else:
            page.evaluate("window.scrollTo(0,0)")
            page.wait_for_timeout(600)
        dest = stills / f"{bid}.png"
        # also write to OUTDIR root for _render_video compat names
        page.screenshot(path=str(dest), full_page=False)
        # legacy names for _render_video.py
        page.screenshot(path=str(outdir / f"{bid}.png"), full_page=False)
        print(f"  📸 {bid} ({dest.stat().st_size})")
    b.close()
print("  page captures done")
PY

# ── P2 TTS-first (voice engine: grok → openai → edge) ──
echo "[P2] Voice engine TTS..."
python3 - <<'PY'
import json, os, sys
from pathlib import Path

sys.path.insert(0, os.environ["ROOT"])

outdir = Path(os.environ["OUTDIR"])
bible = json.loads((outdir / "shot_bible.json").read_text(encoding="utf-8"))
engine = os.environ.get("TTS_ENGINE", "grok")

try:
    from director.voice_engine import synthesize
    HAS_VOICE_ENGINE = True
except ImportError:
    HAS_VOICE_ENGINE = False
    print("  ⚠ director/voice_engine 없음 — edge-tts 직접 사용")

for beat in bible["beats"]:
    bid = beat["id"]
    text = beat["vo"]
    txt = outdir / "voice" / f"{bid}.txt"
    mp3 = outdir / f"{bid}.mp3"  # _render_video expects this
    txt.parent.mkdir(exist_ok=True)
    txt.write_text(text, encoding="utf-8")
    (outdir / f"{bid}.txt").write_text(text, encoding="utf-8")

    if HAS_VOICE_ENGINE:
        try:
            dur, provider = synthesize(text, mp3, engine=engine)
            print(f"  [{bid}] {provider} dur={dur:.2f}s")
        except Exception as e:
            print(f"  ! voice engine fail {bid}: {e}")
            # fallback edge
            import subprocess as sp2
            edge_v = os.environ.get("VOICE", "ko-KR-InJoonNeural")
            sp2.run(["edge-tts", "-f", str(txt), "--voice", edge_v, "--write-media", str(mp3)],
                    capture_output=True, check=False)
            print(f"  [{bid}] edge-FALLBACK/{edge_v}")
    else:
        import subprocess as sp2
        edge_v = os.environ.get("VOICE", "ko-KR-InJoonNeural")
        sp2.run(["edge-tts", "-f", str(txt), "--voice", edge_v, "--write-media", str(mp3)],
                capture_output=True, check=False)
        print(f"  [{bid}] edge/{edge_v}")
print("  TTS done")
PY

# ── P3 bridges: only if files exist (Grok session drops them) ──
echo "[P3] Bridge assets (optional)..."
python3 - <<'PY'
import json, os
from pathlib import Path
outdir = Path(os.environ["OUTDIR"])
bible = json.loads((outdir / "shot_bible.json").read_text(encoding="utf-8"))
for br in bible.get("bridges") or []:
    p = outdir / br["file"]
    print(f"  bridge {br['id']}: {'OK '+str(p.stat().st_size) if p.exists() else 'SKIP (missing — PD can add later)'}")
PY

# ── P4 FFmpeg render (Aider baseline engine, BGM golden vol) ──
echo "[P4] FFmpeg Ken Burns + BGM (volume=$BGM_VOLUME)..."
# Prefer Gymnopédie / shorts-derived bgm
export BGM_PATH="${BGM_PATH:-}"
if [[ -z "$BGM_PATH" ]]; then
  for c in \
    "$OUTDIR/bgm.m4a" \
    "$OUTDIR/bgm.mp3" \
    "$ROOT/helena-piano/bgm/output/satie_gymnopedie1.mp3" \
    "$ROOT/helena-piano/bgm/output/satie_gymnopedie3.mp3" \
    "$ROOT/helena-piano/bgm/output/clair_de_lune.mp3"
  do
    [[ -f "$c" ]] && BGM_PATH="$c" && break
  done
fi
export BGM_PATH
echo "  BGM_PATH=${BGM_PATH:-none}"

python3 "$ROOT/scripts/_render_video.py" "$OUTDIR"

# ── P5 Playable lock + interleave bridges if present ──
echo "[P5] Playable encode lock + bridge insert..."
python3 - <<'PY'
import json, os, subprocess, shutil
from pathlib import Path

outdir = Path(os.environ["OUTDIR"])
ep = os.environ.get("EP", "pd_intro")
raw = outdir / f"{ep}_final.mp4"
if not raw.exists():
    # _render uses EP env; produce_intro used intro
    cands = list(outdir.glob("*_final.mp4"))
    if not cands:
        raise SystemExit("no final mp4 from render")
    raw = cands[0]

bible = json.loads((outdir / "shot_bible.json").read_text(encoding="utf-8"))
bridges = []
for br in bible.get("bridges") or []:
    p = outdir / br["file"]
    if p.exists():
        bridges.append((br, p))

# Ensure playable yuv420p High 48k
play = outdir / f"{ep}_playable.mp4"
cmd = [
    "ffmpeg", "-y", "-i", str(raw),
    "-c:v", "libx264", "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p",
    "-preset", "veryfast", "-crf", "20",
    "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
    "-movflags", "+faststart",
    str(play),
]
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print(r.stderr[-400:])
    raise SystemExit("playable encode failed")

# If bridges exist: simple prepend/append (full timeline rewrite later)
if bridges:
    print(f"  bridges present: {len(bridges)} — re-mux bookends")
    # normalize bridge clips to 1080x1920 yuv420p 10s max
    parts = []
    work = outdir / "work"
    work.mkdir(exist_ok=True)
    for br, p in bridges:
        if br.get("before") == "01_hero" or br.get("after") is None and br["id"].endswith("open"):
            order = 0
        else:
            order = 2
        nb = work / f"br_{br['id']}.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-i", str(p),
            "-t", "6",
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p",
            "-c:v", "libx264", "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p",
            "-an", "-preset", "veryfast", "-crf", "20",
            str(nb),
        ], capture_output=True, check=False)
        if nb.exists():
            parts.append((order, nb, br["id"]))
    # silence audio for bridges + main
    main_a = work / "main.mp4"
    shutil.copy(play, main_a)
    # concat: opens + main + closes
    opens = [p for o, p, i in parts if o == 0]
    closes = [p for o, p, i in parts if o == 2]
    # add silent audio to bridge videos matching duration
    def with_silence(src: Path, dest: Path):
        subprocess.run([
            "ffmpeg", "-y", "-i", str(src),
            "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest",
            str(dest),
        ], capture_output=True, check=False)
    seq = []
    for i, p in enumerate(opens):
        d = work / f"open_{i}.mp4"
        with_silence(p, d)
        if d.exists():
            seq.append(d)
    seq.append(main_a)
    for i, p in enumerate(closes):
        d = work / f"close_{i}.mp4"
        with_silence(p, d)
        if d.exists():
            seq.append(d)
    if len(seq) > 1:
        lst = work / "seq.txt"
        lst.write_text("".join(f"file '{s}'\n" for s in seq), encoding="utf-8")
        merged = outdir / f"{ep}_playable.mp4"
        # re-encode concat for safety
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
            "-c:v", "libx264", "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p",
            "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
            "-movflags", "+faststart",
            str(merged),
        ], capture_output=True, check=False)

# probe
def probe(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=profile,pix_fmt,width,height",
        "-of", "default=nw=1:nk=1", str(path),
    ], text=True)
    return out.strip().splitlines()

play = outdir / f"{ep}_playable.mp4"
print("  playable:", probe(play), "size", play.stat().st_size)
if any("444" in x or "4:4:4" in x for x in probe(play)):
    raise SystemExit("GATE FAIL: still yuv444")
print("  GATE playable OK")
PY

# ── P6 TG 720 ──
echo "[P6] TG 720p..."
PLAY="$OUTDIR/${EP}_playable.mp4"
TG720="$OUTDIR/${EP}_tg.mp4"
ffmpeg -y -i "$PLAY" \
  -c:v libx264 -profile:v high -level 4.0 -pix_fmt yuv420p -preset veryfast -crf 23 \
  -vf "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,format=yuv420p" \
  -c:a aac -b:a 128k -ar 48000 -ac 2 -movflags +faststart \
  "$TG720" 2>/dev/null

if [[ -n "${TG_TOKEN:-}" && -n "${TG_CHAT:-}" && -f "$TG720" ]]; then
  curl -sS --connect-timeout 30 --max-time 240 -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendVideo" \
    -F chat_id="$TG_CHAT" \
    -F video=@"$TG720" \
    -F supports_streaming=true \
    -F caption="🎬 ${EP} · PD pipeline v1
Factory: page capture + Ken Burns (Aider baseline)
Grok: TTS ${GROK_TTS_VOICE} · PD bible · bridges if any
BGM vol=${BGM_VOLUME} · yuv420p High
— produce_pd.sh" \
    -o /tmp/tg_pd.json -w "\nhttp=%{http_code}\n" || true
  python3 -c "import json;d=json.load(open('/tmp/tg_pd.json')); print('TG', d.get('ok'), d.get('result',{}).get('message_id') if d.get('ok') else d.get('description','')[:80])" 2>/dev/null || echo "TG parse skip"
else
  echo "  (TG skip — no token or no file)"
fi

echo "=== DONE ==="
ls -lah "$OUTDIR/${EP}_playable.mp4" "$OUTDIR/${EP}_tg.mp4" 2>/dev/null || true
echo "bible: $BIBLE"
echo "spec:  $ROOT/configs/video_pd_pipeline_v1.json"
