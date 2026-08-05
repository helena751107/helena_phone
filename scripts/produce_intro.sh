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
    page = b.new_page(viewport={'width': 412, 'height': 915})
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

python3 << 'PYEOF'
import subprocess, os, random

outdir = os.environ['OUTDIR']
ep = os.environ.get('EP', 'intro')
W, H = 720, 1280
preset = 'fast'
crf = '23'
font = '/usr/share/fonts/truetype/noto/NotoSansKR-Regular.ttf'
font_bold = '/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf'

# BGM: 헬레나 피아노 트랙 중 하나 자동 선택
bgm_candidates = [f for f in [
    '/root/work/helena-piano/bgm/output/clair_de_lune.mp3',
    '/root/work/helena-piano/bgm/output/satie_gymnopedie1.mp3',
    '/root/work/helena-piano/bgm/output/satie_gymnopedie3.mp3',
] if os.path.exists(f)]
bgm = bgm_candidates[0] if bgm_candidates else None

slides = ['01_hero','02_agents','03_system','04_centers','05_funnel','06_constitution']
titles = [
    'S21 PHONE  ·  Webzine Vol.01',
    'Three AI Agents',
    'System Architecture',
    'Seven Workcenters',
    'Content Funnel  ·  Zero Cost',
    'Handoff is Success',
]
subtitles = [
    '갤럭시 한 대로 돌봄과 소망을',
    'cc · ds · grok',
    'Phone → World 데이터 플로우',
    '공장 · 출판사 · 방송탑 · 탐사대',
    'GitHub Actions · Pages · TG · Discord',
    '모든 계정은 누나 명의',
]

clips = []
clip_durations = []
for i, name in enumerate(slides):
    img = os.path.join(outdir, name + '.png')
    mp3 = os.path.join(outdir, name + '.mp3')
    clip = os.path.join(outdir, f'kb_{name}.mp4')
    title = titles[i]
    sub = subtitles[i]

    # Ken Burns 방향 랜덤 (zoom in or out)
    zoom_dir = random.choice(['in','out'])
    if zoom_dir == 'in':
        zoom_expr = f"1.0+(on/({H}/{2.5}))*0.08"
    else:
        zoom_expr = f"1.08-(on/({H}/{2.5}))*0.08"

    vf = (
        f"scale={W}*2:{H}*2:force_original_aspect_ratio=decrease,"
        f"pad={W}*2:{H}*2:(ow-iw)/2:(oh-ih)/2,"
        f"zoompan=z='{zoom_expr}':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps=25,"
        f"drawtext=text='{title}':fontcolor=#d4a84b:fontsize=32:x=(w-text_w)/2:y=h*0.82"
        f":fontfile={font_bold}:box=0:shadowcolor=black@0.6:shadowx=3:shadowy=3,"
        f"drawtext=text='{sub}':fontcolor=#b5a999:fontsize=22:x=(w-text_w)/2:y=h*0.88"
        f":fontfile={font}:box=0:shadowcolor=black@0.5:shadowx=2:shadowy=2,"
        f"drawtext=text='Helena Piano Studio':fontcolor=#7a7064:fontsize=16"
        f":x=20:y=h-36:fontfile={font},"
        f"vignette=PI/4:mode=multiply,format=yuv420p"
    )

    dur = float(subprocess.check_output(
        ['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',mp3]
    ).decode().strip())

    subprocess.run([
        'ffmpeg','-y',
        '-loop','1','-i',img,
        '-i',mp3,
        '-c:v','libx264','-preset',preset,'-crf',crf,
        '-c:a','aac','-b:a','128k','-shortest',
        '-t',str(dur+0.5),
        '-vf',vf,
        clip
    ], capture_output=True)
    clips.append(clip)
    clip_durations.append(dur + 0.5)
    print(f'  🎞️  {name} ({zoom_dir}, {dur:.1f}s)')
    random.seed()

# 크로스페이드 concat
if len(clips) > 1:
    filter_parts = []
    for ci in range(len(clips)):
        filter_parts.append(f"[{ci}:v]fps=25,setpts=PTS-STARTPTS,format=yuv420p[v{ci}];")
        filter_parts.append(f"[{ci}:a]aformat=sample_rates=44100:channel_layouts=stereo[a{ci}];")

    crossfade_filters = ''
    prev_v = '[v0]'
    prev_a = '[a0]'
    dur_sum = 0
    for ci in range(1, len(clips)):
        next_v = f'[v{ci}]'
        next_a = f'[a{ci}]'
        dur_sum += clip_durations[ci-1] - 0.25
        crossfade_filters += f'{prev_v}{next_v}xfade=transition=fade:duration=0.5:offset={dur_sum:.2f}[vx{ci}];'
        crossfade_filters += f'{prev_a}{next_a}acrossfade=d=0.5[ax{ci}];'
        prev_v = f'[vx{ci}]'
        prev_a = f'[ax{ci}]'

    filter_complex = ''.join(filter_parts) + crossfade_filters
    final = os.path.join(outdir, f'{ep}_final.mp4')

    cmd = ['ffmpeg','-y']
    for c in clips:
        cmd += ['-i', c]
    if bgm and os.path.exists(bgm):
        cmd += ['-stream_loop','-1','-i', bgm]
        filter_complex += f'[{prev_a}]volume=0.25[voice];[{len(clips)}:a]volume=0.12[music];[voice][music]amix=inputs=2:duration=first[finala]'
        cmd += ['-filter_complex', filter_complex, '-map', f'[{prev_v}]', '-map', '[finala]']
    else:
        cmd += ['-filter_complex', filter_complex, '-map', f'[{prev_v}]', '-map', f'[{prev_a}]']

    cmd += ['-c:v','libx264','-preset',preset,'-crf',crf,'-c:a','aac','-b:a','128k',final]
    subprocess.run(cmd, capture_output=True)
else:
    # Single clip: just copy
    final = os.path.join(outdir, f'{ep}_final.mp4')
    import shutil; shutil.copy(clips[0], final)

size = os.path.getsize(final)
print(f'  ✅ {ep}_final.mp4 ({size/1024/1024:.1f}MB)  {"🎵+BGM" if bgm else ""}')
PYEOF

echo ""
echo "=== 🎬 인트로 제작 완료 ==="
echo "파일: ${OUTDIR}/${EP}_final.mp4"
ls -lah "${OUTDIR}/${EP}_final.mp4"
