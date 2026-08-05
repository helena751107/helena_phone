#!/usr/bin/env python3
"""Helena Video Renderer — Ken Burns + 크로스페이드 + BGM"""
import subprocess, os, sys

outdir = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('OUTDIR', '/root/work/out/intro')
ep = os.environ.get('EP', 'intro')
W, H = 1080, 1920
preset = 'fast'
crf = '23'
font = '/usr/share/fonts/truetype/noto/NotoSansKR-Regular.ttf'
font_bold = '/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf'

# BGM: env BGM_PATH 또는 기본 피아노 트랙
bgm_vol = float(os.environ.get('BGM_VOLUME', '0.06'))
_bgm_env = os.environ.get('BGM_PATH', '').strip()
bgm_candidates = []
if _bgm_env and os.path.exists(_bgm_env):
    bgm_candidates.append(_bgm_env)
bgm_candidates += [f for f in [
    os.path.join(outdir, 'bgm.m4a'), os.path.join(outdir, 'bgm.mp3'),
    '/root/work/helena-piano/bgm/output/satie_gymnopedie1.mp3',
    '/root/work/helena-piano/bgm/output/satie_gymnopedie3.mp3',
    '/root/work/helena-piano/bgm/output/clair_de_lune.mp3',
] if os.path.exists(f)]
bgm = bgm_candidates[0] if bgm_candidates else None

slides = ['01_hero','02_agents','03_system','04_centers','05_funnel','06_constitution']
titles = [
    'S21 PHONE  ·  Webzine Vol.01', 'Three AI Agents', 'System Architecture',
    'Seven Workcenters', 'Content Funnel  ·  Zero Cost', 'Handoff is Success',
]
subtitles = [
    '갤럭시 한 대로 돌봄과 소망을', 'cc · ds · grok', 'Phone → World 데이터 플로우',
    '공장 · 출판사 · 방송탑 · 탐사대', 'GitHub Actions · Pages · TG · Discord', '모든 계정은 누나 명의',
]

clips = []
clip_durations = []
fps = 30

for i, name in enumerate(slides):
    img = os.path.join(outdir, name + '.png')
    mp3 = os.path.join(outdir, name + '.mp3')
    clip = os.path.join(outdir, f'kb_{name}.mp4')
    title, sub = titles[i], subtitles[i]

    dur = float(subprocess.check_output(
        ['ffprobe','-v','error','-show_entries','format=duration',
         '-of','default=noprint_wrappers=1:nokey=1',mp3]
    ).decode().strip())

    zoom_amount = 0.06
    zoom_expr = f'1.0+({zoom_amount})*(1-cos(2*PI*on/({dur}*{fps})))/2'
    fo_start = max(0.1, dur - 0.5)

    vf = (
        f"scale={W}*2:{H}*2:force_original_aspect_ratio=decrease,"
        f"pad={W}*2:{H}*2:(ow-iw)/2:(oh-ih)/2,"
        f"zoompan=z='{zoom_expr}':d=1/{fps}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={fps},"
        f"fade=in:st=0:d=0.5,fade=out:st={fo_start:.2f}:d=0.5,"
        f"drawtext=text='{title}':fontcolor=#d4a84b:fontsize=38:x=(w-text_w)/2:y=h*0.80"
        f":fontfile={font_bold}:box=1:boxcolor=black@0.5:boxborderw=12,"
        f"drawtext=text='{sub}':fontcolor=#b5a999:fontsize=26:x=(w-text_w)/2:y=h*0.87"
        f":fontfile={font}:box=1:boxcolor=black@0.5:boxborderw=8,"
        f"drawtext=text='Helena Piano Studio':fontcolor=#7a7064:fontsize=18"
        f":x=w-text_w-24:y=h-40:fontfile={font}:box=1:boxcolor=black@0.5:boxborderw=6,"
        f"drawbox=x=0:y=0:w=iw:h=ih*0.04:color=black@0.3:t=fill,"
        f"drawbox=x=0:y=ih*0.96:w=iw:h=ih*0.04:color=black@0.3:t=fill,"
        f"vignette=PI/5,format=yuv420p"
    )

    cmd = [
        'ffmpeg','-y',
        '-loop','1','-i',img, '-i',mp3,
        '-c:v','libx264','-preset',preset,'-crf',crf,
        '-profile:v','high','-level','4.0','-pix_fmt','yuv420p',
        '-c:a','aac','-b:a','128k','-ar','48000','-ac','2','-shortest',
        '-t',str(dur+0.5), '-vf',vf, '-movflags','+faststart', clip
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f'  ❌ {name}: ffmpeg error'); print('  STDERR:', r.stderr[-300:]); sys.exit(1)
    clips.append(clip)
    clip_durations.append(dur + 0.5)
    print(f'  🎞️  {name} ({dur:.1f}s)')
    sys.stdout.flush()

# Simple concat
concat_list = os.path.join(outdir, 'concat.txt')
with open(concat_list, 'w') as f:
    for c in clips: f.write(f"file '{c}'\n")

tmp = os.path.join(outdir, '_concat.mp4')
r = subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',concat_list,'-c','copy',tmp],
                   capture_output=True, text=True)
if r.returncode != 0:
    print(f'  ❌ Concat failed: {r.stderr[-200:]}'); sys.exit(1)

final = os.path.join(outdir, f'{ep}_final.mp4')
if bgm and os.path.exists(bgm):
    print(f'  🎵 BGM {os.path.basename(bgm)} vol={bgm_vol}')
    r = subprocess.run([
        'ffmpeg','-y','-i',tmp,'-stream_loop','-1','-i',bgm,
        '-filter_complex',
        f'[0:a]volume=1.0[voice];'
        f'[1:a]volume={bgm_vol}[music];'
        f'[voice][music]amix=inputs=2:duration=first',
        '-c:v','copy','-c:a','aac','-b:a','128k','-shortest', final
    ], capture_output=True, text=True)
    if r.returncode != 0:
        print(f'  ⚠️ BGM mix failed, using no-BGM'); import shutil; shutil.copy(tmp, final); bgm = None
else:
    import shutil; shutil.copy(tmp, final)

os.remove(tmp)
size = os.path.getsize(final)
print(f'  ✅ {ep}_final.mp4 ({size/1024/1024:.1f}MB)  {"🎵+BGM" if bgm else "no BGM"}')
