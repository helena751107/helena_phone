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


def _fc_has(family: str) -> bool:
    try:
        r = subprocess.run(
            ['fc-list', family, 'file'],
            capture_output=True, text=True, timeout=5,
        )
        return bool((r.stdout or '').strip())
    except Exception:
        return False


def _resolve_font_opt(preferred_families, file_fallbacks, label='reg'):
    """Return drawtext font option that can render Hangul.

    Prefer fontconfig CJK KR families. Never silently fall back to DejaVu
    (Latin-only → □□□ tofu for Korean captions).
    """
    for fam in preferred_families:
        if _fc_has(fam):
            # Spaces must be escaped for ffmpeg filtergraph
            esc = fam.replace(' ', r'\ ')
            print(f'  🔤 font[{label}]=fontconfig:{fam}')
            return f'font={esc}'
    for fp in file_fallbacks:
        if os.path.exists(fp):
            print(f'  🔤 font[{label}]=file:{fp}')
            return f'fontfile={fp}'
    # Last resort — still Latin-only, but log loudly
    dejavu = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    print(f'  ⚠️ font[{label}]=DejaVu FALLBACK (한글 깨짐 위험 — Noto CJK 설치 필요)')
    return f'fontfile={dejavu}'


# Hangul-capable fonts (this machine has Noto Sans/Serif CJK *.ttc via fontconfig)
font_opt = _resolve_font_opt(
    ['Noto Sans CJK KR', 'Noto Sans CJK JP', 'WenQuanYi Zen Hei'],
    [
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansKR-Regular.ttf',
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
    ],
    'regular',
)
font_bold_opt = _resolve_font_opt(
    ['Noto Serif CJK KR', 'Noto Sans CJK KR', 'Noto Serif CJK JP'],
    [
        '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
    ],
    'bold',
)


def escape_drawtext(s: str) -> str:
    """Escape for ffmpeg drawtext=text=... (colon, quote, backslash, %)."""
    if s is None:
        return ''
    return (
        str(s)
        .replace('\\', r'\\')
        .replace(':', r'\:')
        .replace("'", r"\'")
        .replace('%', '%%')
    )


# BGM whisper volume (성우 안 가리게 · Boss golden 0.025)
bgm_vol = float(os.environ.get('BGM_VOLUME', '0.025'))
_bgm_env = os.environ.get('BGM_PATH', '').strip()
bgm_candidates = []
if _bgm_env and os.path.exists(_bgm_env):
    bgm_candidates.append(_bgm_env)
# Boss 렌더 음원 우선: Shorts/Gymnopédie · helena-piano FluidSynth
bgm_candidates += [f for f in [
    os.path.join(outdir, 'bgm_shorts.m4a'),
    os.path.join(outdir, 'bgm.m4a'),
    os.path.join(outdir, 'bgm.mp3'),
    '/root/work/helena-piano/bgm/output/satie_gymnopedie1.mp3',
    '/root/work/helena-piano/bgm/output/satie_gymnopedie3.mp3',
    '/root/work/helena-piano/bgm/output/clair_de_lune.mp3',
    '/root/work/helena-piano/bgm/output/lakme_pro.mp3',
] if os.path.exists(f) and f not in bgm_candidates]
bgm = bgm_candidates[0] if bgm_candidates else None
if bgm:
    print(f'  🎵 BGM candidate: {bgm} vol={bgm_vol}')
else:
    print('  ⚠️ BGM missing — will ship VO-only')

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

    # ── Ken Burns (cosine = gentle) ──
    # CRITICAL: zoompan d= must be TOTAL output frames (int), NOT 1/fps
    # (d=1/30 → 0 frames → freeze/black after concat)
    clip_t = dur + 0.5
    nframes = max(int(round(clip_t * fps)), int(round(dur * fps)), 2)
    zoom_amount = 0.05
    zoom_base = 1.08  # already zoomed to minimize letterbox bars at clip start
    zoom_expr = f'{zoom_base}+({zoom_amount})*(1-cos(2*PI*on/{nframes}))/2'
    fo_start = max(0.1, clip_t - 0.5)

    # ── Color grade ──
    grade_key = os.environ.get(f'SLIDE_{i+1}_GRADE', '').strip() or DEFAULT_GRADE
    if grade_key not in COLOR_GRADES:
        grade_key = DEFAULT_GRADE
    grade = COLOR_GRADES.get(grade_key, '') or ''
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

    title_esc = escape_drawtext(title)
    sub_esc = escape_drawtext(sub)
    anim_title = (
        f"drawtext=text='{title_esc}':fontcolor=#d4a84b:{title_size}:x=(w-text_w)/2:{title_y}"
        f":{font_bold_opt}:box=1:boxcolor=black@0.5:boxborderw=12"
    )

    # subtitle
    sub_dt = ""
    if sub:
        sub_dt = (
            f",drawtext=text='{sub_esc}':fontcolor=#b5a999:fontsize=26:x=(w-text_w)/2:"
            f"y=h*0.87:{font_opt}:box=1:boxcolor=black@0.5:boxborderw=8"
        )

    # Subscribe CTA (every 3rd slide, small top-left)
    cta = (f",drawtext=text='@HelenaPark-e7c':fontcolor=#d4a84b:fontsize=22"
           f":x=20:y=h*0.06:{font_opt}:box=1:boxcolor=black@0.4:boxborderw=6") \
          if i % 3 == 0 else ""

    # Footer watermark (S21 brand — not piano studio default)
    brand = escape_drawtext(os.environ.get('VIDEO_BRAND', 'S21 Phone'))
    footer = (
        f",drawtext=text='{brand}':fontcolor=#7a7064:fontsize=18"
        f":x=w-text_w-24:y=h-40:{font_opt}:box=1:boxcolor=black@0.5:boxborderw=6"
    )

    # Top/bottom letterbox bars (cinematic)
    bars = (
        f",drawbox=x=0:y=0:w=iw:h=ih*0.03:color=black@0.3:t=fill"
        f",drawbox=x=0:y=ih*0.97:w=iw:h=ih*0.03:color=black@0.3:t=fill"
    )

    # Build filter chain — Ken Burns still→video
    # zoompan d=nframes produces exactly nframes; then trim to clip_t
    vf = (
        f"scale={W*2}:{H*2}:force_original_aspect_ratio=decrease,"
        f"pad={W*2}:{H*2}:(ow-iw)/2:(oh-ih)/2,"
        f"zoompan=z='{zoom_expr}':d={nframes}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={fps},"
        f"fade=t=in:st=0:d=0.4,fade=t=out:st={fo_start:.2f}:d=0.45,"
    )
    if grade and grade != 'natural' and grade != '':
        vf += f"{grade},"
    vf += f"{anim_title}"
    vf += sub_dt
    vf += cta
    vf += footer
    vf += bars
    vf += f",vignette=PI/5,format=yuv420p"

    cmd = [
        'ffmpeg', '-y',
        '-loop', '1', '-i', img,
        '-i', mp3,
        '-vf', vf,
        '-c:v', 'libx264', '-preset', preset, '-crf', crf,
        '-profile:v', 'high', '-level', '4.0', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '128k', '-ar', '48000', '-ac', '2',
        '-t', f'{clip_t:.3f}',
        '-shortest',
        '-movflags', '+faststart', clip,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f'  ❌ {name}: {(r.stderr or "")[-400:]}')
        sys.exit(1)

    # per-clip gate: video must not be a 1-frame still
    try:
        vdur = float(subprocess.check_output([
            'ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'stream=duration',
            '-of', 'default=nw=1:nk=1', clip,
        ], text=True).strip() or '0')
    except Exception:
        vdur = 0.0
    if vdur < dur * 0.85:
        print(f'  ❌ {name}: video dur {vdur:.2f}s << audio {dur:.2f}s (zoompan/encode fail)')
        sys.exit(1)

    clips.append(clip)
    clip_durations.append(clip_t)
    print(f'  🎞️  {name} | {dur:.1f}s vo · {vdur:.1f}s v · frames={nframes} | grade={grade_key} | anim={anim_name}')
    sys.stdout.flush()

# ── Concat v2: demuxer (reliable). Per-clip already has fade in/out.
# OLD xfade used wrong offset = i*(d[i-1]-xfade) → video froze on clip0, rest BLACK.
n = len(clips)
tmp = os.path.join(outdir, '_concat.mp4')
concat_list = os.path.join(outdir, 'concat_v2.txt')
with open(concat_list, 'w', encoding='utf-8') as f:
    for c in clips:
        # absolute paths, single quotes escaped for concat demuxer
        ap = os.path.abspath(c).replace("'", r"'\''")
        f.write(f"file '{ap}'\n")

print(f'  🔗 concat v2 demuxer · {n} clips · expected ≈{sum(clip_durations):.1f}s')
# Re-encode concat so timebase/SAR mismatches never freeze video
concat_cmd = [
    'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_list,
    '-c:v', 'libx264', '-preset', preset, '-crf', crf,
    '-profile:v', 'high', '-level', '4.0', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '128k', '-ar', '48000', '-ac', '2',
    '-movflags', '+faststart', tmp,
]
r = subprocess.run(concat_cmd, capture_output=True, text=True)
if r.returncode != 0:
    print(f'  ❌ Concat: {(r.stderr or "")[-400:]}')
    sys.exit(1)

# concat gate: video duration ≈ sum of clips (allow 1s slack)
try:
    cat_vdur = float(subprocess.check_output([
        'ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=duration',
        '-of', 'default=nw=1:nk=1', tmp,
    ], text=True).strip() or '0')
    cat_adur = float(subprocess.check_output([
        'ffprobe', '-v', 'error', '-select_streams', 'a:0',
        '-show_entries', 'stream=duration',
        '-of', 'default=nw=1:nk=1', tmp,
    ], text=True).strip() or '0')
except Exception as e:
    print(f'  ❌ Concat probe fail: {e}')
    sys.exit(1)

expect = sum(clip_durations)
print(f'  🔗 concat probe v={cat_vdur:.1f}s a={cat_adur:.1f}s expect≈{expect:.1f}s')
if cat_vdur < expect * 0.85 or cat_vdur < cat_adur * 0.85:
    print('  ❌ CONCAT GATE FAIL: video shorter than audio/clips → would ship black tail')
    sys.exit(2)
if abs(cat_vdur - cat_adur) > 1.5:
    print(f'  ⚠️ A/V drift {abs(cat_vdur-cat_adur):.1f}s (continuing if video long enough)')

# ── Keep VO-only body for later full-timeline BGM (bridges bookend 포함) ──
import shutil
vo_only = os.path.join(outdir, f'{ep}_vo.mp4')
shutil.copy(tmp, vo_only)
print(f'  🎙 VO-only body saved: {ep}_vo.mp4')

# ── BGM whisper mix (Boss 렌더 음원 · 들릴락 말락 vol) ──
# normalize=0 keeps VO loud; volume=BGM_VOLUME alone sets the floor (no extra weights crush)
final = os.path.join(outdir, f'{ep}_final.mp4')
total_dur = sum(clip_durations)
if bgm and os.path.exists(bgm):
    fade_out_st = max(0.5, total_dur - 2.5)
    print(f'  🎵 BGM mix {os.path.basename(bgm)} vol={bgm_vol} (whisper, normalize=0)')
    r = subprocess.run([
        'ffmpeg', '-y', '-i', tmp, '-stream_loop', '-1', '-i', bgm,
        '-filter_complex',
        f'[0:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=1.0[voice];'
        f'[1:a]aformat=sample_rates=48000:channel_layouts=stereo,'
        f'volume={bgm_vol},afade=t=in:st=0:d=1.5,afade=t=out:st={fade_out_st:.1f}:d=2.0[music];'
        f'[voice][music]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[aout]',
        '-map', '0:v', '-map', '[aout]',
        '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k', '-ar', '48000', '-ac', '2',
        '-shortest', '-movflags', '+faststart', final,
    ], capture_output=True, text=True)
    if r.returncode != 0:
        print(f'  ⚠️ BGM failed ({(r.stderr or "")[-300:]}), no-BGM')
        shutil.copy(tmp, final)
        bgm = None
    else:
        print(f'  ✅ BGM mixed into {ep}_final.mp4')
else:
    shutil.copy(tmp, final)
    print('  ⚠️ no BGM file — VO only')

os.remove(tmp)
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
