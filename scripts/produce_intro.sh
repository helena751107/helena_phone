#!/bin/bash
# 🎬 produce_intro.sh — S21 Phone Webzine 3분 인트로 영상
# Boss 2026-08-05
set -e

URL="https://helena751107.github.io/helena_phone/"
EP="intro"
export OUTDIR="/root/work/out/${EP}"
# v3: 페이지 비주얼=Playwright(공짜) · 성우=Grok · 조립=FFmpeg
# Grok으로 랜딩 전체를 다시 그리지 않는다 (표준 v3)
export TTS_ENGINE="${TTS_ENGINE:-grok}"
export GROK_TTS_VOICE="${GROK_TTS_VOICE:-ara}"
export VOICE="ko-KR-SunHiNeural"
export URL="$URL"
export ROOT="$(cd "$(dirname "$0")/.." && pwd)"

mkdir -p "$OUTDIR"
echo "=== 🎬 인트로 (page-first · TTS=$TTS_ENGINE) — 비주얼=페이지 캡처 · 성우=Grok ==="

# ── Step 1: 대본 + TTS ──
echo "[1/3] TTS 대본 생성 ($TTS_ENGINE)..."

export PYTHONIOENCODING=utf-8

python3 -c "
import subprocess, os, sys
from pathlib import Path

outdir = os.environ['OUTDIR']
engine = os.environ.get('TTS_ENGINE', 'grok')
grok_voice = os.environ.get('GROK_TTS_VOICE', 'ara')
edge_voice = os.environ.get('VOICE', 'ko-KR-SunHiNeural')
root = Path(os.environ.get('ROOT', '/root/work'))
grok_tts = root / 'scripts' / 'grok_tts.py'

slides = [
    ('S21 Phone. 갤럭시 한 대로 돌봄과 소망을 돌리는 AI 워크스테이션입니다. 대필작가이자 간병인인 헬레나가 스마트폰 하나로 풀스택 개발 환경을 구축했습니다.', '01_hero'),
    ('터먹스와 프로트 우분투 위에 클로드 코드, 딥시크 에이더, 그록까지. 세 명의 AI 에이전트가 각자 역할을 맡아 일합니다.', '02_agents'),
    ('시스템 맵을 보면 데이터가 폰에서 세상으로 흐르는 전체 아키텍처가 한눈에 들어옵니다.', '03_system'),
    ('일곱 개의 워크센터. 공장, 출판사, 방송탑, 탐사대, 연구소, 로비, 인터컴. 모든 작업을 자동화와 수동으로 나누어 운영합니다.', '04_centers'),
    ('콘텐츠는 네이버 웹진에서 그록 에이티 퍼센트 드래프트로 시작해 유튜브 강의로 완성되고, 궁극적으로 누나의 독립으로 이어집니다. 월 비용은 거의 제로. 깃허브 페이지스와 액션즈, 텔레그램, 디스코드까지 전부 공짜입니다.', '05_funnel'),
    ('이 모든 것은 한 가지 원칙 위에 서 있습니다. 핸드오프가 곧 성공이다. 모든 계정은 누나 명의. S21 Phone Webzine. 돌봄은 깨지지 않게. 소망은 세상에 닿게.', '06_constitution'),
]

def tts(text, mp3):
    txt = mp3.replace('.mp3', '.txt') if isinstance(mp3, str) else str(Path(mp3).with_suffix('.txt'))
    Path(txt).write_text(text, encoding='utf-8')
    if engine == 'grok' and grok_tts.exists():
        r = subprocess.run([sys.executable, str(grok_tts), '--file', txt, '--out', mp3, '--voice', grok_voice, '--lang', 'ko'], capture_output=True, text=True)
        if r.returncode == 0 and Path(mp3).exists():
            return 'grok/' + grok_voice
        print('  ! grok tts fail → edge', (r.stderr or r.stdout)[:120])
    subprocess.run(['edge-tts', '-f', txt, '--voice', edge_voice, '--write-media', mp3], capture_output=True, check=False)
    return 'edge/' + edge_voice

for i, (text, name) in enumerate(slides):
    mp3_file = os.path.join(outdir, name + '.mp3')
    prov = tts(text, mp3_file)
    dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', mp3_file]).decode().strip())
    print(f'  [{i+1}/6] {name}: {dur:.1f}s ({prov}) — {text[:50]}...')

print('TTS 완료')
"

# ── Step 2: 스크린샷 (PLUGIN_STILLS 있으면 Grok 스틸 우선) ──
# PLUGIN_STILLS=/path/to/dir  with 01_hero.png|jpg …
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
        if p.exists():
            return p
        # allow 01.jpg mapping
        short = name.split('_')[0]
        p2 = d / f'{short}{ext}'
        if p2.exists():
            return p2
    return None

used_plugin = False
if plugin and Path(plugin).is_dir():
    for name in names:
        src = find_still(Path(plugin), name)
        if src:
            dest = outdir / f'{name}.png'
            if src.suffix.lower() == '.png':
                shutil.copy2(src, dest)
            else:
                # normalize to png via ffmpeg for pipeline
                import subprocess
                subprocess.run(['ffmpeg','-y','-i',str(src),str(dest)], capture_output=True)
            print(f'  🖼  plugin {name} ← {src.name}')
            used_plugin = True
        else:
            print(f'  ! missing plugin still {name}')
    if used_plugin:
        print('플러그인 스틸 사용 (스크린샷 스킵)')
        raise SystemExit(0)

from playwright.sync_api import sync_playwright
url = os.environ['URL']
with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={'width': 390, 'height': 844})  # iPhone 14 Pro = 고밀도
    page.goto(url, wait_until='networkidle')
    page.wait_for_timeout(3000)
    sections = [
        ('01_hero', 0),
        ('02_agents', 1),
        ('03_system', 2),
        ('04_centers', 3),
        ('05_funnel', 4),
        ('06_constitution', 5),
    ]
    for name, nth in sections:
        if nth == 0:
            page.evaluate('window.scrollTo(0, 0)')
        else:
            page.evaluate(f'window.scrollBy(0, window.innerHeight * {nth})')
        page.wait_for_timeout(800)
        page.screenshot(path=str(outdir / f'{name}.png'), full_page=False)
        print(f'  📸 {name}')
    b.close()
    print('스크린샷 완료')
"

# ── Step 3: FFmpeg 영상 — Ken Burns + 크로스페이드 + BGM ──
echo "[3/3] FFmpeg 영상 제작 (Ken Burns + BGM)..."
python3 "$(dirname "$0")/_render_video.py" "$OUTDIR"

echo ""
echo "=== 🎬 인트로 제작 완료 ==="
echo "파일: ${OUTDIR}/${EP}_final.mp4"
ls -lah "${OUTDIR}/${EP}_final.mp4"
