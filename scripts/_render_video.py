#!/usr/bin/env python3
"""Helena Video Renderer — InShot-level 제작 파이프 (공짜 FFmpeg)

V7 — Boss 2026-08-07
- V7: breathing pauses · zoom variety (in/out/pan) · per-slide grade · BGM envelope · staggered end card
- V6: audio ducking (sidechaincompress) · xfade multi-transition · end card
- InShot FX: text pop/slideup/typewriter · multi-transition · speed ramp · color grade
- CapCut style: animated captions · Shorts/TikTok presets · safe zone
- yuv420p High@L4.0 · AAC 48k · phone-playable guarantee
"""
import subprocess, os, sys, math, random, json, shutil
from pathlib import Path

outdir = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('OUTDIR', '/root/work/out/intro')
ep = os.environ.get('EP', 'intro')
W, H = 1080, 1920
fps = 30
preset = os.environ.get('FF_PRESET', 'fast')
crf = os.environ.get('FF_CRF', '23')

# ── V6: audio ducking params ──
duck_enabled = os.environ.get('AUDIO_DUCKING', '1') not in ('0', 'false', 'no')
# sidechaincompress: compress music (1st input) when voice (2nd input) exceeds threshold
duck_threshold = float(os.environ.get('DUCK_THRESHOLD', '0.02'))   # linear 0-1
duck_ratio = int(os.environ.get('DUCK_RATIO', '3'))
duck_attack = int(os.environ.get('DUCK_ATTACK', '5'))              # ms
duck_release = int(os.environ.get('DUCK_RELEASE', '300'))          # ms

# ── V6: xfade transition cycle ──
XFADE_DUR = float(os.environ.get('XFADE_DUR', '0.4'))
TRANSITION_CYCLE = ['fade', 'wipeleft', 'slideright', 'dissolve']

# ── V6: end card ──
END_CARD_DUR = float(os.environ.get('END_CARD_DUR', '3.0'))
end_card_enabled = os.environ.get('END_CARD', '1') not in ('0', 'false', 'no')


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
    for fam in preferred_families:
        if _fc_has(fam):
            esc = fam.replace(' ', r'\ ')
            print(f'  🔤 font[{label}]=fontconfig:{fam}')
            return f'font={esc}'
    for fp in file_fallbacks:
        if os.path.exists(fp):
            print(f'  🔤 font[{label}]=file:{fp}')
            return f'fontfile={fp}'
    dejavu = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    print(f'  ⚠️ font[{label}]=DejaVu FALLBACK (한글 깨짐 위험 — Noto CJK 설치 필요)')
    return f'fontfile={dejavu}'


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
    if s is None:
        return ''
    return (
        str(s)
        .replace('\\', r'\\')
        .replace(':', r'\:')
        .replace("'", r"\'")
        .replace('%', '%%')
    )


# ── V8: build_filter_for_slide — unified per-slide filter chain ──
def build_filter_for_slide(img, mp3, out_clip, beat, fonts, fps, W, H, brand, preset, crf):
    """Encode one slide to kb_{id}.mp4. Returns (clip_path, clip_dur)."""
    dur = float(subprocess.check_output(
        ['ffprobe','-v','error','-show_entries','format=duration',
         '-of','default=noprint_wrappers=1:nokey=1', mp3]
    ).decode().strip())

    name = beat['id']
    pause = beat.get('pause', 0.0)
    zoom_spec = beat.get('zoom', {})
    zoom_dir = zoom_spec.get('type', 'in') if isinstance(zoom_spec, dict) else str(zoom_spec)
    pan_dir = zoom_spec.get('pan', 'none') if isinstance(zoom_spec, dict) else 'none'
    grade_key = beat.get('color_tag', beat.get('grade', 'warm'))

    # ── Ken Burns V8: zoom variety ──
    clip_t = dur + 0.5 + pause
    nframes = max(int(round(clip_t * fps)), int(round(dur * fps)), 2)
    zoom_amount = 0.05
    zoom_base = 1.08
    pan_amount = 0.08

    if zoom_dir == 'out':
        zoom_expr = f'{zoom_base+zoom_amount}-{zoom_amount}*(on/{nframes})'
    elif zoom_dir == 'in':
        zoom_expr = f'{zoom_base}+{zoom_amount}*(1-cos(PI*on/{nframes}))/2'
    else:
        zoom_expr = f'{zoom_base}+{zoom_amount}*(1-cos(2*PI*on/{nframes}))/2'

    if pan_dir == 'right':
        pan_x = f'iw/2-(iw/zoom/2)+{pan_amount}*iw*(2*on/{nframes}-1)/zoom'
    elif pan_dir == 'left':
        pan_x = f'iw/2-(iw/zoom/2)-{pan_amount}*iw*(2*on/{nframes}-1)/zoom'
    else:
        pan_x = f'iw/2-(iw/zoom/2)'

    # ── Color grade ──
    if grade_key not in COLOR_GRADES:
        grade_key = 'warm'
    grade = COLOR_GRADES.get(grade_key, '') or ''
    if isinstance(grade, dict):
        grade = grade.get('vf', '')

    # ── Text animation ──
    title = beat.get('caption', name)
    sub = ''
    anim_name = 'slideup'

    title_y = f"y=h*0.80"
    title_size = "fontsize=40"
    if anim_name == 'slideup':
        title_y = "y='h*0.78 + (h*0.12)*exp(-t*4.5)'"

    font_opt, font_bold_opt = fonts

    title_esc = escape_drawtext(title)
    anim_title = (
        f"drawtext=text='{title_esc}':fontcolor=#d4a84b:{title_size}:x=(w-text_w)/2:{title_y}"
        f":{font_bold_opt}:box=1:boxcolor=black@0.5:boxborderw=12"
    )

    sub_dt = ""
    if sub:
        sub_esc = escape_drawtext(sub)
        sub_dt = (
            f",drawtext=text='{sub_esc}':fontcolor=#b5a999:fontsize=26:x=(w-text_w)/2:"
            f"y=h*0.87:{font_opt}:box=1:boxcolor=black@0.5:boxborderw=8"
        )

    cta = ""
    brand_esc = escape_drawtext(brand)
    footer = (
        f",drawtext=text='{brand_esc}':fontcolor=#7a7064:fontsize=18"
        f":x=w-text_w-24:y=h-40:{font_opt}:box=1:boxcolor=black@0.5:boxborderw=6"
    )

    bars = (
        f",drawbox=x=0:y=0:w=iw:h=ih*0.03:color=black@0.3:t=fill"
        f",drawbox=x=0:y=ih*0.97:w=iw:h=ih*0.03:color=black@0.3:t=fill"
    )

    # ── Assemble vf ──
    vf = (
        f"scale={W*2}:{H*2}:force_original_aspect_ratio=decrease,"
        f"pad={W*2}:{H*2}:(ow-iw)/2:(oh-ih)/2,"
        f"zoompan=z='{zoom_expr}':d={nframes}:x='{pan_x}':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={fps},"
        f"fade=t=in:st=0:d=0.35,"
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
        '-movflags', '+faststart', out_clip,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f'  ❌ {name}: {(r.stderr or "")[-400:]}')
        sys.exit(1)

    # per-clip gate
    try:
        vdur = float(subprocess.check_output([
            'ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'stream=duration',
            '-of', 'default=nw=1:nk=1', out_clip,
        ], text=True).strip() or '0')
    except Exception:
        vdur = 0.0
    if vdur < dur * 0.85:
        print(f'  ❌ {name}: video dur {vdur:.2f}s << audio {dur:.2f}s (zoompan/encode fail)')
        sys.exit(1)

    return out_clip, clip_t


# ── V8: stinger clip generator ──
def build_stinger_clip(out_clip, stinger_cfg, fonts, fps, W, H, preset, crf):
    """Generate 0.5s channel signature stinger: logo flash + short beep."""
    dur = float(stinger_cfg.get('duration', 0.5))
    text = stinger_cfg.get('text', 'S21 Phone')
    font_opt, font_bold_opt = fonts
    text_esc = escape_drawtext(text)
    stinger_vf = (
        f"drawtext=text='{text_esc}':fontcolor=#d4a84b:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2:{font_bold_opt}"
        f":alpha='if(lt(t,0.1),t*10,if(gt(t,{dur-0.15}),({dur}-t)/0.15*3,1))',"
        f"fade=t=in:st=0:d=0.05,fade=t=out:st={dur-0.1}:d=0.1,format=yuv420p"
    )
    r = subprocess.run([
        'ffmpeg', '-y',
        '-f', 'lavfi', '-i', f'color=c=0x0d1117:s={W}x{H}:d={dur}:r={fps}',
        '-f', 'lavfi', '-i', f'sine=frequency=587.33:duration=0.12,volume=0.3',
        '-filter_complex', f'[1:a]adelay=50|50,apad=pad_dur={dur}:whole_dur={dur}[aout]',
        '-vf', stinger_vf,
        '-map', '0:v', '-map', '[aout]',
        '-c:v', 'libx264', '-preset', preset, '-crf', crf,
        '-profile:v', 'high', '-level', '4.0', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '128k', '-ar', '48000', '-ac', '2',
        '-t', str(dur), '-movflags', '+faststart', out_clip,
    ], capture_output=True, text=True)
    if r.returncode != 0:
        print(f'  ⚠️ Stinger failed: {(r.stderr or "")[-200:]}')
        return None, 0
    return out_clip, dur


# ── V8: pattern interrupt clip generator ──
def build_interrupt_clip(out_clip, int_cfg, preset, crf, fps, W, H):
    """Generate 0.4s white flash → black for thumb-stopping effect."""
    dur = float(int_cfg.get('duration', 0.4))
    flash_dur = 0.05
    r = subprocess.run([
        'ffmpeg', '-y',
        '-f', 'lavfi', '-i', f'color=c=white:s={W}x{H}:d={flash_dur}:r={fps}',
        '-f', 'lavfi', '-i', f'color=c=black:s={W}x{H}:d={dur-flash_dur}:r={fps}',
        '-f', 'lavfi', '-i', f'anullsrc=r=48000:cl=stereo',
        '-filter_complex',
        f'[0:v][1:v]concat=n=2:v=1:a=0[vout];[2:a]atrim=duration={dur}[aout]',
        '-map', '[vout]', '-map', '[aout]',
        '-c:v', 'libx264', '-preset', preset, '-crf', crf,
        '-profile:v', 'high', '-level', '4.0', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '128k', '-ar', '48000', '-ac', '2',
        '-t', str(dur), '-movflags', '+faststart', out_clip,
    ], capture_output=True, text=True)
    if r.returncode != 0:
        print(f'  ⚠️ Pattern interrupt failed: {(r.stderr or "")[-200:]}')
        return None, 0
    return out_clip, dur


# BGM
bgm_vol = float(os.environ.get('BGM_VOLUME', '0.025'))
_bgm_env = os.environ.get('BGM_PATH', '').strip()
bgm_candidates = []
if _bgm_env and os.path.exists(_bgm_env):
    bgm_candidates.append(_bgm_env)
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

# Slides autodetect
slides = []
for f in sorted(os.listdir(outdir)):
    if f.endswith('.png') and f[0].isdigit():
        name = f.replace('.png','')
        if os.path.exists(os.path.join(outdir, name + '.mp3')):
            slides.append(name)
if not slides:
    print('❌ No slides found (need NNAME.png + NNAME.mp3)')
    sys.exit(1)

# ── V8: Read shot_bible.json for per-beat metadata ──
bible_path = os.path.join(outdir, 'shot_bible.json')
beat_map = {}  # id → full beat dict
bible_meta = {}  # top-level V8 fields: stinger, interrupt, loop_match
if os.path.exists(bible_path):
    try:
        bible = json.loads(Path(bible_path).read_text(encoding='utf-8'))
        bible_meta = {
            'channel_stinger': bible.get('channel_stinger', {}),
            'pattern_interrupt': bible.get('pattern_interrupt', {}),
            'loop_match': bible.get('loop_match', {}),
            'role_pacing': bible.get('role_pacing', {}),
        }
        for b in bible.get('beats') or []:
            bid = b.get('id', '')
            beat_map[bid] = b  # store full beat dict
        print(f'  📖 shot_bible v{bible.get("version","?")}: {len(beat_map)} beats · stinger={bible_meta["channel_stinger"].get("enabled",False)} · interrupt={bible_meta["pattern_interrupt"].get("enabled",False)} · loop_match={bible_meta["loop_match"].get("enabled",False)}')
    except Exception as e:
        print(f'  ⚠️ shot_bible read error: {e} — using defaults')

titles_env = os.environ.get('SLIDE_TITLES','').split('|')
subtitles_env = os.environ.get('SLIDE_SUBTITLES','').split('|')
trans_env = os.environ.get('SLIDE_TRANSITIONS','').split('|')
anim_env = os.environ.get('SLIDE_ANIMS','').split('|')
while len(titles_env) < len(slides): titles_env.append(slides[len(titles_env)])
while len(subtitles_env) < len(slides): subtitles_env.append('')
while len(trans_env) < len(slides): trans_env.append('')
while len(anim_env) < len(slides): anim_env.append('')

# ── InShot FX presets ──
TRANSITIONS = {
    'fade':       'fade',
    'wipeleft':   'wipeleft',
    'wiperight':  'wiperight',
    'slideup':    'slideup',
    'slidedown':  'slidedown',
    'circlecrop': 'circlecrop',
    'hlslice':    'hlslice',
    'vuslice':    'vuslice',
    'pixelize':   'pixelize',
    'dissolve':   'dissolve',
}
DEFAULT_TRANSITION = 'fade'

COLOR_GRADES = {
    'warm':      'eq=gamma=1.05:contrast=1.05:saturation=1.12:brightness=0.02',
    'cinematic': 'eq=gamma=0.95:contrast=1.15:saturation=0.85:brightness=-0.03',
    'natural':   '',
    'cool':      'eq=gamma=0.98:contrast=1.05:saturation=0.92:brightness=0.01',
    'gold':      'eq=gamma=1.03:contrast=1.08:saturation=1.08:brightness=0.03,colorbalance=rs=0.05:gs=-0.02:bs=-0.08',
}
DEFAULT_GRADE = 'warm'

TEXT_ANIMS = {
    'pop': (
        lambda dur: (
            f":fontsize='max(34, 40 + 8*sin(2*PI*3.5*t))'",
            f"fontsize=40"
        )
    ),
    'slideup': (
        lambda dur: (
            f":y='h*0.78 + (h*0.12)*exp(-t*4.5)'",
            f"y=h*0.80"
        )
    ),
    'typewriter': (
        lambda dur: (
            f":alpha='min(1, t*{max(1.5, 3.0/dur):.1f})'",
            f""
        )
    ),
    'static': (
        lambda dur: ("", "")
    ),
}
DEFAULT_ANIM = 'slideup'

SPEED_RAMPS = {
    'none':       '',
    'slow_in':    "setpts=(0.7+0.3*(1-exp(-t*2)))*PTS,",
    'punch':      "setpts=(1.1-0.25*sin(PI*t/TB)))*PTS,",
}

PRESET = os.environ.get('PRESET', '').strip()
if PRESET == 'shorts':
    crf = '22'
elif PRESET == 'tiktok':
    crf = '23'
    preset = 'veryfast'

clips = []
clip_durations = []

fonts = (font_opt, font_bold_opt)
for i, name in enumerate(slides):
    img = os.path.join(outdir, name + '.png')
    mp3 = os.path.join(outdir, name + '.mp3')
    clip = os.path.join(outdir, f'kb_{name}.mp4')
    beat = beat_map.get(name, {
        'id': name, 'caption': titles_env[i] if i < len(titles_env) else name,
        'pause': 0.0, 'zoom': {'type': 'in', 'pan': 'none'}, 'color_tag': 'warm',
    })
    clip_path, clip_t = build_filter_for_slide(
        img, mp3, clip, beat, fonts, fps, W, H,
        os.environ.get('VIDEO_BRAND', 'S21 Phone'),
        preset, crf,
    )
    clips.append(clip_path)
    clip_durations.append(clip_t)
    dur = float(subprocess.check_output(
        ['ffprobe','-v','error','-show_entries','format=duration',
         '-of','default=noprint_wrappers=1:nokey=1', mp3]
    ).decode().strip())
    grade_key = beat.get('color_tag', beat.get('grade', 'warm'))
    zoom_spec = beat.get('zoom', {})
    zt = zoom_spec.get('type', 'in') if isinstance(zoom_spec, dict) else 'in'
    zp = zoom_spec.get('pan', 'none') if isinstance(zoom_spec, dict) else 'none'
    print(f'  🎞️  {name} | {dur:.1f}s vo · zoom={zt}/{zp} | grade={grade_key}')
    sys.stdout.flush()

# ── V8: Channel stinger (before first slide) ──
stinger_cfg = bible_meta.get('channel_stinger', {})
if stinger_cfg.get('enabled') and not os.environ.get('NO_STINGER'):
    stinger_clip = os.path.join(outdir, 'kb_stinger.mp4')
    sp, sd = build_stinger_clip(stinger_clip, stinger_cfg, fonts, fps, W, H, preset, crf)
    if sp:
        clips.insert(0, sp)
        clip_durations.insert(0, sd)
        print(f'  🔊 stinger: {sd:.1f}s')

# ── V8: Pattern interrupt (after stinger, before first slide) ──
int_cfg = bible_meta.get('pattern_interrupt', {})
if int_cfg.get('enabled') and not os.environ.get('NO_INTERRUPT'):
    int_clip = os.path.join(outdir, 'kb_interrupt.mp4')
    ip, idur = build_interrupt_clip(int_clip, int_cfg, preset, crf, fps, W, H)
    if ip:
        # Insert after stinger if present, else at beginning
        insert_pos = 1 if (stinger_cfg.get('enabled') and clips[0] == stinger_clip) else 0
        clips.insert(insert_pos, ip)
        clip_durations.insert(insert_pos, idur)
        print(f'  ⚡ pattern interrupt: {idur:.1f}s')

# ── V8: End card with loop_match color ──
if end_card_enabled:
    end_card_clip = os.path.join(outdir, 'kb_endcard.mp4')
    brand_text = escape_drawtext(os.environ.get('VIDEO_BRAND', 'S21 Phone'))
    # V8: loop_match — end card background matches opening color tag
    lm_cfg = bible_meta.get('loop_match', {})
    bg_color = '0x0d1117'  # default dark
    if lm_cfg.get('enabled'):
        open_color = lm_cfg.get('open_color', '')
        # Map grade → subtle tinted dark for seamless loop feel
        loop_colors = {
            'gold': '0x1a1a10', 'warm': '0x1a1410', 'cool': '0x10141a',
            'cinematic': '0x101014', 'natural': '0x111111',
        }
        bg_color = loop_colors.get(open_color, '0x0d1117')
    endcard_vf = (
        f"drawtext=text='{brand_text}':fontcolor=#d4a84b:fontsize=52:x=(w-text_w)/2:y=h*0.38:{font_bold_opt}"
        f":alpha='if(lt(t,0.3),0,min(1,(t-0.3)*4))',"
        f"drawtext=text='헨드오프가 곧 성공이다':fontcolor=#ffffff:fontsize=28:x=(w-text_w)/2:y=h*0.48:{font_opt}"
        f":alpha='if(lt(t,0.8),0,min(1,(t-0.8)*4))',"
        f"drawtext=text='@HelenaPark-e7c':fontcolor=#7a7064:fontsize=22:x=(w-text_w)/2:y=h*0.57:{font_opt}"
        f":alpha='if(lt(t,1.3),0,min(1,(t-1.3)*4))',"
        f"drawtext=text='helena751107.github.io':fontcolor=#555555:fontsize=18:x=(w-text_w)/2:y=h*0.65:{font_opt}"
        f":alpha='if(lt(t,1.8),0,min(1,(t-1.8)*4))',"
        f"fade=t=in:st=0:d=0.5,vignette=PI/5,format=yuv420p"
    )
    r = subprocess.run([
        'ffmpeg', '-y',
        '-f', 'lavfi', '-i', f'color=c={bg_color}:s={W}x{H}:d={END_CARD_DUR}:r={fps}',
        '-f', 'lavfi', '-i', f'anullsrc=r=48000:cl=stereo',
        '-vf', endcard_vf,
        '-c:v', 'libx264', '-preset', preset, '-crf', crf,
        '-profile:v', 'high', '-level', '4.0', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '128k', '-ar', '48000', '-ac', '2',
        '-t', str(END_CARD_DUR),
        '-shortest', '-movflags', '+faststart', end_card_clip,
    ], capture_output=True, text=True)
    if r.returncode != 0:
        print(f'  ⚠️ End card failed: {(r.stderr or "")[-300:]}')
        end_card_enabled = False
    else:
        clips.append(end_card_clip)
        clip_durations.append(END_CARD_DUR)
        print(f'  🏁 end card: {END_CARD_DUR:.1f}s')

# ── V6: xfade concat (multi-transition, no more flat fades) ──
n = len(clips)
tmp = os.path.join(outdir, '_concat.mp4')

# Build xfade filter_complex
# V8: use running output time for correct xfade offsets
actual_vdurs = []
for c in clips:
    try:
        vd = float(subprocess.check_output([
            'ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'stream=duration',
            '-of', 'default=nw=1:nk=1', str(c),
        ], text=True).strip() or '0')
    except Exception:
        vd = 0.0
    actual_vdurs.append(max(vd, 0.1))

xfade_dur = XFADE_DUR
filter_parts = []
# Normalise all inputs to same timebase before xfade chain
for i in range(n):
    filter_parts.append(f'[{i}:v]settb=1/{fps},setpts=PTS-STARTPTS[v{i}]')

# V8: track cumulative output time for correct xfade offsets
cum_out = actual_vdurs[0]
for i in range(1, n):
    trans = TRANSITION_CYCLE[(i - 1) % len(TRANSITION_CYCLE)]
    offset = cum_out - xfade_dur
    if offset < 0.05:
        offset = 0.05  # safety floor
    src_a = f'[v0]' if i == 1 else f'[x{i-1}]'
    filter_parts.append(
        f'{src_a}[v{i}]xfade=transition={trans}:duration={xfade_dur}:offset={offset:.3f}[x{i}]'
    )
    cum_out = cum_out + actual_vdurs[i] - xfade_dur

# Rename xfade chain outputs so final label is cross-clip compatible
# After xfade chain: [x1], [x2], ..., [x{n-1}]
# We need the final output label to be [x{n-1}]

vf_expr = ';'.join(filter_parts)

# ── V8: Burn-in ASS karaoke subtitles ──
ass_path = os.path.join(outdir, f'{ep}.ass')
if os.path.exists(ass_path):
    vf_expr += f';[x{n-1}]ass={ass_path}[vout]'
    vid_label = '[vout]'
    print(f'  📝 ASS karaoke subtitles burn-in: {os.path.basename(ass_path)}')
else:
    vid_label = f'[x{n-1}]'

# Audio concat list (demuxer, audio-only)
audio_list = os.path.join(outdir, 'audio_concat.txt')
with open(audio_list, 'w', encoding='utf-8') as f:
    for c in clips:
        ap = os.path.abspath(c).replace("'", r"'\''")
        f.write(f"file '{ap}'\n")

print(f'  🔗 xfade concat · {n} clips · transitions={TRANSITION_CYCLE[:n-1]} · xfade_dur={xfade_dur}s')

concat_cmd = ['ffmpeg', '-y']
for c in clips:
    concat_cmd += ['-i', c]                                   # inputs 0..n-1: video+audio clips
concat_cmd += ['-f', 'concat', '-safe', '0', '-i', audio_list]  # input n: audio-only concat
concat_cmd += [
    '-filter_complex', vf_expr,
    '-map', vid_label,         # xfade final video (with optional ASS subtitles)
    '-map', f'{n}:a',         # concat audio
    '-c:v', 'libx264', '-preset', preset, '-crf', crf,
    '-profile:v', 'high', '-level', '4.0', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '128k', '-ar', '48000', '-ac', '2',
    '-shortest', '-movflags', '+faststart', tmp,
]
r = subprocess.run(concat_cmd, capture_output=True, text=True)
if r.returncode != 0:
    print(f'  ❌ xfade concat: {(r.stderr or "")[-400:]}')
    sys.exit(1)

# concat gate
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

# V8: expected duration = sum of actual clip durations minus xfade overlaps
expect = sum(actual_vdurs) - (n - 1) * xfade_dur if n > 1 else sum(actual_vdurs)
print(f'  🔗 concat probe v={cat_vdur:.1f}s a={cat_adur:.1f}s expect≈{expect:.1f}s')
if cat_vdur < expect * 0.85 or cat_vdur < cat_adur * 0.80:
    print('  ❌ CONCAT GATE FAIL: video shorter than audio/clips → would ship black tail')
    sys.exit(2)
if abs(cat_vdur - cat_adur) > 2.0:
    print(f'  ⚠️ A/V drift {abs(cat_vdur-cat_adur):.1f}s (continuing if video long enough)')

# ── VO-only body (for later full-timeline BGM in _pd_assemble) ──
vo_only = os.path.join(outdir, f'{ep}_vo.mp4')
shutil.copy(tmp, vo_only)
print(f'  🎙 VO-only body saved: {ep}_vo.mp4')

# ── V8: BGM mix with audio ducking (sidechaincompress) ──
final = os.path.join(outdir, f'{ep}_final.mp4')
# Use xfade-corrected total duration for envelope timing
total_dur = float(subprocess.check_output([
    'ffprobe', '-v', 'error', '-select_streams', 'v:0',
    '-show_entries', 'stream=duration',
    '-of', 'default=nw=1:nk=1', tmp,
], text=True).strip() or '0')
if total_dur <= 0:
    total_dur = sum(actual_vdurs) - (n - 1) * xfade_dur
if bgm and os.path.exists(bgm):
    fade_out_st = max(0.5, total_dur - 2.5)
    # V7: BGM envelope — swell at 80-100%
    swell_start = total_dur * 0.80
    swell_dur = total_dur * 0.20
    bgm_env_expr = (
        f"volume='if(gte(t,{swell_start:.1f}),"
        f"{bgm_vol}*(1.0+0.5*(t-{swell_start:.1f})/{swell_dur:.1f}),"
        f"{bgm_vol})':eval=frame"
    )
    if duck_enabled:
        print(f'  🎵 BGM mix {os.path.basename(bgm)} vol={bgm_vol} + 🔊 ducking (thr={duck_threshold} ratio={duck_ratio}) + 📈 swell')
        # sidechaincompress: main=music[1:a], sidechain=voice[0:a]
        # V7: BGM envelope → ducking → mix
        filter_complex = (
            f'[0:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=1.0[voice];'
            f'[1:a]aformat=sample_rates=48000:channel_layouts=stereo,'
            f'{bgm_env_expr},'
            f'afade=t=in:st=0:d=1.5,afade=t=out:st={fade_out_st:.1f}:d=2.0[music_pre];'
            f'[music_pre][voice]sidechaincompress='
            f'threshold={duck_threshold}:ratio={duck_ratio}:attack={duck_attack}:release={duck_release}:makeup=1[music_ducked];'
            f'[voice][music_ducked]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[aout]'
        )
    else:
        print(f'  🎵 BGM mix {os.path.basename(bgm)} vol={bgm_vol} (whisper, no ducking) + 📈 swell')
        filter_complex = (
            f'[0:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=1.0[voice];'
            f'[1:a]aformat=sample_rates=48000:channel_layouts=stereo,'
            f'{bgm_env_expr},'
            f'afade=t=in:st=0:d=1.5,afade=t=out:st={fade_out_st:.1f}:d=2.0[music];'
            f'[voice][music]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[aout]'
        )
    r = subprocess.run([
        'ffmpeg', '-y', '-i', tmp, '-stream_loop', '-1', '-i', bgm,
        '-filter_complex', filter_complex,
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

# ── Encode gate ──
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

trans_used = TRANSITION_CYCLE[:n-1] if n > 1 else ['none']
print(f'  ✅ {ep}_final.mp4 ({size/1024/1024:.1f}MB, {total_dur:.0f}s)  {"🎵+BGM" if bgm else "no BGM"}  GATE={pix_info}')
stinger_on = bible_meta.get('channel_stinger', {}).get('enabled', False)
int_on = bible_meta.get('pattern_interrupt', {}).get('enabled', False)
lm_on = bible_meta.get('loop_match', {}).get('enabled', False)
ass_on = os.path.exists(os.path.join(outdir, f'{ep}.ass'))
zooms = set()
for bm in beat_map.values():
    zs = bm.get('zoom', {})
    if isinstance(zs, dict):
        zooms.add(zs.get('type', '?'))
print(f'  🎬 V8 FX: zoom={zooms if zooms else "N/A"} · duck={"ON" if duck_enabled else "OFF"} · stinger={stinger_on} · interrupt={int_on} · loop={lm_on} · karaoke={ass_on}')

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
