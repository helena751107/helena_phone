#!/home/dtsli/rvc-venv/bin/python3
"""
TIGER DS — Amazing Grace  완전 파이프라인
dsdur(linguistic+dur) → dspitch(linguistic+pitch) → dsacoustic → dsvocoder → Telegram

OpenUTAU와 동일한 4-stage:
1. dur:   linguistic(tokens, word_div, word_dur) → dur(enc, ph_midi, spk) → ph_dur_pred
2. pitch: linguistic(tokens, ph_dur) → pitch(enc, ph_dur, notes, ..., spk) → f0
3. acou:  acoustic(tokens, durations, f0, gender, vel, spk) → mel
4. voc:   tgm_hifigan(mel, f0) → waveform
"""
import os, time, subprocess
import numpy as np, soundfile as sf
import onnxruntime as ort
from pathlib import Path

HOME      = Path.home()
TD        = HOME / '.local/share/OpenUtau/Singers/TIGER_DS'
# Duration model
DUR_LING  = TD / 'dsdur/files/linguistic.onnx'
DUR_MOD   = TD / 'dsdur/files/dur.onnx'
DUR_PH    = TD / 'dsdur/files/phonemes.txt'
# Pitch model
PTC_LING  = TD / 'dspitch/files/linguistic.onnx'
PTC_MOD   = TD / 'dspitch/files/pitch.onnx'
PTC_PH    = TD / 'dspitch/files/phonemes.txt'
# Acoustic + vocoder
ACOU_MOD  = TD / 'dsacoustic/acoustic.onnx'
ACOU_PH   = TD / 'dsacoustic/phonemes.txt'
HIFIGAN   = TD / 'dsvocoder/tgm_hifigan.onnx'

SR = 44100; HOP = 512    # 86.13 FPS

def load_ph(path):
    return {ph: i for i, ph in enumerate(Path(path).read_text().strip().split('\n'))}

# ═══════════════════════════════════════════════════════════════
# Score: Amazing Grace  key=G major, ~72 BPM, 3/4
#
# Each entry = one UTAU note (or SP/AP rest)
#   (syllable_text, [phonemes], midi, dur_sec, is_rest)
#
# AP  = breath at start
# SP  = silence between phrases
# midi = MIDI note number; 0 for rests
# ═══════════════════════════════════════════════════════════════
NOTES = [
    # AP breath
    ('AP',    ['AP'],                  0,   0.12, True),
    # "a-"  /ə/
    ('a',     ['ax'],                  67,  0.70, False),   # G4
    # "-maz-"  /meɪz/ — 'z' belongs here (TIGER dict: amazing=[ax,m,ey,z,ih,ng])
    ('maz',   ['m','ey','z'],          74,  0.60, False),   # D5
    # "-ing"  /ɪŋ/
    ('ing',   ['ih','ng'],             71,  0.55, False),   # B4
    # pause
    ('SP',    ['SP'],                  0,   0.10, True),
    # "grace,"  /ɡreɪs/
    ('grace', ['g','r','ey','s'],      67,  1.40, False),   # G4 (long held)
    # pause
    ('SP',    ['SP'],                  0,   0.12, True),
    # "how"  /haʊ/
    ('how',   ['hh','aw'],             71,  0.60, False),   # B4
    # pause
    ('SP',    ['SP'],                  0,   0.08, True),
    # "sweet"  /swiːt/ — TIGER dict: sweet=[s,w,iy,t,cl]
    ('sweet', ['s','w','iy','t','cl'], 74,  1.00, False),   # D5
    # "the"  /ðə/
    ('the',   ['dh','ax'],             74,  0.45, False),   # D5
    # pause
    ('SP',    ['SP'],                  0,   0.08, True),
    # "sound"  /saʊnd/
    ('sound', ['s','aw','n','d'],      71,  2.20, False),   # B4
    # end breath
    ('SP',    ['SP'],                  0,   0.18, True),
]

def sec_to_frames(s):
    return max(1, round(s * SR / HOP))

def synthesize(out_wav='/tmp/tiger_ag.wav', steps=30, spk='tiger_vinyl'):
    dur_map  = load_ph(DUR_PH)
    ptc_map  = load_ph(PTC_PH)
    acu_map  = load_ph(ACOU_PH)
    dur_emb  = np.fromfile(str(TD / f'dsdur/files/{spk}.emb'),  dtype=np.float32)
    ptc_emb  = np.fromfile(str(TD / f'dspitch/files/{spk}.emb'), dtype=np.float32)
    acu_emb  = np.fromfile(str(TD / f'dsacoustic/{spk}.emb'), dtype=np.float32)

    # ── Build word-level inputs ───────────────────────────────
    all_phs   = []   # flat phoneme list
    word_div  = []   # phonemes per word
    word_dur  = []   # word duration in frames
    ph_midi   = []   # MIDI per phoneme (for dur model)
    note_list = []   # (midi, frames, is_rest) for pitch model

    for (_, phs, midi, dur_s, is_rest) in NOTES:
        fr = sec_to_frames(dur_s)
        all_phs.extend(phs)
        word_div.append(len(phs))
        word_dur.append(fr)
        ph_midi.extend([midi] * len(phs))
        note_list.append((midi, fr, is_rest))

    n_tokens = len(all_phs)
    n_words  = len(word_div)

    # ── STEP 1: Duration model ────────────────────────────────
    print(f"[1/4] dur: {n_tokens} phonemes, {n_words} words")
    t0 = time.time()
    dur_tokens = np.array([[dur_map.get(ph, dur_map['SP']) for ph in all_phs]], dtype=np.int64)
    wd_arr     = np.array([word_div], dtype=np.int64)
    wdur_arr   = np.array([word_dur],  dtype=np.int64)
    ph_midi_arr= np.array([ph_midi],   dtype=np.int64)
    n_tok      = dur_tokens.shape[1]
    dur_spk    = np.tile(dur_emb, (1, n_tok, 1)).reshape(1, n_tok, 256).astype(np.float32)

    sess_dl = ort.InferenceSession(str(DUR_LING), providers=['CPUExecutionProvider'])
    enc_dur, xm_dur = sess_dl.run(
        ['encoder_out', 'x_masks'],
        {'tokens': dur_tokens, 'word_div': wd_arr, 'word_dur': wdur_arr}
    )
    sess_dm = ort.InferenceSession(str(DUR_MOD), providers=['CPUExecutionProvider'])
    ph_dur_pred = sess_dm.run(
        ['ph_dur_pred'],
        {'encoder_out': enc_dur, 'x_masks': xm_dur,
         'ph_midi': ph_midi_arr, 'spk_embed': dur_spk}
    )[0][0]   # (n_tokens,) float32, in frames

    # Normalize: ensure each word's phoneme durations sum to word_dur
    ph_dur_int = np.zeros(n_tokens, dtype=np.int64)
    idx = 0
    for wi, (n_ph, target_fr) in enumerate(zip(word_div, word_dur)):
        seg = ph_dur_pred[idx:idx+n_ph].clip(min=0.5)
        seg_scaled = seg * target_fr / seg.sum()
        seg_int = np.round(seg_scaled).astype(np.int64).clip(min=1)
        # Fix rounding error
        diff = target_fr - seg_int.sum()
        if diff != 0:
            seg_int[seg_int.argmax()] += diff
        ph_dur_int[idx:idx+n_ph] = seg_int
        idx += n_ph

    total_frames = int(ph_dur_int.sum())
    print(f"  {time.time()-t0:.1f}s  ph_dur predicted, total={total_frames} ({total_frames*HOP/SR:.2f}s)")

    # ── STEP 2a: Pitch linguistic ─────────────────────────────
    print(f"[2/4] pitch linguistic + model")
    t0 = time.time()
    ptc_tokens = np.array([[ptc_map.get(ph, ptc_map['SP']) for ph in all_phs]], dtype=np.int64)
    ph_dur_arr = np.array([ph_dur_int], dtype=np.int64)

    sess_pl = ort.InferenceSession(str(PTC_LING), providers=['CPUExecutionProvider'])
    enc_ptc, _ = sess_pl.run(
        ['encoder_out', 'x_masks'],
        {'tokens': ptc_tokens, 'ph_dur': ph_dur_arr}
    )

    # Build note arrays (each NOTES entry = one note)
    note_midi_arr = np.array([[float(n[0]) for n in note_list]], dtype=np.float32)
    note_dur_arr  = np.array([[n[1] for n in note_list]], dtype=np.int64)
    note_rest_arr = np.array([[n[2] for n in note_list]], dtype=bool)

    # Initial pitch guess per frame (MIDI units)
    pitch_guess = np.zeros(total_frames, dtype=np.float32)
    fi = 0
    last_midi = 67.0
    for ph, fr in zip(all_phs, ph_dur_int):
        note_entry = None
        for i, p in enumerate(all_phs):
            if p == ph: break
        # Simpler: use global frame pointer to find which note we're in
        pitch_guess[fi:fi+fr] = last_midi
        fi += fr
    # Redo: map frames to notes, with portamento + vibrato for musicality
    pitch_guess2 = np.zeros(total_frames, dtype=np.float32)
    ph_idx = 0; fi2 = 0
    prev_midi = 67.0
    for ni, (midi, fr_note, is_rest) in enumerate(note_list):
        n_ph = word_div[ni]
        seg_frames = int(ph_dur_int[ph_idx:ph_idx+n_ph].sum())
        fill = float(midi) if midi > 0 else (prev_midi if ni > 0 else 67.0)
        if midi > 0:
            # portamento: glide from prev_midi in first 4 frames
            glide = min(4, seg_frames)
            for gf in range(glide):
                pitch_guess2[fi2+gf] = prev_midi + (fill - prev_midi) * (gf+1) / glide
            # steady pitch for rest of note
            pitch_guess2[fi2+glide:fi2+seg_frames] = fill
            # vibrato for long held notes (>40 frames ≈ 0.46s)
            if seg_frames > 40 and not is_rest:
                vibrato_rate = 5.0 / (SR / HOP)  # 5Hz in frame units
                vibrato_depth = 0.25  # ±0.25 semitone (moderate for classical)
                vibrato_onset = min(10, seg_frames // 4)  # delay before vibrato starts
                for vf in range(vibrato_onset, seg_frames):
                    fade = min(1.0, (vf - vibrato_onset) / 10.0)
                    pitch_guess2[fi2+vf] += vibrato_depth * fade * np.sin(2*np.pi*vibrato_rate*(vf-vibrato_onset))
            prev_midi = fill
        else:
            pitch_guess2[fi2:fi2+seg_frames] = prev_midi
        fi2 += seg_frames
        ph_idx += n_ph
    pitch_guess2 = pitch_guess2[:total_frames].reshape(1, -1)

    expr   = np.ones((1, total_frames), dtype=np.float32)
    retake = np.ones((1, total_frames), dtype=bool)
    ptc_spk= np.tile(ptc_emb, (1, total_frames, 1)).reshape(1, total_frames, 256).astype(np.float32)

    sess_pm = ort.InferenceSession(str(PTC_MOD), providers=['CPUExecutionProvider'])
    pitch_pred = sess_pm.run(
        ['pitch_pred'],
        {
            'encoder_out': enc_ptc,
            'ph_dur':      ph_dur_arr,
            'note_midi':   note_midi_arr,
            'note_rest':   note_rest_arr,
            'note_dur':    note_dur_arr,
            'pitch':       pitch_guess2,
            'expr':        expr,
            'retake':      retake,
            'spk_embed':   ptc_spk,
            'steps':       np.array(steps, dtype=np.int64),
        }
    )[0]  # [1, total_frames]  MIDI units

    # MIDI → Hz
    f0 = 440.0 * (2.0 ** ((pitch_pred[0] - 69.0) / 12.0))
    f0 = np.clip(f0, 50.0, 1500.0).astype(np.float32)
    # Silence unvoiced (SP/AP) frames
    fi3 = 0; ph_idx = 0
    for ni, (midi, fr_note, is_rest) in enumerate(note_list):
        n_ph = word_div[ni]
        seg_frames = int(ph_dur_int[ph_idx:ph_idx+n_ph].sum())
        if is_rest:
            f0[fi3:fi3+seg_frames] = 0.0
        fi3 += seg_frames; ph_idx += n_ph
    print(f"  {time.time()-t0:.1f}s  F0: mean={f0[f0>0].mean():.1f}Hz  voiced={np.sum(f0>0)} frames")

    f0_in = f0.reshape(1, -1)

    # ── STEP 3: Acoustic ──────────────────────────────────────
    print(f"[3/4] acoustic: {n_tokens} phonemes, {total_frames} frames")
    t0 = time.time()
    acu_tokens = np.array([[acu_map.get(ph, acu_map['SP']) for ph in all_phs]], dtype=np.int64)
    acu_dur    = np.array([ph_dur_int], dtype=np.int64)
    acu_spk    = np.tile(acu_emb, (1, total_frames, 1)).reshape(1, total_frames, 256).astype(np.float32)

    sess_am = ort.InferenceSession(str(ACOU_MOD), providers=['CPUExecutionProvider'])
    mel = sess_am.run(
        ['mel'],
        {
            'tokens':    acu_tokens,
            'durations': acu_dur,
            'f0':        f0_in,
            'gender':    np.zeros((1, total_frames), dtype=np.float32),
            'velocity':  np.ones((1, total_frames), dtype=np.float32),
            'spk_embed': acu_spk,
            'depth':     np.array(0.5, dtype=np.float32),
            'steps':     np.array(steps, dtype=np.int64),
        }
    )[0]
    mel_frames = mel.shape[1]
    print(f"  {time.time()-t0:.1f}s  mel={mel.shape}")

    # Align f0 to mel frames (may differ ±1 from conv padding)
    if mel_frames != total_frames:
        f0_mel = np.interp(
            np.linspace(0, 1, mel_frames),
            np.linspace(0, 1, total_frames),
            f0
        ).astype(np.float32)
    else:
        f0_mel = f0.copy()

    # ── STEP 4: Vocoder ───────────────────────────────────────
    print("[4/4] vocoder")
    t0 = time.time()
    sess_hifi = ort.InferenceSession(str(HIFIGAN), providers=['CPUExecutionProvider'])
    wav = sess_hifi.run(
        ['waveform'],
        {'mel': mel, 'f0': f0_mel.reshape(1, -1)}
    )[0][0].astype(np.float32)

    peak = np.abs(wav).max()
    if peak > 0: wav = wav / peak * 0.9
    sf.write(out_wav, wav, SR)
    dur_s = len(wav) / SR
    rms = float(np.sqrt(np.mean(wav**2)))
    print(f"  {time.time()-t0:.1f}s  audio={dur_s:.2f}s  RMS={rms:.4f}")
    return out_wav

def to_mp3(wav, mp3):
    subprocess.run([
        'ffmpeg', '-y', '-i', wav,
        '-af', 'highpass=f=60,loudnorm=I=-14:LRA=11:TP=-1.0',
        '-b:a', '192k', mp3
    ], check=True, capture_output=True)

def send_tg(mp3, caption='TIGER DS Fresh — Amazing Grace 🎵'):
    s = {}
    for line in (Path.home()/'dtslib-papyrus/telegram/.secrets.env').read_text().split('\n'):
        if '=' in line and not line.startswith('#'):
            k, _, v = line.partition('=')
            s[k.strip()] = v.strip().strip('"\'')
    r = subprocess.run([
        'curl', '-s', '-X', 'POST',
        f'https://api.telegram.org/bot{s.get("TG_PARKSY_BRIDGE_BOT","")}/sendAudio',
        '-F', f'chat_id=REDACTED',
        '-F', f'audio=@{mp3}',
        '-F', f'caption={caption}',
    ], capture_output=True, text=True)
    print("TG ✅" if '"ok":true' in r.stdout else f"TG 실패: {r.stdout[:100]}")

if __name__ == '__main__':
    import sys
    spk = sys.argv[1] if len(sys.argv) > 1 else 'tiger_vinyl'
    steps = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    t0 = time.time()
    print(f"speaker={spk}, steps={steps}")
    wav = synthesize('/tmp/tiger_ag.wav', steps=steps, spk=spk)
    mp3 = '/tmp/tiger_ag.mp3'
    print("mastering...")
    to_mp3(wav, mp3)
    sz = os.path.getsize(mp3) // 1024
    print(f"MP3 ✅ {mp3} ({sz}KB)  total={time.time()-t0:.1f}s")
    send_tg(mp3, caption=f'TIGER DS {spk} — Amazing Grace 🎵')
