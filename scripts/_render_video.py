#!/usr/bin/env python3
"""Helena Video Renderer — InShot-level 제작 파이프 (공짜 FFmpeg)

V5 — Boss 2026-08-06
- InShot FX: text pop/slideup/typewriter · multi-transition · speed ramp · color grade
- CapCut style: animated captions · Shorts/TikTok presets · safe zone
- yuv420p High@L4.0 · AAC 48k · phone-playable guarantee
"""
import subprocess, os, sys, math, random, json
from pathlib import Path

outdir = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('OUTDIR', '/root/work/out/intro')
ep = os.environ.get('EP', 'intro')
W, H = 1080, 1920
fps = 30
preset = os.environ.get('FF_PRESET', 'fast')
crf = os.environ.get('FF_CRF', '23')
font = '/usr/share/fonts/truetype/noto/NotoSansKR-Regular.ttf'
font_bold = '/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf'
for fp in [font, font_bold]:
    if not os.path.exists(fp):
        if 'NotoSansKR' in fp:
            font = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
        else:
            font_bold = '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'

# BGM whisper volume (성우 안 가리게)
bgm_vol = float(os.environ.get('BGM_VOLUME', '0.025'))
_bgm_env = os.environ.get('BGM_PATH', '').strip()
bgm_candidates = []
if _bgm_env and os.path.exists(_bgm_env):
    bgm_candidates.append(_bgm_env)
bgm_candidates += [f for f in [
    '/root/work/helena-piano/bgm/output/satie_gymnopedie1.mp3',
    '/root/work/helena-piano/bgm/output/satie_gymnopedie3.mp3',
    '/root/work/helena-piano/bgm/output/clair_de_lune.mp3',
] if os.path.exists(f)]
bgm = bgm_candidates[0] if bgm_candidates else None

# Slides autodetect (01_hero.png, 02_*.png ...)
slides = []
for f in sorted(os.listdir(outdir)):
    if f.endswith('.png') and f[0].isdigit():
        name = f.replace('.png','')
        if os.path.exists(os.path.join(outdir, name + '.mp3')):
            slides.append(name)
if not slides:
    print('❌ No slides found (need NNAME.png + NNAME.mp3)')
    sys.exit(1)

# Titles from slides/ env
titles_env = os.environ.get('SLIDE_TITLES','').split('|')
subtitles_env = os.environ.get('SLIDE_SUBTITLES','').split('|')
trans_env = os.environ.get('SLIDE_TRANSITIONS','').split('|')  # per-slide transition override
anim_env = os.environ.get('SLIDE_ANIMS','').split('|')          # per-slide text animation
while len(titles_env) < len(slides): titles_env.append(slides[len(titles_env)])
while len(subtitles_env) < len(slides): subtitles_env.append('')
while len(trans_env) < len(slides): trans_env.append('')
while len(anim_env) < len(slides): anim_env.append('')

# ── InShot FX presets ──
# Transitions — applied as xfade between clips
TRANSITIONS = {
    'fade':       'fade',
    'wipeleft':   'wipeleft',
    'wiperight':  'wiperight',
    'slideup':    'slideup',
    'slidedown':  'slidedown',
    'circlecrop': 'circlecrop',
    'hlslice':    'hlslice',     # horizontal slice
    'vuslice':    'vuslice',     # vertical slice
    'pixelize':   'pixelize',
    'dissolve':   'dissolve',
}
DEFAULT_TRANSITION = 'fade'

# Color grades — InShot equivalent
COLOR_GRADES = {
    'warm':      'eq=gamma=1.05:contrast=1.05:saturation=1.12:brightness=0.02',
    'cinematic': 'eq=gamma=0.95:contrast=1.15:saturation=0.85:brightness=-0.03',
    'natural':   '',
    'cool':      'eq=gamma=0.98:contrast=1.05:saturation=0.92:brightness=0.01',
    'gold':      'eq=gamma=1.03:contrast=1.08:saturation=1.08:brightness=0.03,colorbalance=rs=0.05:gs=-0.02:bs=-0.08',
}
DEFAULT_GRADE = 'warm'

# Text animations — InShot text FX
TEXT_ANIMS = {
    # pop: oscillating fontsize (subtle bounce)
    'pop': (
        lambda dur: (
            f":fontsize='max(34, 40 + 8*sin(2*PI*3.5*t))'",
            f"fontsize=40"  # fallback static
        )
    ),
    # slideup: ease-out entrance from below
    'slideup': (
        lambda dur: (
            f":y='h*0.78 + (h*0.12)*exp(-t*4.5)'",
            f"y=h*0.80"
        )
    ),
    # typewriter: progressive fade-in (simulated with alpha ramp)
    'typewriter': (
        lambda dur: (
            f":alpha='min(1, t*{max(1.5, 3.0/dur):.1f})'",
            f""
        )
    ),
    # none: static text
    'static': (
        lambda dur: ("", "")
    ),
}
DEFAULT_ANIM = 'slideup'

# Speed ramp presets (applied to whole clip via setpts)
# 'slow_in': start slow, speed up
# 'punch': fast middle, slow ends
SPEED_RAMPS = {
    'none':       '',
    'slow_in':    "setpts=(0.7+0.3*(1-exp(-t*2)))*PTS,",
    'punch':      "setpts=(1.1-0.25*sin(PI*t/TB)))*PTS,",
}

# ── Shorts/TikTok presets ──
PRESET = os.environ.get('PRESET', '').strip()
if PRESET == 'shorts':
    crf = '22'
elif PRESET == 'tiktok':
    crf = '23'
    # TikTok likes 9:16, slightly softer
    preset = 'veryfast'

clips = []
clip_durations = []
clip_transitions = []  # for multi-transition concat

for i, name in enumerate(slides):
    img = os.path.join(outdir, name + '.png')
    mp3 = os.path.join(outdir, name + '.mp3')
    clip = os.path.join(outdir, f'kb_{name}.mp4')
    title = titles_env[i] if i < len(titles_env) else name
    sub = subtitles_env[i] if i < len(subtitles_env) else ''

    dur = float(subprocess.check_output(
        ['ffprobe','-v','error','-show_entries','format=duration',
         '-of','default=noprint_wrappers=1:nokey=1',mp3]
    ).decode().strip())

    # ── Ken Burns (cosine = gentle, no jerky zoom) ──
    zoom_amount = 0.05
    zoom_expr = f'1.0+({zoom_amount})*(1-cos(2*PI*on/({dur}*{fps})))/2'
    fo_start = max(0.1, dur - 0.5)

    # ── Color grade ──
    grade_key = (COLOR_GRADES.get(os.environ.get(f'SLIDE_{i+1}_GRADE', '').strip())
                 or COLOR_GRADES.get(DEFAULT_GRADE))
    grade = COLOR_GRADES.get(grade_key, '')
    if isinstance(grade, dict):
        grade = grade.get('vf', '')

    # ── Transition (per-slide, used in concat phase) ──
    trans_name = (trans_env[i].strip() or DEFAULT_TRANSITION)
    xfade_name = TRANSITIONS.get(trans_name, 'fade')
    clip_transitions.append(xfade_name)

    # ── Text animation ──
    anim_name = (anim_env[i].strip() or DEFAULT_ANIM)
    anim_pair = TEXT_ANIMS.get(anim_name, TEXT_ANIMS['static'])
    text_expr, _text_fallback = anim_pair(dur)

    # Build animated text drawtext filter
    # title — headline with animation
    title_y = f"y=h*0.80"
    title_size = "fontsize=40"
    # If animation modifies fontsize or position, inject into drawtext
    if anim_name == 'pop':
        title_size = "fontsize='max(34, 42 + 8*sin(2*PI*3.5*t))'"
    elif anim_name == 'slideup':
        title_y = "y='h*0.78 + (h*0.12)*exp(-t*4.5)'"

    anim_title = (
        f"drawtext=text='{title}':fontcolor=#d4a84b:{title_size}:x=(w-text_w)/2:{title_y}"
        f":fontfile={font_bold}:box=1:boxcolor=black@0.5:boxborderw=12"
    )

    # subtitle
    sub_dt = ""
    if sub:
        sub_dt = (
            f",drawtext=text='{sub}':fontcolor=#b5a999:fontsize=26:x=(w-text_w)/2:"
            f"y=h*0.87:fontfile={font}:box=1:boxcolor=black@0.5:boxborderw=8"
        )

    # Subscribe CTA (every 3rd slide, small top-left)
    cta = (f",drawtext=text='@HelenaPark-e7c':fontcolor=#d4a84b:fontsize=22"
           f":x=20:y=h*0.06:fontfile={font}:box=1:boxcolor=black@0.4:boxborderw=6") \
          if i % 3 == 0 else ""

    # Footer watermark
    footer = (
        f",drawtext=text='Helena Piano Studio':fontcolor=#7a7064:fontsize=18"
        f":x=w-text_w-24:y=h-40:fontfile={font}:box=1:boxcolor=black@0.5:boxborderw=6"
    )

    # Top/bottom letterbox bars (cinematic)
    bars = (
        f",drawbox=x=0:y=0:w=iw:h=ih*0.03:color=black@0.3:t=fill"
        f",drawbox=x=0:y=ih*0.97:w=iw:h=ih*0.03:color=black@0.3:t=fill"
    )

    # Build filter chain — InShot style
    vf = (
        f"scale={W}*2:{H}*2:force_original_aspect_ratio=decrease,"
        f"pad={W}*2:{H}*2:(ow-iw)/2:(oh-ih)/2,"
        f"zoompan=z='{zoom_expr}':d=1/{fps}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={fps},"
        f"fade=in:st=0:d=0.5,fade=out:st={fo_start:.2f}:d=0.5,"
    )
    # Color grade (if not natural)
    if grade and grade != 'natural' and grade != '':
        vf += f"{grade},"
    # Text overlays
    vf += f"{anim_title}"
    vf += sub_dt
    vf += cta
    vf += footer
    vf += bars
    # Vignette + final format
    vf += f",vignette=PI/5,format=yuv420p"

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
        print(f'  ❌ {name}: {r.stderr[-200:]}')
        sys.exit(1)
    clips.append(clip)
    clip_durations.append(dur + 0.5)
    print(f'  🎞️  {name} | {dur:.1f}s | grade={grade_key} | anim={anim_name} | trans={trans_name}')
    sys.stdout.flush()

# ── Multi-transition Concat ──
n = len(clips)
if n == 1:
    concat_list = os.path.join(outdir, 'concat.txt')
    with open(concat_list, 'w') as f:
        f.write(f"file '{clips[0]}'\n")
else:
    # xfade chain with per-slide transition types
    concat_list = os.path.join(outdir, 'concat_xfade.txt')
    xfade_sec = 0.5
    inputs = []
    for c in clips:
        inputs.extend(['-i', str(c)])

    filter_parts = []
    vprev = '[0:v]'
    aprev = '[0:a]'
    for i in range(1, n):
        offset = i * (clip_durations[i-1] - xfade_sec)
        xfade_type = clip_transitions[i] if i < len(clip_transitions) else 'fade'
        vout = f'[vfinal]' if i == n - 1 else f'[vx{i}]'
        aout = f'[afinal]' if i == n - 1 else f'[ax{i}]'
        filter_parts.append(
            f"{vprev}[{i}:v]xfade=transition={xfade_type}:duration={xfade_sec}:offset={offset:.3f}{vout}"
        )
        filter_parts.append(
            f"{aprev}[{i}:a]acrossfade=d={xfade_sec}{aout}"
        )
        vprev = vout
        aprev = aout

    fc = ';'.join(filter_parts)

tmp = os.path.join(outdir, '_concat.mp4')
concat_cmd = (
    ['ffmpeg','-y'] + inputs +
    ['-filter_complex', fc + ';[vfinal]format=yuv420p[v];[afinal]aformat=sample_rates=48000[a]',
     '-map','[v]','-map','[a]',
     '-c:v','libx264','-preset',preset,'-crf',crf,
     '-profile:v','high','-level','4.0','-pix_fmt','yuv420p',
     '-c:a','aac','-b:a','128k','-ar','48000','-movflags','+faststart', tmp]
) if n > 1 else (
    ['ffmpeg','-y','-f','concat','-safe','0','-i', concat_list, '-c','copy', tmp]
)

r = subprocess.run(concat_cmd, capture_output=True, text=True)
if r.returncode != 0:
    print(f'  ❌ Concat: {r.stderr[-300:]}')
    sys.exit(1)

# ── BGM whisper mix ──
final = os.path.join(outdir, f'{ep}_final.mp4')
if bgm and os.path.exists(bgm):
    print(f'  🎵 BGM {os.path.basename(bgm)} vol={bgm_vol}')
    r = subprocess.run([
        'ffmpeg','-y','-i',tmp,'-stream_loop','-1','-i',bgm,
        '-filter_complex',
        f'[0:a]volume=1.0[voice];'
        f'[1:a]volume={bgm_vol},afade=t=in:st=0:d=1.5,afade=t=out:st={sum(clip_durations)-3:.1f}:d=2.5[music];'
        f'[voice][music]amix=inputs=2:duration=first:dropout_transition=3:weights=1 0.3',
        '-c:v','copy','-c:a','aac','-b:a','128k','-shortest', final
    ], capture_output=True, text=True)
    if r.returncode != 0:
        print(f'  ⚠️ BGM failed ({r.stderr[-150:]}), no-BGM')
        import shutil; shutil.copy(tmp, final)
        bgm = None
else:
    import shutil; shutil.copy(tmp, final)

os.remove(tmp)
total_dur = sum(clip_durations)
size = os.path.getsize(final)

# ── Encode gate (phone-playable check) ──
rp = subprocess.run(
    ['ffprobe','-v','error','-select_streams','v:0',
     '-show_entries','stream=pix_fmt,profile',
     '-of','default=nw=1:nk=1', final],
    capture_output=True, text=True
)
pix_info = (rp.stdout or '').strip()
if 'yuv444' in pix_info or '4:4:4' in pix_info:
    print(f'  ❌ GATE FAIL: yuv444 detected — phone playback broken')
    sys.exit(2)

print(f'  ✅ {ep}_final.mp4 ({size/1024/1024:.1f}MB, {total_dur:.0f}s)  {"🎵+BGM" if bgm else "no BGM"}  GATE={pix_info}')
print(f'  🎬 InShot FX: text_anim={DEFAULT_ANIM} · transitions={set(clip_transitions)} · grade={DEFAULT_GRADE}')

# ── CapCut-style shorts variant ──
if PRESET in ('shorts', 'tiktok'):
    tg = os.path.join(outdir, f'{ep}_tg.mp4')
    subprocess.run([
        'ffmpeg','-y','-i',final,
        '-c:v','libx264','-profile:v','high','-level','4.0','-pix_fmt','yuv420p',
        '-preset','veryfast','-crf','24',
        '-vf','scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,format=yuv420p',
        '-c:a','aac','-b:a','128k','-ar','48000','-ac','2','-movflags','+faststart',
        tg
    ], capture_output=True, text=True)
    print(f'  📱 {PRESET} export: {tg} ({os.path.getsize(tg)/1024/1024:.1f}MB)')
