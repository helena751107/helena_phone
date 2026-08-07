#!/usr/bin/env bash
# 🎬 produce_pd.sh — PD Pipeline STANDARD v3 (canonical · Grok-free · V7 renderer)
# 표준: configs/video_pd_pipeline_v2.json · CURRENT → configs/video_pd_pipeline_CURRENT.json
# 역할:
#   Factory(공짜) = Playwright 페이지 캡처 + FFmpeg Ken Burns + xfade multi-transition
#   Boss(수동)   = Gemini/공짜LLM으로 bridge 영상 제작 → Android 갤러리에 저장
#   성우          = Kokoro FP32 + jf_alpha (sid=37, 일본인 여성) · 완전 공짜
# V7: breathing pauses · zoom variety (in/out/pan) · per-slide grade · BGM swell · staggered end card
# V6: audio ducking · xfade(fade/wipe/slide/dissolve) · end card · chrono-pair bridge
# 고정 상수: BGM_VOLUME=0.025 · TTS=local · CJK 폰트 · QA gate 필수
#
# Bridge 워크플로 (Grok 제로):
#   1. Gemini로 open/close 영상 만들기
#   2. Android Download 폴더에 저장 (b_open.mp4 / b_close.mp4)
#   3. produce_pd.sh 실행 → _bridge_pickup.sh가 자동 감지
#
# 사용 (매번 동일):
#   bash scripts/produce_pd.sh [ep_id] [page_url]
#   bash scripts/produce_pd.sh pd_intro
#

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EP="${1:-pd_intro}"
URL="${2:-https://helena751107.github.io/helena_phone/}"
OUTDIR="${OUTDIR:-$ROOT/out/$EP}"
export OUTDIR EP URL ROOT
export BGM_VOLUME="${BGM_VOLUME:-0.025}"  # Golden whisper — 들릴락 말락 은은
export TTS_ENGINE="${TTS_ENGINE:-local}"
export GROK_TTS_VOICE="${GROK_TTS_VOICE:-ara}"
export VOICE="${VOICE:-ko-KR-InJoonNeural}"
export PYTHONIOENCODING=utf-8

# ── STANDARD v2 pin (변경 금지 — configs/video_pd_pipeline_CURRENT.json) ──
export PD_STANDARD="video_pd_pipeline_v2"
export PD_STANDARD_PATH="$ROOT/configs/video_pd_pipeline_v2.json"
export BGM_VOLUME="${BGM_VOLUME:-0.025}"
export TTS_ENGINE="${TTS_ENGINE:-local}"
export GROK_TTS_VOICE="${GROK_TTS_VOICE:-ara}"
export VIDEO_BRAND="${VIDEO_BRAND:-S21 Phone}"
if [[ ! -f "$PD_STANDARD_PATH" ]]; then
  echo "❌ missing standard $PD_STANDARD_PATH"; exit 1
fi
echo "  STANDARD=$PD_STANDARD"

if [[ -f "$ROOT/.secrets.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.secrets.env"
  set +a
fi

mkdir -p "$OUTDIR"/{stills,voice,bridge,work}
echo "=== 🎬 produce_pd · $EP ==="
echo "  URL=$URL"
echo "  BGM_VOLUME=$BGM_VOLUME (golden)  TTS=$TTS_ENGINE/jf_alpha (Kokoro)"

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
  "standard": "video_pd_pipeline_v2",
  "bgm_volume": float(os.environ.get("BGM_VOLUME", "0.025")),
  "resolution": "1080:1920",
  "beats": [
    {"id": "01_hero", "kind": "page", "emotion": "hook",
     "pause": 0.8, "zoom_dir": "in", "grade": "gold",
     "caption": "한 대의 폰",
     "vo": "갤럭시 한 대. 돌봄은 깨지지 않게, 소망은 세상에 닿게. 스마트폰으로 돌리는 AI 워크스테이션, S21 Phone입니다."},
    {"id": "02_agents", "kind": "page", "emotion": "trust",
     "pause": 0.5, "zoom_dir": "pan_right", "grade": "warm",
     "caption": "세 동료",
     "vo": "역할이 다른 세 동료. 지휘 클로드, 외과 에이더, 미디어 그록. 분업이 강합니다."},
    {"id": "03_system", "kind": "page", "emotion": "map",
     "pause": 0.6, "zoom_dir": "out", "grade": "cool",
     "caption": "시스템 맵",
     "vo": "시스템 맵. 데이터가 폰에서 세상으로 흐릅니다. 실제 페이지 위 아키텍처입니다."},
    {"id": "04_centers", "kind": "page", "emotion": "rhythm",
     "pause": 0.4, "zoom_dir": "pan_left", "grade": "warm",
     "caption": "워크센터",
     "vo": "일곱 워크센터. 공장부터 인터컴까지, 자동화와 수동이 리듬처럼 맞춰집니다."},
    {"id": "05_funnel", "kind": "page", "emotion": "rise",
     "pause": 0.7, "zoom_dir": "in", "grade": "gold",
     "caption": "콘텐츠 흐름",
     "vo": "웹진 미끼에서 유튜브 강의로, 누나의 독립까지. 월 비용은 거의 제로입니다."},
    {"id": "06_constitution", "kind": "page", "emotion": "handoff",
     "pause": 1.0, "zoom_dir": "out", "grade": "cinematic",
     "caption": "핸드오프",
     "vo": "원칙은 하나. 핸드오프가 곧 성공이다. 모든 계정은 누나 명의. S21 Phone."},
  ],
  "bridges": [
    {"id": "b_open", "after": None, "before": "01_hero", "file": "bridge/b_open.mp4",
     "note": "Gemini/공짜LLM으로 제작 → Android Download에 b_open.mp4로 저장"},
    {"id": "b_close", "after": "06_constitution", "before": None, "file": "bridge/b_close.mp4",
     "note": "Gemini/공짜LLM으로 제작 → Android Download에 b_close.mp4로 저장"},
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
    "06_constitution": "#install",  # page has #install (no #constitution)
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

# ── P2 TTS (voice engine: Kokoro jf_alpha local → 폴백 grok/openai/edge) ──
echo "[P2] Voice engine TTS..."
python3 - <<'PY'
import json, os, sys
from pathlib import Path

sys.path.insert(0, os.environ["ROOT"])

outdir = Path(os.environ["OUTDIR"])
bible = json.loads((outdir / "shot_bible.json").read_text(encoding="utf-8"))
engine = os.environ.get("TTS_ENGINE", "local")

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

# ── P3 bridges: Android 갤러리/Download → 자동 감지 → bridge/ ──
echo "[P3] Bridge pickup (Android 갤러리 → bridge/)..."
bash "$ROOT/scripts/_bridge_pickup.sh" "$EP"
python3 - <<'PY'
import json, os
from pathlib import Path
outdir = Path(os.environ["OUTDIR"])
bible = json.loads((outdir / "shot_bible.json").read_text(encoding="utf-8"))
for br in bible.get("bridges") or []:
    p = outdir / br["file"]
    print(f"  bridge {br['id']}: {'OK '+str(p.stat().st_size) if p.exists() else 'SKIP (직접 넣거나 Gemini로 만들기)'}")
PY

# ── P4 FFmpeg render (Aider baseline engine, BGM golden vol) ──
echo "[P4] FFmpeg Ken Burns + BGM (volume=$BGM_VOLUME)..."
# Boss 렌더 음원 우선 (YouTube Shorts Gymnopédie → FluidSynth/helena-piano)
# 저작권: Boss 자작 렌더 · Content ID 회피 · whisper vol
export BGM_PATH="${BGM_PATH:-}"
if [[ -z "$BGM_PATH" ]]; then
  for c in \
    "$OUTDIR/bgm_shorts.m4a" \
    "$OUTDIR/bgm.m4a" \
    "$OUTDIR/bgm.mp3" \
    "$ROOT/helena-piano/bgm/output/satie_gymnopedie1.mp3" \
    "$ROOT/helena-piano/bgm/output/satie_gymnopedie3.mp3" \
    "$ROOT/helena-piano/bgm/output/clair_de_lune.mp3" \
    "$ROOT/helena-piano/bgm/output/lakme_pro.mp3"
  do
    [[ -f "$c" ]] && BGM_PATH="$c" && break
  done
fi
export BGM_PATH
echo "  BGM_PATH=${BGM_PATH:-none}"

# shot_bible captions → 한글 자막 (폰트는 _render_video CJK 해결)
export VIDEO_BRAND="${VIDEO_BRAND:-S21 Phone}"
CAPTION_ENV="$OUTDIR/work/caption_env.sh"
python3 - <<'PY'
import json, os
from pathlib import Path
out = Path(os.environ["OUTDIR"])
b = json.loads((out / "shot_bible.json").read_text(encoding="utf-8"))
beats = b.get("beats") or []
titles = [str(x.get("caption") or x.get("id", "")) for x in beats]
# shell export file (pipe-joined)
def sh_quote(s: str) -> str:
    return "'" + s.replace("'", "'\"'\"'") + "'"
envp = out / "work" / "caption_env.sh"
envp.parent.mkdir(parents=True, exist_ok=True)
envp.write_text(
    "export SLIDE_TITLES=" + sh_quote("|".join(titles)) + "\n"
    "export SLIDE_SUBTITLES=" + sh_quote("|".join("" for _ in titles)) + "\n",
    encoding="utf-8",
)
print("  captions:", titles)
PY
# shellcheck disable=SC1091
source "$CAPTION_ENV"
export SLIDE_TITLES SLIDE_SUBTITLES
echo "  SLIDE_TITLES=$SLIDE_TITLES"

python3 "$ROOT/scripts/_render_video.py" "$OUTDIR"

# ── P5 Playable + bridges + FULL-timeline Boss BGM whisper ──
echo "[P5] Playable encode + bridge bookends + full-timeline BGM..."
python3 "$ROOT/scripts/_pd_assemble.py"

# ── P5b SRT subtitles (VO 원본 → YouTube 업로드용 .srt) ──
echo "[P5b] SRT subtitles (YouTube caption sync)..."
python3 "$ROOT/scripts/_make_srt.py"

# ── P6 TG 720 ──
echo "[P6] TG 720p..."
PLAY="$OUTDIR/${EP}_playable.mp4"
TG720="$OUTDIR/${EP}_tg.mp4"
SRT="$OUTDIR/${EP}.srt"
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
    -F caption="🎬 ${EP} · PD pipeline V7
Factory: xfade + zoom variety + per-slide grade + BGM swell + staggered end card
TTS: Kokoro jf_alpha · bridges: Android 갤러리 chrono-pair
BGM vol=${BGM_VOLUME} · yuv420p High · QA gate
📝 SRT: ${SRT##*/}
— produce_pd.sh v3/V7" \
    -o /tmp/tg_pd.json -w "\nhttp=%{http_code}\n" || true
  python3 -c "import json;d=json.load(open('/tmp/tg_pd.json')); print('TG', d.get('ok'), d.get('result',{}).get('message_id') if d.get('ok') else d.get('description','')[:80])" 2>/dev/null || echo "TG parse skip"
else
  echo "  (TG skip — no token or no file)"
fi

echo "=== DONE ==="
ls -lah "$OUTDIR/${EP}_playable.mp4" "$OUTDIR/${EP}_tg.mp4" "$SRT" 2>/dev/null || true
echo "bible: $BIBLE"
echo "spec:  $ROOT/configs/video_pd_pipeline_v2.json (CURRENT)"
