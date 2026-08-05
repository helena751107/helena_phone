#!/bin/bash
# 🎬 produce_intro.sh — S21 Phone Webzine 인트로 영상 (InShot-level)
# Boss 2026-08-06 · V4
set -e

URL="https://helena751107.github.io/helena_phone/"
EP="intro"
export OUTDIR="/root/work/out/${EP}"
export TTS_ENGINE="${TTS_ENGINE:-grok}"          # grok|openai|edge (edge=비상업 only)
export GROK_TTS_VOICE="${GROK_TTS_VOICE:-ara}"
export VOICE="ko-KR-SunHiNeural"
export BGM_VOLUME="${BGM_VOLUME:-0.025}"         # Golden whisper
export PRESET="${PRESET:-}"                       # shorts|tiktok|""
export CAPTION_STYLE="${CAPTION_STYLE:-bounce}"   # CapCut captions: bounce|type|glow|""
export URL="$URL"
export ROOT="$(cd "$(dirname "$0")/.." && pwd)"

mkdir -p "$OUTDIR"
echo "=== 🎬 S21 Phone 인트로 영상 제작 (TTS=$TTS_ENGINE, BGM=$BGM_VOLUME, preset=$PRESET) ==="

# ── Step 1: TTS (voice engine — Grok 우선, 6슬라이드) ──
echo "[1/3] TTS 대본 생성 (voice_engine/$TTS_ENGINE)..."
python3 "$(dirname "$0")/_make_tts.py" "$OUTDIR"

# ── Step 2: 스크린샷 ──
export PLUGIN_STILLS="${PLUGIN_STILLS:-}"
echo "[2/3] 비주얼 (plugin stills 또는 페이지 스크린샷)..."

python3 -c "
import os, shutil
from pathlib import Path

outdir = Path(os.environ['OUTDIR'])
plugin = os.environ.get('PLUGIN_STILLS', '').strip()
names = ['01_hero', '02_agents', '03_system', '04_centers', '05_funnel', '06_constitution']

def find_still(d: Path, name: str):
    for ext in ('.png', '.jpg', '.jpeg', '.webp'):
        p = d / f'{name}{ext}'
        if p.exists(): return p
        short = name.split('_')[0]
        p2 = d / f'{short}{ext}'
        if p2.exists(): return p2
    return None

if plugin and Path(plugin).is_dir():
    for name in names:
        src = find_still(Path(plugin), name)
        if src:
            dest = outdir / f'{name}.png'
            if src.suffix.lower() == '.png':
                shutil.copy2(src, dest)
            else:
                subprocess.run(['ffmpeg','-y','-i',str(src),str(dest)], capture_output=True)
            print(f'  🖼  plugin {name} ← {src.name}')
        else:
            print(f'  ! missing plugin still {name}')
    raise SystemExit(0)

from playwright.sync_api import sync_playwright
url = os.environ['URL']
with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={'width': 390, 'height': 844})
    page.goto(url, wait_until='networkidle')
    page.wait_for_timeout(3000)
    sections = [(n, i) for i, n in enumerate(names)]
    for name, nth in sections:
        page.evaluate('window.scrollTo(0, 0)') if nth == 0 else page.evaluate(f'window.scrollBy(0, window.innerHeight * {nth})')
        page.wait_for_timeout(800)
        page.screenshot(path=str(outdir / f'{name}.png'), full_page=False)
        print(f'  📸 {name}')
    b.close()
    print('스크린샷 완료')
"

# ── Step 3: InShot-level FFmpeg ──
echo "[3/3] FFmpeg 영상 제작 (InShot FX + BGM whisper)..."
python3 "$(dirname "$0")/_render_video.py" "$OUTDIR"

echo ""
echo "=== 🎬 인트로 제작 완료 ==="
ls -lah "${OUTDIR}/${EP}_final.mp4"
