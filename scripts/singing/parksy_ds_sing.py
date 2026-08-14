#!/home/dtsli/rvc-venv/bin/python3
"""
parksy_ds_sing.py — PARKSY_DS 완전 파이프라인 (OpenUTAU DiffSinger 방식)
==========================================================================
linguistic-dur → dur → linguistic-pitch → pitch → variance → acoustic → tgm_hifigan → helena RVC

사용법:
  ~/rvc-venv/bin/python3 parksy_ds_sing.py --preset amazing_grace --out /tmp/out.mp3
  ~/rvc-venv/bin/python3 parksy_ds_sing.py \
    --lyrics "나같은죄인살리신" \
    --notes "G4,Bb4,Bb4,D5,Eb5,D5,Bb4,G4" \
    --durs  "0.75,0.75,0.375,1.5,0.75,1.125,0.375,2.25" \
    --out /tmp/out.mp3
"""

import argparse, json, os, subprocess, sys, time
from pathlib import Path
import numpy as np
import soundfile as sf
import onnxruntime as ort

# ─── 경로 ─────────────────────────────────────────────────────────────────────
HOME          = Path.home()
DS_DIR        = HOME / '.local/share/OpenUtau/Singers/PARKSY_DS'
ACOUSTIC      = DS_DIR / 'files/acoustic.onnx'
DUR_LING      = DS_DIR / 'files/linguistic-dur.onnx'
DUR_MODEL     = DS_DIR / 'files/dur.onnx'
PITCH_LING    = DS_DIR / 'files/linguistic-pitch.onnx'
PITCH_MODEL   = DS_DIR / 'files/pitch.onnx'
VARIANCE      = DS_DIR / 'files/variance.onnx'
HIFIGAN       = DS_DIR / 'tgm_hifigan/tgm_hifigan_v110.onnx'
PHONEMES_JSON = DS_DIR / 'files/phonemes.json'
SPK_EMB_FILE  = DS_DIR / 'embeds/standard.emb'

RVC_DIR    = HOME / 'rvc-webui-local'
HELENA_PTH = HOME / 'rvc_models/helena_rvc/helena_rvc.pth'
HELENA_IDX = HOME / 'rvc_models/helena_rvc/helena_rvc.index'

SR       = 44100
HOP      = 512
FPS      = SR / HOP          # ≈ 86.13 frames/sec

WORK = Path('/tmp/parksy_sing')
WORK.mkdir(exist_ok=True)

# ─── 프리셋 ───────────────────────────────────────────────────────────────────
PRESETS = {
    'amazing_grace': {
        'title': 'Amazing Grace — 나 같은 죄인 살리신',
        'lyrics': '나같은죄인살리신',               # 8 syllables
        'notes':  'G4,Bb4,Bb4,D5,Eb5,D5,Bb4,G4',
        'durs':   '0.75,0.75,0.375,1.5,0.75,1.125,0.375,2.25',
    },
    'lord_prayer': {
        'title': '주기도문 — 하늘에 계신 우리 아버지',
        'lyrics': '하늘에계신우리아버지',
        'notes':  'C4,D4,E4,F4,G4,A4,G4,G4,A4',
        'durs':   '0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,1.0',
    },
}

# ─── 한국어 G2P ───────────────────────────────────────────────────────────────
ONSET_MAP = {
    'ᄀ':'g','ᄁ':'kk','ᄂ':'n','ᄃ':'d','ᄄ':'tt','ᄅ':'r','ᄆ':'m',
    'ᄇ':'b','ᄈ':'pp','ᄉ':'s','ᄊ':'ss','ᄋ':'','ᄌ':'j','ᄍ':'jj',
    'ᄎ':'ch','ᄏ':'k','ᄐ':'t','ᄑ':'p','ᄒ':'h',
}
NUCLEUS_MAP = {
    'ᅡ':['a'],'ᅢ':['e'],'ᅣ':['y','a'],'ᅤ':['y','e'],'ᅥ':['eo'],
    'ᅦ':['e'],'ᅧ':['y','eo'],'ᅨ':['y','e'],'ᅩ':['o'],'ᅪ':['w','a'],
    'ᅫ':['w','e'],'ᅬ':['w','e'],'ᅭ':['y','o'],'ᅮ':['u'],'ᅯ':['w','eo'],
    'ᅰ':['w','e'],'ᅱ':['w','i'],'ᅲ':['y','u'],'ᅳ':['eu'],'ᅴ':['eu','i'],
    'ᅵ':['i'],
}
CODA_MAP = {
    'ᆨ':'K','ᆩ':'K','ᆪ':'K','ᆫ':'N','ᆬ':'N','ᆭ':'N','ᆮ':'T',
    'ᆯ':'L','ᆰ':'K','ᆱ':'M','ᆲ':'L','ᆳ':'L','ᆴ':'L','ᆵ':'P',
    'ᆶ':'L','ᆷ':'M','ᆸ':'P','ᆹ':'P','ᆺ':'T','ᆻ':'T','ᆼ':'NG',
    'ᆽ':'T','ᆾ':'T','ᆿ':'K','ᇀ':'T','ᇁ':'P','ᇂ':'T',
}

def syl_to_ph(ch):
    code = ord(ch) - 0xAC00
    onset = chr(0x1100 + code // 588)
    nuc   = chr(0x1161 + (code % 588) // 28)
    ci    = code % 28
    coda  = chr(0x11A8 + ci - 1) if ci else None
    ph = []
    o = ONSET_MAP.get(onset, '')
    if o: ph.append(o)
    ph.extend(NUCLEUS_MAP.get(nuc, ['a']))
    if coda:
        c = CODA_MAP.get(coda)
        if c: ph.append(c)
    return ph or ['a']

NOTE_MAP = {'C':0,'C#':1,'Db':1,'D':2,'D#':3,'Eb':3,'E':4,'F':5,
            'F#':6,'Gb':6,'G':7,'G#':8,'Ab':8,'A':9,'A#':10,'Bb':10,'B':11}

def note_to_midi(note):
    note = note.strip()
    if note.lower() in ('rest','r','ap','sp',''): return 60
    if len(note) >= 2 and note[1] in ('#','b') and len(note) >= 3:
        n, oct_ = note[:2], int(note[2:])
    else:
        n, oct_ = note[0], int(note[1:])
    return (oct_ + 1) * 12 + NOTE_MAP.get(n, 0)

def midi_to_hz(midi): return 440.0 * (2.0 ** ((midi - 69) / 12.0))

# ─── ONNX 세션 ────────────────────────────────────────────────────────────────
def sess(path):
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 4
    opts.inter_op_num_threads = 2
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    return ort.InferenceSession(str(path), sess_options=opts,
                                providers=['CPUExecutionProvider'])

# ─── 핵심 파이프라인 ──────────────────────────────────────────────────────────
def synthesize(lyrics, note_seq, note_dur_s, steps=20):
    ph_map  = json.loads(PHONEMES_JSON.read_text())
    spk_emb = np.fromfile(str(SPK_EMB_FILE), dtype=np.float32)   # (384,)

    # ── G2P: 음절 → 음소 시퀀스 ──────────────────────────────────────────────
    syllables = [ch for ch in lyrics if '가' <= ch <= '힣']
    assert len(syllables) == len(note_seq), \
        f'음절 수({len(syllables)}) ≠ 음표 수({len(note_seq)})'

    # AP + 음절별 음소 + SP
    all_ph   = ['AP']
    word_div = [1]                           # AP = 1 phoneme
    word_dur_f = [max(1, round(0.2 * FPS))]  # AP duration in frames

    ph_midi_list = [60]   # AP → middle C
    syl_ph_seqs  = []     # 음절별 음소 리스트 (f0 빌드용)

    for syl, note, dur_s in zip(syllables, note_seq, note_dur_s):
        ph = syl_to_ph(syl)
        n_ph = len(ph)
        total_f = max(n_ph, round(dur_s * FPS))
        all_ph.extend(ph)
        word_div.append(n_ph)
        word_dur_f.append(total_f)
        midi = note_to_midi(note)
        ph_midi_list.extend([midi] * n_ph)
        syl_ph_seqs.append((ph, total_f, dur_s, midi))

    all_ph.append('SP')
    word_div.append(1)
    word_dur_f.append(max(1, round(0.3 * FPS)))
    ph_midi_list.append(60)

    n_tokens = len(all_ph)
    n_words  = len(word_div)

    unk = ph_map.get('SP', 1)
    tokens   = np.array([[ph_map.get(p, unk) for p in all_ph]], dtype=np.int64)
    langs    = np.zeros((1, n_tokens), dtype=np.int64)   # use_lang_id=false
    w_div    = np.array([word_div], dtype=np.int64)
    w_dur    = np.array([word_dur_f], dtype=np.int64)
    ph_midi  = np.array([ph_midi_list], dtype=np.int64)

    print(f'  음소: {all_ph}')

    # ── STEP 1: linguistic-dur → encoder_out ─────────────────────────────────
    t0 = time.time()
    enc_out, x_masks = sess(DUR_LING).run(
        ['encoder_out', 'x_masks'],
        {'tokens': tokens, 'languages': langs,
         'word_div': w_div, 'word_dur': w_dur}
    )
    # enc_out: [1, n_tokens, 384]

    # ── STEP 2: dur.onnx → ph_dur_pred ───────────────────────────────────────
    spk_tok = np.tile(spk_emb, (1, n_tokens, 1))   # [1, n_tokens, 384]
    ph_dur_pred = sess(DUR_MODEL).run(
        ['ph_dur_pred'],
        {'encoder_out': enc_out, 'x_masks': x_masks,
         'ph_midi': ph_midi, 'spk_embed': spk_tok}
    )[0]   # [1, n_tokens] float32

    # 예측된 duration을 note_dur로 스케일 조정 (word별 합 보정)
    ph_dur_int = np.maximum(1, np.round(ph_dur_pred[0])).astype(np.int64)
    # word별 합을 w_dur에 맞춤
    idx = 0
    for wi, (n_ph, target_f) in enumerate(zip(word_div, word_dur_f)):
        seg = ph_dur_int[idx:idx+n_ph]
        cur = int(seg.sum())
        if cur != target_f and n_ph > 0:
            # 보정: 가장 긴 음소에 차이 분배
            diff = target_f - cur
            longest = int(np.argmax(seg))
            seg[longest] = max(1, int(seg[longest]) + diff)
            ph_dur_int[idx:idx+n_ph] = seg
        idx += n_ph

    durations = ph_dur_int[np.newaxis, :]   # [1, n_tokens]
    total_frames = int(durations.sum())
    print(f'  총 프레임: {total_frames} ({total_frames/FPS:.1f}s)  ({time.time()-t0:.1f}s)')

    # ── STEP 3: linguistic-pitch → encoder_out ────────────────────────────────
    enc_out_p, _ = sess(PITCH_LING).run(
        ['encoder_out', 'x_masks'],
        {'tokens': tokens, 'languages': langs, 'ph_dur': durations}
    )

    # ── STEP 4: pitch.onnx → pitch_pred (F0 곡선) ────────────────────────────
    # note_midi / note_dur (프레임 단위, word별)
    note_midi_arr = np.array([[float(note_to_midi(n)) for n in note_seq]], dtype=np.float32)
    note_dur_arr  = np.array([[max(1, round(d * FPS)) for d in note_dur_s]], dtype=np.int64)
    # note_dur에 AP+SP 추가 (pitch 모델은 AP/SP 포함 전체 word_dur를 봄)
    note_midi_full = np.concatenate([np.array([[60.0]], dtype=np.float32), note_midi_arr, np.array([[60.0]], dtype=np.float32)], axis=1)
    note_dur_full  = np.concatenate([np.array([[word_dur_f[0]]], dtype=np.int64),
                                      note_dur_arr,
                                      np.array([[word_dur_f[-1]]], dtype=np.int64)], axis=1)

    spk_frame = np.tile(spk_emb, (1, total_frames, 1))   # [1, n_frames, 384]
    init_pitch = np.zeros((1, total_frames), dtype=np.float32)
    expr       = np.zeros((1, total_frames), dtype=np.float32)
    retake     = np.ones((1, total_frames), dtype=bool)   # 전부 예측

    pitch_pred = sess(PITCH_MODEL).run(
        ['pitch_pred'],
        {'encoder_out': enc_out_p, 'ph_dur': durations,
         'note_midi': note_midi_full, 'note_dur': note_dur_full,
         'pitch': init_pitch, 'expr': expr, 'retake': retake,
         'spk_embed': spk_frame,
         'steps': np.array(steps // 2, dtype=np.int64)}
    )[0]   # [1, n_frames] float32 — MIDI 단위

    # MIDI → Hz
    f0 = (440.0 * (2.0 ** ((pitch_pred - 69) / 12.0))).astype(np.float32)
    f0 = np.clip(f0, 40.0, 2000.0)
    print(f'  F0 mean={float(f0.mean()):.1f}Hz  min={float(f0.min()):.1f}  max={float(f0.max()):.1f}')

    # ── STEP 5: variance.onnx → tension ───────────────────────────────────────
    retake_v = np.ones((1, total_frames, 1), dtype=bool)
    tension_in = np.zeros((1, total_frames), dtype=np.float32)
    tension_pred = sess(VARIANCE).run(
        ['tension_pred'],
        {'encoder_out': enc_out_p, 'ph_dur': durations,
         'pitch': pitch_pred, 'tension': tension_in,
         'retake': retake_v, 'spk_embed': spk_frame,
         'steps': np.array(steps // 2, dtype=np.int64)}
    )[0]   # [1, n_frames]
    tension = np.clip(tension_pred, -4.0, 4.0).astype(np.float32)

    # ── STEP 6: acoustic.onnx → mel ───────────────────────────────────────────
    ones  = np.ones((1, total_frames), dtype=np.float32)
    t0 = time.time()
    mel = sess(ACOUSTIC).run(
        ['mel'],
        {'tokens':    tokens,
         'durations': durations,
         'f0':        f0,
         'tension':   tension,
         'gender':    ones * 0.0,
         'velocity':  ones * 1.0,
         'depth':     np.array(1.0, dtype=np.float32),
         'steps':     np.array(steps, dtype=np.int64)}
    )[0]
    print(f'  acoustic: {time.time()-t0:.1f}s  mel={mel.shape}')

    # ── STEP 7: tgm_hifigan → waveform ────────────────────────────────────────
    t0 = time.time()
    wav = sess(HIFIGAN).run(
        ['waveform'],
        {'mel': mel, 'f0': f0}
    )[0].squeeze()
    rms = float(np.sqrt(np.mean(wav ** 2)))
    print(f'  hifigan: {time.time()-t0:.1f}s  audio={len(wav)/SR:.2f}s  RMS={rms:.4f}')
    return wav.astype(np.float32), f0

# ─── helena RVC ───────────────────────────────────────────────────────────────
def apply_rvc(wav, out_wav):
    sf.write(str(WORK / 'ds_raw.wav'), wav, SR)
    weights_dir = RVC_DIR / 'assets/weights'
    logs_dir    = RVC_DIR / 'logs/helena_rvc'
    weights_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    wlink = weights_dir / 'helena_rvc.pth'
    ilink = logs_dir / 'helena_rvc.index'
    if not wlink.exists(): wlink.symlink_to(HELENA_PTH)
    if not ilink.exists(): ilink.symlink_to(HELENA_IDX)

    script = f"""
import os,sys,numpy as np,soundfile as sf
os.chdir('{RVC_DIR}'); sys.path.insert(0,'{RVC_DIR}')
os.environ.update({{'weight_root':'{weights_dir}','index_root':'{RVC_DIR}/logs',
    'outside_index_root':'{RVC_DIR}/logs','rmvpe_root':'{RVC_DIR}/assets/rmvpe'}})
from configs.config import Config
from infer.vc.modules import VC
vc = VC(Config()); vc.get_vc('helena_rvc.pth')
sr,audio = vc.vc_single(sid=0,input_audio_path='{WORK}/ds_raw.wav',
    f0_up_key=0,f0_method='rmvpe',
    file_index='{logs_dir}/helena_rvc.index',
    index_rate=0.75,resample_sr=40000,rms_mix_rate=0.25,protect=0.33)[1]
a=audio.astype(np.float32)/32768.0
sf.write('{out_wav}',a,sr)
print(f'RVC OK {{len(a)/sr:.1f}}s RMS={{float(np.sqrt(np.mean(a**2))):.4f}}')
"""
    t0 = time.time()
    r = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True)
    for line in r.stdout.splitlines():
        if line.strip(): print(f'  {line}')
    if r.returncode != 0:
        print(f'  ❌ RVC 실패: {r.stderr[-300:]}')
        return False
    print(f'  helena_rvc ✅ {time.time()-t0:.1f}s')
    return True

def to_mp3(wav_in, mp3_out):
    r = subprocess.run(['ffmpeg','-y','-i',wav_in,
        '-af','highpass=f=80,loudnorm=I=-14:LRA=11:TP=-1.0',
        '-b:a','192k',mp3_out], capture_output=True)
    if r.returncode == 0:
        print(f'  MP3 ✅ {mp3_out} ({Path(mp3_out).stat().st_size//1024}KB)')

def send_tg(mp3, caption):
    secrets = HOME / 'dtslib-papyrus/telegram/.secrets.env'
    if not secrets.exists(): return
    env = {}
    for ln in secrets.read_text().splitlines():
        if '=' in ln and not ln.startswith('#'):
            k, v = ln.split('=',1); env[k.strip()] = v.strip().strip('"\'')
    token = env.get('TG_PARKSY_BRIDGE_BOT','')
    if not token: return
    chat = env.get('TG_PARKSY_CHAT_ID','REDACTED')
    r = subprocess.run(['curl','-s','-F',f'audio=@{mp3}','-F',f'caption={caption}',
        f'https://api.telegram.org/bot{token}/sendAudio?chat_id={chat}'],
        capture_output=True, text=True)
    print('  TG ✅' if '"ok":true' in r.stdout else f'  TG ⚠️ {r.stdout[:80]}')

# ─── main ─────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--preset', default='amazing_grace')
    ap.add_argument('--lyrics')
    ap.add_argument('--notes')
    ap.add_argument('--durs')
    ap.add_argument('--steps', type=int, default=20)
    ap.add_argument('--no-rvc', action='store_true')
    ap.add_argument('--telegram', action='store_true')
    ap.add_argument('--out', default='/tmp/helena_sing.mp3')
    args = ap.parse_args()

    if args.lyrics and args.notes and args.durs:
        lyrics   = args.lyrics
        note_seq = [n.strip() for n in args.notes.split(',')]
        note_dur = [float(d) for d in args.durs.split(',')]
        title    = '가창 합성'
    else:
        p = PRESETS[args.preset]
        lyrics, note_seq, note_dur, title = (
            p['lyrics'],
            [n.strip() for n in p['notes'].split(',')],
            [float(d) for d in p['durs'].split(',')],
            p['title']
        )

    print(f'=== {title} ===')
    print(f'가사: {lyrics}  음표: {note_seq}')
    wav, f0 = synthesize(lyrics, note_seq, note_dur, args.steps)

    rvc_wav = str(WORK / 'helena_rvc.wav')
    if not args.no_rvc and HELENA_PTH.exists() and apply_rvc(wav, rvc_wav):
        to_mp3(rvc_wav, args.out)
    else:
        raw_wav = str(WORK / 'ds_out.wav')
        sf.write(raw_wav, wav, SR)
        to_mp3(raw_wav, args.out)

    print(f'\n✅ {args.out}')
    if args.telegram:
        send_tg(args.out, f'helena 가창: {title}')

if __name__ == '__main__':
    main()
